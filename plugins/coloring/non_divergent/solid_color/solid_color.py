import numpy as np
from typing import Dict
from debug import DebugLogger, LogLevel

def apply_solid_color(
    colored: np.ndarray,
    non_divergent_mask: np.ndarray,
    params: Dict,
    logger: DebugLogger
    ) -> None:
    """非発散領域を単色で着色する
    フラクタル集合の非発散領域（内部領域）を指定された単色で塗りつぶす。
    Args:
        colored (np.ndarray): 着色結果を格納するRGBA配列 (形状: (height, width, 4), dtype=float32)
                               この配列の該当箇所が直接変更されます。
        non_divergent_mask (np.ndarray): 非発散領域を示すマスク配列
                                        (形状: (height, width), dtype=bool)
                                        True のピクセルが非発散領域です。
        params (Dict): パラメータを含む辞書 (現在は未使用)
        logger (DebugLogger): デバッグログ出力用ロガーインスタンス
    """
    # マスクがTrue（非発散）の箇所に色を設定
    # 色は [R, G, B, A] の形式で、値の範囲は 0.0 - 255.0
    # 現在は黒色 (0, 0, 0) で不透明 (255) に固定
    solid_color_rgba = [0.0, 0.0, 0.0, 255.0]

    # マスクを使用して、該当するピクセルに直接色を代入
    colored[non_divergent_mask] = solid_color_rgba
