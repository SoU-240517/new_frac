import numpy as np
from coloring import color_algorithms
from fractal.fractal_types import julia, mandelbrot
from ui.zoom_function.debug_logger import DebugLogger
from ui.zoom_function.enums import LogLevel # LogLevel をインポート

def render_fractal(params, logger: DebugLogger):
    """ 指定されたパラメータに基づいてフラクタルを描画 """
    logger.log(LogLevel.INFO, "Rendering fractal with parameters")

    resolution = 500
    # ズーム情報があればそれを使用、なければ初期値
    center_x = params.get("center_x", 0.0)
    center_y = params.get("center_y", 0.0)
    width = params.get("width", 4.0)
    height = params.get("height", 4.0)
    rotation = params.get("rotation", 0.0)

    # キャンバスのアスペクト比を維持するために、高さを幅に合わせる
    aspect_ratio = resolution / resolution  # 縦横比（通常は1）
    height = width / aspect_ratio

    x = np.linspace(-width/2, width/2, resolution)
    y = np.linspace(-height/2, height/2, resolution)
    X, Y = np.meshgrid(x, y)

    # グリッドをズーム中心にシフト
    X = X + center_x
    Y = Y + center_y
    Z = X + 1j * Y

    # フラクタルの種類に応じた計算
    if params["fractal_type"] == "Julia":
        C = complex(params["c_real"], params["c_imag"])
        # compute_julia に logger を渡す
        results = julia.compute_julia(Z, C, params["max_iterations"], logger)
    else:
        Z0 = complex(params["z_real"], params["z_imag"])
        # compute_mandelbrot に logger を渡す
        results = mandelbrot.compute_mandelbrot(Z, Z0, params["max_iterations"], logger)

    # 着色アルゴリズムの適用
    # apply_coloring_algorithm に logger を渡す
    colored = color_algorithms.apply_coloring_algorithm(results, params, logger)
    return colored
