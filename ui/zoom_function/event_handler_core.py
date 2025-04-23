from matplotlib.backend_bases import MouseEvent, MouseButton, KeyEvent
from typing import Optional, TYPE_CHECKING, Tuple, List, Dict, Any
from .enums import LogLevel, ZoomState
from .event_handlers_private import EventHandlersPrivate
from .event_handlers_utils import EventHandlersUtils

# 型ヒント用インポート (循環参照回避)
if TYPE_CHECKING:
    from .cursor_manager import CursorManager
    from .debug_logger import DebugLogger
    from .event_validator import EventValidator
    from .rect_manager import RectManager
    from .zoom_selector import ZoomSelector
    from .zoom_state_handler import ZoomStateHandler

class EventHandler:
    """マウス/キーボードイベントを処理し、適切な操作に変換するクラス
    - 役割:
        - matplotlib のイベントを処理し、各コンポーネントに指示を出す
        - イベントの種類と現在の状態に応じて、具体的な処理を行うクラスに処理を委譲する（振り分ける）
    """
    # ズーム領域回転時の振動を調整するためのパラメータ
    ROTATION_THRESHOLD = 2.0 # この値以下の角度変化（度単位）は無視して更新しない
    ROTATION_SENSITIVITY = 1.0 # 角度変化の感度係数 (0.0 < 値 <= 1.0)。1.0で変更なし。小さくすると鈍くなる

    # スロットリングの設定
    ROTATION_THROTTLE_INTERVAL = 1 / 60 # 秒 (60fps相当に制限)
    _last_rotation_update_time = 0 # 最後に回転処理を実行した時刻

    def __init__(self,
                 zoom_selector: 'ZoomSelector',
                 state_handler: 'ZoomStateHandler',
                 rect_manager: 'RectManager',
                 cursor_manager: 'CursorManager',
                 validator: 'EventValidator',
                 logger: 'DebugLogger',
                 canvas):
        """イベントハンドラのコンストラクタ（親: ZoomSelector）

        Args:
            zoom_selector: ZoomSelector インスタンス
            state_handler: ZoomStateHandler インスタンス
            rect_manager: RectManager インスタンス
            cursor_manager: CursorManager インスタンス
            validator: EventValidator インスタンス
            logger: DebugLogger インスタンス
            canvas: FigureCanvasTkAgg インスタンス
        """
        self.logger = logger

        # 依存コンポーネント
        self.zoom_selector = zoom_selector
        self.state_handler = state_handler
        self.rect_manager = rect_manager
        self.cursor_manager = cursor_manager
        self.validator = validator
        self.canvas = canvas

        # 分割した他のクラスのインスタンスを作成
        self.logger.log(LogLevel.INIT, "EventHandlersPrivate クラスのインスタンスを作成")
        self.private_handlers = EventHandlersPrivate(self)
        self.logger.log(LogLevel.INIT, "EventHandlersUtils クラスのインスタンスを作成")
        self.utils = EventHandlersUtils(self)

        # --- 内部状態 ---
        # ログ出力フラグ（プライベートハンドラや utils に移動しても良いが、ここではコアに残しておく）
        self._create_logged = False
        self._move_logged = False
        self._resize_logged = False
        self._rotate_logged = False

        # イベント接続ID
        self._cid_press: Optional[int] = None
        self._cid_release: Optional[int] = None
        self._cid_motion: Optional[int] = None
        self._cid_key_press: Optional[int] = None
        self._cid_key_release: Optional[int] = None

        # ドラッグ開始位置 (矩形作成用)
        self.start_x: Optional[float] = None
        self.start_y: Optional[float] = None

        # 矩形移動用
        self.move_start_x: Optional[float] = None # 移動開始時のマウスX座標
        self.move_start_y: Optional[float] = None # 移動開始時のマウスY座標
        self.rect_start_pos: Optional[Tuple[float, float]] = None # 移動開始時の矩形左下座標（x, y）

        # 矩形リサイズ用
        self.resize_corner_index: Optional[int] = None # リサイズ中の角のインデックス（0-3）
        self.fixed_corner_pos: Optional[Tuple[float, float]] = None # リサイズ中の固定された対角の座標

        # 矩形回転用
        self._alt_pressed: bool = False # Altキーが押されているか
        self.rotate_start_mouse_pos: Optional[Tuple[float, float]] = None # 回転開始時のマウス座標
        self.rotate_center: Optional[Tuple[float, float]] = None # 回転中心座標
        self.previous_vector_angle: Optional[float] = None # 前回のベクトル角度

        # Undo 用の編集履歴（履歴自体はutilsで管理するが、リストの変数はコアに残しておく）
        self.edit_history: List[Optional[Dict[str, Any]]] = []
		# --- 内部状態ここまで ---

    def connect(self):
        """全イベントハンドラを接続"""
        if self._cid_press is None: # すでに接続されている場合は何もしない
            self._cid_press = self.canvas.mpl_connect('button_press_event', self.on_press)
            self._cid_motion = self.canvas.mpl_connect('motion_notify_event', self.on_motion)
            self._cid_release = self.canvas.mpl_connect('button_release_event', self.on_release)
            self._cid_key_press = self.canvas.mpl_connect('key_press_event', self.on_key_press)
            self._cid_key_release = self.canvas.mpl_connect('key_release_event', self.on_key_release)

    # --- イベント処理メソッド (ディスパッチャ) ---
    def on_press(self, event: MouseEvent) -> None:
        """マウスボタン押下イベントのディスパッチャ
        Args:
            event: MouseEvent オブジェクト
        """
        validation_result = self.validator.validate_event(event, self.zoom_selector.ax)
        if not validation_result.is_press_valid:
            self.logger.log(LogLevel.ERROR, "基本検証失敗：処理中断")
            return

        state = self.state_handler.state
        self.logger.log(LogLevel.DEBUG, f"状態取得完了：{state.name}, ボタン={event.button}")

        if state == ZoomState.NO_RECT:
            if event.button == MouseButton.LEFT:
                self.private_handlers.handle_press_no_rect_left(event)
        elif state == ZoomState.EDIT:
            if event.button == MouseButton.LEFT:
                self.private_handlers.dispatch_press_edit_left(event)
            elif event.button == MouseButton.RIGHT:
                self.private_handlers.handle_press_edit_right_confirm(event)

    def on_motion(self, event: MouseEvent) -> None:
        """マウス移動イベントのディスパッチャ
        Args:
            event: MouseEvent オブジェクト
        """
        validation_result = self.validator.validate_event(event, self.zoom_selector.ax)
        if not (validation_result.is_in_axes and validation_result.has_coords):
            self.logger.log(LogLevel.WARNING, "Axes外または座標無効のため処理中断")
            return

        state = self.state_handler.state
        # self.logger.log(LogLevel.DEBUG, f"状態取得完了：{state.name}")

        if state == ZoomState.CREATE:
            if event.button == MouseButton.LEFT:
                self.private_handlers.handle_motion_create(event)
        elif state == ZoomState.EDIT:
            self.private_handlers.handle_motion_edit(event)
        elif state == ZoomState.ON_MOVE:
            if event.button == MouseButton.LEFT:
                self.private_handlers.handle_motion_move(event)
        elif state == ZoomState.RESIZING:
            if event.button == MouseButton.LEFT:
                self.private_handlers.handle_motion_resizing(event)
        elif state == ZoomState.ROTATING:
            if event.button == MouseButton.LEFT:
                self.private_handlers.handle_motion_rotating(event)

    def on_release(self, event: MouseEvent) -> None:
        """マウスボタン解放イベントのディスパッチャ
        Args:
            event: MouseEvent オブジェクト
        """
        validation_result = self.validator.validate_event(event, self.zoom_selector.ax)
        is_outside = not validation_result.has_coords # 軸外でのリリースか

        state = self.state_handler.state
        self.logger.log(LogLevel.DEBUG, f"状態取得完了：{state.name}, ボタン={event.button}, 軸外={is_outside}")

        operation_ended = False
        final_state_to_set = ZoomState.EDIT # デフォルトは操作完了後のEDIT状態

        if state == ZoomState.CREATE:
            if event.button == MouseButton.LEFT:
                final_state_to_set = self.private_handlers.handle_release_create(event, is_outside)
                operation_ended = True
        elif state == ZoomState.ON_MOVE:
            if event.button == MouseButton.LEFT:
                final_state_to_set = self.private_handlers.handle_release_move(event)
                operation_ended = True
        elif state == ZoomState.RESIZING:
            if event.button == MouseButton.LEFT:
                final_state_to_set = self.private_handlers.handle_release_resizing(event)
                operation_ended = True
        elif state == ZoomState.ROTATING:
            if event.button == MouseButton.LEFT:
                final_state_to_set = self.private_handlers.handle_release_rotating(event)
                operation_ended = True

        if operation_ended: # 操作が終了した場合の共通後処理
            self.state_handler.update_state(final_state_to_set, {"action": f"{state.name}：操作終了"})
            self.zoom_selector.invalidate_rect_cache()

            # Altキーの状態も考慮してカーソルを更新
            self.cursor_manager.cursor_update(event, state=final_state_to_set, is_rotating=self._alt_pressed)
            self.canvas.draw_idle()

    def on_key_press(self, event: KeyEvent) -> None:
        """キーボード押下イベントのディスパッチャ
        Args:
            event: KeyEvent オブジェクト
        """
        if event.key == 'escape':
            self.private_handlers._handle_key_escape(event)
        elif event.key == 'alt':
            if not self.rect_manager.get_rect(): return
            self.private_handlers.handle_key_alt_press(event)
            corner_index = self.zoom_selector.pointer_near_corner(event)
            self.cursor_manager.cursor_update(event, state=ZoomState.ROTATING, near_corner_index=corner_index, is_rotating=self._alt_pressed)
            self.canvas.draw_idle()
        # 他のキー処理が必要なら追加

    def on_key_release(self, event: KeyEvent) -> None:
        """キーボード解放イベントのディスパッチャ
        Args:
            event: KeyEvent オブジェクト
        """
        if event.key == 'alt':
            if not self.rect_manager.get_rect(): return
            self.private_handlers.handle_key_alt_release(event)
            corner_index = self.zoom_selector.pointer_near_corner(event)
            self.cursor_manager.cursor_update(event, state=ZoomState.EDIT, near_corner_index=corner_index, is_rotating=self._alt_pressed)
            self.canvas.draw_idle()
        # 他のキー処理が必要なら追加
    # --- イベント処理メソッド (ディスパッチャ) ここまで ---

    # --- 状態リセットメソッド ---
    def reset_internal_state(self):
        """全ての内部状態と編集履歴をリセット"""
        # EventHandler の公開メソッドとして残しておく
        # ただし、内部での具体的なリセット処理は utils に依頼する
        self.utils.reset_internal_state()
    # --- 状態リセットメソッド ここまで ---

    # --- Undo 関連メソッド ---
    def clear_edit_history(self):
        """編集履歴をクリア"""
        # EventHandler の公開メソッドとして残しておく
        # ただし、内部での具体的なクリア処理は utils に依頼する
        self.utils.clear_edit_history()
    # --- Undo 関連メソッド ここまで ---
