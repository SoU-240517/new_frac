# インポート
from dataclasses import dataclass
import numpy as np
import matplotlib.patches as patches
import matplotlib.transforms as transforms
from enum import Enum, auto
import time  # スロットリング用の時間処理モジュール

@dataclass
class ResizeOperationData:            # リサイズ操作のデータを保持するデータクラス
    corner_name: str                  # 操作中の角（'bottom_left'など）
    fixed_point: tuple[float, float]  # 固定される対角の座標
    original_x: float                 # 矩形の元のx座標
    original_y: float                 # 矩形の元のy座標
    original_width: float             # 矩形の元の幅
    original_height: float            # 矩形の元の高さ
    press_x: float                    # ドラッグ開始時のx座標
    press_y: float                    # ドラッグ開始時のy座標

@dataclass
class RotationOperationData:
    center_x: float
    center_y: float
    initial_angle: float

class ZoomState(Enum):                    # ズーム操作の状態を表す列挙型
    NO_ZOOM_RECT = auto()                 # ズーム領域無し（領域が存在しない）
    CREATE = auto()                       # ズーム領域新規作成モード（左ボタン ONで開始）
    WAIT_NOKEY_ZOOM_RECT_EXISTS = auto()  # ズーム領域有り（キー入力無し）
    MOVE = auto()                         # 領域移動モード（領域内で左ドラッグ）
    WAIT_SHIFT_RESIZE = auto()            # リサイズ待機モード（shift ON）
    RESIZE = auto()                       # リサイズモード（shift＋左ドラッグ）
    WAIT_ALT_ROTATE = auto()              # 回転待機モード（alt ON）
    ROTATE = auto()                       # 回転モード（alt＋左ドラッグ）

class ZoomSelector:
    def __init__(self, ax, on_zoom_confirm, on_zoom_cancel):
        print("START : __init__")
        """
        ax: 対象の matplotlib Axes
        on_zoom_confirm: ズーム確定時のコールバック（zoom_params を引数に取る）
        on_zoom_cancel: ズームキャンセル時のコールバック
        """
        self.ax = ax
        self.canvas = ax.figure.canvas
        self.on_zoom_confirm = on_zoom_confirm
        self.on_zoom_cancel = on_zoom_cancel
        self.rect = None         # 現在のズーム領域（情報があれば領域有り）
        self.last_rect = None    # 直前のズーム領域（キャンセル用）
        self.press = None        # ドラッグ開始時の情報（移動・リサイズ・回転共通）
        self.start_x = None      # 新規作成開始時の x 座標
        self.start_y = None      # 新規作成開始時の y 座標
        self.key_pressed = {'shift': False, 'alt': False}  # キー状態追跡用の変数
        self.angle = 0.0         # 現在の回転角（度）
        self.rot_base = 0.0      # 回転開始時の角度
        self.last_cursor_state = "arrow"
        self.last_motion_time = int(time.time() * 1000)  # 初期値を設定
        self.motion_throttle_ms = 30  # 30ミリ秒ごとに処理（約33fps）
        self.MIN_RECT_SIZE = 0.1  # ズーム領域の最小サイズ
        self._state = ZoomState.NO_ZOOM_RECT  # 内部状態変数（アンダースコア付き）
        self._debug = True  # デバッグモードフラグ
        self._cached_rect_props = None  # キャッシュ用変数
        self._last_motion_event = None  # 直前のマウス移動イベントを保存する変数

        # イベントハンドラ接続
        self.cid_press       = self.canvas.mpl_connect('button_press_event', self.on_press)
        self.cid_release     = self.canvas.mpl_connect('button_release_event', self.on_release)
        self.cid_motion      = self.canvas.mpl_connect('motion_notify_event', self.on_motion)
        self.cid_key_press   = self.canvas.mpl_connect("key_press_event", self.on_key_press)
        self.cid_key_release = self.canvas.mpl_connect("key_release_event", self.on_key_release)

    # プロパティの定義 --------------------------------------------------
    @property
    def state(self):
        """
        ゲッター：ズーム操作の現在の状態を返すだけ
        """
        return self._state

    @state.setter
    def state(self, new_state):
        """
        セッター：ズーム操作の状態変更時の処理を一元管理
        引数：new_state（新しい状態）
        """
        # new_state が ZoomState 型かどうかを確認し、違う場合はエラー（TypeError）を発生させる
        if not isinstance(new_state, ZoomState):
            raise TypeError("型 ERROR! : tate must be a ZoomState enum")

        old_state = self._state  # 現在の状態を保存
        if old_state == new_state:  # ズーム操作の状態に変化が無いなら、何もしない
            return
        self._state = new_state  # ズーム操作の状態に変化がある場合は、現在の状態を更新

        # デバッグモードなら、状態遷移に関連するログを出力
        if self._debug:
            self._debug_log_transition(old_state, new_state)

        # 必要に応じて追加処理
        self._on_state_changed(old_state, new_state)

    def _on_state_changed(self, old_state, new_state):
        """
        ズーム操作の状態変更時の追加処理
        今は、メソッド内で引数が未使用
        """
        # サンプル: カーソル更新
        if self._last_motion_event:  # 直前のマウス移動イベントがある場合
            self.update_cursor(self._last_motion_event)  #  カーソルを更新
    # ----------------------------------------------------------------

    def on_press(self, event):
        # _is_valid_event メソッドの戻り値が true ではない場合はメソッドを終了
        if not self._is_valid_event(event):
            return

        # 状態ごとの処理を定義
        state_handlers = {
            ZoomState.NO_ZOOM_RECT: self._handle_no_zoom_rect_press,
            ZoomState.WAIT_NOKEY_ZOOM_RECT_EXISTS: self._handle_zoom_rect_exists_press,
            ZoomState.WAIT_SHIFT_RESIZE: self._handle_resize_press,
            ZoomState.WAIT_ALT_ROTATE: self._handle_rotate_press,
        }

        # 現在の状態に対応するハンドラを実行
        if self.state in state_handlers:
            state_handlers[self.state](event)
        # 他の状態では何もしない
        else:
            pass

        self.update_cursor(event)
        self.canvas.draw()

    def _handle_no_zoom_rect_press(self, event):
        if event.button == 1:
            self.state = ZoomState.CREATE  # 自動でログ記録
            self._begin_zoom_rect_creation(event)
        elif event.button == 2:
            self._cancel_zoom()

    def _handle_zoom_rect_exists_press(self, event):
            if event.button == 1:
                self.state = ZoomState.MOVE  # 自動でログ記録
                self._record_drag_start(event)
            elif event.button == 2:
                self._cancel_zoom()
            elif event.button == 3:
                self._confirm_zoom()

    def _handle_resize_press(self, event):
        if not self._validate_resize_event(event):
            return

        if self._get_pointer_near_corner(event) and event.button == 1:
            self.state = ZoomState.RESIZE
            self.press = self._prepare_resize(event)

    def _handle_rotate_press(self, event):
        if self._get_pointer_near_corner(event) and event.button == 1:
            self.state = ZoomState.ROTATE
            self._initiate_rotation(event)

    def _begin_zoom_rect_creation(self, event):
        """
        ズーム領域の作成開始
        """
        # ズーム領域の開始位置を記録
        self.start_x, self.start_y = event.xdata, event.ydata
        # ズーム領域を作成
        self.rect = patches.Rectangle(
            (self.start_x, self.start_y), 0, 0,  # ズーム領域指定開始時の左上の座標と幅、高さ
            edgecolor='white', facecolor='none', linestyle='solid'
        )
        # ズーム領域をキャンバスに追加
        self.ax.add_patch(self.rect)

    def _cancel_zoom(self):
        """
        直前の描画情報があれば復元、無い場合は領域を削除してコールバックを呼び出す
        """
        if self.state == ZoomState.WAIT_NOKEY_ZOOM_RECT_EXISTS:
            if self.last_rect:
                # 直前の矩形を復元し、prev_zoom_params も更新
                x, y, width, height = self.last_rect
                self.rect.set_xy((x, y))
                self.rect.set_width(width)
                self.rect.set_height(height)
                self.state = ZoomState.WAIT_NOKEY_ZOOM_RECT_EXISTS  # cancel_zoom：ズームキャンセル後、領域無し：WAIT_NOKEY_ZOOM_AREA_EXISTS へ変更
            else:
                self._clear_zoom_rect()
                self.state = ZoomState.NO_ZOOM_RECT  # _cancel_zoom：ズームキャンセル後、領域無し：NO_ZOOM_AREA へ変更
        elif self.state == ZoomState.NO_ZOOM_RECT:
            if self.on_zoom_cancel:
                self.on_zoom_cancel()  # コールバック：MainWindow.on_zoom_cancel を呼ぶ
                self.state = ZoomState.NO_ZOOM_RECT  # _cancel_zoom：ズームキャンセル後、領域無し：NO_ZOOM_AREA へ変更

    def on_motion(self, event):
        # 受け取ったイベント情報を保存
        self._last_motion_event = event

        # _is_valid_event メソッドの返り値が true でない場合は、カーソルを矢印にしてメソッドを終了
        if not self._is_valid_event(event):
            self.canvas.get_tk_widget().config(cursor="arrow")
            return

        # スロットリング処理
        current_time = int(time.time() * 1000)  # 現在時刻をミリ秒単位で取得
        # 前回のモーションイベントからの経過時間がスロットリング時間を超えている場合、メソッドを終了
        if hasattr(self, 'last_motion_time') and current_time - self.last_motion_time < self.motion_throttle_ms:
            return
        self.last_motion_time = current_time  # 現在時刻を更新

        # 状態ごとの更新処理を定義
        state_handlers = {
            ZoomState.CREATE: self._update_zoom_rect,
            ZoomState.MOVE: self._update_zoom_rect_position,
            ZoomState.RESIZE: self._update_zoom_rect_size,
            ZoomState.ROTATE: self._update_zoom_rect_rotate,
        }

        # 矩形プロパティの取得（一度だけ）
        old_props = self._get_zoom_rect_properties()
        changed = False

        # メイン処理
        # ズーム状態と対応する更新メソッドが存在する場合、対応する更新メソッドを実行
        if self.state in state_handlers:
            state_handlers[self.state](event)
            new_props = self._get_zoom_rect_properties()
            changed = old_props != new_props  # 変更があれば True を返す
        elif self.state == ZoomState.WAIT_NOKEY_ZOOM_RECT_EXISTS:
            # カーソルが角付近にある場合、ズーム状態を変更
            if self._get_pointer_near_corner(event):
                if self.key_pressed['shift']:
                    self.state = ZoomState.WAIT_SHIFT_RESIZE
                elif self.key_pressed['alt']:
                    self.state = ZoomState.WAIT_ALT_ROTATE
            new_props = self._get_zoom_rect_properties()
            changed = old_props != new_props  # 変更があれば True を返す

        # カーソル更新と再描画
        self.update_cursor(event)
        if changed:
            self.canvas.draw()

    def _update_zoom_rect(self, event):
        """
        ズーム領域の更新
        """
        # _is_valid_event メソッドの戻り値が true ではない場合はメソッドを終了
        if not self._is_valid_event(event):
            return

        # 差分計算（現在の座標 - 開始座標）
        dx = event.xdata - self.start_x
        dy = event.ydata - self.start_y
        self.rect.set_bounds(
            min(self.start_x, event.xdata),
            min(self.start_y, event.ydata),
            abs(dx),
            abs(dy)
        )

        # キャッシュを確実に無効化
        self._invalidate_rect_cache()

    def _update_zoom_rect_position(self, event):
        """
        ズーム領域の位置の更新
        """
        orig_xy, press_x, press_y = self.press
        dx = event.xdata - press_x
        dy = event.ydata - press_y
        self.rect.set_xy((orig_xy[0] + dx, orig_xy[1] + dy))
        self._invalidate_rect_cache()

    def _update_zoom_rect_size(self, event):
        """
        ズーム領域のサイズ更新
        """
        if not self._validate_resize_event(event):
            return

        if self.press is None or self.rect is None:
            return

        # 変更後（データクラスの属性にアクセス）
        if not isinstance(self.press, ResizeOperationData):
            return

        # 共通メソッドで座標計算
        rect_params = self._calculate_resized_rect(event.xdata, event.ydata)
        if rect_params is None:
            return

        x, y, width, height = rect_params

        # 最小サイズ制限（絶対値で比較）
        width = max(width, self.MIN_RECT_SIZE)
        height = max(height, self.MIN_RECT_SIZE)

        # 矩形の左下座標とサイズを設定
        self.rect.set_bounds(x, y, width, height)
        self._invalidate_rect_cache()
        self.canvas.draw()

    def on_release(self, event):
        if not self._is_valid_event(event):
            return

        # 状態ごとの処理を定義
        state_handlers = {
            ZoomState.CREATE: self._handle_create_release,
            ZoomState.MOVE: self._handle_move_release,
            ZoomState.RESIZE: self._handle_resize_release,
            ZoomState.ROTATE: self._handle_rotate_release,
        }

        # 現在の状態に対応するハンドラを実行
        if self.state in state_handlers:
            state_handlers[self.state](event)
        else:
            # 他の状態では何もしない
            pass

        self.update_cursor(event)
        self.canvas.draw()

    def _handle_create_release(self, event):
        """
        CREATE状態でのリリース処理
        """
        self.press = None
        self._finalize_zoom_rect(event)

    def _handle_move_release(self, event):
        """
        MOVE状態でのリリース処理
        """
        self.press = None
        self.state = ZoomState.WAIT_NOKEY_ZOOM_RECT_EXISTS

    def _handle_resize_release(self, event):
        """
        RESIZE状態でのリリース処理
        """
        self.press = None
        # shift ON なら、WAIT_SHIFT_RESIZE に遷移
        if self.key_pressed['shift']:
            self.state = ZoomState.WAIT_SHIFT_RESIZE
        else:
            self.state = ZoomState.WAIT_NOKEY_ZOOM_RECT_EXISTS

    def _handle_rotate_release(self, event):
        """
        ROTATE状態でのリリース処理
        """
        self.press = None
        # alt ON なら、WAIT_ALT_ROTATE に遷移
        if self.key_pressed['alt']:
            self.state = ZoomState.WAIT_ALT_ROTATE
        else:
            self.state = ZoomState.WAIT_NOKEY_ZOOM_RECT_EXISTS

    def _finalize_zoom_rect(self, event):
        """
        ズーム領域の作成を確定し、最小サイズを保証する
        """
        # 差分計算（現在の座標 - 開始座標）
        dx = event.xdata - self.start_x
        dy = event.ydata - self.start_y

        # ズーム領域の幅か高さが 0 の場合は、ズーム領域をクリア
        if dx == 0 or dy == 0:
            self._clear_zoom_rect()
            self.state = ZoomState.NO_ZOOM_RECT
            return

        # 矩形の仮位置・サイズ計算（最小サイズ適用前）
        new_x = self.start_x if dx > 0 else event.xdata
        new_y = self.start_y if dy > 0 else event.ydata
        width = abs(dx)
        height = abs(dy)

        # 最小サイズ適用（サイズと位置を同時に調整）
        if width < self.MIN_RECT_SIZE:
            width = self.MIN_RECT_SIZE
            new_x = self.start_x - width if dx < 0 else self.start_x  # 左方向ドラッグ時は開始位置から左側に拡張
        if height < self.MIN_RECT_SIZE:
            height = self.MIN_RECT_SIZE
            new_y = self.start_y - height if dy < 0 else self.start_y  # 上方向ドラッグ時は開始位置から上側に拡張

        # 矩形を更新
        self.rect.set_bounds(new_x, new_y, width, height)
        self.state = ZoomState.WAIT_NOKEY_ZOOM_RECT_EXISTS

    def on_key_press(self, event):
        # キーイベントでは event.inaxes や xdata が不要
        if event.key not in ['shift', 'alt']:  # 必要なキーのみ許可
            return

        # キー割り込みは、ズーム領域が有り、かつ shift か alt キーが押された場合のみ実行
        if self.state == ZoomState.WAIT_NOKEY_ZOOM_RECT_EXISTS and event.key in ['shift', 'alt']:

            if not self.key_pressed[self.current_key]:  # キーがまだ押されていない場合のみ処理
                self.key_pressed[self.current_key] = True  # キー状態を「押されている」に更新

                if event.key == 'shift':
                    if self._get_pointer_near_corner(self._last_motion_event):  # マウスカーソルが角許容範囲内の場合
                        self.state = ZoomState.WAIT_SHIFT_RESIZE  # on_key_press：shift ON、カーソルが角許容範囲内：WAIT_SHIFT_RESIZE へ変更

                elif event.key == 'alt':  # alt ON → 回転モードへ（マウスカーソルが角に近いかチェック）
                    if self._get_pointer_near_corner(self._last_motion_event):  # マウスカーソルが角許容範囲内の場合
                        self.state = ZoomState.WAIT_ALT_ROTATE  # on_key_press：alt ON、カーソルが角許容範囲内：WAIT_ALT_ROTATE へ変更

                self.canvas.draw()

        self.update_cursor(self._last_motion_event)

    def on_key_release(self, event):
        # 離されたキーが 'shift' または 'alt' でなければ無視
        if event.key not in ['shift', 'alt']:
            return

        # 直前のマウスイベント情報があるかチェック(カーソル更新のために必要)
        if self._last_motion_event is None:
            return

        # 対応するキーの状態を「離された」 (False) に更新
        if event.key in self.key_pressed:
            self.key_pressed[event.key] = False

        # --- 状態遷移のロジック ---
        state_changed = False # 状態が変わったかどうかのフラグ

        # Shift キーが離された場合
        if event.key == 'shift':
            # リサイズ関連の状態だったら、待機状態に戻す
            if self.state in (ZoomState.WAIT_SHIFT_RESIZE, ZoomState.RESIZE):
                self.state = ZoomState.WAIT_NOKEY_ZOOM_RECT_EXISTS
                state_changed = True

        # Alt キーが離された場合
        elif event.key == 'alt':
            # 回転関連の状態だったら、待機状態に戻す
            if self.state in (ZoomState.WAIT_ALT_ROTATE, ZoomState.ROTATE):
                self.state = ZoomState.WAIT_NOKEY_ZOOM_RECT_EXISTS
                state_changed = True

        # 状態が変わった場合のみログ出力と再描画
        if state_changed:
            # カーソル更新のために self._last_motion_event を使う
            self.update_cursor(self._last_motion_event)
            self.canvas.draw()
        # 状態が変わらなくてもカーソルは更新する可能性がある
        else:
            # カーソル更新のために self._last_motion_event を使う
            self.update_cursor(self._last_motion_event)

        self.update_cursor(event)
        self.canvas.draw()

    def _confirm_zoom(self):
        """
        ズーム領域の情報からズームパラメータを生成しコールバック呼び出す
        """
        if self.rect is None:
            return
        x, y, width, height = self._get_zoom_rect_properties()
        center_x = x + width / 2.0
        center_y = y + height / 2.0
        zoom_params = {
            "center_x": center_x,
            "center_y": center_y,
            "width": abs(width),
            "height": abs(height),
            "rotation": self.angle
        }
        self._clear_zoom_rect()
        if self.on_zoom_confirm:
            self.on_zoom_confirm(zoom_params)
        self.state = ZoomState.NO_ZOOM_RECT  # _confirm_zoom：ズーム確定後：NO_ZOOM_AREA へ変更

    def _clear_zoom_rect(self):
        """
        ズーム矩形を完全にクリア（キャッシュ・状態もリセット）
        """
        # 矩形の削除
        if self.rect is not None:
            self.rect.remove()
            self.rect = None

        # 状態の完全リセット
        self._invalidate_rect_cache()  # キャッシュクリア
        self.last_rect = None  # 直前の矩形情報もクリア
        self.press = None  # ドラッグ情報をリセット
        self.start_x = self.start_y = None  # 開始座標リセット

        # GUIの更新
        self.last_cursor_state = None  # カーソル状態を完全リセット
        self.canvas.get_tk_widget().config(cursor="arrow")
        self.canvas.draw()

    def _cursor_inside_zoom_rect(self, event):
        """
        マウスカーソルが領域内部に在るかどうかを判定する
        :param event:
        :return: マウスカーソルが領域内部に在る場合は True、そうでない場合は False
        """
        if self.rect is None:
            return False  # 領域が存在しない場合は False を返す
        contains, _ = self.rect.contains(event)  # マウスカーソルが領域に含まれるかどうかを判定
        return contains  # マウスカーソルが領域内部に在る場合は True、そうでない場合は False を返す

    def _record_drag_start(self, event):
        """
        移動開始位置を取得する
        :param event:
        :return: 移動開始位置
        """
        self.press = (self.rect.get_xy(), event.xdata, event.ydata)

    def _get_zoom_rect_properties(self):
        """
        矩形の位置とサイズを取得する
        矩形が存在しない場合は None を返す
        戻り値 : 矩形の位置とサイズ
        """
        # 矩形が存在しない場合は None を返す
        if self.rect is None:
            return None

        if self._cached_rect_props is None:  # キャッシュがない場合のみ計算
            x, y = self.rect.get_xy()  # 矩形の位置を取得
            self._cached_rect_props = (x, y, self.rect.get_width(), self.rect.get_height())  # 矩形の位置とサイズをキャッシュ
        return self._cached_rect_props  # キャッシュした情報を返す

    def _get_zoom_rect_center(self):
        x, y, width, height = self._get_zoom_rect_properties()
        return (x + width / 2.0, y + height / 2.0)

    def _get_pointer_near_corner(self, event):
        """
        マウス位置が領域の角に近いかどうかを判定する
        許容範囲 tol = 0.1 * min(width, height)（ただし min が 0 の場合は 0.2）
        :param event:
        :return: マウス位置が領域の角に近い場合は True、そうでない場合は False
        """
        if self.rect is None:
            return False

        x, y, width, height = self._get_zoom_rect_properties()
        # 通常の許容範囲
        tol = 0.1 * min(width, height) if min(width, height) != 0 else 0.2
        corners = [(x, y), (x + width, y), (x, y + height), (x + width, y + height)]
        for cx, cy in corners:
            if np.hypot(event.xdata - cx, event.ydata - cy) < tol:
                return True
        return False

    def _invalidate_rect_cache(self):
        self._cached_rect_props = None  # キャッシュをクリア

    def _prepare_resize(self, event):
        """
        マウス位置から最も近い角を選定し、対角固定のため固定すべき点を求める
        """
        # 領域の現在の位置・サイズを保存
        x, y, width, height = self._get_zoom_rect_properties()
        # 角の名前と座標を取得
        corners = {
            'bottom_left': (x, y),
            'bottom_right': (x + width, y),
            'top_left': (x, y + height),
            'top_right': (x + width, y + height)
        }
#        nearest_corner = None
        min_dist = float('inf')
        nearest_key = None  # 最も近い角の名前を保存する変数
        for key, (cx, cy) in corners.items():
            dist = np.hypot(event.xdata - cx, event.ydata - cy)
            if dist < min_dist:
                min_dist = dist
                nearest_corner = (cx, cy)
                nearest_key = key
        # 固定する対角の点を設定（例：bottom_left の場合は top_right が固定点）
        if nearest_key == 'bottom_left':
            fixed = (x + width, y + height)
        elif nearest_key == 'bottom_right':
            fixed = (x, y + height)
        elif nearest_key == 'top_left':
            fixed = (x + width, y)
        elif nearest_key == 'top_right':
            fixed = (x, y)
        # 変更後（データクラスを返す）
        return ResizeOperationData(
            corner_name=nearest_key,
            fixed_point=fixed,
            original_x=x,
            original_y=y,
            original_width=width,
            original_height=height,
            press_x=event.xdata,
            press_y=event.ydata
        )

    def _validate_resize_event(self, event) -> bool:
        """リサイズ操作の事前チェック"""
        checks = [
            (self.rect is not None, "Zoom rectangle not exists"),
            (isinstance(self.press, ResizeOperationData), "Invalid resize data"),
            (event.xdata is not None, "X coordinate is None"),
            (event.ydata is not None, "Y coordinate is None"),
            (self.state == ZoomState.RESIZE, "Not in resize mode")
        ]

        for condition, error_msg in checks:
            if not condition:
                if self._debug:
                    print(f"[Resize Validation Failed] {error_msg}")
                return False
        return True

    def _initiate_rotation(self, event):
        """
        回転の準備
        """
        cx, cy = self._get_zoom_rect_center()
        initial_angle = np.degrees(np.arctan2(event.ydata - cy, event.xdata - cx))
        self.rot_base = self.angle
        self.press = RotationOperationData(
            center_x=cx,
            center_y=cy,
            initial_angle=initial_angle
        )

    def _calculate_resized_rect(self, current_x: float, current_y: float) -> tuple:
        """
        リサイズ後の矩形座標を計算（共通化されたロジック）
        Returns:
            tuple: (x, y, width, height)
        """
        if not isinstance(self.press, ResizeOperationData):
            return None

        # 固定点と現在の座標から矩形を計算
        fixed_x, fixed_y = self.press.fixed_point

        if self.press.corner_name == 'bottom_left':
            x0, x1 = sorted([current_x, fixed_x])
            y0, y1 = sorted([current_y, fixed_y])
        elif self.press.corner_name == 'bottom_right':
            x0, x1 = sorted([fixed_x, current_x])
            y0, y1 = sorted([current_y, fixed_y])
        elif self.press.corner_name == 'top_left':
            x0, x1 = sorted([current_x, fixed_x])
            y0, y1 = sorted([fixed_y, current_y])
        elif self.press.corner_name == 'top_right':
            x0, x1 = sorted([fixed_x, current_x])
            y0, y1 = sorted([fixed_y, current_y])
        else:
            return None

        return (x0, y0, x1 - x0, y1 - y0)


    def _update_zoom_rect_rotate(self, event):
        """
        ズーム領域の回転の更新（キャッシュ対応・安全性強化版）
        """
        # イベントと矩形の有効性チェック
        if (self.press is None or
            not isinstance(self.press, RotationOperationData) or
            self.rect is None or
            None in (event.xdata, event.ydata)):
            return

        # 回転中心と現在角度を計算
        cx = self.press.center_x
        cy = self.press.center_y
        initial_angle = self.press.initial_angle

        current_angle = np.degrees(np.arctan2(
            event.ydata - cy,
            event.xdata - cx
        ))

        # 角度差分を計算（-180°~180°に正規化）
        angle_diff = (current_angle - initial_angle) % 360
        if angle_diff > 180:
            angle_diff -= 360

        # 角度の急激な変化を防ぐためのスムージング
        smoothing_factor = 0.8
        smoothed_angle_diff = angle_diff * smoothing_factor

        # 新しい角度を設定
        self.angle = (self.rot_base + smoothed_angle_diff) % 360

        # アフィン変換を適用
        t = transforms.Affine2D().rotate_deg_around(cx, cy, self.angle)
        self.rect.set_transform(t + self.ax.transData)

        # キャッシュ無効化と再描画
        self._invalidate_rect_cache()
        self.canvas.draw()

    def _is_valid_event(self, event):
        """
        イベントの有効性をチェック
        """
        # 以下の４つの条件を全て満たす場合に、True を返す
            # event に xdata の属性がある
            # event に ydata の属性がある
            # event.xdata が None ではない
            # event.ydata が None ではない
        # これにより、イベントが マウスカーソルの位置を持っているかどうかを判定できる
        # hasattr は、オブジェクトが特定の属性（プロパティ）を持っているかどうかを確認するための組み込み関数
        has_valid_coords = (
            hasattr(event, 'xdata') and
            hasattr(event, 'ydata') and
            event.xdata is not None and
            event.ydata is not None
        )
        # ズーム領域がない場合
        if self.state == ZoomState.NO_ZOOM_RECT:
            # 以下の３つの条件を全て満たす場合に、True を返す
                # event に inaxes（イベントが発生した軸）がある
                # event.inaxes が self.ax（現在の描画エリア）と一致する
                # event.xdata と event.ydata が None ではなく有効な値を持つ
            # つまり、マウスの座標が有効で、イベントが self.ax 内で発生していれば True を返す
            return hasattr(event, 'inaxes') and event.inaxes == self.ax and has_valid_coords
        # ズーム領域がある場合
        else:
            # 以下の４つの条件を全て満たす場合に、True を返す
                # event に inaxes（イベントが発生した軸）がある
                # event.inaxes が self.ax（現在の描画エリア）と一致する
                # event.xdata と event.ydata が None ではなく有効な値を持つ
                # self.rect が None ではなく、有効な値を持つ
            return hasattr(event, 'inaxes') and event.inaxes == self.ax and has_valid_coords and self.rect is not None

    def update_cursor(self, event):
        """
        各状態およびカーソル位置に応じたカーソル形状を設定する
        """
        if not hasattr(event, 'xdata') or event.xdata is None or not hasattr(event, 'ydata') or event.ydata is None:
            self.canvas.get_tk_widget().config(cursor="arrow")
            return

        new_cursor = "arrow"
        if self.state in (ZoomState.NO_ZOOM_RECT, ZoomState.CREATE):  # update_cursor：NO_ZOOM_AREA か CREATE 場合の処理
            new_cursor = "arrow"
        elif self.state == ZoomState.MOVE:  # update_cursor：MOVE の場合の処理
            new_cursor = "fleur"
        # WAIT_SHIFT_RESIZE か RESIZE の場合は、角近傍なら crosshair、それ以外は arrow
        elif self.state in (ZoomState.WAIT_SHIFT_RESIZE, ZoomState.RESIZE):  # update_cursor：WAIT_SHIFT_RESIZE ＆ RESIZE の場合の処理
            new_cursor = "crosshair" if self._get_pointer_near_corner(event) else "arrow"
        # WAIT_ALT_ROTATE か ROTATE の場合は、角近傍なら exchange、それ以外は arrow
        elif self.state in (ZoomState.WAIT_ALT_ROTATE, ZoomState.ROTATE):  # update_cursor：WAIT_ALT_ROTATE ＆ ROTATE の場合の処理
            new_cursor = "exchange" if self._get_pointer_near_corner(event) else "arrow"
        elif self.state == ZoomState.WAIT_NOKEY_ZOOM_RECT_EXISTS:  # update_cursor：WAIT_NOKEY_ZOOM_AREA_EXISTSの場合の処理
            new_cursor = "fleur" if self._cursor_inside_zoom_rect(event) else "arrow"
        else:
            new_cursor = "arrow"

        if new_cursor != self.last_cursor_state:  # 変更が有る場合のみ更新
            self.canvas.get_tk_widget().config(cursor=new_cursor)  # カーソルの形状を更新
            self.last_cursor_state = new_cursor  # カーソルの形状を更新

    def _debug_log_transition(self, old_state, new_state):
        """
        状態遷移のログを出力する
        """
        # self._debug（デバッグモード）が true ではない場合、メソッドを終了
        if not self._debug:
            return

        # None値に対応したフォーマット
        # start_x と start_y が None でない場合
        # 小数点1桁でフォーマット（start_x=12.3456, start_y=78.9 の場合 → "(12.3, 78.9)"）
        # どちらかが None の場合は "None" とする
            # Python では、A if 条件 else B の形式のコードがあるとき
            # 条件が True の場合は A が処理され、False の場合は B が処理される
        mouse_pos = (
            f"({self.start_x:.1f}, {self.start_y:.1f})"
            if self.start_x is not None and self.start_y is not None
            else "None"
        )

        rect_props = self._get_zoom_rect_properties()  #  矩形のプロパティを取得
        rect_str = f"{rect_props}" if rect_props else "None"  # 矩形のプロパティがあれば、それを文字列に変換
        key_status = f"shift: {self.key_pressed['shift']}, alt: {self.key_pressed['alt']}"  # キーの状態を文字列に変換

        # リサイズ関連の追加情報
        resize_info = ""  # 内容をクリア
        if self.press and isinstance(self.press, ResizeOperationData):  # リサイズ操作中の場合
            corner_name = self.press.corner_name
            fixed_x, fixed_y = self.press.fixed_point
            resize_info = (
                f"\n  - Resize Debug:\n"
                f"    - corner: {corner_name}\n"
                f"    - fixed_point: ({fixed_x:.1f}, {fixed_y:.1f})\n"
                f"    - original_size: {self.press.original_width:.1f}x{self.press.original_height:.1f}\n"
                f"    - press_pos: ({self.press.press_x:.1f}, {self.press.press_y:.1f})"
            )

        # イベント座標（可能なら）
        event_pos = ""  # 内容をクリア
        if hasattr(self, '_last_event') and self._last_motion_event:  # イベントが存在し、かつ、最後のモーションイベントが存在する場合
            e = self._last_motion_event
            event_pos = f"\n  - event_pos: ({e.xdata:.1f}, {e.ydata:.1f})"

        key_status = f"shift: {self.key_pressed['shift']}, alt: {self.key_pressed['alt']}"

        print(
            f"State changed: {old_state.name} → {new_state.name}\n"
            f"  - mouse_pos: {mouse_pos}\n"
            f"  - key_pressed: {key_status}\n"
            f"  - Rect: {rect_str}"
            f"{resize_info}"
            f"{event_pos}"
        )
