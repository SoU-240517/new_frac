import numpy as np
from typing import Dict
from matplotlib.colors import Colormap
from debug.debug_logger import DebugLogger
from debug.enum_debug import LogLevel
from coloring.utils import _normalize_and_color

def apply_potential(
    colored: np.ndarray,
    divergent_mask: np.ndarray,
    z_vals: np.ndarray,
    cmap_func: Colormap,
    params: Dict,
    logger: DebugLogger
) -> None:
    """発散領域に対して、ポテンシャル関数法に基づくカラーリングを適用する
    - ポテンシャル関数を用いて発散の度合いを計算し、カラーマップで着色する
    Args:
        colored (np.ndarray): 出力先のRGBA配列 (形状: (h, w, 4), dtype=float32)
        divergent_mask (np.ndarray): 発散した点のマスク配列 (形状: (h, w), dtype=bool)
        z_vals (np.ndarray): 各点での複素数の値を持つ配列 (形状: (h, w), dtype=complex)
        cmap_func (Colormap): 発散領域の着色に使うカラーマップ関数
        params (Dict): 使用しない
        logger (DebugLogger): デバッグ用ロガー
    """
    # 発散していない部分のマスクを作成
    mask = ~divergent_mask

    # 発散した点の複素数値を抽出
    z = z_vals[divergent_mask]

    # ポテンシャルの計算
    # ポテンシャル = log(|z|) - log(2) で、
    # log(2)の補正項は通常のポテンシャル値を0に正規化するため
    potential = np.log(np.abs(z)) - np.log(2.0)

    # 正規化と着色
    # ポテンシャル値を0-1の範囲に正規化
    normalized = (potential - np.min(potential)) / (np.max(potential) - np.min(potential))

    # 正規化された値をカラーマップに変換し、発散した部分に適用
    colored[divergent_mask] = cmap_func(normalized) * 255.0

    # 発散していない部分は黒（0）に設定
    colored[mask] = 0
