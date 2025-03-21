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
        self.root = root  # Tkinter のルートウィンドウ
        self.root.title("フラクタル描画アプリケーション")  # ウィンドウタイトルの設定
        self.root.geometry("1200x800")  # ウィンドウサイズの設定

        # ズームパラメータ（初期状態）
        self.zoom_params = {"center_x": 0.0, "center_y": 0.0, "width": 4.0, "height": 4.0, "rotation": 0.0}  # ズームパラメータ
        self.prev_zoom_params = None  # 前回のズームパラメータを保存するための変数

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
        self.fractal_canvas = FractalCanvas(self.canvas_frame)  # キャンバスの初期化

        # ZoomSelector のコールバックを MainWindow のメソッドに設定
        self.fractal_canvas.set_zoom_callback(self.on_zoom_confirm, self.on_zoom_cancel)  # コールバックの設定
        self.parameter_panel = ParameterPanel(self.control_frame, self.update_fractal, reset_callback=self.reset_zoom)  # パラメータパネルの初期化

        # 初期描画
        self.update_fractal()

    def update_fractal(self, *args):
        """
        パラメータパネルの最新パラメータにズーム情報を上書きしてフラクタルを再描画。
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
        ズーム確定時のコールバック。
        - 縦横比を調整
        - ズームレベルに応じて反復回数を自動調整
        """
        if new_zoom_params == self.zoom_params:
            return  # ズームパラメータが変わっていないなら何もしない

        # ズーム確定前の状態を保存（キャンセル機能用）
        self.prev_zoom_params = self.zoom_params.copy()

        # 縦横比補正
        aspect_ratio = self.fractal_canvas.fig.get_size_inches()[0] / self.fractal_canvas.fig.get_size_inches()[1]
        new_width = new_zoom_params["width"]
        new_height = new_width / aspect_ratio  # 縦横比を維持

        # ズームレベルに応じて `max_iterations` を増やす
        zoom_factor = self.zoom_params["width"] / new_width  # ズーム倍率
        new_max_iterations = min(1000, int(self.parameter_panel.max_iter_var.get()) * zoom_factor)

        # 新しいズームパラメータを適用
        self.zoom_params = {
            "center_x": new_zoom_params["center_x"],
            "center_y": new_zoom_params["center_y"],
            "width": new_width,
            "height": new_height,
            "rotation": new_zoom_params["rotation"]
        }

        # 反復回数を更新
        self.parameter_panel.max_iter_var.set(str(new_max_iterations))

        # 再描画
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
