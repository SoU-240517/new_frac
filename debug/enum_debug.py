from enum import Enum, auto

class LogLevel(Enum):
    """ ログレベル """
    DEBUG = auto()
    INIT = auto() # 初期化処理
    CALL = auto() # メソッド呼出し元
    SUCCESS = auto()
    INFO = auto()
    WARNING = auto()
    ERROR = auto()
    CRITICAL = auto()
