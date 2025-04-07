import tkinter as tk
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

class FractalCanvas:
    """ フラクタル描画キャンバスクラス """
    def __init__(self, parent):
        """ キャンバス初期化（MatplotlibのFigure を Tkinter ウィジェットに埋め込む）"""
        print("初期化 : CLASS→ FractalCanvas : FILE→ canvas.py")
        self.parent = parent
        self.fig = Figure(figsize=(6, 6), dpi=100)
        self.ax = self.fig.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.parent)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # ZoomSelector をインスタンス化（コールバック MainWindow から設定）
        from ui.zoom_function.zoom_selector import ZoomSelector
        self.zoom_selector = ZoomSelector(
            self.ax,
            on_zoom_confirm=self.zoom_confirmed,
            on_zoom_cancel=self.zoom_cancelled
        )

    def set_zoom_callback(self, zoom_confirm_callback, zoom_cancel_callback):
        """ ズーム確定・キャンセル時のコールバックを設定 """
        print("コールバック設定 : set_zoom_callback : CLASS→ FractalCanvas : FILE→ canvas.py")
        self.zoom_confirm_callback = zoom_confirm_callback
        self.zoom_cancel_callback = zoom_cancel_callback

    def zoom_confirmed(self, zoom_params):
        """ ズーム確定時のコールバック """
        print("ズーム確定 : zoom_confirmed : CLASS→ FractalCanvas : FILE→ canvas.py")
        if hasattr(self, 'zoom_confirm_callback') and self.zoom_confirm_callback:
            new_zoom_params = {
                "center_x": zoom_params[0],
                "center_y": zoom_params[1],
                "width": zoom_params[2],
                "height": zoom_params[3],
#                "rotation": zoom_params[4]
            }
            self.zoom_confirm_callback(new_zoom_params)

    def zoom_cancelled(self):
        """ ズームキャンセル時のコールバック """
        print("ズームキャンセル : zoom_cancelled : CLASS→ FractalCanvas : FILE→ canvas.py")
        if hasattr(self, 'zoom_cancel_callback') and self.zoom_cancel_callback:
            self.zoom_cancel_callback()

    def update_canvas(self, fractal_image, params):
        """ キャンバスを更新し、指定されたフラクタル画像を描画 """
        print("更新 : キャンバス : update_canvas : CLASS→ FractalCanvas : FILE→ canvas.py")
        self.ax.clear()  # キャンバスをクリア
        self.ax.axis('off')  # 座標軸は非表示
        self.fig.subplots_adjust(left=0, right=1, top=1, bottom=0)  # キャンバスのパディングを削除
        self.ax.set_position([0, 0, 1, 1])  # キャンバスの位置を調整
        aspect_ratio = fractal_image.shape[1] / fractal_image.shape[0]  # 画像のアスペクト比を取得
        width = params["width"]  # 幅を取得
        height = width / aspect_ratio  # アスペクト比を維持するために高さを計算

        self.ax.set_aspect("auto")  # 縦横比を自動調整
        self.ax.imshow(fractal_image, extent=[
            params["center_x"] - width / 2,
            params["center_x"] + width / 2,
            params["center_y"] - height / 2,
            params["center_y"] + height / 2
        ], origin="lower")
        self.fig.patch.set_visible(False)
        self.canvas.draw()
