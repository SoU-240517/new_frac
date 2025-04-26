import numpy as np
from typing import Dict
from matplotlib.colors import Colormap
from ui.zoom_function.debug_logger import DebugLogger
from ui.zoom_function.enums import LogLevel
from ..gradient import compute_gradient

def apply_gradient_based(
    colored: np.ndarray,
    non_divergent_mask: np.ndarray,
    iterations: np.ndarray,
    gradient_values: np.ndarray,
    non_cmap_func: Colormap,
    params: Dict,
    logger: DebugLogger
) -> None:
    """非発散部：グラデーションで着色する
    Args:
        colored (np.ndarray): 出力用のRGBA配列 (形状: (h, w, 4), dtype=float32)
        non_divergent_mask (np.ndarray): 非発散した点のマスク (形状: (h, w), dtype=bool)
        iterations (np.ndarray): 反復回数配列
        gradient_values (np.ndarray): グラデーション値配列
        non_cmap_func (Colormap): 非発散部分用のカラーマップ関数
        params (Dict): 着色パラメータ
            - gradient_type: 'linear' | 'radial'
            - gradient_size: グラデーションのサイズ
            - gradient_position: (x, y) の座標
        logger (DebugLogger): ロガーインスタンス
    """
    # グラデーションの計算にパラメータを使用
    grad = compute_gradient(iterations.shape, logger=logger)

    # 非発散部分にグラデーションを適用
    colored[non_divergent_mask] = non_cmap_func(grad[non_divergent_mask]) * 255.0
