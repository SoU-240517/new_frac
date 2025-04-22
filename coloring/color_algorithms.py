import matplotlib.pyplot as plt
import numpy as np
import time
from matplotlib.colors import Normalize
from coloring import gradient
from ui.zoom_function.debug_logger import DebugLogger
from ui.zoom_function.enums import LogLevel

# fast_smoothing 関数をモジュールレベルに移動
def fast_smoothing(z, iters, out):
    """ 高速スムージングアルゴリズム """
    with np.errstate(divide='ignore', invalid='ignore'):
        abs_z = np.abs(z)
        # abs_z が 2 より大きい場合のみスムージング計算を行う
        # log(log(abs_z)) は abs_z > 1 で定義されるが、スムージングは通常 abs_z > 2 で適用
        mask_smooth = abs_z > 2
        # np.log(2) は定数なので事前に計算しておく
        log2 = np.log(2)
        # マスクされた部分にのみ計算を適用
        smooth_values = iters[mask_smooth] - np.log(np.log(abs_z[mask_smooth])) / log2
        # 結果を out 配列に書き込む
        out[...] = iters # まず全要素を iters で初期化
        out[mask_smooth] = smooth_values # スムージング計算結果で上書き

"""フラクタルの着色アルゴリズムを実装
- 役割:
    - 着色アルゴリズムを適用
    - 着色アルゴリズムの結果をキャッシュ
"""
def apply_coloring_algorithm(results, params, logger: DebugLogger):
    """ 着色アルゴリズムを適用（高速スムージング追加）。float32 [0, 255] RGBA 配列を返す """
    # FractalCache のインスタンスを作成し、保持
    logger.log(LogLevel.INIT, "FractalCache 初期化開始")
    cache = ColorCache()
    cached = cache.get_cache(params)
    if cached:
        logger.log(LogLevel.INFO, "キャッシュイメージ使用")
        return cached['image']
    # 着色処理
    iterations = results['iterations']
    mask = results['mask'] # 発散しない点のマスク
    z_vals = results['z_vals'] # zの値
    # float32 配列で初期化
    colored = np.zeros((*iterations.shape, 4), dtype=np.float32)
    divergent = iterations > 0 # 発散した点のマスク

    # 不要な事前計算ブロックを削除

    # === 発散する場合の処理 ===
    if np.any(divergent):
        algo = params["diverge_algorithm"]
        logger.log(LogLevel.DEBUG, f"着色アルゴリズム選択: {algo}")
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
            # smooth_iter 配列を作成
            smooth_iter = np.zeros_like(iterations, dtype=np.float32)
            # モジュールレベルの fast_smoothing を呼び出し、smooth_iter を更新
            fast_smoothing(z_vals, iterations, smooth_iter)
            elapsed = time.perf_counter() - start_time
            logger.log(LogLevel.INFO, f"高速スムージング処理時間: {elapsed:.5f}秒")
            # smooth_iter を使用して正規化と着色
            valid_vals = smooth_iter[divergent & np.isfinite(smooth_iter)]
            vmin = np.min(valid_vals) if len(valid_vals) > 0 else 0
            vmax = np.max(valid_vals) if len(valid_vals) > 0 else params["max_iterations"]
            # vmin と vmax が同じ場合、Normalize はエラーを起こす可能性があるため、微小な差をつける
            if vmin == vmax:
                vmax += 1e-9
            norm = Normalize(vmin=vmin, vmax=vmax)
            # divergent マスクを適用して着色
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
            valid_iter_mask = divergent & (iterations > 0) # log(0) を避けるためのマスク
            iter_log[valid_iter_mask] = np.log(iterations[valid_iter_mask]) / np.log(params["max_iterations"])
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
    logger.log(LogLevel.DEBUG, f"発散する点の数: {np.sum(divergent)}, 発散しない点の数: {np.sum(non_divergent)}")
    if np.any(non_divergent):
        # === 発散しない場合の処理 ===
        non_algo = params["non_diverge_algorithm"]
        if non_algo == "単色":
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
                # タプルを NumPy 配列に変換してから乗算する
                color_val_normalized = plt.cm.get_cmap(params["non_diverge_colormap"])(angle) # [0, 1] のタプルを取得
                color_val = np.array(color_val_normalized) * 255.0 # NumPy 配列に変換して [0, 255] にスケール
                colored[non_divergent] = color_val
            else: # Mandelbrotの場合、各点のC（座標値）を使う
                logger.log(LogLevel.WARNING, "Mandelbrotの非発散部パラメータ(C)着色は現在z_valsを使用しており、意図通りでない可能性があります。")
                c_real, c_imag = np.real(z_vals[non_divergent]), np.imag(z_vals[non_divergent])
                angle = (np.arctan2(c_imag, c_real) / (2 * np.pi)) + 0.5
                colored[non_divergent] = plt.cm.get_cmap(params["non_diverge_colormap"])(angle) * 255.0
        elif non_algo == "パラメータ(Z)":
            # 最終的なZ値を使う
            z_real, z_imag = np.real(z_vals[non_divergent]), np.imag(z_vals[non_divergent])
            angle = (np.arctan2(z_imag, z_real) / (2 * np.pi)) + 0.5
            colored[non_divergent] = plt.cm.get_cmap(params["non_diverge_colormap"])(angle) * 255.0
    logger.log(LogLevel.DEBUG, f"最終的な colored 配列の dtype: {colored.dtype}, min: {np.min(colored)}, max: {np.max(colored)}")
    # float32 [0, 255] 配列を返す
    # キャッシュに保存
    cache.put_cache(params, colored)
    return colored

class ColorCache:
    """フラクタル画像をキャッシュするクラス
    - 役割:
        - 着色済み画像（RGBA配列）のキャッシュ
        - FractalCache は別に存在する（render.py）
    """
    def __init__(self, max_size=100, logger=None):
        """カラーキャッシュのコンストラクタ

        Args:
            max_size (int, optional): キャッシュの最大サイズ. Defaults to 100.
        """
        self.cache = {}
        self.max_size = max_size
        self.logger = logger or DebugLogger()  # logger が渡されない場合は新規作成
        self.logger.log(LogLevel.INIT, "DebugLogger 初期化完了（になっちゃう）")

    def _create_cache_key(self, params):
        """キャッシュキーを生成するためのヘルパーメソッド

        Args:
            params (dict): 計算パラメータ
        """
        # キャッシュキーは、パラメータの組み合わせから生成される
        # より多くのパラメータを含めて、キャッシュの衝突を防ぐ
        key_params = {
            'center_x': params.get('center_x'),
            'center_y': params.get('center_y'),
            'width': params.get('width'),
            'rotation': params.get('rotation'),
            'max_iterations': params.get('max_iterations'),
            'fractal_type': params.get('fractal_type'),
            'c_real': params.get('c_real'),
            'c_imag': params.get('c_imag'),
            'z_real': params.get('z_real'),
            'z_imag': params.get('z_imag'),
            'diverge_algorithm': params.get('diverge_algorithm'),
            'diverge_colormap': params.get('diverge_colormap'),
            'non_diverge_algorithm': params.get('non_diverge_algorithm'),
            'non_diverge_colormap': params.get('non_diverge_colormap'),
            # 解像度に関わるパラメータもキーに含めるべき
            # 'resolution': _calculate_dynamic_resolution(params.get("width", 4.0)) # render.pyから持ってくる必要あり
            # 'samples_per_pixel': ... # render.pyから持ってくる必要あり
        }
        # None 値を除外してハッシュ化
        frozen_items = frozenset(item for item in key_params.items() if item[1] is not None)
        return hash(frozen_items)


    def get_cache(self, params):
        """キャッシュから画像を取得

        Args:
            params (dict): 計算パラメータ
        """
        key = self._create_cache_key(params)
        self.logger.log(LogLevel.CALL, f"キャッシュキー取得試行: {key}")
        if key in self.cache:
            self.logger.log(LogLevel.SUCCESS, "キャッシュヒット")
            return self.cache[key]['image'] # 画像のみ返すように修正
        self.logger.log(LogLevel.INFO, "キャッシュミス")
        return None

    def put_cache(self, params, image):
        """キャッシュに画像を追加

        Args:
            params (dict): 計算パラメータ
            image (np.ndarray): 着色済み画像
        """
        key = self._create_cache_key(params)
        self.logger.log(LogLevel.DEBUG, f"キャッシュキー書込み試行: {key}")
        # キャッシュが満杯の場合、最古のエントリを削除 (LRUではない単純なFIFO)
        if len(self.cache) >= self.max_size:
            oldest_key = next(iter(self.cache))
            self.logger.log(LogLevel.INFO, f"キャッシュフル（最古エントリ削除）：{oldest_key}")
            del self.cache[oldest_key]
        self.cache[key] = {
            'image': image.copy(), # 念のためコピーを保存
            'timestamp': time.time(),
            # 'params': params # デバッグ用には有用だが、メモリを消費する
        }
        self.logger.log(LogLevel.SUCCESS, "キャッシュエントリ追加")

    def clear_cache(self):
        """キャッシュをクリア"""
        self.logger.log(LogLevel.INFO, "キャッシュクリア")
        self.cache.clear()

    def get_cache_stats(self):
        """キャッシュの統計情報を取得

        Returns:
            dict: キャッシュの統計情報
        """
        # メモリ使用量の計算をより正確に
        memory_usage_bytes = sum(v['image'].nbytes for v in self.cache.values())
        return {
            'size': len(self.cache),
            'max_size': self.max_size,
            'memory_usage_bytes': memory_usage_bytes
        }
