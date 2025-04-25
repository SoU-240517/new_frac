import numpy as np
from typing import Dict, Tuple
from matplotlib.colors import Colormap
from ui.zoom_function.debug_logger import DebugLogger
from ..utils import _normalize_and_color

def distance(
    colored: np.ndarray,
    divergent_mask: np.ndarray,
    iterations: np.ndarray,
    z_vals: np.ndarray,
    cmap: Colormap,
    params: Dict,
    logger: DebugLogger
) -> None:
    """距離カラーリング
    Args:
        colored (np.ndarray): 出力用のRGBA配列 (形状: (h, w, 4), dtype=float32)
        divergent_mask (np.ndarray): 発散した点のマスク (形状: (h, w), dtype=bool)
        iterations (np.ndarray): 反復回数配列 (形状: (h, w), dtype=int)
        z_vals (np.ndarray): 複素数配列
        cmap (Colormap): 色マップ
        params (Dict): 着色パラメータ
        logger (DebugLogger): ロガーインスタンス
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
            colored[divergent] = cmap(norm_dist) * 255.0
        else:
            # 距離が全て同じ場合
            colored[divergent] = cmap(0.5) * 255.0
    else:
        # 発散点がない場合
        colored.fill(0)