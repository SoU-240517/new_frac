# main.py

import tkinter as tk
from tkinter import ttk
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from matplotlib import cm
import matplotlib.colors as mcolors
import time
import math

class FractalGenerator:
    def __init__(self, root):
        self.root = root
        self.root.title("フラクタル描画アプリケーション")
        self.root.geometry("1200x800")

        # メインフレームを作成（左右に分割）
        self.main_frame = ttk.PanedWindow(root, orient=tk.HORIZONTAL)
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        # 左側のキャンバスフレーム
        self.canvas_frame = ttk.Frame(self.main_frame)
        self.main_frame.add(self.canvas_frame, weight=3)

        # 右側の操作パネルフレーム
        self.control_frame = ttk.Frame(self.main_frame)
        self.main_frame.add(self.control_frame, weight=1)

        # Matplotlibのカラーマップ一覧を取得
        self.colormaps = sorted([m for m in plt.colormaps() if not m.endswith('_r')])

        # フラクタルパラメータの初期化
        self.fractal_type = "Julia"  # デフォルトはJuliaセット
        self.max_iterations = 100
        self.z_real = 0.0
        self.z_imag = 0.0
        self.c_real = -0.7
        self.c_imag = 0.27015
        self.diverge_algorithm = "反復回数線形マッピング"
        self.diverge_colormap = "viridis"
        self.non_diverge_algorithm = "単色"
        self.non_diverge_colormap = "plasma"

        # 発散部の着色アルゴリズム一覧
        self.diverge_algorithms = [
            "反復回数線形マッピング",
            "スムージングカラーリング",
            "ヒストグラム平坦化法",
            "反復回数対数マッピング",
            "距離カラーリング",
            "角度カラーリング",
            "ポテンシャル関数法",
            "軌道トラップ法"
        ]

        # 非発散部の着色アルゴリズム一覧
        self.non_diverge_algorithms = [
            "単色",
            "グラデーション",
            "パラメータ(C)",
            "パラメータ(Z)"
        ]

        # 着色アルゴリズムの説明
        self.diverge_algorithm_descriptions = {
            "反復回数線形マッピング": "反復回数をそのまま色のパレットに線形にマッピングします。反復回数が少ないほどある色に近く、多いほど別の色に近くなります。",
            "スムージングカラーリング": "発散の速さによって補正値を計算し、滑らかな色のグラデーションを実現します。エッジ部分の色の境界が滑らかになり、より美しい画像が得られます。",
            "ヒストグラム平坦化法": "全画素の反復回数の分布（ヒストグラム）を元に、色が均一に使われるように再マッピングします。色のバランスがとれて、見やすい画像になります。",
            "反復回数対数マッピング": "反復回数の対数を色のパレットにマッピングします。脱出速度の違いをより細かく表現できます。",
            "距離カラーリング": "境界からの距離に基づいて色を決定します。境界に近いほどある色に、遠いほど別の色になるように設定します。滑らかなグラデーションを表現できます。",
            "角度カラーリング": "発散する際の角度や、反復ごとの角度の変化に応じて色を決定します。フラクタル特有の回転構造を視覚的に表現できます。",
            "ポテンシャル関数法": "反復回数を連続的な関数を用いて色を決定します。より滑らかで自然なグラデーションが得られます。",
            "軌道トラップ法": "あらかじめ定めた形状をトラップとして設定し、反復軌道がそのトラップに近づいた時に色を変化させます。芸術的な効果や、特定の構造を強調するために使われ、個性的な結果が得られます。"
        }

        self.non_diverge_algorithm_descriptions = {
            "単色": "フラクタル集合の内部を単一の色で塗りつぶします。",
            "グラデーション": "非発散部全体にグラデーションを適用します。",
            "パラメータ(C)": "パラメータCの値に応じて非発散部の色を変えます。",
            "パラメータ(Z)": "パラメータZの値に応じて非発散部の色を変えます。"
        }

        # Matplotlibのキャンバスを作成
        self.fig = Figure(figsize=(6, 6), dpi=100)
        self.ax = self.fig.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.canvas_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # 操作パネルの構築
        self.setup_control_panel()

        # 初期描画
        self.draw_fractal()

    def setup_control_panel(self):
        # グリッドレイアウトを使用
        row = 0

        # 漸化式表示（タイプ選択に応じて変更）
        ttk.Label(self.control_frame, text="フラクタルタイプ:").grid(row=row, column=0, sticky=tk.W, padx=10, pady=5)
        self.fractal_type_var = tk.StringVar(value=self.fractal_type)
        fractal_type_combo = ttk.Combobox(self.control_frame, textvariable=self.fractal_type_var, values=["Julia", "Mandelbrot"], state="readonly")
        fractal_type_combo.grid(row=row, column=1, sticky=tk.W+tk.E, padx=10, pady=5)
        fractal_type_combo.bind("<<ComboboxSelected>>", self.update_formula_display)
        row += 1

        # 漸化式表示エリア
        self.formula_var = tk.StringVar()
        self.formula_label = ttk.Label(self.control_frame, textvariable=self.formula_var, font=("Courier", 12))
        self.formula_label.grid(row=row, column=0, columnspan=2, sticky=tk.W, padx=10, pady=5)
        self.update_formula_display()
        row += 1

        # 最大反復回数
        ttk.Label(self.control_frame, text="最大反復回数:").grid(row=row, column=0, sticky=tk.W, padx=10, pady=5)
        self.max_iter_var = tk.StringVar(value=str(self.max_iterations))
        max_iter_entry = ttk.Entry(self.control_frame, textvariable=self.max_iter_var)
        max_iter_entry.grid(row=row, column=1, sticky=tk.W+tk.E, padx=10, pady=5)
        max_iter_entry.bind("<Return>", self.update_fractal)
        max_iter_entry.bind("<FocusOut>", self.update_fractal)
        row += 1

        # Z (実部)
        ttk.Label(self.control_frame, text="Z (実部):").grid(row=row, column=0, sticky=tk.W, padx=10, pady=5)
        self.z_real_var = tk.StringVar(value=str(self.z_real))
        z_real_entry = ttk.Entry(self.control_frame, textvariable=self.z_real_var)
        z_real_entry.grid(row=row, column=1, sticky=tk.W+tk.E, padx=10, pady=5)
        z_real_entry.bind("<Return>", self.update_fractal)
        z_real_entry.bind("<FocusOut>", self.update_fractal)
        row += 1

        # Z (虚部)
        ttk.Label(self.control_frame, text="Z (虚部):").grid(row=row, column=0, sticky=tk.W, padx=10, pady=5)
        self.z_imag_var = tk.StringVar(value=str(self.z_imag))
        z_imag_entry = ttk.Entry(self.control_frame, textvariable=self.z_imag_var)
        z_imag_entry.grid(row=row, column=1, sticky=tk.W+tk.E, padx=10, pady=5)
        z_imag_entry.bind("<Return>", self.update_fractal)
        z_imag_entry.bind("<FocusOut>", self.update_fractal)
        row += 1

        # C (実部)
        ttk.Label(self.control_frame, text="C (実部):").grid(row=row, column=0, sticky=tk.W, padx=10, pady=5)
        self.c_real_var = tk.StringVar(value=str(self.c_real))
        c_real_entry = ttk.Entry(self.control_frame, textvariable=self.c_real_var)
        c_real_entry.grid(row=row, column=1, sticky=tk.W+tk.E, padx=10, pady=5)
        c_real_entry.bind("<Return>", self.update_fractal)
        c_real_entry.bind("<FocusOut>", self.update_fractal)
        row += 1

        # C (虚部)
        ttk.Label(self.control_frame, text="C (虚部):").grid(row=row, column=0, sticky=tk.W, padx=10, pady=5)
        self.c_imag_var = tk.StringVar(value=str(self.c_imag))
        c_imag_entry = ttk.Entry(self.control_frame, textvariable=self.c_imag_var)
        c_imag_entry.grid(row=row, column=1, sticky=tk.W+tk.E, padx=10, pady=5)
        c_imag_entry.bind("<Return>", self.update_fractal)
        c_imag_entry.bind("<FocusOut>", self.update_fractal)
        row += 1

        # 発散部の着色アルゴリズム選択
        ttk.Label(self.control_frame, text="発散部の着色アルゴリズム:").grid(row=row, column=0, columnspan=2, sticky=tk.W, padx=10, pady=5)
        row += 1
        self.diverge_algo_var = tk.StringVar(value=self.diverge_algorithm)
        diverge_algo_combo = ttk.Combobox(self.control_frame, textvariable=self.diverge_algo_var, values=self.diverge_algorithms, state="readonly")
        diverge_algo_combo.grid(row=row, column=0, columnspan=2, sticky=tk.W+tk.E, padx=10, pady=5)
        diverge_algo_combo.bind("<<ComboboxSelected>>", self.update_diverge_description)
        row += 1

        # 発散部の着色アルゴリズム説明
        self.diverge_desc_var = tk.StringVar(value=self.diverge_algorithm_descriptions[self.diverge_algorithm])
        self.diverge_desc_text = tk.Text(self.control_frame, height=4, wrap=tk.WORD)
        self.diverge_desc_text.grid(row=row, column=0, columnspan=2, sticky=tk.W+tk.E, padx=10, pady=5)
        self.diverge_desc_text.insert(tk.END, self.diverge_desc_var.get())
        self.diverge_desc_text.config(state=tk.DISABLED)
        row += 1

        # 発散部のカラーマップ選択
        ttk.Label(self.control_frame, text="発散部のカラーマップ:").grid(row=row, column=0, columnspan=2, sticky=tk.W, padx=10, pady=5)
        row += 1
        self.diverge_colormap_var = tk.StringVar(value=self.diverge_colormap)
        diverge_colormap_combo = ttk.Combobox(self.control_frame, textvariable=self.diverge_colormap_var, values=self.colormaps, state="readonly")
        diverge_colormap_combo.grid(row=row, column=0, columnspan=2, sticky=tk.W+tk.E, padx=10, pady=5)
        diverge_colormap_combo.bind("<<ComboboxSelected>>", self.update_fractal)
        row += 1

        # 非発散部の着色アルゴリズム選択
        ttk.Label(self.control_frame, text="非発散部の着色アルゴリズム:").grid(row=row, column=0, columnspan=2, sticky=tk.W, padx=10, pady=5)
        row += 1
        self.non_diverge_algo_var = tk.StringVar(value=self.non_diverge_algorithm)
        non_diverge_algo_combo = ttk.Combobox(self.control_frame, textvariable=self.non_diverge_algo_var, values=self.non_diverge_algorithms, state="readonly")
        non_diverge_algo_combo.grid(row=row, column=0, columnspan=2, sticky=tk.W+tk.E, padx=10, pady=5)
        non_diverge_algo_combo.bind("<<ComboboxSelected>>", self.update_non_diverge_description)
        row += 1

        # 非発散部の着色アルゴリズム説明
        self.non_diverge_desc_var = tk.StringVar(value=self.non_diverge_algorithm_descriptions[self.non_diverge_algorithm])
        self.non_diverge_desc_text = tk.Text(self.control_frame, height=4, wrap=tk.WORD)
        self.non_diverge_desc_text.grid(row=row, column=0, columnspan=2, sticky=tk.W+tk.E, padx=10, pady=5)
        self.non_diverge_desc_text.insert(tk.END, self.non_diverge_desc_var.get())
        self.non_diverge_desc_text.config(state=tk.DISABLED)
        row += 1

        # 非発散部のカラーマップ選択
        ttk.Label(self.control_frame, text="非発散部のカラーマップ:").grid(row=row, column=0, columnspan=2, sticky=tk.W, padx=10, pady=5)
        row += 1
        self.non_diverge_colormap_var = tk.StringVar(value=self.non_diverge_colormap)
        non_diverge_colormap_combo = ttk.Combobox(self.control_frame, textvariable=self.non_diverge_colormap_var, values=self.colormaps, state="readonly")
        non_diverge_colormap_combo.grid(row=row, column=0, columnspan=2, sticky=tk.W+tk.E, padx=10, pady=5)
        non_diverge_colormap_combo.bind("<<ComboboxSelected>>", self.update_fractal)
        row += 1

        # 描画ボタン
        render_button = ttk.Button(self.control_frame, text="描画", command=self.draw_fractal)
        render_button.grid(row=row, column=0, columnspan=2, sticky=tk.W+tk.E, padx=10, pady=10)

    def update_formula_display(self, event=None):
        self.fractal_type = self.fractal_type_var.get()
        if self.fractal_type == "Julia":
            self.formula_var.set("Z_n+1 = Z_n² + C")
        else:  # Mandelbrot
            self.formula_var.set("Z_n+1 = Z_n² + C\nZ_0 = 0, C = 座標")

        # フラクタルタイプが変更されたらフラクタルを再描画
        if event:
            self.draw_fractal()

    def update_diverge_description(self, event=None):
        self.diverge_algorithm = self.diverge_algo_var.get()
        self.diverge_desc_text.config(state=tk.NORMAL)
        self.diverge_desc_text.delete(1.0, tk.END)
        self.diverge_desc_text.insert(tk.END, self.diverge_algorithm_descriptions[self.diverge_algorithm])
        self.diverge_desc_text.config(state=tk.DISABLED)

        # 着色アルゴリズムが変更されたらフラクタルを再描画
        if event:
            self.draw_fractal()

    def update_non_diverge_description(self, event=None):
        self.non_diverge_algorithm = self.non_diverge_algo_var.get()
        self.non_diverge_desc_text.config(state=tk.NORMAL)
        self.non_diverge_desc_text.delete(1.0, tk.END)
        self.non_diverge_desc_text.insert(tk.END, self.non_diverge_algorithm_descriptions[self.non_diverge_algorithm])
        self.non_diverge_desc_text.config(state=tk.DISABLED)

        # 着色アルゴリズムが変更されたらフラクタルを再描画
        if event:
            self.draw_fractal()

    def update_fractal(self, event=None):
        # エントリーから値を取得して更新
        try:
            self.max_iterations = int(self.max_iter_var.get())
            self.z_real = float(self.z_real_var.get())
            self.z_imag = float(self.z_imag_var.get())
            self.c_real = float(self.c_real_var.get())
            self.c_imag = float(self.c_imag_var.get())
            self.diverge_colormap = self.diverge_colormap_var.get()
            self.non_diverge_colormap = self.non_diverge_colormap_var.get()

            # フラクタルを再描画
            self.draw_fractal()
        except ValueError:
            # 無効な入力があれば無視
            pass

    def draw_fractal(self):
        start_time = time.time()
        self.ax.clear()

        # 計算範囲の設定 (-2.0 <= x <= 2.0, -2.0 <= y <= 2.0)
        x_min, x_max = -2.0, 2.0
        y_min, y_max = -2.0, 2.0
        resolution = 500  # グリッドの解像度

        # 座標グリッドの作成
        x = np.linspace(x_min, x_max, resolution)
        y = np.linspace(y_min, y_max, resolution)
        X, Y = np.meshgrid(x, y)

        # 複素数グリッドの作成
        Z = X + 1j * Y

        # フラクタルの種類に応じて計算
        if self.fractal_type == "Julia":
            C = complex(self.c_real, self.c_imag)
            results = self.compute_julia(Z, C, self.max_iterations)
        else:  # Mandelbrot
            Z0 = complex(self.z_real, self.z_imag)
            results = self.compute_mandelbrot(Z, Z0, self.max_iterations)

        # 着色アルゴリズムの適用
        colored_results = self.apply_coloring_algorithm(results)

        # 結果の表示
        im = self.ax.imshow(colored_results, extent=[x_min, x_max, y_min, y_max], origin="lower", aspect="equal")
        self.ax.set_title(f"{self.fractal_type}セット")
        self.fig.tight_layout()

        # キャンバスの更新
        self.canvas.draw()

        end_time = time.time()
        print(f"描画時間: {end_time - start_time:.2f}秒")

    def compute_julia(self, Z, C, max_iter):
        """Juliaセットを計算"""
        # 結果を保存する配列を作成
        shape = Z.shape
        iterations = np.zeros(shape, dtype=int)
        mask = np.zeros(shape, dtype=bool)
        z_vals = np.zeros(shape, dtype=complex)

        # Z値の初期化
        z = Z.copy()

        # 発散チェック
        for i in range(max_iter):
            # マスクを更新（まだ発散していない点）
            mask = np.abs(z) <= 2.0
            if not np.any(mask):
                break

            # 値が2より小さい点のみ更新
            z[mask] = z[mask]**2 + C

            # 新たに発散した点の反復回数を記録
            iterations[mask & (np.abs(z) > 2.0)] = i + 1

            # 各点の最終値を記録
            z_vals = z.copy()

        # 最大反復回数に達した点は集合の内部
        iterations[mask] = 0

        return {
            'iterations': iterations,
            'mask': mask,
            'z_vals': z_vals
        }

    def compute_mandelbrot(self, Z, Z0, max_iter):
        """Mandelbrotセットを計算"""
        # 結果を保存する配列を作成
        shape = Z.shape
        iterations = np.zeros(shape, dtype=int)
        mask = np.zeros(shape, dtype=bool)
        z_vals = np.zeros(shape, dtype=complex)

        # Z値の初期化
        z = np.full(shape, Z0, dtype=complex)

        # CはMandelbrotの場合、座標そのもの
        c = Z.copy()

        # 発散チェック
        for i in range(max_iter):
            # マスクを更新（まだ発散していない点）
            mask = np.abs(z) <= 2.0
            if not np.any(mask):
                break

            # 値が2より小さい点のみ更新
            z[mask] = z[mask]**2 + c[mask]

            # 新たに発散した点の反復回数を記録
            iterations[mask & (np.abs(z) > 2.0)] = i + 1

            # 各点の最終値を記録
            z_vals = z.copy()

        # 最大反復回数に達した点は集合の内部
        iterations[mask] = 0

        return {
            'iterations': iterations,
            'mask': mask,
            'z_vals': z_vals
        }

    def apply_coloring_algorithm(self, results):
        """着色アルゴリズムを適用"""
        iterations = results['iterations']
        mask = results['mask']
        z_vals = results['z_vals']

        # 結果の配列を作成（RGBAフォーマット）
        colored = np.zeros((*iterations.shape, 4))

        # 発散部分の着色
        divergent = iterations > 0
        if np.any(divergent):
            # 発散部分の着色アルゴリズムを適用
            if self.diverge_algorithm == "反復回数線形マッピング":
                norm = plt.Normalize(1, self.max_iterations)
                colored[divergent] = plt.cm.get_cmap(self.diverge_colormap)(norm(iterations[divergent]))

            elif self.diverge_algorithm == "スムージングカラーリング":
                # スムージングアルゴリズム
                log_zn = np.log(np.abs(z_vals))
                nu = np.log(log_zn/np.log(2)) / np.log(2)
                smooth_iter = iterations - nu
                smooth_iter[mask] = 0  # 非発散部分は0に

                norm = plt.Normalize(0, self.max_iterations)
                colored[divergent] = plt.cm.get_cmap(self.diverge_colormap)(norm(smooth_iter[divergent]))

            elif self.diverge_algorithm == "ヒストグラム平坦化法":
                # ヒストグラム平坦化
                hist, bins = np.histogram(iterations[divergent], bins=self.max_iterations, density=True)
                cdf = hist.cumsum()
                cdf = cdf / cdf[-1]  # 正規化

                # CDFを使用して再マッピング
                remapped = np.interp(iterations[divergent], bins[:-1], cdf)
                colored[divergent] = plt.cm.get_cmap(self.diverge_colormap)(remapped)

            elif self.diverge_algorithm == "反復回数対数マッピング":
                # 対数マッピング
                iter_log = np.zeros_like(iterations, dtype=float)
                iter_log[divergent] = np.log(iterations[divergent]) / np.log(self.max_iterations)

                colored[divergent] = plt.cm.get_cmap(self.diverge_colormap)(iter_log[divergent])

            elif self.diverge_algorithm == "距離カラーリング":
                # 距離カラーリング (境界からの距離)
                dist = np.abs(z_vals)
                dist[mask] = 0

                norm = plt.Normalize(0, 10)  # 適当な正規化範囲
                colored[divergent] = plt.cm.get_cmap(self.diverge_colormap)(norm(dist[divergent]))

            elif self.diverge_algorithm == "角度カラーリング":
                # 角度カラーリング
                angles = np.angle(z_vals) / (2*np.pi) + 0.5  # 0~1に正規化
                colored[divergent] = plt.cm.get_cmap(self.diverge_colormap)(angles[divergent])

            elif self.diverge_algorithm == "ポテンシャル関数法":
                # ポテンシャル関数法
                potential = 1 - 1 / np.log(np.abs(z_vals) + 1)
                potential[mask] = 0

                colored[divergent] = plt.cm.get_cmap(self.diverge_colormap)(potential[divergent])

            elif self.diverge_algorithm == "軌道トラップ法":
                # 軌道トラップ法（円形のトラップを仮定）
                trap_dist = np.abs(z_vals - 1.0)  # 原点からのずれを1.0と仮定
                trap_dist[mask] = float('inf')

                norm = plt.Normalize(0, 2)
                colored[divergent] = plt.cm.get_cmap(self.diverge_colormap)(norm(trap_dist[divergent]))

        # 非発散部分の着色
        non_divergent = ~divergent
        if np.any(non_divergent):
            # 非発散部分の着色アルゴリズムを適用
            if self.non_diverge_algorithm == "単色":
                # 単色（黒）
                colored[non_divergent] = np.array([0, 0, 0, 1])  # 黒色（RGBA）

            elif self.non_diverge_algorithm == "グラデーション":
                # 非発散部全体にグラデーションを適用
                x, y = np.indices(iterations.shape)
                normalized_distance = np.sqrt((x - iterations.shape[0]/2)**2 + (y - iterations.shape[1]/2)**2) / np.sqrt((iterations.shape[0]/2)**2 + (iterations.shape[1]/2)**2)
                colored[non_divergent] = plt.cm.get_cmap(self.non_diverge_colormap)(normalized_distance[non_divergent])

            elif self.non_diverge_algorithm == "パラメータ(C)":
                # Cの値に応じて内部の色を変える
                if self.fractal_type == "Julia":
                    # Juliaの場合はCは固定値
                    c_val = complex(self.c_real, self.c_imag)
                    angle = (np.angle(c_val) / (2*np.pi)) + 0.5  # 0〜1に正規化
                    colored[non_divergent] = plt.cm.get_cmap(self.non_diverge_colormap)(angle)
                else:
                    # Mandelbrotの場合はCは座標
                    c_real, c_imag = np.real(z_vals), np.imag(z_vals)
                    angle = (np.arctan2(c_imag, c_real) / (2*np.pi)) + 0.5
                    colored[non_divergent] = plt.cm.get_cmap(self.non_diverge_colormap)(angle[non_divergent])

            elif self.non_diverge_algorithm == "パラメータ(Z)":
                # Zの値に応じて内部の色を変える
                z_real, z_imag = np.real(z_vals), np.imag(z_vals)
                angle = (np.arctan2(z_imag, z_real) / (2*np.pi)) + 0.5
                colored[non_divergent] = plt.cm.get_cmap(self.non_diverge_colormap)(angle[non_divergent])

        return colored

if __name__ == "__main__":
    root = tk.Tk()
    app = FractalGenerator(root)
    root.mainloop()
