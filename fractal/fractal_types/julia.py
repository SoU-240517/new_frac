import numpy as np
from ui.zoom_function.debug_logger import DebugLogger
from ui.zoom_function.enums import LogLevel
from typing import Dict

def compute_julia(
    Z: np.ndarray,  # 複素数のグリッド
    C: complex,     # ジュリア集合のパラメータ
    max_iter: int,  # 最大反復回数
    logger: DebugLogger  # デバッグログ用
) -> Dict[str, np.ndarray]:
    """ジュリア集合の計算を実行
    Args:
        Z (np.ndarray): 複素数のグリッド配列
        C (complex): ジュリア集合のパラメータ
        max_iter (int): 最大反復回数
        logger (DebugLogger): デバッグログ出力用オブジェクト
    Returns:
        Dict[str, np.ndarray]: 計算結果を含む辞書
            - 'iterations': 各点の反復回数
            - 'mask': 収束判定用のマスク
            - 'z_vals': 最終的な複素数値
    Notes:
        ジュリア集合は、z = z^2 + C の反復式で定義される
        |z| > 2 の時点で発散すると判断する
    """
    # グリッドの形状を取得
    shape = Z.shape
    
    # 初期化
    iterations = np.zeros(shape, dtype=int)  # 反復回数カウンタ
    current_z = Z.copy()  # 現在の複素数値
    mask = np.abs(current_z) <= 2.0  # 初期マスク：絶対値2以下の点
    final_z = np.zeros(shape, dtype=complex)  # 最終的な複素数値

    # 反復計算
    for iteration in range(max_iter):
        mask = np.abs(current_z) <= 2.0  # 収束判定
        
        # 収束する点がなければ終了
        if not np.any(mask):
            break
        
        # ジュリア集合の反復式を適用
        current_z[mask] = current_z[mask]**2 + C
        
        # 発散した点の反復回数を記録
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
