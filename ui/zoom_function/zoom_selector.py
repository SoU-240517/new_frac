from matplotlib.axes import Axes
from typing import Callable, Optional
# --- 以下、他の自作クラスやEnumをインポート ---
from .enums import ZoomState, LogLevel
from .debug_logger import DebugLogger
from .event_validator import EventValidator
from .zoom_state_handler import ZoomStateHandler
from .rect_manager import RectManager
from .cursor_manager import CursorManager
from .event_handler import EventHandler # EventHandlerをインポート

class ZoomSelector:
    """
    マウスドラッグで矩形を描画する機能を持つクラス (機能限定版)
    """
    def __init__(self, ax: Axes,
                 on_zoom_confirm: Callable[[float, float, float, float], None],
                 on_zoom_cancel: Callable[[], None],
                 debug_enabled: bool = True):
        self.ax = ax
        self.canvas = ax.figure.canvas
        self.on_zoom_confirm = on_zoom_confirm # ユーザーが指定するコールバック関数
        self.on_zoom_cancel = on_zoom_cancel   # ユーザーが指定するコールバック関数

        # --- 各コンポーネントの初期化 ---
        self.logger = DebugLogger(debug_enabled=debug_enabled)
        self.state_handler = ZoomStateHandler(initial_state=ZoomState.NO_RECT, logger=self.logger)
        self.rect_manager = RectManager(ax, self.logger)
        self.cursor_manager = CursorManager(self.canvas, self.state_handler)
        self.validator = EventValidator()
        # EventHandlerに他のコンポーネントへの参照を渡す
        self.event_handler = EventHandler(
            self, self.state_handler, self.rect_manager, self.cursor_manager,
            self.validator, self.logger, self.canvas
        )
        # --- 初期化ここまで ---

        # 初期状態でイベントを接続
        self.connect_events()
        self.logger.log(LogLevel.INFO, "ZoomSelector initialized and events connected.")

    def connect_events(self):
        """ イベントハンドラの接続 """
        self.logger.log(LogLevel.DEBUG, "Connecting events via EventHandler.")
        self.event_handler.connect()
        self.cursor_manager.update()

    def disconnect_events(self):
        """ イベントハンドラの切断 """
        self.logger.log(LogLevel.DEBUG, "Disconnecting events via EventHandler.")
        self.event_handler.disconnect()
        self.cursor_manager.reset()

    def confirm_zoom(self):
        """ (内部用) 矩形が確定された時に呼ばれる """
        rect_props = self.rect_manager.get_properties()
        if rect_props:
            self.logger.log(LogLevel.INFO, f"Zoom rectangle confirmed: x={rect_props[0]:.2f}, y={rect_props[1]:.2f}, w={rect_props[2]:.2f}, h={rect_props[3]:.2f}")
            self.on_zoom_confirm(rect_props[0], rect_props[1], rect_props[2], rect_props[3])
            self.state_handler.update_state(ZoomState.NO_RECT, {"action": "confirm"})
            self.cursor_manager.update()
        else:
            self.logger.log(LogLevel.WARNING, "Confirm attempted but no valid rectangle exists.")

    def cancel_zoom(self):
        """ (内部用) キャンセル時に呼ばれる (主にESCキー or 外部からの呼び出し) """
        self.logger.log(LogLevel.INFO, "Zoom operation cancelled.")
        self.rect_manager.clear()
        self.state_handler.update_state(ZoomState.NO_RECT, {"action": "cancel"})
        self.event_handler.reset_internal_state() # 開始座標などもリセット
        self.cursor_manager.update()
        self.on_zoom_cancel()

    def reset(self):
        """ ZoomSelectorの状態をリセット """
        self.logger.log(LogLevel.INFO, "ZoomSelector reset.")
        self.rect_manager.clear()
        self.state_handler.update_state(ZoomState.NO_RECT, {"action": "reset"})
        self.event_handler.reset_internal_state()
        self.cursor_manager.update()
        # reset時もキャンセルコールバックを呼ぶか、あるいは別のコールバックを用意するかは設計次第
        # self.on_zoom_cancel()
