import numpy as np
import time
from coloring import color_algorithms
from fractal.fractal_types import julia, mandelbrot
from ui.zoom_function.debug_logger import DebugLogger
from ui.zoom_function.enums import LogLevel

"""フラクタル画像を生成する主要ロジック部分
- 役割:
    - 設定されたパラメータでフラクタルを描画
"""
def _calculate_dynamic_resolution(width, base_res=600, min_res=400, max_res=1200):
    """ズームレベルに応じて描画解像度を動的に計算
    Args:
        width (float): ウィンドウの幅（データ座標系）。ズームレベルの指標として使用。
                       widthが小さいほどズームインしており、高解像度が必要。
        base_res (int, optional): 基準となる解像度. Defaults to 600.
        min_res (int, optional): 最小解像度. Defaults to 300.
        max_res (int, optional): 最大解像度. Defaults to 1200.
    Returns:
        int: 計算された描画解像度（一辺のピクセル数）。実際にはこれにsamples_per_pixelをかけた高解像度で計算し、後で縮小します。
    """
    # 対数スケールでズームファクターを計算
    # width=4.0 を基準（ズームなし）とすると log(5) あたり
    # width が小さくなる（ズームイン）ほど zoom_factor は大きくなりる
    # +1.0 は width が非常に小さい場合に log(ほぼ0) にならないようにするため
    zoom_factor = np.log(5.0 / width + 1.0) # 調整可能なマジックナンバー (5.0)

    # zoom_factorにbase_resを掛けて基本解像度を決定
    resolution = int(base_res * zoom_factor)

    # 最小解像度と最大解像度でクリップ
    return np.clip(resolution, min_res, max_res)

def _create_fractal_grid(params: dict, super_resolution_x: int, super_resolution_y: int, logger: DebugLogger) -> np.ndarray:
    """フラクタルの計算用グリッドを作成
    Args:
        params (dict): パラメータ辞書
        super_resolution_x (int): 水平方向の解像度
        super_resolution_y (int): 垂直方向の解像度
        logger (DebugLogger): ログ出力クラス
    Returns:
        np.ndarray: 複素数グリッド
    """
    center_x = params.get("center_x", 0.0)
    center_y = params.get("center_y", 0.0)
    width = params.get("width", 4.0)
    height = width * (9 / 16)

    dtype = np.float16 if width > 1.0 else np.float32
    x = np.linspace(center_x - width/2, center_x + width/2, super_resolution_x, dtype=dtype)
    y = np.linspace(center_y - height/2, center_y + height/2, super_resolution_y, dtype=dtype)

    X, Y = np.meshgrid(x, y)
    Z = X + 1j * Y
    Z = Z.astype(np.complex64)

    rotation_deg = params.get("rotation", 0.0)
    if rotation_deg != 0:
        logger.log(LogLevel.DEBUG, f"回転適用: {rotation_deg} 度")
        rotation_rad = np.radians(rotation_deg)
        Z -= complex(center_x, center_y)
        rotation_operator = np.exp(1j * rotation_rad)
        Z *= rotation_operator
        Z += complex(center_x, center_y)
        logger.log(LogLevel.SUCCESS, "グリッド回転適用完了")

    return Z

def _compute_fractal(
    Z: np.ndarray,
    params: dict,
    logger: DebugLogger
) -> dict:
    """フラクタルを計算
    Args:
        Z (np.ndarray): 複素数グリッド
        params (dict): パラメータ辞書
        logger (DebugLogger): ログ出力クラス
    Returns:
        dict: 計算結果（iterations, mask, z_vals）
    """
    start_time = time.perf_counter()

    if params["fractal_type"] == "Julia":
        c_val = complex(params.get("c_real", -0.7), params.get("c_imag", 0.27015))
        results = julia.compute_julia(Z, c_val, params.get("max_iterations", 100), logger)
        logger.log(LogLevel.INFO, f"ジュリア集合計算時間：{time.perf_counter() - start_time:.3f}秒")
    else:  # Mandelbrot
        z0_val = complex(params.get("z_real", 0.0), params.get("z_imag", 0.0))
        results = mandelbrot.compute_mandelbrot(Z, z0_val, params.get("max_iterations", 100), logger)
        logger.log(LogLevel.INFO, f"マンデルブロ集合計算時間：{time.perf_counter() - start_time:.3f}秒")

    results['iterations'] = results['iterations'].astype(np.uint16)
    return results

def _downsample_image(
    high_res_image: np.ndarray,
    resolution: int,
    samples_per_pixel: int,
    logger: DebugLogger
) -> np.ndarray:
    """高解像度画像をダウンサンプリング
    Args:
        high_res_image (np.ndarray): 高解像度画像
        resolution (int): 目標解像度
        samples_per_pixel (int): 1ピクセルあたりのサンプル数
        logger (DebugLogger): ログ出力クラス
    Returns:
        np.ndarray: ダウンサンプリングされた画像
    """
    try:
        expected_shape = (resolution * samples_per_pixel, resolution * samples_per_pixel, 4)
        if high_res_image.shape == expected_shape:
            downsampled = high_res_image.reshape(
                (resolution, samples_per_pixel, resolution, samples_per_pixel, 4)
            ).mean(axis=(1, 3))
        else:
            logger.log(LogLevel.ERROR, f"ダウンサンプリングエラー: 形状が不正です。期待値: {expected_shape}, 実際: {high_res_image.shape}")
            downsampled = np.full((resolution, resolution, 4), [255, 0, 0, 255], dtype=np.float32)
    except ValueError as e:
        logger.log(LogLevel.ERROR, f"ダウンサンプリング中のValueError: {e}")
        downsampled = np.full((resolution, resolution, 4), [255, 0, 0, 255], dtype=np.float32)

    return downsampled

def render_fractal(params: dict, logger: DebugLogger, cache=None) -> np.ndarray:
    """フラクタルを描画
    Args:
        params (dict): パラメータ辞書
        logger (DebugLogger): ログ出力クラス
        cache (FractalCache): キャッシュクラス
    Returns:
        np.ndarray: フラクタル画像 (uint8 [0, 255] RGBA 配列)
    """
    # 動的解像度計算
    resolution = _calculate_dynamic_resolution(params.get("width", 4.0))
    logger.log(LogLevel.SUCCESS, f"動的解像度計算完了: {resolution}x{resolution}")

    # アンチエイリアシング設定
    zoom_level = 4.0 / params.get("width", 4.0)
    # アンチエイリアシング設定: 全体表示(widthが大きい)でも一定のサンプル数を保つ
    # ズームレベルが0.8より小さい場合（ある程度ズームアウトしている場合）も samples_per_pixel=4 とする
    samples_per_pixel = 2 if zoom_level < 0.8 else 4
    logger.log(LogLevel.SUCCESS, f"アンチエイリアシング設定完了：samples_per_pixel={samples_per_pixel}")

    # 高解像度グリッドサイズ
    super_resolution_x = resolution * samples_per_pixel
    super_resolution_y = resolution * samples_per_pixel

    # グリッド作成
    Z = _create_fractal_grid(params, super_resolution_x, super_resolution_y, logger)
    logger.log(LogLevel.SUCCESS, "グリッドの作成と変換完了")

    # フラクタル計算
    results = _compute_fractal(Z, params, logger)

    # 着色処理
    colored_high_res = color_algorithms.apply_coloring_algorithm(results, params, logger)

    # ダウンサンプリング
    colored = colored_high_res if samples_per_pixel == 1 else \
        _downsample_image(colored_high_res, resolution, samples_per_pixel, logger)

    # 最終的な結果を uint8 に変換
    colored = np.clip(colored, 0, 255).astype(np.uint8)
    logger.log(LogLevel.DEBUG, f"最終的な render_fractal 出力 dtype: {colored.dtype}, shape: {colored.shape}")

    return colored
