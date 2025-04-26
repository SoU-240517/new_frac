import numpy as np
from typing import Dict, Tuple
from matplotlib.colors import Colormap
from ui.zoom_function.debug_logger import DebugLogger
from ui.zoom_function.enums import LogLevel

def apply_parameter_coloring(
    colored: np.ndarray,
    non_divergent_mask: np.ndarray,
    z_vals: np.ndarray, # iterations の代わりに z_vals を受け取る
    non_cmap_func: Colormap, # 正しいカラーマップ関数を受け取る
    params: Dict,
    logger: DebugLogger
) -> None:
    """非発散部：パラメータ(C)とパラメータ(Z)で着色する
        非発散した点（フラクタルの内部）を、以下のいずれかで着色します。
        - パラメータC（複素数Cの角度）
        - パラメータZ（最終的な複素数Zの角度）
    Args:
        colored (np.ndarray): 出力用のRGBA配列 (形状: (h, w, 4), dtype=float32)
        non_divergent_mask (np.ndarray): 非発散した点のマスク (形状: (h, w), dtype=bool)
        z_vals (np.ndarray): 複素数配列
        non_cmap_func (Colormap): 非発散部分用のカラーマップ関数
        params (Dict): 着色パラメータ
        logger (DebugLogger): ロガーインスタンス
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
    else:  # パラメータ(Z)の場合
        # zの値による着色処理
        # 非発散した点の最終的な複素数Zの値を使って着色
        # JuliaとMandelbrotの両方で有効
        z_real, z_imag = np.real(z_vals[non_divergent_mask]), np.imag(z_vals[non_divergent_mask])
        # Zの実部と虚部から偏角を計算し、0-1の範囲に正規化
        angle = (np.arctan2(z_imag, z_real) / (2 * np.pi)) + 0.5
        # カラーマップを使って色を取得し、非発散部分を塗りつぶす
        colored[non_divergent_mask] = non_cmap_func(angle) * 255.0
