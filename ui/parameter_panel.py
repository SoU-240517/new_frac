import tkinter as tk
from tkinter import ttk
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image, ImageTk
from .zoom_function.debug_logger import DebugLogger
from .zoom_function.enums import LogLevel

class ParameterPanel:
    """ パラメータパネルクラス """
    COLORBAR_WIDTH = 150 # カラーバーの幅 (ピクセル)
    COLORBAR_HEIGHT = 15  # カラーバーの高さ (ピクセル)

    def __init__(self, parent, update_callback, reset_callback, logger: DebugLogger):
        """ パラメータパネルの初期化 """
        self.logger = logger
        self.parent = parent
        self.update_callback = update_callback # フラクタル更新用コールバック
        self.reset_callback = reset_callback
        self.logger.log(LogLevel.INIT, "パラメータパネルセットアップ開始")
        self.setup_panel()
        self._update_colorbars() # パネル設定後に初期カラーバーを更新

    def _create_colorbar_image(self, cmap_name: str) -> ImageTk.PhotoImage:
        """ 指定されたカラーマップ名からカラーバーのPhotoImageを生成 """
        self.logger.log(LogLevel.SUCCESS, "カラーバー生成開始")
        try:
            cmap = plt.get_cmap(cmap_name)
            # NumPyでグラデーションデータを作成 (幅 x 高さ x RGBA)
            gradient = np.linspace(0, 1, self.COLORBAR_WIDTH)
            colors = cmap(gradient) # (width, 4) の RGBA配列 (0.0-1.0)
            # (height, width, 4) に拡張し、uint8に変換
            rgba_image = np.uint8(np.tile(colors, (self.COLORBAR_HEIGHT, 1, 1)) * 255)
            # NumPy配列からPIL Imageへ変換
            pil_image = Image.fromarray(rgba_image, 'RGBA')
            # PIL ImageからPhotoImageへ変換
            photo_image = ImageTk.PhotoImage(pil_image)
            return photo_image
        except ValueError:
            # 無効なカラーマップ名の場合、単色のダミー画像を返すなど
            self.logger.log(LogLevel.WARNING, f"無効なカラーマップ名: {cmap_name}")
            # 透明なダミー画像を生成
            dummy_rgba = np.zeros((self.COLORBAR_HEIGHT, self.COLORBAR_WIDTH, 4), dtype=np.uint8)
            pil_image = Image.fromarray(dummy_rgba, 'RGBA')
            photo_image = ImageTk.PhotoImage(pil_image)
            return photo_image
        except Exception as e:
            self.logger.log(LogLevel.ERROR, f"カラーバー生成中にエラー ({cmap_name}): {e}")
             # 透明なダミー画像を生成
            dummy_rgba = np.zeros((self.COLORBAR_HEIGHT, self.COLORBAR_WIDTH, 4), dtype=np.uint8)
            pil_image = Image.fromarray(dummy_rgba, 'RGBA')
            photo_image = ImageTk.PhotoImage(pil_image)
            return photo_image

    def _update_colorbars(self, *args):
        """ 選択されているカラーマップに基づいてカラーバーの表示を更新 """
        # 発散部
        diverge_cmap_name = self.diverge_colormap_var.get()
        self.logger.log(LogLevel.CALL, "カラーバー更新：発散部")
        diverge_photo = self._create_colorbar_image(diverge_cmap_name)
        self.diverge_colorbar_label.config(image=diverge_photo)
        self.diverge_colorbar_label.image = diverge_photo # 参照を保持
        # 非発散部
        non_diverge_cmap_name = self.non_diverge_colormap_var.get()
        self.logger.log(LogLevel.CALL, "カラーバー更新：非発散部")
        non_diverge_photo = self._create_colorbar_image(non_diverge_cmap_name)
        self.non_diverge_colorbar_label.config(image=non_diverge_photo)
        self.non_diverge_colorbar_label.image = non_diverge_photo # 参照を保持

    def setup_panel(self):
        """ パラメータパネルの設定 """
        # --- フラクタルタイプ ---
        row = 0
        ttk.Label(self.parent, text="フラクタルタイプ:").grid(row=row, column=0, sticky=tk.W, padx=10, pady=(5,0))
        self.fractal_type_var = tk.StringVar(value="Julia")
        fractal_type_combo = ttk.Combobox(
            self.parent, textvariable=self.fractal_type_var,
            values=["Julia", "Mandelbrot"], state="readonly")
        fractal_type_combo.grid(row=row, column=1, sticky=tk.W+tk.E, padx=10, pady=(5,0))
        # フラクタルタイプ変更時に、描画更新をし、その後にカラーバー更新を行う
        fractal_type_combo.bind("<<ComboboxSelected>>", lambda e: [self.update_callback(), self._update_colorbars()])

        # --- 漸化式表示 ---
        row += 1
        self.formula_var = tk.StringVar()
        self.formula_label = ttk.Label(self.parent, textvariable=self.formula_var, font=("Courier", 10)) # フォント調整
        self.formula_label.grid(row=row, column=0, columnspan=2, sticky=tk.W, padx=10, pady=2)
        self.show_formula_display()

        # --- パラメータ入力 (最大反復回数, Z, C) ---
        row += 1 # 最大反復回数
        ttk.Label(self.parent, text="最大反復回数:").grid(row=row, column=0, sticky=tk.W, padx=10, pady=2)
        self.max_iter_var = tk.StringVar(value="100")
        max_iter_entry = ttk.Entry(self.parent, textvariable=self.max_iter_var)
        max_iter_entry.grid(row=row, column=1, sticky=tk.W+tk.E, padx=10, pady=2)
        max_iter_entry.bind("<Return>", lambda e: [self.update_callback(), self._update_colorbars()]) # エントリーの変更時にも描画更新とカラーバー更新を行う
# サンプルとして残す
#        max_iter_entry.bind("<FocusOut>", lambda e: [self.update_callback(), self._update_colorbars()])

        row += 1 # Z (実部)
        ttk.Label(self.parent, text="Z (実部):").grid(row=row, column=0, sticky=tk.W, padx=10, pady=2)
        self.z_real_var = tk.StringVar(value="0.0")
        z_real_entry = ttk.Entry(self.parent, textvariable=self.z_real_var)
        z_real_entry.grid(row=row, column=1, sticky=tk.W+tk.E, padx=10, pady=2)
        z_real_entry.bind("<Return>", lambda e: [self.update_callback(), self._update_colorbars()])

        row += 1 # Z (虚部)
        ttk.Label(self.parent, text="Z (虚部):").grid(row=row, column=0, sticky=tk.W, padx=10, pady=2)
        self.z_imag_var = tk.StringVar(value="0.0")
        z_imag_entry = ttk.Entry(self.parent, textvariable=self.z_imag_var)
        z_imag_entry.grid(row=row, column=1, sticky=tk.W+tk.E, padx=10, pady=2)
        z_imag_entry.bind("<Return>", lambda e: [self.update_callback(), self._update_colorbars()])

        row += 1 # C (実部)
        ttk.Label(self.parent, text="C (実部):").grid(row=row, column=0, sticky=tk.W, padx=10, pady=2)
        self.c_real_var = tk.StringVar(value="-0.7")
        c_real_entry = ttk.Entry(self.parent, textvariable=self.c_real_var)
        c_real_entry.grid(row=row, column=1, sticky=tk.W+tk.E, padx=10, pady=2)
        c_real_entry.bind("<Return>", lambda e: [self.update_callback(), self._update_colorbars()])

        row += 1 # C (虚部)
        ttk.Label(self.parent, text="C (虚部):").grid(row=row, column=0, sticky=tk.W, padx=10, pady=2)
        self.c_imag_var = tk.StringVar(value="0.27015")
        c_imag_entry = ttk.Entry(self.parent, textvariable=self.c_imag_var)
        c_imag_entry.grid(row=row, column=1, sticky=tk.W+tk.E, padx=10, pady=2)
        c_imag_entry.bind("<Return>", lambda e: [self.update_callback(), self._update_colorbars()])

        # --- 発散部の着色設定 ---
        row += 1
        ttk.Label(self.parent, text="--- 発散部 ---").grid(row=row, column=0, columnspan=2, pady=(10, 0))

        row += 1 # アルゴリズム選択
        ttk.Label(self.parent, text="着色アルゴリズム:").grid(row=row, column=0, sticky=tk.W, padx=10, pady=(5,0))
        self.diverge_algo_var = tk.StringVar(value="スムージングカラーリング") # デフォルト変更
        self.diverge_algorithms = [
            "スムージングカラーリング", "高速スムージング", "指数スムージング", "反復回数線形マッピング", "ヒストグラム平坦化法",
            "反復回数対数マッピング", "距離カラーリング", "角度カラーリング",
            "ポテンシャル関数法", "軌道トラップ法"
        ]
        diverge_algo_combo = ttk.Combobox(self.parent, textvariable=self.diverge_algo_var,
                                          values=self.diverge_algorithms, state="readonly")
        diverge_algo_combo.grid(row=row, column=1, sticky=tk.W+tk.E, padx=10, pady=(5,0))
        diverge_algo_combo.bind("<<ComboboxSelected>>", lambda e: [self.update_callback(), self._update_colorbars()])

        row += 1 # カラーマップ選択
        ttk.Label(self.parent, text="カラーマップ:").grid(row=row, column=0, sticky=tk.W, padx=10, pady=(5,0))
        self.colormaps = sorted([m for m in plt.colormaps() if not m.endswith('_r')])
        self.diverge_colormap_var = tk.StringVar(value="viridis")
        diverge_colormap_combo = ttk.Combobox(self.parent, textvariable=self.diverge_colormap_var,
                                              values=self.colormaps, state="readonly", width=18) # 幅調整
        diverge_colormap_combo.grid(row=row, column=1, sticky=tk.W, padx=10, pady=(5,0)) # 右寄せ解除
        # カラーマップ変更時は、メインの更新コールバックに加えてカラーバー更新も呼ぶ
        diverge_colormap_combo.bind("<<ComboboxSelected>>", lambda e: [self.update_callback(), self._update_colorbars()])

        row += 1 # カラーバー表示用ラベル
        self.diverge_colorbar_label = tk.Label(self.parent) # ここにカラーバー画像を表示
        self.diverge_colorbar_label.grid(row=row, column=1, sticky=tk.W, padx=10, pady=(0, 5))

        # --- 非発散部の着色設定 ---
        row += 1
        ttk.Label(self.parent, text="--- 非発散部 ---").grid(row=row, column=0, columnspan=2, pady=(10, 0))

        row += 1 # アルゴリズム選択
        ttk.Label(self.parent, text="着色アルゴリズム:").grid(row=row, column=0, sticky=tk.W, padx=10, pady=(5,0))
        self.non_diverge_algo_var = tk.StringVar(value="単色")
        self.non_diverge_algorithms = ["単色", "グラデーション", "パラメータ(C)", "パラメータ(Z)"]
        non_diverge_algo_combo = ttk.Combobox(self.parent, textvariable=self.non_diverge_algo_var,
                                              values=self.non_diverge_algorithms, state="readonly")
        non_diverge_algo_combo.grid(row=row, column=1, sticky=tk.W+tk.E, padx=10, pady=(5,0))
        non_diverge_algo_combo.bind("<<ComboboxSelected>>", lambda e: [self.update_callback(), self._update_colorbars()])

        row += 1 # カラーマップ選択
        ttk.Label(self.parent, text="カラーマップ:").grid(row=row, column=0, sticky=tk.W, padx=10, pady=(5,0))
        self.non_diverge_colormap_var = tk.StringVar(value="plasma")
        non_diverge_colormap_combo = ttk.Combobox(self.parent, textvariable=self.non_diverge_colormap_var,
                                              values=self.colormaps, state="readonly", width=18) # 幅調整
        non_diverge_colormap_combo.grid(row=row, column=1, sticky=tk.W, padx=10, pady=(5,0)) # 右寄せ解除
        # カラーマップ変更時は、メインの更新コールバックに加えてカラーバー更新も呼ぶ
        non_diverge_colormap_combo.bind("<<ComboboxSelected>>", lambda e: [self.update_callback(), self._update_colorbars()])

        row += 1 # カラーバー表示用ラベル
        self.non_diverge_colorbar_label = tk.Label(self.parent) # ここにカラーバー画像を表示
        self.non_diverge_colorbar_label.grid(row=row, column=1, sticky=tk.W, padx=10, pady=(0, 5))

        # --- ボタン ---
        row += 1
        render_button = ttk.Button(self.parent, text="描画", command=lambda: [self.update_callback(), self._update_colorbars()])
        render_button.grid(row=row, column=0, columnspan=2, sticky=tk.W+tk.E, padx=10, pady=10)

        row += 1
        if self.reset_callback is not None:
            reset_button = ttk.Button(self.parent, text="描画リセット", command=lambda: [self.reset_callback(), self._update_colorbars()])
            reset_button.grid(row=row, column=0, columnspan=2, sticky=tk.W+tk.E, padx=10, pady=10)

        # パネル全体の列幅を設定（必要に応じて）
        self.parent.columnconfigure(1, weight=1)

    def show_formula_display(self):
        """ 漸化式を表示 """
        fractal_type = self.fractal_type_var.get()
        if fractal_type == "Julia":
            self.formula_var.set("Z(n+1) = Z(n)² + C")
        else: # Mandelbrot
            self.formula_var.set("Z(n+1) = Z(n)² + C\n(Z(0)=0, C=座標)")

    def get_parameters(self) -> dict:
        """ パラメータパネルから値を取得 """
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
            # 数値パラメータのバリデーションを追加するとより堅牢になります
            if panel_params["max_iterations"] <= 0:
                self.logger.log(LogLevel.WARNING, "最大反復回数は正の整数である必要があります。")
                panel_params["max_iterations"] = 100 # デフォルトに戻すなど
        except ValueError as e:
            self.logger.log(LogLevel.ERROR, f"パラメータ取得エラー: 無効な数値入力 - {e}")
            # エラーが発生した場合、空の辞書ではなく、デフォルト値やNoneを返すなど、
            # 呼出し元でのエラーハンドリングを考慮した設計が良いかもしれません。
            # ここでは簡単な例として、エラーがあった項目を特定するのは難しいので空を返します。
            panel_params = {} # または一部の有効なパラメータのみ返すなど
        return panel_params
