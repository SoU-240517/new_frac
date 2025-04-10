from matplotlib.backend_bases import Event
from typing import Optional, TYPE_CHECKING
from .debug_logger import DebugLogger
from .enums import ZoomState, LogLevel

if TYPE_CHECKING:
    from .zoom_state_handler import ZoomStateHandler
    from .zoom_selector import ZoomSelector

class CursorManager:
    """ マウスカーソルの形状を管理するクラス """
    def __init__(self,
                canvas,
                state_handler: 'ZoomStateHandler',
                zoom_selector: 'ZoomSelector',
                logger: DebugLogger):
        self.logger = logger
        self.logger.log(LogLevel.INIT, "CursorManager")
        self.canvas = canvas
        self.state_handler = state_handler
        self.zoom_selector = zoom_selector
        self.last_cursor_state: Optional[str] = None # tkのカーソル名

    def cursor_update(self, event: Optional[Event] = None):
        """ 現在の状態に応じてカーソル形状を更新 """
        current_state = self.state_handler.get_state() # 現在の状態を取得
        new_cursor: str

        if current_state == ZoomState.CREATE:
            new_cursor = 'crosshair'
        elif current_state == ZoomState.EDIT:
            new_cursor = "fleur" if self.zoom_selector.cursor_inside_rect(event) else "arrow"
        else: # NO_RECT または他の状態
            new_cursor = 'arrow'

        if new_cursor != self.last_cursor_state:
            try:  # カーソルの更新を試みる
                widget = self.canvas.get_tk_widget()  # キャンバスのTkインターフェースを取得
                if widget:
                    widget.config(cursor=new_cursor)
                    self.last_cursor_state = new_cursor
                    self.logger.log(LogLevel.DEBUG, "success.", {"to": new_cursor, "previous_cursor": self.last_cursor_state})
                else:
                    self.logger.log(LogLevel.WARNING, "Failed. Could not get Tk widget to update cursor.")
            except AttributeError: # Tkinterのバックエンドを使用していない場合、AttributeErrorが発生することがあります
                 self.logger.log(LogLevel.WARNING, "AttributeError: Likely not using Tk backend, skipping cursor update.")
                 pass

    def cursor_reset(self):
        """ カーソルをデフォルト (arrow) に戻す """

        self.last_cursor_state = None # 強制的に更新させる
        try:
            widget = self.canvas.get_tk_widget()
            if widget:
                self.logger.log(LogLevel.INFO, "Change cursor back to arrow.")
                widget.config(cursor='arrow')
            else:
                pass
        except AttributeError:
            pass
