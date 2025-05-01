import numpy as np
from typing import Dict
from matplotlib.colors import Colormap
from debug.debug_logger import DebugLogger
from debug.enum_debug import LogLevel
from coloring.gradient import compute_gradient

def apply_gradient_based(
    colored: np.ndarray,
    non_divergent_mask: np.ndarray,
    iterations: np.ndarray,
    gradient_values: np.ndarray,
    non_cmap_func: Colormap,
    params: Dict,
    logger: DebugLogger
) -> None:
    """非発散領域にグラデーションを適用して着色する
    - 指定されたパラメータに基づいてグラデーションを計算し、非発散領域に着色する
    Args:
        colored (np.ndarray): 出力用のRGBA配列 (形状: (h, w, 4), dtype=float32)
        non_divergent_mask (np.ndarray): 非発散点のマスク配列 (形状: (h, w), dtype=bool)
        iterations (np.ndarray): 反復回数配列
        gradient_values (np.ndarray): グラデーション値配列
        non_cmap_func (Colormap): 非発散領域の着色に使用するカラーマップ関数
        params (Dict): グラデーションのパラメータ
            - gradient_type (str): グラデーションの種類 ('linear' または 'radial')
            - gradient_size (int): グラデーションのサイズ
            - gradient_position (Tuple[int, int]): グラデーションの中心座標 (x, y)
        logger (DebugLogger): デバッグ用ロガーインスタンス
    """
    #  グラデーションを計算
    grad = compute_gradient(iterations.shape, logger=logger)

    # 非発散領域にグラデーションを適用
    colored[non_divergent_mask] = non_cmap_func(grad[non_divergent_mask]) * 255.0
