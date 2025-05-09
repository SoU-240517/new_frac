FILE_NAME = "linear.py"

# 表示名 (UIのコンボボックスで使われる)
DISPLAY_NAME = "反復回数線形マッピング"

# このプラグインのメインの着色関数の名前
COLORING_FUNCTION_NAME = "apply_linear_mapping"

import numpy as np
from matplotlib.colors import Normalize, Colormap
from typing import Dict
from debug import DebugLogger, LogLevel
from coloring.utils import _normalize_and_color

def apply_linear_mapping(
    colored: np.ndarray,
    divergent_mask: np.ndarray,
    iterations: np.ndarray,
    cmap_func: Colormap,
    params: Dict,
    logger: DebugLogger
) -> None:
    """発散領域に対して、反復回数に基づく線形マッピングでカラーリングを適用する
    - 発散領域の各点に対して、その反復回数を線形に正規化し、カラーマップを用いて色を決定する
    Args:
        colored (np.ndarray): 出力先のRGBA配列 (形状: (h, w, 4), dtype=float32)
        divergent_mask (np.ndarray): 発散した点のマスク配列 (形状: (h, w), dtype=bool)
        iterations (np.ndarray): 各点での反復回数を持つ配列 (形状: (h, w), dtype=int)
        cmap_func (Colormap): 発散領域の着色に使うカラーマップ関数
        params (Dict): 計算パラメータを含む辞書。'max_iterations'キーが必要
        logger (DebugLogger): デバッグ用ロガー
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
