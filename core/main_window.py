import json
import numpy as np
import os
import threading
import tkinter as tk
from tkinter import ttk
from debug import DebugLogger, LogLevel
from plugins.fractal_types.loader import FractalTypeLoader
from .canvas import FractalCanvas
from .parameter_panel import ParameterPanel
from .render import render_fractal
from .status_bar import StatusBarManager

def load_config(logger: DebugLogger, config_path: str) -> dict:
    """
    設定ファイル (JSON) を読み込む

    Args:
        logger (DebugLogger): デバッグログ用インスタンス
        config_path (str): 読み込む設定ファイルのパス

    Returns:
        dict: 読み込んだ設定データ
            設定ファイルが見つからない、または読み込みに失敗した場合は空の辞書を返す

    Raises:
        json.JSONDecodeError: JSON データの解析に失敗した場合
        Exception: その他の予期せぬエラーが発生した場合
    """
    if not os.path.exists(config_path):
        logger.log(LogLevel.ERROR, f"設定ファイルが見つかりません: {config_path}")
        # デフォルト設定を返すか、エラーを発生させるかを選択
        # ここでは空の辞書を返し、呼び出し元でデフォルト値を使う想定
        return {}

    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
            logger.log(LogLevel.SUCCESS, f"設定ファイル読込成功: {config_path}")
            return config
    except json.JSONDecodeError as e:
        logger.log(LogLevel.ERROR, f"設定ファイルの JSON 解析エラー: {e}")
        return {}
    except Exception as e:
        logger.log(LogLevel.ERROR, f"設定ファイル読み込み中に予期せぬエラー: {e}")
        return {}

class MainWindow:
    """
    アプリケーションのメインウィンドウを管理するクラス

    このクラスは、フラクタル描画アプリケーションのメインウィンドウを管理し、
    UIコンポーネントの初期化、配置、フラクタルの描画、ズーム操作、
    ステータス表示、ログ管理などの機能を提供します。

    Attributes:
        root (tk.Tk): Tkinter のルートウィンドウ
        logger (DebugLogger): デバッグログを管理するロガーインスタンス
        config (dict): アプリケーションの設定データ
        canvas_frame (ttk.Frame): フラクタル描画領域を配置するフレーム
        fractal_canvas (FractalCanvas): フラクタルを描画するキャンバス
        parameter_frame (ttk.Frame): パラメータパネルを配置するフレーム
        parameter_panel (ParameterPanel): フラクタルのパラメータを管理するパネル
        status_bar_manager (StatusBarManager): ステータスバーを管理するクラス
        zoom_params (dict): ズーム操作に関するパラメータ
        prev_zoom_params (dict): 直前のズーム操作のパラメータ
        is_drawing (bool): フラクタル描画中かどうかを示すフラグ
        draw_thread (threading.Thread): フラクタル描画処理を実行するスレッド
        canvas_width (int): キャンバスの幅 (ピクセル単位)
        canvas_height (int): キャンバスの高さ (ピクセル単位)
    """

    def __init__(self, root: tk.Tk, logger: DebugLogger, config: dict):
        """
        MainWindow クラスの初期化

        初期化時に以下の処理を行います：
        1. フラクタルローダーの初期化とプラグインの読み込み
        2. ルートウィンドウの基本設定
        3. ステータスバーの初期化と配置
        4. パラメータパネルの初期化と配置
        5. フラクタル描画領域の初期化と配置
        6. ズーム操作のパラメータ初期化
        7. 初期描画の開始

        Args:
            root (tk.Tk): Tkinter のルートウィンドウ
            logger (DebugLogger): デバッグログを管理するロガーインスタンス
            config (dict): アプリケーションの設定データ
        """
        self.root = root
        self.logger = logger
        self.config = config
        self.is_drawing = False
        self.draw_thread = None

        # 設定ファイルから情報取得
        self.ui_settings = self.config.get("ui_settings", {})
        self.plugin_dir = self.config.get("system_settings",{}).get("plugin_dir", "plugins/fractal_types")

        # フラクタルローダーの初期化と読み込み
        self.logger.log(LogLevel.INIT, "FractalTypeLoader クラスのインスタンス作成開始")
        self.fractal_loader = FractalTypeLoader(plugin_dir=self.plugin_dir, logger=self.logger)
        self.logger.log(LogLevel.CALL, "プラグインのスキャンとロードを開始")
        self.fractal_loader.scan_and_load_plugins()

        self.logger.log(LogLevel.CALL, "ルートウィンドウの基本設定を開始")
        self._setup_root_window()
        self.logger.log(LogLevel.CALL, "ステータスバーの初期化と配置開始")
        self._setup_status_bar()
        self.logger.log(LogLevel.CALL, "パラメータパネルを配置するフレームの初期化と配置開始")
        self._setup_parameter_frame()
        self.logger.log(LogLevel.CALL, "フラクタル描画領域を配置するフレームの初期化と配置開始")
        self._setup_canvas_frame()
        self.logger.log(LogLevel.CALL, "ズーム操作に関するパラメータを初期化開始")
        self._setup_zoom_params()
        self.logger.log(LogLevel.CALL, "アプリケーション起動時の初期描画を開始")
        self._start_initial_drawing()

    def _setup_root_window(self) -> None:
        """
        ルートウィンドウ (tk.Tk) の基本設定を行う

        設定内容：
        - ウィンドウタイトルの設定
        - ウィンドウサイズの設定（設定ファイルから読み込み）

        Raises:
            TypeError: 設定ファイルの形式が不正な場合
        """
        app_title = self.config.get("ui_settings", {}).get("app_title", "フラクタル描画アプリケーション")
        window_width = self.config.get("ui_settings", {}).get("window_width", 1280)
        window_height = self.config.get("ui_settings", {}).get("window_height", 800)

        self.root.title(app_title)
        self.root.geometry(f"{window_width}x{window_height}")

        self.logger.log(LogLevel.SUCCESS, "ルートウィンドウの基本設定を完了")

    def _setup_status_bar(self) -> None:
        """
        ステータスバーを初期化し、ルートウィンドウの下部に配置する

        ステータスバーは以下の機能を提供します：
        - アプリケーションの状態表示
        - エラーメッセージの表示
        - プログレスインジケータの表示
        """
        status_frame = ttk.Frame(self.root)
        status_frame.pack(fill=tk.X, side=tk.BOTTOM, pady=(0, 5))

        self.logger.log(LogLevel.INIT, "StatusBarManager クラスのインスタンス作成開始")
        self.status_bar_manager = StatusBarManager(
            self.root,
            status_frame,
            self.logger
        )

        self.logger.log(LogLevel.SUCCESS, "ステータスバーの初期化と配置成功")

    def _setup_zoom_params(self) -> None:
        """
        ズーム操作に関するパラメータを初期化する

        初期化されるパラメータ：
        - center_x: 中心X座標
        - center_y: 中心Y座標
        - width: 表示範囲の幅
        - height: 表示範囲の高さ（幅と比率から計算）
        - rotation: 回転角

        Raises:
            KeyError: 設定ファイルに必要なパラメータが存在しない場合
        """
        # 初期ズームパラメータを設定ファイルから読み込む
        initial_zoom_config = self.config.get("fractal_settings", {}).get("initial_zoom", {})
        center_x = initial_zoom_config.get("center_x", 0.0)
        center_y = initial_zoom_config.get("center_y", 0.0)
        width = initial_zoom_config.get("width", 4.0)
        # 高さは幅と比率から計算 (設定ファイルに height_ratio あり)
        height_ratio = initial_zoom_config.get("height_ratio", 9 / 16)
        height = width * height_ratio
        rotation = initial_zoom_config.get("rotation", 0.0)

        self.zoom_params = {
            "center_x": center_x,       # 中心X座標
            "center_y": center_y,       # 中心Y座標
            "width": width,             # 初期表示範囲の幅
            "height": height,           # 幅と比率から計算
            "rotation": rotation        # 回転角
        }

        self.prev_zoom_params = None

        self.logger.log(LogLevel.SUCCESS, "ズーム操作に関するパラメータを初期化成功", context=self.zoom_params)

    def _setup_parameter_frame(self) -> None:
        """
        パラメータパネルを配置するフレームを初期化し、ルートウィンドウの右側に配置する

        パラメータパネルは以下の機能を提供します：
        - フラクタルの種類選択
        - 描画パラメータの設定
        - ズームリセット機能
        """
        width = self.config.get("ui_settings", {}).get("parameter_panel_width", 300)

        self.parameter_frame = ttk.Frame(self.root, width=width)
        self.parameter_frame.pack(
            side=tk.RIGHT,
            fill=tk.Y,
            padx=(0, 5),
            pady=5,
            expand=False
        )
        self.parameter_frame.pack_propagate(False)

        self.logger.log(LogLevel.INIT, "ParameterPanel クラスのインスタンス作成開始")
        self.parameter_panel = ParameterPanel(
            self.parameter_frame,
            self.update_fractal,
            reset_callback=self.reset_zoom,
            logger=self.logger,
            config=self.config,
            fractal_loader=self.fractal_loader # ローダーインスタンスを渡す
        )

        self.logger.log(LogLevel.SUCCESS, "パラメータパネルを配置するフレームの初期化と配置成功")

    def _setup_canvas_frame(self) -> None:
        """
        フラクタル描画領域を配置するキャンバスフレームを初期化し、
        ルートウィンドウの左側に配置する

        キャンバスフレームは以下の機能を提供します：
        - フラクタルの描画
        - ズーム操作
        - パン操作
        - 回転操作
        """
        self.canvas_frame = ttk.Frame(self.root)
        self.canvas_frame.pack(
            side=tk.LEFT,
            fill=tk.BOTH,
            expand=True,
            padx=(5, 0),
            pady=5
        )

        self.canvas_frame.bind("<Configure>", self._on_canvas_frame_configure)

        initial_canvas_width = self.config.get("ui_settings", {}).get("initial_canvas_width", 1067)
        initial_canvas_height = self.config.get("ui_settings", {}).get("initial_canvas_height", 600)

        self.logger.log(LogLevel.INIT, "FractalCanvas クラスのインスタンス作成開始")
        self.fractal_canvas = FractalCanvas(
            self.canvas_frame,
            width=initial_canvas_width,
            height=initial_canvas_height,
            logger=self.logger,
            zoom_confirm_callback=self.on_zoom_confirm,
            zoom_cancel_callback=self.on_zoom_cancel,
            config=self.config
        )

        self.logger.log(LogLevel.SUCCESS, "フラクタル描画領域を配置するフレームの初期化と配置成功")

    def _start_initial_drawing(self) -> None:
        """
        アプリケーション起動時の初期描画を開始する

        - ステータスバーにメッセージを表示
        - 別スレッドでフラクタル描画処理を開始
        """
        self.status_bar_manager.set_text("準備中...")

        self.logger.log(LogLevel.CALL, "非同期でフラクタル描画開始")
        self.status_bar_manager.start_animation()
        self.draw_thread = threading.Thread(
            target=self._update_fractal_thread,
            daemon=True
        )
        self.draw_thread.start()

        self.logger.log(LogLevel.SUCCESS, "アプリケーション起動時の初期描画成功")

    def update_fractal(self) -> None:
        """
        フラクタルを再描画する

        - 描画中の場合は新しい描画要求を無視
        - 描画中はステータスバーにアニメーションを表示し、別スレッドで描画処理を実行
        """
        if self.is_drawing:
            self.logger.log(LogLevel.WARNING, "描画中でスキップ：前回の描画が未完了")
            return

        self.is_drawing = True
        self.status_bar_manager.start_animation()

        self.logger.log(LogLevel.CALL, "新しい描画スレッドを開始")
        self.draw_thread = threading.Thread(
            target=self._update_fractal_thread,
            daemon=True
        )
        self.draw_thread.start()

    def _update_fractal_thread(self) -> None:
        """
        フラクタル更新処理を別スレッドで実行する

        - パラメータパネルから描画パラメータを取得
        - フラクタル画像を生成
        - 生成された画像をメインスレッドでキャンバスに描画
        - エラー発生時はログ出力とステータスバーにエラーメッセージを表示
        """
        try:
            self.logger.log(LogLevel.CALL, "描画パラメータ：取得開始（スレッド内）")
            panel_params = self.parameter_panel.get_parameters() # 新しいメソッド名 (後で ParameterPanel に実装)
            if not panel_params:
                 self.logger.log(LogLevel.ERROR, "パラメータ取得に失敗したため描画を中止します。")
                 self.status_bar_manager.stop_animation("エラー: パラメータ無効")
                 self.is_drawing = False
                 return

            current_params = self._merge_zoom_and_panel_params(panel_params)

            # --- 選択されたフラクタルタイプの計算関数を取得 ---
            selected_fractal_type_name = panel_params.get("fractal_type_name") # ParameterPanel が返す辞書に含める
            compute_function = self.fractal_loader.get_compute_function(selected_fractal_type_name)

            if compute_function is None:
                self.logger.log(LogLevel.CRITICAL, f"選択されたフラクタルタイプ '{selected_fractal_type_name}' の計算関数が見つかりません！")
                self.status_bar_manager.stop_animation("エラー: 計算関数不明")
                self.is_drawing = False
                return
            # ------------------------------------------------------

            self.logger.log(LogLevel.CALL, f"フラクタル計算 ({selected_fractal_type_name}) と着色処理を開始（スレッド内）")
            fractal_image = render_fractal(current_params, compute_function, self.logger, config=self.config)

            self.logger.log(LogLevel.CALL, "メインスレッドでキャンバス更新要求（スレッド内）")
            # メインスレッドでキャンバス更新をスケジュール
            self.root.after(0, lambda: self.fractal_canvas.update_canvas(
                fractal_image, current_params
            ))

            self.status_bar_manager.stop_animation("完了")
        except Exception as e:
            # 参考用としてキープ（デバッグ用スタックトレース出力）
            # import traceback
            # stack_trace = traceback.format_exc()
            # self.logger.log(LogLevel.ERROR, f"フラクタル更新スレッドエラー: {str(e)}",
            #                 context={"stack_trace": stack_trace})

            self.logger.log(LogLevel.ERROR, f"フラクタル更新スレッドエラー: {str(e)}")
            self.status_bar_manager.stop_animation(f"エラー: {str(e)}")
        finally:
            self.is_drawing = False

    def _merge_zoom_and_panel_params(self, panel_params: dict) -> dict:
        """
        ズームパラメータとパラメータパネルのパラメータを結合する

        Args:
            panel_params (dict): パラメータパネルから取得したパラメータ

        Returns:
            dict: 結合されたパラメータ
        """
        current_params = self.zoom_params.copy()
        current_params.update(panel_params)
        current_params["render_mode"] = self.parameter_panel.render_mode
        return current_params

    def on_zoom_confirm(self, x: float, y: float, w: float, h: float, angle: float) -> None:
        """
        ズーム操作確定時のコールバック関数

        - 新しい中心座標、幅、高さ、回転角を計算
        - フラクタルを再描画
        - ズームファクターに応じて最大イテレーション回数も調整

        Args:
            x (float): ズーム矩形の左上隅のX座標
            y (float): ズーム矩形の左上隅のY座標
            w (float): ズーム矩形の幅
            h (float): ズーム矩形の高さ
            angle (float): ズーム矩形の回転角度 (度数法)
        """
        center_x = x + w / 2
        center_y = y + h / 2

        self.prev_zoom_params = self.zoom_params.copy()

        new_width = w
        height_ratio = self.config.get("fractal_settings", {}).get("initial_zoom", {}).get("height_ratio", 9/16)
        new_height = new_width * height_ratio # 16:9 アスペクト比維持

        zoom_factor = self.zoom_params["width"] / new_width if new_width > 0 else 1

        # panel_params が None でないことを確認
        panel_params = self.parameter_panel.get_parameters()
        if panel_params:
            current_max_iter = panel_params.get("max_iterations", 100) # デフォルト値を追加
        else:
            # パラメータ取得に失敗した場合のデフォルト処理
            current_max_iter = self.config.get("fractal_settings", {}).get("parameter_panel", {}).get("max_iterations", 100)
            self.logger.log(LogLevel.WARNING, "パラメータパネルから最大反復回数を取得できませんでした。設定ファイルのデフォルト値を使用します。")


        new_max_iterations = self._calculate_max_iterations(current_max_iter, zoom_factor)

        self.logger.log(
            LogLevel.SUCCESS,
            context={
                "zoom_factor": zoom_factor,
                "new_width": new_width,
                "new_height": new_height,
                "current_max_iter": current_max_iter,
                "new_max_iterations": new_max_iterations,
                "new_center_x": center_x,
                "new_center_y": center_y,
                "new_rotation": angle
            },
            message="新しいズームパラメータ"
        )

        self.zoom_params = {
            "center_x": center_x,
            "center_y": center_y,
            "width": new_width,
            "height": new_height,
            "rotation": angle
        }

        # パラメータパネルの更新
        self.parameter_panel.max_iter_var.set(str(new_max_iterations))

        self.update_fractal()

    def _calculate_max_iterations(self, current_max_iter: int, zoom_factor: float) -> int:
        """
        ズームファクターに基づいてフラクタル計算の最大イテレーション回数を計算する

        - ズームインするほど詳細なフラクタル構造を表示するために、最大イテレーション回数を増やす

        Args:
            current_max_iter (int): 現在の最大イテレーション回数
            zoom_factor (float): ズームファクター (1より大きい場合、ズームイン)

        Returns:
            int: 計算された新しい最大イテレーション回数
        """
        # この計算ロジック自体も設定ファイル化可能だが、一旦現状維持
        if zoom_factor > 1: # ズームインの場合
            # 最大イテレーション回数を増やす（上限 1000）
            # 対数の底や係数、上限値などを設定ファイルから読み込むことも可能
            new_iter = min(1000, max(current_max_iter, int(current_max_iter + 50 * np.log2(zoom_factor))))
            self.logger.log(LogLevel.DEBUG, f"ズームイン: イテレーション回数更新 {current_max_iter} -> {new_iter}")
            return new_iter
        self.logger.log(LogLevel.DEBUG, f"ズームアウト/変化なし: イテレーション回数維持 {current_max_iter}")
        return current_max_iter # ズームアウトまたは変化なしの場合

    def on_zoom_cancel(self):
        """
        ズーム操作キャンセル時のコールバック関数

        - 直前のズームパラメータに戻してフラクタルを再描画
        """
        if self.prev_zoom_params is not None:
            self.logger.log(LogLevel.CALL, "直前のズームパラメータに戻す")
            self.zoom_params = self.prev_zoom_params.copy()
            # キャンセル時もイテレーション回数を元に戻すか検討
            # prev_panel_params のようなものが必要になる
            # ここではイテレーションは変更されたままにする
            self.update_fractal()
            self.prev_zoom_params = None
        else:
            self.logger.log(LogLevel.WARNING, "キャンセル処理をスキップ：直前のパラメータなし")

    def reset_zoom(self):
        """
        操作パネルの「描画リセット」ボタン押下時の処理

        - ズームパラメータを初期状態に戻し、フラクタルを再描画
        - 初期値は設定ファイルから読み込む
        """
        self._setup_zoom_params()

        # --- パラメータパネルの状態も初期化 ------------------
        # 初期表示のフラクタルタイプを取得
        default_fractal_type = self.config.get("fractal_settings", {}).get("parameter_panel", {}).get("fractal_type", None)
        if default_fractal_type is None and self.fractal_loader.get_available_types():
             default_fractal_type = self.fractal_loader.get_available_types()[0] # ローダーから最初のタイプを取得

        if default_fractal_type:
             self.parameter_panel.reset_to_defaults(default_fractal_type)
             self.logger.log(LogLevel.CALL, f"パラメータパネルをデフォルト ({default_fractal_type}) にリセット")
        else:
             self.logger.log(LogLevel.WARNING, "デフォルトのフラクタルタイプが見つからないため、パラメータパネルのリセットをスキップ")
             reset_iter = self.config.get("fractal_settings", {}).get("reset_max_iterations", 200)
             self.parameter_panel.max_iter_var.set(str(reset_iter)) # max_iter_var がまだ存在する場合
             self.logger.log(LogLevel.CALL, f"最大反復回数のみリセット: {reset_iter}")
        # -------------------------------------------------

        self.logger.log(LogLevel.CALL, "ZoomSelector の状態リセット開始")
        # FractalCanvas が初期化されているか確認
        if hasattr(self, 'fractal_canvas') and self.fractal_canvas:
            self.fractal_canvas.reset_zoom_selector() # ズーム選択領域をリセット
        else:
             self.logger.log(LogLevel.WARNING, "FractalCanvas が初期化されていないため、ZoomSelector のリセットをスキップ")

        self.update_fractal()

    def _on_canvas_frame_configure(self, event):
        """
        キャンバスフレームのリサイズ時に、内部の Matplotlib Figure のサイズを調整し、16:9 の縦横比を維持する

        Args:
            event (tk.Event): Tkinter の Configure イベント
        """
        frame_width_pixels = event.width
        frame_height_pixels = event.height

        # フレームサイズが有効でない場合は処理をスキップ
        if frame_width_pixels <= 1 or frame_height_pixels <= 1: # 0以下だとエラーになる可能性があるので1以下でチェック
            self.logger.log(LogLevel.INFO, f"Figure サイズ更新をスキップ：フレームサイズが無効 ({frame_width_pixels}x{frame_height_pixels})")
            return

        # 目標アスペクト比 (設定ファイルから読み込むことも可能だが、現状維持)
        target_aspect = 16 / 9

        frame_aspect = frame_width_pixels / frame_height_pixels

        if frame_aspect > target_aspect:
            new_height_pixels = frame_height_pixels
            new_width_pixels = int(new_height_pixels * target_aspect)
            self.logger.log(LogLevel.DEBUG, f"横長フレーム：高さを基準に Figure サイズ計算 ({new_width_pixels}x{new_height_pixels})")
        else:
            new_width_pixels = frame_width_pixels
            new_height_pixels = int(new_width_pixels / target_aspect) if target_aspect > 0 else frame_height_pixels
            self.logger.log(LogLevel.DEBUG, f"縦長/同等フレーム：幅を基準に Figure サイズ計算 ({new_width_pixels}x{new_height_pixels})")

        # Figureオブジェクトが存在するか確認
        if not (self.fractal_canvas and hasattr(self.fractal_canvas, 'fig') and self.fractal_canvas.fig):
             self.logger.log(LogLevel.WARNING, "FractalCanvas または Figure が利用不可（Figure サイズ更新スキップ）")
             return

        dpi = self.fractal_canvas.fig.get_dpi()

        # ピクセル数が小さすぎる場合、インチ数がほぼゼロになりエラーになる可能性
        if new_width_pixels < 1 or new_height_pixels < 1:
             self.logger.log(LogLevel.WARNING, f"計算後のピクセル数が小さすぎるため更新をスキップ: {new_width_pixels}x{new_height_pixels}")
             return

        new_width_inches = new_width_pixels / dpi
        new_height_inches = new_height_pixels / dpi

        try:
            self.fractal_canvas.fig.set_size_inches(new_width_inches, new_height_inches, forward=True)
            self.logger.log(LogLevel.DEBUG, f"Matplotlib Figure サイズ更新完了: {new_width_inches:.2f}x{new_height_inches:.2f}インチ ({new_width_pixels}x{new_height_pixels}ピクセル)")
        except Exception as e:
            self.logger.log(LogLevel.ERROR, f"Matplotlib Figure サイズ更新中にエラー: {e}")
