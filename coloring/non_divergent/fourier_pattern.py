import numpy as np
from typing import Dict, Tuple
from matplotlib.colors import Colormap
from ui.zoom_function.debug_logger import DebugLogger
from ui.zoom_function.enums import LogLevel

def apply_fourier_pattern(
    colored: np.ndarray,
    non_divergent_mask: np.ndarray,
    z_vals: np.ndarray, # iterations の代わりに z_vals を受け取る
    non_cmap_func: Colormap, # 正しいカラーマップ関数を受け取る
    params: Dict,
    logger: DebugLogger
) -> None:
    """非発散部：フーリエ干渉で着色する
    Args:
        colored (np.ndarray): 出力用のRGBA配列 (形状: (h, w, 4), dtype=float32)
        non_divergent_mask (np.ndarray): 非発散した点のマスク (形状: (h, w), dtype=bool)
        z_vals (np.ndarray): 複素数配列
        non_cmap_func (Colormap): 非発散部分用のカラーマップ関数
        params (Dict): 着色パラメータ
        logger (DebugLogger): ロガーインスタンス
    """
    # 非発散点の実部と虚部を取得
    x = np.real(z_vals[non_divergent_mask])
    y = np.imag(z_vals[non_divergent_mask])

    # 複数の周波数成分を合成して干渉パターンを生成
    # 10.0, 8.0, 5.0, 3.0の周波数で干渉パターンを作成
    # これらの周波数は視覚的に魅力的なパターンを生成するために選択
    pattern = (np.sin(x * 10.0) * np.cos(y * 8.0) +
            np.sin(x * 5.0 + y * 3.0)) / 2.0

    # 生成されたパターンを0-1の範囲に正規化
    normalized = (pattern - np.min(pattern)) / (np.max(pattern) - np.min(pattern))

    # 正規化された位相値をカラーマップに適用
    # 結果を255倍して0-255の範囲に変換
    colored[non_divergent_mask] = non_cmap_func(normalized) * 255.0
