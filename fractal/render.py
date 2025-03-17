import numpy as np
from fractal.fractal_types import julia, mandelbrot
from coloring import color_algorithms

def render_fractal(params):
    # 座標グリッドの作成（-2〜2の範囲、解像度500）
    x_min, x_max = -2.0, 2.0
    y_min, y_max = -2.0, 2.0
    resolution = 500
    x = np.linspace(x_min, x_max, resolution)
    y = np.linspace(y_min, y_max, resolution)
    X, Y = np.meshgrid(x, y)
    Z = X + 1j * Y

    # フラクタルの種類に応じた計算
    if params["fractal_type"] == "Julia":
        C = complex(params["c_real"], params["c_imag"])
        results = julia.compute_julia(Z, C, params["max_iterations"])
    else:
        Z0 = complex(params["z_real"], params["z_imag"])
        results = mandelbrot.compute_mandelbrot(Z, Z0, params["max_iterations"])

    # 着色アルゴリズムの適用
    colored = color_algorithms.apply_coloring_algorithm(results, params)
    return colored
