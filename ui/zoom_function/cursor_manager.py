import tkinter as tk
from matplotlib.backend_bases import MouseEvent, Event
from typing import Optional, TYPE_CHECKING
from .debug_logger import DebugLogger
from .enums import ZoomState, LogLevel
from .event_validator import EventValidator, ValidationResult

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
    """マウスカーソルの形状を操作状態に応じて変更するクラス
    - 役割:
        - イベントと状態に基づいてカーソル形状を更新する
        - イベントと状態に基づいて矩形を更新する
    """
    def __init__(self, canvas_widget, logger: Optional[DebugLogger]):
        """CursorManager クラスのコンストラクタ（親: ZoomSelector)）

        Args:
            canvas_widget: Tkinter Canvas ウィジェット (FigureCanvasTkAgg.get_tk_widget())
            logger: DebugLogger インスタンス、または None
        """
        self.widget = canvas_widget
        self.logger = logger
        # logger が None でないことを確認してからログを記録
        self._current_cursor = CURSOR_DEFAULT
        self.zoom_selector: Optional['ZoomSelector'] = None
        # Validatorインスタンスが必要な場合 (通常は EventHandler が持っているものを共有)
        # self.validator = EventValidator() # 必要に応じてインスタンス化

    def cursor_update(self,
                      event: Optional[MouseEvent],
                      state: ZoomState, # 現在の状態を引数で受け取る
                      near_corner_index: Optional[int] = None,
                      is_rotating: bool = False):
        """イベントと状態に基づいてカーソル形状を更新する

        Args:
            event: MouseEvent オブジェクト (Noneの場合、デフォルトカーソルに戻す)
            state: 現在の ZoomState
            near_corner_index: 近接している角のインデックス (0-3)。Noneの場合は角に近くない
            is_rotating: 回転モードが有効かどうか
        """
        new_cursor = CURSOR_DEFAULT # デフォルトは標準カーソル
        # --- イベント検証 ---
        validation_result = None
        if event and self.zoom_selector: # イベントと zoom_selector が存在する場合のみ検証
             # EventHandlerが持っているvalidatorインスタンスを使うのが通常
             # ここでは EventValidator.validate_event を直接呼び出す例
            validation_result = EventValidator.validate_event(
                event, self.zoom_selector.ax, self.logger
            )
            # カーソル更新に必要なのは Axes 内であることと座標があること
            should_update_cursor = validation_result.is_in_axes and validation_result.has_coords
        else:
            should_update_cursor = False # イベントがない、または検証できない場合は更新しない
        # --- 検証ここまで ---
        if should_update_cursor:
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
                # zoom_selector が設定されているか、かつ None でないか確認 (should_update_cursorで確認済み)
                if self.zoom_selector.cursor_inside_rect(event): # cursor_inside_rect は event を引数に取る
                    new_cursor = CURSOR_MOVE
                else:
                    # 角に近くない、かつ矩形の内側でもない場合
                    new_cursor = CURSOR_DEFAULT # または適切なカーソル
            else:
                 # 上記以外の場合 (例: EDIT状態で矩形外かつ角にも近くない)
                 new_cursor = CURSOR_DEFAULT # デフォルトに戻す
        else:
            # 検証失敗またはイベントがない場合はデフォルトカーソル
            new_cursor = CURSOR_DEFAULT
        if new_cursor != self._current_cursor:
            try:
                self.widget.config(cursor=new_cursor)
                self._current_cursor = new_cursor
                self.logger.log(LogLevel.SUCCESS, f"カーソル変更 to '{new_cursor}'", {"state": state.name})
            except tk.TclError as e:
                self.logger.log(LogLevel.ERROR, f"カーソルの設定に失敗 '{new_cursor}': {e}")

    def set_default_cursor(self):
        """カーソルをデフォルトに戻す"""
        if self._current_cursor != CURSOR_DEFAULT:
            try:
                self.widget.config(cursor=CURSOR_DEFAULT)
                self._current_cursor = CURSOR_DEFAULT
            except tk.TclError as e:
                self.logger.log(LogLevel.ERROR, f"カーソルをデフォルトにできない: {e}")

    def set_zoom_selector(self, zoom_selector: 'ZoomSelector'):
        """ZoomSelector のインスタンスへの参照を設定

        Args:
            zoom_selector: ZoomSelector インスタンス
        """
        self.logger.log(LogLevel.INIT, "CursorManager に ZoomSelector インスタンスへの参照を設定")
        self.zoom_selector = zoom_selector
        self.logger.log(LogLevel.INIT, "CursorManager に設定された ZoomSelector インスタンスへの参照終了")
