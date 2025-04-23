import numpy as np
from ui.zoom_function.debug_logger import DebugLogger
from ui.zoom_function.enums import LogLevel

"""グラデーション生成モジュール
このモジュールは画像処理用のグラデーションパターンを生成する
生成されたグラデーションは、画像の色付けや効果の適用に使用される
"""

def compute_gradient(shape, logger: DebugLogger):
    """画像サイズに基づいた2Dグラデーションを計算する
    Args:
        shape (tuple): 画像のサイズ（高さ, 幅）
        logger (DebugLogger): デバッグログの出力用クラス
    Returns:
        np.ndarray: 正規化された距離値を含む2D配列
            - 値の範囲: 0.0 (中心) から 1.0 (端)
            - 中心からの距離に応じて線形に変化
    Notes:
        - 生成されるグラデーションは円形で、画像の中心から端に向かって
          値が0から1に線形に増加する
        - 計算はピクセルの座標と画像の中心との距離に基づいて行われる
    """
    # 画像の2D座標を生成
    x, y = np.indices(shape)
    logger.log(LogLevel.DEBUG, f"2D座標生成: {x.shape}, {y.shape}")

    # 中心からの距離を計算し、正規化
    normalized_distance = np.sqrt(
        # 中心からの距離を正規化
        (x - shape[0]/2)**2 + (y - shape[1]/2)**2) / np.sqrt((shape[0]/2)**2 + (shape[1]/2)**2)
    
    return normalized_distance
