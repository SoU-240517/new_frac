from enum import Enum, auto

class ZoomState(Enum):
    """ ズームセレクタの状態 """
    print('\033[34m'+'DIC INI: ZoomState: enums.py'+'\033[0m')
    NO_RECT = auto()  # 矩形がない、または確定済み
    CREATE = auto()   # 矩形を作成中 (ドラッグ中)
    EDIT = auto()    # 矩形を編集中
    # DISABLED = auto() # 将来的に無効状態を追加する場合

class LogLevel(Enum):
    """ ログレベル """
    print('\033[34m'+'DIC INI: LogLevel: enums.py'+'\033[0m')
    DEBUG = auto()
    INFO = auto()
    WARNING = auto()
    ERROR = auto()
