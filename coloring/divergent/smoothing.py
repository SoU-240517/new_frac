# coloring/divergent/smoothing.py

import numpy as np
from matplotlib.colors import Colormap
from typing import Dict

# utils.pyからスムージング関数をインポート
from ..utils import _smooth_iterations, _normalize_and_color, fast_smoothing, ColorAlgorithmError

# UI関連のインポート (ロガーなど)
from ui.zoom_function.debug_logger import DebugLogger
from ui.zoom_function.enums import LogLevel

"""発散部分の着色: 各種スムージング"""

def apply_smoothing(
    colored: np.ndarray,
    divergent_mask: np.ndarray,
    iterations: np.ndarray,
    z_vals: np.ndarray,
    cmap_func: Colormap,
    params: Dict,
    smoothing_method: str, # 'standard', 'fast', or 'exponential'
    logger: DebugLogger
    ) -> None:
    """発散部分をスムージングされた反復回数に基づいて着色する (インプレース処理)

    Args:
        colored (np.ndarray): 着色結果を格納するRGBA配列 (形状: (height, width, 4), dtype=float32)
                                この配列の該当箇所が直接変更されます。
        divergent_mask (np.ndarray): 発散した点のマスク (形状: (height, width), dtype=bool)
                                     True のピクセルが発散部分です。
        iterations (np.ndarray): 元の反復回数配列 (形状: (height, width), dtype=int)
        z_vals (np.ndarray): 計算終了時の複素数値配列 (形状: (height, width), dtype=complex)
        cmap_func (Colormap): 発散部分用のカラーマップ関数
        params (Dict): 計算パラメータ辞書 (現在は未使用だが将来的な拡張のため)
        smoothing_method (str): 使用するスムージングの種類 ('standard', 'fast', 'exponential')
        logger (DebugLogger): デバッグログを出力するためのロガーインスタンス。
    """
    logger.log(LogLevel.DEBUG, f"Applying {smoothing_method} smoothing for divergent points.")

    # 指定された方法でスムージング処理を実行
    try:
        # utils モジュールの _smooth_iterations を呼び出す
        smooth_iter = _smooth_iterations(z_vals, iterations, method=smoothing_method)
        logger.log(LogLevel.DEBUG, f"Calculated smoothed iterations using '{smoothing_method}'.")
    except ColorAlgorithmError as e:
        logger.log(LogLevel.ERROR, f"Error during smoothing calculation: {e}")
        # エラーが発生した場合、このアルゴリズムでの着色はスキップ
        # (または、エラーを示す色で塗るなどの代替処理も可能)
        return
    except Exception as e:
        logger.log(LogLevel.ERROR, f"Unexpected error during _smooth_iterations: {e}")
        return # 予期せぬエラーの場合もスキップ

    # スムージング結果から、発散していて、かつ有限な値を持つものを抽出
    # divergent_mask で発散点を絞り込み、np.isfinite で NaN や Inf を除外
    valid_mask = divergent_mask & np.isfinite(smooth_iter)
    valid_smooth_values = smooth_iter[valid_mask]

    # 有効なスムージング値が存在するかチェック
    if valid_smooth_values.size == 0:
        logger.log(LogLevel.WARNING, f"No finite smooth iteration values found for divergent points with method '{smoothing_method}'. Cannot apply coloring.")
        # 有効な値がない場合は着色できないため、ここで処理を終了
        return

    # 正規化のための最小値と最大値を計算
    # ここで計算することで、発散点全体での色の連続性を保つ
    vmin = np.min(valid_smooth_values)
    vmax = np.max(valid_smooth_values)

    logger.log(LogLevel.DEBUG, f"Smooth values range (min/max): {vmin:.4f} / {vmax:.4f}")

    # vminとvmaxが非常に近い、または同じ場合に対処 (utils._normalize_and_color内で処理されるが念のためログ)
    if np.isclose(vmin, vmax):
        logger.log(LogLevel.DEBUG, "vmin and vmax are close or equal. Normalization might produce uniform color.")
        # vmax = vmin + 1e-9 # 微小値を加える処理は _normalize_and_color に任せる

    # 発散点（かつスムージング値が有限）の部分だけを対象に正規化＆着色
    # _normalize_and_color は NaN を含む入力に対応していない可能性があるため、
    # valid_smooth_values (NaNを含まない) を渡す
    # ただし、元の colored 配列のどこに書き込むかを示すために valid_mask が必要

    # 一時的な配列に着色結果を格納
    colored_divergent_part = _normalize_and_color(
        valid_smooth_values, # NaNを含まない値で正規化・着色
        cmap_func,
        vmin=vmin,
        vmax=vmax
    )

    # 元の colored 配列の、valid_mask が True の位置に着色結果を代入
    colored[valid_mask] = colored_divergent_part

    logger.log(LogLevel.DEBUG, f"Applied smoothed coloring to {valid_smooth_values.size} points.")
