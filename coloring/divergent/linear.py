import numpy as np
from matplotlib.colors import Normalize, Colormap
from typing import Dict

# coloring.utils から正規化関数をインポート
# manager.py から呼び出されることを想定し、相対インポートを使用
from ..utils import _normalize_and_color

# from ui.zoom_function.debug_logger import DebugLogger # 必要に応じてコメント解除
# from ui.zoom_function.enums import LogLevel # 必要に応じてコメント解除

"""発散部分の着色: 反復回数線形マッピング"""

def apply_linear_mapping(
    colored: np.ndarray,
    divergent_mask: np.ndarray,
    iterations: np.ndarray,
    cmap_func: Colormap,
    params: Dict,
    # logger: DebugLogger # 必要に応じてコメント解除
    ) -> None:
    """発散部分を反復回数の線形マッピングで着色する (インプレース処理)
    Args:
        colored (np.ndarray): 着色結果を格納するRGBA配列 (形状: (height, width, 4), dtype=float32)
        divergent_mask (np.ndarray): 発散した点のマスク (形状: (height, width), dtype=bool)
        iterations (np.ndarray): 反復回数配列 (形状: (height, width), dtype=int)
        cmap_func (Colormap): 発散部分用のカラーマップ関数
        params (Dict): 計算パラメータ辞書 ('max_iterations' を含む)
        logger (DebugLogger): ロガーインスタンス
    """
    # logger.log(LogLevel.DEBUG, "Applying linear mapping for divergent points.") # 必要に応じてロギング

    # 発散した点の反復回数を取得
    divergent_iters = iterations[divergent_mask]

    # 有効な反復回数がない場合は何もしない
    if divergent_iters.size == 0:
        # logger.log(LogLevel.DEBUG, "No divergent points to color with linear mapping.") # 必要に応じてロギング
        return

    # 線形正規化 (1 から max_iterations の範囲)
    # Normalize は vmin, vmax が同じだとエラーになる可能性があるため、チェックが必要
    min_iter = 1
    max_iter = params.get("max_iterations", 100) # params辞書にキーがない場合のデフォルト値

    # max_iterationsが1以下のような稀なケースに対応
    if max_iter <= min_iter:
        max_iter = min_iter + 1

    # _normalize_and_color を使用して正規化と着色を行う
    # マスクされた部分だけを処理するため、一時的な配列に着色結果を格納
    colored_divergent_part = _normalize_and_color(
        divergent_iters,
        cmap_func,
        vmin=min_iter,
        vmax=max_iter
    )

    # 元の colored 配列の対応する位置に着色結果を代入
    colored[divergent_mask] = colored_divergent_part

    # logger.log(LogLevel.DEBUG, f"Applied linear mapping to {divergent_iters.size} points.") # 必要に応じてロギング
