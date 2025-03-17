import numpy as np
from fractal.fractal_types import julia, mandelbrot
from coloring import color_algorithms

def render_fractal(params):
    resolution = 500
    # ズーム情報があればそれを使用、なければ初期値
    center_x = params.get("center_x", 0.0)
    center_y = params.get("center_y", 0.0)
    width = params.get("width", 4.0)
    height = params.get("height", 4.0)
    rotation = params.get("rotation", 0.0)

    # ローカル座標系でグリッド作成
    x = np.linspace(-width/2, width/2, resolution)
    y = np.linspace(-height/2, height/2, resolution)
    X, Y = np.meshgrid(x, y)

    # 回転があれば回転変換
    if rotation != 0.0:
        cos_theta = np.cos(rotation)
        sin_theta = np.sin(rotation)
        X_rot = X * cos_theta - Y * sin_theta
        Y_rot = X * sin_theta + Y * cos_theta
        X, Y = X_rot, Y_rot

    # グリッドをズーム中心にシフト
    X = X + center_x
    Y = Y + center_y
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
