import numpy as np
from typing import Dict
from debug import DebugLogger, LogLevel

def compute_mandelbrot(
    Z: np.ndarray,  # 複素数のグリッド
    params: dict,   # 全パラメータを含む辞書
    logger: DebugLogger  # デバッグログ用
) -> Dict[str, np.ndarray]:
    """
    マンデルブロ集合の計算を実行
    - 複素グリッドと初期値からマンデルブロ集合を計算する
    - 各点での反復回数、収束マスク、最終的な複素数値を返す

    Args:
        Z (np.ndarray): 複素数を格納したグリッド配列
        params (dict): 計算パラメータを含む辞書
            - z0_real: 初期値の実部（デフォルト: 0.0）
            - z0_imag: 初期値の虚部（デフォルト: 0.0）
            - max_iterations: 最大反復回数（デフォルト: 100）
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
    # パラメータ取得（デフォルト値付き）
    z0_real = params.get("z0_real", 0.0)
    z0_imag = params.get("z0_imag", 0.0)
    max_iter = params.get("max_iterations", 100)

    Z0 = complex(z0_real, z0_imag)

    # グリッドの形状を取得
    shape = Z.shape

    # 初期化
    iterations = np.zeros(shape, dtype=int)
    current_z = np.full(shape, Z0, dtype=complex)
    c = Z.copy()
    mask = np.abs(current_z) <= 2.0
    final_z = np.zeros(shape, dtype=complex)

    # 反復計算
    for iteration in range(max_iter):
        mask = np.abs(current_z) <= 2.0

        if not np.any(mask):
            break

        current_z[mask] = current_z[mask]**2 + c[mask]
        newly_diverged = mask & (np.abs(current_z) > 2.0)
        iterations[newly_diverged] = iteration + 1
        final_z = current_z.copy()

    iterations[mask] = 0

    return {
        'iterations': iterations,
        'mask': mask,
        'z_vals': final_z
    }
