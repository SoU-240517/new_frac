# インポート
import numpy as np
import matplotlib.patches as patches
import matplotlib.transforms as transforms
from enum import Enum, auto
import time  # スロットリング用の時間処理モジュール

class ZoomState(Enum):                    # ズーム操作の状態を表す列挙型
    NO_ZOOM_AREA = auto()                 # ズーム領域無し（領域が存在しない）
    CREATE = auto()                       # ズーム領域新規作成モード（左ボタン ONで開始）
    WAIT_NOKEY_ZOOM_AREA_EXISTS = auto()  # ズーム領域有り（キー入力無し）
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
        self.state = ZoomState.NO_ZOOM_AREA  # 初期状態：NO_ZOOM_AREA を設定
        self.rect = None         # 現在のズーム領域（情報があれば領域有り）
        self.last_rect = None    # 直前のズーム領域（キャンセル用）
        self.press = None        # ドラッグ開始時の情報（移動・リサイズ・回転共通）
        self.start_x = None      # 新規作成開始時の x 座標
        self.start_y = None      # 新規作成開始時の y 座標
        self.current_key = None  # 現在 ON のキー（'shift' または 'alt'）
        self.key_pressed = {'shift': False, 'alt': False}  # キー状態追跡用の変数を追加
        self.angle = 0.0         # 現在の回転角（度）
        self.rot_base = 0.0      # 回転開始時の角度
        self.last_cursor_state = "arrow"

        self._debug = True  # デバッグモードフラグ
        self._cached_rect_props = None  # キャッシュ用変数

        self.last_motion_time = int(time.time() * 1000)  # 初期値を設定
        self.motion_throttle_ms = 30  # 30ミリ秒ごとに処理（約33fps）

        # イベントハンドラ接続
        self.cid_press       = self.canvas.mpl_connect('button_press_event', self.on_press)
        self.cid_release     = self.canvas.mpl_connect('button_release_event', self.on_release)
        self.cid_motion      = self.canvas.mpl_connect('motion_notify_event', self.on_motion)
        self.cid_key_press   = self.canvas.mpl_connect("key_press_event", self.on_key_press)
        self.cid_key_release = self.canvas.mpl_connect("key_release_event", self.on_key_release)

    def on_press(self, event):
        if not self._is_valid_event(event):
            return

        # 状態ごとの処理を定義
        state_handlers = {
            ZoomState.NO_ZOOM_AREA: self._handle_no_zoom_area_press,
            ZoomState.WAIT_NOKEY_ZOOM_AREA_EXISTS: self._handle_zoom_area_exists_press,
            ZoomState.WAIT_SHIFT_RESIZE: self._handle_resize_press,
            ZoomState.WAIT_ALT_ROTATE: self._handle_rotate_press,
        }

        # 現在の状態に対応するハンドラを実行
        if self.state in state_handlers:
            state_handlers[self.state](event)
        else:
            # CREATE/MOVE/RESIZE/ROTATE状態では特別な処理は不要
            pass

        self.update_cursor(event)
        self.canvas.draw()

    def on_motion(self, event):
        if not self._is_valid_event(event):
            self.canvas.get_tk_widget().config(cursor="arrow")
            return

        # スロットリング処理
        current_time = int(time.time() * 1000)
        if hasattr(self, 'last_motion_time') and current_time - self.last_motion_time < self.motion_throttle_ms:
            return
        self.last_motion_time = current_time

        # 状態ごとの更新処理を定義
        state_handlers = {
            ZoomState.CREATE: self._update_zoom_area,
            ZoomState.MOVE: self._update_zoom_position,
            ZoomState.RESIZE: self._update_zoom_size,
            ZoomState.ROTATE: self._update_zoom_rotate,
        }

        # 矩形プロパティの取得（一度だけ）
        old_props = self._get_rect_properties()
        changed = False

        # メイン処理
        if self.state in state_handlers:
            # 状態に対応する更新メソッドを実行
            state_handlers[self.state](event)
            new_props = self._get_rect_properties()
            changed = old_props != new_props

        elif self.state == ZoomState.WAIT_NOKEY_ZOOM_AREA_EXISTS:
            # 状態遷移のチェック
            if self._get_pointer_near_corner(event):
                if self.current_key == 'shift':
                    old_state = self.state
                    self.state = ZoomState.WAIT_SHIFT_RESIZE
                    self._log_state_change(old_state, self.state)
                elif self.current_key == 'alt':
                    old_state = self.state
                    self.state = ZoomState.WAIT_ALT_ROTATE
                    self._log_state_change(old_state, self.state)

            new_props = self._get_rect_properties()
            changed = old_props != new_props

        # カーソル更新と再描画
        self.update_cursor(event)
        if changed:
            self.canvas.draw()

    def on_release(self, event):
        if not self._is_valid_event(event):
            return

        if self.state == ZoomState.CREATE:  # on_release：CREATE が完了した場合の処理
            self.press = None
            self._fix_create_zoom_rectangle(event)

        elif self.state == ZoomState.MOVE:  # on_release：MOVE が完了の場合の処理
            self.press = None
            old_state = self.state
            self.state = ZoomState.WAIT_NOKEY_ZOOM_AREA_EXISTS  # on_release：移動完了：WAIT_NOKEY_ZOOM_AREA_EXISTS へ変更
            self._log_state_change(old_state, self.state)

        elif self.state == ZoomState.RESIZE:  # on_release：RESIZE が完了した場合の処理
            self.press = None
            # shift ON なら、WAIT_SHIFT_RESIZE に遷移
            if event.key == 'shift':
                old_state = self.state
                self.state = ZoomState.WAIT_SHIFT_RESIZE  # on_release：リサイズ完了、shift ON：WAIT_SHIFT_RESIZE へ変更
                self._log_state_change(old_state, self.state)
            else:
                old_state = self.state
                self.state = ZoomState.WAIT_NOKEY_ZOOM_AREA_EXISTS  # on_release：リサイズ完了、shift OFF：WAIT_NOKEY_ZOOM_AREA_EXISTS へ変更
                self._log_state_change(old_state, self.state)

        elif self.state == ZoomState.ROTATE:  # on_release：ROTATE が完了した場合の処理
            self.press = None
            # alt ON なら、WAIT_ALT_ROTATE に遷移
            if event.key == 'alt':
                old_state = self.state
                self.state = ZoomState.WAIT_ALT_ROTATE  # on_release：回転完了、alt ON：WAIT_ALT_ROTATE へ変更
                self._log_state_change(old_state, self.state)
            else:
                old_state = self.state
                self.state = ZoomState.WAIT_NOKEY_ZOOM_AREA_EXISTS  # on_release：回転完了、alt OFF：WAIT_NOKEY_ZOOM_AREA_EXISTS へ変更
                self._log_state_change(old_state, self.state)

        self.update_cursor(event)
        self.canvas.draw()

    def on_key_press(self, event):
        # キーイベントでは event.inaxes や xdata が不要
        if event.key not in ['shift', 'alt']:  # 必要なキーのみ許可
            return

        # キー割り込みは、ズーム領域が有り、かつ shift か alt キーが押された場合のみ実行
        if self.state == ZoomState.WAIT_NOKEY_ZOOM_AREA_EXISTS and event.key in ['shift', 'alt']:
            self.current_key = event.key  # 「現在のキー」を「押されているキー」で更新

            if not self.key_pressed[self.current_key]:  # キーがまだ押されていない場合のみ処理
                self.key_pressed[self.current_key] = True  # キー状態を「押されている」に更新

                if self.current_key == 'shift':
#                    print(f"pointer_near_corner/on_key_press: {self._get_pointer_near_corner(event)}")
#                    print(f"state前/on_key_press: {self.state}")
                    if self._get_pointer_near_corner(event):  # マウスカーソルが角許容範囲内の場合
                        old_state = self.state
                        self.state = ZoomState.WAIT_SHIFT_RESIZE  # on_key_press：shift ON、カーソルが角許容範囲内：WAIT_SHIFT_RESIZE へ変更
                        self._log_state_change(old_state, self.state)

                elif self.current_key == 'alt':  # alt ON → 回転モードへ（マウスカーソルが角に近いかチェック）
                    if self._get_pointer_near_corner(event):  # マウスカーソルが角許容範囲内の場合
                        old_state = self.state
                        self.state = ZoomState.WAIT_ALT_ROTATE  # on_key_press：alt ON、カーソルが角許容範囲内：WAIT_ALT_ROTATE へ変更
                        self._log_state_change(old_state, self.state)

                self.canvas.draw()

        self.update_cursor(event)

    def on_key_release(self, event):
        if event.key != getattr(self, 'current_key', None):  # 現在のキーと一致するか
            return

        if event.key in ['shift', 'alt']:
            self.current_key = event.key
            self.key_pressed[self.current_key] = False  # そのキーだけを「離された」状態に更新
            self.current_key = None
            if self.state in (ZoomState.WAIT_SHIFT_RESIZE, ZoomState.RESIZE, ZoomState.WAIT_ALT_ROTATE, ZoomState.ROTATE):  # キー割り込みで入ったモードの場合、解除して待機状態へ戻す
                old_state = self.state
                self.state = ZoomState.WAIT_NOKEY_ZOOM_AREA_EXISTS  # on_key_release：キー割り込みが解除された場合：WAIT_NOKEY_ZOOM_AREA_EXISTS へ変更
                self._log_state_change(old_state, self.state)

        self.update_cursor(event)
        self.canvas.draw()

    def _handle_no_zoom_area_press(self, event):
        if event.button == 1:  # 左クリック
            old_state = self.state
            self.state = ZoomState.CREATE
            self._log_state_change(old_state, self.state)
            self._start_create_zoom_rectangle(event)
        elif event.button == 2:  # 中クリック
            self._handle_cancel_zoom()

    def _handle_zoom_area_exists_press(self, event):
        if self._cursor_inside_rect(event):
            if event.button == 1:  # 左クリック
                old_state = self.state
                self.state = ZoomState.MOVE
                self._log_state_change(old_state, self.state)
                self._start_create_zoom_rectangle(event)
                self._get_move_start_position(event)
            elif event.button == 2:  # 中クリック
                self._handle_cancel_zoom()
            elif event.button == 3:  # 右クリック
                self._handle_confirm_zoom()

    def _handle_resize_press(self, event):
        if self._get_pointer_near_corner(event) and event.button == 1:
            old_state = self.state
            self.state = ZoomState.RESIZE
            self._log_state_change(old_state, self.state)
            self._start_create_zoom_rectangle(event)
            self.press = self._prepare_resize(event)

    def _handle_rotate_press(self, event):
        if self._get_pointer_near_corner(event) and event.button == 1:
            old_state = self.state
            self.state = ZoomState.ROTATE
            self._log_state_change(old_state, self.state)
            self._start_create_zoom_rectangle(event)
            self._prepare_rotation(event)

    def _handle_confirm_zoom(self):
        """
        ズーム領域の情報からズームパラメータを生成しコールバック呼び出す
        """
        if self.rect is None:
            return
        x, y, width, height = self._get_rect_properties()
        center_x = x + width / 2.0
        center_y = y + height / 2.0
        zoom_params = {
            "center_x": center_x,
            "center_y": center_y,
            "width": abs(width),
            "height": abs(height),
            "rotation": self.angle
        }
        self._clear_zoom_rectangle()
        if self.on_zoom_confirm:
            self.on_zoom_confirm(zoom_params)
        old_state = self.state
        self.state = ZoomState.NO_ZOOM_AREA  # _clear_zoom_rectangle：ズーム確定後：NO_ZOOM_AREA へ変更
        self._log_state_change(old_state, self.state)

    def _handle_cancel_zoom(self):
        """
        直前の描画情報があれば復元、無い場合は領域を削除してコールバックを呼び出す
        """
        # 直前の領域と現在の領域が在る場合、直前の領域を復元
        if self.last_rect and self.rect:
            x, y, width, height = self.last_rect
            self.rect.set_xy((x, y))
            self.rect.set_width(width)
            self.rect.set_height(height)
            old_state = self.state
            self.state = ZoomState.WAIT_NOKEY_ZOOM_AREA_EXISTS  # _handle_cancel_zoom：ズームキャンセル後、領域無し：WAIT_NOKEY_ZOOM_AREA_EXISTS へ変更
            self._log_state_change(old_state, self.state)
        else:  # 直前の領域がない場合、領域を削除してコールバックを呼び出す
            self._clear_zoom_rectangle()
            if self.on_zoom_cancel:
                self.on_zoom_cancel()  # コールバック呼び出し（main_window.py）
                old_state = self.state
                self.state = ZoomState.NO_ZOOM_AREA  # _handle_cancel_zoom：ズームキャンセル後、領域無し：NO_ZOOM_AREA へ変更
                self._log_state_change(old_state, self.state)

    def _start_create_zoom_rectangle(self, event):
        """
        ズーム領域の作成開始
        :param event:
        :return:
        """
        self.start_x, self.start_y = event.xdata, event.ydata
        self.rect = patches.Rectangle(
            (self.start_x, self.start_y), 0, 0,
            edgecolor='white', facecolor='none', linestyle='solid'
        )
        self.ax.add_patch(self.rect)

    def _fix_create_zoom_rectangle(self, event):
        """
        ズーム領域の作成完了
        :param event:
        :return:
        """
        dx = event.xdata - self.start_x
        dy = event.ydata - self.start_y
        if dx != 0 and dy != 0:
            new_x = min(self.start_x, event.xdata)
            new_y = min(self.start_y, event.ydata)
            self.rect.set_xy((new_x, new_y))
            self.rect.set_width(abs(dx))
            self.rect.set_height(abs(dy))
            old_state = self.state
            self.state = ZoomState.WAIT_NOKEY_ZOOM_AREA_EXISTS  # _fix_create_zoom_rectangle：領域作成完了：WAIT_NOKEY_ZOOM_AREA_EXISTS へ変更
            self._log_state_change(old_state, self.state)
        else:
            self._clear_zoom_rectangle()
            old_state = self.state
            self.state = ZoomState.NO_ZOOM_AREA  # _fix_create_zoom_rectangle：領域が未作成：NO_ZOOM_AREA へ変更
            self._log_state_change(old_state, self.state)

    def _clear_zoom_rectangle(self):
        """
        ズーム矩形を完全にクリア（キャッシュ・状態もリセット）
        :param event:
        :return:
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

    def _cursor_inside_rect(self, event):
        """
        マウスカーソルが領域内部に在るかどうかを判定する
        :param event:
        :return: マウスカーソルが領域内部に在る場合は True、そうでない場合は False
        """
        if self.rect is None:
            return False  # 領域が存在しない場合は False を返す
        contains, _ = self.rect.contains(event)  # マウスカーソルが領域に含まれるかどうかを判定
        return contains  # マウスカーソルが領域内部に在る場合は True、そうでない場合は False を返す

    def _get_move_start_position(self, event):
        """
        移動開始位置を取得する
        :param event:
        :return: 移動開始位置
        """
        self.press = (self.rect.get_xy(), event.xdata, event.ydata)

    def _get_rect_center(self):
        x, y, width, height = self._get_rect_properties()
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

        x, y, width, height = self._get_rect_properties()
        # 通常の許容範囲
        tol = 0.1 * min(width, height) if min(width, height) != 0 else 0.2
        corners = [(x, y), (x + width, y), (x, y + height), (x + width, y + height)]
        for cx, cy in corners:
            if np.hypot(event.xdata - cx, event.ydata - cy) < tol:
                return True
        return False

    def _get_rect_properties(self):
        """
        矩形の位置とサイズを取得する。矩形が存在しない場合はNoneを返す
        :param event:
        :return: 矩形の位置とサイズ
        """
        if self.rect is None:
            return None

        if self._cached_rect_props is None:  # キャッシュがない場合のみ計算
            x, y = self.rect.get_xy()
            self._cached_rect_props = (x, y, self.rect.get_width(), self.rect.get_height())
        return self._cached_rect_props  # キャッシュがあればそのまま返す

    def _invalidate_rect_cache(self):
        self._cached_rect_props = None  # キャッシュをクリア

    def _prepare_resize(self, event):
        """
        マウス位置から最も近い角を選定し、対角固定のため固定すべき点を求める
        :param event:
        :return: 固定する対角の点
        """
        # 領域の現在の位置・サイズを保存
        x, y, width, height = self._get_rect_properties()
        # 角の名前と座標を取得
        corners = {
            'bottom_left': (x, y),
            'bottom_right': (x + width, y),
            'top_left': (x, y + height),
            'top_right': (x + width, y + height)
        }
        nearest_corner = None
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
        return (nearest_key, fixed, x, y, width, height, event.xdata, event.ydata)

    def _prepare_rotation(self, event):
        """
        回転の準備
        :param event:
        :return:
        """
        cx, cy = self._get_rect_center()
        initial_angle = np.degrees(np.arctan2(event.ydata - cy, event.xdata - cx))
        self.rot_base = self.angle
        self.press = (cx, cy, initial_angle)

    def _update_zoom_area(self, event):
        """
        ズーム領域の更新
        :param event:
        :return:
        """
        # イベントデータの有効性チェック
        if None in (event.xdata, event.ydata) or self.rect is None:
            return

        # 差分計算（dx/dyが0の場合の最小サイズ対策）
        dx = event.xdata - self.start_x
        dy = event.ydata - self.start_y

        # 最小サイズ制限（例: 0.1ピクセル以上）
        min_size = 0.1
        abs_dx = max(abs(dx), min_size)
        abs_dy = max(abs(dy), min_size)

        # 矩形の左上座標決定
        new_x = min(self.start_x, event.xdata)
        new_y = min(self.start_y, event.ydata)

        # 矩形更新（set_boundsで一括処理）
        self.rect.set_bounds(new_x, new_y, abs_dx, abs_dy)
        self._invalidate_rect_cache()  # キャッシュを確実に無効化

    def _update_zoom_position(self, event):
        """
        ズーム領域の位置の更新
        :param event:
        :return:
        """
        orig_xy, press_x, press_y = self.press
        dx = event.xdata - press_x
        dy = event.ydata - press_y
        self.rect.set_xy((orig_xy[0] + dx, orig_xy[1] + dy))
        self._invalidate_rect_cache()

    def _update_zoom_size(self, event):
        """
        ズーム領域のサイズ更新
        :param event:
        :return:
        """
        # press が None の場合か、rect が None の場合はメソッドを終了
        if self.press is None or self.rect is None:
            return

        # xdata か ydata が None の場合はメソッドを終了
        if event.xdata is None or event.ydata is None:
            return

        (corner_name, fixed, orig_x, orig_y, orig_width, orig_height, press_x, press_y) = self.press

        # 固定点と現在のマウス位置
        fixed_x, fixed_y = fixed
        current_x, current_y = event.xdata, event.ydata

        # マウスの移動方向に応じて新しい座標を計算
        if corner_name == 'bottom_left':
            new_x, new_y = current_x, current_y
            new_width, new_height = fixed_x - current_x, fixed_y - current_y
        elif corner_name == 'bottom_right':
            new_x, new_y = fixed_x, current_y
            new_width, new_height = current_x - fixed_x, fixed_y - current_y
        elif corner_name == 'top_left':
            new_x, new_y = current_x, fixed_y
            new_width, new_height = fixed_x - current_x, current_y - fixed_y
        elif corner_name == 'top_right':
            new_x, new_y = fixed_x, fixed_y
            new_width, new_height = current_x - fixed_x, current_y - fixed_y

        # 最小サイズ制限
        min_size = 1.0
        new_width = max(abs(new_width), min_size) * (1 if new_width >= 0 else -1)
        new_height = max(abs(new_height), min_size) * (1 if new_height >= 0 else -1)

        # 矩形を更新（左下座標とサイズをまとめて設定）
        self.rect.set_bounds(new_x, new_y, new_width, new_height)

        # ★キャッシュ無効化の追加
        self._invalidate_rect_cache()

        # 再描画
        self.canvas.draw()

    def _update_zoom_rotate(self, event):
        """
        ズーム領域の回転の更新（キャッシュ対応・安全性強化版）
        :param event:
        :return:
        """
        # イベントと矩形の有効性チェック
        if (self.press is None or
            self.rect is None or
            None in (event.xdata, event.ydata)):
            return

        # 回転中心と現在角度を計算
        cx, cy, initial_angle = self.press
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
        :param event:
        :return:
        """
        has_valid_coords = (
            hasattr(event, 'xdata') and
            hasattr(event, 'ydata') and
            event.xdata is not None and
            event.ydata is not None
        )

        # 状態に応じた条件分岐
        if self.state == ZoomState.NO_ZOOM_AREA:
            return hasattr(event, 'inaxes') and event.inaxes == self.ax and has_valid_coords
        else:
            return (hasattr(event, 'inaxes') and
                    event.inaxes == self.ax and
                    has_valid_coords and
                    self.rect is not None)

    def _log_state_change(self, old_state, new_state):
        """状態変化を安全にログ出力"""
        if not self._debug or old_state == new_state:
            return

        # None値に対応したフォーマット
        mouse_pos = (
            f"({self.start_x:.1f}, {self.start_y:.1f})"
            if self.start_x is not None and self.start_y is not None
            else "None"
        )

        print(
            f"State changed: {old_state.name} → {new_state.name}\n"
            f"  - Mouse: {mouse_pos}\n"
            f"  - Key: {self.current_key or 'None'}\n"
            f"  - Rect: {self._get_rect_properties() or 'None'}"
        )

    def update_cursor(self, event):
        """
        各状態およびカーソル位置に応じたカーソル形状を設定する
        :param event:
        :return:
        """
        if not hasattr(event, 'xdata') or event.xdata is None or not hasattr(event, 'ydata') or event.ydata is None:
            self.canvas.get_tk_widget().config(cursor="arrow")
            return

#        print(f"pointer_near_corner: {self._get_pointer_near_corner(event)}")
        new_cursor = "arrow"
        if self.state in (ZoomState.NO_ZOOM_AREA, ZoomState.CREATE):  # update_cursor：NO_ZOOM_AREA か CREATE 場合の処理
            new_cursor = "arrow"
        elif self.state == ZoomState.MOVE:  # update_cursor：MOVE の場合の処理
            new_cursor = "fleur"
        # WAIT_SHIFT_RESIZE か RESIZE の場合は、角近傍なら crosshair、それ以外は arrow
        elif self.state in (ZoomState.WAIT_SHIFT_RESIZE, ZoomState.RESIZE):  # update_cursor：WAIT_SHIFT_RESIZE ＆ RESIZE の場合の処理
            new_cursor = "crosshair" if self._get_pointer_near_corner(event) else "arrow"
        # WAIT_ALT_ROTATE か ROTATE の場合は、角近傍なら exchange、それ以外は arrow
        elif self.state in (ZoomState.WAIT_ALT_ROTATE, ZoomState.ROTATE):  # update_cursor：WAIT_ALT_ROTATE ＆ ROTATE の場合の処理
            new_cursor = "exchange" if self._get_pointer_near_corner(event) else "arrow"
        elif self.state == ZoomState.WAIT_NOKEY_ZOOM_AREA_EXISTS:  # update_cursor：WAIT_NOKEY_ZOOM_AREA_EXISTSの場合の処理
            new_cursor = "fleur" if self._cursor_inside_rect(event) else "arrow"
        else:
            new_cursor = "arrow"

        if new_cursor != self.last_cursor_state:  # 変更が有る場合のみ更新
            self.canvas.get_tk_widget().config(cursor=new_cursor)
            self.last_cursor_state = new_cursor  # カーソルの形状を更新
