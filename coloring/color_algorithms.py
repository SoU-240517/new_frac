import time
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import Normalize
from coloring import gradient
from ui.zoom_function.debug_logger import DebugLogger
from ui.zoom_function.enums import LogLevel

def apply_coloring_algorithm(results, params, logger: DebugLogger):
    """ 着色アルゴリズムを適用（高速スムージング追加） """
    iterations = results['iterations']
    mask = results['mask'] # 発散しない点のマスク
    z_vals = results['z_vals'] # zの値
    colored = np.zeros((*iterations.shape, 4), dtype=np.float32) # RGBA形式の配列を初期化
    divergent = iterations > 0 # 発散した点のマスク
    # 高速スムージング用の事前計算

    def fast_smoothing(z, iters):
        """ 高速スムージングアルゴリズム """
        with np.errstate(divide='ignore', invalid='ignore'):
            abs_z = np.abs(z)
            # 近似計算: abs_z > 2 の領域のみ精密計算
            smooth = np.where(
                abs_z > 2,
                iters - np.log(np.log(abs_z)) / np.log(2),
                iters
            )
            return np.nan_to_num(smooth, nan=iters)

    # === 発散する場合の処理 ===
    if np.any(divergent):
        algo = params["diverge_algorithm"]
        logger.log(LogLevel.INFO, f"着色アルゴリズム選択: {algo}")
        if algo == "反復回数線形マッピング":
            norm = Normalize(1, params["max_iterations"])
            colored[divergent] = plt.cm.get_cmap(params["diverge_colormap"])(norm(iterations[divergent]))
        if algo == "スムージングカラーリング":
            with np.errstate(invalid='ignore', divide='ignore'):
                log_zn = np.log(np.abs(z_vals))
                nu = np.log(log_zn / np.log(2)) / np.log(2)
                smooth_iter = iterations - nu
            invalid_mask = ~np.isfinite(smooth_iter)
            smooth_iter[invalid_mask] = iterations[invalid_mask]
        elif algo == "高速スムージング":
            start_time = time.perf_counter()
            smooth_iter = fast_smoothing(z_vals, iterations)
            elapsed = time.perf_counter() - start_time
            logger.log(LogLevel.PERF, f"高速スムージング処理時間: {elapsed:.5f}秒")
        # 共通の正規化処理
        if algo in ["スムージングカラーリング", "高速スムージング"]:
            valid_vals = smooth_iter[divergent & np.isfinite(smooth_iter)]
            vmin = np.min(valid_vals) if len(valid_vals) > 0 else 0
            vmax = np.max(valid_vals) if len(valid_vals) > 0 else params["max_iterations"]
            norm = Normalize(vmin=vmin, vmax=vmax)
            colored[divergent] = plt.cm.get_cmap(params["diverge_colormap"])(norm(smooth_iter[divergent]))
        elif algo == "指数スムージング":
            with np.errstate(divide='ignore', invalid='ignore'):
                smooth_iter = iterations + 1 - np.log(np.log(np.abs(z_vals))) / np.log(2)
            # 不正な値の処理
            smooth_iter[~np.isfinite(smooth_iter)] = iterations[~np.isfinite(smooth_iter)]
            norm = Normalize(vmin=0, vmax=params["max_iterations"])
            colored[divergent] = plt.cm.get_cmap(params["diverge_colormap"])(norm(smooth_iter[divergent]))
        elif algo == "ヒストグラム平坦化法":
            hist, bins = np.histogram(iterations[divergent], bins=params["max_iterations"], density=True)
            cdf = hist.cumsum()
            cdf = cdf / cdf[-1]
            remapped = np.interp(iterations[divergent], bins[:-1], cdf)
            colored[divergent] = plt.cm.get_cmap(params["diverge_colormap"])(remapped)
        elif algo == "反復回数対数マッピング":
            iter_log = np.zeros_like(iterations, dtype=float)
            valid_iter = iterations[divergent] > 0 # log(0) を避ける
            iter_log[divergent][valid_iter] = np.log(iterations[divergent][valid_iter]) / np.log(params["max_iterations"])
            colored[divergent] = plt.cm.get_cmap(params["diverge_colormap"])(iter_log[divergent])
        elif algo == "距離カラーリング":
            dist = np.abs(z_vals)
            dist[mask] = 0
            norm = Normalize(0, 10) # この上限値(10)は調整可能
            colored[divergent] = plt.cm.get_cmap(params["diverge_colormap"])(norm(dist[divergent]))
        elif algo == "角度カラーリング":
            angles = np.angle(z_vals) / (2 * np.pi) + 0.5
            colored[divergent] = plt.cm.get_cmap(params["diverge_colormap"])(angles[divergent])
        elif algo == "ポテンシャル関数法":
            # log(|z|) が必要。|z|=0 や |z|=1 で問題発生の可能性
            with np.errstate(divide='ignore', invalid='ignore'):
                abs_z = np.abs(z_vals)
                log_abs_z = np.log(abs_z)
                # log_abs_z が 0 (つまり |z|=1) の場合に発散するのを防ぐ
                potential = np.full_like(log_abs_z, 0.0)
                valid_potential = (log_abs_z != 0) & np.isfinite(log_abs_z) & divergent
                potential[valid_potential] = -np.log(log_abs_z[valid_potential]) / log_abs_z[valid_potential]
                # Wikipedia等では log(|z|) で正規化する式もある -> 1 - log(log(|z|))/log(2)
                # potential = 1.0 - np.log(log_abs_z) / np.log(2) # こちらもlog(log)で警告の可能性
            potential[mask] = 0 # 発散しなかった点は0
            norm = Normalize(vmin=0) # vmin=0, vmaxはデータに依存
            colored[divergent] = plt.cm.get_cmap(params["diverge_colormap"])(norm(potential[divergent]))
        elif algo == "軌道トラップ法":
            # トラップ形状 (点、線、円など) によって定義が変わる
            # 例: 点 (1, 0) への距離
            trap_target = complex(1.0, 0.0)
            trap_dist = np.abs(z_vals - trap_target)
            # 発散しなかった点は無限大距離として扱う（色がつかないように）
            trap_dist[mask] = float('inf')
            # 発散した点のみを正規化
            min_dist = np.min(trap_dist[divergent]) if np.any(divergent) else 0
            max_dist = np.max(trap_dist[divergent & np.isfinite(trap_dist)]) if np.any(divergent & np.isfinite(trap_dist)) else 1
            # 距離が小さいほど明るくなるように反転させる場合もある
            # norm_dist = 1.0 - (trap_dist - min_dist) / (max_dist - min_dist + 1e-9)
            norm = Normalize(vmin=min_dist, vmax=max_dist)
            colored[divergent] = plt.cm.get_cmap(params["diverge_colormap"])(norm(trap_dist[divergent]))
    non_divergent = ~divergent
    if np.any(non_divergent):
        # === 発散しない場合の処理 ===
        non_algo = params["non_diverge_algorithm"]
        if non_algo == "単色":
            colored[non_divergent] = [0, 0, 0, 1] # 黒で塗りつぶし
        elif non_algo == "グラデーション":
            grad = gradient.compute_gradient(iterations.shape, logger)
            colored[non_divergent] = plt.cm.get_cmap(params["non_diverge_colormap"])(grad[non_divergent])
        elif non_algo == "パラメータ(C)":
            if params["fractal_type"] == "Julia":
                c_val = complex(params["c_real"], params["c_imag"])
                angle = (np.angle(c_val) / (2 * np.pi)) + 0.5
                # 非発散領域全体に同じ色を適用
                color_val = plt.cm.get_cmap(params["non_diverge_colormap"])(angle)
                colored[non_divergent] = color_val
            else: # Mandelbrotの場合、各点のC（座標値）を使う
                c_real, c_imag = np.real(z_vals[non_divergent]), np.imag(z_vals[non_divergent])
                angle = (np.arctan2(c_imag, c_real) / (2 * np.pi)) + 0.5
                colored[non_divergent] = plt.cm.get_cmap(params["non_diverge_colormap"])(angle)
        elif non_algo == "パラメータ(Z)":
            # 最終的なZ値を使う
            z_real, z_imag = np.real(z_vals[non_divergent]), np.imag(z_vals[non_divergent])
            angle = (np.arctan2(z_imag, z_real) / (2 * np.pi)) + 0.5
            colored[non_divergent] = plt.cm.get_cmap(params["non_diverge_colormap"])(angle)
    return colored
