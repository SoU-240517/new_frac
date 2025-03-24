import tkinter as tk
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

class FractalCanvas:
    def __init__(self, parent):
        """
        フラクタル描画キャンバスの初期化。MatplotlibのFigureをTkinterウィジェットに埋め込みます。
        """
        print("====== キャンバスの初期化開始:（def __init__）")  # ← debug print★
        self.parent = parent
        self.fig = Figure(figsize=(6, 6), dpi=100)
        self.ax = self.fig.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.parent)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # ZoomSelector をインスタンス化（コールバックは後述の MainWindow から設定）
        from ui.zoom_selector import ZoomSelector
        self.zoom_selector = ZoomSelector(self.ax, on_zoom_confirm=self.zoom_confirmed, on_zoom_cancel=self.zoom_cancelled)

    def set_zoom_callback(self, zoom_confirm_callback, zoom_cancel_callback):
        print("====== コールバックの設定開始:（def set_zoom_callback）")  # ← debug print★
        self.zoom_confirm_callback = zoom_confirm_callback
        self.zoom_cancel_callback = zoom_cancel_callback

    def zoom_confirmed(self, zoom_params):
        print("====== ズーム確定:（def zoom_confirmed）")  # ← debug print★
        if hasattr(self, 'zoom_confirm_callback') and self.zoom_confirm_callback:
            self.zoom_confirm_callback(zoom_params)

    def zoom_cancelled(self):
        print("====== ズームキャンセル:（def zoom_cancelled）")  # ← debug print★
        if hasattr(self, 'zoom_cancel_callback') and self.zoom_cancel_callback:
            self.zoom_cancel_callback()

    def update_canvas(self, fractal_image, params):
        """
        キャンバスを更新し、指定されたフラクタル画像を描画します。
        指定された画像をキャンバスに表示し、フラクタルのタイプに基づいてタイトルを設定します。
        画像は [-2, 2] の範囲で描画され、アスペクト比を維持します。

        引数:
            fractal_image (numpy.ndarray): 描画するフラクタル画像
            params (dict): フラクタルのパラメータ（'fractal_type' キーを含む）
        """
        print("====== キャンバスの更新開始:（def update_canvas）")  # ← debug print★
        self.ax.clear()
        self.ax.axis('off')  # 座標軸を非表示
        self.fig.subplots_adjust(left=0, right=1, top=1, bottom=0)
        self.ax.set_position([0, 0, 1, 1])
        aspect_ratio = fractal_image.shape[1] / fractal_image.shape[0]  # 画像のアスペクト比を取得
        width = params["width"]
        height = width / aspect_ratio  # アスペクト比を維持するために高さを計算

        self.ax.set_aspect("auto")  # 縦横比を自動調整
        self.ax.imshow(fractal_image, extent=[
            params["center_x"] - width / 2, params["center_x"] + width / 2,
            params["center_y"] - height / 2, params["center_y"] + height / 2
        ], origin="lower")
        self.fig.patch.set_visible(False)
        self.canvas.draw()
