from matplotlib.axes import Axes
from typing import Callable
from .enums import ZoomState, LogLevel
from .event_validator import EventValidator
from .zoom_state_handler import ZoomStateHandler
from .rect_manager import RectManager
from .cursor_manager import CursorManager
from .debug_logger import DebugLogger
from .event_handler import EventHandler

class ZoomSelector:
    """ マウスドラッグで矩形を描画する機能を持つクラス (機能限定版) """
    def __init__(self,
                ax: Axes,
                on_zoom_confirm: Callable[[float, float, float, float], None],
                on_zoom_cancel: Callable[[], None],
                logger: DebugLogger):
        """ ZoomSelector の初期化 """
        self.logger = logger # logger をインスタンス変数として保持
        self.logger.log(LogLevel.INIT, "ZoomSelector")
        self.ax = ax # 描画対象の Axes オブジェクト
        self.canvas = ax.figure.canvas # 描画対象の Figure の Canvas オブジェクト
        self.on_zoom_confirm = on_zoom_confirm # ユーザーが指定するコールバック関数
        self.on_zoom_cancel = on_zoom_cancel # ユーザーが指定するコールバック関数

        # --- 各コンポーネントの初期化 ---
        self.state_handler = ZoomStateHandler(
                                initial_state=ZoomState.NO_RECT,
                                logger=self.logger,
                                canvas=self.canvas)

        self.rect_manager = RectManager(ax, self.logger)
        # 修正: CursorManager の初期化時に self を渡す
        self.cursor_manager = CursorManager(self.canvas, self.state_handler, self, self.logger)
        self.validator = EventValidator()

        # EventHandlerに他のコンポーネントへの参照を渡す
        self.event_handler = EventHandler(self,
                                        self.state_handler,
                                        self.rect_manager,
                                        self.cursor_manager,
                                        self.validator,
                                        self.logger, # 引数で受け取った logger を渡す
                                        self.canvas)

        self.state_handler.event_handler = self.event_handler # StateHandler に EventHandler の参照を設定
        # --- 初期化ここまで ---

        # 初期状態でイベントを接続
        self.connect_events()

    def connect_events(self):
        """ イベントハンドラの接続 """
        self.logger.log(LogLevel.INFO, "Connecting events.")
        self.event_handler.connect() # EventHandlerに他のコンポーネントへの参照を渡す
        self.cursor_manager.cursor_update() # カーソルの初期化

    def disconnect_events(self):
        """ イベントハンドラの切断 """
        self.logger.log(LogLevel.INFO, "Disconnecting events.")
        self.event_handler.disconnect() # EventHandlerに他のコンポーネントへの参照を渡す
        self.cursor_manager.cursor_reset() # カーソルのリセット

    def cursor_inside_rect(self, event) -> bool:
        """ マウスカーソル位置がズーム領域内か判定する """
        rect_props = self.rect_manager.get_rect()
        contains, _ = rect_props.contains(event)
        return contains

    def confirm_zoom(self):
        """ ズーム領域決定 """
        rect_props = self.rect_manager.get_properties()
        if rect_props:
            self.logger.log(LogLevel.INFO, "Zoom rectangle confirmed.", {
                "x": rect_props[0], "y": rect_props[1], "w": rect_props[2], "h": rect_props[3]})
            self.on_zoom_confirm(rect_props)
            self.state_handler.update_state(ZoomState.NO_RECT, {"action": "confirm"})
            self.cursor_manager.cursor_update()
        else:
            self.logger.log(LogLevel.WARNING, "Confirm attempted but no valid rectangle exists.")

    def cancel_zoom(self):
        """ (内部用) キャンセル時に呼ばれる (主にESCキー or 外部からの呼び出し) """
        self.logger.log(LogLevel.INFO, "Zoom operation cancelled.")
        self.rect_manager.clear()
        self.state_handler.update_state(ZoomState.NO_RECT, {"action": "cancel"})
        self.event_handler.reset_internal_state() # 開始座標などもリセット
        self.cursor_manager.cursor_update()
        self.on_zoom_cancel()

    def reset(self):
        """ ZoomSelectorの状態をリセット """
        self.logger.log(LogLevel.INFO, "ZoomSelector reset.")
        self.rect_manager.clear()
        self.state_handler.update_state(ZoomState.NO_RECT, {"action": "reset"})
        self.event_handler.reset_internal_state()
        self.cursor_manager.cursor_update()
        # reset時もキャンセルコールバックを呼ぶか、あるいは別のコールバックを用意するかは設計次第
        # self.on_zoom_cancel()
