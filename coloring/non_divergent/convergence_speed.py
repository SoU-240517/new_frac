import numpy as np
from typing import Dict, Tuple
from matplotlib.colors import Colormap
from ui.zoom_function.debug_logger import DebugLogger
from ui.zoom_function.enums import LogLevel

def apply_convergence_speed(
    colored: np.ndarray,
    non_divergent_mask: np.ndarray,
    z_vals: np.ndarray, # iterations の代わりに z_vals を受け取る
    non_cmap_func: Colormap, # 正しいカラーマップ関数を受け取る
    params: Dict,
    logger: DebugLogger
) -> None:
    """非発散部：反復収束速度で着色する
    Args:
        colored (np.ndarray): 出力用のRGBA配列 (形状: (h, w, 4), dtype=float32)
        non_divergent_mask (np.ndarray): 非発散した点のマスク (形状: (h, w), dtype=bool)
        z_vals (np.ndarray): 複素数配列
        non_cmap_func (Colormap): 非発散部分用のカラーマップ関数
        params (Dict): 着色パラメータ
        logger (DebugLogger): ロガーインスタンス
    """
    # 収束速度の計算：1/|z|で計算し、zが0に近づくほど収束が速いと判断
    # 1e-10の加算はゼロ除算を防ぐための安全対策
    speed = 1 / (np.abs(z_vals[non_divergent_mask]) + 1e-10)

    # 速度値を0-1の範囲に正規化
    # この正規化により、カラーマップに適切な値を供給できる
    normalized = (speed - np.min(speed)) / (np.max(speed) - np.min(speed))

    # ガンマ補正
    # 1.5: カラートランジションをより自然に見せる
    # 1.0: 線形補正
    # 2.0: より急なトランジション
    gamma = 1.5  # 1.0～2.0で調整
    normalized = normalized ** (1/gamma)

    # 正規化された位相値をカラーマップに適用
    # 結果を255倍して0-255の範囲に変換
    colored[non_divergent_mask] = non_cmap_func(normalized) * 255.0
