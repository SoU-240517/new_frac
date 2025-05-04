import matplotlib.pyplot as plt
import numpy as np
import tkinter as tk
from PIL import Image, ImageTk
from tkinter import ttk
from typing import Dict, Any, Optional, List, Callable
from debug import DebugLogger, LogLevel
from plugins.fractal_types.loader import FractalTypeLoader

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

    def __init__(self, parent, update_callback, reset_callback, logger: DebugLogger, config: Dict[str, Any], fractal_loader: FractalTypeLoader): # loader を追加
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
        # --- 追加 ---
        self.fractal_loader = fractal_loader # ローダーを保持
        self.current_plugin_params: List[Dict[str, Any]] = [] # 現在表示中のプラグインパラメータ設定
        self.param_vars: Dict[str, tk.StringVar] = {} # パラメータID -> StringVar の辞書
        self.param_widgets: Dict[str, tk.Widget] = {} # パラメータID -> Widget の辞書
        self.param_frame: Optional[ttk.Frame] = None # パラメータウィジェットを配置するフレーム
        # -----------
        self.render_mode = "quick"  # "quick" or "full"

        ui_settings = self.config.get("ui_settings", {})
        self.COLORBAR_WIDTH = ui_settings.get("colorbar_width", 150)
        self.COLORBAR_HEIGHT = ui_settings.get("colorbar_height", 15)
        self.logger.log(LogLevel.DEBUG, f"カラーバーサイズ設定完了: {self.COLORBAR_WIDTH}x{self.COLORBAR_HEIGHT}")

        # --- 追加: self.colormaps をここで初期化 ---
        # カラーマップリストを設定ファイルから取得
        self.colormaps = self.config.get("coloring_options", {}).get("available_colormaps", [])
        if not self.colormaps:
            # 設定ファイルにない、または空の場合のフォールバック処理
            self.logger.log(LogLevel.WARNING, "設定ファイルにカラーマップリストが見つからないか空なので、matplotlibから取得します。")
            try:
                # matplotlib がインストールされていない可能性も考慮
                # import matplotlib.pyplot as plt # ファイル先頭で import 済みなら不要
                # `_r` で終わるリバースカラーマップを除外してソートする
                self.colormaps = sorted([m for m in plt.colormaps() if not m.endswith('_r')])
            except ImportError:
                self.logger.log(LogLevel.ERROR, "matplotlib がインポートできませんでした。カラーマップリストは空になります。")
                self.colormaps = [] # matplotlib がない場合は空リスト
            except Exception as e:
                self.logger.log(LogLevel.ERROR, f"matplotlibからカラーマップ取得中にエラー: {e}")
                self.colormaps = [] # その他のエラーでも空リスト
        self.logger.log(LogLevel.DEBUG, f"カラーマップロード数: {len(self.colormaps)} 個")
        # -----------------------------------------

        self._setup_panel()
        self._update_colorbars() # 初期カラーバー表示

    def _setup_panel(self) -> None:
        """パネルのセットアップ
        - 各セクションのセットアップ
        - パネルのレイアウト設定
        """
#        self._setup_fractal_type_section()
#        self._setup_formula_section()
#        self._setup_parameter_section()

        # --- 変更: セクションの構成を変更 ---
        current_row = 0
        current_row = self._setup_fractal_type_section(current_row)
        current_row = self._setup_formula_section(current_row)
        # --- 追加: 動的パラメータ用フレーム ---
        current_row = self._setup_dynamic_parameter_frame(current_row)
        # ------------------------------------

        current_row = self._setup_diverge_section(current_row)
        current_row = self._setup_non_diverge_section(current_row)
        current_row = self._setup_buttons(current_row)
        self.parent.columnconfigure(1, weight=1) # これは parent (右側フレーム全体) に対する設定なので維持

        # --- 追加: 初期パラメータ表示のトリガー ---
        initial_type = self.fractal_type_var.get()
        if initial_type:
             self._on_fractal_type_selected() # 初期タイプのパラメータを表示
        # --------------------------------------


    def _setup_fractal_type_section(self, start_row: int) -> int:
        """フラクタルタイプセクションのセットアップ
        - ラベルとコンボボックスの追加
        - イベントバインド
        - 初期値を設定ファイルから読み込む
        """
        row = start_row
        self._add_label("フラクタルタイプ:", row, 0, pady=(5,0))

        # フラクタルタイプのデフォルト値を設定ファイルから取得
#        default_fractal_type = self.config.get("fractal_settings", {}).get("parameter_panel", {}).get("fractal_type", "Julia")
#        self.fractal_type_var = tk.StringVar(value=default_fractal_type)
        # フラクタルタイプのリストを設定ファイルから読み込む
#        fractal_types = self.config.get("fractal_settings", {}).get("available_fractal_types", [])

        # リストが空の場合のフォールバック
#        if not fractal_types:
#            self.logger.log(LogLevel.WARNING, "設定ファイルにフラクタルタイプリストが見つからないか空なので、デフォルトリストを使用")
#            fractal_types = ["Julia", "Mandelbrot"] # フォールバック

        # --- 変更: ローダーからタイプ一覧を取得 ---
        fractal_types = self.fractal_loader.get_available_types()
        if not fractal_types:
            self.logger.log(LogLevel.ERROR, "ロードされたフラクタルタイプがありません！")
            fractal_types = ["(ロード失敗)"] # エラー表示

        # デフォルト値もローダーから取得するか、config から読む
        default_fractal_type = self.config.get("fractal_settings", {}).get("parameter_panel", {}).get("fractal_type", None)
        # デフォルトがリストにない場合や未設定の場合は最初のタイプを選択
        if default_fractal_type not in fractal_types or default_fractal_type is None:
             default_fractal_type = fractal_types[0] if fractal_types else ""

        self.fractal_type_var = tk.StringVar(value=default_fractal_type)
        # ----------------------------------------

        combo = self._add_combobox(row, 1, self.fractal_type_var, fractal_types)
        # コンボボックス選択時と数式表示更新を紐付け
#        combo.bind("<<ComboboxSelected>>", lambda event: [self._common_callback(event), self._show_formula_display()])

        # --- 変更: コールバックを専用メソッドに ---
        combo.bind("<<ComboboxSelected>>", self._on_fractal_type_selected)
        # --------------------------------------

        return row + 1

    def _setup_formula_section(self, start_row: int) -> int:
        """数式表示セクションのセットアップ
        - 数式表示ラベルの追加
        - 数式の初期表示
        """
        row = start_row

        # 設定ファイルからフォント名とサイズを取得
        Panel_font = self.config.get("fractal_settings", {}).get("parameter_panel", {}).get("panel_font", "Courier")
        panel_font_size = self.config.get("fractal_settings", {}).get("parameter_panel", {}).get("panel_font_size", 10)

#        self.formula_var = tk.StringVar()
#        self.formula_label = ttk.Label(self.parent, textvariable=self.formula_var, font=(Panel_font, panel_font_size))
#        self.formula_label.grid(row=row, column=0, columnspan=2, sticky=tk.W, padx=10, pady=2)
#        self._show_formula_display() # 初期表示

        Panel_font = self.config.get("fractal_settings", {}).get("parameter_panel", {}).get("panel_font", "Courier")
        panel_font_size = self.config.get("fractal_settings", {}).get("parameter_panel", {}).get("panel_font_size", 10)
        self.formula_var = tk.StringVar()
        self.formula_label = ttk.Label(self.parent, textvariable=self.formula_var, font=(Panel_font, panel_font_size), wraplength=self.config.get("ui_settings",{}).get("parameter_panel_width", 300)-20) # 折返し追加
        self.formula_label.grid(row=row, column=0, columnspan=2, sticky=tk.W, padx=10, pady=2)
        # 初期表示は _on_fractal_type_selected で行う

        return row + 1

#    def _setup_parameter_section(self) -> None:
        """パラメータ表示セクションのセットアップ
        - 各パラメータのラベルと入力欄の追加
        - イベントバインド
        - 初期値を設定ファイルから読み込む
        """
#        row = self._formula_row + 1
#        param_defaults = self.config.get("fractal_settings", {}).get("parameter_panel", {})

        # 最大反復回数
 #       self._add_label("最大反復回数:", row, 0)
 #       default_max_iter = str(param_defaults.get("max_iterations", 100)) # 文字列に変換
 #       self.max_iter_var = tk.StringVar(value=default_max_iter)
 #       entry = self._add_entry(row, 1, self.max_iter_var)
 #       entry.bind("<Return>", self._common_callback) # Enterキーでクイック描画

        # Z と C のパラメータ
#        params_config = [
#            ("Z (実部):", "z_real_var", "z_real", "0.0"),
#            ("Z (虚部):", "z_imag_var", "z_imag", "0.0"),
#            ("C (実部):", "c_real_var", "c_real", "-0.7"),
#            ("C (虚部):", "c_imag_var", "c_imag", "0.27015")
#        ]

#        for label_text, var_name, config_key, fallback_default in params_config:
#            row += 1
#            self._add_label(label_text, row, 0)
            # 設定ファイルからデフォルト値を取得、なければフォールバック値
#            default_value = str(param_defaults.get(config_key, fallback_default)) # 文字列に変換
            # インスタンス変数として StringVar を設定
#            setattr(self, var_name, tk.StringVar(value=default_value))
            # _add_entry に渡すのはインスタンス変数
#            entry = self._add_entry(row, 1, getattr(self, var_name))
#            entry.bind("<Return>", self._common_callback) # Enterキーでクイック描画

#        self._param_section_last_row = row

    # --- 追加: 動的パラメータ用フレームのセットアップ ---
    def _setup_dynamic_parameter_frame(self, start_row: int) -> int:
        """動的にパラメータウィジェットを配置するためのフレームを作成"""
        row = start_row
#        ttk.Separator(self.parent).grid(row=row, column=0, columnspan=2, sticky="ew", padx=5, pady=5)
#        row += 1
        self.param_frame = ttk.Frame(self.parent)
        self.param_frame.grid(row=row, column=0, columnspan=2, sticky="nsew", padx=5)
        # フレーム内の列設定 (ラベルと入力欄)
        self.param_frame.columnconfigure(1, weight=1)
        return row + 1 # フレームが1行占有

    # --- 追加: フラクタルタイプ選択時の処理 ---
    def _on_fractal_type_selected(self, event=None) -> None:
        """フラクタルタイプが選択されたときに呼び出される"""
        selected_type_name = self.fractal_type_var.get()
        self.logger.log(LogLevel.INFO, f"フラクタルタイプ変更: {selected_type_name}")

        # 1. 以前のパラメータウィジェットを削除
        self._clear_dynamic_parameters()

        # 2. 選択されたタイプのパラメータ設定を取得
        self.current_plugin_params = self.fractal_loader.get_parameters_config(selected_type_name) or []
        self.logger.log(LogLevel.DEBUG, f"ロードされたパラメータ設定 ({selected_type_name}): {self.current_plugin_params}")

        # 3. 新しいパラメータウィジェットを生成
        if self.param_frame: # param_frame が作成されているか確認
            param_row = 0
            # --- 最大反復回数 (これは共通かもしれないので固定で置くか検討) ---
            self._add_label("最大反復回数:", param_row, 0, parent=self.param_frame)
            # デフォルト値は config かプラグインJSONか？ -> config優先
            default_max_iter = str(self.config.get("fractal_settings", {}).get("parameter_panel", {}).get("max_iterations", 100))
            # max_iter_var はクラス変数として持つ
            if not hasattr(self, 'max_iter_var'):
                 self.max_iter_var = tk.StringVar()
            self.max_iter_var.set(default_max_iter)
            entry = self._add_entry(param_row, 1, self.max_iter_var, parent=self.param_frame)
            entry.bind("<Return>", self._common_callback)
            param_row += 1
            # ------------------------------------------------------------

            # --- プラグイン固有パラメータ ---
            for param_config in self.current_plugin_params:
                param_id = param_config.get("id")
                param_label = param_config.get("label", param_id) # ラベルがなければIDを使う
                param_type = param_config.get("type", "string") # 型 (float, int, string 想定)
                param_default = str(param_config.get("default", "")) # デフォルト値 (文字列で)

                if not param_id:
                    self.logger.log(LogLevel.WARNING, f"パラメータ設定に 'id' がありません: {param_config}")
                    continue

                # ラベルを追加
                self._add_label(f"{param_label}:", param_row, 0, parent=self.param_frame)

                # StringVar を作成して辞書に保存
                var = tk.StringVar(value=param_default)
                self.param_vars[param_id] = var

                # 型に応じてウィジェットを作成 (今は Entry のみ)
                # TODO: type に応じてスライダーなどを追加する場合はここで分岐
                entry = self._add_entry(param_row, 1, var, parent=self.param_frame)
                entry.bind("<Return>", self._common_callback)

                # ウィジェットも辞書に保存 (削除用)
                # ラベルとEntryをセットで管理した方が良いかもしれない
                # ここでは Entry のみを保存
                self.param_widgets[param_id] = entry
                # self.param_widgets[f"{param_id}_label"] = label_widget # ラベルも保存する場合

                param_row += 1
            # -------------------------------

        # 4. 数式表示を更新
        description = self.fractal_loader.get_description(selected_type_name) or ""
        self.formula_var.set(description)

        # 5. (オプション) 推奨カラーリング設定を適用
        recommended = self.fractal_loader.get_recommended_coloring(selected_type_name)
        if recommended:
             self.logger.log(LogLevel.DEBUG, f"推奨カラーリング設定を適用: {recommended}")
             if recommended.get("divergent_algorithm"):
                 self.diverge_algo_var.set(recommended["divergent_algorithm"])
             if recommended.get("divergent_colormap"):
                 self.diverge_colormap_var.set(recommended["divergent_colormap"])
             if recommended.get("non_divergent_algorithm"):
                 self.non_diverge_algo_var.set(recommended["non_divergent_algorithm"])
             if recommended.get("non_divergent_colormap"):
                 self.non_diverge_colormap_var.set(recommended["non_divergent_colormap"])
             self._update_colorbars() # カラーバーも更新

        # 6. (重要) 変更を即時描画（クイックモードで）
        self._common_callback()

    # --- 追加: 動的パラメータウィジェットのクリア ---
    def _clear_dynamic_parameters(self) -> None:
        """param_frame 内のすべての動的ウィジェットを削除する"""
        if self.param_frame:
            for widget in self.param_frame.winfo_children():
                widget.destroy()
        self.param_vars.clear()
        self.param_widgets.clear()
        # max_iter_var はクリアしない（クラス変数として保持）
        self.logger.log(LogLevel.DEBUG, "動的パラメータウィジェットをクリア完了")

    # --- 変更: 各セクションのセットアップは row を返すように ---
    def _setup_diverge_section(self, start_row: int) -> int:
        """発散部セクションのセットアップ
        - 各ウィジェットの追加と設定
        - イベントバインド
        - 初期値とリストを設定ファイルから読み込む
        """
        row = start_row

        # --- セパレーター追加 ---
        ttk.Separator(self.parent).grid(row=row, column=0, columnspan=2, sticky="ew", padx=5, pady=5)
        row += 1
        # ----------------------

        self._add_label("--- 発散部 ---", row, 0, columnspan=2, pady=(10, 0))
        param_defaults = self.config.get("fractal_settings", {}).get("parameter_panel", {})
        fractal_settings = self.config.get("fractal_settings", {})

        # 着色アルゴリズム
        row += 1
        self._add_label("着色アルゴリズム:", row, 0, pady=(5,0))
        default_diverge_algo = param_defaults.get("diverge_algorithm", "スムージング")
#        self.diverge_algo_var = tk.StringVar(value=default_diverge_algo)
        # アルゴリズムリストを設定ファイルから取得

        if not hasattr(self, 'diverge_algo_var'):
             self.diverge_algo_var = tk.StringVar()
        self.diverge_algo_var.set(default_diverge_algo)

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
        if not hasattr(self, 'diverge_colorbar_label'):
            self.diverge_colorbar_label = tk.Label(self.parent)
            self.diverge_colorbar_label.grid(row=row, column=1, sticky=tk.W, padx=10, pady=(5,0))

        # カラーマップ選択
        row += 1
        self._add_label("カラーマップ:", row, 0, pady=(2,5))
        default_diverge_cmap = param_defaults.get("diverge_colormap", "viridis")

        # diverge_colormap_var はクラス変数として持つ
        if not hasattr(self, 'diverge_colormap_var'):
             self.diverge_colormap_var = tk.StringVar()
        self.diverge_colormap_var.set(default_diverge_cmap)
        # カラーマップリストは共通なので再利用
        combo = self._add_combobox(row, 1, self.diverge_colormap_var, self.colormaps, width=18)
        combo.bind("<<ComboboxSelected>>", self._common_callback)

#        self.diverge_colormap_var = tk.StringVar(value=default_diverge_cmap)
        # カラーマップリストを設定ファイルから取得
#        self.colormaps = self.config.get("coloring_options", {}).get("available_colormaps", [])
         # リストが空の場合のフォールバック
#        if not self.colormaps:
#            self.logger.log(LogLevel.WARNING, "設定ファイルにカラーマップリストが見つからないか空なので、matplotlibから取得")
#            self.colormaps = sorted([m for m in plt.colormaps() if not m.endswith('_r')]) # フォールバック
#        combo = self._add_combobox(row, 1, self.diverge_colormap_var, self.colormaps, width=18)
#        combo.bind("<<ComboboxSelected>>", self._common_callback)

        return row + 1

    def _setup_non_diverge_section(self, start_row: int) -> int:
        """非発散部セクションのセットアップ
        - 各ウィジェットの追加と設定
        - イベントバインド
        - 初期値とリストを設定ファイルから読み込む
        """
        row = start_row

        # --- セパレーター追加 ---
        ttk.Separator(self.parent).grid(row=row, column=0, columnspan=2, sticky="ew", padx=5, pady=5)
        row += 1
        # ----------------------

        self._add_label("--- 非発散部 ---", row, 0, columnspan=2, pady=(10, 0))
        param_defaults = self.config.get("fractal_settings", {}).get("parameter_panel", {})
        fractal_settings = self.config.get("fractal_settings", {})

        # 着色アルゴリズム
        row += 1
        self._add_label("着色アルゴリズム:", row, 0, pady=(5,0))
        default_non_diverge_algo = param_defaults.get("non_diverge_algorithm", "単色")

        # non_diverge_algo_var はクラス変数として持つ
        if not hasattr(self, 'non_diverge_algo_var'):
             self.non_diverge_algo_var = tk.StringVar()
        self.non_diverge_algo_var.set(default_non_diverge_algo)

#        self.non_diverge_algo_var = tk.StringVar(value=default_non_diverge_algo)

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
#        row += 1
#        self.non_diverge_colorbar_label = tk.Label(self.parent)
#        self.non_diverge_colorbar_label.grid(row=row, column=1, sticky=tk.W, padx=10, pady=(5,0))

        # カラーバー表示用ラベル
        row += 1
        # non_diverge_colorbar_label はクラス変数として持つ
        if not hasattr(self, 'non_diverge_colorbar_label'):
             self.non_diverge_colorbar_label = tk.Label(self.parent)
             self.non_diverge_colorbar_label.grid(row=row, column=1, sticky=tk.W, padx=10, pady=(5,0))

        # カラーマップ選択
#        row += 1
#        self._add_label("カラーマップ:", row, 0, pady=(2,5))
#        default_non_diverge_cmap = param_defaults.get("non_diverge_colormap", "magma")
#        self.non_diverge_colormap_var = tk.StringVar(value=default_non_diverge_cmap)
        # カラーマップリストは発散部と共通なので再利用
#        combo = self._add_combobox(row, 1, self.non_diverge_colormap_var, self.colormaps, width=18)
#        combo.bind("<<ComboboxSelected>>", self._common_callback)

        # カラーマップ選択
        row += 1
        self._add_label("カラーマップ:", row, 0, pady=(2,5))
        default_non_diverge_cmap = param_defaults.get("non_diverge_colormap", "magma")
        # non_diverge_colormap_var はクラス変数として持つ
        if not hasattr(self, 'non_diverge_colormap_var'):
             self.non_diverge_colormap_var = tk.StringVar()
        self.non_diverge_colormap_var.set(default_non_diverge_cmap)
        # カラーマップリストは共通なので再利用
        combo = self._add_combobox(row, 1, self.non_diverge_colormap_var, self.colormaps, width=18)
        combo.bind("<<ComboboxSelected>>", self._common_callback)

        return row + 1

    def _setup_buttons(self, start_row: int) -> int:
        """ボタンのセットアップ
        - 描画ボタンと描画リセットボタンの追加
        - 各ボタンのコールバック設定
        """
        row = start_row

        # --- セパレーター追加 ---
        ttk.Separator(self.parent).grid(row=row, column=0, columnspan=2, sticky="ew", padx=5, pady=5)
        row += 1
        # ----------------------

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

        return row + 1

    def _add_label(self, text, row, col, columnspan=1, padx=10, pady=2, parent=None) -> ttk.Label:
        """ラベルを追加 (parent を指定可能に)"""
        target_parent = parent if parent else self.parent
        label = ttk.Label(target_parent, text=text)
        label.grid(
            row=row, column=col, columnspan=columnspan, sticky=tk.W, padx=padx, pady=pady)
        return label # ラベルウィジェットを返すように変更 (必要であれば)

    def _add_entry(self, row, col, var, padx=10, pady=2, parent=None) -> ttk.Entry:
        """入力欄を追加 (parent を指定可能に)"""
        target_parent = parent if parent else self.parent
        entry = ttk.Entry(target_parent, textvariable=var)
        entry.grid(row=row, column=col, sticky=tk.W+tk.E, padx=padx, pady=pady)
        return entry

    def _add_combobox(self, row, col, var, values, width=None, padx=10, pady=2, parent=None) -> ttk.Combobox:
        """コンボボックスを追加 (parent を指定可能に)"""
        target_parent = parent if parent else self.parent
        kwargs = {"textvariable": var, "values": values, "state": "readonly"}
        if width:
            kwargs["width"] = width
        combo = ttk.Combobox(target_parent, **kwargs)
        combo.grid(row=row, column=col, sticky=tk.W, padx=padx, pady=pady)
        return combo

    def _add_button(self, text, row, col, colspan, command, parent=None) -> ttk.Button:
        """ボタンを追加 (parent を指定可能に)"""
        target_parent = parent if parent else self.parent
        btn = ttk.Button(target_parent, text=text, command=command)
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

#    def _show_formula_display(self) -> None:
        """数式を表示する
        - 選択されたフラクタルタイプに応じて数式を更新する
        """
#        fractal_type = self.fractal_type_var.get()
#        if fractal_type == "Julia":
#            self.formula_var.set("Z(n+1) = Z(n)² + C")
#        elif fractal_type == "Mandelbrot":
#            self.formula_var.set("Z(n+1) = Z(n)² + C\n(Z(0)=0, C=座標)")
#        else:
#            self.formula_var.set("") # 未知のタイプの場合は空に

    def get_parameters(self) -> Optional[Dict[str, Any]]:
        """現在のパネル設定を取得する (動的パラメータ対応)

        Returns:
            Optional[Dict[str, Any]]: パラメータ辞書、またはエラー時は None
        """
        panel_params: Dict[str, Any] = {}
        try:
            # 1. フラクタルタイプ名
            selected_type_name = self.fractal_type_var.get()
            if not selected_type_name or selected_type_name == "(ロード失敗)":
                self.logger.log(LogLevel.ERROR, "有効なフラクタルタイプが選択されていません。")
                return None
            panel_params["fractal_type_name"] = selected_type_name # MainWindow で計算関数取得に使用

            # 2. 最大反復回数 (これは共通)
            max_iter_str = self.max_iter_var.get()
            max_iterations = int(max_iter_str)
            if max_iterations <= 0:
                self.logger.log(LogLevel.WARNING, f"最大反復回数({max_iterations})は正の整数が必要なので、100に補正")
                max_iterations = 100
            panel_params["max_iterations"] = max_iterations

            # 3. 動的に生成されたパラメータを取得
            plugin_params_config = self.fractal_loader.get_parameters_config(selected_type_name) or []
            dynamic_params: Dict[str, Any] = {}
            for param_config in plugin_params_config:
                param_id = param_config.get("id")
                param_type = param_config.get("type", "string")
                if param_id and param_id in self.param_vars:
                    value_str = self.param_vars[param_id].get()
                    # 型変換
                    try:
                        if param_type == "float":
                            dynamic_params[param_id] = float(value_str)
                        elif param_type == "int":
                            dynamic_params[param_id] = int(value_str)
                        else: # string or other
                            dynamic_params[param_id] = value_str
                    except ValueError:
                        self.logger.log(LogLevel.ERROR, f"パラメータ '{param_id}' の値 '{value_str}' を型 '{param_type}' に変換できません。")
                        # エラー時の処理: デフォルト値を使うか、None を返すか
                        # ここではエラーとして None を返す
                        return None
                else:
                    self.logger.log(LogLevel.WARNING, f"パラメータ '{param_id}' の値を取得できませんでした。")
                    # return None # 取得できないパラメータがあればエラーにする

            # panel_params に動的パラメータをマージ
            panel_params.update(dynamic_params)
            # 例: Julia なら panel_params["c_real"] = ..., panel_params["c_imag"] = ... が入る
            # 例: Mandelbrot なら panel_params["z0_real"] = ..., panel_params["z0_imag"] = ... が入る

            # 4. 着色関連のパラメータ (これらは固定)
            panel_params["diverge_algorithm"] = self.diverge_algo_var.get()
            panel_params["non_diverge_algorithm"] = self.non_diverge_algo_var.get()
            panel_params["diverge_colormap"] = self.diverge_colormap_var.get()
            panel_params["non_diverge_colormap"] = self.non_diverge_colormap_var.get()

            self.logger.log(LogLevel.SUCCESS, "パラメータ取得成功", context=panel_params)
            return panel_params

        except ValueError as e:
            self.logger.log(LogLevel.ERROR, f"パラメータ取得エラー: 無効な数値入力 - {e}。UIの値を要確認")
            return None
        except Exception as e:
            self.logger.log(LogLevel.CRITICAL, f"パラメータ取得中に予期せぬエラー: {e}")
            return None

    # --- 追加: デフォルト状態に戻すメソッド ---
    def reset_to_defaults(self, default_type_name: str) -> None:
        """パネルを指定されたフラクタルタイプのデフォルト状態に戻す"""
        self.logger.log(LogLevel.CALL, f"パラメータパネルを '{default_type_name}' のデフォルトにリセット")

        # 1. フラクタルタイプを選択
        available_types = self.fractal_loader.get_available_types()
        if default_type_name in available_types:
            self.fractal_type_var.set(default_type_name)
            # タイプ選択イベントを発火させて、パラメータ欄と推奨設定を更新
            self._on_fractal_type_selected()
        else:
            self.logger.log(LogLevel.WARNING, f"指定されたデフォルトタイプ '{default_type_name}' が見つかりません。リセットできません。")
            return # ここで処理中断

        # 2. 最大反復回数を config のリセット値に設定
        reset_iter = self.config.get("fractal_settings", {}).get("reset_max_iterations", 200)
        self.max_iter_var.set(str(reset_iter))

        # 3. (オプション) カラーリングも config のデフォルト値に戻す (推奨設定ではなく)
        param_defaults = self.config.get("fractal_settings", {}).get("parameter_panel", {})
        self.diverge_algo_var.set(param_defaults.get("diverge_algorithm", "スムージング"))
        self.diverge_colormap_var.set(param_defaults.get("diverge_colormap", "viridis"))
        self.non_diverge_algo_var.set(param_defaults.get("non_diverge_algorithm", "単色"))
        self.non_diverge_colormap_var.set(param_defaults.get("non_diverge_colormap", "magma"))
        self._update_colorbars()

        self.logger.log(LogLevel.SUCCESS, "パラメータパネルのリセット完了")
