import tkinter as tk
from tkinter import ttk
from ui.canvas import FractalCanvas
from ui.parameter_panel import ParameterPanel
from fractal.render import render_fractal

class MainWindow:
    def __init__(self, root):
        """
        フラクタル描画アプリケーションのメインウィンドウ初期化。
        キャンバスとパラメータパネルを含む左右分割レイアウトを作成し、
        ズーム操作の状態管理も行います。
        """
        self.root = root
        self.root.title("フラクタル描画アプリケーション")
        self.root.geometry("1200x800")

        # ズームパラメータ（初期状態）
        self.zoom_params = {"center_x": 0.0, "center_y": 0.0, "width": 4.0, "height": 4.0, "rotation": 0.0}
        self.prev_zoom_params = None

        # メインフレーム（左右分割）
        self.main_frame = ttk.PanedWindow(root, orient=tk.HORIZONTAL)
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        # 左側：キャンバスフレーム
        self.canvas_frame = ttk.Frame(self.main_frame)
        self.main_frame.add(self.canvas_frame, weight=3)

        # 右側：操作パネルフレーム
        self.control_frame = ttk.Frame(self.main_frame)
        self.main_frame.add(self.control_frame, weight=1)

        # キャンバスとパラメータパネルの初期化
        self.fractal_canvas = FractalCanvas(self.canvas_frame)
        # ZoomSelector のコールバックを MainWindow のメソッドに設定
        self.fractal_canvas.set_zoom_callback(self.on_zoom_confirm, self.on_zoom_cancel)
        self.parameter_panel = ParameterPanel(self.control_frame, self.update_fractal, reset_callback=self.reset_zoom)

        # 初期描画
        self.update_fractal()

    def update_fractal(self, *args):
        """
        パラメータパネルの最新パラメータに、ズーム情報を上書きしてフラクタルを再描画。
        """
        # パネルからパラメータを取得
        params = self.parameter_panel.get_parameters()
        # ズーム情報をパラメータに追加
        params.update(self.zoom_params)
        fractal_image = render_fractal(params)
        # キャンバスを更新
        self.fractal_canvas.update_canvas(fractal_image, params)

    def on_zoom_confirm(self, new_zoom_params):
        """
        ZoomSelector によるズーム確定時のコールバック。
        直前のズーム状態を保存し、新しいズームパラメータに更新して再描画。
        """
        self.prev_zoom_params = self.zoom_params.copy()
        self.zoom_params = new_zoom_params
        self.update_fractal()

    def on_zoom_cancel(self):
        """
        ズームキャンセル時のコールバック。
        既にズーム確定後の場合は直前の状態に戻し、未確定の場合は単に再描画。
        """
        if self.prev_zoom_params is not None:
            self.zoom_params = self.prev_zoom_params
            self.prev_zoom_params = None
        self.update_fractal()

    def reset_zoom(self):
        """
        操作パネルの「描画リセット」ボタン押下時の処理。
        ズームパラメータを初期状態に戻して再描画。
        """
        self.zoom_params = {"center_x": 0.0, "center_y": 0.0, "width": 4.0, "height": 4.0, "rotation": 0.0}
        self.prev_zoom_params = None
        self.update_fractal()
