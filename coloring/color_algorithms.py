import time
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import Normalize
from coloring import gradient
from ui.zoom_function.debug_logger import DebugLogger
from ui.zoom_function.enums import LogLevel

class FractalCache:
    def __init__(self, max_size=100):
        self.cache = {}
        self.max_size = max_size
        self.logger = DebugLogger()
        self.logger.log(LogLevel.INFO, "FractalCache initialized")

    def _create_cache_key(self, params):
        # キャッシュキーを生成
        key_params = {
            'zoom_level': params.get('zoom_level', 1),
            'center': params.get('center', (0, 0)),
            'size': params.get('size', (1, 1)),
            'max_iterations': params.get('max_iterations', 100),
            'diverge_algorithm': params.get('diverge_algorithm', 'default')
        }
        return hash(frozenset(key_params.items()))

    def get(self, params):
        key = self._create_cache_key(params)
        self.logger.log(LogLevel.DEBUG, f"Cache get attempt for key: {key}")
        if key in self.cache:
            self.logger.log(LogLevel.SUCCESS, "Cache hit")
            return self.cache[key]
        self.logger.log(LogLevel.DEBUG, "Cache miss")
        return None

    def put(self, params, image):
        key = self._create_cache_key(params)
        self.logger.log(LogLevel.DEBUG, f"Cache put attempt for key: {key}")
        
        # キャッシュが満杯の場合、最古のエントリを削除
        if len(self.cache) >= self.max_size:
            oldest_key = next(iter(self.cache))
            self.logger.log(LogLevel.INFO, f"Cache full, removing oldest entry: {oldest_key}")
            del self.cache[oldest_key]
        
        self.cache[key] = {
            'image': image,
            'timestamp': time.time(),
            'params': params
        }
        self.logger.log(LogLevel.SUCCESS, "Cache entry added")

    def clear(self):
        self.logger.log(LogLevel.INFO, "Clearing cache")
        self.cache.clear()

    def get_stats(self):
        return {
            'size': len(self.cache),
            'max_size': self.max_size,
            'memory_usage': sum(len(v['image']) for v in self.cache.values())
        }

class ColorCache:
    def __init__(self, max_size=100):
        self.cache = {}
        self.max_size = max_size

    def get(self, params, iterations):
        key = hash(frozenset(params.items()))
        if key in self.cache:
            return self.cache[key]
        return None

    def put(self, params, iterations, colored):
        key = hash(frozenset(params.items()))
        if len(self.cache) >= self.max_size:
            oldest_key = next(iter(self.cache))
            del self.cache[oldest_key]
        self.cache[key] = colored

def apply_coloring_algorithm(results, params, logger: DebugLogger):
    """ 着色アルゴリズムを適用（高速スムージング追加）。float32 [0, 255] RGBA 配列を返す """

    cache = FractalCache()
    cached = cache.get(params)
    
    if cached:
        logger.log(LogLevel.INFO, "Using cached image")
        return cached['image']

    # 着色処理
    iterations = results['iterations']
    mask = results['mask'] # 発散しない点のマスク
    z_vals = results['z_vals'] # zの値

    # float32 配列で初期化
    colored = np.zeros((*iterations.shape, 4), dtype=np.float32)
    divergent = iterations > 0 # 発散した点のマスク

    # 中間データを必要最小限に
    if params["diverge_algorithm"] == "高速スムージング":
        smooth_iter = np.zeros_like(iterations, dtype=np.float32)
        fast_smoothing(z_vals, iterations, smooth_iter)
        del z_vals  # これ以降不要なので削除

    # 高速スムージング用の事前計算
    def fast_smoothing(z, iters, out):
        """ 高速スムージングアルゴリズム """
        with np.errstate(divide='ignore', invalid='ignore'):
            abs_z = np.abs(z)
            smooth = np.where(
                abs_z > 2,
                iters - np.log(np.log(abs_z)) / np.log(2),
                iters
            )
            out[...] = smooth  # 既存の配列を更新

    # === 発散する場合の処理 ===
    if np.any(divergent):
        algo = params["diverge_algorithm"]
        logger.log(LogLevel.INFO, f"着色アルゴリズム選択: {algo}")
        # Colormap適用結果は float [0, 1]。これを [0, 255] にスケールする
        cmap_func = plt.cm.get_cmap(params["diverge_colormap"])

        if algo == "反復回数線形マッピング":
            norm = Normalize(1, params["max_iterations"])
            colored[divergent] = cmap_func(norm(iterations[divergent])) * 255.0
        elif algo == "スムージングカラーリング":
            with np.errstate(invalid='ignore', divide='ignore'):
                log_zn = np.log(np.abs(z_vals))
                nu = np.log(log_zn / np.log(2)) / np.log(2)
                smooth_iter = iterations - nu
            invalid_mask = ~np.isfinite(smooth_iter)
            smooth_iter[invalid_mask] = iterations[invalid_mask]
            valid_vals = smooth_iter[divergent & np.isfinite(smooth_iter)]
            vmin = np.min(valid_vals) if len(valid_vals) > 0 else 0
            vmax = np.max(valid_vals) if len(valid_vals) > 0 else params["max_iterations"]
            norm = Normalize(vmin=vmin, vmax=vmax)
            colored[divergent] = cmap_func(norm(smooth_iter[divergent])) * 255.0
        elif algo == "高速スムージング":
            start_time = time.perf_counter()
            smooth_iter = fast_smoothing(z_vals, iterations)
            elapsed = time.perf_counter() - start_time
            logger.log(LogLevel.INFO, f"高速スムージング処理時間: {elapsed:.5f}秒")
            valid_vals = smooth_iter[divergent & np.isfinite(smooth_iter)]
            vmin = np.min(valid_vals) if len(valid_vals) > 0 else 0
            vmax = np.max(valid_vals) if len(valid_vals) > 0 else params["max_iterations"]
            norm = Normalize(vmin=vmin, vmax=vmax)
            colored[divergent] = cmap_func(norm(smooth_iter[divergent])) * 255.0
        elif algo == "指数スムージング":
            with np.errstate(divide='ignore', invalid='ignore'):
                smooth_iter = iterations + 1 - np.log(np.log(np.abs(z_vals))) / np.log(2)
            # 不正な値の処理
            smooth_iter[~np.isfinite(smooth_iter)] = iterations[~np.isfinite(smooth_iter)]
            norm = Normalize(vmin=0, vmax=params["max_iterations"])
            colored[divergent] = cmap_func(norm(smooth_iter[divergent])) * 255.0
        elif algo == "ヒストグラム平坦化法":
            hist, bins = np.histogram(iterations[divergent], bins=params["max_iterations"], density=True)
            cdf = hist.cumsum()
            cdf = cdf / cdf[-1]
            remapped = np.interp(iterations[divergent], bins[:-1], cdf)
            colored[divergent] = cmap_func(remapped) * 255.0
        elif algo == "反復回数対数マッピング":
            iter_log = np.zeros_like(iterations, dtype=float)
            valid_iter = iterations[divergent] > 0 # log(0) を避ける
            iter_log[divergent][valid_iter] = np.log(iterations[divergent][valid_iter]) / np.log(params["max_iterations"])
            colored[divergent] = cmap_func(iter_log[divergent]) * 255.0
        elif algo == "距離カラーリング":
            dist = np.abs(z_vals)
            dist[mask] = 0
            norm = Normalize(0, 10) # この上限値(10)は調整可能
            colored[divergent] = cmap_func(norm(dist[divergent])) * 255.0
        elif algo == "角度カラーリング":
            angles = np.angle(z_vals) / (2 * np.pi) + 0.5
            colored[divergent] = cmap_func(angles[divergent]) * 255.0
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
            colored[divergent] = cmap_func(norm(potential[divergent])) * 255.0
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
            colored[divergent] = cmap_func(norm(trap_dist[divergent])) * 255.0

    non_divergent = ~divergent
    logger.log(LogLevel.DEBUG, f"発散する点の数: {np.sum(divergent)}, 発散しない点の数: {np.sum(non_divergent)}") # 追加: 点の数をログ出力
    if np.any(non_divergent):
        # === 発散しない場合の処理 ===
        non_algo = params["non_diverge_algorithm"]
        if non_algo == "単色":
            # デバッグ用の白 [255, 255, 255, 255] を float で設定
            colored[non_divergent] = [0.0, 0.0, 0.0, 255.0]
        elif non_algo == "グラデーション":
            grad = gradient.compute_gradient(iterations.shape, logger)
            # cmap は [0, 1] を返すので 255.0 を掛ける
            colored[non_divergent] = plt.cm.get_cmap(params["non_diverge_colormap"])(grad[non_divergent]) * 255.0
        elif non_algo == "パラメータ(C)":
            if params["fractal_type"] == "Julia":
                c_val = complex(params["c_real"], params["c_imag"])
                angle = (np.angle(c_val) / (2 * np.pi)) + 0.5
                # 非発散領域全体に同じ色を適用
                color_val = plt.cm.get_cmap(params["non_diverge_colormap"])(angle) * 255.0 # RGBAを[0, 255]範囲に
                colored[non_divergent] = color_val
            else: # Mandelbrotの場合、各点のC（座標値）を使う
                c_real, c_imag = np.real(z_vals[non_divergent]), np.imag(z_vals[non_divergent])
                angle = (np.arctan2(c_imag, c_real) / (2 * np.pi)) + 0.5
                colored[non_divergent] = plt.cm.get_cmap(params["non_diverge_colormap"])(angle) * 255.0
        elif non_algo == "パラメータ(Z)":
            # 最終的なZ値を使う
            z_real, z_imag = np.real(z_vals[non_divergent]), np.imag(z_vals[non_divergent])
            angle = (np.arctan2(z_imag, z_real) / (2 * np.pi)) + 0.5
            colored[non_divergent] = plt.cm.get_cmap(params["non_diverge_colormap"])(angle) * 255.0

    logger.log(LogLevel.DEBUG, f"最終的な colored 配列の dtype: {colored.dtype}, min: {np.min(colored)}, max: {np.max(colored)}") # 追加: 最終的な配列情報をログ出力
    # float32 [0, 255] 配列を返す

    # キャッシュに保存
    cache.put(params, colored)

    return colored
