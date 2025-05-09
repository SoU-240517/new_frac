import numpy as np
from matplotlib.colors import Colormap
from typing import Dict, Tuple
from debug import DebugLogger, LogLevel

def apply_fourier_pattern(
    colored: np.ndarray,
    non_divergent_mask: np.ndarray,
    z_vals: np.ndarray, # iterations の代わりに z_vals を受け取る
    non_cmap_func: Colormap, # 正しいカラーマップ関数を受け取る
    params: Dict,
    logger: DebugLogger
) -> None:
    """非発散領域をフーリエ干渉パターンで着色する
    - 非発散領域の複素数値の座標成分を用いて、複数の正弦波および余弦波を組み合わせた干渉パターンを生成し、着色に利用する
    Args:
        colored (np.ndarray): 出力用のRGBA配列 (形状: (h, w, 4), dtype=float32)
        non_divergent_mask (np.ndarray): 非発散点のマスク配列 (形状: (h, w), dtype=bool)
        z_vals (np.ndarray): 複素数値の配列
        non_cmap_func (Colormap): 非発散領域の着色に使用するカラーマップ関数
        params (Dict): 使用しない
        logger (DebugLogger): デバッグ用ロガーインスタンス
    """
    # 非発散点の実部と虚部を取得
    x = np.real(z_vals[non_divergent_mask])
    y = np.imag(z_vals[non_divergent_mask])

    # 複数の周波数成分を合成して干渉パターンを生成
    # 10.0, 8.0, 5.0, 3.0は視覚的に面白いパターンを生成するために選択された周波数
    pattern = (np.sin(x * 10.0) * np.cos(y * 8.0) +
            np.sin(x * 5.0 + y * 3.0)) / 2.0

    # 生成されたパターンを0-1の範囲に正規化
    normalized = (pattern - np.min(pattern)) / (np.max(pattern) - np.min(pattern))

    # 正規化された値をカラーマップに適用し、0-255の範囲に変換
    colored[non_divergent_mask] = non_cmap_func(normalized) * 255.0
