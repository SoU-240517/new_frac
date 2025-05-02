import numpy as np
from typing import Dict
from debug import DebugLogger, LogLevel

def compute_mandelbrot(
    Z: np.ndarray,  # 複素数のグリッド
    Z0: complex,    # 初期値
    max_iter: int,  # 最大反復回数
    logger: DebugLogger  # デバッグログ用
) -> Dict[str, np.ndarray]:
    """マンデルブロ集合の計算を実行
    - 複素グリッドと初期値からマンデルブロ集合を計算する
    - 各点での反復回数、収束マスク、最終的な複素数値を返す
    Args:
        Z (np.ndarray): 複素数を格納したグリッド配列
        Z0 (complex):  反復計算の初期値（通常は0）
        max_iter (int): マンデルブロ集合の最大反復回数
        logger (DebugLogger): デバッグログ出力用のロガーオブジェクト
    Returns:
        Dict[str, np.ndarray]: 計算結果を格納した辞書
            - 'iterations': 各グリッド点での反復回数
            - 'mask': 収束判定に使用したマスク配列
            - 'z_vals': 各グリッド点の最終的な複素数値
    Notes:
        マンデルブロ集合は z = z^2 + c の反復式で定義される
        反復計算において |z| > 2 となる場合、その点は発散するとみなす
        c はグリッド上の対応する点の複素数
    """
    # グリッドの形状を取得
    shape = Z.shape

    # 初期化
    iterations = np.zeros(shape, dtype=int)  # 各点での反復回数を格納する配列
    current_z = np.full(shape, Z0, dtype=complex)  # 現在の複素数値のグリッド。初期値Z0で初期化
    c = Z.copy()  # グリッドの各点が反復式におけるcの値に対応
    mask = np.abs(current_z) <= 2.0  # 初期マスク：絶対値が2以下の点を選択
    final_z = np.zeros(shape, dtype=complex)  # 最終的な複素数値を格納する配列

    # 反復計算
    for iteration in range(max_iter):
        mask = np.abs(current_z) <= 2.0  # 現在のマスクを更新：絶対値が2以下の点

        # 全ての点が発散した場合、計算を終了する
        if not np.any(mask):
            break

        # マンデルブロ集合の反復式を適用: z = z^2 + c
        current_z[mask] = current_z[mask]**2 + c[mask]

        # 新たに発散した点の反復回数を記録
        newly_diverged = mask & (np.abs(current_z) > 2.0)
        iterations[newly_diverged] = iteration + 1

        # 最終的な複素数値を保存
        final_z = current_z.copy()

    # 収束した点の反復回数を0に設定
    iterations[mask] = 0

    return {
        'iterations': iterations,
        'mask': mask,
        'z_vals': final_z
    }
