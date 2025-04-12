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
        Args:
            canvas_widget: Tkinter Canvas ウィジェット (FigureCanvasTkAgg.get_tk_widget())
            logger: DebugLogger インスタンス、または None
        """
        self.widget = canvas_widget
        self.logger = logger
        # logger が None でないことを確認してからログを記録
        self._log(LogLevel.INIT, "CursorManager")
        self._current_cursor = CURSOR_DEFAULT
        self.zoom_selector: Optional['ZoomSelector'] = None # zoom_selector の初期化と型ヒント

    # 内部ログ記録用ヘルパーメソッド
    def _log(self, level: LogLevel, message: str):
        """ logger が存在する場合にログを記録する """
        if self.logger:
            try:
                self.logger.log(level, message)
            except Exception as e:
                # logger.log でエラーが発生した場合に備える (例: logger が期待通りでない場合)
                print(f"[CursorManager Log Error] Failed to log message: {message}. Error: {e}")


    # シグネチャに state: ZoomState を追加
    def cursor_update(self,
                      event: Optional[MouseEvent],
                      state: ZoomState, # 現在の状態を引数で受け取る
                      near_corner_index: Optional[int] = None,
                      is_rotating: bool = False):
        """
        イベントと状態に基づいてカーソル形状を更新する。

        Args:
            event: MouseEvent オブジェクト (Noneの場合、デフォルトカーソルに戻す)。
            state: 現在の ZoomState。
            near_corner_index: 近接している角のインデックス (0-3)。Noneの場合は角に近くない。
            is_rotating: 回転モードが有効かどうか。
        """
        new_cursor = CURSOR_DEFAULT # デフォルトは標準カーソル

        if event and event.inaxes: # Axes 内の場合のみカーソルを変更
            if is_rotating and near_corner_index is not None:
                new_cursor = CURSOR_ROTATE
                # self._log(LogLevel.DEBUG, f"Cursor set to ROTATE (corner {near_corner_index})")
            elif not is_rotating and near_corner_index is not None:
                if near_corner_index in [0, 3]:
                    new_cursor = CURSOR_RESIZE_NW_SE
                else:
                    new_cursor = CURSOR_RESIZE_NE_SW
                # self._log(LogLevel.DEBUG, f"Cursor set to RESIZE (corner {near_corner_index})")
            elif state == ZoomState.CREATE:
                new_cursor = CURSOR_CROSSHAIR
                # self._log(LogLevel.DEBUG, "Cursor set to CREATE (crosshair)")
            elif state == ZoomState.MOVE:
                 new_cursor = CURSOR_MOVE
                 # self._log(LogLevel.DEBUG, "Cursor set to MOVE")
            elif state == ZoomState.EDIT:
                 # zoom_selector が設定されているか、かつ None でないか確認
                 if self.zoom_selector and hasattr(self.zoom_selector, 'cursor_inside_rect') and self.zoom_selector.cursor_inside_rect(event):
                     new_cursor = CURSOR_MOVE
                     # self._log(LogLevel.DEBUG, "Cursor set to MOVE (inside rect in EDIT)")
                 else:
                     new_cursor = CURSOR_DEFAULT
                     # self._log(LogLevel.DEBUG, "Cursor set to DEFAULT (in EDIT, not near corner/inside)")
            # RESIZING, ROTATING の状態は near_corner_index の条件でカバーされる
            elif state == ZoomState.RESIZING:
                 pass # near_corner_index is not None の分岐で処理
            elif state == ZoomState.ROTATING:
                 pass # is_rotating and near_corner_index is not None の分岐で処理
            # 他の状態 (NO_RECT など) ではデフォルトカーソルが使われる
        else:
            # Axes 外またはイベントがない場合
            # self._log(LogLevel.DEBUG, "Cursor set to DEFAULT (outside axes or no event)")
            new_cursor = CURSOR_DEFAULT

        if new_cursor != self._current_cursor:
            try:
                self.widget.config(cursor=new_cursor)
                self._current_cursor = new_cursor
                self._log(LogLevel.CALL, f"カーソル変更 to '{new_cursor}'")
            except tk.TclError as e:
                self._log(LogLevel.ERROR, f"カーソルの設定に失敗 '{new_cursor}': {e}")
                try:
                    # 不明なカーソル名の場合、デフォルトに戻す
                    if self._current_cursor != CURSOR_DEFAULT:
                        self.widget.config(cursor=CURSOR_DEFAULT)
                        self._current_cursor = CURSOR_DEFAULT
                        self._log(LogLevel.WARNING, f"カーソル変更失敗 '{new_cursor}' デフォルトに戻す")
                except tk.TclError as e_reset:
                     self._log(LogLevel.ERROR, f"エラー後、カーソルをデフォルトにリセットできない: {e_reset}")
                     pass # これも失敗したら諦める

    def set_default_cursor(self):
        """ カーソルをデフォルトに戻す """
        if self._current_cursor != CURSOR_DEFAULT:
            try:
                self.widget.config(cursor=CURSOR_DEFAULT)
                self._current_cursor = CURSOR_DEFAULT
            except tk.TclError as e:
                self._log(LogLevel.ERROR, f"カーソルをデフォルトにできない: {e}")

    # ZoomSelector への参照を保持するためのメソッド
    def set_zoom_selector(self, zoom_selector: 'ZoomSelector'): # 型ヒントを追加
        """ ZoomSelector のインスタンスへの参照を設定します。 """
        self.zoom_selector = zoom_selector
        self._log(LogLevel.INFO, "CursorManager に設定された ZoomSelector インスタンスへの参照終了")
