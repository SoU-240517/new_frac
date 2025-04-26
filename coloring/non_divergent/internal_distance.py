import numpy as np
from typing import Dict, Tuple
from matplotlib.colors import Colormap
from ui.zoom_function.debug_logger import DebugLogger
from ui.zoom_function.enums import LogLevel

def apply_internal_distance(
    colored: np.ndarray,
    non_divergent_mask: np.ndarray,
    z_vals: np.ndarray,
    non_cmap_func: Colormap,
    params: Dict,
    logger: DebugLogger
) -> None:
    """非発散部：内部距離で着色する
    Args:
        colored (np.ndarray): 出力用のRGBA配列 (形状: (h, w, 4), dtype=float32)
        non_divergent_mask (np.ndarray): 非発散した点のマスク (形状: (h, w), dtype=bool)
        z_vals (np.ndarray): 複素数配列
        non_cmap_func (Colormap): 非発散部分用のカラーマップ関数
        params (Dict): 着色パラメータ
        logger (DebugLogger): ロガーインスタンス
    """
    with np.errstate(invalid='ignore', divide='ignore'):
        # z_valsの絶対値を計算 (0にならないように微小値を加算)
        abs_z = np.abs(z_vals[non_divergent_mask]) + 1e-10
        # 対数を取って正規化 (値が大きいほど境界に近い)
        distance = np.log(abs_z) / np.log(2.0)
        # 0-1の範囲に正規化
        distance = (distance - np.min(distance)) / (np.max(distance) - np.min(distance))
    # カラーマップを適用
    colored[non_divergent_mask] = non_cmap_func(distance) * 255.0
