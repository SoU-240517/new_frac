import numpy as np
from typing import Dict, Tuple
from matplotlib.colors import Colormap
from ui.zoom_function.debug_logger import DebugLogger
from ui.zoom_function.enums import LogLevel

def apply_histogram_equalization(
    colored: np.ndarray,
    non_divergent_mask: np.ndarray,
    iterations: np.ndarray,
    non_cmap_func: Colormap, # 正しいカラーマップ関数を受け取る
    params: Dict,
    logger: DebugLogger
) -> None:
    """非発散部：統計分布で着色
    Args:
        colored (np.ndarray): 出力用のRGBA配列 (形状: (h, w, 4), dtype=float32)
        non_divergent_mask (np.ndarray): 非発散した点のマスク (形状: (h, w), dtype=bool)
        iterations (np.ndarray): 反復回数配列
        non_cmap_func (Colormap): 非発散部分用のカラーマップ関数
        params (Dict): 着色パラメータ
            - gradient_type: 'linear' | 'radial'
            - gradient_size: グラデーションのサイズ
            - gradient_position: (x, y) の座標
        logger (DebugLogger): ロガーインスタンス
    """
    # 非発散部分の反復回数のヒストグラムを作成
    hist, bins = np.histogram(iterations[non_divergent_mask], bins=256)

    # 累積分布関数（CDF）を計算し、0-1の範囲に正規化
    cdf = hist.cumsum()
    cdf_normalized = cdf / cdf[-1]

    # ガンマ補正
    # 1.5: カラートランジションをより自然に見せる
    # 1.0: 線形補正
    # 2.0: より急なトランジション
    gamma = 1.5  # 1.0～2.0で調整
    cdf_normalized = cdf_normalized ** (1/gamma)

    # 正規化された値を新しい値にマッピング
    equalized = np.interp(iterations[non_divergent_mask], bins[:-1], cdf_normalized)

    # 正規化された位相値をカラーマップに適用
    # 結果を255倍して0-255の範囲に変換
    colored[non_divergent_mask] = non_cmap_func(equalized) * 255.0
