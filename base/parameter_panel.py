import matplotlib.pyplot as plt
import numpy as np
import tkinter as tk
from PIL import Image, ImageTk
from tkinter import ttk
from typing import Dict, Any # 型ヒント用
from debug.debug_logger import DebugLogger
from debug.enum_debug import LogLevel

class ParameterPanel:
    """ParameterPanel クラス
    - フラクタル生成用のパラメータを設定するパネル
    Attributes:
        parent: 親ウィジェット
        update_callback: 描画更新コールバック関数
        reset_callback: 描画リセットコールバック関数
        logger: デバッグロガーインスタンス
        render_mode: 描画モード ("quick" or "full")
        fractal_type_var: フラクタルタイプの選択 (tk.StringVar)
        formula_var: 数式表示 (tk.StringVar)
        formula_label: 数式表示ラベル (ttk.Label)
        max_iter_var: 最大反復回数 (tk.StringVar)
        z_real_var: Z (実部) (tk.StringVar)
        z_imag_var: Z (虚部) (tk.StringVar)
        c_real_var: C (実部) (tk.StringVar)
        c_imag_var: C (虚部) (tk.StringVar)
        diverge_algo_var: 発散部着色アルゴリズム (tk.StringVar)
        diverge_colorbar_label: 発散部カラーバー表示ラベル (tk.Label)
        diverge_colormap_var: 発散部カラーマップ (tk.StringVar)
        non_diverge_algo_var: 非発散部着色アルゴリズム (tk.StringVar)
        non_diverge_colorbar_label: 非発散部カラーバー表示ラベル (tk.Label)
        non_diverge_colormap_var: 非発散部カラーマップ (tk.StringVar)
        _fractal_type_row: フラクタルタイプ選択行
        _formula_row: 数式表示行
        _param_section_last_row: パラメータセクション最終行
        _diverge_section_last_row: 発散部セクション最終行
        _non_diverge_section_last_row: 非発散部セクション最終行
        colormaps: カラーマップリスト
        diverge_algorithms: 発散部アルゴリズムリスト
        non_diverge_algorithms: 非発散部アルゴリズムリスト
        COLORBAR_WIDTH: カラーバー幅
        COLORBAR_HEIGHT: カラーバー高さ
        config (dict): config.json から読み込んだ設定データ
    """

    def __init__(self, parent, update_callback, reset_callback, logger: DebugLogger, config: Dict[str, Any]):
        """ParameterPanel クラスのコンストラクタ
        - パネルのセットアップ
        - カラーバーの初期化

        Args:
            parent: 親ウィジェット
            update_callback: 描画更新コールバック関数
            reset_callback: 描画リセットコールバック関数
            logger: デバッグロガーインスタンス
            config (Dict[str, Any]): config.json から読み込んだ設定データ
        """
        self.logger = logger
        self.parent = parent
        self.config = config # 設定データをインスタンス変数に保存
        self.update_callback = update_callback
        self.reset_callback = reset_callback
        self.render_mode = "quick"  # "quick" or "full"

        ui_settings = self.config.get("ui_settings", {})
        self.COLORBAR_WIDTH = ui_settings.get("colorbar_width", 150)
        self.COLORBAR_HEIGHT = ui_settings.get("colorbar_height", 15)
        self.logger.log(LogLevel.DEBUG, f"カラーバーサイズ設定完了: {self.COLORBAR_WIDTH}x{self.COLORBAR_HEIGHT}")

        self._setup_panel()
        self._update_colorbars() # 初期カラーバー表示

    def _setup_panel(self) -> None:
        """パネルのセットアップ
        - 各セクションのセットアップ
        - パネルのレイアウト設定
        """
        self._setup_fractal_type_section()
        self._setup_formula_section()
        self._setup_parameter_section()
        self._setup_diverge_section()
        self._setup_non_diverge_section()
        self._setup_buttons()
        self.parent.columnconfigure(1, weight=1)

    def _setup_fractal_type_section(self) -> None:
        """フラクタルタイプセクションのセットアップ
        - ラベルとコンボボックスの追加
        - イベントバインド
        - 初期値を設定ファイルから読み込む
        """
        row = 0
        self._add_label("フラクタルタイプ:", row, 0, pady=(5,0))

        # フラクタルタイプのデフォルト値を設定ファイルから取得
        default_fractal_type = self.config.get("fractal_settings", {}).get("parameter_panel", {}).get("fractal_type", "Julia")
        self.fractal_type_var = tk.StringVar(value=default_fractal_type)
        # フラクタルタイプのリストを設定ファイルから読み込む
        fractal_types = self.config.get("fractal_settings", {}).get("available_fractal_types", [])

        # リストが空の場合のフォールバック
        if not fractal_types:
            self.logger.log(LogLevel.WARNING, "設定ファイルにフラクタルタイプリストが見つからないか空なので、デフォルトリストを使用")
            fractal_types = ["Julia", "Mandelbrot"] # フォールバック

        combo = self._add_combobox(row, 1, self.fractal_type_var, fractal_types)
        # コンボボックス選択時と数式表示更新を紐付け
        combo.bind("<<ComboboxSelected>>", lambda event: [self._common_callback(event), self._show_formula_display()])
        self._fractal_type_row = row

    def _setup_formula_section(self) -> None:
        """数式表示セクションのセットアップ
        - 数式表示ラベルの追加
        - 数式の初期表示
        """
        row = self._fractal_type_row + 1

        # 設定ファイルからフォント名とサイズを取得
        Panel_font = self.config.get("fractal_settings", {}).get("parameter_panel", {}).get("panel_font", "Courier")
        panel_font_size = self.config.get("fractal_settings", {}).get("parameter_panel", {}).get("panel_font_size", 10)

        self.formula_var = tk.StringVar()
        self.formula_label = ttk.Label(self.parent, textvariable=self.formula_var, font=(Panel_font, panel_font_size))
        self.formula_label.grid(row=row, column=0, columnspan=2, sticky=tk.W, padx=10, pady=2)
        self._show_formula_display() # 初期表示
        self._formula_row = row

    def _setup_parameter_section(self) -> None:
        """パラメータ表示セクションのセットアップ
        - 各パラメータのラベルと入力欄の追加
        - イベントバインド
        - 初期値を設定ファイルから読み込む
        """
        row = self._formula_row + 1
        param_defaults = self.config.get("fractal_settings", {}).get("parameter_panel", {})

        # 最大反復回数
        self._add_label("最大反復回数:", row, 0)
        default_max_iter = str(param_defaults.get("max_iterations", 100)) # 文字列に変換
        self.max_iter_var = tk.StringVar(value=default_max_iter)
        entry = self._add_entry(row, 1, self.max_iter_var)
        entry.bind("<Return>", self._common_callback) # Enterキーでクイック描画

        # Z と C のパラメータ
        params_config = [
            ("Z (実部):", "z_real_var", "z_real", "0.0"),
            ("Z (虚部):", "z_imag_var", "z_imag", "0.0"),
            ("C (実部):", "c_real_var", "c_real", "-0.7"),
            ("C (虚部):", "c_imag_var", "c_imag", "0.27015")
        ]

        for label_text, var_name, config_key, fallback_default in params_config:
            row += 1
            self._add_label(label_text, row, 0)
            # 設定ファイルからデフォルト値を取得、なければフォールバック値
            default_value = str(param_defaults.get(config_key, fallback_default)) # 文字列に変換
            # インスタンス変数として StringVar を設定
            setattr(self, var_name, tk.StringVar(value=default_value))
            # _add_entry に渡すのはインスタンス変数
            entry = self._add_entry(row, 1, getattr(self, var_name))
            entry.bind("<Return>", self._common_callback) # Enterキーでクイック描画

        self._param_section_last_row = row

    def _setup_diverge_section(self) -> None:
        """発散部セクションのセットアップ
        - 各ウィジェットの追加と設定
        - イベントバインド
        - 初期値とリストを設定ファイルから読み込む
        """
        row = self._param_section_last_row + 1
        self._add_label("--- 発散部 ---", row, 0, columnspan=2, pady=(10, 0))
        param_defaults = self.config.get("fractal_settings", {}).get("parameter_panel", {})
        fractal_settings = self.config.get("fractal_settings", {})

        # 着色アルゴリズム
        row += 1
        self._add_label("着色アルゴリズム:", row, 0, pady=(5,0))
        default_diverge_algo = param_defaults.get("diverge_algorithm", "スムージング")
        self.diverge_algo_var = tk.StringVar(value=default_diverge_algo)
        # アルゴリズムリストを設定ファイルから取得
        self.diverge_algorithms = list(fractal_settings.get("coloring_algorithms", {}).get("divergent", {}).keys())
        if not self.diverge_algorithms:
            self.logger.log(LogLevel.WARNING, "設定ファイルに発散部アルゴリズムリストが見つからないか空なので、デフォルトリストを使用")
            self.diverge_algorithms = [
                "スムージング",
                "高速スムージング",
                "指数スムージング",
                "反復回数線形マッピング",
                "反復回数対数マッピング",
                "ヒストグラム平坦化法",
                "距離カラーリング",
                "角度カラーリング",
                "ポテンシャル関数法",
                "軌道トラップ法"
            ] # フォールバック
        combo = self._add_combobox(row, 1, self.diverge_algo_var, self.diverge_algorithms)
        combo.bind("<<ComboboxSelected>>", self._common_callback)

        # カラーバー表示用ラベル
        row += 1
        self.diverge_colorbar_label = tk.Label(self.parent)
        self.diverge_colorbar_label.grid(row=row, column=1, sticky=tk.W, padx=10, pady=(5,0))

        # カラーマップ選択
        row += 1
        self._add_label("カラーマップ:", row, 0, pady=(2,5))
        default_diverge_cmap = param_defaults.get("diverge_colormap", "viridis")
        self.diverge_colormap_var = tk.StringVar(value=default_diverge_cmap)
        # カラーマップリストを設定ファイルから取得
        self.colormaps = self.config.get("coloring_options", {}).get("available_colormaps", [])
         # リストが空の場合のフォールバック
        if not self.colormaps:
            self.logger.log(LogLevel.WARNING, "設定ファイルにカラーマップリストが見つからないか空なので、matplotlibから取得")
            self.colormaps = sorted([m for m in plt.colormaps() if not m.endswith('_r')]) # フォールバック
        combo = self._add_combobox(row, 1, self.diverge_colormap_var, self.colormaps, width=18)
        combo.bind("<<ComboboxSelected>>", self._common_callback)

        self._diverge_section_last_row = row

    def _setup_non_diverge_section(self) -> None:
        """非発散部セクションのセットアップ
        - 各ウィジェットの追加と設定
        - イベントバインド
        - 初期値とリストを設定ファイルから読み込む
        """
        row = self._diverge_section_last_row + 1
        self._add_label("--- 非発散部 ---", row, 0, columnspan=2, pady=(10, 0))
        param_defaults = self.config.get("fractal_settings", {}).get("parameter_panel", {})
        fractal_settings = self.config.get("fractal_settings", {})

        # 着色アルゴリズム
        row += 1
        self._add_label("着色アルゴリズム:", row, 0, pady=(5,0))
        default_non_diverge_algo = param_defaults.get("non_diverge_algorithm", "単色")
        self.non_diverge_algo_var = tk.StringVar(value=default_non_diverge_algo)
        # アルゴリズムリストを設定ファイルから取得
        self.non_diverge_algorithms = list(fractal_settings.get("coloring_algorithms", {}).get("non_divergent", {}).keys())
        if not self.non_diverge_algorithms:
            self.logger.log(LogLevel.WARNING, "設定ファイルに非発散部アルゴリズムリストが見つからないか空なので、デフォルトリストを使用")
            self.non_diverge_algorithms = [
                "単色",
                "グラデーション",
                "内部距離（Escape Time Distance）",
                "軌道トラップ(円)（Orbit Trap Coloring）",
                "位相对称（Phase Angle Symmetry）",
                "反復収束速度（Convergence Speed）",
                "微分係数（Derivative Coloring）",
                "統計分布（Histogram Equalization）",
                "複素ポテンシャル（Complex Potential Mapping）",
                "カオス軌道混合（Chaotic Orbit Mixing）",
                "フーリエ干渉（Fourier Pattern）",
                "フラクタルテクスチャ（Fractal Texture）",
                "量子もつれ（Quantum Entanglement）",
                "パラメータ(C)",
                "パラメータ(Z)"
            ] # フォールバック
        combo = self._add_combobox(row, 1, self.non_diverge_algo_var, self.non_diverge_algorithms)
        combo.bind("<<ComboboxSelected>>", self._common_callback)

        # カラーバー表示用ラベル
        row += 1
        self.non_diverge_colorbar_label = tk.Label(self.parent)
        self.non_diverge_colorbar_label.grid(row=row, column=1, sticky=tk.W, padx=10, pady=(5,0))

        # カラーマップ選択
        row += 1
        self._add_label("カラーマップ:", row, 0, pady=(2,5))
        default_non_diverge_cmap = param_defaults.get("non_diverge_colormap", "magma")
        self.non_diverge_colormap_var = tk.StringVar(value=default_non_diverge_cmap)
        # カラーマップリストは発散部と共通なので再利用
        combo = self._add_combobox(row, 1, self.non_diverge_colormap_var, self.colormaps, width=18)
        combo.bind("<<ComboboxSelected>>", self._common_callback)

        self._non_diverge_section_last_row = row

    def _setup_buttons(self) -> None:
        """ボタンのセットアップ
        - 描画ボタンと描画リセットボタンの追加
        - 各ボタンのコールバック設定
        """
        row = self._non_diverge_section_last_row + 1
        # 「描画」ボタン - フル描画モード
        # コールバック内で render_mode を設定し、update_callback を呼び出す
        self._add_button(
            "描画", row, 0, 2,
            lambda: [
                setattr(self, 'render_mode', 'full'), # フル描画モードに設定
                self.logger.log(LogLevel.INFO, "描画ボタンクリック: フル描画モード"),
                self.update_callback() # 描画更新
            ]
        )
        row += 1
        if self.reset_callback is not None:
            # 「描画リセット」ボタン - クイック描画モード
            # コールバック内で render_mode を設定し、reset_callback を呼び出す
            self._add_button(
                "描画リセット", row, 0, 2,
                lambda: [
                    setattr(self, 'render_mode', 'quick'), # クイック描画モードに設定
                    self.logger.log(LogLevel.INFO, "描画リセットボタンクリック: クイック描画モード"),
                    self.reset_callback() # リセット処理
                ]
            )

    def _add_label(self, text, row, col, columnspan=1, padx=10, pady=2) -> None:
        """ラベルを追加する

        Args:
            text: ラベルのテキスト
            row: 行
            col: 列
            columnspan: 列のスパン
            padx: 横方向のパディング
            pady: 縦方向のパディング
        """
        ttk.Label(self.parent, text=text).grid(
            row=row, column=col, columnspan=columnspan, sticky=tk.W, padx=padx, pady=pady)

    def _add_entry(self, row, col, var, padx=10, pady=2) -> ttk.Entry:
        """入力欄を追加する

        Args:
            row: 行
            col: 列
            var: 文字列変数
            padx: 横方向のパディング
            pady: 縦方向のパディング

        Returns:
            ttk.Entry: 追加された入力欄
        """
        entry = ttk.Entry(self.parent, textvariable=var)
        entry.grid(row=row, column=col, sticky=tk.W+tk.E, padx=padx, pady=pady)
        return entry

    def _add_combobox(self, row, col, var, values, width=None, padx=10, pady=2) -> ttk.Combobox:
        """コンボボックスを追加する

        Args:
            row: 行
            col: 列
            var: 文字列変数
            values: コンボボックスの値リスト
            width: コンボボックスの幅
            padx: 横方向のパディング
            pady: 縦方向のパディング

        Returns:
            ttk.Combobox: 追加されたコンボボックス
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
            text: ボタンのテキスト
            row: 行
            col: 列
            colspan: 列のスパン
            command: コマンド

        Returns:
            ttk.Button: 追加されたボタン
        """
        btn = ttk.Button(self.parent, text=text, command=command)
        btn.grid(row=row, column=col, columnspan=colspan, sticky=tk.W+tk.E, padx=10, pady=10)
        return btn

    def _common_callback(self, event=None) -> None:
        """共通のコールバック関数
        - 描画モードをクイックに設定
        - 描画更新コールバックを呼び出し
        - カラーバーを更新
        - 数式表示を更新
        """
        self.render_mode = "quick"  # 簡易描画モードに設定
        self.logger.log(LogLevel.INFO, f"UI操作イベント: クイック描画モード設定 ({event})")
        self.update_callback()      # 描画更新をトリガー
        self._update_colorbars()    # カラーバーを更新

    def _create_colorbar_image(self, cmap_name: str) -> ImageTk.PhotoImage:
        """カラーバー画像を生成する

        Args:
            cmap_name: カラーマップ名

        Returns:
            ImageTk.PhotoImage: カラーバー画像のPhotoImageオブジェクト
        """
        try:
            cmap = plt.get_cmap(cmap_name)
            gradient = np.linspace(0, 1, self.COLORBAR_WIDTH) # インスタンス変数を使用
            colors = cmap(gradient)
            # タイルする高さもインスタンス変数を使用
            rgba_image = np.uint8(np.tile(colors, (self.COLORBAR_HEIGHT, 1, 1)) * 255)
            pil_image = Image.fromarray(rgba_image, 'RGBA')
            photo_image = ImageTk.PhotoImage(pil_image)
            self.logger.log(LogLevel.DEBUG, f"カラーバー生成完了: {cmap_name}")
            return photo_image
        except ValueError:
            self.logger.log(LogLevel.WARNING, f"無効なカラーマップ名: {cmap_name}：ダミー画像を表示する")
             # ダミー画像生成 (サイズはインスタンス変数から)
            dummy_rgba = np.zeros((self.COLORBAR_HEIGHT, self.COLORBAR_WIDTH, 4), dtype=np.uint8)
            dummy_rgba[:, :, 0] = 128 # 灰色など、エラーを示す色にしても良い
            dummy_rgba[:, :, 3] = 255 # 不透明
            pil_image = Image.fromarray(dummy_rgba, 'RGBA')
            photo_image = ImageTk.PhotoImage(pil_image)
            return photo_image
        except Exception as e:
            self.logger.log(LogLevel.ERROR, f"カラーバー生成中に予期せぬエラー ({cmap_name}): {e}")
            # ダミー画像生成
            dummy_rgba = np.zeros((self.COLORBAR_HEIGHT, self.COLORBAR_WIDTH, 4), dtype=np.uint8)
            pil_image = Image.fromarray(dummy_rgba, 'RGBA')
            photo_image = ImageTk.PhotoImage(pil_image)
            return photo_image

    def _update_colorbars(self, *args) -> None:
        """カラーバーを更新する
        - 発散部と非発散部のカラーバー画像を生成し、ラベルに設定する
        """
        # 発散部のカラーバー画像を生成
        diverge_cmap_name = self.diverge_colormap_var.get()
        diverge_photo = self._create_colorbar_image(diverge_cmap_name)
        self.diverge_colorbar_label.config(image=diverge_photo)
        # self.diverge_colorbar_label.image に参照を保持しないとガベージコレクションされる
        self.diverge_colorbar_label.image = diverge_photo

        # 非発散部のカラーバー画像を生成
        non_diverge_cmap_name = self.non_diverge_colormap_var.get()
        non_diverge_photo = self._create_colorbar_image(non_diverge_cmap_name)
        self.non_diverge_colorbar_label.config(image=non_diverge_photo)
        # self.diverge_colorbar_label.image に参照を保持しないとガベージコレクションされる
        self.non_diverge_colorbar_label.image = non_diverge_photo

    def _show_formula_display(self) -> None:
        """数式を表示する
        - 選択されたフラクタルタイプに応じて数式を更新する
        """
        fractal_type = self.fractal_type_var.get()
        if fractal_type == "Julia":
            self.formula_var.set("Z(n+1) = Z(n)² + C")
        elif fractal_type == "Mandelbrot":
            self.formula_var.set("Z(n+1) = Z(n)² + C\n(Z(0)=0, C=座標)")
        else:
            self.formula_var.set("") # 未知のタイプの場合は空に

    def _get_parameters(self) -> dict:
        """パラメータを取得する
        - パネル上のウィジェットから現在のパラメータを取得し、辞書として返す

        Returns:
            dict: パラメータの辞書
                - fractal_type: フラクタルタイプ (str)
                - max_iterations: 最大反復回数 (int)
                - z_real: Zの実部 (float)
                - z_imag: Zの虚部 (float)
                - c_real: Cの実部 (float)
                - c_imag: Cの虚部 (float)
                - diverge_algorithm: 発散部アルゴリズム (str)
                - non_diverge_algorithm: 非発散部アルゴリズム (str)
                - diverge_colormap: 発散部カラーマップ (str)
                - non_diverge_colormap: 非発散部カラーマップ (str)
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
            # 最大反復回数が正かチェック
            if panel_params["max_iterations"] <= 0:
                self.logger.log(LogLevel.WARNING, f"最大反復回数({panel_params['max_iterations']})は正の整数が必要なので、100に補正")
                panel_params["max_iterations"] = 100 # 強制的にデフォルト値に

            self.logger.log(LogLevel.SUCCESS, "パラメータ取得成功", context=panel_params)
            return panel_params
        except ValueError as e:
            # tk.messagebox などでユーザーに通知しても良い
            self.logger.log(LogLevel.ERROR, f"パラメータ取得エラー: 無効な数値入力 - {e}。UIの値を要確認")
            # ここでNoneや空辞書を返すと描画が中断される (MainWindow側でハンドリング)
            return None # エラーがあった場合は None を返す
        except Exception as e:
            self.logger.log(LogLevel.CRITICAL, f"パラメータ取得中に予期せぬエラー: {e}")
            return None
