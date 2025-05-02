import numpy as np
from matplotlib.colors import Colormap
from typing import Dict, Tuple
from debug import DebugLogger, LogLevel
from coloring.utils import _normalize_and_color

def apply_distance_coloring(
    colored: np.ndarray,
    divergent_mask: np.ndarray,
    z_vals: np.ndarray,
    cmap_func: Colormap,
    params: Dict,
    logger: DebugLogger
) -> None:
    """発散領域に対して、原点からの距離に基づいたカラーリングを適用する
    - 発散した点の原点からの距離を計算し、その距離に基づいて色を付ける
    Args:
        colored (np.ndarray): 出力先のRGBA配列 (形状: (h, w, 4), dtype=float32)
        divergent_mask (np.ndarray): 発散した点のマスク配列 (形状: (h, w), dtype=bool)
        z_vals (np.ndarray): 各点での複素数の値を持つ配列 (形状: (h, w), dtype=complex)
        cmap_func (Colormap): 発散領域の着色に使うカラーマップ関数
        params (Dict): 使用しない
        logger (DebugLogger): デバッグ用ロガー
    """
    # 発散した点の距離を計算
    divergent = divergent_mask
    dist = np.abs(z_vals[divergent])

    # 距離の範囲を正規化
    if len(dist) > 0:
        min_dist = np.min(dist)
        max_dist = np.max(dist)
        if max_dist > min_dist:
            # 0-1の範囲に正規化
            norm_dist = (dist - min_dist) / (max_dist - min_dist)
            colored[divergent] = cmap_func(norm_dist) * 255.0
        else:
            # 距離が全て同じ場合
            colored[divergent] = cmap_func(0.5) * 255.0
    else:
        # 発散点がない場合
        colored.fill(0)
