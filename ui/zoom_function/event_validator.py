from matplotlib.axes import Axes
from matplotlib.backend_bases import Event

class EventValidator:
    """イベントの基本的な妥当性をチェックするクラス"""
    @staticmethod
    def validate_basic(event: Event, ax: Axes) -> bool:
        """基本的なイベント検証"""
        print('\033[32m'+'validate_basic: EventValidator: event_validator.py'+'\033[0m')
        # event.inaxes でイベントが指定されたAxes内で発生したかチェック
        # event.xdata, event.ydata が None でないことも保証される (inaxes is not Noneの場合)
        # event.button でマウスボタンが押されたイベントかチェック（Noneでない）
        return event.inaxes == ax and event.button is not None
