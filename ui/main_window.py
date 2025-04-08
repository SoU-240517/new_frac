import tkinter as tk
import numpy as np
from tkinter import ttk
from ui.canvas import FractalCanvas
from ui.parameter_panel import ParameterPanel
from fractal.render import render_fractal
from .zoom_function.debug_logger import DebugLogger
from .zoom_function.enums import LogLevel

class MainWindow:
    """ フラクタル描画アプリケーションのメインウィンドウクラス """
    def __init__(self, root, logger: DebugLogger):
        """ フラクタル描画アプリケーションのメインウィンドウ初期化（ズーム操作の状態管理も行う） """
        self.logger = logger
        self.logger.log(LogLevel.INIT, "Initializing MainWindow")
        self.root = root  # Tkinter ルートウィンドウ
        self.root.title("フラクタル描画アプリケーション")  # ウィンドウタイトル設定
        self.root.geometry("1200x800")  # ウィンドウサイズ設定
        # ズームパラメータ
        self.zoom_params = {
            "center_x": 0.0,
            "center_y": 0.0,
            "width": 4.0,
            "height": 4.0,
#            "rotation": 0.0
        }
        self.prev_zoom_params = None  # ズームパラメータ：直前
        self.main_frame = ttk.PanedWindow(root, orient=tk.HORIZONTAL)  # パネルウィンドウを作成
        self.main_frame.pack(fill=tk.BOTH, expand=True)  # パネルウィンドウをメインフレームに追加
        self.canvas_frame = ttk.Frame(self.main_frame)  # キャンバスフレームを作成
        self.main_frame.add(self.canvas_frame, weight=3)  # パネルウィンドウにキャンバスフレームを追加
        self.control_frame = ttk.Frame(self.main_frame)  # パラメータパネルフレームを作成
        self.main_frame.add(self.control_frame, weight=1)  # パネルウィンドウにパラメータパネルフレームを追加
        self.fractal_canvas = FractalCanvas(self.canvas_frame, self.logger) # Logger を渡す
        self.fractal_canvas.set_zoom_callback(self.on_zoom_confirm, self.on_zoom_cancel)
        self.parameter_panel = ParameterPanel(self.control_frame, self.update_fractal, reset_callback=self.reset_zoom, logger=self.logger) # Logger を渡す

        self.update_fractal()  # 初期描画

    def update_fractal(self, *args):
        """ 最新パラメータにズーム情報を上書きしてフラクタルを再描画 """
        self.logger.log(LogLevel.METHOD, "Updating fractal")
        panel_params = self.parameter_panel.get_parameters()  # パネルからパラメータを取得
        panel_params.update(self.zoom_params)  # ズーム情報を上書き
        # render_fractal に logger を渡す
        fractal_image = render_fractal(panel_params, self.logger)
        self.fractal_canvas.update_canvas(fractal_image, panel_params)  # キャンバスを更新

    def on_zoom_confirm(self, new_zoom_params):
        """ ズーム確定時のコールバック（縦横比を調整し、ズームレベルに応じて反復回数を自動調整） """
        self.logger.log(LogLevel.DEBUG, "Zoom confirmed", context={"new_zoom_params": new_zoom_params})
        if new_zoom_params == self.zoom_params:
            return

        # ズーム確定前の状態を保存（キャンセル機能用）
        self.prev_zoom_params = self.zoom_params.copy()

        # 縦横比補正
        aspect_ratio = self.fractal_canvas.fig.get_size_inches()[0] / self.fractal_canvas.fig.get_size_inches()[1]
        new_width = new_zoom_params["width"]
        new_height = new_width / aspect_ratio  # 縦横比を維持

        # ズームレベルに応じて `max_iterations` を増やす
        zoom_factor = self.zoom_params["width"] / new_width
        current_max_iter = int(self.parameter_panel.max_iter_var.get())
        # ズームインした場合のみ反復回数を増やす（上限あり）
        if zoom_factor > 1:
             new_max_iterations = min(1000, max(current_max_iter, int(current_max_iter + 50 * np.log2(zoom_factor)))) # 増加量を調整
        else:
             new_max_iterations = current_max_iter # ズームアウト時は変更しない

        self.logger.log(LogLevel.DEBUG, "Adjusting zoom parameters", context={
            "aspect_ratio": aspect_ratio,
            "new_width": new_width,
            "new_height": new_height,
            "zoom_factor": zoom_factor,
            "current_max_iter": current_max_iter,
            "new_max_iterations": new_max_iterations
        })


        self.zoom_params = {
            "center_x": new_zoom_params["center_x"],
            "center_y": new_zoom_params["center_y"],
            "width": new_width,
            "height": new_height,
        }

        self.parameter_panel.max_iter_var.set(str(new_max_iterations))  # 反復回数を更新
        self.update_fractal()

    def on_zoom_cancel(self):
        """ ズームキャンセル時のコールバック """
        self.logger.log(LogLevel.DEBUG, "Zoom cancelled")
        if self.prev_zoom_params is not None:  # 直前のズーム領域がある場合
            self.logger.log(LogLevel.DEBUG, "Restoring previous zoom parameters", context={"prev_zoom": self.prev_zoom_params})
            self.zoom_params = self.prev_zoom_params.copy()
            self.update_fractal()
            self.prev_zoom_params = None
        else:
            self.logger.log(LogLevel.DEBUG, "No previous zoom parameters to restore, redrawing current view.")
            self.update_fractal()  # 未確定時のキャンセルでも再描画

    def reset_zoom(self):
        """ 操作パネルの「描画リセット」ボタン押下時の処理（ズームパラメータを初期状態に戻して再描画） """
        self.logger.log(LogLevel.DEBUG, "Resetting zoom")
        self.zoom_params = {
            "center_x": 0.0,
            "center_y": 0.0,
            "width": 4.0,
            "height": 4.0,
#            "rotation": 0.0
        }
        self.prev_zoom_params = None
        self.update_fractal()

# 注意: FractalCanvas や ParameterPanel の __init__ も logger を受け取れるように修正が必要になる場合があります。
# 例: FractalCanvas の __init__
# def __init__(self, parent, logger=None):
#     self.logger = logger if logger else DebugLogger() # logger が渡されなければデフォルトで作成
#     self.logger.log(LogLevel.INIT, "Initializing FractalCanvas")
#     # ... rest of the init code ...

# 例: ParameterPanel の __init__
# def __init__(self, parent, update_callback, reset_callback, logger=None):
#     self.logger = logger if logger else DebugLogger()
#     self.logger.log(LogLevel.INIT, "Initializing ParameterPanel")
#     # ... rest of the init code ...
