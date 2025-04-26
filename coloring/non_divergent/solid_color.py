import numpy as np
from typing import Dict
from ui.zoom_function.debug_logger import DebugLogger
from ui.zoom_function.enums import LogLevel

def apply_solid_color(
    colored: np.ndarray,
    non_divergent_mask: np.ndarray,
    params: Dict,
    logger: DebugLogger
    ) -> None:
    """非発散部：単色（現在黒色）で着色する (インプレース処理)
    Args:
        colored (np.ndarray): 着色結果を格納するRGBA配列 (形状: (height, width, 4), dtype=float32)
                               この配列の該当箇所が直接変更されます。
        non_divergent_mask (np.ndarray): 非発散（フラクタル集合内部）の点のマスク
                                        (形状: (height, width), dtype=bool)
                                        True のピクセルが非発散部分です。
        params (Dict): 計算パラメータ辞書 (将来的に色を指定する場合に使用する可能性あり)
                       現在は未使用です。
        logger (DebugLogger): デバッグログを出力するためのロガーインスタンス。
    """
    # マスクがTrue（非発散）の箇所に色を設定
    # 色は [R, G, B, A] の形式で、値の範囲は 0.0 - 255.0
    # 現在は黒色 (0, 0, 0) で不透明 (255) に固定
    solid_color_rgba = [0.0, 0.0, 0.0, 255.0]

    # マスクを使用して、該当するピクセルに直接色を代入
    colored[non_divergent_mask] = solid_color_rgba
