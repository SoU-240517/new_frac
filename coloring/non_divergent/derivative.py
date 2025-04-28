import numpy as np
from typing import Dict, Tuple
from matplotlib.colors import Colormap
from ui.zoom_function.debug_logger import DebugLogger
from ui.zoom_function.enums import LogLevel

def apply_derivative_coloring(
    colored: np.ndarray,
    non_divergent_mask: np.ndarray,
    z_vals: np.ndarray, # iterations の代わりに z_vals を受け取る
    non_cmap_func: Colormap, # 正しいカラーマップ関数を受け取る
    params: Dict,
    logger: DebugLogger
) -> None:
    """非発散領域を微分係数で着色する
    - マンデルブロ集合の非発散部分を、微分係数（f'(z)）に基づいて着色する
    - f(z) = z² + c の場合、f'(z) = 2z となる
    Args:
        colored (np.ndarray): 出力用のRGBA配列 (形状: (h, w, 4), dtype=float32)
        non_divergent_mask (np.ndarray): 非発散点のマスク配列 (形状: (h, w), dtype=bool)
        z_vals (np.ndarray): 複素数値の配列
        non_cmap_func (Colormap): 非発散領域の着色に使用するカラーマップ関数
        params (Dict): 使用しない
        logger (DebugLogger): デバッグ用ロガーインスタンス
    """
    # マンデルブロ集合の基本関数 f(z) = z² + c の微分係数 f'(z) = 2z を計算
    # 0.5 は調整可能な係数（明るさ調整用）
    derivative = 2 * np.abs(z_vals[non_divergent_mask]) * 0.5

    # 微分係数の対数を計算して、大きな範囲を適切に可視化
    # ゼロ除算を防ぐために微小値を加える
    log_deriv = np.log(derivative + 1e-10)

    # 0-1の範囲に正規化
    normalized = (log_deriv - np.min(log_deriv)) / (np.max(log_deriv) - np.min(log_deriv))

    # ガンマ補正を適用して色の遷移を調整
    gamma = 1.5  # 1.0～2.0の範囲で調整
    normalized = normalized ** (1/gamma)

    # 正規化された値をカラーマップに適用し、0-255の範囲に変換
    colored[non_divergent_mask] = non_cmap_func(normalized) * 255.0
