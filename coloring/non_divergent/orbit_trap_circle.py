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
    """非発散部：軌道トラップ(円)で着色する
        軌道トラップは、複素数の軌道が特定の形状（この場合は円）に近づいた距離を計算し、
        その距離に基づいて着色を行う手法です。
    Args:
        colored (np.ndarray): 出力用のRGBA配列 (形状: (h, w, 4), dtype=float32)
        non_divergent_mask (np.ndarray): 非発散した点のマスク (形状: (h, w), dtype=bool)
        z_vals (np.ndarray): 複素数配列
        non_cmap_func (Colormap): 非発散部分用のカラーマップ関数
        params (Dict): 着色パラメータ
        logger (DebugLogger): ロガーインスタンス
    Notes:
        軌道トラップの基本的な動作:
        1. 複素数の絶対値を計算
        2. その値からトラップ円の半径を引く
        3. 絶対値を取ることで正の値のみを扱う
        4. 正規化して0-1の範囲に収める
        5. ガンマ補正を適用して明るさを調整
        6. カラーマップに適用して着色
    """
    R = 1.4 # タラップ円の半径（通常0.5～2.0の範囲で調整）

    # 複素数の絶対値からトラップ円との距離を計算
    # 絶対値を取ることで正の値のみを扱う
    trap_dist = np.abs(np.abs(z_vals[non_divergent_mask]) - R)

    # 距離を正規化（0-1の範囲に収める）
    # 1から引くことで、円に近い点ほど大きな値になるようにする
    normalized = 1 - (trap_dist / np.max(trap_dist))

    # ガンマ補正を適用（明るさの調整）
    # gammaの値を大きくするとコントラストが高くなる
    gamma = 1.0 # 1.0～2.0で調整
    normalized = normalized ** (1/gamma)

    # 正規化された値をカラーマップに適用し、非発散部分を着色
    colored[non_divergent_mask] = non_cmap_func(normalized) * 255.0
