import numpy as np
from matplotlib.colors import Colormap
from typing import Dict, Tuple
from debug import DebugLogger, LogLevel

def apply_histogram_equalization(
    colored: np.ndarray,
    non_divergent_mask: np.ndarray,
    iterations: np.ndarray,
    non_cmap_func: Colormap,
    params: Dict,
    logger: DebugLogger
) -> None:
    """非発散領域をヒストグラム平坦化によって着色する
    - 非発散領域の反復回数の分布を均等化し、その結果を用いて着色を行う
    Args:
        colored (np.ndarray): 出力用のRGBA配列 (形状: (h, w, 4), dtype=float32)
        non_divergent_mask (np.ndarray): 非発散点のマスク配列 (形状: (h, w), dtype=bool)
        iterations (np.ndarray): 反復回数配列
        non_cmap_func (Colormap): 非発散領域の着色に使用するカラーマップ関数
        params (Dict): 使用しない
        logger (DebugLogger): デバッグ用ロガーインスタンス
    """
    # 非発散領域の反復回数のヒストグラムを計算
    hist, bins = np.histogram(iterations[non_divergent_mask], bins=256)

    # ヒストグラムの累積分布関数（CDF）を計算し、0-1の範囲に正規化
    cdf = hist.cumsum()
    cdf_normalized = cdf / cdf[-1]

    # ガンマ補正を適用して色の遷移を調整
    gamma = 1.5  # 1.0～2.0の範囲で調整
    cdf_normalized = cdf_normalized ** (1/gamma)

    # 正規化されたCDFを使用して反復回数を新しい値にマッピング
    equalized = np.interp(iterations[non_divergent_mask], bins[:-1], cdf_normalized)

    # 正規化された値をカラーマップに適用し、0-255の範囲に変換
    colored[non_divergent_mask] = non_cmap_func(equalized) * 255.0
