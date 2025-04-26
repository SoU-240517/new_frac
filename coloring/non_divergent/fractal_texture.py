import numpy as np
from typing import Dict, Tuple
from matplotlib.colors import Colormap
from ui.zoom_function.debug_logger import DebugLogger
from ui.zoom_function.enums import LogLevel

def apply_fractal_texture(
    colored: np.ndarray,
    non_divergent_mask: np.ndarray,
    z_vals: np.ndarray, # iterations の代わりに z_vals を受け取る
    non_cmap_func: Colormap, # 正しいカラーマップ関数を受け取る
    params: Dict,
    logger: DebugLogger
) -> None:
    """非発散部：フラクタルテクスチャで着色する
        非発散部をマルチオクターブノイズを使用したフラクタルテクスチャで着色する
    Args:
        colored (np.ndarray): 出力用のRGBA配列 (形状: (h, w, 4), dtype=float32)
        non_divergent_mask (np.ndarray): 非発散した点のマスク (形状: (h, w), dtype=bool)
        z_vals (np.ndarray): 複素数配列
        non_cmap_func (Colormap): 非発散部分用のカラーマップ関数
        params (Dict): 着色パラメータ
        logger (DebugLogger): ロガーインスタンス
    Notes:
        - マルチオクターブノイズを使用してフラクタルテクスチャを生成
        - 各ノイズのスケールは 5.0, 10.0, 20.0 を使用
        - 正規化された値をカラーマップ関数に渡すことで、一貫性のある色付けを実現
    """
    # ノイズ生成関数を定義
    def noise(x, y, scale=1.0): # noise関数内のscaleパラメータを調整
        return np.sin(scale * x) * np.cos(scale * y)

    # 非発散点の複素数座標を取得
    x = np.real(z_vals[non_divergent_mask])
    y = np.imag(z_vals[non_divergent_mask])

    # マルチオクターブノイズ
    # 異なるスケールと重みでノイズを生成し、組み合わせる
    n1 = noise(x, y, 5.0) # 基本周波数
    n2 = noise(x, y, 10.0) * 0.5 # 第2周波数、振幅を半分に
    n3 = noise(x, y, 20.0) * 0.25 # 第3周波数、振幅を1/4に
    combined = n1 + n2 + n3 # 各オクターブのノイズを合成

    # ノイズ値を0から1の範囲に正規化
    # np.min と np.max を使用して、現在のデータ範囲に基づいて正規化
    normalized = (combined - np.min(combined)) / (np.max(combined) - np.min(combined))

    # 正規化された位相値をカラーマップに適用
    # 結果を255倍して0-255の範囲に変換
    colored[non_divergent_mask] = non_cmap_func(normalized) * 255.0
