from enum import Enum, auto

class ZoomState(Enum):
    """ ズームセレクタの状態 """
    NO_RECT = auto()  # 矩形がない、または確定済み
    CREATE = auto()   # 矩形を作成中 (ドラッグ中)
    # DISABLED = auto() # 将来的に無効状態を追加する場合

class LogLevel(Enum):
    """ ログレベル """
    DEBUG = auto()
    INFO = auto()
    WARNING = auto()
    ERROR = auto()
