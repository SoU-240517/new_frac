import numpy as np
from debug.debug_logger import DebugLogger
from debug.enum_debug import LogLevel
from typing import Dict

def compute_julia(
    Z: np.ndarray,  # 複素数のグリッド
    C: complex,     # ジュリア集合のパラメータ
    max_iter: int,  # 最大反復回数
    logger: DebugLogger  # デバッグログ用
) -> Dict[str, np.ndarray]:
    """ジュリア集合の計算を実行
    - 複素グリッドとパラメータからジュリア集合を計算する
    - 各点での反復回数、収束マスク、最終的な複素数値を返す
    Args:
        Z (np.ndarray): 複素数を格納したグリッド配列
        C (complex): ジュリア集合の計算に用いる複素パラメータ
        max_iter (int): ジュリア集合の最大反復回数
        logger (DebugLogger): デバッグログ出力用のロガーオブジェクト
    Returns:
        Dict[str, np.ndarray]: 計算結果を格納した辞書
            - 'iterations': 各グリッド点での反復回数
            - 'mask': 収束判定に使用したマスク配列
            - 'z_vals': 各グリッド点の最終的な複素数値
    Notes:
        ジュリア集合は z = z^2 + C の反復式で定義される
        反復計算において |z| > 2 となる場合、その点は発散するとみなす
    """
    # グリッドの形状を取得
    shape = Z.shape

    # 初期化
    iterations = np.zeros(shape, dtype=int)  # 各点での反復回数を格納する配列
    current_z = Z.copy()  # 現在の複素数値のグリッド
    mask = np.abs(current_z) <= 2.0  # 初期マスク：絶対値が2以下の点を選択
    final_z = np.zeros(shape, dtype=complex)  # 最終的な複素数値を格納する配列

    # 反復計算
    for iteration in range(max_iter):
        mask = np.abs(current_z) <= 2.0  # 現在のマスクを更新：絶対値が2以下の点

        # 全ての点が発散した場合、計算を終了する
        if not np.any(mask):
            break

        # ジュリア集合の反復式を適用: z = z^2 + C
        current_z[mask] = current_z[mask]**2 + C

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
