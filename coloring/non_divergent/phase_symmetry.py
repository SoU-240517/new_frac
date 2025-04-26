import numpy as np
from typing import Dict, Tuple
from matplotlib.colors import Colormap
from ui.zoom_function.debug_logger import DebugLogger
from ui.zoom_function.enums import LogLevel

def apply_phase_symmetry(
    colored: np.ndarray,
    non_divergent_mask: np.ndarray,
    z_vals: np.ndarray,
    non_cmap_func: Colormap,
    params: Dict,
    logger: DebugLogger
) -> None:
    """非発散部：位相対称で着色する
    Args:
        colored (np.ndarray): 出力用のRGBA配列 (形状: (h, w, 4), dtype=float32)
        non_divergent_mask (np.ndarray): 非発散した点のマスク (形状: (h, w), dtype=bool)
        z_vals (np.ndarray): 複素数配列
        non_cmap_func (Colormap): 非発散部分用のカラーマップ関数
        params (Dict): 着色パラメータ
        logger (DebugLogger): ロガーインスタンス
    """
    # 複素数の位相（角度）を取得
    # np.angleは[-π, π)の範囲で角度を返す
    angles = np.angle(z_vals[non_divergent_mask])

    # 対称性の次数 (4なら90度ごとに同じ色)
    symmetry_order = 5 # 3～8の整数で様々な対称性が試せます
    
    # 位相を対称性の次数で正規化
    # 2πをsymmetry_orderで分割することで、指定された次数の対称性を実現
    # % 1.0で0-1の範囲に正規化
    normalized = (angles * symmetry_order / (2*np.pi)) % 1.0

    # ガンマ補正
    # 1.5: カラートランジションをより自然に見せる
    # 1.0: 線形補正
    # 2.0: より急なトランジション
    gamma = 1.5 # 1.0～2.0で調整
    normalized = normalized ** (1/gamma)

    # 正規化された位相値をカラーマップに適用
    # 結果を255倍して0-255の範囲に変換
    colored[non_divergent_mask] = non_cmap_func(normalized) * 255.0
