from dataclasses import dataclass
import numpy as np
import matplotlib.patches as patches
import matplotlib.transforms as transforms
from enum import Enum, auto
import time  # 時間処理モジュール
from typing import Optional, Dict, Any

@dataclass
class ResizeOperationData:
    """ズーム領域のリサイズ時の列挙型"""
    corner_name: str                  # 操作中の角（'bottom_left'など）
    fixed_point: tuple[float, float]  # 固定される対角の座標
    original_x: float                 # ズーム領域の元のx座標
    original_y: float                 # ズーム領域の元のy座標
    original_width: float             # ズーム領域の元の幅
    original_height: float            # ズーム領域の元の高さ
    press_x: float                    # ドラッグ開始時のx座標
    press_y: float                    # ドラッグ開始時のy座標

@dataclass
class RotationOperationData:
    """ズーム領域の回転時の列挙型"""
    center_x: float       # 中心点のx座標
    center_y: float       # 中心点のy座標
    initial_angle: float  # 回転開始時の角度

class LogLevel(Enum):
    """ログレベルを表す列挙型"""
    DEBUG = auto()  # 開発中の詳細な変数確認（マウス座標の細かい変化、計算途中の値とか）
    INFO = auto()  # 正常系の重要な状態変化（ズーム領域の確定、状態遷移とか）
    WARNING = auto()  # 想定外だが処理は継続可能な問題（最小サイズ未満の入力、許容範囲外の座標とか）
    ERROR = auto()  # 処理継続不可能な重大なエラー（不正な状態遷移、NULL参照エラーとか）

class DebugLogger:
    """デバッグログ出力を一元管理するクラス"""
    def __init__(self, debug_enabled: bool = True):
        self.debug_enabled = debug_enabled
        self.last_log_time = 0
        self.log_throttle_ms = 100  # ログのスロットリング間隔(ms)
        self.min_level = LogLevel.DEBUG

    def log(self,
            level: LogLevel,
            message: str,
            context: Optional[Dict[str, Any]] = None,
            force: bool = False) -> None:
        """
        デバッグログを出力する
        Args:
            level: ログレベル
            message: メッセージ本文
            context: 追加コンテキスト情報(dict)
            force: スロットリングを無視して強制出力
        """
        if level.value < self.min_level.value:  # ログレベルが最小レベルより低い場合、メソッドを終了
            return

        if not self.debug_enabled and not force:  # デバッグモードが無効、かつ、強制出力でない場合は、メソッドを終了
            return

        current_time = int(time.time() * 1000)  # スロットリングチェック
        if not force and current_time - self.last_log_time < self.log_throttle_ms:
            return
        self.last_log_time = current_time

        # デバッグログのフォーマット
        timestamp = time.strftime("%H:%M:%S", time.localtime())
        level_str = level.name.ljust(7)
        log_entry = f"[{timestamp}] {level_str} - {message}"
        if context:
            log_entry += "\n" + self._format_context(context)

        print(log_entry)

    def _format_context(self, context: Dict[str, Any]) -> str:
        """コンテキスト情報を整形して文字列に変換"""
        lines = []
        for key, value in context.items():
            if isinstance(value, (int, float)):
                formatted = f"{value:.2f}" if isinstance(value, float) else str(value)
            elif isinstance(value, Enum):
                formatted = value.name
            elif value is None:
                formatted = "None"
            else:
                formatted = str(value)
            lines.append(f"  - {key}: {formatted}")

        return "\n".join(lines)

class ZoomState(Enum):
    """ズーム操作の状態を表す列挙型"""
    NO_RECT = auto()           # ズーム領域なし
    CREATE = auto()            # ズーム領域の新規作成モード
    WAIT_RECT_EXISTS = auto()  # ズーム領域あり
    MOVE = auto()              # ズーム領域移動モード
    WAIT_RESIZE = auto()       # リサイズ待機モード（shift ON）
    RESIZE = auto()            # リサイズモード（shift＋左ドラッグ）
    WAIT_ROTATE = auto()       # 回転待機モード（alt ON）
    ROTATE = auto()            # 回転モード（alt＋左ドラッグ）

class ZoomSelector:
    def __init__(self, ax, on_zoom_confirm, on_zoom_cancel):
        """
        ズームセレクターのインスタンスを作成する
        Args:
            ax: 対象の matplotlib Axes
            on_zoom_confirm: ズーム確定時のコールバック（zoom_params を引数に取る）
            on_zoom_cancel: ズームキャンセル時のコールバック
        """
        print("START : __init__.ZoomSelector")
        self.ax = ax
        self.canvas = ax.figure.canvas
        self.on_zoom_confirm = on_zoom_confirm
        self.on_zoom_cancel = on_zoom_cancel
        self.rect = None  # ズーム領域：現在（構造は matplotlib.patches.Rectangle）
        self.last_rect = None  # ズーム領域：直前
        self.angle = 0.0  # 現在の回転角（度）
        self.rot_base = 0.0  # 回転開始時の角度
        self._cached_rect_props = None  # ズーム領域のプロパティをキャッシュ
        self.press = None  # マウス押下時のデータ（構造は ResizeOperationData または RotationOperationData）
        self._last_motion_event = None  # 直前のマウス移動イベント
        self.drag_direction = None  # ドラッグ方向
        self.start_x = None  # 新規作成開始時の x 座標
        self.start_y = None  # 新規作成開始時の y 座標
        self.key_pressed = {'shift': False, 'alt': False}  # キー状態追跡用
        self.last_cursor_state = "arrow"
        self.last_motion_time = int(time.time() * 1000)  # 初期値を設定
        self.motion_throttle_ms = 66.8  # 3 フレームごとに 1 回のみ実行されるように設定（16.7ms × 3 = 50.1ms）（50.1：会社設定）
        self.MIN_RECT_PIXELS = 10  # ピクセル基準の最小サイズ
        self.MIN_RECT_SIZE = 0.1   # ズーム領域の最小サイズの初期値（後で動的計算で上書き）
        self._state = ZoomState.NO_RECT  # 内部状態変数（アンダースコア付き）
        self.validator = EventValidator  # バリデータークラスのインスタンス
        self._debug = True  # デバッグモードフラグ
        self.debug_logger = DebugLogger(debug_enabled=self._debug)

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
        Returns:
            ZoomState: 現在のズーム操作の状態
        """
        return self._state

    @state.setter
    def state(self, new_state):
        """
        セッター：新しい状態（new_state）が現在の状態（self._state）と異なる場合にのみ、状態を更新する
        Args:
            new_state (ZoomState): 新しい状態
        Returns:
            None
        """

        # 型チェック（必須）
            # 新しい状態 (new_state) が ZoomState 型でなければエラーを発生させる
        if not isinstance(new_state, ZoomState):
            error_msg = f"無効な状態型.state: {type(new_state)} (期待: ZoomState)"
            self._log_debug_info(error_msg, level=LogLevel.ERROR)
            raise TypeError(error_msg)

        # 現在の状態を old_state に記録
        old_state = self._state

        # 現在の状態 (old_state) と新しい状態を比較し、変化が無いなら、何もしない
        if old_state == new_state:
            return

        # ズーム領域新規作成時の座標が有効な場合、座標を文字列形式で生成
        coord_str = (
            f"({self.start_x:.1f}, {self.start_y:.1f})"
            if self.start_x is not None and self.start_y is not None
            else "None"
        )

        # ズーム状態変化時のデバッグログの内容
        context = {
            "ズーム状態の変化.state": f"{old_state.name} → {new_state.name}",
            "キーの状態.state": f"SHIFT = {self.key_pressed['shift']}, ALT = {self.key_pressed['alt']}",
            "マウス座標.state": coord_str,
            "ズーム領域サイズ.state": self._get_rect_properties()[2:] if self.rect else None
        }

        # ズーム状態がリサイズであり、かつズーム領域が存在する場合、ズーム領域のサイズをコンソールに出力
        if new_state == ZoomState.RESIZE and isinstance(self.press, ResizeOperationData):
            context["操作中の角.state"] = self.press.corner_name
            context["固定点座標.state"] = self.press.fixed_point

        # デバッグログ出力
        self._log_debug_info(
            "状態遷移を検出.state",
            context=context,
            level=LogLevel.INFO
        )

        # 実際の状態更新
        self._state = new_state  # ズーム操作の状態に変化がある場合は、現在の状態を更新

        self._on_state_changed(old_state, new_state)

    def _on_state_changed(self, old_state, new_state):
        """
        ズーム操作の状態変更時の追加処理（今は未使用）
        Args:
            old_state (_type_): 未使用
            new_state (_type_): 未使用
        """
        # サンプル: カーソル更新
        if self._last_motion_event:  # 直前のマウス移動イベントがある場合
            self.update_cursor(self._last_motion_event)  #  カーソルを更新

    # on_press 関連 ----------------------------------------------------------------------------------------------------
    def on_press(self, event):
        if not self.validator.validate_basic_event(event, self):
            return

        state_handlers = {
            ZoomState.NO_RECT: self._handle_no_rect_press,
            ZoomState.WAIT_RECT_EXISTS: self._handle_rect_exists_press,
            ZoomState.WAIT_RESIZE: self._handle_resize_press,
            ZoomState.WAIT_ROTATE: self._handle_rotate_press,
        }
        if self.state in state_handlers:
            state_handlers[self.state](event)

        self.update_cursor(event)
        self.canvas.draw()

    def _handle_no_rect_press(self, event):
        """マウスボタン押下：ズーム領域なし"""
        if event.button == 1:
            self.state = ZoomState.CREATE
            self._begin_rect_set(event)
        elif event.button == 2:
            if self.on_zoom_cancel:
                self.on_zoom_cancel()  # コールバック：MainWindow.on_zoom_cancel を呼ぶ

    def _begin_rect_set(self, event):
        """ズーム領域を作成するための初期化処理"""
        if event.xdata is None or event.ydata is None:  # イベント座標が取得できない (None) 場合
            self._log_debug_info(  # デバッグログを出力して、メソッドを終了
                "座標取得不可._begin_rect_creation",
            context={
                "開始座標._begin_rect_creation": (self.start_x, self.start_y),
                "イベント種別._begin_rect_creation": "左クリック"
            },
            level=LogLevel.INFO
            )
            return

        self.start_x, self.start_y = event.xdata, event.ydata  # ズーム領域の開始位置を取得
        self.rect = patches.Rectangle(  # 取得した情報でズーム領域を作成（左押下直後なので、幅と高さはゼロ）
            (self.start_x, self.start_y), 0, 0,
            edgecolor='white', facecolor='none', linestyle='solid'
        )
        self.ax.add_patch(self.rect)  # ズーム領域をキャンバスに追加

    def _handle_rect_exists_press(self, event):
        """マウスボタン押下：ズーム領域あり、待機中（リサイズか回転か不特定）"""
        if event.button == 1:
            self._record_drag_start(event)
            self.state = ZoomState.MOVE
        elif event.button == 2:
            if self.last_rect:
                self._previou_rect()
            else:
                self._clear_rect()
                self.state = ZoomState.NO_RECT
        elif event.button == 3:
            self._confirm_zoom()
            self.state = ZoomState.NO_RECT

    def _record_drag_start(self, event):
        """マウスボタン押下時の情報を更新（左下座標、現在のマウスカーソル座標）"""
        self.press = (self.rect.get_xy(), event.xdata, event.ydata)

    def _previou_rect(self):
        """ズーム領域を直前の状態に戻す"""
        x, y, width, height = self.last_rect
        self.rect.set_xy((x, y))
        self.rect.set_width(width)
        self.rect.set_height(height)

    def _confirm_zoom(self):
        """ズーム領域確定処理：ズーム領域の情報からズームパラメータを生成しコールバック呼び出す"""
        if self.rect is None:
            return

        _, _, width, height = self._get_rect_properties()
        center_x, center_y = self._get_rect_center()

        zoom_params = {
            "center_x": center_x,
            "center_y": center_y,
            "width": abs(width),
            "height": abs(height),
            "rotation": self.angle
        }

        if self._debug:
            self._log_debug_info(
                "ズーム領域確定._confirm_zoom",
                context={
                    "中心座標._confirm_zoom": f"({center_x:.2f}, {center_y:.2f})",
                    "サイズ._confirm_zoom": f"{abs(width):.2f} x {abs(height):.2f}",
                    "角度._confirm_zoom": f"{self.angle:.2f}°"
                },
                level=LogLevel.INFO
            )

        self._clear_rect()

        if self.on_zoom_confirm:
            self.on_zoom_confirm(zoom_params)  # コールバック：MainWindow.on_zoom_confirm

    def _handle_resize_press(self, event):
        """マウスボタン押下：ズーム領域あり、かつ Shift 押下（リサイズ待機中）"""
        if (event.button != 1 or  # マウス左以外の場合か
            not self._get_pointer_near_corner(event)):  # マウスカーソルがズーム領域の角許容範囲外にある場合
            return

        self.press = self._prepare_resize(event)  # マウス押下時のデータを更新

        if (  # リサイズに必要な情報が揃っていない場合
            self.rect is None or
            not isinstance(self.press, ResizeOperationData) or
            event.xdata is None or
            event.ydata is None):
            self.press = None  # マウス押下時のデータを None に設定

            if self._debug:
                self._log_debug_info(
                    "サイズ変更の初期化に失敗: 初期状態が無効です._handle_resize_press",
                    level=LogLevel.ERROR
                )
            return

        self.state = ZoomState.RESIZE

    def _handle_rotate_press(self, event):
        """マウスボタン押下：ズーム領域あり、かつ Alt 押下（回転待機中）"""
        if (event.button != 1 or  # マウス左以外の場合か
            not self._get_pointer_near_corner(event)):  #マウスカーソルがズーム領域の角許容範囲外にある場合
            return

        self._initiate_rect_rotation(event)

        if (  # リサイズに必要な情報が揃っていない場合
            self.rect is None or
            not isinstance(self.press, RotationOperationData) or
            event.xdata is None or
            event.ydata is None):
            self.press = None  # マウス押下時のデータを None に設定

            if self._debug:
                self._log_debug_info(
                    "回転の初期化に失敗: 初期状態が無効です._handle_rotate_press",
                    level=LogLevel.ERROR
                )

            return

        self.state = ZoomState.ROTATE

    def _prepare_resize(self, event):
        """
        マウス位置から最も近いズーム領域の角を選定し、固定すべき点を求める
        Returns:
            ResizeOperationData: リサイズに必要な情報を含むオブジェクト
        """
        x, y, width, height = self._get_rect_properties()
        corners = {
            'bottom_left': (x, y),
            'bottom_right': (x + width, y),
            'top_left': (x, y + height),
            'top_right': (x + width, y + height)
        }

        min_dist = float('inf')  # 角までの距離を保存する変数（この場合、初期値は無限大となる）
        nearest_key = None  # 角の名前を保存する変数
        for key, (cx, cy) in corners.items():
            dist = np.hypot(event.xdata - cx, event.ydata - cy)  # 直角三角形の斜辺の長さでマウス位置と角の距離を計算
            if dist < min_dist:
                min_dist = dist
                nearest_key = key

        if nearest_key == 'bottom_left':  # 左下の場合
            fixed = (x + width, y + height) # 右上が固定点
        elif nearest_key == 'bottom_right':
            fixed = (x, y + height)
        elif nearest_key == 'top_left':
            fixed = (x + width, y)
        elif nearest_key == 'top_right':
            fixed = (x, y)

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

    def _initiate_rect_rotation(self, event):
        """回転の準備"""
        cx, cy = self._get_rect_center()
        initial_angle = np.degrees(np.arctan2(event.ydata - cy, event.xdata - cx))
        self.rot_base = self.angle
        self.press = RotationOperationData(
            center_x=cx,
            center_y=cy,
            initial_angle=initial_angle
        )

    def _get_rect_center(self):
        """ズーム領域の中心座標を取得"""
        x, y, width, height = self._get_rect_properties()
        return (x + width / 2.0, y + height / 2.0)

    # on_motion 関連 ----------------------------------------------------------------------------------------------------
    def on_motion(self, event):
        self._last_motion_event = event  # 直前のマウス移動イベントを保存

        if not self.validator.validate_basic_event(event, self):
            return

        # スロットリング処理
        current_time = int(time.time() * 1000)  # 現在時刻をミリ秒単位で取得
        if (
            hasattr(self, 'last_motion_time') and  # オブジェクトselfに属性last_motion_timeが存在する場合、かつ、
            current_time - self.last_motion_time < self.motion_throttle_ms):  # 現在の時刻と前回の動作時刻の差がスロットリング間隔より小さい場合
            return  # メソッドを終了
        self.last_motion_time = current_time  # 現在時刻を更新

        old_props = self._get_rect_properties()  # ズーム領域のキャッシュを取得
        draw_flag = False  # 再描画用フラグを初期化

        state_handlers = {
            ZoomState.CREATE: self._update_rect,
            ZoomState.MOVE: self._update_rect_pos,
            ZoomState.RESIZE: self._update_rect_size,
            ZoomState.ROTATE: self._update_rect_rotate,
        }
        if self.state in state_handlers:  # ズーム状態と対応する更新メソッドが存在する場合、対応する更新メソッドを実行
            state_handlers[self.state](event)
            new_props = self._get_rect_properties()
            draw_flag = old_props != new_props  # ズーム領域に変化があれば True を返す
        elif self.state == ZoomState.WAIT_RECT_EXISTS:
            if self._get_pointer_near_corner(event):  # カーソルが角付近にある場合、ズーム状態を変更
                if self.key_pressed['shift']:
                    self.state = ZoomState.WAIT_RESIZE
                elif self.key_pressed['alt']:
                    self.state = ZoomState.WAIT_ROTATE
            new_props = self._get_rect_properties()
            draw_flag = old_props != new_props

        self.update_cursor(event)

        if draw_flag:  # ズーム領域に変化がある場合、再描画
            self.canvas.draw()

    def _update_rect(self, event):
        """新規で作成したズーム領域の更新"""
        if not self.validator.validate_basic_event(event, self):
            return

        # 差分計算（現在の座標 - 開始座標）
        diff_x = event.xdata - self.start_x
        diff_y = event.ydata - self.start_y

        self.rect.set_bounds(
            min(self.start_x, event.xdata),
            min(self.start_y, event.ydata),
            abs(diff_x),
            abs(diff_y)
        )

        self._invalidate_rect_cache()

    def _update_rect_pos(self, event):
        """ズーム領域の位置の更新"""
        orig_xy, press_x, press_y = self.press

        diff_x = event.xdata - press_x
        diff_y = event.ydata - press_y

        self.rect.set_xy((orig_xy[0] + diff_x, orig_xy[1] + diff_y))

        self._invalidate_rect_cache()

    def _update_rect_size(self, event):
        """ズーム領域のサイズ更新"""
        if not self.validator.validate_resize(event, self):
            return

        rect_params = self._calculate_resized_rect(event.xdata, event.ydata)

        self._log_debug_info(
            "リサイズ計算結果._update_rect_size",
            context={
                "マウス座標._update_rect_size": (event.xdata, event.ydata),
                "新しいズーム領域のサイズ._update_rect_size": f"{rect_params[2]:.1f}x{rect_params[3]:.1f}"
            },
            level=LogLevel.DEBUG
        )

        if rect_params is None:
            return

        x, y, width, height = rect_params
        self.rect.set_bounds(x, y, width, height)

        self._invalidate_rect_cache()

        if self._debug:
            self._log_debug_info(
                "ズーム領域：サイズ更新._update_rect_size",
                context={
                    "左下座標._update_rect_size": f"({x:.2f}, {y:.2f})",
                    "サイズ._update_rect_size": f"{width:.2f}x{height:.2f}"
                },
                level=LogLevel.INFO
            )

    def _calculate_resized_rect(self, current_x: float, current_y: float) -> tuple:
        """
        リサイズ中のズーム領域の座標を計算（共通化されたロジック）
        Args:
            current_x (float): 現在のマウスX座標
            current_y (float): 現在のマウスY座標
        Returns:
            tuple: (x, y, width, height)
        """
        if not isinstance(self.press, ResizeOperationData):
            return None

        fixed_x, fixed_y = self.press.fixed_point
        corner_mapping = {
            'bottom_left': ([current_x, fixed_x], [current_y, fixed_y]),
            'bottom_right': ([fixed_x, current_x], [current_y, fixed_y]),
            'top_left': ([current_x, fixed_x], [fixed_y, current_y]),
            'top_right': ([fixed_x, current_x], [fixed_y, current_y])
        }
        if self.press.corner_name in corner_mapping:
            x_values, y_values = corner_mapping[self.press.corner_name]
            x0, x1 = sorted(x_values)
            y0, y1 = sorted(y_values)
        else:
            return None
        width = x1 - x0
        height = y1 - y0
        return (x0, y0, width, height)

    def _update_rect_rotate(self, event):
        """回転中のズーム領域の情報を更新"""
        if not self.validator.validate_rotate(event, self):
            return

        cx = self.press.center_x
        cy = self.press.center_y
        initial_angle = self.press.initial_angle

        current_angle = np.degrees(np.arctan2(
            event.ydata - cy,
            event.xdata - cx
        ))

        angle_diff = (current_angle - initial_angle) % 360
        if angle_diff > 180:
            angle_diff -= 360

        smoothing_factor = 0.8
        smoothed_angle_diff = angle_diff * smoothing_factor

        self.angle = (self.rot_base + smoothed_angle_diff) % 360

        t = transforms.Affine2D().rotate_deg_around(cx, cy, self.angle)  # アフィン変換を適用
        self.rect.set_transform(t + self.ax.transData)

        self._invalidate_rect_cache()
        self.canvas.draw()

    # on_release 関連 ----------------------------------------------------------------------------------------------------
    def on_release(self, event):
        if not self.validator.validate_basic_event(event, self):
            return

        state_handlers = {
            ZoomState.CREATE: self._handle_create_release,
            ZoomState.MOVE: self._handle_move_release,
            ZoomState.RESIZE: self._handle_resize_release,
            ZoomState.ROTATE: self._handle_rotate_release,
        }
        if self.state in state_handlers:
            state_handlers[self.state](event)

        self.update_cursor(event)

        self.canvas.draw()

    def _handle_create_release(self, event):
        """CREATE 状態でのリリース処理"""
        self.press = None
        self._finalize_rect(event)
        self._apply_min_size_constraints()
        self.state = ZoomState.WAIT_RECT_EXISTS

    def _handle_move_release(self, event):
        """MOVE 状態でのリリース処理"""
        self.press = None
        self.state = ZoomState.WAIT_RECT_EXISTS

    def _handle_resize_release(self, event):
        """RESIZE 状態でのリリース処理"""
        if self.rect is not None:
            self._apply_min_size_constraints()
        self.press = None
        if self.key_pressed['shift']:
            self.state = ZoomState.WAIT_RESIZE
        if self.key_pressed['alt']:
            self.state = ZoomState.WAIT_RECT_EXISTS

    def _handle_rotate_release(self, event):
        """ROTATE 状態でのリリース処理"""
        self.press = None
        if self.key_pressed['shift']:
            self.state = ZoomState.WAIT_RECT_EXISTS
        if self.key_pressed['alt']:
            self.state = ZoomState.WAIT_ROTATE

    def _finalize_rect(self, event):
        """ズーム領域の作成を確定"""
        end_x, end_y = event.xdata, event.ydata

        diff_x = end_x - self.start_x
        diff_y = end_y - self.start_y

        if diff_x == 0 or diff_y == 0:
            self._clear_rect()
            self.state = ZoomState.NO_RECT
            return

        new_x = self.start_x if diff_x > 0 else end_x
        new_y = self.start_y if diff_y > 0 else end_y
        width = abs(diff_x)
        height = abs(diff_y)

        self.rect.set_bounds(new_x, new_y, width, height)

        self._invalidate_rect_cache()

        self.drag_direction = {  # ドラッグ方向を記録（最小サイズ適用時に使用）
            'x': 'right' if diff_x > 0 else 'left',
            'y': 'up' if diff_y > 0 else 'down'
        }

    def _apply_min_size_constraints(self):
        """ズーム領域が最小サイズ未満の場合、最小サイズを適用する"""
        if self.rect is None:
            return

        x, y, width, height = self._get_rect_properties()
        min_size = self._get_min_size_in_data_coords()  # データ座標系での最小サイズを取得

        if (
            abs(width) >= min_size and  # ズーム領域のサイズが最小サイズ以上の場合、メソッドを終了
            abs(height) >= min_size):
            return

        norm_angle = self.angle % 180  # 回転角度の正規化 (0～180度)

        if abs(norm_angle) > 1e-6 and abs(norm_angle - 90) > 1e-6:
            diag = np.hypot(abs(width), abs(height))  # ズーム領域の対角距離を計算
            eff_size = diag * np.sin(np.radians(min(norm_angle, 180 - norm_angle)))  # 対角距離と回転角から実効サイズを計算
        else:
            eff_size = min(abs(width), abs(height))

        if eff_size < min_size:
            ratio = min_size / eff_size  # 実効サイズと最小サイズの比率を計算
            new_width = width * ratio
            new_height = height * ratio

            if hasattr(self, 'drag_direction'):  # ドラッグ方向に応じて位置調整
                if self.drag_direction['x'] == 'left':
                    x -= (new_width - width)
                if self.drag_direction['y'] == 'down':
                    y -= (new_height - height)

            self.rect.set_xy((x, y))
            self.rect.set_width(new_width)
            self.rect.set_height(new_height)

            self._invalidate_rect_cache()

        if self._debug:
            self._log_debug_info(
                "ズーム領域：最小サイズ適用._apply_min_size_constraints",
                context={
                    "サイズ：リサイズ前._apply_min_size_constraints": f"{width:.2f}x{height:.2f}",
                    "サイズ：リサイズ後._apply_min_size_constraints": f"{new_width:.2f}x{new_height:.2f}",
                    "左下座標._apply_min_size_constraints": f"({x:.2f}, {y:.2f})",
                    "角度._apply_min_size_constraints": f"{self.angle:.1f}°",
                    "ドラッグ方向._apply_min_size_constraints": getattr(self, 'drag_direction', 'unknown'),
                    "最最小サイズのピクセル値._apply_min_size_constraints": self.MIN_RECT_PIXELS,
                    "最小サイズ：データ._apply_min_size_constraints": f"{min_size:.2f}"
                },
                level=LogLevel.DEBUG
            )

    def _get_min_size_in_data_coords(self):
        """
        現在の表示スケールでのズーム領域の最小サイズをデータ座標で計算
        Returns:
            float: 最小サイズ（データ座標）
        """
        transform = self.ax.transData.inverted()  # ディスプレイ座標系→データ座標系の変換を設定

        # ピクセルの最小サイズを変換し、データ座標での最小サイズ（px_diff）を計算する
            # [0] の指定で x 座標のみを取得している
        px_diff = transform.transform((self.MIN_RECT_PIXELS, 0))[0] - transform.transform((0, 0))[0]
        self._min_rsct_data = abs(px_diff)  # 計算結果の絶対値を self にキャッシュする

        self._log_debug_info(
            "最小サイズ更新._get_min_size_in_data_coordsclear_rect",
            context={
                "最小サイズのピクセル値._get_min_size_in_data_coords": self.MIN_RECT_PIXELS,
                "最小サイズのキャッシュ（データ座標）._get_min_size_in_data_coords": f"{self._min_rsct_data:.6f} data units",
                "現在の変換スケール._get_min_size_in_data_coords": f"{self.ax.transData.transform((1,1)) - self.ax.transData.transform((0,0))}"
            },
            level=LogLevel.DEBUG
        )

        return self._min_rsct_data

    # on_key_press 関連 ----------------------------------------------------------------------------------------------------

    def on_key_press(self, event):
        if event.key not in ['shift', 'alt']:
            return

        if self.state == ZoomState.WAIT_RECT_EXISTS and event.key in ['shift', 'alt']:
            if not self.key_pressed[event.key]:  # キーリピート対策：初めてキーが押された場合は Ture ではないので、処理を実行
                self.key_pressed[event.key] = True  # 直後に True になるので、その後は実行しない
                if self.key_pressed['shift']:
                    if self._get_pointer_near_corner(self._last_motion_event):
                        self.state = ZoomState.WAIT_RESIZE  # on_key_press：RESIZE、カーソルが角許容範囲内
                elif self.key_pressed['alt']:
                    if self._get_pointer_near_corner(self._last_motion_event):
                        self.state = ZoomState.WAIT_ROTATE  # on_key_press：ROTATE、カーソルが角許容範囲内
                self.canvas.draw()

        self.update_cursor(self._last_motion_event)

    # on_key_release 関連 ----------------------------------------------------------------------------------------------------

    def on_key_release(self, event):
        if self._last_motion_event is None:
            return

        if event.key not in ['shift', 'alt']:  # 離されたキーが shift か alt でない場合
            return  # メソッドを終了（これを通過するなら、離されたキーが shift または alt である）

        # 離されたキーが self.key_pressed 辞書に含まれるか（追跡対象か）を確認する
            # 例えば、shift キーが離された場合、'shift' in self.key_pressed は True になりるので、
            # その後の処理が実行されて、self.key_pressed['shift'] に False が設定される
        if event.key in self.key_pressed:
            self.key_pressed[event.key] = False

        state_changed = False  # 状態が変わったかどうかのフラグに、false を設定
        if not self.key_pressed['shift']:  # Shift キーが離された場合
            if self.state in (ZoomState.WAIT_RESIZE, ZoomState.RESIZE):  # 状態が WAIT_SHIFT_RESIZE か RESIZE なら
                self.state = ZoomState.WAIT_RECT_EXISTS  # WAIT_NOKEY_ZOOM_RECT_EXISTS に戻す
                state_changed = True
        if not self.key_pressed['alt']:  # Alt キーが離された場合
            if self.state in (ZoomState.WAIT_ROTATE, ZoomState.ROTATE):  # WAIT_ALT_ROTATE か ROTATE なら
                self.state = ZoomState.WAIT_RECT_EXISTS  # WAIT_NOKEY_ZOOM_RECT_EXISTS に戻す
                state_changed = True

        if state_changed:  # 状態が変わった場合のみデバッグログ出力と再描画
            self.update_cursor(self._last_motion_event)  # カーソル更新のために self._last_motion_event を使う
            self.canvas.draw()
        else:  # 状態が変わらなくてもカーソルは更新する可能性がある
            self.update_cursor(self._last_motion_event)

        self.update_cursor(event)
        self.canvas.draw()

    # ------------------------------------------------------------------------------------------------------------------------
    def _clear_rect(self):
        """ズーム領域を完全にクリア（キャッシュ・状態もリセット）"""
        if self.rect is not None:
            self.rect.remove()  # ズーム領域の削除
            self.rect = None

        self._invalidate_rect_cache()  # キャッシュクリア
        self.last_rect = None  # 直前のズーム領域の情報をクリア
        self.press = None  # マウスボタン押下情報をクリア
        self.start_x = self.start_y = None  # 開始座標リセット
        self.last_cursor_state = None  # カーソル状態を完全リセット
        self.canvas.get_tk_widget().config(cursor="arrow")

        self.canvas.draw()

        if self._debug:
            self._log_debug_info(
                "ズーム領域クリア._clear_rect",
                level=LogLevel.INFO
            )

    def _invalidate_rect_cache(self):
        """ズーム領域のキャッシュを無効化"""
        self._cached_rect_props = None

    def update_cursor(self, event):
        """各状態とカーソル位置に応じたカーソル形状を設定"""
        if (not hasattr(event, 'xdata') or
            event.xdata is None or
            not hasattr(event, 'ydata') or
            event.ydata is None):
            self.canvas.get_tk_widget().config(cursor="arrow")
            return

        new_cursor = "arrow"
        if self.state in (ZoomState.NO_RECT, ZoomState.CREATE):
            new_cursor = "arrow"
        elif self.state == ZoomState.MOVE:
            new_cursor = "fleur"
        elif self.state in (ZoomState.WAIT_RESIZE, ZoomState.RESIZE):
            new_cursor = "crosshair" if self._get_pointer_near_corner(event) else "arrow"
        elif self.state in (ZoomState.WAIT_ROTATE, ZoomState.ROTATE):
            new_cursor = "exchange" if self._get_pointer_near_corner(event) else "arrow"
        elif self.state == ZoomState.WAIT_RECT_EXISTS:
            new_cursor = "fleur" if self._cursor_inside_rect(event) else "arrow"
        else:
            new_cursor = "arrow"

        if new_cursor != self.last_cursor_state:  # 変更が有る場合
            self.canvas.get_tk_widget().config(cursor=new_cursor)  # カーソルを変更
            self.last_cursor_state = new_cursor  # 最後のカーソル状態を更新

    def _cursor_inside_rect(self, event):
        """マウスカーソルがズーム領域内部に在るかどうかを判定する"""
        if self.rect is None:
            return False
        contains, _ = self.rect.contains(event)
        return contains

    def _log_debug_info(self,
                        message: str,
                        context: Optional[Dict[str, Any]] = None,
                        old_state: Optional[ZoomState] = None,
                        new_state: Optional[ZoomState] = None,
                        level: LogLevel = LogLevel.DEBUG) -> None:
        """
        デバッグ情報をログに出力
        Args:
            message: メインのログメッセージ
            context: 追加コンテキスト情報(オプション)
            old_state: 変更前の状態(オプション)
            new_state: 変更後の状態(オプション)
            level: ログレベル
        """
        if not self._debug:
            return

        if context is None: # コンテキストが None の場合
            context = {}  # 空の辞書を初期化

        if old_state is not None and new_state is not None:
            context["ズーム状態変更._log_debug_info"] = f"{old_state.name} → {new_state.name}"

        # マウス位置
        # start_x と start_y が None でない場合
        # 小数点1桁でフォーマット（start_x=12.3456, start_y=78.9 の場合 → "(12.3, 78.9)"）
        # どちらかが None の場合は "None" とする
            # Python では、A if 条件 else B の形式のコードがあるとき
            # 条件が True の場合は A が処理され、False の場合は B が処理される
#        mouse_pos = (
#            f"({self.start_x:.1f}, {self.start_y:.1f})"
#            if self.start_x is not None and self.start_y is not None
#            else "None"
#        )
#        context["マウス位置._log_debug_info"] = mouse_pos

        # キー状態
#        context["キーステータス._log_debug_info"] = f"SHIFT: {self.key_pressed['shift']}, ALT: {self.key_pressed['alt']}"

        # ズーム領域情報
#        rect_props = self._get_rect_properties()
#        context["ズーム領域._log_debug_info"] = f"{rect_props}" if rect_props else "None"

        # リサイズ操作情報
        if self.press and isinstance(self.press, ResizeOperationData):
            resize_info = {
                "角の名前._log_debug_info": self.press.corner_name,
                "固定点._log_debug_info": f"({self.press.fixed_point[0]:.1f}, {self.press.fixed_point[1]:.1f})",
                "ズーム前のサイズ._log_debug_info": f"{self.press.original_width:.1f}x{self.press.original_height:.1f}",
                "ドラッグ開始位置._log_debug_info": f"({self.press.press_x:.1f}, {self.press.press_y:.1f})"
            }
            context["リサイズ情報._log_debug_info"] = resize_info

        # 回転操作情報
        if self.press and isinstance(self.press, RotationOperationData):
            rotate_info = {
                "中心点": f"({self.press.center_x:.1f}, {self.press.center_y:.1f})",
                "角度": f"{self.press.initial_angle:.1f}°"
            }
            context["回転情報._log_debug_info"] = rotate_info

        # イベント位置
        if hasattr(self, '_last_motion_event') and self._last_motion_event:
            e = self._last_motion_event
            context["直前のマウス座標._log_debug_info"] = f"({e.xdata:.1f}, {e.ydata:.1f})"

        self.debug_logger.log(level, message, context)

    def _get_rect_properties(self):
        """
        ズーム領域のプロパティのキャッシュが無い場合、ズーム領域の位置とサイズを取得してキャッシュし、その値を返す。
        Returns:
            tuple_or_None: ズーム領域の位置とサイズ（x, y, width, height）。ズーム領域が存在しない場合は None
        """
        if self.rect is None:
            return None

        if self._cached_rect_props is None:
            x, y = self.rect.get_xy()  # ズーム領域の左下の座標を取得
            self._cached_rect_props = (
                x, y, self.rect.get_width(), self.rect.get_height())  # ズーム領域の位置とサイズをキャッシュ

        return self._cached_rect_props

    def _get_pointer_near_corner(self, event):
        """
        マウス位置がズーム領域の角に近いかどうかを判定する。
        許容範囲 tol = 0.1 * min(width, height)（ただし min が 0 の場合は 0.2）
        """
        if self.rect is None:
            return False

        x, y, width, height = self._get_rect_properties()

        tol = 0.1 * min(width, height) if min(width, height) != 0 else 0.2  # 通常の許容範囲

        corners = [(x, y), (x + width, y), (x, y + height), (x + width, y + height)]  # 角の座標をリストに格納

        for cx, cy in corners:  # 各角についてマウス位置との距離を計算
            if np.hypot(event.xdata - cx, event.ydata - cy) < tol:  # マウス位置と角の距離が許容範囲内なら
                return True
        return False

class EventValidator:
    @staticmethod
    def validate_basic_event(event, selector):
        """
        イベント有効性チェック：基本
        Args:
            event: 検証するイベント
            selector: ZoomSelectorインスタンス
        Returns:
            bool: イベントが有効ならTrue
        """
        checks = [
            (hasattr(event, 'xdata') and hasattr(event, 'ydata'), "座標が見つかりません"),
            (event.xdata is not None and event.ydata is not None, "座標なし"),
            (hasattr(event, 'inaxes') and event.inaxes == selector.ax, "無効な軸")
        ]
        return all(condition for condition, _ in checks)

    @staticmethod
    def validate_rect_operation(event, selector):
        """
        イベント有効性チェック：矩形操作用
        Args:
            event: 検証するイベント
            selector: ZoomSelectorインスタンス
        Returns:
            bool: 矩形操作が可能ならTrue
        """
        return (
            EventValidator.validate_basic_event(event, selector) and
            selector.rect is not None
        )

    @staticmethod
    def validate_resize(event, selector):
        """
        イベント有効性チェック：リサイズ操作用
        Args:
            event: 検証するイベント
            selector: ZoomSelectorインスタンス
        Returns:
            bool: リサイズ操作が可能ならTrue
        """
        return (
            EventValidator.validate_rect_operation(event, selector) and
            isinstance(selector.press, ResizeOperationData) and
            selector.state == ZoomState.RESIZE
        )

    @staticmethod
    def validate_rotate(event, selector):
        """
        イベント有効性チェック：回転操作用
        Args:
            event: 検証するイベント
            selector: ZoomSelectorインスタンス
        Returns:
            bool: 回転操作が可能ならTrue
        """
        return (
            EventValidator.validate_rect_operation(event, selector) and
            isinstance(selector.press, RotationOperationData) and
            selector.state == ZoomState.ROTATE
        )

    @staticmethod
    def validate_size_constraints(selector):
        """
        サイズ制約のバリデーション
        Args:
            selector: ZoomSelectorインスタンス
        Returns:
            bool: サイズ制約が満たされていればTrue
        """
        if selector.rect is None:
            return False

        min_size = selector._get_min_size_in_data_coords()
        props = selector._get_rect_properties()
        return all(abs(p) >= min_size * 0.9 for p in props[2:])  # 10%のマージン
