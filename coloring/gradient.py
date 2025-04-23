import numpy as np
from ui.zoom_function.debug_logger import DebugLogger
from ui.zoom_function.enums import LogLevel

"""グラデーション生成を担当
- 役割:
    - 設定されたパラメータでグラデーションを生成
"""
def compute_gradient(shape, logger: DebugLogger):
    """グラデーションを計算
    Args:
        shape (tuple): 画像サイズ
        logger (DebugLogger): ログ出力クラス
    """
    x, y = np.indices(shape) # 2D座標を生成
    logger.log(LogLevel.DEBUG, f"2D座標生成: {x.shape}, {y.shape}")
    normalized_distance = np.sqrt(
        # 中心からの距離を正規化
        (x - shape[0]/2)**2 + (y - shape[1]/2)**2) / np.sqrt((shape[0]/2)**2 + (shape[1]/2)**2)
    return normalized_distance
