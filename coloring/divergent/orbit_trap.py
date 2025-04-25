import numpy as np
from typing import Dict, Tuple
from matplotlib.colors import Colormap

def _normalize_and_color(dist: np.ndarray, cmap: Colormap, min_dist: float, max_dist: float) -> np.ndarray:
    """Normalize distance and color"""
    normalized = (dist - min_dist) / (max_dist - min_dist)
    return cmap(normalized)

def apply_orbit_trap(z: np.ndarray, iterations: np.ndarray, params: Dict, cmap: Colormap) -> np.ndarray:
    """軌道トラップ法
    Args:
        z (np.ndarray): 複素数配列
        iterations (np.ndarray): 反復回数配列
        params (Dict): 着色パラメータ
            - trap_type: 'circle' | 'square' | 'cross' | 'triangle'
            - trap_size: トラップのサイズ
            - trap_position: (x, y) の座標
        cmap (Colormap): 色マップ
    Returns:
        np.ndarray: 着色されたRGBA配列
    """
    # デフォルトパラメータ
    trap_type = params.get('trap_type', 'circle')
    trap_size = params.get('trap_size', 0.5)
    trap_position = params.get('trap_position', (0.0, 0.0))

    # 発散した点のマスク（反復回数が最大反復回数未満の点）
    max_iterations = np.max(iterations)
    divergent = iterations < max_iterations

    # トラップ位置の複素数
    trap_target = complex(trap_position[0], trap_position[1])

    # 距離の計算
    if trap_type == 'circle':
        # 円形トラップ
        trap_dist = np.abs(z - trap_target) / trap_size
    elif trap_type == 'square':
        # 正方形トラップ
        real_dist = np.abs(np.real(z) - trap_position[0]) / trap_size
        imag_dist = np.abs(np.imag(z) - trap_position[1]) / trap_size
        trap_dist = np.maximum(real_dist, imag_dist)
    elif trap_type == 'cross':
        # 十字トラップ
        real_dist = np.abs(np.real(z) - trap_position[0]) / trap_size
        imag_dist = np.abs(np.imag(z) - trap_position[1]) / trap_size
        trap_dist = np.minimum(real_dist, imag_dist)
    elif trap_type == 'triangle':
        # 三角形トラップ
        angle = np.angle(z - trap_target)
        trap_dist = (np.abs(z - trap_target) / trap_size) * np.cos(angle)
    else:
        # デフォルトは円形
        trap_dist = np.abs(z - trap_target) / trap_size

    # マスク処理
    trap_dist[~divergent] = float('inf')

    # 距離の正規化
    divergent_points = divergent & np.isfinite(trap_dist)
    if np.any(divergent_points):
        min_dist = np.min(trap_dist[divergent_points])
        max_dist = np.max(trap_dist[divergent_points])
    else:
        min_dist = 0
        max_dist = 1

    # 着色
    colored = np.zeros((*iterations.shape, 4), dtype=np.float32)
    if np.any(divergent_points):
        colored[divergent_points] = _normalize_and_color(
            trap_dist[divergent_points],
            cmap,
            min_dist,
            max_dist
        )

    return colored
