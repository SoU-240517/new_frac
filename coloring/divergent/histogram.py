import numpy as np
from typing import Dict, Tuple
from matplotlib.colors import Colormap
from ui.zoom_function.debug_logger import DebugLogger

def apply_histogram_flattening(
    colored: np.ndarray,
    divergent_mask: np.ndarray,
    iterations: np.ndarray,
    cmap: Colormap,
    params: Dict,
    logger: DebugLogger
) -> None:
    """ヒストグラム平坦化法
    Args:
        colored (np.ndarray): 出力用のRGBA配列 (形状: (h, w, 4), dtype=float32)
        divergent_mask (np.ndarray): 発散した点のマスク (形状: (h, w), dtype=bool)
        iterations (np.ndarray): 反復回数配列 (形状: (h, w), dtype=int)
        cmap (Colormap): 色マップ
        params (Dict): 着色パラメータ
        logger (DebugLogger): ロガーインスタンス
    """
    divergent = iterations > 0
    hist, bins = np.histogram(iterations[divergent], bins=params["max_iterations"], density=True)
    cdf = hist.cumsum()
    cdf = cdf / cdf[-1]
    remapped = np.interp(iterations[divergent], bins[:-1], cdf)
    colored[divergent] = cmap(remapped) * 255.0
