import numpy as np
from typing import Dict
from matplotlib.colors import Colormap, Normalize
from ui.zoom_function.debug_logger import DebugLogger
from ui.zoom_function.enums import LogLevel # LogLevelもインポート
# utils からインポートする方が良い
from ..utils import _normalize_and_color

def apply_logarithmic_mapping(
    colored: np.ndarray,
    divergent_mask: np.ndarray,
    iterations: np.ndarray,
    cmap_func: Colormap, # manager.py から渡される変数名に合わせる
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
    divergent = divergent_mask # 引数のマスクを使用
    if not np.any(divergent): # 発散点がなければ何もしない
        logger.log(LogLevel.DEBUG, "No divergent points for logarithmic mapping.")
        return

    divergent_iters = iterations[divergent]
    if divergent_iters.size == 0:
        logger.log(LogLevel.DEBUG, "Filtered divergent points resulted in empty array.")
        return

    max_iter = params.get("max_iterations", 100)
    if max_iter <= 1: max_iter = 2 # log(1) 回避

    with np.errstate(divide='ignore', invalid='ignore'): # log(0) 対策
        log_iters = np.log(divergent_iters)
        vmin_log = np.log(1.0) # 1回の反復から
        vmax_log = np.log(float(max_iter))

    # log_iters に含まれる -inf や nan を除外して正規化・着色
    finite_mask = np.isfinite(log_iters)
    if not np.any(finite_mask):
        logger.log(LogLevel.WARNING,"No finite log values for logarithmic mapping.")
        return

    valid_log_iters = log_iters[finite_mask]
    if valid_log_iters.size == 0:
        logger.log(LogLevel.WARNING,"Filtered log iters resulted in empty array.")
        return

    # 実際の有限な値の範囲を使うか、理論的な範囲を使うか選択（ここでは理論値）
    # norm = Normalize(np.min(valid_log_iters), np.max(valid_log_iters))
    norm = Normalize(vmin=vmin_log, vmax=vmax_log)

    # マスクを使って元の配列の対応する位置に書き込む
    # colored[divergent][finite_mask] のような多重マスクは直接使えない場合がある
    # 一度、発散点全体のインデックスを取得する方が確実
    indices = np.where(divergent)
    original_indices_divergent = (indices[0], indices[1])

    # さらに finite_mask で絞り込んだインデックス
    finite_indices = (original_indices_divergent[0][finite_mask], original_indices_divergent[1][finite_mask])

    # 着色処理
    colored_part = _normalize_and_color(valid_log_iters, cmap_func, vmin=vmin_log, vmax=vmax_log)
    #colored_part = cmap_func(norm(valid_log_iters)) * 255.0 # _normalize_and_colorを使わない場合

    # 元の colored 配列の該当箇所に代入
    colored[finite_indices] = colored_part

    logger.log(LogLevel.DEBUG, f"Applied logarithmic mapping to {valid_log_iters.size} points.")
