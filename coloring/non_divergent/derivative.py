import numpy as np
from typing import Dict, Tuple
from matplotlib.colors import Colormap

def apply_derivative_coloring(z: np.ndarray, iterations: np.ndarray, params: Dict, cmap: Colormap) -> np.ndarray:
    """微分係数着色
    Args:
        z (np.ndarray): 複素数配列
        iterations (np.ndarray): 反復回数配列
        params (Dict): 着色パラメータ
        cmap (Colormap): 色マップ
    Returns:
        np.ndarray: 着色されたRGBA配列
    """
    non_divergent = iterations <= 0
    derivative = 2 * np.abs(z[non_divergent]) * 0.5
    log_deriv = np.log(derivative + 1e-10)
    normalized = (log_deriv - np.min(log_deriv)) / (np.max(log_deriv) - np.min(log_deriv))
    gamma = 1.5
    normalized = normalized ** (1/gamma)
    colored = np.zeros((*iterations.shape, 4), dtype=np.float32)
    colored[non_divergent] = cmap(normalized) * 255.0
    return colored
