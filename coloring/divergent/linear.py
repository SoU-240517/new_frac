import numpy as np
from typing import Dict, Tuple
from matplotlib.colors import Normalize, Colormap
from ..utils import _normalize_and_color
from ui.zoom_function.debug_logger import DebugLogger

"""発散部分の着色: 反復回数線形マッピング"""

def linear_mapping(
    colored: np.ndarray,
    divergent_mask: np.ndarray,
    iterations: np.ndarray,
    cmap_func: Colormap,
    params: Dict,
    logger: DebugLogger
) -> None:
    """発散部分を反復回数の線形マッピングで着色する (インプレース処理)
    Args:
        colored (np.ndarray): 出力用のRGBA配列 (形状: (h, w, 4), dtype=float32)
        divergent_mask (np.ndarray): 発散した点のマスク (形状: (h, w), dtype=bool)
        iterations (np.ndarray): 反復回数配列 (形状: (h, w), dtype=int)
        cmap_func (Colormap): 発散部分用のカラーマップ関数
        params (Dict): 計算パラメータ辞書 ('max_iterations' を含む)
        logger (DebugLogger): ロガーインスタンス
    """
    # 発散した点の反復回数を取得
    divergent_iters = iterations[divergent_mask]

    # 発散した点が存在しない場合は処理を終了
    if divergent_iters.size == 0:
        return

    # 線形正規化 (1 から max_iterations の範囲)
    norm = Normalize(1, params["max_iterations"])
    colored_divergent_part = cmap_func(norm(divergent_iters)) * 255.0

    # 元の colored 配列の対応する位置に着色結果を代入
    colored[divergent_mask] = colored_divergent_part

def linear(z: np.ndarray, iterations: np.ndarray, params: Dict, cmap: Colormap, logger: DebugLogger) -> np.ndarray:
    """反復回数線形マッピング
    Args:
        z (np.ndarray): 複素数配列
        iterations (np.ndarray): 反復回数配列
        params (Dict): 着色パラメータ
        cmap (Colormap): 色マップ
        logger (DebugLogger): ロガーインスタンス
    Returns:
        np.ndarray: 着色されたRGBA配列
    """
    divergent = iterations > 0
    norm = Normalize(1, params["max_iterations"])
    colored = np.zeros((*iterations.shape, 4), dtype=np.float32)
    colored[divergent] = cmap(norm(iterations[divergent])) * 255.0
    return colored
