import numpy as np
import time
# from coloring import color_algorithms
from coloring import manager
from fractal.fractal_types import julia, mandelbrot
from ui.zoom_function.debug_logger import DebugLogger
from ui.zoom_function.enums import LogLevel

"""フラクタル画像生成エンジン
このモジュールはフラクタル画像の生成を担当する
主な機能：
1. 動的解像度制御
   - ズームレベルに応じて最適な解像度を自動調整
   - パフォーマンスと品質のバランスを取る
2. フラクタル計算
   - Mandelbrot集合とJulia集合の生成
   - 高精度な複素数計算
3. レンダリング最適化
   - スーパーサンプリングによる高品質画像生成
   - パフォーマンス最適化された計算
"""

def _calculate_dynamic_resolution(width, base_res=600, min_res=400, max_res=1200):
    """ズームレベルに応じて描画解像度を動的に計算
    - 解像度は対数スケールで調整
    - ズームインするほど高解像度になる
    Args:
        width (float): 描画範囲の幅
            - ズームレベルの指標
            - 値が小さいほどズームイン
        base_res (int, optional): 基準解像度. Defaults to 600.
        min_res (int, optional): 最小解像度. Defaults to 400.
        max_res (int, optional): 最大解像度. Defaults to 1200.
    Returns:
        int: 計算された描画解像度（ピクセル数）
            - 実際の描画時はこの解像度にサンプリング倍率をかける
            - 最終的な画像はこの解像度に縮小される
    """
    # 対数スケールでズームファクターを計算
    # width=4.0 を基準（ズームなし）
    # width が小さい（ズームイン）ほど zoom_factor は大きくなる
    zoom_factor = np.log(5.0 / width + 1.0) # 調整可能なマジックナンバー (5.0)

    # zoom_factorにbase_resを掛けて基本解像度を決定
    resolution = int(base_res * zoom_factor)

    # 最小解像度と最大解像度でクリップ
    return np.clip(resolution, min_res, max_res)

def _create_fractal_grid(params: dict, super_resolution_x: int, super_resolution_y: int, logger: DebugLogger) -> np.ndarray:
    """フラクタル計算用の複素数グリッドを生成
    Args:
        params (dict): フラクタルのパラメータ
            - center_x: 中心X座標
            - center_y: 中心Y座標
            - width:  描画範囲の幅
        super_resolution_x (int): 水平方向の解像度
        super_resolution_y (int): 垂直方向の解像度
        logger (DebugLogger): デバッグログ出力用
    Returns:
        np.ndarray: 複素数グリッド
            - shape: (super_resolution_y, super_resolution_x)
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
        logger.log(LogLevel.DEBUG, f"回転適用: {rotation_deg:.2f} 度")
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
    """フラクタル計算を実行
    Args:
        Z (np.ndarray): 複素数グリッド
        params (dict): フラクタルのパラメータ
            - fractal_type: フラクタルの種類 (Mandelbrot または Julia)
            - c_real:       Julia集合のcの実部
            - c_imag:       Julia集合のcの虚部
            - z_real:       Mandelbrot集合の初期値の実部
            - z_imag:       Mandelbrot集合の初期値の虚部
            - max_iterations: 最大反復回数
        logger (DebugLogger): デバッグログ出力用
    Returns:
        dict: 計算結果
            - iterations: 各点の反復回数
            - mask:       フラクタル集合の内側かどうかのマスク
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
    """高解像度画像をダウンサンプリングしてアンチエイリアシング
    Args:
        high_res_image (np.ndarray): 高解像度画像
        resolution (int): 目標解像度
        samples_per_pixel (int): 1ピクセルあたりのサンプル数
        logger (DebugLogger): デバッグログ出力用
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
    """フラクタル画像を生成
    Args:
        params (dict): フラクタルのパラメータ
            - fractal_type:   フラクタルの種類 (Mandelbrot または Julia)
            - c_real:         Julia集合のcの実部
            - c_imag:         Julia集合のcの虚部
            - z_real:         Mandelbrot集合の初期値の実部
            - z_imag:         Mandelbrot集合の初期値の虚部
            - max_iterations: 最大反復回数
            - center_x:       中心X座標
            - center_y:       中心Y座標
            - width:          描画範囲の幅
            - rotation:       回転角度
        logger (DebugLogger): デバッグログ出力用
        cache (FractalCache): キャッシュ（未使用）
    Returns:
        np.ndarray: RGBA形式のフラクタル画像 (uint8 [0, 255])
    """
    render_mode = params.get("render_mode", "quick")  # デフォルトは簡易モード

    # 動的解像度計算
    if render_mode == "quick":
        resolution = _calculate_dynamic_resolution(params.get("width", 4.0)) // 2  # 解像度を半分に
        samples_per_pixel = 1  # アンチエイリアシングなし
    else:
        resolution = _calculate_dynamic_resolution(params.get("width", 4.0))
        zoom_level = 4.0 / params.get("width", 4.0)
        samples_per_pixel = 2 if zoom_level < 0.8 else 4

    logger.log(LogLevel.SUCCESS, f"描画モード: {render_mode}, 解像度: {resolution}x{resolution}, サンプル数: {samples_per_pixel}")

    # アンチエイリアシング設定
    zoom_level = 4.0 / params.get("width", 4.0)
    # アンチエイリアシング設定: 全体表示(widthが大きい)でも一定のサンプル数を保つ
    # ズームレベルが0.8より小さい場合（ある程度ズームアウトしている場合）も samples_per_pixel=4 とする
    samples_per_pixel = 2 if zoom_level < 0.8 else 4
    logger.log(LogLevel.SUCCESS, f"アンチエイリアシング設定完了: samples_per_pixel={samples_per_pixel}")

    # 高解像度グリッドサイズ
    super_resolution_x = resolution * samples_per_pixel
    super_resolution_y = resolution * samples_per_pixel

    # グリッド作成
    Z = _create_fractal_grid(params, super_resolution_x, super_resolution_y, logger)
    logger.log(LogLevel.SUCCESS, "グリッドの作成と変換完了")

    # フラクタル計算
    results = _compute_fractal(Z, params, logger)

    # 着色処理
    colored_high_res = manager.apply_coloring_algorithm(results, params, logger)

    # ダウンサンプリング
    colored = colored_high_res if samples_per_pixel == 1 else \
        _downsample_image(colored_high_res, resolution, samples_per_pixel, logger)

    # 最終的な結果を uint8 に変換
    colored = np.clip(colored, 0, 255).astype(np.uint8)
    logger.log(LogLevel.DEBUG, f"最終的な render_fractal 出力 dtype: {colored.dtype}, shape: {colored.shape}")

    return colored
