FILE_NAME = "fractal_texture.py"

# 表示名 (UIのコンボボックスで使われる)
DISPLAY_NAME = "フラクタルテクスチャ"

# このプラグインのメインの着色関数の名前
COLORING_FUNCTION_NAME = "apply_fractal_texture"

import numpy as np
from matplotlib.colors import Colormap
from typing import Dict, Tuple
from debug import DebugLogger, LogLevel

def apply_fractal_texture(
    colored: np.ndarray,
    non_divergent_mask: np.ndarray,
    z_vals: np.ndarray, # iterations の代わりに z_vals を受け取る
    non_cmap_func: Colormap, # 正しいカラーマップ関数を受け取る
    params: Dict,
    logger: DebugLogger
) -> None:
    """非発散領域をフラクタルテクスチャで着色する
    - 非発散領域をマルチオクターブノイズを使用したフラクタルテクスチャで着色する
    Args:
        colored (np.ndarray): 出力用のRGBA配列 (形状: (h, w, 4), dtype=float32)
        non_divergent_mask (np.ndarray): 非発散点のマスク配列 (形状: (h, w), dtype=bool)
        z_vals (np.ndarray): 複素数値の配列
        non_cmap_func (Colormap): 非発散領域の着色に使用するカラーマップ関数
        params (Dict): 使用しない
        logger (DebugLogger): デバッグ用ロガーインスタンス
    """
    # ノイズ生成関数を定義
    def noise(x, y, scale=1.0):
        """指定されたスケールで2次元ノイズを生成する

        Args:
            x (float): x座標
            y (float): y座標
            scale (float, optional): ノイズのスケール. Defaults to 1.0.

        Returns:
            float: 指定された座標におけるノイズの値
        """
        return np.sin(scale * x) * np.cos(scale * y)

    # 非発散点の複素数座標を取得
    x = np.real(z_vals[non_divergent_mask])
    y = np.imag(z_vals[non_divergent_mask])

    # マルチオクターブノイズを生成
    # 異なるスケールと重みでノイズを生成し、組み合わせる
    n1 = noise(x, y, 5.0) # 基本周波数成分
    n2 = noise(x, y, 10.0) * 0.5 # 第2周波数成分、振幅を半分に
    n3 = noise(x, y, 20.0) * 0.25 # 第3周波数成分、振幅を1/4に
    combined = n1 + n2 + n3 # 各オクターブのノイズを合成

    # ノイズ値を0-1の範囲に正規化
    normalized = (combined - np.min(combined)) / (np.max(combined) - np.min(combined))

    # 正規化された値をカラーマップに適用し、0-255の範囲に変換
    colored[non_divergent_mask] = non_cmap_func(normalized) * 255.0
