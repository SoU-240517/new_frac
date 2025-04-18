import tkinter as tk
import numpy as np
import threading
import time
from tkinter import ttk
from ui.canvas import FractalCanvas
from ui.parameter_panel import ParameterPanel
from fractal.render import render_fractal # render_fractal が rotation パラメータを扱えると仮定
from .zoom_function.debug_logger import DebugLogger
from .zoom_function.enums import LogLevel

class MainWindow:
    """
    フラクタル描画アプリケーションのメインウィンドウクラス
    """
    def __init__(self, root, logger: DebugLogger):
        """
        フラクタル描画アプリケーションのメインウィンドウ初期化（ズーム操作の状態管理も行う）
        """
        self.logger = logger
        self.logger = logger
        self.init_root_window(root)

		# ズーム操作用パラメータ
        self.zoom_params = {
            "center_x": 0.0, "center_y": 0.0, "width": 4.0, "height": 4.0, "rotation": 0.0
        }
        self.prev_zoom_params = None

        self.logger.log(LogLevel.INIT, "コールバック設定")
        self.fractal_canvas.set_zoom_callback(self.on_zoom_confirm, self.on_zoom_cancel)

        # 非同期処理用変数
        self.is_drawing = False
        self.draw_thread = None

        self.logger.log(LogLevel.INFO, "非同期でフラクタル描画を開始")
        threading.Thread(target=self.update_fractal, daemon=True).start()

    def init_root_window(self, root):
        """
        メインウィンドウの初期化
        """
        # Tkinter ルートウィンドウの初期化
        self.root = root
        self.root.title("フラクタル描画アプリケーション")
        self.root.geometry("1200x800")

        # メインフレーム
        self.main_frame = ttk.PanedWindow(root, orient=tk.HORIZONTAL) # 作成
        self.main_frame.pack(fill=tk.BOTH, expand=True) # 配置

        # キャンバスフレーム
        self.canvas_frame = ttk.Frame(self.main_frame) # 作成
        self.main_frame.add(self.canvas_frame, weight=3) # 配置
        self.logger.log(LogLevel.INIT, "FractalCanvas 初期化開始")
        self.fractal_canvas = FractalCanvas(
            self.canvas_frame,
            width=800,
            height=600,
            logger=self.logger,
            zoom_confirm_callback=self.on_zoom_confirm,
            zoom_cancel_callback=self.on_zoom_cancel)
        self.fractal_canvas.set_black_background() # 黒背景

        # パラメータフレーム
        self.parameter_frame = ttk.Frame(self.main_frame) # 作成
        self.main_frame.add(self.parameter_frame, weight=1) # 配置
        self.logger.log(LogLevel.INIT, "ParameterPanel 初期化開始")
        self.parameter_panel = ParameterPanel(
            self.parameter_frame,
            self.update_fractal,
            reset_callback=self.reset_zoom,
            logger=self.logger)

        # ステータスバー
        self.status_frame = ttk.Frame(self.root) # 作成
        self.status_frame.pack(fill=tk.X, side=tk.BOTTOM) # 配置

        # ステータスバーのラベル
        self.status_label = ttk.Label(self.status_frame, text="準備中...") # 作成
        self.status_label.pack(side=tk.LEFT, padx=5, pady=2) # 配置

        # ステータスバーのアニメーション用変数
        self.animation_thread = None
        self.animation_running = False
        self.animation_dots = 0
        self.animation_max_dots = 5

    def update_fractal(self) -> None:
        """
        最新パラメータにズーム情報を上書きしてフラクタルを再描画
        """
        if self.draw_thread and self.draw_thread.is_alive(): return

        self.is_drawing = True
        self.start_status_animation()
        self.draw_thread = threading.Thread(
            target=self._update_fractal_thread,
            daemon=True)
        self.draw_thread.start()

    def _update_fractal_thread(self):
        """
        フラクタル更新の実際の処理
        """
        try:
            self.logger.log(LogLevel.CALL, "描画パラメータ：取得開始")
            panel_params = self.parameter_panel.get_parameters()
            current_params = self.zoom_params.copy()
            current_params.update(panel_params) # パラメータパネルの設定で上書き（max_iterなど）
            self.logger.log(LogLevel.CALL, "フラクタル描画開始")
            fractal_image = render_fractal(current_params, self.logger)
            self.logger.log(LogLevel.CALL, "メインスレッドでキャンバス更新開始（待機中...）")
            self.fractal_canvas.update_canvas(fractal_image, current_params)
            self.root.after(0, lambda: self.stop_status_animation()) # ステータス更新
        except Exception as e: # 例外処理
            self.logger.log(LogLevel.ERROR, f"フラクタル更新エラー: {str(e)}")
            self.root.after(0, lambda: self.stop_status_animation())
        finally: # 描画スレッドの終了処理
            self.is_drawing = False

    def on_zoom_confirm(self, x: float, y: float, w: float, h: float, angle: float):
        """
        ズーム確定時のコールバック（縦横比を調整し、ズームレベルに応じて反復回数を自動調整）
        """
        center_x = x + w / 2
        center_y = y + h / 2

        self.logger.log(LogLevel.SUCCESS, "ズーム確定", {"rect_x": x, "rect_y": y, "rect_w": w, "rect_h": h,
            "center_x": center_x, "center_y": center_y, "angle": angle})
        self.prev_zoom_params = self.zoom_params.copy() # ズーム確定前の状態を保存（ズーム確定キャンセル用）

        # 縦横比補正 (幅を基準に高さを調整)
        aspect_ratio = self.fractal_canvas.fig.get_size_inches()[0] / self.fractal_canvas.fig.get_size_inches()[1]
        new_width = w # 選択された矩形の幅をそのまま使用
        new_height = new_width / aspect_ratio # 縦横比を維持するように高さを計算

        zoom_factor = self.zoom_params["width"] / new_width if new_width > 0 else 1 # 幅の変化率でズームファクターを計算
        current_max_iter = int(self.parameter_panel.max_iter_var.get()) # 現在の最大反復回数を取得

        # ズームインした場合のみ反復回数を増やす（上限あり）
        if zoom_factor > 1:
            new_max_iterations = min(1000, max(current_max_iter, int(current_max_iter + 50 * np.log2(zoom_factor))))
        self.logger.log(LogLevel.SUCCESS, "ズームパラメータ調整結果", {
            "zoom_factor": zoom_factor, "aspect_ratio": aspect_ratio,
            "new_width": new_width, "new_height": new_height,
            "current_max_iter": current_max_iter, "new_max_iterations": new_max_iterations})

        # 新しいズームパラメータを設定
        self.zoom_params = {
            "center_x": center_x, "center_y": center_y, "width": new_width, "height": new_height, "rotation": angle}
        self.parameter_panel.max_iter_var.set(str(new_max_iterations))  # 反復回数をパラメータパネルに反映

        self.update_fractal()

    def on_zoom_cancel(self):
        """
        ズームキャンセル時のコールバック
        """
        if self.prev_zoom_params is not None:
            self.logger.log(LogLevel.SUCCESS, "ズームキャンセル")
            self.zoom_params = self.prev_zoom_params.copy()
            self.update_fractal()
            self.prev_zoom_params = None
        else:
            self.logger.log(LogLevel.INFO, "直前のズームパラメータなし")

    def reset_zoom(self):
        """
        操作パネルの「描画リセット」ボタン押下時の処理（ズームパラメータを初期状態に戻して再描画）
        """
        self.logger.log(LogLevel.DEBUG, "描画リセットボタンのメソッド開始")
        self.zoom_params = {
            "center_x": 0.0, "center_y": 0.0, "width": 4.0, "height": 4.0, "rotation": 0.0}
        self.prev_zoom_params = None
        self.parameter_panel.max_iter_var.set("100")
        self.logger.log(LogLevel.CALL, "ZoomSelector の状態リセット開始")
        self.fractal_canvas.reset_zoom_selector()
        self.update_fractal()

    def set_black_background(self):
        """
        黒背景を設定するヘルパーメソッド
        """
        self.fractal_canvas.ax.set_facecolor('black')
        self.fractal_canvas.fig.patch.set_facecolor('black')
        self.fractal_canvas.canvas.draw()

    def start_status_animation(self):
        """
        ステータスアニメーションを開始
        """
        if self.animation_thread and self.animation_thread.is_alive():
            return
        self.animation_running = True
        self.animation_dots = 0
        self.animation_thread = threading.Thread(
            target=self._status_animation_thread,
            daemon=True
        )
        self.animation_thread.start()

    def _status_animation_thread(self):
        """
        ステータスアニメーションの実際の処理
        """
        while self.animation_running:
            # ドットの数を増やして、最大に達したらリセット
            self.animation_dots = (self.animation_dots + 1) % (self.animation_max_dots + 1)
            # テキストを更新
            dots = "." * self.animation_dots
            self.root.after(0, lambda: self.status_label.config(text=f"描画中{dots}"))
            # 一定時間待機
            time.sleep(0.1)

    def stop_status_animation(self):
        """
        ステータスアニメーションを停止
        """
        self.animation_running = False
        if self.animation_thread and self.animation_thread.is_alive():
            self.animation_thread.join()
            self.status_label.config(text="完了")
