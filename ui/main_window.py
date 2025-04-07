import tkinter as tk
import numpy as np
from tkinter import ttk
from ui.canvas import FractalCanvas
from ui.parameter_panel import ParameterPanel
from fractal.render import render_fractal

class MainWindow:
    """ フラクタル描画アプリケーションのメインウィンドウクラス """
    def __init__(self, root):
        """ フラクタル描画アプリケーションのメインウィンドウ初期化（ズーム操作の状態管理も行う） """
        print('\033[34m'+'INI: MainWindow: main_window.py'+'\033[0m')

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
        self.fractal_canvas = FractalCanvas(self.canvas_frame)  # キャンバス初期化
        self.fractal_canvas.set_zoom_callback(self.on_zoom_confirm, self.on_zoom_cancel)  # コールバックの設定
        self.parameter_panel = ParameterPanel(self.control_frame, self.update_fractal, reset_callback=self.reset_zoom)  # パラメータパネル初期化

        self.update_fractal()  # 初期描画

    def update_fractal(self, *args):
        """ 最新パラメータにズーム情報を上書きしてフラクタルを再描画 """
        print('\033[32m'+'update_fractal: MainWindow: main_window.py'+'\033[0m')
        panel_params = self.parameter_panel.get_parameters()  # パネルからパラメータを取得
        panel_params.update(self.zoom_params)  # ズーム情報を上書き
        fractal_image = render_fractal(panel_params)
        self.fractal_canvas.update_canvas(fractal_image, panel_params)  # キャンバスを更新

    def on_zoom_confirm(self, new_zoom_params):
        """ ズーム確定時のコールバック（縦横比を調整し、ズームレベルに応じて反復回数を自動調整） """
        print('\033[32m'+'on_zoom_confirm Callback: MainWindow: main_window.py'+'\033[0m')
        if new_zoom_params == self.zoom_params:
            return

        # ズーム確定前の状態を保存（キャンセル機能用）
        self.prev_zoom_params = self.zoom_params.copy()

        # 縦横比補正
        aspect_ratio = self.fractal_canvas.fig.get_size_inches()[0] / self.fractal_canvas.fig.get_size_inches()[1]
        new_width = new_zoom_params["width"]
        new_height = new_width / aspect_ratio  # 縦横比を維持

        # ズームレベルに応じて `max_iterations` を増やす
        zoom_factor = self.zoom_params["width"] / new_width  # ズーム倍率
        new_max_iterations = min(1000, max(int(self.parameter_panel.max_iter_var.get()), int(100 * np.log2(zoom_factor + 1))))

        # 新しいズームパラメータを適用
        self.zoom_params = {
            "center_x": new_zoom_params["center_x"],
            "center_y": new_zoom_params["center_y"],
            "width": new_width,
            "height": new_height,
#            "rotation": new_zoom_params["rotation"]
        }

        self.parameter_panel.max_iter_var.set(str(new_max_iterations))  # 反復回数を更新
        self.update_fractal()

    def on_zoom_cancel(self):
        """ ズームキャンセル時のコールバック """
        print('\033[32m'+'on_zoom_cancel Callback: MainWindow: main_window.py'+'\033[0m')
        if self.prev_zoom_params is not None:  # 直前のズーム領域がある場合
            self.zoom_params = self.prev_zoom_params.copy()  # 直前のズーム領域を復元
            self.update_fractal()
            self.prev_zoom_params = None
        else:
            self.update_fractal()  # 未確定時のキャンセルでも再描画

    def reset_zoom(self):
        """ 操作パネルの「描画リセット」ボタン押下時の処理（ズームパラメータを初期状態に戻して再描画） """
        print('\033[32m'+'reset_zoom: MainWindow: main_window.py'+'\033[0m')
        self.zoom_params = {
            "center_x": 0.0,
            "center_y": 0.0,
            "width": 4.0,
            "height": 4.0,
#            "rotation": 0.0
        }
        self.prev_zoom_params = None
        self.update_fractal()
