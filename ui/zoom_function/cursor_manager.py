import tkinter as tk
from matplotlib.backend_bases import MouseEvent, Event
from typing import Optional, TYPE_CHECKING
from .debug_logger import DebugLogger
from .enums import ZoomState, LogLevel
from .event_validator import EventValidator, ValidationResult

if TYPE_CHECKING:
    from .zoom_state_handler import ZoomStateHandler
    from .zoom_selector import ZoomSelector

# カーソル定義
CURSORS = {
    'default': '',
    'crosshair': 'crosshair',
    'resize_nw_se': 'size_nw_se',
    'resize_ne_sw': 'size_ne_sw',
    'move': 'fleur',
    'rotate': 'exchange'
}

class CursorManager:
    """マウスカーソルの形状を操作状態に応じて変更するクラス
    - 役割:
        - イベントと状態に基づいてカーソル形状を更新する
        - カーソルの状態を管理する
    """

    def __init__(self, zoom_selector: 'ZoomSelector', logger: DebugLogger) -> None:
        """CursorManagerの初期化
        
        Args:
            zoom_selector: ZoomSelectorインスタンス
            logger: ログ出力用の DebugLogger インスタンス
        """
        self.zoom_selector = zoom_selector
        self.logger = logger
        self.validator = EventValidator(logger)
        self._current_cursor = CURSORS['default']
        self._canvas_widget = getattr(zoom_selector.canvas, 'get_tk_widget', lambda: None)()
        if self._canvas_widget is None:
            raise ValueError("Tkinter ウィジェット取得不可：FigureCanvasTkAgg の使用を要確認")

    def cursor_update(self,
                      event: Optional[MouseEvent],
                      state: ZoomState,
                      near_corner_index: Optional[int] = None,
                      is_rotating: bool = False) -> None:
        """イベントと状態に基づいてカーソル形状を更新する
        Args:
            event: MouseEvent オブジェクト
            state: 現在の ZoomState
            near_corner_index: 近接している角のインデックス
            is_rotating: 回転モードが有効かどうか
        """
        if not self._should_update_cursor(event):
            return

        new_cursor = self._determine_cursor(event, state, near_corner_index, is_rotating)

        if new_cursor != self._current_cursor:
            self._update_cursor(new_cursor, state)

    def _should_update_cursor(self, event: MouseEvent) -> bool:
        """カーソル更新が必要かを判定
        
        Args:
            event: MouseEvent オブジェクト
            
        Returns:
            bool: カーソル更新が必要か
        """
        if not event.inaxes:
            return False

        validation_result = self.validator.validate_event(event, self.zoom_selector.ax)
        return validation_result.is_in_axes and validation_result.has_coords

    def _determine_cursor(self,
                         event: MouseEvent,
                         state: ZoomState,
                         near_corner_index: Optional[int],
                         is_rotating: bool) -> str:
        """カーソルの種類を決定する
        Args:
            event: MouseEvent オブジェクト
            state: 現在の状態
            near_corner_index: 近接している角のインデックス
            is_rotating: 回転モードが有効かどうか
        Returns:
            str: カーソルの種類
        """
        if is_rotating:
            return CURSORS['rotate'] if near_corner_index is not None else CURSORS['default']

        if near_corner_index is not None:
            return CURSORS['resize_nw_se'] if near_corner_index in [0, 3] else CURSORS['resize_ne_sw']

        if state == ZoomState.CREATE:
            return CURSORS['crosshair']
        elif state == ZoomState.ON_MOVE:
            return CURSORS['move']
        elif state == ZoomState.EDIT:
            return CURSORS['move'] if self.zoom_selector.cursor_inside_rect(event) else CURSORS['default']

        return CURSORS['default']

    def _update_cursor(self, new_cursor: str, state: ZoomState) -> None:
        """カーソルを更新する
        Args:
            new_cursor: 新しいカーソルの種類
            state: 現在の状態
        """
        try:
            self._canvas_widget.config(cursor=new_cursor)
            self._current_cursor = new_cursor
            self.logger.log(LogLevel.SUCCESS, f"カーソル変更 to '{new_cursor}'", {"state": state.name})
        except tk.TclError as e:
            self.logger.log(LogLevel.ERROR, f"カーソル変更失敗: {e}", {"state": state.name})

    def set_default_cursor(self) -> None:
        """カーソルをデフォルトに戻す"""
        if self._current_cursor != CURSORS['default']:
            self._update_cursor(CURSORS['default'], ZoomState.DEFAULT)
