from enum import Enum, auto

class ZoomState(Enum):
    """ ズームセレクタの状態 """
    NO_RECT = auto() # 矩形がない、または確定済み
    CREATE = auto() # 矩形を作成中 (ドラッグ中)
    EDIT = auto() # 矩形を編集中
    ON_MOVE = auto() # 矩形を移動中
    RESIZING = auto() # 矩形をリサイズ中
    ROTATING = auto() # 矩形を回転中
