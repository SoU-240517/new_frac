import numpy as np
from typing import Dict, Tuple
from matplotlib.colors import Colormap
from ui.zoom_function.debug_logger import DebugLogger
from ui.zoom_function.enums import LogLevel

def apply_orbit_trap_circle(
    colored: np.ndarray,
    non_divergent_mask: np.ndarray,
    z_vals: np.ndarray,
    non_cmap_func: Colormap,
    params: Dict,
    logger: DebugLogger
) -> None:
    """非発散領域を軌道トラップ(円)で着色する
    - 複素数の軌道が特定の形状（この場合は円）に近づいた距離を計算し、その距離に基づいて着色を行う
    Args:
        colored (np.ndarray): 出力用のRGBA配列 (形状: (h, w, 4), dtype=float32)
        non_divergent_mask (np.ndarray): 非発散点のマスク配列 (形状: (h, w), dtype=bool)
        z_vals (np.ndarray): 複素数値の配列
        non_cmap_func (Colormap): 非発散領域の着色に使用するカラーマップ関数
        params (Dict): 使用しない
        logger (DebugLogger): デバッグ用ロガーインスタンス
    """
    R = 1.4  # トラップ円の半径（通常0.5～2.0の範囲で調整）

    # 複素数の絶対値からトラップ円との距離を計算
    trap_dist = np.abs(np.abs(z_vals[non_divergent_mask]) - R)

    # 距離を0-1の範囲に正規化
    normalized = 1 - (trap_dist / np.max(trap_dist))

    # ガンマ補正を適用して明るさを調整
    gamma = 1.0  # 1.0～2.0で調整
    normalized = normalized ** (1/gamma)

    # 正規化された値をカラーマップに適用
    colored[non_divergent_mask] = non_cmap_func(normalized) * 255.0
