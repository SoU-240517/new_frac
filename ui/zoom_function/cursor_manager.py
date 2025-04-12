import tkinter as tk
from matplotlib.backend_bases import MouseEvent, Event
from typing import Optional, TYPE_CHECKING
from .debug_logger import DebugLogger
from .enums import ZoomState, LogLevel

if TYPE_CHECKING:
    from .zoom_state_handler import ZoomStateHandler
    from .zoom_selector import ZoomSelector

# Tkinterの標準カーソル名 (必要に応じて調整)
# 参考: https://anzeljg.github.io/rin2/book2/2405/docs/tkinter/cursors.html
CURSOR_DEFAULT = "" # 標準カーソル (通常は矢印)
CURSOR_CROSSHAIR = "crosshair" # 十字カーソル (矩形作成時)
CURSOR_RESIZE_NW_SE = "size_nw_se" # 左上/右下リサイズ
CURSOR_RESIZE_NE_SW = "size_ne_sw" # 右上/左下リサイズ
CURSOR_MOVE = "fleur" # 移動カーソル (全方向矢印)
CURSOR_ROTATE = "exchange" # 回転カーソル (例: exchange, または circle, dotbox など試す)

class CursorManager:
    """ マウスカーソルの形状を管理するクラス """
    def __init__(self, canvas_widget, logger: Optional[DebugLogger]): # logger の型ヒントを Optional に変更
        """
        CursorManager クラスのコンストラクタ
        Args:
            canvas_widget: Tkinter Canvas ウィジェット (FigureCanvasTkAgg.get_tk_widget())
            logger: DebugLogger インスタンス、または None
        """
        self.widget = canvas_widget
        self.logger = logger
        # logger が None でないことを確認してからログを記録
        self.logger.log(LogLevel.INIT, "CursorManager")
        self._current_cursor = CURSOR_DEFAULT
        self.zoom_selector: Optional['ZoomSelector'] = None # zoom_selector の初期化と型ヒント

#    def _log(self, level: LogLevel, message: str):
#        """ logger が存在する場合にログを記録する """
#        if self.logger:
#            try:
#                self.logger.log(level, message)
#            except Exception as e:
#                # logger.log でエラーが発生した場合に備える (例: logger が期待通りでない場合)
#                print(f"[CursorManager Log Error] Failed to log message: {message}. Error: {e}")

    def cursor_update(self,
                      event: Optional[MouseEvent],
                      state: ZoomState, # 現在の状態を引数で受け取る
                      near_corner_index: Optional[int] = None,
                      is_rotating: bool = False):
        """
        イベントと状態に基づいてカーソル形状を更新する。

        Args:
            event: MouseEvent オブジェクト (Noneの場合、デフォルトカーソルに戻す)
            state: 現在の ZoomState
            near_corner_index: 近接している角のインデックス (0-3)。Noneの場合は角に近くない
            is_rotating: 回転モードが有効かどうか
        """
        new_cursor = CURSOR_DEFAULT # デフォルトは標準カーソル

        if event and event.inaxes: # Axes 内の場合のみカーソルを変更
            if is_rotating and near_corner_index is not None: # 回転モードで、かつ角に近い場合
                new_cursor = CURSOR_ROTATE
            elif not is_rotating and near_corner_index is not None: # 回転モードでない場合、かつ角に近い場合
                if near_corner_index in [0, 3]:
                    new_cursor = CURSOR_RESIZE_NW_SE
                else:
                    new_cursor = CURSOR_RESIZE_NE_SW
            elif state == ZoomState.CREATE:
                new_cursor = CURSOR_CROSSHAIR
            elif state == ZoomState.ON_MOVE:
                new_cursor = CURSOR_MOVE
            elif state == ZoomState.EDIT:
                # zoom_selector が設定されているか、かつ None でないか確認
                if self.zoom_selector and hasattr(self.zoom_selector, 'cursor_inside_rect') and self.zoom_selector.cursor_inside_rect(event):
                    new_cursor = CURSOR_MOVE
                else:
                    new_cursor = CURSOR_DEFAULT
            elif state == ZoomState.RESIZING:
                 pass # near_corner_index is not None の分岐で処理
            elif state == ZoomState.ROTATING:
                 pass # is_rotating and near_corner_index is not None の分岐で処理
        else: # Axes 外またはイベントがない場合
            new_cursor = CURSOR_DEFAULT
        if new_cursor != self._current_cursor: # カーソルが変更されている場合のみ更新
            try: # カーソルの設定に失敗した場合の例外処理
                self.widget.config(cursor=new_cursor)
                self._current_cursor = new_cursor
                self.logger.log(LogLevel.SUCCESS, f"カーソル変更 to '{new_cursor}'")
            except tk.TclError as e:
                self.logger.log(LogLevel.ERROR, f"カーソルの設定に失敗 '{new_cursor}': {e}")
                try: # 不明なカーソル名の場合、デフォルトに戻す
                    if self._current_cursor != CURSOR_DEFAULT:
                        self.widget.config(cursor=CURSOR_DEFAULT)
                        self._current_cursor = CURSOR_DEFAULT
                        self._log(LogLevel.WARNING, f"カーソル変更失敗 '{new_cursor}' デフォルトに戻す")
                except tk.TclError as e_reset:
                     self.logger.log(LogLevel.ERROR, f"エラー後、カーソルをデフォルトにリセットできない: {e_reset}")
                     pass # これも失敗したら諦める

    def set_default_cursor(self):
        """ カーソルをデフォルトに戻す """
        if self._current_cursor != CURSOR_DEFAULT:
            try:
                self.widget.config(cursor=CURSOR_DEFAULT)
                self._current_cursor = CURSOR_DEFAULT
            except tk.TclError as e:
                self.logger.log(LogLevel.ERROR, f"カーソルをデフォルトにできない: {e}")

    def set_zoom_selector(self, zoom_selector: 'ZoomSelector'):
        """ ZoomSelector のインスタンスへの参照を設定 """
        self.zoom_selector = zoom_selector
        self.logger.log(LogLevel.INFO, "CursorManager に設定された ZoomSelector インスタンスへの参照終了")
