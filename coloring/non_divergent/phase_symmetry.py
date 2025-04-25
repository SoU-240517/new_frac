import numpy as np
from typing import Dict, Tuple
from matplotlib.colors import Colormap

def apply_phase_symmetry(z: np.ndarray, iterations: np.ndarray, params: Dict, cmap: Colormap) -> np.ndarray:
    """位相対称着色
    Args:
        z (np.ndarray): 複素数配列
        iterations (np.ndarray): 反復回数配列
        params (Dict): 着色パラメータ
        cmap (Colormap): 色マップ
    Returns:
        np.ndarray: 着色されたRGBA配列
    """
    non_divergent = iterations <= 0
    angles = np.angle(z[non_divergent])
    symmetry_order = 5
    normalized = (angles * symmetry_order / (2*np.pi)) % 1.0
    gamma = 1.5
    normalized = normalized ** (1/gamma)
    colored = np.zeros((*iterations.shape, 4), dtype=np.float32)
    colored[non_divergent] = cmap(normalized) * 255.0
    return colored
