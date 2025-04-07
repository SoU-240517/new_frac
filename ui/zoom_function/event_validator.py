from matplotlib.axes import Axes
from matplotlib.backend_bases import Event

class EventValidator:
    """イベントの基本的な妥当性をチェックするクラス"""
    @staticmethod
    def validate_basic(event: Event, ax: Axes) -> bool:
        """基本的なイベント検証"""
        print("イベント検証 : validate_basic : CLASS→ EventValidator : FILE→ event_validator.py")
        # event.inaxes でイベントが指定されたAxes内で発生したかチェック
        # event.xdata, event.ydata が None でないことも保証される (inaxes is not Noneの場合)
        # event.button でマウスボタンが押されたイベントかチェック（Noneでない）
        return event.inaxes == ax and event.button is not None
