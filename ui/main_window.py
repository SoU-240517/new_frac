import tkinter as tk
from tkinter import ttk
from ui.canvas import FractalCanvas
from ui.parameter_panel import ParameterPanel
from fractal.render import render_fractal

class MainWindow:
    def __init__(self, root):
        """
        フラクタル描画アプリケーションのメイン ウィンドウを初期化します。
        アプリケーションのルート ウィンドウを設定し、キャンバス フレームと
        コントロール パネル フレームを含む分割レイアウトを作成し、
        フラクタル キャンバスとパラメーター パネルを初期化し、
        初期フラクタル レンダリングを実行します。

        引数:
            root (tk.Tk): アプリケーションのルート Tkinter ウィンドウ。
        """
        self.root = root
        self.root.title("フラクタル描画アプリケーション")
        self.root.geometry("1200x800")

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
        self.parameter_panel = ParameterPanel(self.control_frame, self.update_fractal)

        # 初期描画
        self.update_fractal()

    def update_fractal(self, *args):
        """
        現在のパラメータを使用してフラクタルを再描画します。
        パラメータパネルから最新のパラメータを取得し、フラクタルを計算・描画し、
        キャンバスを更新します。

        引数:
            *args: 追加の引数（イベントハンドリング用）
        """
        # パネルからパラメータを取得
        params = self.parameter_panel.get_parameters()
        # フラクタル描画（計算・着色）
        fractal_image = render_fractal(params)
        # キャンバスを更新
        self.fractal_canvas.update_canvas(fractal_image, params)
