import numpy as np
from typing import Dict
from debug import DebugLogger, LogLevel

def compute_julia(
    Z: np.ndarray,  # 複素数のグリッド
    params: dict,  # 全パラメータを受け取る
    logger: DebugLogger  # デバッグログ用
) -> Dict[str, np.ndarray]:
    """
    ジュリア集合の計算を実行
    - 複素グリッドとパラメータからジュリア集合を計算する
    - 各点での反復回数、収束マスク、最終的な複素数値を返す

    Args:
        Z (np.ndarray): 複素数を格納したグリッド配列
        params (dict): ジュリア集合の計算に必要なパラメータを含む辞書
            - 'c_real': 複素数Cの実部（デフォルト: -0.8）
            - 'c_imag': 複素数Cの虚部（デフォルト: 0.156）
            - 'max_iterations': 最大反復回数（デフォルト: 100）
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
    # パラメータ取得（デフォルト値付き）
    c_real = params.get("c_real", -0.8)
    c_imag = params.get("c_imag", 0.156)
    max_iter = params.get("max_iterations", 100)

    C = complex(c_real, c_imag)

    # 初期化
    iterations = np.zeros(Z.shape, dtype=int)
    current_z = Z.copy()
    mask = np.abs(current_z) <= 2.0

    # 反復計算
    for iteration in range(max_iter):
        mask = np.abs(current_z) <= 2.0
        if not np.any(mask):
            break

        current_z[mask] = current_z[mask]**2 + C
        newly_diverged = mask & (np.abs(current_z) > 2.0)
        iterations[newly_diverged] = iteration + 1

    iterations[mask] = 0

    return {
        'iterations': iterations,
        'mask': mask,
        'z_vals': current_z
    }
