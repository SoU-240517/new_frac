import numpy as np
from matplotlib.colors import Normalize, Colormap
from typing import Optional
from ui.zoom_function.debug_logger import DebugLogger
from ui.zoom_function.enums import LogLevel

"""着色処理のための共通ユーティリティ関数"""

class ColorAlgorithmError(Exception):
    """着色アルゴリズム関連のエラーを処理する例外クラス
    この例外は、着色処理中に発生するエラーをキャッチするために使用される
    主に以下のケースで発生：
    - 不正な着色アルゴリズムの指定
    - 計算値の範囲エラー
    - パラメータの不整合
    """
    pass

def _normalize_and_color(values: np.ndarray, cmap: Colormap, vmin: Optional[float] = None, vmax: Optional[float] = None) -> np.ndarray:
    """値を正規化してカラーマップを適用し、RGBA配列（0-255）を返す
    Args:
        values (np.ndarray): 着色対象の値 (NaN や Inf を含まないこと)
        cmap (Colormap): 色マップ
        vmin (float, optional): 正規化の最小値。Noneの場合は値から自動計算。
        vmax (float, optional): 正規化の最大値。Noneの場合は値から自動計算。
    Returns:
        np.ndarray: 着色されたRGBA配列 (形状: values.shape + (4,), dtype=float32, 値域: 0.0-255.0)
    Notes:
        - 入力 values に NaN や Inf が含まれている場合の動作は未定義です。
          呼び出し側で適切に処理してください。
        - vmin と vmax が同じ場合、vmaxに微小値を加算してゼロ除算を防ぎます。
    """
    # vmin/vmax が指定されていない、または NaN/Inf の場合に計算
    # np.isfiniteで有限な値のみを対象にする
    finite_values = values[np.isfinite(values)]

    # 有効な値がない場合はデフォルト値を設定するか、エラーを出す (ここではデフォルト値)
    if finite_values.size == 0:
        # 有効な値がない場合、デフォルトの黒色 (0, 0, 0, 255) を返す
        # またはエラーを発生させる (ここでは黒を返す)
        return np.zeros(values.shape + (4,), dtype=np.float32) # shape + (4,) でRGBA次元を追加

    # vmin/vmax が None の場合、有限な値から計算
    if vmin is None:
        vmin = np.min(finite_values) if finite_values.size > 0 else 0.0
    if vmax is None:
        vmax = np.max(finite_values) if finite_values.size > 0 else 1.0

    # vminとvmaxが非常に近い、または同じ場合に対処
    if np.isclose(vmin, vmax):
        vmax = vmin + 1e-9 # 微小値を加えてゼロ除算を回避

    # 正規化オブジェクトを作成
    norm = Normalize(vmin=vmin, vmax=vmax)

    # 正規化とカラーマップ適用、0-255スケールに変換
    colored_values = np.nan_to_num(cmap(norm(values))) * 255.0

    return colored_values

def _smooth_iterations(z: np.ndarray, iters: np.ndarray, method: str = 'standard') -> np.ndarray:
    """反復回数のスムージングを適用
    Args:
        z (np.ndarray): 複素数配列
        iters (np.ndarray): 反復回数配列
        method (str): スムージング方法 ('standard', 'fast', 'exponential')
    Returns:
        np.ndarray: スムージングされた反復回数配列
    """
    if method == 'fast':
        # 高速スムージング
        out = np.zeros_like(iters, dtype=np.float32)
        fast_smoothing(z, iters, out)
        return out
    elif method == 'standard':
        # 標準スムージング
        abs_z = np.abs(z)
        # 発散した点 (abs(z) > 2) のマスク
        diverged_mask = abs_z > 2
        log2 = np.log(2)
        # 結果を格納する配列を NaN で初期化
        smooth_values = np.full(iters.shape, np.nan, dtype=np.float32)

        # 発散した点が存在する場合のみ計算
        if np.any(diverged_mask):
            # 発散した点の z と iterations を取得
            z_diverged = z[diverged_mask]
            iters_diverged = iters[diverged_mask]
            abs_z_diverged = np.abs(z_diverged) # abs_z[diverged_mask] と同じ

            # log(log(|z|)) の計算 (ゼロ除算、無効な値を無視)
            with np.errstate(divide='ignore', invalid='ignore'):
                # log(|z|) > 0 (つまり |z| > 1) が必要
                log_abs_z = np.log(abs_z_diverged)
                # log(log(|z|))
                log_log_abs_z = np.log(log_abs_z)

            # 計算結果が有限な点のみを対象とするマスク
            valid_calculation_mask = np.isfinite(log_log_abs_z)

            # 有効な計算ができた点に対してスムージング値を計算
            if np.any(valid_calculation_mask):
                calculated_smooth = (
                    iters_diverged[valid_calculation_mask] -
                    log_log_abs_z[valid_calculation_mask] / log2
                )
                # 元の配列の対応する位置に計算結果を代入
                # smooth_values の diverged_mask が True の部分を取得し、
                # さらにその中の valid_calculation_mask が True の部分に代入する
                # 一時変数を使わずに直接代入する方が、マスクの形状が一致しやすい
                temp_smooth = np.full(diverged_mask.sum(), np.nan, dtype=np.float32)
                temp_smooth[valid_calculation_mask] = calculated_smooth.astype(np.float32)
                smooth_values[diverged_mask] = temp_smooth

        return smooth_values
    elif method == 'exponential':
        # 指数スムージング
        abs_z = np.abs(z) + 1e-10  # 0除算を防ぐための微小値
        with np.errstate(divide='ignore', invalid='ignore'):
            return iters - np.log(np.log(abs_z)) / np.log(2)
    else:
        raise ColorAlgorithmError(f"Unknown smoothing method: {method}")

def fast_smoothing(z: np.ndarray, iters: np.ndarray, out: np.ndarray) -> None:
    """高速スムージングアルゴリズム（インプレース処理）
    Args:
        z (np.ndarray): 複素数配列
        iters (np.ndarray): 反復回数配列
        out (np.ndarray): スムージング結果を格納する配列 (itersと同じ形状)
    """
    with np.errstate(divide='ignore', invalid='ignore'):
        abs_z = np.abs(z)
        mask_smooth = abs_z > 2
        log2 = np.log(2)
        log_abs_z = np.log(abs_z[mask_smooth])
        valid_log_mask = np.isfinite(log_abs_z) & (log_abs_z > 0)
        smooth_values = np.full(iters[mask_smooth].shape, np.nan, dtype=np.float64)

        if np.any(valid_log_mask):
            log_log_abs_z = np.log(log_abs_z[valid_log_mask])
            valid_log_log_mask = np.isfinite(log_log_abs_z)
            if np.any(valid_log_log_mask):
                smooth_values[valid_log_mask][valid_log_log_mask] = (
                    iters[mask_smooth][valid_log_mask][valid_log_log_mask] -
                    log_log_abs_z[valid_log_log_mask] / log2
                )

        out[...] = iters.astype(np.float32)
        final_smooth_mask = np.zeros_like(mask_smooth, dtype=bool)
        final_smooth_mask[mask_smooth] = valid_log_mask & ~np.isnan(smooth_values)
        out[final_smooth_mask] = smooth_values[~np.isnan(smooth_values)].astype(np.float32)
