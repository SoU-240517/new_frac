import numpy as np
from typing import Dict, Tuple
from matplotlib.colors import Colormap

def histogram_equalization(z: np.ndarray, iterations: np.ndarray, params: Dict, cmap: Colormap) -> np.ndarray:
    """ヒストグラム平坦化着色
    Args:
        z (np.ndarray): 複素数配列
        iterations (np.ndarray): 反復回数配列
        params (Dict): 着色パラメータ
        cmap (Colormap): 色マップ
    Returns:
        np.ndarray: 着色されたRGBA配列
    """
    non_divergent = iterations <= 0
    hist, bins = np.histogram(iterations[non_divergent], bins=256)
    cdf = hist.cumsum()
    cdf_normalized = cdf / cdf[-1]
    gamma = 1.5
    cdf_normalized = cdf_normalized ** (1/gamma)
    equalized = np.interp(iterations[non_divergent], bins[:-1], cdf_normalized)
    colored = np.zeros((*iterations.shape, 4), dtype=np.float32)
    colored[non_divergent] = cmap(equalized) * 255.0
    return colored