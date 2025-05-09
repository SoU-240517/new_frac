FILE_NAME = "palam_c_z.py"

# 表示名 (UIのコンボボックスで使われる)
DISPLAY_NAME = "パラメータ(C/Z)"

# このプラグインのメインの着色関数の名前
COLORING_FUNCTION_NAME = "apply_parameter_coloring"

import numpy as np
from matplotlib.colors import Colormap
from typing import Dict
from debug import DebugLogger, LogLevel

def apply_parameter_coloring(
    colored: np.ndarray,
    non_divergent_mask: np.ndarray,
    z_vals: np.ndarray, # iterations の代わりに z_vals を受け取る
    non_cmap_func: Colormap, # 正しいカラーマップ関数を受け取る
    params: Dict,
    logger: DebugLogger
) -> None:
    """非発散部の着色処理
        非発散した点（フラクタルの内部）を、指定されたアルゴリズムに基づいて着色する。
        着色アルゴリズムは、パラメータCの角度または最終的な複素数Zの値の角度を使用する。
    Args:
        colored (np.ndarray): 出力用のRGBA配列 (形状: (h, w, 4), dtype=float32)
        non_divergent_mask (np.ndarray): 非発散領域を示すマスク配列 (形状: (h, w), dtype=bool)
        z_vals (np.ndarray): 各点における複素数Zの最終値の配列 (形状: (h, w), dtype=complex128)
        non_cmap_func (Colormap): 非発散領域の着色に使用するカラーマップ関数
        params (Dict): 着色に関するパラメータを含む辞書
        logger (DebugLogger): デバッグログ出力用ロガーインスタンス
    """
    algo_name = params.get("diverge_algorithm")
    if algo_name == "パラメータ(C)":
        # パラメータCによる着色処理
        # Julia集合の場合、複素数Cの角度（偏角）を使って着色
        if params["fractal_type"] == "Julia":
            c_val = complex(params["c_real"], params["c_imag"])
            # 複素数Cの偏角を計算し、0-1の範囲に正規化
            angle = (np.angle(c_val) / (2 * np.pi)) + 0.5
            # カラーマップを使って色を取得
            color = non_cmap_func(angle)  # 色を取得
            # 非発散部分を同じ色で塗りつぶす
            colored[non_divergent_mask] = np.tile(color, (np.sum(non_divergent_mask), 1)) * 255.0
        else:
            # Mandelbrot集合の場合、Cは初期値（通常0）なので意味がない
            # 代わりに黒で塗るか、別のデフォルト色を使う
            colored[non_divergent_mask] = [0.0, 0.0, 0.0, 255.0]
            #colored[non_divergent_mask] = [0.0, 0.0, 255.0, 255.0] # 青色で塗りつぶす例
    else:  # パラメータ(Z)の場合
        # zの値による着色処理
        # 非発散した点の最終的な複素数Zの値を使って着色
        # JuliaとMandelbrotの両方で有効
        z_real, z_imag = np.real(z_vals[non_divergent_mask]), np.imag(z_vals[non_divergent_mask])
        # Zの実部と虚部から偏角を計算し、0-1の範囲に正規化
        angle = (np.arctan2(z_imag, z_real) / (2 * np.pi)) + 0.5
        # カラーマップを使って色を取得し、非発散部分を塗りつぶす
        colored[non_divergent_mask] = non_cmap_func(angle) * 255.0
