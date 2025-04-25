import numpy as np
from typing import Dict, Tuple
from matplotlib.colors import Colormap
from ui.zoom_function.debug_logger import DebugLogger
from ui.zoom_function.enums import LogLevel


def apply_histogram_flattening(
    colored: np.ndarray,
    divergent_mask: np.ndarray,
    iterations: np.ndarray,
    cmap_func: Colormap,
    params: Dict,
    logger: DebugLogger
) -> None:
    """発散部：ヒストグラム平坦化法で着色する
    Args:
        colored (np.ndarray): 出力用のRGBA配列 (形状: (h, w, 4), dtype=float32)
        divergent_mask (np.ndarray): 発散した点のマスク (形状: (h, w), dtype=bool)
        iterations (np.ndarray): 反復回数配列 (形状: (h, w), dtype=int)
        cmap_func (Colormap): 発散部分用のカラーマップ関数
        params (Dict): 計算パラメータ辞書 ('max_iterations' を含む)
        logger (DebugLogger): ロガーインスタンス
    """
    # 発散した点を抽出
    # iterations > 0 は、発散した点（反復回数が0より大きい点）を意味します
    divergent = iterations > 0

    # ヒストグラムの計算
    # iterations[divergent] は発散した点の反復回数のみを取得
    # bins=params["max_iterations"] で、最大反復回数までのビンを指定
    # density=True により、確率密度関数として正規化
    hist, bins = np.histogram(iterations[divergent], bins=params["max_iterations"], density=True)

    # 累積分布関数（CDF）の計算
    cdf = hist.cumsum() # hist.cumsum() で累積和を計算
    cdf = cdf / cdf[-1] # cdf[-1] で正規化して0-1の範囲にスケーリング

    # 反復回数を累積分布関数の値にリマッピング
    # np.interp で線形補間を行い、発散の早い点と遅い点のコントラストを改善
    remapped = np.interp(iterations[divergent], bins[:-1], cdf)

    # リマッピングされた値をカラーマップに適用
    # cmap_func で色を決定し、255.0倍して0-255の範囲にスケーリング
    colored[divergent] = cmap_func(remapped) * 255.0
