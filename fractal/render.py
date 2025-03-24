import numpy as np
from fractal.fractal_types import julia, mandelbrot
from coloring import color_algorithms

def render_fractal(params):
    print("====== フラクタル描画開始:（def render_fractal）")  # ← debug print★
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
        results = julia.compute_julia(Z, C, params["max_iterations"])
    else:
        Z0 = complex(params["z_real"], params["z_imag"])
        results = mandelbrot.compute_mandelbrot(Z, Z0, params["max_iterations"])

    # 着色アルゴリズムの適用
    colored = color_algorithms.apply_coloring_algorithm(results, params)
    return colored
