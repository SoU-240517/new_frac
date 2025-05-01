import numpy as np
from typing import Dict
from matplotlib.colors import Colormap, Normalize
from debug.debug_logger import DebugLogger
from debug.enum_debug import LogLevel
from coloring.utils import _normalize_and_color

def apply_logarithmic_mapping(
    colored: np.ndarray,
    divergent_mask: np.ndarray,
    iterations: np.ndarray,
    cmap_func: Colormap,
    params: Dict,
    logger: DebugLogger
) -> None:
    """発散領域に対して、反復回数の対数に基づくカラーリングを適用する
    - 発散領域の各点に対して、その反復回数の対数をとり、カラーマップを用いて色を決定する
    Args:
        colored (np.ndarray): 出力先のRGBA配列 (形状: (h, w, 4), dtype=float32)
        divergent_mask (np.ndarray): 発散した点のマスク配列 (形状: (h, w), dtype=bool)
        iterations (np.ndarray): 各点での反復回数を持つ配列 (形状: (h, w), dtype=int)
        cmap_func (Colormap): 発散領域の着色に使うカラーマップ関数
        params (Dict): 計算パラメータを含む辞書。'max_iterations'キーが必要
        logger (DebugLogger): デバッグ用ロガー
    """
    # 発散した点が存在しない場合は処理を終了
    if not np.any(divergent_mask):
        return

    # 発散した点の反復回数を取得
    divergent_iters = iterations[divergent_mask]

    max_iter = params.get("max_iterations")
    if max_iter <= 1:
        max_iter = 2  # log(1) 回避
        logger.log(LogLevel.WARNING, "max_iterations は <=1 でしたが、2 に調整されました。")

    with np.errstate(divide='ignore', invalid='ignore'):  # log(0) 対策
        log_iters = np.log(divergent_iters)
        vmin_log = np.log(1.0)  # 1回の反復から
        vmax_log = np.log(float(max_iter))

    # log_iters に含まれる -inf や nan を除外
    finite_mask = np.isfinite(log_iters)

    # 有限な値が1つもない場合は処理を終了
    if not np.any(finite_mask):
        logger.log(LogLevel.WARNING, "対数写像では有限値は見つからない。")
        return

    valid_log_iters = log_iters[finite_mask]

    # 元の配列のインデックスを取得
    divergent_indices = np.where(divergent_mask)

    # 有限な値に対応するインデックス
    finite_indices = (
        divergent_indices[0][finite_mask],
        divergent_indices[1][finite_mask]
    )

    try:
        # 着色処理
        colored_part = _normalize_and_color(
            valid_log_iters,
            cmap_func,
            vmin=vmin_log,
            vmax=vmax_log
        )

        # 元の colored 配列の該当箇所に代入
        colored[finite_indices] = colored_part
    except Exception as e:
        logger.log(LogLevel.ERROR, f"Error in logarithmic mapping: {str(e)}")
        raise
