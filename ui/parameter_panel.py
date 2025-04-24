import matplotlib.pyplot as plt
import numpy as np
import tkinter as tk
from PIL import Image, ImageTk
from tkinter import ttk
from .zoom_function.debug_logger import DebugLogger
from .zoom_function.enums import LogLevel

class ParameterPanel:
    """ParameterPanel クラス
    - 役割:
        - フラクタル生成用のパラメータを設定するパネル
    """
    COLORBAR_WIDTH = 150
    COLORBAR_HEIGHT = 15

    def __init__(self, parent, update_callback, reset_callback, logger: DebugLogger):
        """ParameterPanel クラスのコンストラクタ（親: MainWindow）
        Args:
            parent: 親ウィジェット
            update_callback: 描画更新コールバック関数
            reset_callback: 描画リセットコールバック関数
            logger: デバッグロガーインスタンス
        """
        self.logger = logger
        self.parent = parent
        self.update_callback = update_callback
        self.reset_callback = reset_callback
        self._setup_panel()
        self._update_colorbars()

    def _setup_panel(self) -> None:
        """パネルのセットアップを行う"""
        self._setup_fractal_type_section()
        self._setup_formula_section()
        self._setup_parameter_section()
        self._setup_diverge_section()
        self._setup_non_diverge_section()
        self._setup_buttons()
        self.parent.columnconfigure(1, weight=1)

    def _setup_fractal_type_section(self) -> None:
        """フラクタルタイプセクションのセットアップ"""
        row = 0
        self._add_label("フラクタルタイプ:", row, 0, pady=(5,0))
        self.fractal_type_var = tk.StringVar(value="Julia")
        combo = self._add_combobox(row, 1, self.fractal_type_var, ["Julia", "Mandelbrot"])
        combo.bind("<<ComboboxSelected>>", self._common_callback)
        self._fractal_type_row = row

    def _setup_formula_section(self) -> None:
        """数式表示セクションのセットアップ"""
        row = self._fractal_type_row + 1
        self.formula_var = tk.StringVar()
        self.formula_label = ttk.Label(self.parent, textvariable=self.formula_var, font=("Courier", 10))
        self.formula_label.grid(row=row, column=0, columnspan=2, sticky=tk.W, padx=10, pady=2)
        self._show_formula_display()
        self._formula_row = row

    def _setup_parameter_section(self) -> None:
        """パラメータ表示セクションのセットアップ"""
        row = self._formula_row + 1
        # 最大反復回数
        self._add_label("最大反復回数:", row, 0)
        self.max_iter_var = tk.StringVar(value="100")
        entry = self._add_entry(row, 1, self.max_iter_var)
        entry.bind("<Return>", self._common_callback)
        params = [("Z (実部):", "z_real_var", "0.0"),
                  ("Z (虚部):", "z_imag_var", "0.0"),
                  ("C (実部):", "c_real_var", "-0.7"),
                  ("C (虚部):", "c_imag_var", "0.27015"
        )]
        for label, varname, default in params:
            row += 1
            self._add_label(label, row, 0)
            setattr(self, varname, tk.StringVar(value=default))
            entry = self._add_entry(row, 1, getattr(self, varname))
            entry.bind("<Return>", self._common_callback)
        self._param_section_last_row = row

    def _setup_diverge_section(self) -> None:
        """発散部セクションのセットアップ"""
        row = self._param_section_last_row + 1
        self._add_label("--- 発散部 ---", row, 0, columnspan=2, pady=(10, 0))
        row += 1
        self._add_label("着色アルゴリズム:", row, 0, pady=(5,0))
        self.diverge_algo_var = tk.StringVar(value="スムージングカラーリング")
        self.diverge_algorithms = [
            "スムージングカラーリング",
            "高速スムージング",
            "指数スムージング",
            "反復回数線形マッピング",
            "反復回数対数マッピング",
            "ヒストグラム平坦化法",
            "距離カラーリング",
            "角度カラーリング",
            "ポテンシャル関数法",
            "軌道トラップ法"
        ]
        combo = self._add_combobox(row, 1, self.diverge_algo_var, self.diverge_algorithms)
        combo.bind("<<ComboboxSelected>>", self._common_callback)
        row += 1
        self.diverge_colorbar_label = tk.Label(self.parent)
        self.diverge_colorbar_label.grid(row=row, column=1, sticky=tk.W, padx=10, pady=(5,0))
        row += 1
        self.colormaps = sorted([m for m in plt.colormaps() if not m.endswith('_r')])
        self._add_label("カラーマップ:", row, 0, pady=(2,5))
        self.diverge_colormap_var = tk.StringVar(value="viridis")
        combo = self._add_combobox(row, 1, self.diverge_colormap_var, self.colormaps, width=18)
        combo.bind("<<ComboboxSelected>>", self._common_callback)
        self._diverge_section_last_row = row

    def _setup_non_diverge_section(self) -> None:
        """非発散部セクションのセットアップ"""
        row = self._diverge_section_last_row + 1
        self._add_label("--- 非発散部 ---", row, 0, columnspan=2, pady=(10, 0))
        row += 1
        self._add_label("着色アルゴリズム:", row, 0, pady=(5,0))
        self.non_diverge_algo_var = tk.StringVar(value="単色")
        self.non_diverge_algorithms = [
            "単色",
            "グラデーション",
            "内部距離（Escape Time Distance）",
            "軌道トラップ(円)（Orbit Trap Coloring）",
            "位相对称（Phase Angle Symmetry）",
            "反復収束速度（Convergence Speed）",
            "微分係数（Derivative Coloring）",
            "統計分布（Histogram Equalization）",
            "パラメータ(C)",
            "パラメータ(Z)"
        ]
        combo = self._add_combobox(row, 1, self.non_diverge_algo_var, self.non_diverge_algorithms)
        combo.bind("<<ComboboxSelected>>", self._common_callback)
        row += 1
        self.non_diverge_colorbar_label = tk.Label(self.parent)
        self.non_diverge_colorbar_label.grid(row=row, column=1, sticky=tk.W, padx=10, pady=(5,0))
        row += 1
        self._add_label("カラーマップ:", row, 0, pady=(2,5))
        self.non_diverge_colormap_var = tk.StringVar(value="plasma")
        combo = self._add_combobox(row, 1, self.non_diverge_colormap_var, self.colormaps, width=18)
        combo.bind("<<ComboboxSelected>>", self._common_callback)
        self._non_diverge_section_last_row = row

    def _setup_buttons(self) -> None:
        """ボタンのセットアップ"""
        row = self._non_diverge_section_last_row + 1
        self._add_button("描画", row, 0, 2, lambda: [self.update_callback(), self._update_colorbars()])
        row += 1
        if self.reset_callback is not None:
            self._add_button("描画リセット", row, 0, 2, lambda: [self.reset_callback(), self._update_colorbars()])

    def _add_label(self, text, row, col, columnspan=1, padx=10, pady=2) -> None:
        """ラベルを追加する
        Args:
            text: ラベルのテキスト
            row: 行
            col: 列
            columnspan: 列のスパン
            padx: 横方向のパディング
            pady: 縦方向のパディング
        """
        ttk.Label(self.parent, text=text).grid(
            row=row, column=col, columnspan=columnspan, sticky=tk.W, padx=padx, pady=pady)

    def _add_entry(self, row, col, var, padx=10, pady=2) -> ttk.Entry:
        """入力欄を追加する
        Args:
            row: 行
            col: 列
            var: 文字列変数
            padx: 横方向のパディング
            pady: 縦方向のパディング
        """
        entry = ttk.Entry(self.parent, textvariable=var)
        entry.grid(row=row, column=col, sticky=tk.W+tk.E, padx=padx, pady=pady)
        return entry

    def _add_combobox(self, row, col, var, values, width=None, padx=10, pady=2) -> ttk.Combobox:
        """コンボックスボックスを追加する
        Args:
            row: 行
            col: 列
            var: 文字列変数
            values: コンボックスボックスの値リスト
            width: コンボックスボックスの幅
            padx: 横方向のパディング
            pady: 縦方向のパディング
        Returns:
            コンボックスボックス
        """
        kwargs = {"textvariable": var, "values": values, "state": "readonly"}
        if width:
            kwargs["width"] = width
        combo = ttk.Combobox(self.parent, **kwargs)
        combo.grid(row=row, column=col, sticky=tk.W, padx=padx, pady=pady)
        return combo

    def _add_button(self, text, row, col, colspan, command) -> ttk.Button:
        """ボタンを追加する
        Args:
            text: ボタンのテキスト
            row: 行
            col: 列
            colspan: 列のスパン
            command: コマンド
        Returns:
            ボタン
        """
        btn = ttk.Button(self.parent, text=text, command=command)
        btn.grid(row=row, column=col, columnspan=colspan, sticky=tk.W+tk.E, padx=10, pady=10)
        return btn

    def _common_callback(self, event=None) -> None:
        """共通のコールバック関数"""
        self.update_callback()
        self._update_colorbars()

    def _create_colorbar_image(self, cmap_name: str) -> ImageTk.PhotoImage:
        """カラーバー画像を生成する
        Args:
            cmap_name: カラーマップ名
        Returns:
            カラーバー画像のPhotoImageオブジェクト
        """
        try:
            cmap = plt.get_cmap(cmap_name)
            gradient = np.linspace(0, 1, self.COLORBAR_WIDTH)
            colors = cmap(gradient)
            rgba_image = np.uint8(np.tile(colors, (self.COLORBAR_HEIGHT, 1, 1)) * 255)
            pil_image = Image.fromarray(rgba_image, 'RGBA')
            photo_image = ImageTk.PhotoImage(pil_image)
            self.logger.log(LogLevel.SUCCESS, "カラーバー生成完了")
            return photo_image
        except ValueError:
            self.logger.log(LogLevel.WARNING, f"無効なカラーマップ名: {cmap_name}")
            dummy_rgba = np.zeros((self.COLORBAR_HEIGHT, self.COLORBAR_WIDTH, 4), dtype=np.uint8)
            pil_image = Image.fromarray(dummy_rgba, 'RGBA')
            photo_image = ImageTk.PhotoImage(pil_image)
            return photo_image
        except Exception as e:
            self.logger.log(LogLevel.ERROR, f"カラーバー生成中にエラー ({cmap_name}): {e}")
            dummy_rgba = np.zeros((self.COLORBAR_HEIGHT, self.COLORBAR_WIDTH, 4), dtype=np.uint8)
            pil_image = Image.fromarray(dummy_rgba, 'RGBA')
            photo_image = ImageTk.PhotoImage(pil_image)
            return photo_image

    def _update_colorbars(self, *args) -> None:
        """カラーバーを更新する"""
        diverge_cmap_name = self.diverge_colormap_var.get()
        self.logger.log(LogLevel.CALL, "カラーバー更新：発散部")
        diverge_photo = self._create_colorbar_image(diverge_cmap_name)
        self.diverge_colorbar_label.config(image=diverge_photo)
        self.diverge_colorbar_label.image = diverge_photo
        non_diverge_cmap_name = self.non_diverge_colormap_var.get()
        self.logger.log(LogLevel.CALL, "カラーバー更新：非発散部")
        non_diverge_photo = self._create_colorbar_image(non_diverge_cmap_name)
        self.non_diverge_colorbar_label.config(image=non_diverge_photo)
        self.non_diverge_colorbar_label.image = non_diverge_photo

    def _show_formula_display(self) -> None:
        """式を表示する"""
        fractal_type = self.fractal_type_var.get()
        if fractal_type == "Julia":
            self.formula_var.set("Z(n+1) = Z(n)² + C")
        else:
            self.formula_var.set("Z(n+1) = Z(n)² + C\n(Z(0)=0, C=座標)")

    def _get_parameters(self) -> dict:
        """パラメータを取得する
        Returns:
            dict: パラメータの辞書
        """
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
            if panel_params["max_iterations"] <= 0:
                self.logger.log(LogLevel.WARNING, "最大反復回数は正の整数である必要があります。")
                panel_params["max_iterations"] = 100
        except ValueError as e:
            self.logger.log(LogLevel.ERROR, f"パラメータ取得エラー: 無効な数値入力 - {e}")
            panel_params = {}
        return panel_params
