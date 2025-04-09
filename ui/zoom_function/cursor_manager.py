from matplotlib.backend_bases import Event
from typing import Optional, TYPE_CHECKING
from .debug_logger import DebugLogger

# ZoomStateHandlerクラスの型ヒントのためにインポートするが、
# 循環参照を避けるためTYPE_CHECKINGブロック内でインポート
if TYPE_CHECKING:
    from .zoom_state_handler import ZoomStateHandler

from .enums import ZoomState, LogLevel # ZoomStateはEnumなので直接インポートしてOK

class CursorManager:
    """ マウスカーソルの形状を管理するクラス """
    def __init__(self,
                canvas,
                state_handler: 'ZoomStateHandler',
                logger: DebugLogger):
        self.logger = logger
        self.logger.log(LogLevel.INIT, "CursorManager")
        self.canvas = canvas
        self.state_handler = state_handler
        self.last_cursor_state: Optional[str] = None # tkのカーソル名

    def cursor_update(self, event: Optional[Event] = None):
        """ 現在の状態に応じてカーソル形状を更新 """
        current_state = self.state_handler.get_state()
        new_cursor: str

        if current_state == ZoomState.CREATE:
            new_cursor = 'crosshair'
        else: # NO_RECT または他の状態
            new_cursor = 'arrow'

        if new_cursor != self.last_cursor_state:
            try:  # カーソルの更新を試みる
                widget = self.canvas.get_tk_widget()  # キャンバスのTkインターフェースを取得
                if widget:
                    widget.config(cursor=new_cursor)
                    self.last_cursor_state = new_cursor
                    self.logger.log(LogLevel.INFO, "Previous cursor state.", {"cursor": self.last_cursor_state})
                else:
                    pass
            except AttributeError:
                 pass # Tk以外のバックエンドの場合など

    def cursor_reset(self):
        """ カーソルをデフォルト (arrow) に戻す """
        self.logger.log(LogLevel.METHOD, "cursor_reset")
        self.last_cursor_state = None # 強制的に更新させる
        try:
            widget = self.canvas.get_tk_widget()
            if widget:
                widget.config(cursor='arrow')
            else:
                pass
        except AttributeError:
            pass
