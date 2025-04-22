# main_window.py の修正案

import tkinter as tk
import numpy as np
import threading
from tkinter import ttk
from ui.canvas import FractalCanvas
from ui.parameter_panel import ParameterPanel
from fractal.render import render_fractal
from .status_bar import StatusBarManager
from .zoom_function.debug_logger import DebugLogger
from .zoom_function.enums import LogLevel

class MainWindow:
    """アプリケーションのメインウィンドウクラス
    - 役割:
        - アプリケーションのメインウィンドウを管理する
        - UIの初期化、イベント処理、フラクタル描画の制御を行う
    """
    def __init__(self, root, logger: DebugLogger):
        """メインウィンドウクラスのコンストラクタ

        Args:
            root (tkinter.Tk): Tkinter ルートウィンドウ
            logger (DebugLogger): ログ出力用の DebugLogger インスタンス
        """
        self.logger = logger

        self._init_root_window(root)

        # ズーム操作用パラメータ
        self.zoom_params = {
            "center_x": 0.0, "center_y": 0.0, "width": 4.0, "height": 4.0, "rotation": 0.0}
        self.prev_zoom_params = None

        self.logger.log(LogLevel.INIT, "コールバック設定開始")
        self.fractal_canvas.set_zoom_callback(self.on_zoom_confirm, self.on_zoom_cancel)

        # 非同期処理用変数
        self.is_drawing = False
        self.draw_thread = None

        # アプリケーション起動時の最初の描画スレッド開始前に、ステータスバーアニメーションを開始
        self.logger.log(LogLevel.DEBUG, "ステータスバーテキスト設定要求")
        self.status_bar_manager.set_text("準備中...") # ステータスバーの初期テキストを設定

        # フラクタル描画スレッドを作成後、開始する
        # アプリケーション起動時は update_fractal を経由せず直接スレッドを開始する
        self.logger.log(LogLevel.DEBUG, "非同期でフラクタル描画開始")
        self.status_bar_manager.start_animation() # アプリケーション起動時のアニメーション開始
        self.draw_thread = threading.Thread(target=self._update_fractal_thread, daemon=True) # Daemonスレッドとして作成
        self.draw_thread.start() # フラクタル描画スレッドを開始

    def _init_root_window(self, root):
        """メインウィンドウの初期化

        Args:
            root (tkinter.Tk): Tkinter ルートウィンドウ
        """
        # Tkinter ルートウィンドウの初期化
        self.root = root
        self.root.title("フラクタル描画アプリケーション")
        self.root.geometry("1200x800")

        # ステータスバーのフレームを作成、配置
        status_frame = ttk.Frame(self.root) # 作成
        status_frame.pack(fill=tk.X, side=tk.BOTTOM, pady=(0, 5))
        # StatusBarManager のインスタンスを作成、保持
        self.logger.log(LogLevel.INIT, "StatusBarManager 初期化開始")
        self.status_bar_manager = StatusBarManager(
            self.root,
            status_frame,
            self.logger)

        # --- パラメータパネルフレームの作成と配置 (pack で右側固定) ---
        self.parameter_frame = ttk.Frame(root, width=300) # 作成（width=300）
        # 右側に幅 300px 固定で配置、Y方向にのみ引き伸ばす
        # expand=False でウィンドウリサイズ時に幅が変わらないようにする
        self.parameter_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=(0, 5), pady=5, expand=False) # 配置
        # widthで指定した幅を維持するため、フレーム内のウィジェットサイズに合わせてフレームサイズが変わるのを防ぐ
        self.parameter_frame.pack_propagate(False) # フレームのサイズを固定

        # --- キャンバスフレームの作成と配置 (pack で残り領域) ---
        self.canvas_frame = ttk.Frame(root) # 作成
        # 左側の残りスペース全体に配置、両方向に引き伸ばす
        # expand=True でウィンドウリサイズ時に残りスペースを埋めるように広がる
        self.canvas_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(5, 0), pady=5) # 配置

        # キャンバスフレームのリサイズイベントをバインド
        # <Configure> イベントが発生すると、_on_canvas_frame_configure メソッドが呼ばれる
        self.canvas_frame.bind("<Configure>", self._on_canvas_frame_configure)

        # FractalCanvas のインスタンスを作成、保持
        # 親を canvas_frame に設定 (PanedWindow を使わないため直接 root の子フレームになる)
        self.logger.log(LogLevel.INIT, "FractalCanvas 初期化開始")
        self.fractal_canvas = FractalCanvas(
            self.canvas_frame, # 親ウィジェットを更新
            width=1067, # この初期サイズは configure イベントで上書きされる可能性がある
            height=600,
            logger=self.logger,
            zoom_confirm_callback=self.on_zoom_confirm, # 確定用コールバックをキャンバスに渡す
            zoom_cancel_callback=self.on_zoom_cancel) # キャンセル用コールバックをキャンバスに渡す

        # ParameterPanel のインスタンスを作成、保持
        # 親を parameter_frame に設定
        self.logger.log(LogLevel.INIT, "ParameterPanel 初期化開始")
        self.parameter_panel = ParameterPanel(
            self.parameter_frame, # 親ウィジェットを更新
            self.update_fractal, # パラメータ変更時のコールバックとしてMainWindowのupdate_fractalを渡す
            reset_callback=self.reset_zoom, # リセット用コールバックをパラメータパネルに渡す
            logger=self.logger)

    def update_fractal(self):
        """最新パラメータにズーム情報を上書きしてフラクタルを再描画（非同期処理を開始）"""
        # 既に描画中の場合は新しい描画を開始しない
        if self.is_drawing:
             self.logger.log(LogLevel.INFO, "描画中スキップ：前回の描画が未完了")
             return

        self.is_drawing = True

        # 描画開始時にステータスバーアニメーションを開始
        self.status_bar_manager.start_animation()

        self.logger.log(LogLevel.INFO, "新しい描画スレッドを開始")
        self.draw_thread = threading.Thread(target=self._update_fractal_thread, daemon=True)
        self.draw_thread.start()

    def _update_fractal_thread(self):
        """フラクタル更新の実際の処理（別スレッドで実行される）"""
        try:
            self.logger.log(LogLevel.CALL, "描画パラメータ：取得開始（スレッド内）")
            panel_params = self.parameter_panel._get_parameters()

            # ズーム操作によるパラメータとパラメータパネルの設定を結合
            current_params = self.zoom_params.copy()
            current_params.update(panel_params) # パラメータパネルの設定で上書き（max_iterなど）

            self.logger.log(LogLevel.CALL, "フラクタル計算と着色処理を開始（スレッド内）")
            fractal_image = render_fractal(current_params, self.logger)

            self.logger.log(LogLevel.CALL, "メインスレッドでキャンバス更新要求（スレッド内）")
            # Tkinterのウィジェット操作は必ずメインスレッドで行う必要があるため、
            # root.after を使用し、update_canvas メソッドをメインスレッドで実行するようにスケジュールする
            self.root.after(0, lambda: self.fractal_canvas.update_canvas(fractal_image, current_params))

            # アニメーションと時間計測を停止し、最終メッセージを表示
            self.status_bar_manager.stop_animation("完了")
        except Exception as e: # 例外処理
            self.logger.log(LogLevel.ERROR, f"フラクタル更新スレッドエラー: {str(e)}")
            # エラー発生時もアニメーションを停止し、エラーメッセージを表示
            self.status_bar_manager.stop_animation(f"エラー: {str(e)}")
        finally: # 描画スレッドの終了処理
            self.is_drawing = False # is_drawing フラグをリセット

    def on_zoom_confirm(self, x: float, y: float, w: float, h: float, angle: float):
        """ズーム確定時のコールバック（ZoomSelectorから呼ばれる）
        - 縦横比を考慮して新しいズームパラメータを計算し、フラクタルを再描画
        - 矩形の中心座標を回転前の座標系に変換

        Args:
            x (float): 矩形左上の x 座標 (データ座標系)
            y (float): 矩形左上の y 座標 (データ座標系)
            w (float): 矩形の幅 (データ座標系)
            h (float): 矩形の高さ (データ座標系)
            angle (float): 矩形の回転角度 (度)
        """
        # ズーム矩形の中心座標を計算（回転前の座標系）
        center_x = x + w / 2
        center_y = y + h / 2

        self.logger.log(LogLevel.SUCCESS, "ズーム確定矩形情報", {
            "rect_x": x, "rect_y": y, "rect_w": w, "rect_h": h,
            "center_x": center_x, "center_y": center_y, "angle": angle})

        # ズーム確定前の現在のズームパラメータを保存（ズーム確定キャンセル用）
        self.prev_zoom_params = self.zoom_params.copy()

        # 新しいズームパラメータ（中心座標、幅、高さ、回転角度）を計算
        new_width = w # 幅は選択された矩形の幅を使用
        # 高さは、キャンバスの縦横比（16:9）に合わせて計算
        # update_canvas で (9 / 16) と計算しているので、ここでも合わせる
        new_height = new_width * (9 / 16) # 16:9の縦横比を維持

        # ズームファクターを計算（幅の変化率から）して最大反復回数を調整時に利用する
        zoom_factor = self.zoom_params["width"] / new_width if new_width > 0 else 1
        current_max_iter = int(self.parameter_panel.max_iter_var.get()) # 現在の最大反復回数を取得

        # ズームインした場合（zoom_factor > 1）のみ反復回数を増やす（上限あり）
        new_max_iterations = current_max_iter # デフォルトは現在の値
        if zoom_factor > 1:
            # ズームファクターに基づいて反復回数を増加させるロジック
            new_max_iterations = min(1000, max(current_max_iter, int(current_max_iter + 50 * np.log2(zoom_factor))))
        else:
             self.logger.log(LogLevel.DEBUG, f"ズームアウトまたは移動のみ: 反復回数変更なし ({current_max_iter})")

        self.logger.log(LogLevel.SUCCESS, "新しいズームパラメータ計算結果", {
            "zoom_factor": zoom_factor,"new_width": new_width, "new_height": new_height,
            "current_max_iter": current_max_iter, "new_max_iterations": new_max_iterations,
            "new_center_x": center_x, "new_center_y": center_y, "new_rotation": angle})

        # 新しいズームパラメータを設定
        self.zoom_params = {
            "center_x": center_x, "center_y": center_y,
            "width": new_width,
            "height": new_height, # この値は render_fractal での計算範囲の高さ設定に使用される
            "rotation": angle}

        # 計算された新しい最大反復回数をパラメータパネルに反映
        self.parameter_panel.max_iter_var.set(str(new_max_iterations))

        self.update_fractal() # 新しいパラメータでフラクタルを再描画

    def on_zoom_cancel(self):
        """ズームキャンセル時のコールバック（ZoomSelectorから呼ばれる）
        - ズーム確定前の状態に戻して再描画
        """
        if self.prev_zoom_params is not None:
            self.logger.log(LogLevel.DEBUG, "直前のズームパラメータに戻す")
            self.zoom_params = self.prev_zoom_params.copy() # 確定前のズームパラメータに戻す
            self.update_fractal()
            self.prev_zoom_params = None
        else:
            self.logger.log(LogLevel.INFO, "キャンセル処理スキップ：直前のパラメータなし")

    def reset_zoom(self):
        """操作パネルの「描画リセット」ボタン押下時の処理
        - ズームパラメータを初期状態に戻して再描画
        """
        # ズームパラメータを初期値にリセット
        self.zoom_params = {
            "center_x": 0.0, "center_y": 0.0, "width": 4.0, "height": 4.0, "rotation": 0.0}
        self.prev_zoom_params = None # 確定前のパラメータをクリア
        self.parameter_panel.max_iter_var.set("100")
        self.logger.log(LogLevel.CALL, "ZoomSelector の状態リセット開始")
        self.fractal_canvas.reset_zoom_selector() # ZoomSelectorの状態もリセット（矩形などを消去）
        self.update_fractal()

    def _on_canvas_frame_configure(self, event):
        """キャンバスフレームのリサイズ時に Matplotlib Figure のサイズを更新し、16:9 の縦横比を維持する"""
        # キャンバスフレームの新しいピクセルサイズを取得
        frame_width_pixels = event.width
        frame_height_pixels = event.height

        if frame_width_pixels <= 0 or frame_height_pixels <= 0:
            self.logger.log(LogLevel.DEBUG, "Figure サイズ更新スキップ：フレームサイズが無効なため")
            return

        target_aspect = 16 / 9 # 目標の縦横比 (幅 / 高さ)

        # 現在のフレームの縦横比を計算（ゼロ除算を防ぐ）
        frame_aspect = frame_width_pixels / frame_height_pixels if frame_height_pixels > 0 else float('inf')

        # どちらを基準に Figure サイズを決定するか判断
        if frame_aspect > target_aspect:
            # フレームが目標より横長の場合、フレームの高さを基準に Figure サイズを計算
            new_height_pixels = frame_height_pixels
            new_width_pixels = int(new_height_pixels * target_aspect)
            self.logger.log(LogLevel.DEBUG, f"横長フレーム：高さを基準に Figure サイズ計算 ({new_width_pixels}x{new_height_pixels})")
        else:
            # フレームが目標より縦長、または同じ縦横比の場合、フレームの幅を基準にFigureサイズを計算
            new_width_pixels = frame_width_pixels
            # 目標縦横比が 0 でないことを確認して計算（ゼロ除算を防ぐ）
            new_height_pixels = int(new_width_pixels / target_aspect) if target_aspect > 0 else frame_height_pixels
            self.logger.log(LogLevel.DEBUG, f"縦長/同等フレーム：幅を基準に Figure サイズ計算 ({new_width_pixels}x{new_height_pixels})")

        # Matplotlib の Figure サイズをインチ単位で計算 (dpi=100 を仮定、FractalCanvas で設定されている)
        # Figure の get_dpi() メソッドで実際の dpi を取得可能だが、初期化時の dpi=100 を使用
        dpi = self.fractal_canvas.fig.get_dpi() if self.fractal_canvas and hasattr(self.fractal_canvas, 'fig') and self.fractal_canvas.fig else 100

        new_width_inches = new_width_pixels / dpi
        new_height_inches = new_height_pixels / dpi

        # Figure のサイズを更新
        try:
            if self.fractal_canvas and hasattr(self.fractal_canvas, 'fig') and self.fractal_canvas.fig:
                # Matplotlib の Figure サイズを更新
                # forward=True で FigureCanvasTkAgg に通知し、再描画を促す
                # これにより Tkinter キャンバスウィジェットのサイズも Figure サイズに合うように調整される
                self.fractal_canvas.fig.set_size_inches(new_width_inches, new_height_inches, forward=True)
                self.logger.log(LogLevel.SUCCESS, f"Matplotlib Figure サイズ更新完了: {new_width_inches:.2f}x{new_height_inches:.2f}インチ ({new_width_pixels}x{new_height_pixels}ピクセル)")
                # Figure サイズ変更により Axes の表示も自動的に更新されるはずだが、
                # 必要に応じて self.fractal_canvas.canvas.draw_idle() を追加しても良い（ただしパフォーマンス注意）
            else:
                self.logger.log(LogLevel.ERROR, "FractalCanvas または Figure が利用不可（Figure サイズ更新スキップ）")
        except Exception as e:
            self.logger.log(LogLevel.ERROR, f"Matplotlib Figure サイズ更新中にエラー: {e}")
