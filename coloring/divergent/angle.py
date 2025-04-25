import numpy as np
from typing import Dict, Tuple
from matplotlib.colors import Colormap
from ui.zoom_function.debug_logger import DebugLogger

def angle(
    colored: np.ndarray,
    divergent_mask: np.ndarray,
    z_vals: np.ndarray,
    cmap: Colormap,
    params: Dict,
    logger: DebugLogger
) -> None:
    """角度カラーリング
    Args:
        colored (np.ndarray): 出力用のRGBA配列 (形状: (h, w, 4), dtype=float32)
        divergent_mask (np.ndarray): 発散した点のマスク (形状: (h, w), dtype=bool)
        z_vals (np.ndarray): 複素数配列
        cmap (Colormap): 色マップ
        params (Dict): 着色パラメータ
        logger (DebugLogger): ロガーインスタンス
    """
    divergent = divergent_mask
    angles = np.angle(z_vals) / (2 * np.pi) + 0.5
    colored[divergent] = cmap(angles[divergent]) * 255.0