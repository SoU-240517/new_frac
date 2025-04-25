import numpy as np
from typing import Dict, Tuple
from matplotlib.colors import Colormap
from ui.zoom_function.debug_logger import DebugLogger
from ..utils import _normalize_and_color

def apply_potential(
    colored: np.ndarray,
    divergent_mask: np.ndarray,
    z_vals: np.ndarray,
    cmap: Colormap,
    params: Dict,
    logger: DebugLogger
) -> None:
    """ポテンシャル関数法
    Args:
        colored (np.ndarray): 出力用のRGBA配列 (形状: (h, w, 4), dtype=float32)
        divergent_mask (np.ndarray): 発散した点のマスク (形状: (h, w), dtype=bool)
        iterations (np.ndarray): 反復回数配列 (形状: (h, w), dtype=int)
        z_vals (np.ndarray): 複素数配列
        cmap (Colormap): 色マップ
        params (Dict): 着色パラメータ
        logger (DebugLogger): ロガーインスタンス
    """
    divergent = divergent_mask
    mask = ~divergent
    z = z_vals[divergent]

    # ポテンシャルの計算
    potential = np.log(np.abs(z)) - np.log(2.0)

    # 正規化と着色
    normalized = (potential - np.min(potential)) / (np.max(potential) - np.min(potential))
    colored[divergent] = cmap(normalized) * 255.0
    colored[mask] = 0
