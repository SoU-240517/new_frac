# cursor_manager.py
from matplotlib.backend_bases import Event
from typing import Optional, TYPE_CHECKING

# ZoomStateHandlerクラスの型ヒントのためにインポートするが、
# 循環参照を避けるためTYPE_CHECKINGブロック内でインポート
if TYPE_CHECKING:
    from .zoom_state_handler import ZoomStateHandler

from .enums import ZoomState # ZoomStateはEnumなので直接インポートしてOK

class CursorManager:
    """ マウスカーソルの形状を管理するクラス """
    def __init__(self, canvas, state_handler: 'ZoomStateHandler'):
        print("初期化 : CLASS→ CursorManager : FILE→ cursor_manager.py")
        self.canvas = canvas
        self.state_handler = state_handler
        self.last_cursor_state: Optional[str] = None # tkのカーソル名

    def update(self, event: Optional[Event] = None):
        """ 現在の状態に応じてカーソル形状を更新 """
        print("更新 : update : CLASS→ CursorManager : FILE→ cursor_manager.py")
        current_state = self.state_handler.get_state()
        new_cursor: str

        if current_state == ZoomState.CREATE:
            new_cursor = 'crosshair' # 十字カーソル
        else: # NO_RECT または他の状態
            new_cursor = 'arrow'     # 通常の矢印カーソル

        if new_cursor != self.last_cursor_state:
            try:
                widget = self.canvas.get_tk_widget()
                if widget:
                    widget.config(cursor=new_cursor)
                    self.last_cursor_state = new_cursor
                else:
                    pass
            except AttributeError:
                 pass # Tk以外のバックエンドの場合など

    def reset(self):
        """ カーソルをデフォルト (arrow) に戻す """
        print("リセット : reset : CLASS→ CursorManager : FILE→ cursor_manager.py")
        self.last_cursor_state = None # 強制的に更新させる
        try:
            widget = self.canvas.get_tk_widget()
            if widget:
                widget.config(cursor='arrow')
            else:
                pass
        except AttributeError:
            pass
