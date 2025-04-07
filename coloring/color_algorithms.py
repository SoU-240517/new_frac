import numpy as np
import matplotlib.pyplot as plt
from coloring import gradient

def apply_coloring_algorithm(results, params):
    """ 着色アルゴリズムを適用して結果を返す """
    print("apply_coloring_algorithm:: FILE→ color_algorithms.py")
    iterations = results['iterations']
    mask = results['mask']
    z_vals = results['z_vals']

    # RGBA画像用の配列
    colored = np.zeros((*iterations.shape, 4))
    divergent = iterations > 0

    if np.any(divergent):
        # 発散する場合の処理
        algo = params["diverge_algorithm"]
        if algo == "反復回数線形マッピング":
            norm = plt.Normalize(1, params["max_iterations"])
            colored[divergent] = plt.cm.get_cmap(params["diverge_colormap"])(norm(iterations[divergent]))
        elif algo == "スムージングカラーリング":
            log_zn = np.log(np.abs(z_vals))
            nu = np.log(log_zn/np.log(2)) / np.log(2)
            smooth_iter = iterations - nu
            smooth_iter[mask] = 0
            norm = plt.Normalize(0, params["max_iterations"])
            colored[divergent] = plt.cm.get_cmap(params["diverge_colormap"])(norm(smooth_iter[divergent]))
        elif algo == "ヒストグラム平坦化法":
            hist, bins = np.histogram(iterations[divergent], bins=params["max_iterations"], density=True)
            cdf = hist.cumsum()
            cdf = cdf / cdf[-1]
            remapped = np.interp(iterations[divergent], bins[:-1], cdf)
            colored[divergent] = plt.cm.get_cmap(params["diverge_colormap"])(remapped)
        elif algo == "反復回数対数マッピング":
            iter_log = np.zeros_like(iterations, dtype=float)
            iter_log[divergent] = np.log(iterations[divergent]) / np.log(params["max_iterations"])
            colored[divergent] = plt.cm.get_cmap(params["diverge_colormap"])(iter_log[divergent])
        elif algo == "距離カラーリング":
            dist = np.abs(z_vals)
            dist[mask] = 0
            norm = plt.Normalize(0, 10)
            colored[divergent] = plt.cm.get_cmap(params["diverge_colormap"])(norm(dist[divergent]))
        elif algo == "角度カラーリング":
            angles = np.angle(z_vals) / (2 * np.pi) + 0.5
            colored[divergent] = plt.cm.get_cmap(params["diverge_colormap"])(angles[divergent])
        elif algo == "ポテンシャル関数法":
            potential = 1 - 1 / np.log(np.abs(z_vals) + 1)
            potential[mask] = 0
            colored[divergent] = plt.cm.get_cmap(params["diverge_colormap"])(potential[divergent])
        elif algo == "軌道トラップ法":
            trap_dist = np.abs(z_vals - 1.0)
            trap_dist[mask] = float('inf')
            norm = plt.Normalize(0, 2)
            colored[divergent] = plt.cm.get_cmap(params["diverge_colormap"])(norm(trap_dist[divergent]))

    non_divergent = ~divergent
    if np.any(non_divergent):
        # 発散しない場合の処理
        non_algo = params["non_diverge_algorithm"]
        if non_algo == "単色":
            colored[non_divergent] = [0, 0, 0, 1]
        elif non_algo == "グラデーション":
            grad = gradient.compute_gradient(iterations.shape)
            colored[non_divergent] = plt.cm.get_cmap(params["non_diverge_colormap"])(grad[non_divergent])
        elif non_algo == "パラメータ(C)":
            if params["fractal_type"] == "Julia":
                c_val = complex(params["c_real"], params["c_imag"])
                angle = (np.angle(c_val) / (2 * np.pi)) + 0.5
                colored[non_divergent] = plt.cm.get_cmap(params["non_diverge_colormap"])(angle)
            else:
                c_real, c_imag = np.real(z_vals), np.imag(z_vals)
                angle = (np.arctan2(c_imag, c_real) / (2 * np.pi)) + 0.5
                colored[non_divergent] = plt.cm.get_cmap(params["non_diverge_colormap"])(angle[non_divergent])
        elif non_algo == "パラメータ(Z)":
            z_real, z_imag = np.real(z_vals), np.imag(z_vals)
            angle = (np.arctan2(z_imag, z_real) / (2 * np.pi)) + 0.5
            colored[non_divergent] = plt.cm.get_cmap(params["non_diverge_colormap"])(angle[non_divergent])
    return colored
