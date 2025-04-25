import numpy as np
from typing import Dict, Tuple
from matplotlib.colors import Colormap, Normalize
from ui.zoom_function.debug_logger import DebugLogger

def logarithmic(
    colored: np.ndarray,
    divergent_mask: np.ndarray,
    iterations: np.ndarray,
    cmap: Colormap,
    params: Dict,
    logger: DebugLogger
) -> None:
    """反復回数対数マッピング
    Args:
        colored (np.ndarray): 出力用のRGBA配列 (形状: (h, w, 4), dtype=float32)
        divergent_mask (np.ndarray): 発散した点のマスク (形状: (h, w), dtype=bool)
        iterations (np.ndarray): 反復回数配列 (形状: (h, w), dtype=int)
        cmap (Colormap): 色マップ
        params (Dict): 着色パラメータ
        logger (DebugLogger): ロガーインスタンス
    """
    divergent = iterations > 0
    # 対数スケールに変換
    log_iters = np.log(iterations[divergent])
    # 対数スケールの正規化
    norm = Normalize(np.log(1), np.log(params["max_iterations"]))
    colored[divergent] = cmap(norm(log_iters)) * 255.0