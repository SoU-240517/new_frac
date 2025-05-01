import numpy as np
from debug.debug_logger import DebugLogger
from debug.enum_debug import LogLevel

"""グラデーション生成モジュール
このモジュールは画像処理用のグラデーションパターンを生成する
生成されたグラデーションは、画像の色付けや効果の適用に使用される
"""

def compute_gradient(shape, logger: DebugLogger):
    """画像サイズに基づいた2Dグラデーションを計算する
    - 指定された形状の2次元グラデーション配列を生成する
    - グラデーションは画像の中心から外側に向かって放射状に変化する
    Args:
        shape (tuple): グラデーション配列の形状（高さ, 幅）を示すタプル
        logger (DebugLogger): デバッグログ出力用のロガークラス
    Returns:
        np.ndarray: 正規化された距離値を含む2D配列
            - 配列の値は0.0（中心）から1.0（端）の範囲で変化する
            - 画像の中心からの距離に応じて線形に増加する
    Raises:
        ValueError: shapeが不正な値の場合
            - shapeが2要素のタプルでない場合
            - shapeの要素が0以下の場合
    Notes:
        - 生成されるグラデーションは画像の中心を基準とした円形
        - グラデーションの値は中心から端に向かって線形に増加
        - 距離の計算にはユークリッド距離を使用
    """
    # shapeのバリデーション
    if len(shape) != 2 or shape[0] <= 0 or shape[1] <= 0:
        raise ValueError(f"Invalid shape: {shape}. Must be positive integers.")

    # 画像の2D座標を生成
    x, y = np.indices(shape)
    logger.log(LogLevel.DEBUG, f"2D座標生成: {x.shape}, {y.shape}") # 生成された座標の形状をログ出力

    # 中心座標の計算（奇数サイズの補正を含む）
    center_x = shape[0] / 2
    center_y = shape[1] / 2
    if shape[0] % 2 == 1: center_x += 0.5 # 奇数幅の場合、中心X座標を0.5ピクセル分シフト
    if shape[1] % 2 == 1: center_y += 0.5 # 奇数高さの場合、中心Y座標を0.5ピクセル分シフト

    # 中心からの距離を計算し、正規化
    normalized_distance = np.sqrt(
        (x - center_x)**2 + (y - center_y)**2
    ) / np.sqrt((shape[0]/2)**2 + (shape[1]/2)**2) # 最大距離で正規化

    logger.log(LogLevel.DEBUG, f"正規化された距離範囲: {normalized_distance.min()} to {normalized_distance.max()}") # 正規化された距離の最小値と最大値をログ出力

    return normalized_distance
