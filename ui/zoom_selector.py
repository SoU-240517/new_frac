# インポート
from dataclasses import dataclass
import numpy as np
import matplotlib.patches as patches
import matplotlib.transforms as transforms
from enum import Enum, auto
import time  # 時間処理モジュール
from typing import Optional, Dict, Any

@dataclass
class ResizeOperationData:
    """ ズーム領域のリサイズ時の列挙型 """
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
    """ ズーム領域の回転時の列挙型 """
    center_x: float
    center_y: float
    initial_angle: float

class LogLevel(Enum):
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
        if level.value < self.min_level.value:  # レベルが足りない場合は無視
            return

        if not self.debug_enabled and not force:
            return

        # スロットリングチェック
        current_time = int(time.time() * 1000)
        if not force and current_time - self.last_log_time < self.log_throttle_ms:
            return
        self.last_log_time = current_time

        # ログのフォーマット
        timestamp = time.strftime("%H:%M:%S", time.localtime())
        level_str = level.name.ljust(7)
        log_entry = f"[{timestamp}] {level_str} - {message}"

        if context:
            log_entry += "\n" + self._format_context(context)

        print(log_entry)

    def _format_context(self, context: Dict[str, Any]) -> str:
        """ コンテキスト情報を整形して文字列に変換 """
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
    """ ズーム操作の状態を表す列挙型 """
    NO_ZOOM_RECT = auto()                 # ズーム領域無し（ズーム領域が存在しない）
    CREATE = auto()                       # ズーム領域の新規作成モード（左ボタン ONで開始）
    WAIT_NOKEY_ZOOM_RECT_EXISTS = auto()  # ズーム領域有り（キー入力無し）
    MOVE = auto()                         # ズーム領域移動モード（ズーム領域内で左ドラッグ）
    WAIT_SHIFT_RESIZE = auto()            # リサイズ待機モード（shift ON）
    RESIZE = auto()                       # リサイズモード（shift＋左ドラッグ）
    WAIT_ALT_ROTATE = auto()              # 回転待機モード（alt ON）
    ROTATE = auto()                       # 回転モード（alt＋左ドラッグ）

class ZoomSelector:
    """ ズームセレクタークラス """

    def __init__(self, ax, on_zoom_confirm, on_zoom_cancel):
        """
        ズームセレクターの初期化
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
        self.press = None  # マウス押下時のデータ（構造は ResizeOperationData または RotationOperationData）
        self._last_motion_event = None  # 直前のマウス移動イベントを保存する変数
        self.drag_direction = None  # ドラッグ方向を保存する変数
        self.start_x = None  # 新規作成開始時の x 座標
        self.start_y = None  # 新規作成開始時の y 座標
        self.key_pressed = {'shift': False, 'alt': False}  # キー状態追跡用の変数
        self.angle = 0.0  # 現在の回転角（度）
        self.rot_base = 0.0  # 回転開始時の角度
        self.last_cursor_state = "arrow"
        self.last_motion_time = int(time.time() * 1000)  # 初期値を設定
        self.motion_throttle_ms = 66.8  # 3 フレームごとに 1 回のみ実行されるように設定（16.7ms × 3 = 50.1ms）（50.1：会社設定）
        self.MIN_RECT_SIZE = 0.1  # ズーム領域の最小サイズ
        self._cached_rect_props = None  # ズーム領域のプロパティをキャッシュする変数
        self._state = ZoomState.NO_ZOOM_RECT  # 内部状態変数（アンダースコア付き）
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
            error_msg = f"無効な状態型: {type(new_state)} (期待: ZoomState)"
            self._log_debug_info(error_msg, level=LogLevel.ERROR)
            raise TypeError(error_msg)

        # 現在の状態を old_state に記録
        old_state = self._state

        # 現在の状態 (old_state) と新しい状態と比較し、変化が無いなら、何もしない
        if old_state == new_state:
            return

        # 安全な座標フォーマット
        coord_str = (
            f"({self.start_x:.1f}, {self.start_y:.1f})"
            if self.start_x is not None and self.start_y is not None
            else "None"
        )

        # 状態変化時のコンテキスト情報
        context = {
            "前の状態": old_state.name,
            "新しい状態": new_state.name,
            "マウス座標": coord_str,
            "シフトキー": self.key_pressed['shift'],
            "Altキー": self.key_pressed['alt'],
            "ズーム領域サイズ": self._get_rect_properties()[2:] if self.rect else None
        }

        # 特別な状態変化の場合の追加情報
        if new_state == ZoomState.RESIZE and isinstance(self.press, ResizeOperationData):
            context["操作中の角"] = self.press.corner_name
            context["固定点座標"] = self.press.fixed_point

        # ログ出力（INFOレベルで重要な変化を記録）
        self._log_debug_info(
            "状態遷移を検出",
            context=context,
            level=LogLevel.INFO
        )

        # 実際の状態更新
        self._state = new_state  # ズーム操作の状態に変化がある場合は、現在の状態を更新
        self._on_state_changed(old_state, new_state)

    def _on_state_changed(self, old_state, new_state):
        """
        ズーム操作の状態変更時の追加処理（今は、メソッド内で引数が未使用）
        Args:
            old_state (_type_): 未使用
            new_state (_type_): 未使用
        """
        # サンプル: カーソル更新
        if self._last_motion_event:  # 直前のマウス移動イベントがある場合
            self.update_cursor(self._last_motion_event)  #  カーソルを更新

    # on_press 関連--------------------------------------------------
    def on_press(self, event):

        if not self.validator.validate_basic_event(event, self):
            return

        # ズーム状態ごとの処理を定義
        state_handlers = {
            ZoomState.NO_ZOOM_RECT: self._handle_no_rect_press,
            ZoomState.WAIT_NOKEY_ZOOM_RECT_EXISTS: self._handle_rect_exists_press,
            ZoomState.WAIT_SHIFT_RESIZE: self._handle_resize_press,
            ZoomState.WAIT_ALT_ROTATE: self._handle_rotate_press,
        }

        # 現在の状態に対応するメソッドを実行。対応メソッドが無い場合は、何もしない
        if self.state in state_handlers:
            state_handlers[self.state](event)
        else:
            pass

        self.update_cursor(event)
        self.canvas.draw()

    def _handle_no_rect_press(self, event):
        """ マウスボタンが押下された時の処理：ズーム領域が無い """
        if event.button == 1:
            self.state = ZoomState.CREATE
            self._begin_rect_creation(event)
        elif event.button == 2:
            if self.on_zoom_cancel:
                self.on_zoom_cancel()  # コールバック：MainWindow.on_zoom_cancel を呼ぶ

    def _begin_rect_creation(self, event):
        """ ズーム領域を作成するための初期化処理 """

        if event.xdata is None or event.ydata is None:
            self._log_debug_info(
                "ズーム領域作成開始",
            context={
                "開始座標": (self.start_x, self.start_y),
                "イベント種別": "左クリック"
            },
            level=LogLevel.INFO
            )
            return

        # ズーム領域の開始位置を記録
        self.start_x, self.start_y = event.xdata, event.ydata

        # ズーム領域を作成
        self.rect = patches.Rectangle(
            (self.start_x, self.start_y), 0, 0,
            edgecolor='white', facecolor='none', linestyle='solid'
        )

        # ズーム領域をキャンバスに追加
        self.ax.add_patch(self.rect)

    def _handle_rect_exists_press(self, event):
        """ マウスボタンが押下された時の処理：ズーム領域あり、かつ待機中（リサイズか回転か不特定） """
        if event.button == 1:
            self._record_drag_start(event)
            self.state = ZoomState.MOVE
        elif event.button == 2:
            if self.last_rect:
                self._previou_rect()
            else:
                self._clear_rect()
                self.state = ZoomState.NO_ZOOM_RECT  # _cancel_zoom：ズームキャンセル後、直前のズーム領域無し
        elif event.button == 3:
            self._confirm_zoom()
            self.state = ZoomState.NO_ZOOM_RECT  # _confirm_zoom：ズーム確定後：NO_ZOOM_AREA へ変更

    def _previou_rect(self):
        """ ズーム領域を直前の状態に戻す """

        x, y, width, height = self.last_rect
        self.rect.set_xy((x, y))
        self.rect.set_width(width)
        self.rect.set_height(height)

    def _record_drag_start(self, event):
        """ ズーム領域の情報を更新（矩形の左下, 現在のマウスカーソルの位置 x, y） """

        self.press = (self.rect.get_xy(), event.xdata, event.ydata)

    def _confirm_zoom(self):
        """ ズーム領域確定処理：ズーム領域の情報からズームパラメータを生成しコールバック呼び出す """

        # ズーム領域が無い場合は、メソッドを終了
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

        # 修正箇所: デバッグログ出力
        if self._debug:
            self._log_debug_info(
                "Zoom confirmed",
                context={
                    "center": f"({center_x:.2f}, {center_y:.2f})",
                    "size": f"{abs(width):.2f}x{abs(height):.2f}",
                    "rotation": f"{self.angle:.2f}°"
                },
                level=LogLevel.INFO
            )

        self._clear_rect()

        if self.on_zoom_confirm:
            self.on_zoom_confirm(zoom_params)  # コールバック：MainWindow.on_zoom_confirm を呼ぶ

    def _handle_resize_press(self, event):
        """ マウス押下時の処理：ズーム領域あり、かつ Shift 押下（リサイズ待機中） """

        # マウス左以外の場合か、マウスカーソルがズーム領域の角許容範囲にある場合は、メソッドを終了
        if event.button != 1 or not self._get_pointer_near_corner(event):
            return

        # マウス押下時のデータを更新
        self.press = self._prepare_resize(event)

        # リサイズに必要な情報が揃っているか確認
            # 揃っていない場合はマウス押下時のデータを None に設定し、メソッドを終了
            # デバッグ中なら、エラーを出力
        if (
            self.rect is None or
            not isinstance(self.press, ResizeOperationData) or
            event.xdata is None or
            event.ydata is None
        ):

            self.press = None

            # エラーログ出力
            if self._debug:
                self._log_debug_info(
                    "Resize initialization failed: Invalid initial state",
                    level=LogLevel.ERROR
                )
            return

        self.state = ZoomState.RESIZE

    def _handle_rotate_press(self, event):
        """ マウス押下時の処理：ズーム領域あり、かつ Alt 押下（回転待機中） """

        # マウス左以外の場合か、マウスカーソルがズーム領域の角許容範囲にある場合は、メソッドを終了
        if event.button != 1 or not self._get_pointer_near_corner(event):
            return

        self._initiate_rect_rotation(event)

        # リサイズに必要な情報が揃っているか確認
            # 揃っていない場合はマウス押下時のデータを None に設定し、メソッドを終了
            # デバッグ中なら、エラーを出力
        if (
            self.rect is None or
            not isinstance(self.press, RotationOperationData) or
            event.xdata is None or
            event.ydata is None
        ):

            self.press = None

            # エラーログ出力
            if self._debug:
                self._log_debug_info(
                    "Rotate initialization failed: Invalid initial state",
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

        # ズーム領域の位置とサイズを取得
        x, y, width, height = self._get_rect_properties()

        # 左下、右下、左上、右上の4つの角とその名前を辞書で定義
        corners = {
            'bottom_left': (x, y),
            'bottom_right': (x + width, y),
            'top_left': (x, y + height),
            'top_right': (x + width, y + height)
        }

        # マウス位置から最も近い角を特定するための変数の初期化
        min_dist = float('inf')  # 角までの距離を保存する変数（この場合、初期値は無限大となる）
        nearest_key = None  # 角の名前を保存する変数

        # 各角までの距離を計算
        for key, (cx, cy) in corners.items():  # 辞書のキーと x, y 座標を取得

            # 直角三角形の斜辺の長さ利用して、マウス位置と角の距離を計算
            dist = np.hypot(event.xdata - cx, event.ydata - cy)

            if dist < min_dist:
                min_dist = dist
                nearest_key = key

        # 固定する対角の点を決定（例：bottom_left の場合は top_right が固定点）
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

    def _initiate_rect_rotation(self, event):
        """ 回転の準備 """

        cx, cy = self._get_rect_center()
        initial_angle = np.degrees(np.arctan2(event.ydata - cy, event.xdata - cx))

        self.rot_base = self.angle

        self.press = RotationOperationData(
            center_x=cx,
            center_y=cy,
            initial_angle=initial_angle
        )

    def _get_rect_center(self):
        """ ズーム領域の中心座標を取得する """

        x, y, width, height = self._get_rect_properties()

        return (x + width / 2.0, y + height / 2.0)

    # on_motion 関連--------------------------------------------------
    def on_motion(self, event):

        # 受け取ったイベント情報を直前のズーム領域として保存
        self._last_motion_event = event

        if not self.validator.validate_basic_event(event, self):
            return

        # スロットリング処理
        # 現在時刻をミリ秒単位で取得
        current_time = int(time.time() * 1000)

        # 属性に last_motion_time がない場合、または、
        # 前回のモーションイベントからの経過時間がスロットリング時間を超えている場合、メソッドを終了
        if (
            hasattr(self, 'last_motion_time') and
            current_time - self.last_motion_time < self.motion_throttle_ms
        ):
            return

        # 現在時刻を更新
        self.last_motion_time = current_time

        # 状態ごとの更新処理を定義
        state_handlers = {
            ZoomState.CREATE: self._update_rect,
            ZoomState.MOVE: self._update_rect_position,
            ZoomState.RESIZE: self._update_rect_size,
            ZoomState.ROTATE: self._update_rect_rotate,
        }

        # ズーム領域のプロパティの取得（一度だけ）
        old_props = self._get_rect_properties()

        changed = False

        # ズーム状態と対応する更新メソッドが存在する場合、対応する更新メソッドを実行
        if self.state in state_handlers:

            state_handlers[self.state](event)
            new_props = self._get_rect_properties()
            changed = old_props != new_props  # 変更があれば True を返す

        elif self.state == ZoomState.WAIT_NOKEY_ZOOM_RECT_EXISTS:

            # カーソルが角付近にある場合、ズーム状態を変更
            if self._get_pointer_near_corner(event):
                if self.key_pressed['shift']:
                    self.state = ZoomState.WAIT_SHIFT_RESIZE
                elif self.key_pressed['alt']:
                    self.state = ZoomState.WAIT_ALT_ROTATE

            new_props = self._get_rect_properties()

            changed = old_props != new_props  # 変更があれば True を返す

        # カーソル更新と、ズーム領域に変化がある場合の再描画
        self.update_cursor(event)
        if changed:
            self.canvas.draw()

    def _update_rect(self, event):
        """ 新規で作成したズーム領域の更新 """

        if not self.validator.validate_basic_event(event, self):
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

        self._invalidate_rect_cache()

    def _update_rect_position(self, event):
        """ ズーム領域の位置の更新 """

        orig_xy, press_x, press_y = self.press

        dx = event.xdata - press_x
        dy = event.ydata - press_y

        self.rect.set_xy((orig_xy[0] + dx, orig_xy[1] + dy))

        self._invalidate_rect_cache()

    def _update_rect_size(self, event):
        """ ズーム領域のサイズ更新 """

        if not self.validator.validate_resize(event, self):
            return

        # 共通メソッドで座標計算
        rect_params = self._calculate_resized_rect(event.xdata, event.ydata)

        self._log_debug_info(
            "リサイズ計算結果",
            context={
                "マウス座標": (event.xdata, event.ydata),
                "新しいサイズ": f"{rect_params[2]:.1f}x{rect_params[3]:.1f}"
            }
        )

        if rect_params is None:
            return

        x, y, width, height = rect_params

        # ズーム領域の左下座標とサイズを設定
        self.rect.set_bounds(x, y, width, height)

        self._invalidate_rect_cache()

        # デバッグログ出力
        if self._debug:
            self._log_debug_info(
                "ズーム領域：サイズ更新",
                context={
                    "position": f"({x:.2f}, {y:.2f})",
                    "size": f"{width:.2f}x{height:.2f}"
                },
                level=LogLevel.DEBUG
            )

    def _calculate_resized_rect(self, current_x: float, current_y: float) -> tuple:
        """
        リサイズ後のズーム領域の座標を計算（共通化されたロジック）
        Args:
            current_x (float): 現在のマウスX座標
            current_y (float): 現在のマウスY座標
        Returns:
            tuple: (x, y, width, height)
        """

        if not isinstance(self.press, ResizeOperationData):
            return None

        # 固定点を取得
        fixed_x, fixed_y = self.press.fixed_point

        # 現在のマウス座標と固定点の座標を比較して、リサイズの方向を決定
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

        width = x1 - x0
        height = y1 - y0

        return (x0, y0, width, height)

    def _update_rect_rotate(self, event):
        """ ズーム領域の回転の更新（キャッシュ対応・安全性強化版） """

        if not self.validator.validate_rotate(event, self):
            return

        # 回転中心と現在角度を計算
        cx = self.press.center_x
        cy = self.press.center_y
        initial_angle = self.press.initial_angle

        # 現在の角度を計算
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

    # on_release 関連--------------------------------------------------
    def on_release(self, event):

        if not self.validator.validate_basic_event(event, self):
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
        """ CREATE 状態でのリリース処理 """

        self.press = None
        self._finalize_rect(event)
        self._apply_min_size_constraints()
        self.state = ZoomState.WAIT_NOKEY_ZOOM_RECT_EXISTS

    def _handle_move_release(self, event):
        """ MOVE 状態でのリリース処理 """

        self.press = None
        self.state = ZoomState.WAIT_NOKEY_ZOOM_RECT_EXISTS

    def _handle_resize_release(self, event):
        """ RESIZE 状態でのリリース処理 """

        if self.rect is not None:
            self._apply_min_size_constraints()

        self.press = None

        if self.key_pressed['shift']:
            self.state = ZoomState.WAIT_SHIFT_RESIZE
        else:
            self.state = ZoomState.WAIT_NOKEY_ZOOM_RECT_EXISTS

    def _handle_rotate_release(self, event):
        """ ROTATE 状態でのリリース処理 """

        self.press = None

        if self.key_pressed['alt']:
            self.state = ZoomState.WAIT_ALT_ROTATE
        else:
            self.state = ZoomState.WAIT_NOKEY_ZOOM_RECT_EXISTS

    def _finalize_rect(self, event):
        """ ズーム領域の作成を確定し、最小サイズを保証する """

        # 終了点として現在のマウス位置を取得
        end_x, end_y = event.xdata, event.ydata

        # 開始点との差分を計算
        dx = end_x - self.start_x
        dy = end_y - self.start_y

        # ズーム領域の幅か高さが 0 の場合は、ズーム領域をクリアし、ズーム状態を NO_ZOOM_RECT に設定
        if dx == 0 or dy == 0:
            self._clear_rect()
            self.state = ZoomState.NO_ZOOM_RECT
            return

        # ズーム領域の位置とサイズを計算
        new_x = self.start_x if dx > 0 else end_x
        new_y = self.start_y if dy > 0 else end_y
        width = abs(dx)
        height = abs(dy)

        # ズーム領域を設定
        self.rect.set_bounds(new_x, new_y, width, height)

        self._invalidate_rect_cache()

        # ドラッグ方向を保存（最小サイズ適用時に使用）
        self.drag_direction = {
            'x': 'right' if dx > 0 else 'left',
            'y': 'up' if dy > 0 else 'down'
        }

    def _apply_min_size_constraints(self):
        """ ズーム領域のサイズが最小サイズ未満の場合、最小サイズを適用する """

        if self.rect is None:
            return

        x, y, width, height = self._get_rect_properties()

        new_width = max(width, self.MIN_RECT_SIZE)
        new_height = max(height, self.MIN_RECT_SIZE)

        # サイズ変更が必要ない場合は終了
        if abs(width - new_width) < 1e-6 and abs(height - new_height) < 1e-6:
            return

        # ドラッグ方向に基づいて拡張方向を決定
        if hasattr(self, 'drag_direction'):
            # 幅の拡張
            if width < new_width:
                if self.drag_direction['x'] == 'left':
                    x -= (new_width - width)  # 左方向に拡張
                # else: 右方向はデフォルトで拡張される

            # 高さの拡張
            if height < new_height:
                if self.drag_direction['y'] == 'down':
                    y -= (new_height - height)  # 下方向に拡張
                # else: 上方向はデフォルトで拡張される

        # ズーム領域を更新
        self.rect.set_bounds(x, y, new_width, new_height)

        self._invalidate_rect_cache()

        # デバッグログ出力
        if self._debug:
            self._log_debug_info(
                "ズーム領域：最小サイズ適用",
                context={
                    "original_size": f"{width:.2f}x{height:.2f}",
                    "new_size": f"{new_width:.2f}x{new_height:.2f}",
                    "position": f"({x:.2f}, {y:.2f})",
                    "direction": getattr(self, 'drag_direction', 'unknown')
                },
                level=LogLevel.DEBUG
            )

    # on_key_press 関連 --------------------------------------------------
    def on_key_press(self, event):

        # キー割り込みは、shift か alt キーが押された場合のみ実行
        if event.key not in ['shift', 'alt']:
            return

        # ズーム領域が有り、かつ shift か alt キーが押された場合のみ実行
        if self.state == ZoomState.WAIT_NOKEY_ZOOM_RECT_EXISTS and event.key in ['shift', 'alt']:

            # キーリピート対策：初めてキーが押された場合は Ture ではないので、処理を実行
                # 直後に True になるので、その後は実行しない
            if not self.key_pressed[event.key]:
                self.key_pressed[event.key] = True
                if self.key_pressed['shift']:
                    if self._get_pointer_near_corner(self._last_motion_event):
                        self.state = ZoomState.WAIT_SHIFT_RESIZE  # on_key_press：shift ON、カーソルが角許容範囲内
                elif self.key_pressed['alt']:
                    if self._get_pointer_near_corner(self._last_motion_event):
                        self.state = ZoomState.WAIT_ALT_ROTATE  # on_key_press：alt ON、カーソルが角許容範囲内
                self.canvas.draw()

        self.update_cursor(self._last_motion_event)

    # on_key_release 関連--------------------------------------------------
    def on_key_release(self, event):

        # 直前のマウスイベント情報があるかチェック(カーソル更新のために必要)
        if self._last_motion_event is None:
            return

        # 離されたキーが 'shift' または 'alt' でなければ無視
            # これを通過するなら、離されたキーが shift または alt であることが確定する
        if event.key not in ['shift', 'alt']:
            return

        # 離されたキーが self.key_pressed 辞書に含まれるか（追跡対象か）を確認する
            # 例えば、shift キーが離された場合、'shift' in self.key_pressed は True になりるので、
            # その後の処理が実行されて、self.key_pressed['shift'] は False になる
        if event.key in self.key_pressed:
            self.key_pressed[event.key] = False

        # 状態が変わったかどうかのフラグに、false を設定
        state_changed = False

        # Shift キーが離された場合
        if not self.key_pressed['shift']:

            # 状態が WAIT_SHIFT_RESIZE か RESIZE だったら、WAIT_NOKEY_ZOOM_RECT_EXISTS に戻す
            if self.state in (ZoomState.WAIT_SHIFT_RESIZE, ZoomState.RESIZE):
                self.state = ZoomState.WAIT_NOKEY_ZOOM_RECT_EXISTS  # on_key_release：shift OFF
                state_changed = True

        # Alt キーが離された場合
        if not self.key_pressed['alt']:
            # WAIT_ALT_ROTATE か ROTATE だったら、WAIT_NOKEY_ZOOM_RECT_EXISTS に戻す
            if self.state in (ZoomState.WAIT_ALT_ROTATE, ZoomState.ROTATE):
                self.state = ZoomState.WAIT_NOKEY_ZOOM_RECT_EXISTS  # on_key_release：alt OFF
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

    # -------------------------------------------------------------------------
    def _clear_rect(self):
        """ ズーム領域を完全にクリア（キャッシュ・状態もリセット） """

        # ズーム領域の削除
        if self.rect is not None:
            self.rect.remove()
            self.rect = None

        # 状態の完全リセット
        self._invalidate_rect_cache()  # キャッシュクリア
        self.last_rect = None  # 直前のズーム領域の情報をクリア
        self.press = None  # マウスボタン押下情報をクリア
        self.start_x = self.start_y = None  # 開始座標リセット

        # デバッグログ出力
        if self._debug:
            self._log_debug_info(
                "Rectangle cleared",
                level=LogLevel.INFO
            )

        # GUIの更新
        self.last_cursor_state = None  # カーソル状態を完全リセット
        self.canvas.get_tk_widget().config(cursor="arrow")

        self.canvas.draw()

    def _invalidate_rect_cache(self):
        """ ズーム領域のキャッシュを無効化する """

        # ズーム領域のキャッシュを無効化
        self._cached_rect_props = None

    def update_cursor(self, event):
        """ 各状態およびカーソル位置に応じたカーソル形状を設定する """

        if (not hasattr(event, 'xdata') or
            event.xdata is None or
            not hasattr(event, 'ydata') or
            event.ydata is None):

            self.canvas.get_tk_widget().config(cursor="arrow")

            return

        new_cursor = "arrow"

        # update_cursor：NO_ZOOM_AREA か CREATE 場合の処理
        if self.state in (ZoomState.NO_ZOOM_RECT, ZoomState.CREATE):
            new_cursor = "arrow"

        # update_cursor：MOVE の場合の処理
        elif self.state == ZoomState.MOVE:
            new_cursor = "fleur"

        # WAIT_SHIFT_RESIZE か RESIZE の場合は、角近傍なら crosshair、それ以外は arrow
        elif self.state in (ZoomState.WAIT_SHIFT_RESIZE, ZoomState.RESIZE):
            new_cursor = "crosshair" if self._get_pointer_near_corner(event) else "arrow"

        # WAIT_ALT_ROTATE か ROTATE の場合は、角近傍なら exchange、それ以外は arrow
        elif self.state in (ZoomState.WAIT_ALT_ROTATE, ZoomState.ROTATE):
            new_cursor = "exchange" if self._get_pointer_near_corner(event) else "arrow"

        # update_cursor：WAIT_NOKEY_ZOOM_AREA_EXISTSの場合の処理
        elif self.state == ZoomState.WAIT_NOKEY_ZOOM_RECT_EXISTS:
            new_cursor = "fleur" if self._cursor_inside_rect(event) else "arrow"

        else:
            new_cursor = "arrow"

        if new_cursor != self.last_cursor_state:  # 変更が有る場合のみ更新
            self.canvas.get_tk_widget().config(cursor=new_cursor)  # カーソルの形状を更新
            self.last_cursor_state = new_cursor  # カーソルの形状を更新

    def _cursor_inside_rect(self, event):
        """ マウスカーソルがズーム領域内部に在るかどうかを判定する """

        # ズーム領域が存在しない場合は False を返す
        if self.rect is None:
            return False

        # マウスカーソルがズーム領域に含まれるかどうかを判定
        contains, _ = self.rect.contains(event)

        # マウスカーソルがズーム領域内部に在る場合は True、そうでない場合は False を返す
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

        # コンテキストがNoneの場合のデフォルト値
        if context is None:
            context = {}

        # 状態遷移情報
        if old_state is not None and new_state is not None:
            context["state_change"] = f"{old_state.name} → {new_state.name}"

        # マウス位置
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

        context["mouse_pos"] = mouse_pos

        # キー状態
        context["key_status"] = f"shift: {self.key_pressed['shift']}, alt: {self.key_pressed['alt']}"

        # ズーム領域情報
        rect_props = self._get_rect_properties()
        context["rect"] = f"{rect_props}" if rect_props else "None"

        # リサイズ操作情報
        if self.press and isinstance(self.press, ResizeOperationData):
            resize_info = {
                "corner": self.press.corner_name,
                "fixed_point": f"({self.press.fixed_point[0]:.1f}, {self.press.fixed_point[1]:.1f})",
                "original_size": f"{self.press.original_width:.1f}x{self.press.original_height:.1f}",
                "press_pos": f"({self.press.press_x:.1f}, {self.press.press_y:.1f})"
            }
            context["resize_info"] = resize_info

        # 回転操作情報
        if self.press and isinstance(self.press, RotationOperationData):
            rotate_info = {
                "center": f"({self.press.center_x:.1f}, {self.press.center_y:.1f})",
                "initial_angle": f"{self.press.initial_angle:.1f}°"
            }
            context["rotate_info"] = rotate_info

        # イベント位置
        if hasattr(self, '_last_motion_event') and self._last_motion_event:
            e = self._last_motion_event
            context["event_pos"] = f"({e.xdata:.1f}, {e.ydata:.1f})"

        self.debug_logger.log(level, message, context)

    def _get_rect_properties(self):
        """
        ズーム領域の位置とサイズを取得する。内部キャッシュを使用して、繰り返し実行されるプロパティの取得を最適化する。
        Returns:
            tuple_or_None: ズーム領域の位置とサイズ（x, y, width, height）。ズーム領域が存在しない場合は None
        """
        # ズーム領域が存在しない場合は None を返す
        if self.rect is None:
            return None

        # キャッシュがない場合のみ計算
        if self._cached_rect_props is None:

            # ズーム領域の位置を取得
            x, y = self.rect.get_xy()

            # ズーム領域の位置とサイズをキャッシュ
            self._cached_rect_props = (x, y, self.rect.get_width(), self.rect.get_height())

        # キャッシュした情報を返す
        return self._cached_rect_props

    def _get_pointer_near_corner(self, event):
        """
        マウス位置がズーム領域の角に近いかどうかを判定する。
        許容範囲 tol = 0.1 * min(width, height)（ただし min が 0 の場合は 0.2）
        """

        if self.rect is None:
            return False

        # ズーム領域の位置とサイズを取得
        x, y, width, height = self._get_rect_properties()

        # 通常の許容範囲
        tol = 0.1 * min(width, height) if min(width, height) != 0 else 0.2

        # 角を特定
        corners = [(x, y), (x + width, y), (x, y + height), (x + width, y + height)]

        # 各角についてマウス位置との距離を計算
        for cx, cy in corners:
            if np.hypot(event.xdata - cx, event.ydata - cy) < tol:
                return True
        return False

class EventValidator:
    """ イベントバリデーションを一元化するクラス """

    @staticmethod
    def validate_basic_event(event, selector):
        """
        イベントの基本的な有効性をチェック
        Args:
            event: 検証するイベント
            selector: ZoomSelectorインスタンス
        Returns:
            bool: イベントが有効ならTrue
        """

        checks = [
            (hasattr(event, 'xdata') and hasattr(event, 'ydata'), "Missing coordinates"),
            (event.xdata is not None and event.ydata is not None, "None coordinates"),
            (hasattr(event, 'inaxes') and event.inaxes == selector.ax, "Invalid axes")
        ]
        return all(condition for condition, _ in checks)

    @staticmethod
    def validate_rect_operation(event, selector):
        """
        矩形操作に必要なバリデーション
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
        リサイズ操作に必要なバリデーション
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
        回転操作に必要なバリデーション
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
