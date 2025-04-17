import tkinter as tk
import numpy as np
from tkinter import ttk
from ui.canvas import FractalCanvas
from ui.parameter_panel import ParameterPanel
from fractal.render import render_fractal # render_fractal が rotation パラメータを扱えると仮定
from .zoom_function.debug_logger import DebugLogger
from .zoom_function.enums import LogLevel
import threading

class MainWindow:
    """ フラクタル描画アプリケーションのメインウィンドウクラス """
    def __init__(self, root, logger: DebugLogger):
        """ フラクタル描画アプリケーションのメインウィンドウ初期化（ズーム操作の状態管理も行う） """
        self.logger = logger
        self.logger.log(LogLevel.INIT, "MainWindow")
        self.root = root # Tkinter ルートウィンドウ
        self.root.title("フラクタル描画アプリケーション")
        self.root.geometry("1200x800")
		# 初期パラメータ設定
        self.zoom_params = {
            "center_x": 0.0, "center_y": 0.0, "width": 4.0, "height": 4.0, "rotation": 0.0
        }
        self.prev_zoom_params = None

        # UI初期化
        self.main_frame = ttk.PanedWindow(root, orient=tk.HORIZONTAL)
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        self.canvas_frame = ttk.Frame(self.main_frame)
        self.main_frame.add(self.canvas_frame, weight=3)

        self.parameter_frame = ttk.Frame(self.main_frame)
        self.main_frame.add(self.parameter_frame, weight=1)

        # キャンバス初期化（即時表示）
        self.fractal_canvas = FractalCanvas(
            self.canvas_frame, width=800, height=600, logger=self.logger,
            zoom_confirm_callback=self.on_zoom_confirm,
            zoom_cancel_callback=self.on_zoom_cancel
        )

        # 初期黒背景設定
        self.fractal_canvas.set_black_background()

        # パラメータパネル初期化
        self.parameter_panel = ParameterPanel(
            self.parameter_frame, self.update_fractal,
            reset_callback=self.reset_zoom, logger=self.logger
        )

        # コールバック設定
        self.fractal_canvas.set_zoom_callback(self.on_zoom_confirm, self.on_zoom_cancel)

        # 非同期でフラクタル描画を開始
        threading.Thread(target=self.update_fractal, daemon=True).start()

    def set_black_background(self):
        """黒背景を設定するヘルパーメソッド"""
        self.fractal_canvas.ax.set_facecolor('black')
        self.fractal_canvas.fig.patch.set_facecolor('black')
        self.fractal_canvas.canvas.draw()

    # ... (他のメソッドはそのまま保持) ...
    def update_fractal(self, *args) -> None:
        """ 最新パラメータにズーム情報を上書きしてフラクタルを再描画 """
        self.logger.log(LogLevel.CALL, "描画パラメータ：取得開始")

    def update_fractal(self, *args) -> None:
        """ 最新パラメータにズーム情報を上書きしてフラクタルを再描画 """
        self.logger.log(LogLevel.CALL, "描画パラメータ：取得開始")
        panel_params = self.parameter_panel.get_parameters()
        current_params = self.zoom_params.copy()
        current_params.update(panel_params) # パラメータパネルの設定で上書き（max_iterなど）
        self.logger.log(LogLevel.CALL, "フラクタル描画開始")
        fractal_image = render_fractal(current_params, self.logger)
        self.logger.log(LogLevel.CALL, "キャンバス更新開始（待機中...）")
        self.fractal_canvas.update_canvas(fractal_image, current_params)

    def on_zoom_confirm(self, x: float, y: float, w: float, h: float, angle: float):
        """ ズーム確定時のコールバック（縦横比を調整し、ズームレベルに応じて反復回数を自動調整） """
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
        """ ズームキャンセル時のコールバック """
        if self.prev_zoom_params is not None:
            self.logger.log(LogLevel.SUCCESS, "ズームキャンセル")
            self.zoom_params = self.prev_zoom_params.copy()
            self.update_fractal()
            self.prev_zoom_params = None
        else:
            self.logger.log(LogLevel.INFO, "直前のズームパラメータなし")

    def reset_zoom(self):
        """ 操作パネルの「描画リセット」ボタン押下時の処理（ズームパラメータを初期状態に戻して再描画） """
        self.logger.log(LogLevel.DEBUG, "描画リセットボタンのメソッド開始")
        self.zoom_params = {
            "center_x": 0.0, "center_y": 0.0, "width": 4.0, "height": 4.0, "rotation": 0.0}
        self.prev_zoom_params = None
        self.parameter_panel.max_iter_var.set("100")
        self.logger.log(LogLevel.CALL, "ZoomSelector の状態リセット開始")
        self.fractal_canvas.reset_zoom_selector()
        self.update_fractal()
