"""
Zoom機能を実装するためのモジュール群

主な機能:
- ズーム領域の描画と編集
- カーソルの管理
- ズーム状態の管理
- イベント処理
"""

from .cursor_manager import CursorManager
from .enum_rect import ZoomState
from .event_handler_core import EventHandler
from .event_handlers_private import EventHandlersPrivate
from .event_handlers_utils import EventHandlersUtils
from .rect_manager import RectManager
from .zoom_selector import ZoomSelector
from .zoom_state_handler import ZoomStateHandler

__all__ = [
    'CursorManager',
    'ZoomState'
    'EventHandler',
    'EventHandlersPrivate',
    'EventHandlersUtils',
    'RectManager',
    'ZoomSelector',
    'ZoomStateHandler',
]

__version__ = '0.0.0'
