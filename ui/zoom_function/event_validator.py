from matplotlib.axes import Axes
from matplotlib.backend_bases import MouseEvent
from .debug_logger import DebugLogger
from .enums import LogLevel

class EventValidator:
    """イベントの基本的な妥当性をチェックするクラス"""
    @staticmethod
    def validate_basic(event: MouseEvent, ax: Axes, logger: DebugLogger) -> bool:
        """基本的なイベント検証"""
        return (
            event.inaxes == ax and # event.inaxes でイベントが指定されたAxes内で発生したかチェック
            event.button is not None # event.button でマウスボタンが押されたイベントかチェック（Noneでない）
        )
