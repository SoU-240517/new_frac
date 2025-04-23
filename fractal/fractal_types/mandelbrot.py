import numpy as np
from ui.zoom_function.debug_logger import DebugLogger
from ui.zoom_function.enums import LogLevel

def compute_mandelbrot(Z, Z0, max_iter, logger: DebugLogger) -> dict:
    """マンデルブロ集合の計算
    Args:
        Z (np.ndarray): 初期値
        Z0 (complex): 初期値
        max_iter (int): 最大反復回数
        logger (DebugLogger): ログ出力クラス
    Returns:
        dict: 計算結果
    """
    shape = Z.shape
    iterations = np.zeros(shape, dtype=int)
    z = np.full(shape, Z0, dtype=complex)
    c = Z.copy()
    mask = np.abs(z) <= 2.0
    z_vals = np.zeros(shape, dtype=complex)

    for i in range(max_iter):
        mask = np.abs(z) <= 2.0
        if not np.any(mask):
            break
        z[mask] = z[mask]**2 + c[mask]
        iterations[mask & (np.abs(z) > 2.0)] = i + 1
        z_vals = z.copy()
    iterations[mask] = 0

    return {
        'iterations': iterations,
        'mask': mask,
        'z_vals': z_vals
    }
