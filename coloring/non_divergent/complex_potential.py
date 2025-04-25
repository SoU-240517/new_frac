import numpy as np
from typing import Dict, Tuple
from matplotlib import cm
from matplotlib.colors import Colormap

def complex_potential(z: np.ndarray, iterations: np.ndarray, params: Dict, cmap: Colormap) -> np.ndarray:
    """複素ポテンシャル着色
    Args:
        z (np.ndarray): 複素数配列
        iterations (np.ndarray): 反復回数配列
        params (Dict): 着色パラメータ
        cmap (Colormap): 色マップ
    Returns:
        np.ndarray: 着色されたRGBA配列
    """
    non_divergent = iterations <= 0
    with np.errstate(divide='ignore', invalid='ignore'):
        potential = np.log(np.abs(z[non_divergent]) + 1e-10)
        potential = np.nan_to_num(potential, nan=0.0, posinf=0.0, neginf=0.0)
        normalized = (potential - np.min(potential)) / (np.max(potential) - np.min(potential))
        angle_effect = np.angle(z[non_divergent]) / (2*np.pi)
        combined = (normalized + 0.3 * angle_effect) % 1.0
    colored = np.zeros((*iterations.shape, 4), dtype=np.float32)
    colored[non_divergent] = cmap(combined) * 255.0
    return colored