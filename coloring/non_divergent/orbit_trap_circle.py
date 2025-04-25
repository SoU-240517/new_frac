import numpy as np
from typing import Dict, Tuple
from matplotlib.colors import Colormap

def apply_orbit_trap_circle(z: np.ndarray, iterations: np.ndarray, params: Dict, cmap: Colormap) -> np.ndarray:
    """軌道トラップ(円)着色
    Args:
        z (np.ndarray): 複素数配列
        iterations (np.ndarray): 反復回数配列
        params (Dict): 着色パラメータ
        cmap (Colormap): 色マップ
    Returns:
        np.ndarray: 着色されたRGBA配列
    """
    non_divergent = iterations <= 0
    R = 1.4
    trap_dist = np.abs(np.abs(z[non_divergent]) - R)
    normalized = 1 - (trap_dist / np.max(trap_dist))
    gamma = 1.0
    normalized = normalized ** (1/gamma)
    colored = np.zeros((*iterations.shape, 4), dtype=np.float32)
    colored[non_divergent] = cmap(normalized) * 255.0
    return colored
