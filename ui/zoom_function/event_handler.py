from matplotlib.backend_bases import Event, MouseButton
from typing import Optional, TYPE_CHECKING
from .enums import LogLevel

# 他のクラスの型ヒントのためにインポート (循環参照回避)
if TYPE_CHECKING:
    from .zoom_selector import ZoomSelector
    from .zoom_state_handler import ZoomStateHandler
    from .rect_manager import RectManager
    from .cursor_manager import CursorManager
    from .event_validator import EventValidator
    from .debug_logger import DebugLogger

# Enumは直接インポート
from .enums import ZoomState, LogLevel

class EventHandler:
    """ matplotlibのイベントを処理し、各コンポーネントに指示を出すクラス """
    def __init__(self,
                selector: 'ZoomSelector',
                state_handler: 'ZoomStateHandler',
                rect_manager: 'RectManager',
                cursor_manager: 'CursorManager',
                validator: 'EventValidator',
                logger: 'DebugLogger',
                canvas):
        self.logger = logger
        self.logger.log(LogLevel.INIT, "EventHandler")
        self.selector = selector
        self.state_handler = state_handler
        self.rect_manager = rect_manager
        self.cursor_manager = cursor_manager
        self.validator = validator
        self.logger = logger
        self.canvas = canvas

        # イベント接続ID
        self._cid_press: Optional[int] = None
        self._cid_release: Optional[int] = None
        self._cid_motion: Optional[int] = None
        self._cid_key_press: Optional[int] = None

        # ドラッグ開始位置
        self.start_x: Optional[float] = None
        self.start_y: Optional[float] = None

    def _connect_motion(self):
        """ motion_notify_event を接続 """
        if self._cid_motion is None:
            self._cid_motion = self.canvas.mpl_connect('motion_notify_event', self.on_motion)
            self.logger.log(LogLevel.INFO, "motion_notify_event Connected.")

    def _disconnect_motion(self):
        """ motion_notify_event を切断 """
        if self._cid_motion is not None:
            self.canvas.mpl_disconnect(self._cid_motion)
            self._cid_motion = None
            self.logger.log(LogLevel.INFO, "motion_notify_event Disconnected.")

    def connect(self):
        """ イベントハンドラを接続 """
        if self._cid_press is None:
            self._cid_press = self.canvas.mpl_connect('button_press_event', self.on_press)
            self._cid_release = self.canvas.mpl_connect('button_release_event', self.on_release)
            self._cid_key_press = self.canvas.mpl_connect('key_press_event', self.on_key_press)
            self.logger.log(LogLevel.INFO, "Connection completed.", {
                "cid_press": self._cid_press, "cid_release": self._cid_release, "cid_key_press": self._cid_key_press})

    def disconnect(self):
        """ イベントハンドラを切断 """
        if self._cid_press is not None:
            self.canvas.mpl_disconnect(self._cid_press)
            self._cid_press = None
        if self._cid_release is not None:
            self.canvas.mpl_disconnect(self._cid_release)
            self._cid_release = None
        self._disconnect_motion()
        if self._cid_key_press is not None:
            self.canvas.mpl_disconnect(self._cid_key_press)
            self._cid_key_press = None
        self.logger.log(LogLevel.INFO, "All event handlers disconnected.")

    def on_press(self, event: Event):
        """ マウスボタンが押された時の処理 """
        if not self.validator.validate_basic(event, self.selector.ax, self.logger) or event.button != MouseButton.LEFT:
            return

        state = self.state_handler.get_state()
        self.logger.log(LogLevel.INFO, "Mouse press detected.", {"button": event.button, "x": event.xdata, "y": event.ydata, "state": state})

        if state == ZoomState.NO_RECT:
            # 矩形作成開始
            self.start_x, self.start_y = event.xdata, event.ydata
            self.rect_manager.create_rect_start(self.start_x, self.start_y)
            self.state_handler.update_state(ZoomState.CREATE)
            self._connect_motion() # <<<--- motion イベントを接続
            self.cursor_manager.cursor_update(event)
            self.canvas.draw_idle()

    def on_motion(self, event: Event):
        """ マウスが動いた時の処理 """
        self.logger.log(LogLevel.METHOD, "on_motion")
        if event.inaxes != self.selector.ax and self.state_handler.get_state() != ZoomState.CREATE:
            return
        if event.xdata is None or event.ydata is None:
            return

        if self.start_x is not None and self.start_y is not None:
            self.rect_manager.update_creation( # 矩形を作成中なら更新
                self.start_x, self.start_y, event.xdata, event.ydata)
            self.canvas.draw_idle() # 再描画を要求

    def on_release(self, event: Event):
        """ マウスボタンが離された時の処理 """
        if event.button != MouseButton.LEFT:
            return

        state = self.state_handler.get_state() # 現在の状態を取得しておく

        # 座標が取れない場合の処理
        if event.xdata is None or event.ydata is None:
            if state == ZoomState.CREATE:
                self.logger.log(LogLevel.WARNING, "Mouse released outside axes during creation, cancelling.")
                self._disconnect_motion() # motion イベントを切断
                self.selector.cancel_zoom()
            return

        self.logger.log(LogLevel.DEBUG, "Mouse release detected.", {
            "button": event.button, "x": event.xdata, "y": event.ydata, "state": state})

        if state == ZoomState.CREATE:
            self._disconnect_motion() # motion イベントを切断
            if self.start_x is not None and self.start_y is not None:
                self.rect_manager.finalize_creation(self.start_x, self.start_y, event.xdata, event.ydata)
                self.state_handler.update_state(ZoomState.EDIT, {"action": "preparation"})

#                success = self.rect_manager.finalize_creation(self.start_x, self.start_y, event.xdata, event.ydata)
#                if success:
                    # confirm_zoom の中で状態が NO_RECT に更新される
#                    self.selector.confirm_zoom()
#                else:
                    # finalize_creation が False を返した場合 (例: 小さすぎる矩形)
#                    self.state_handler.update_state(ZoomState.NO_RECT) # 状態を直接更新

            self.start_x = None
            self.start_y = None
            self.cursor_manager.cursor_update(event)
            self.canvas.draw_idle()

    def on_key_press(self, event: Event):
        """ キーボードが押された時の処理 """
        self.logger.log(LogLevel.DEBUG, "Key press detected", {"key": event.key})
        if event.key == 'escape':
            state = self.state_handler.get_state()
            if state == ZoomState.CREATE:
                self.logger.log(LogLevel.INFO, "Rectangle creation cancelled by ESC.")
                self._disconnect_motion() # <<<--- motion イベントを切断
                # cancel_zoomの中で clear や状態更新が行われる
                self.selector.cancel_zoom()
                self.canvas.draw_idle()

    def reset_internal_state(self):
        """ イベントハンドラ内部の状態をリセット """
        self.start_x = None
        self.start_y = None
        self.logger.log(LogLevel.DEBUG, "EventHandler internal state reset.")
