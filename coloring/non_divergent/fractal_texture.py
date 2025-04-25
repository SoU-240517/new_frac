import numpy as np
from typing import Dict, Tuple
from matplotlib.colors import Colormap

def fractal_texture(z: np.ndarray, iterations: np.ndarray, params: Dict, cmap: Colormap) -> np.ndarray:
    """フラクタルテクスチャ着色
    Args:
        z (np.ndarray): 複素数配列
        iterations (np.ndarray): 反復回数配列
        params (Dict): 着色パラメータ
        cmap (Colormap): 色マップ
    Returns:
        np.ndarray: 着色されたRGBA配列
    """
    non_divergent = iterations <= 0
    # フラクタルテクスチャの計算
    with np.errstate(divide='ignore', invalid='ignore'):
        # 複素数の絶対値の対数を計算
        abs_log = np.log(np.abs(z[non_divergent]) + 1e-10)
        # 角度の計算
        angles = np.angle(z[non_divergent])
        # テクスチャの計算（複数の周波数成分を組み合わせる）
        texture = (
            np.sin(abs_log * 2) +
            0.5 * np.sin(abs_log * 4) +
            0.25 * np.sin(abs_log * 8)
        )
        # 正規化
        normalized = (texture - np.min(texture)) / (np.max(texture) - np.min(texture))
        # ガンマ補正
        gamma = 1.4
        normalized = normalized ** (1/gamma)
    
    colored = np.zeros((*iterations.shape, 4), dtype=np.float32)
    colored[non_divergent] = cmap(normalized) * 255.0
    return colored