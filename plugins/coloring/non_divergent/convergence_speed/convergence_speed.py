FILE_NAME = "convergence_speed.py"

# 表示名 (UIのコンボボックスで使われる)
DISPLAY_NAME = "反復収束速度"

# このプラグインのメインの着色関数の名前
COLORING_FUNCTION_NAME = "apply_convergence_speed"

import numpy as np
from matplotlib.colors import Colormap
from typing import Dict, Tuple
from debug import DebugLogger, LogLevel

def apply_convergence_speed(
    colored: np.ndarray,
    non_divergent_mask: np.ndarray,
    z_vals: np.ndarray, # iterations の代わりに z_vals を受け取る
    non_cmap_func: Colormap, # 正しいカラーマップ関数を受け取る
    params: Dict,
    logger: DebugLogger
) -> None:
    """非発散領域を収束速度で着色する
    - 各ピクセルが非発散領域に収束する速さを計算し、それに基づいて色を決定する
    Args:
        colored (np.ndarray): 出力用のRGBA配列 (形状: (h, w, 4), dtype=float32)
        non_divergent_mask (np.ndarray): 非発散点のマスク配列 (形状: (h, w), dtype=bool)
        z_vals (np.ndarray): 複素数値の配列
        non_cmap_func (Colormap): 非発散領域の着色に使用するカラーマップ関数
        params (Dict): 使用しない
        logger (DebugLogger): デバッグ用ロガーインスタンス
    """
    # 収束速度の計算：1/|z|で計算し、zが0に近いほど収束が速いとみなす
    # ゼロ除算を防ぐために微小値を加える
    speed = 1 / (np.abs(z_vals[non_divergent_mask]) + 1e-10)

    # 速度を0-1の範囲に正規化
    normalized = (speed - np.min(speed)) / (np.max(speed) - np.min(speed))

    # ガンマ補正を適用して色の遷移を調整
    gamma = 1.5  # 1.0～2.0の範囲で調整
    normalized = normalized ** (1/gamma)

    # 正規化された値をカラーマップに適用し、0-255の範囲に変換
    colored[non_divergent_mask] = non_cmap_func(normalized) * 255.0
