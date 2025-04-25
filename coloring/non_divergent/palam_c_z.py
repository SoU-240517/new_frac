import numpy as np
from typing import Dict, Tuple
from matplotlib.colors import Colormap

def palam_c_z(z: np.ndarray, iterations: np.ndarray, params: Dict, cmap: Colormap) -> np.ndarray:
    """パラメータ(C)とパラメータ(Z)着色
    Args:
        z (np.ndarray): 複素数配列
        iterations (np.ndarray): 反復回数配列
        params (Dict): 着色パラメータ
        cmap (Colormap): 色マップ
    Returns:
        np.ndarray: 着色されたRGBA配列
    """
    non_divergent = iterations <= 0
    # パラメータCとZの関係を可視化
    with np.errstate(divide='ignore', invalid='ignore'):
        # CとZの相対的な位置関係を計算
        rel_pos = np.abs(z[non_divergent] - params.get('c', 0))
        # 対数スケールで正規化
        log_rel = np.log(rel_pos + 1e-10)
        # 正規化
        normalized = (log_rel - np.min(log_rel)) / (np.max(log_rel) - np.min(log_rel))
        # ガンマ補正
        gamma = 1.3
        normalized = normalized ** (1/gamma)
    
    colored = np.zeros((*iterations.shape, 4), dtype=np.float32)
    colored[non_divergent] = cmap(normalized) * 255.0
    return colored