import numpy as np
from typing import Dict
from matplotlib.colors import Colormap
from ui.zoom_function.debug_logger import DebugLogger
from ui.zoom_function.enums import LogLevel
# utils からインポート
from ..utils import _normalize_and_color

def apply_convergence_speed(
    colored: np.ndarray, # 引数に追加
    non_divergent_mask: np.ndarray, # 引数に追加
    z_vals: np.ndarray, # iterations の代わりに z_vals を受け取る
    non_cmap_func: Colormap, # 正しいカラーマップ関数を受け取る
    params: Dict,
    logger: DebugLogger # logger を受け取る
) -> None: # 戻り値をなくす

    """収束速度着色
    Args:
        z (np.ndarray): 複素数配列
        iterations (np.ndarray): 反復回数配列
        params (Dict): 着色パラメータ
        cmap (Colormap): 色マップ
    Returns:
        np.ndarray: 着色されたRGBA配列
    """
    """収束速度着色"""
    non_divergent = non_divergent_mask # 引数のマスクを使用
    if not np.any(non_divergent):
        logger.log(LogLevel.DEBUG, "No non-divergent points for convergence speed.")
        return

    z_nd = z_vals[non_divergent] # マスクされた z_vals を取得
    if z_nd.size == 0:
        logger.log(LogLevel.WARNING,"Filtered non-divergent z_vals resulted in empty array.")
        return

    # np.errstate でゼロ除算警告を抑制
    with np.errstate(divide='ignore', invalid='ignore'):
        speed = 1.0 / (np.abs(z_nd) + 1e-10) # + 1e-10 でゼロ除算回避

    # speedがinfやnanになる可能性に対処
    finite_mask = np.isfinite(speed)
    if not np.any(finite_mask):
        logger.log(LogLevel.WARNING, "No finite speed values calculated.")
        return
    valid_speed = speed[finite_mask]
    if valid_speed.size == 0:
        logger.log(LogLevel.WARNING, "Filtered speed values resulted in empty array.")
        return

    # 最小値・最大値の計算は有限な値のみで行う
    min_speed = np.min(valid_speed)
    max_speed = np.max(valid_speed)

    # ゼロ除算チェック
    if np.isclose(max_speed, min_speed):
        normalized = np.full_like(valid_speed, 0.5) # 全て同じ値なら中央値(0.5)で塗る
        logger.log(LogLevel.DEBUG, "Speed values are uniform.")
    else:
        normalized = (valid_speed - min_speed) / (max_speed - min_speed)

    gamma = params.get('non_diverge_gamma', 1.5) # paramsからガンマ値を取得できるようにする
    normalized = normalized ** (1.0/gamma)

    # 着色処理
    colored_part = _normalize_and_color(normalized, non_cmap_func, vmin=0.0, vmax=1.0) # normalized は 0-1 のはず

    # 元の配列の対応する位置に書き込むためのインデックス処理
    original_indices = np.where(non_divergent)
    valid_indices = (original_indices[0][finite_mask], original_indices[1][finite_mask])

    # 書き込み
    colored[valid_indices] = colored_part
    logger.log(LogLevel.DEBUG, f"Applied convergence speed coloring to {valid_speed.size} points.")
