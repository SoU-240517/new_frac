import numpy as np
from typing import Dict, Tuple
from matplotlib.colors import Colormap

def internal_distance(z: np.ndarray, iterations: np.ndarray, params: Dict, cmap: Colormap) -> np.ndarray:
    """内部距離着色
    Args:
        z (np.ndarray): 複素数配列
        iterations (np.ndarray): 反復回数配列
        params (Dict): 着色パラメータ
        cmap (Colormap): 色マップ
    Returns:
        np.ndarray: 着色されたRGBA配列
    """
    non_divergent = iterations <= 0
    abs_z = np.abs(z[non_divergent]) + 1e-10
    distance = np.log(abs_z) / np.log(2.0)
    normalized = (distance - np.min(distance)) / (np.max(distance) - np.min(distance))
    colored = np.zeros((*iterations.shape, 4), dtype=np.float32)
    colored[non_divergent] = cmap(normalized) * 255.0
    return colored