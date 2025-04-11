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
        self.last_cursor_state: Optional[str] = None # tkのカーソル名初期値

        # 角インデックスとTkカーソル名のマッピング
        self._resize_cursors = {
            0: "size_nw_se", # 左上(NW)
            1: "size_ne_sw", # 右上(NE)
            2: "size_ne_sw", # 左下(SW)
            3: "size_nw_se"  # 右下(SE)
        }

    def cursor_update(self, event: Optional[Event] = None, near_corner_index: Optional[int] = None):
        """ 現在の状態とマウス位置に応じてカーソル形状を更新 """
        current_state = self.state_handler.get_state() # 現在の状態を取得
        new_cursor: str

        if current_state == ZoomState.CREATE:
            new_cursor = 'crosshair'
        elif current_state == ZoomState.EDIT:
            if near_corner_index is not None:
                # 角に近い場合はリサイズカーソル
                new_cursor = self._resize_cursors.get(near_corner_index, "arrow") # 不明なインデックスならarrow
                self.logger.log(LogLevel.DEBUG, f"Near corner {near_corner_index}, setting cursor to {new_cursor}")
            elif event and self.zoom_selector.cursor_inside_rect(event):
                new_cursor = "fleur" # 矩形内部（角以外）なら移動カーソル
            else:
                new_cursor = "arrow" # 矩形外部ならデフォルトカーソル
        elif current_state == ZoomState.RESIZING:
            # リサイズ中は、開始した角に対応するリサイズカーソルを表示
            resize_corner = self.zoom_selector.event_handler.resize_corner_index
            if resize_corner is not None:
                new_cursor = self._resize_cursors.get(resize_corner, "arrow")
                self.logger.log(LogLevel.DEBUG, f"Resizing from corner {resize_corner}, setting cursor to {new_cursor}")
            else:
                # 通常は発生しないはずだが、念のため
                new_cursor = "arrow"
                self.logger.log(LogLevel.WARNING, "In RESIZING state but resize_corner_index is None.")
        elif current_state == ZoomState.MOVE:
            new_cursor = "fleur" # 移動中は移動カーソル
        else: # NO_RECT または他の未定義状態
            new_cursor = 'arrow'

        if new_cursor != self.last_cursor_state:
            try:  # カーソルの更新を試みる
                widget = self.canvas.get_tk_widget()  # キャンバスのTkインターフェースを取得
                if widget:
                    widget.config(cursor=new_cursor)
                    self.logger.log(LogLevel.SUCCESS, f"success. from '{self.last_cursor_state}' to '{new_cursor}'.")
                    self.last_cursor_state = new_cursor
                else:
                    self.logger.log(LogLevel.WARNING, "Failed. Could not get Tk widget to update cursor.")
            except AttributeError: # Tkinterのバックエンドを使用していない場合、AttributeErrorが発生することがあります
                 self.logger.log(LogLevel.WARNING, "AttributeError: Likely not using Tk backend, skipping cursor update.")
                 pass
            except Exception as e: # その他の予期せぬエラー
                 self.logger.log(LogLevel.ERROR, f"Failed to update cursor: {e}")
                 pass

    def cursor_reset(self):
        """ カーソルをデフォルト (arrow) に戻す """
        default_cursor = 'arrow'
        if self.last_cursor_state != default_cursor:
            try:
                widget = self.canvas.get_tk_widget()
                if widget:
                    self.logger.log(LogLevel.DEBUG, "Resetting cursor to arrow.")
                    widget.config(cursor=default_cursor)
                    self.last_cursor_state = default_cursor
                else:
                    self.logger.log(LogLevel.WARNING, "Failed to reset cursor. Could not get Tk widget.")
            except AttributeError:
                self.logger.log(LogLevel.WARNING, "AttributeError: Likely not using Tk backend, skipping cursor reset.")
                pass
            except Exception as e:
                self.logger.log(LogLevel.ERROR, f"Failed to reset cursor: {e}")
                pass
        else:
            self.logger.log(LogLevel.DEBUG, "Cursor is already default (arrow). No reset needed.")
