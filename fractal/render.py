import numpy as np
from coloring import color_algorithms
from fractal.fractal_types import julia, mandelbrot
from ui.zoom_function.debug_logger import DebugLogger
from ui.zoom_function.enums import LogLevel

def render_fractal(params, logger: DebugLogger) -> np.ndarray:
    """ 設定されたパラメータでフラクタルを描画（動的解像度版） """
    # 動的解像度計算
    resolution = calculate_dynamic_resolution(params.get("width", 4.0))
    # アンチエイリアシング設定（ズームレベルに応じてサンプル数を調整）
    zoom_level = 4.0 / params.get("width", 4.0)
    samples_per_pixel = 2 if zoom_level < 1.0 else 4  # ズームアウト時はサンプル数減らす
    super_resolution = resolution * samples_per_pixel
    center_x = params.get("center_x", 0.0)
    center_y = params.get("center_y", 0.0)
    width = params.get("width", 4.0)
    # height は width と aspect_ratio から計算されるため、params から取得しない
    rotation_deg = params.get("rotation", 0.0)
    # キャンバスのアスペクト比を維持するために、高さを幅に合わせる
    # 注意: ここでの aspect_ratio は描画解像度に基づくもので、
    # MainWindow での補正とは異なる可能性がある。一貫性を保つことが重要。
    # ここでは正方形解像度を仮定。
    aspect_ratio = 1.0  # 正方形を維持
    height = width / aspect_ratio
    # 回転前のグリッド座標、かつ高解像度でグリッドを生成
    super_resolution = resolution * samples_per_pixel
    x = np.linspace(-width/2, width/2, super_resolution)
    y = np.linspace(-height/2, height/2, super_resolution)
    X, Y = np.meshgrid(x, y)
    # 複素数グリッドを作成 (まだ中心シフト・回転は適用しない)
    Z_unrotated_centered_origin = X + 1j * Y
    # 回転を適用
    if rotation_deg != 0:
        logger.log(LogLevel.DEBUG, f"回転適用: {rotation_deg} 度")
        rotation_rad = np.radians(rotation_deg) # 度からラジアンに変換
        rotation_operator = np.exp(1j * rotation_rad) # 回転演算子 (複素数)
        Z_rotated_centered_origin = Z_unrotated_centered_origin * rotation_operator # グリッドを回転
    else:
        Z_rotated_centered_origin = Z_unrotated_centered_origin # 回転がない場合はそのまま
    # 回転後のグリッドを中心座標にシフト
    Z = Z_rotated_centered_origin + complex(center_x, center_y)
    logger.log(LogLevel.DEBUG, "グリッドの作成と変換完了",
               context={"中心_x": center_x, "中心_y": center_y, "w": width, "h": height, "角度": rotation_deg})
    # フラクタルの種類に応じた計算（高解像度版）
    if params["fractal_type"] == "Julia":
        C = complex(params["c_real"], params["c_imag"])
        logger.log(LogLevel.DEBUG, "ジュリア集合の計算開始")
        # 回転・シフト後のグリッド Z を使用
        results = julia.compute_julia(Z, complex(params["c_real"], params["c_imag"]), params["max_iterations"], logger)
    else: # Mandelbrot
        Z0 = complex(params["z_real"], params["z_imag"])
        logger.log(LogLevel.DEBUG, "マンデルブロ集合の計算開始")
        # 回転・シフト後のグリッド Z を使用
        results = mandelbrot.compute_mandelbrot(Z, complex(params["z_real"], params["z_imag"]), params["max_iterations"], logger)
    # 着色アルゴリズムの適用
    logger.log(LogLevel.DEBUG, "着色アルゴリズムの適用開始")
    # 解像度をダウンサンプリング（アンチエイリアシング効果）
    colored_high_res = color_algorithms.apply_coloring_algorithm(results, params, logger)
    # ダウンサンプリング（サンプル数が1の場合はスキップ）
    if samples_per_pixel > 1:
        colored = colored_high_res.reshape((resolution, samples_per_pixel, resolution, samples_per_pixel, -1)).mean(axis=(1, 3))
    else:
        colored = colored_high_res
    return colored

def calculate_dynamic_resolution(width, base_res=600, min_res=300, max_res=1200):
    """ズームレベルに応じて解像度を動的に計算"""
    zoom_factor = np.log(5.0 / width + 1.0)  # より滑らかな解像度変化
    resolution = int(base_res * zoom_factor)
    return np.clip(resolution, min_res, max_res)
