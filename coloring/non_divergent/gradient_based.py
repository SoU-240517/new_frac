import numpy as np
from typing import Dict, Tuple
from ..gradient import compute_gradient
from matplotlib.colors import Colormap

def gradient_based(z: np.ndarray, iterations: np.ndarray, params: Dict, cmap: Colormap) -> np.ndarray:
    """グラデーション着色
    Args:
        z (np.ndarray): 複素数配列
        iterations (np.ndarray): 反復回数配列
        params (Dict): 着色パラメータ
        cmap (Colormap): 色マップ
    Returns:
        np.ndarray: 着色されたRGBA配列
    """
    non_divergent = iterations <= 0
    grad = compute_gradient(iterations.shape)
    colored = np.zeros((*iterations.shape, 4), dtype=np.float32)
    colored[non_divergent] = cmap(grad[non_divergent]) * 255.0
    return colored