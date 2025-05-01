import numpy as np
from typing import Dict
from matplotlib.colors import Colormap
from debug.debug_logger import DebugLogger
from debug.enum_debug import LogLevel

def apply_chaotic_orbit(
    colored: np.ndarray,
    non_divergent_mask: np.ndarray,
    z_vals: np.ndarray, # iterations の代わりに z_vals を受け取る
    non_cmap_func: Colormap, # 正しいカラーマップ関数を受け取る
    params: Dict,
    logger: DebugLogger
) -> None:
    """非発散領域をカオス軌道で着色する
    - 非発散領域の各点に対して、複素数値に基づいたRGB値を計算し、出力配列に適用する
    Args:
        colored (np.ndarray): 出力用のRGBA配列 (形状: (h, w, 4), dtype=float32)
        non_divergent_mask (np.ndarray): 非発散点のマスク配列 (形状: (h, w), dtype=bool)
        z_vals (np.ndarray): 複素数値の配列
        non_cmap_func (Colormap): 非発散領域の着色に使用するカラーマップ関数
        params (Dict): 使用しない
        logger (DebugLogger): デバッグ用ロガーインスタンス
    """
    # 非発散点の複素数値から極座標系の値を計算
    # r: 複素数の絶対値（原点からの距離）
    # theta: 複素数の偏角（位相）
    r = np.abs(z_vals[non_divergent_mask])
    theta = np.angle(z_vals[non_divergent_mask])

    # カオス軌道の特徴を反映したRGB値の計算
    # 各チャンネルに異なる数学関数を適用することで、
    # 複雑で一意なパターンを生成
    red = np.sin(r * 5.0)**2 # 距離に基づく周期的な変動
    green = (np.cos(theta * 3.0) + 1) / 2 # 位相に基づく周期的な変動
    blue = (np.sin(r * 3.0 + theta * 2.0) + 1) / 2 # 距離と位相の組み合わせ

    # RGB値を0-1の範囲に正規化し、255倍して8bitカラーバリューに変換
    # アルファチャンネルは完全不透明（1.0）に設定
    colored[non_divergent_mask] = np.stack([red, green, blue, np.ones_like(red)], axis=-1) * 255.0
