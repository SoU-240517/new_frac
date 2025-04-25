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
        # logger.log(LogLevel.WARNING, "_normalize_and_color: No finite values found.") # 必要ならロギング
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
    # cmap()は通常0.0-1.0の範囲でRGBAを返すので、255.0を掛ける
    # np.nan_to_numで、正規化やカラーマップ適用中に発生しうる NaN/Inf を 0 に置換
    colored_values = np.nan_to_num(cmap(norm(values))) * 255.0

    # 期待される形状と一致しているか確認（デバッグ用）
    # print(f"Input shape: {values.shape}, Output shape: {colored_values.shape}")

    return colored_values

def fast_smoothing(z: np.ndarray, iters: np.ndarray, out: np.ndarray) -> None:
    """高速スムージングアルゴリズム（インプレース処理）
    Args:
        z (np.ndarray): 複素数配列
        iters (np.ndarray): 反復回数配列
        out (np.ndarray): スムージング結果を格納する配列 (itersと同じ形状)
    """
    # errstateで数値計算上の警告(ゼロ除算、無効な値)を無視
    with np.errstate(divide='ignore', invalid='ignore'):
        abs_z = np.abs(z)
        # スムージングを適用するマスク (絶対値が閾値(通常2)を超えた点)
        mask_smooth = abs_z > 2
        log2 = np.log(2)
        # スムージング計算: iter - log(log(|z|))/log(2)
        # np.log(abs_z[mask_smooth]) が非常に小さい場合、logが負の無限大になる可能性があるため注意
        log_abs_z = np.log(abs_z[mask_smooth])
        # log_abs_z が負の無限大やNaNでないことを確認
        valid_log_mask = np.isfinite(log_abs_z) & (log_abs_z > 0) # logの中は正である必要あり
        smooth_values = np.full(iters[mask_smooth].shape, np.nan, dtype=np.float64) # float64で精度確保

        if np.any(valid_log_mask):
             # np.log(log_abs_z[valid_log_mask]) が log(0) にならないように
             log_log_abs_z = np.log(log_abs_z[valid_log_mask])
             valid_log_log_mask = np.isfinite(log_log_abs_z)
             if np.any(valid_log_log_mask):
                 smooth_values[valid_log_mask][valid_log_log_mask] = iters[mask_smooth][valid_log_mask][valid_log_log_mask] - log_log_abs_z[valid_log_log_mask] / log2

        # 元のitersをoutにコピー
        out[...] = iters.astype(np.float32) # 出力配列の型に合わせる
        # スムージング計算が成功した箇所だけをoutに上書き
        # outのマスクもmask_smoothとvalid_log_maskを組み合わせる
        final_smooth_mask = np.zeros_like(mask_smooth, dtype=bool)
        final_smooth_mask[mask_smooth] = valid_log_mask & ~np.isnan(smooth_values) # NaNでない値のみ

        out[final_smooth_mask] = smooth_values[~np.isnan(smooth_values)].astype(np.float32) # NaNを除外して代入

def _smooth_iterations(z: np.ndarray, iters: np.ndarray, method: str = 'standard') -> np.ndarray:
    """反復回数のスムージング処理を実行
    Args:
        z (np.ndarray): 複素数配列
        iters (np.ndarray): 反復回数配列
        method (str): スムージング方法 ('standard', 'fast', 'exponential')
    Returns:
        np.ndarray: スムージングされた反復回数 (float)
    Raises:
        ColorAlgorithmError: 無効なスムージング方法が指定された場合
    Notes:
        - スムージングはフラクタルの境界線を滑らかにするために使用
        - 数値の不安定性を防ぐため、np.errstateを使用
    """
    if iters.size == 0:  # 空配列のチェック
        return np.zeros((800, 800), dtype=np.float32)  # 空配列の場合は0で埋めた配列を返す

    # errstateで数値計算上の警告(ゼロ除算、無効な値)を無視
    with np.errstate(invalid='ignore', divide='ignore'):
        if method == 'standard':
            # log(log(|z|)) の計算で NaN が発生しやすいので注意
            abs_z = np.abs(z)
            # abs_z が 1 より大きい場合にのみ計算可能 (log(log(1)) = log(0) -> -inf)
            valid_mask = abs_z > 1.0
            smooth_iter = iters.astype(np.float64)  # 計算精度のためfloat64に

            log_abs_z = np.log(abs_z[valid_mask])
            log_log_abs_z = np.log(log_abs_z)  # ここで log(0) や log(負数) の可能性
            valid_log_log_mask = np.isfinite(log_log_abs_z)

            nu = np.full(log_log_abs_z.shape, np.nan)
            if np.any(valid_log_log_mask):
                nu[valid_log_log_mask] = np.log(log_log_abs_z[valid_log_log_mask] / np.log(2.0)) / np.log(2.0)

            smooth_iter[valid_mask][valid_log_log_mask] = iters[valid_mask][valid_log_log_mask] + 1.0 - nu[valid_log_log_mask]
            
            # NaNの値を元のitersの値で補完
            nan_mask = np.isnan(smooth_iter)
            smooth_iter[nan_mask] = iters[nan_mask].astype(np.float64)
            
            return smooth_iter.astype(np.float32)  # 元の型に戻す

        elif method == 'fast':
            # 高速スムージング (専用関数を呼び出す)
            smooth_iter = np.zeros_like(iters, dtype=np.float32)
            fast_smoothing(z, iters, smooth_iter) # インプレースで smooth_iter が更新される
            return smooth_iter

        elif method == 'exponential':
            # 指数スムージング: iter + 1 - log(log(|z|)) / log(2)
            # 'standard' と同じ計算式だが、実装によっては微妙に異なる場合がある
            # ここでは standard と同じ実装とする
            abs_z = np.abs(z)
            valid_mask = abs_z > 1.0
            smooth_iter = iters.astype(np.float64)

            log_abs_z = np.log(abs_z[valid_mask])
            log_log_abs_z = np.log(log_abs_z)
            valid_log_log_mask = np.isfinite(log_log_abs_z)

            nu = np.full(log_log_abs_z.shape, np.nan)
            if np.any(valid_log_log_mask):
                 nu[valid_log_log_mask] = log_log_abs_z[valid_log_log_mask] / np.log(2.0) # 修正: standardの定義に合わせるなら log(nu)/log(2)だが、一般的にはこの形が多い

            smooth_iter[valid_mask][valid_log_log_mask] = iters[valid_mask][valid_log_log_mask] + 1.0 - nu[valid_log_log_mask]

            return np.nan_to_num(smooth_iter, nan=iters.astype(np.float64)[np.isnan(smooth_iter)]).astype(np.float32)

        else:
            # 未知のスムージング方法が指定されたらエラー
            raise ColorAlgorithmError(f"Unknown smoothing method: {method}")
