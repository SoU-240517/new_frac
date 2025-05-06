import numpy as np
from matplotlib.colors import Colormap
from typing import Dict, Tuple
from debug import DebugLogger, LogLevel
from coloring.utils import _normalize_and_color

def apply_color(iterations: np.ndarray, z_values: np.ndarray, mask: np.ndarray, params: dict, logger: DebugLogger, config: dict) -> np.ndarray:
    """
    スムージングによる着色を行う関数

    Args:
        iterations (np.ndarray): 各点の反復回数
        z_values (np.ndarray): 各点の最終的なZ値
        mask (np.ndarray): 着色対象のマスク (Trueの部分を着色)
        params (dict): カラーマップ名などのパラメータ
        logger (DebugLogger): ロガー
        config (dict): アプリケーション設定

    Returns:
        np.ndarray: 着色後のRGBA画像データ (形状: (height, width, 4), 値域: 0-255)
    """
    logger.log(LogLevel.CALL, "Smoothing プラグインによる着色開始")
    # ここに具体的なスムージング処理とカラーマップ適用処理を記述
    # ... (既存の manager.py 内の該当処理を参考に)
    colored_image_segment = np.zeros((*iterations.shape, 4), dtype=np.uint8) # 仮の画像データ
    # ...
    logger.log(LogLevel.SUCCESS, "Smoothing プラグインによる着色完了")
    return colored_image_segment

def apply_angle_coloring(
    colored: np.ndarray,
    divergent_mask: np.ndarray,
    z_vals: np.ndarray,
    cmap_func: Colormap,
    params: Dict,
    logger: DebugLogger
) -> None:
    """発散領域に対して、複素数の偏角に基づいたカラーリングを適用する
    - 複素数の偏角を計算し、カラーマップを用いて着色する
    Args:
        colored (np.ndarray): 出力先のRGBA配列 (形状: (h, w, 4), dtype=float32)
        divergent_mask (np.ndarray): 発散した点のマスク配列 (形状: (h, w), dtype=bool)
        z_vals (np.ndarray): 各点での複素数の値を持つ配列 (形状: (h, w), dtype=complex)
        cmap_func (Colormap): 発散領域の着色に使うカラーマップ関数
        params (Dict): 使用しない
        logger (DebugLogger): デバッグ用ロガー
    """
    # 複素数の角度を計算し、0〜1の範囲に正規化
    # np.angle()は-π〜πの範囲を返すため、2πで割って0〜1の範囲に変換し、0.5を加算して0〜1の範囲に正規化
    angles = np.angle(z_vals) / (2 * np.pi) + 0.5

    # 発散した点のみを対象にカラーマップを適用
    # cmap_funcの結果を0〜255の範囲に変換してcolored配列に書き込む
    colored[divergent_mask] = cmap_func(angles[divergent_mask]) * 255.0
