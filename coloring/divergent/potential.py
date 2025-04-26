import numpy as np
from typing import Dict, Tuple
from matplotlib.colors import Colormap
from ui.zoom_function.debug_logger import DebugLogger
from ui.zoom_function.enums import LogLevel
from ..utils import _normalize_and_color

def apply_potential(
    colored: np.ndarray,
    divergent_mask: np.ndarray,
    z_vals: np.ndarray,
    cmap_func: Colormap,
    params: Dict,
    logger: DebugLogger
) -> None:
    """発散部：ポテンシャル関数法で着色する
        ポテンシャル関数法とは、発散した点の強度を対数関数を用いて計算し、
        その値をカラーマップに変換して可視化する方法です。
        マンデルブロ集合などのフラクタル画像において、
        発散速度の違いを色で表現することで、より詳細な構造を可視化できます。
    Args:
        colored (np.ndarray): 出力用のRGBA配列 (形状: (h, w, 4), dtype=float32)
        divergent_mask (np.ndarray): 発散した点のマスク (形状: (h, w), dtype=bool)
        z_vals (np.ndarray): 複素数配列
        cmap_func (Colormap): 発散部分用のカラーマップ関数
        params (Dict): 着色パラメータ
        logger (DebugLogger): ロガーインスタンス
    """
    # 発散していない部分のマスクを作成
    mask = ~divergent_mask

    # 発散した点の複素数値を抽出
    z = z_vals[divergent_mask]

    # ポテンシャルの計算
    # ポテンシャル = log(|z|) - log(2) で、
    # log(2)の補正項は通常のポテンシャル値を0に正規化するため
    potential = np.log(np.abs(z)) - np.log(2.0)

    # 正規化と着色
    # ポテンシャル値を0-1の範囲に正規化
    normalized = (potential - np.min(potential)) / (np.max(potential) - np.min(potential))

    # 正規化された値をカラーマップに変換し、発散した部分に適用
    colored[divergent_mask] = cmap_func(normalized) * 255.0

    # 発散していない部分は黒（0）に設定
    colored[mask] = 0
