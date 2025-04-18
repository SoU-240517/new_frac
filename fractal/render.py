import numpy as np
import time
from coloring import color_algorithms
from fractal.fractal_types import julia, mandelbrot
from ui.zoom_function.debug_logger import DebugLogger
from ui.zoom_function.enums import LogLevel

class FractalCache:
    def __init__(self, max_size=100):
        self.cache = {}
        self.max_size = max_size

    def get(self, params):
        key = hash(frozenset(params.items()))
        return self.cache.get(key)

    def put(self, params, result):
        key = hash(frozenset(params.items()))
        if len(self.cache) >= self.max_size:
            oldest_key = next(iter(self.cache))
            del self.cache[oldest_key]
        self.cache[key] = result

def render_fractal(params, logger: DebugLogger, cache=None) -> np.ndarray:
    """ 設定されたパラメータでフラクタルを描画（動的解像度版） """
    # キャッシュから取得
    if cache:
        cached_result = cache.get(params)
        if cached_result is not None:
            logger.log(LogLevel.SUCCESS, "キャッシュヒット")
            return cached_result
    # 動的解像度計算
    resolution = calculate_dynamic_resolution(params.get("width", 4.0))
    logger.log(LogLevel.SUCCESS, f"動的解像度計算完了: {resolution}x{resolution} (width={params.get('width', 4.0):.2f})")
    zoom_level = 4.0 / params.get("width", 4.0) # アンチエイリアシング設定（ズームレベルに応じてサンプル数を調整）
    samples_per_pixel = 2 if zoom_level < 1.0 else 4 # ズームアウト時はサンプル数減らす
    logger.log(LogLevel.DEBUG, f"アンチエイリアシング設定：samples_per_pixel={samples_per_pixel}")
    super_resolution = resolution * samples_per_pixel
    center_x = params.get("center_x", 0.0)
    center_y = params.get("center_y", 0.0)
    width = params.get("width", 4.0)
    # height は params から取得しない（width と aspect_ratio から計算する）
    rotation_deg = params.get("rotation", 0.0)
    aspect_ratio = 1.0  # 正方形を維持
    height = width / aspect_ratio
    # 回転前のグリッド座標、かつ高解像度でグリッドを生成
    super_resolution = resolution * samples_per_pixel
    # データ型の最適化
    dtype = np.float16 if params.get("width", 4.0) > 1.0 else np.float32
    x = np.linspace(-width/2, width/2, super_resolution, dtype=dtype)
    y = np.linspace(-height/2, height/2, super_resolution, dtype=dtype)
    X, Y = np.meshgrid(x, y, sparse=True)  # sparse=Trueでメモリ使用量を削減
    # 複素数グリッドを作成 (まだ中心シフト・回転は適用しない)
    Z_unrotated_centered_origin = X + 1j * Y
    Z_unrotated_centered_origin = Z_unrotated_centered_origin.astype(np.complex64)
    if rotation_deg != 0: # 回転を適用
        logger.log(LogLevel.DEBUG, f"回転適用: {rotation_deg} 度")
        rotation_rad = np.radians(rotation_deg) # ラジアンに変換
        rotation_operator = np.exp(1j * rotation_rad) # 回転演算子 (複素数)
        Z_rotated_centered_origin = Z_unrotated_centered_origin * rotation_operator # グリッドを回転
    else:
        Z_rotated_centered_origin = Z_unrotated_centered_origin # 回転がない場合はそのまま
    # 回転後のグリッドを中心座標にシフト
    Z = Z_rotated_centered_origin + complex(center_x, center_y)
    logger.log(LogLevel.SUCCESS, "グリッドの作成と変換完了",
               context={"中心_x": center_x, "中心_y": center_y, "w": width, "h": height, "角度": rotation_deg})
    # フラクタルの種類に応じた計算（高解像度版）
    if params["fractal_type"] == "Julia":
        C = complex(params["c_real"], params["c_imag"])
        # 回転・シフト後のグリッド Z を使用
        start_time = time.perf_counter()
        results = julia.compute_julia(Z, complex(params["c_real"], params["c_imag"]), params["max_iterations"], logger)
        results['iterations'] = results['iterations'].astype(np.uint16)  # イテレーション数は16bit整数で十分
        elapsed = time.perf_counter() - start_time
        logger.log(LogLevel.INFO, f"ジュリア集合計算時間：{elapsed:.3f}秒")
    else: # Mandelbrot
        Z0 = complex(params["z_real"], params["z_imag"])
        # 回転・シフト後のグリッド Z を使用
        start_time = time.perf_counter()
        results = mandelbrot.compute_mandelbrot(Z, complex(params["z_real"], params["z_imag"]), params["max_iterations"], logger)
        results['iterations'] = results['iterations'].astype(np.uint16)  # イテレーション数は16bit整数で十分
        elapsed = time.perf_counter() - start_time
        logger.log(LogLevel.INFO, f"マンデルブロ集合計算時間：{elapsed:.3f}秒")
    # 着色処理 (float32 [0, 255] RGBA 配列が返される)
    colored_high_res = color_algorithms.apply_coloring_algorithm(results, params, logger)
    # ダウンサンプリング（アンチエイリアシング効果）
    if samples_per_pixel > 1: # ダウンサンプリング（サンプル数が1の場合はスキップ）
        logger.log(LogLevel.DEBUG, "ダウンサンプリング実行")
        # .mean() は float を返す (入力も float なので型は維持される)
        colored = colored_high_res.reshape((resolution, samples_per_pixel, resolution, samples_per_pixel, -1)).mean(axis=(1, 3))
    else:
        # ダウンサンプリングしない場合は、そのまま float 配列を使用
        colored = colored_high_res
    # 最終的な結果を uint8 [0, 255] に変換
    # np.clip で範囲外の値が発生しないように念のためクリップ
    colored = np.clip(colored, 0, 255).astype(np.uint8)
    logger.log(LogLevel.DEBUG, f"最終的な render_fractal 出力 dtype: {colored.dtype}, shape: {colored.shape}")
    # キャッシュに保存 (uint8 の最終結果を保存)
    if cache:
        cache.put(params, colored)
    # uint8 [0, 255] 配列を返す
    return colored

def calculate_dynamic_resolution(width, base_res=600, min_res=300, max_res=1200):
    """ズームレベルに応じて解像度を動的に計算"""
    zoom_factor = np.log(5.0 / width + 1.0)
    resolution = int(base_res * zoom_factor)
    return np.clip(resolution, min_res, max_res)
