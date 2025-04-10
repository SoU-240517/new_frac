import tkinter as tk
from tkinter import ttk
import matplotlib.pyplot as plt
from .zoom_function.debug_logger import DebugLogger # DebugLogger をインポート
from .zoom_function.enums import LogLevel # LogLevel をインポート

class ParameterPanel:
    """ パラメータパネルクラス """
    def __init__(self, parent, update_callback, reset_callback, logger: DebugLogger):
        """ パラメータパネルの初期化 """
        self.logger = logger
        self.logger.log(LogLevel.INIT, "ParameterPanel")
        self.parent = parent
        self.update_callback = update_callback
        self.reset_callback = reset_callback
        self.logger.log(LogLevel.DEBUG, "Parameter panel settings.")
        self.setup_panel()

    def setup_panel(self):
        """ パラメータパネルの設定 """
        self.logger.log(LogLevel.DEBUG, "Parameter panel settings.")
        row = 0

        # フラクタルタイプ選択
        ttk.Label(self.parent, text="フラクタルタイプ:").grid(row=row, column=0, sticky=tk.W, padx=10, pady=5)
        self.fractal_type_var = tk.StringVar(value="Julia")
        fractal_type_combo = ttk.Combobox(self.parent, textvariable=self.fractal_type_var,
                                          values=["Julia", "Mandelbrot"], state="readonly")
        fractal_type_combo.grid(row=row, column=1, sticky=tk.W+tk.E, padx=10, pady=5)
        fractal_type_combo.bind("<<ComboboxSelected>>", self.update_callback)
        row += 1

        # 漸化式表示
        self.formula_var = tk.StringVar()
        self.formula_label = ttk.Label(self.parent, textvariable=self.formula_var, font=("Courier", 12))
        self.formula_label.grid(row=row, column=0, columnspan=2, sticky=tk.W, padx=10, pady=5)
        self.logger.log(LogLevel.DEBUG, "Show display formula.")
        self.show_formula_display()
        row += 1

        # 最大反復回数
        ttk.Label(self.parent, text="最大反復回数:").grid(row=row, column=0, sticky=tk.W, padx=10, pady=5)
        self.max_iter_var = tk.StringVar(value="100")
        max_iter_entry = ttk.Entry(self.parent, textvariable=self.max_iter_var)
        max_iter_entry.grid(row=row, column=1, sticky=tk.W+tk.E, padx=10, pady=5)
        max_iter_entry.bind("<Return>", lambda e: self.update_callback())
        max_iter_entry.bind("<FocusOut>", lambda e: self.update_callback())
        row += 1

        # Z (実部)
        ttk.Label(self.parent, text="Z (実部):").grid(row=row, column=0, sticky=tk.W, padx=10, pady=5)
        self.z_real_var = tk.StringVar(value="0.0")
        z_real_entry = ttk.Entry(self.parent, textvariable=self.z_real_var)
        z_real_entry.grid(row=row, column=1, sticky=tk.W+tk.E, padx=10, pady=5)
        z_real_entry.bind("<Return>", lambda e: self.update_callback())
        z_real_entry.bind("<FocusOut>", lambda e: self.update_callback())
        row += 1

        # Z (虚部)
        ttk.Label(self.parent, text="Z (虚部):").grid(row=row, column=0, sticky=tk.W, padx=10, pady=5)
        self.z_imag_var = tk.StringVar(value="0.0")
        z_imag_entry = ttk.Entry(self.parent, textvariable=self.z_imag_var)
        z_imag_entry.grid(row=row, column=1, sticky=tk.W+tk.E, padx=10, pady=5)
        z_imag_entry.bind("<Return>", lambda e: self.update_callback())
        z_imag_entry.bind("<FocusOut>", lambda e: self.update_callback())
        row += 1

        # C (実部)
        ttk.Label(self.parent, text="C (実部):").grid(row=row, column=0, sticky=tk.W, padx=10, pady=5)
        self.c_real_var = tk.StringVar(value="-0.7")
        c_real_entry = ttk.Entry(self.parent, textvariable=self.c_real_var)
        c_real_entry.grid(row=row, column=1, sticky=tk.W+tk.E, padx=10, pady=5)
        c_real_entry.bind("<Return>", lambda e: self.update_callback())
        c_real_entry.bind("<FocusOut>", lambda e: self.update_callback())
        row += 1

        # C (虚部)
        ttk.Label(self.parent, text="C (虚部):").grid(row=row, column=0, sticky=tk.W, padx=10, pady=5)
        self.c_imag_var = tk.StringVar(value="0.27015")
        c_imag_entry = ttk.Entry(self.parent, textvariable=self.c_imag_var)
        c_imag_entry.grid(row=row, column=1, sticky=tk.W+tk.E, padx=10, pady=5)
        c_imag_entry.bind("<Return>", lambda e: self.update_callback())
        c_imag_entry.bind("<FocusOut>", lambda e: self.update_callback())
        row += 1

        # 発散部の着色アルゴリズム選択
        ttk.Label(self.parent, text="発散部の着色アルゴリズム:").grid(row=row, column=0, columnspan=2, sticky=tk.W, padx=10, pady=5)
        row += 1
        self.diverge_algo_var = tk.StringVar(value="反復回数線形マッピング")
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
        diverge_algo_combo = ttk.Combobox(self.parent, textvariable=self.diverge_algo_var,
                                          values=self.diverge_algorithms, state="readonly")
        diverge_algo_combo.grid(row=row, column=0, columnspan=2, sticky=tk.W+tk.E, padx=10, pady=5)
        diverge_algo_combo.bind("<<ComboboxSelected>>", self.update_callback)
        row += 1

        # 非発散部の着色アルゴリズム選択
        ttk.Label(self.parent, text="非発散部の着色アルゴリズム:").grid(row=row, column=0, columnspan=2, sticky=tk.W, padx=10, pady=5)
        row += 1
        self.non_diverge_algo_var = tk.StringVar(value="単色")
        self.non_diverge_algorithms = [
            "単色",
            "グラデーション",
            "パラメータ(C)",
            "パラメータ(Z)"
        ]
        non_diverge_algo_combo = ttk.Combobox(self.parent, textvariable=self.non_diverge_algo_var,
                                              values=self.non_diverge_algorithms, state="readonly")
        non_diverge_algo_combo.grid(row=row, column=0, columnspan=2, sticky=tk.W+tk.E, padx=10, pady=5)
        non_diverge_algo_combo.bind("<<ComboboxSelected>>", self.update_callback)
        row += 1

        # 発散部のカラーマップ選択
        ttk.Label(self.parent, text="発散部のカラーマップ:").grid(row=row, column=0, columnspan=2, sticky=tk.W, padx=10, pady=5)
        row += 1
        self.colormaps = sorted([m for m in plt.colormaps() if not m.endswith('_r')])
        self.diverge_colormap_var = tk.StringVar(value="viridis")
        diverge_colormap_combo = ttk.Combobox(self.parent, textvariable=self.diverge_colormap_var,
                                              values=self.colormaps, state="readonly")
        diverge_colormap_combo.grid(row=row, column=0, columnspan=2, sticky=tk.W+tk.E, padx=10, pady=5)
        diverge_colormap_combo.bind("<<ComboboxSelected>>", self.update_callback)
        row += 1

        # 非発散部のカラーマップ選択
        ttk.Label(self.parent, text="非発散部のカラーマップ:").grid(row=row, column=0, columnspan=2, sticky=tk.W, padx=10, pady=5)
        row += 1
        self.non_diverge_colormap_var = tk.StringVar(value="plasma")
        non_diverge_colormap_combo = ttk.Combobox(self.parent, textvariable=self.non_diverge_colormap_var,
                                                  values=self.colormaps, state="readonly")
        non_diverge_colormap_combo.grid(row=row, column=0, columnspan=2, sticky=tk.W+tk.E, padx=10, pady=5)
        non_diverge_colormap_combo.bind("<<ComboboxSelected>>", self.update_callback)
        row += 1

        # 描画ボタン
        render_button = ttk.Button(self.parent, text="描画", command=self.update_callback)
        render_button.grid(row=row, column=0, columnspan=2, sticky=tk.W+tk.E, padx=10, pady=10)
        row += 1

        # 描画リセットボタン（reset_callbackが設定されていれば）
        if self.reset_callback is not None:
            reset_button = ttk.Button(self.parent, text="描画リセット", command=self.reset_callback)
            reset_button.grid(row=row, column=0, columnspan=2, sticky=tk.W+tk.E, padx=10, pady=10)

    def show_formula_display(self):
        """ 漸化式を表示する関数 """
        fractal_type = self.fractal_type_var.get()
        if fractal_type == "Julia":
            self.formula_var.set("Z_n+1 = Z_n² + C")
        else:
            self.formula_var.set("Z_n+1 = Z_n² + C\nZ_0 = 0, C = 座標")

    def get_parameters(self):
        """ パラメータを取得する関数 """
        try:
            panel_params = {
                "fractal_type": self.fractal_type_var.get(),
                "max_iterations": int(self.max_iter_var.get()),
                "z_real": float(self.z_real_var.get()),
                "z_imag": float(self.z_imag_var.get()),
                "c_real": float(self.c_real_var.get()),
                "c_imag": float(self.c_imag_var.get()),
                "diverge_algorithm": self.diverge_algo_var.get(),
                "non_diverge_algorithm": self.non_diverge_algo_var.get(),
                "diverge_colormap": self.diverge_colormap_var.get(),
                "non_diverge_colormap": self.non_diverge_colormap_var.get()
            }
        except ValueError:
            panel_params = {}
        return panel_params
