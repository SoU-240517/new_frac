import numpy as np
from typing import Dict, Tuple
from matplotlib.colors import Colormap
from ui.zoom_function.debug_logger import DebugLogger
from ui.zoom_function.enums import LogLevel
from ..utils import _normalize_and_color

def apply_orbit_trap(
    colored: np.ndarray,
    divergent_mask: np.ndarray,
    iterations: np.ndarray,
    z_vals: np.ndarray,
    cmap_func: Colormap,
    params: Dict,
    logger: DebugLogger
) -> None:
    """発散領域に対して、軌道トラップ法に基づくカラーリングを適用する
    - 複素数列がある特定の領域（トラップ）にどれだけ近づくかに基づいて色を付ける
    Args:
        colored (np.ndarray): 出力先のRGBA配列 (形状: (h, w, 4), dtype=float32)
        divergent_mask (np.ndarray): 発散した点のマスク配列 (形状: (h, w), dtype=bool)
        iterations (np.ndarray): 各点での反復回数を持つ配列 (形状: (h, w), dtype=int)
        z_vals (np.ndarray): 各点での複素数の値を持つ配列 (形状: (h, w), dtype=complex)
        cmap_func (Colormap): 発散領域の着色に使うカラーマップ関数
        params (Dict): 軌道トラップのパラメータを含む辞書
            - trap_type (str, optional): トラップの形状。'circle', 'square', 'cross', 'triangle' のいずれか。デフォルトは 'circle'
            - trap_size (float, optional): トラップのサイズ。デフォルトは 0.5
            - trap_position (Tuple[float, float], optional): トラップの中心座標 (x, y)。デフォルトは (0.0, 0.0)
        logger (DebugLogger): デバッグ用ロガー
    """
    # デフォルトパラメータ
    trap_type = params.get('trap_type', 'circle')
    trap_size = params.get('trap_size', 0.5)
    trap_position = params.get('trap_position', (0.0, 0.0))

    # 発散した点のマスク。反復回数が最大反復回数未満の点を発散点として扱う
    max_iterations = np.max(iterations)
    divergent = iterations < max_iterations

    # トラップ位置の複素数化。トラップの中心位置を複素数として表現
    trap_target = complex(trap_position[0], trap_position[1])

    # 距離の計算。距離はトラップサイズで正規化される
    if trap_type == 'circle':
        # 円形トラップ
        trap_dist = np.abs(z_vals - trap_target) / trap_size
    elif trap_type == 'square':
        # 正方形トラップ
        real_dist = np.abs(np.real(z_vals) - trap_position[0]) / trap_size
        imag_dist = np.abs(np.imag(z_vals) - trap_position[1]) / trap_size
        trap_dist = np.maximum(real_dist, imag_dist)
    elif trap_type == 'cross':
        # 十字トラップ
        real_dist = np.abs(np.real(z_vals) - trap_position[0]) / trap_size
        imag_dist = np.abs(np.imag(z_vals) - trap_position[1]) / trap_size
        trap_dist = np.minimum(real_dist, imag_dist)
    elif trap_type == 'triangle':
        # 三角形トラップ
        angle = np.angle(z_vals - trap_target)
        trap_dist = (np.abs(z_vals - trap_target) / trap_size) * np.cos(angle)
    else:
        # デフォルトは円形
        trap_dist = np.abs(z_vals - trap_target) / trap_size

    # マスク処理
    trap_dist[~divergent] = float('inf')

    # 距離の正規化
    divergent_points = divergent & np.isfinite(trap_dist)
    if np.any(divergent_points):
        min_dist = np.min(trap_dist[divergent_points])
        max_dist = np.max(trap_dist[divergent_points])
        logger.log(LogLevel.INFO, f"Orbit trap distances: min={min_dist}, max={max_dist}")
    else:
        min_dist = 0
        max_dist = 1
        logger.log(LogLevel.WARNING, "No divergent points found for orbit trap coloring")

    # 着色
    if np.any(divergent_points):
        colors = _normalize_and_color(
            trap_dist[divergent_points],
            cmap_func,
            min_dist,
            max_dist
        )
        colored[divergent_points] = colors
    else:
        logger.log(LogLevel.WARNING, "No colors applied due to lack of divergent points")
