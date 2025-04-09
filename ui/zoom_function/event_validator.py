from matplotlib.axes import Axes
from matplotlib.backend_bases import Event
from .debug_logger import DebugLogger
from .enums import LogLevel

class EventValidator:
    """イベントの基本的な妥当性をチェックするクラス"""
    @staticmethod
    def validate_basic(event: Event, ax: Axes, logger: DebugLogger) -> bool:
        """基本的なイベント検証"""
        logger.log(LogLevel.DEBUG, "validation: Basic event")
        # event.inaxes でイベントが指定されたAxes内で発生したかチェック
        # event.button でマウスボタンが押されたイベントかチェック（Noneでない）
        return event.inaxes == ax and event.button is not None
