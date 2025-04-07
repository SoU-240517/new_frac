from ui.canvas import FractalCanvas
from ui.parameter_panel import ParameterPanel
import tkinter as tk
import numpy as np
from tkinter import ttk
from fractal.render import render_fractal

class MainWindow:
    def __init__(self, root):
        """
        フラクタル描画アプリケーションのメインウィンドウ初期化。
        キャンバスとパラメータパネルを含む左右分割レイアウトを作成し、
        ズーム操作の状態管理も行います。
        """
        print("初期化 : メインウィンドウ : __init__ / main_window.py")  # debug_log(print)
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
        print("描画更新開始 : update_fractal / main_window.py")  # debug_log(print)
        params = self.parameter_panel.get_parameters()  # パネルからパラメータを取得
        params.update(self.zoom_params)  # ズーム情報をパラメータに追加
        fractal_image = render_fractal(params)
        self.fractal_canvas.update_canvas(fractal_image, params)  # キャンバスを更新

    def on_zoom_confirm(self, new_zoom_params):
        """
        ズーム確定時のコールバック
        - 縦横比を調整
        - ズームレベルに応じて反復回数を自動調整
        """
        print(f"=== Zoom Confirmed Callback : on_zoom_confirm / main_window.py ===")
        if new_zoom_params == self.zoom_params:
            return  # ズームパラメータが変わっていないなら何もしない

        # ズーム確定前の状態を保存（キャンセル機能用）
        self.prev_zoom_params = self.zoom_params.copy()

        # 縦横比補正
        aspect_ratio = self.fractal_canvas.fig.get_size_inches()[0] / self.fractal_canvas.fig.get_size_inches()[1]
        new_width = new_zoom_params[2]
        new_height = new_width / aspect_ratio  # 縦横比を維持

        # ズームレベルに応じて `max_iterations` を増やす
        zoom_factor = self.zoom_params["width"] / new_width  # ズーム倍率
        new_max_iterations = min(1000, max(int(self.parameter_panel.max_iter_var.get()), int(100 * np.log2(zoom_factor + 1))))

        # 新しいズームパラメータを適用
        self.zoom_params = {
            "center_x": new_zoom_params[0],  # [0] の部分は、以前は["center_x"]。バグる。なんで？
            "center_y": new_zoom_params[1],  # [1] の部分は、以前は["center_y"]。バグる。なんで？
            "width": new_width,
            "height": new_height,
            "rotation": new_zoom_params[0]  # [0] の部分は、以前は["rotation"]。バグる。なんで？
        }

        # 反復回数を更新
        self.parameter_panel.max_iter_var.set(str(new_max_iterations))

        # 再描画
        self.update_fractal()

    def on_zoom_cancel(self):
        """
        ズームキャンセル時のコールバック
        既にズーム確定後の場合は直前の状態に戻し、未確定の場合は単に再描画
        """
        print("=== Zoom Cancelled Callback : on_zoom_cancel / main_window.py ===")
        if self.prev_zoom_params is not None:  # ズーム確定済みの場合
            self.zoom_params = self.prev_zoom_params.copy()  # 状態を復元
            self.update_fractal()  # 再描画を実行
            self.prev_zoom_params = None  # 再描画後にクリア
        else:
            self.update_fractal()  # 未確定時のキャンセルでも再描画

    def reset_zoom(self):
        """
        操作パネルの「描画リセット」ボタン押下時の処理。
        ズームパラメータを初期状態に戻して再描画。
        """
        print("描画リセット : reset_zoom / main_window.py")  # debug_log(print)
        self.zoom_params = {"center_x": 0.0, "center_y": 0.0, "width": 4.0, "height": 4.0, "rotation": 0.0}
        self.prev_zoom_params = None
        self.update_fractal()
