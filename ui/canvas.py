import tkinter as tk
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from .zoom_function.debug_logger import DebugLogger
from .zoom_function.enums import LogLevel # LogLevel をインポート

class FractalCanvas:
    """ フラクタル描画キャンバスクラス """
    def __init__(self, master, width, height, logger, zoom_confirm_callback, zoom_cancel_callback):
        """ キャンバス初期化（MatplotlibのFigure を Tkinter ウィジェットに埋め込む）"""
        self.logger = logger
        self.logger.log(LogLevel.INIT, "FractalCanvas")

        self.parent = master
        self.fig = Figure(figsize=(6, 6), dpi=100)
        self.ax = self.fig.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.parent)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        self.zoom_confirm_callback = zoom_confirm_callback

        # ZoomSelector をインスタンス化（コールバック MainWindow から設定）
        from ui.zoom_function.zoom_selector import ZoomSelector
        self.zoom_selector = ZoomSelector(
            self.ax,
            on_zoom_confirm=lambda x, y, w, h, angle: self.zoom_confirmed(x, y, w, h, angle), # Accept 5 args, pass 5
            on_zoom_cancel=self.zoom_cancelled,
            logger=self.logger
        )

    def set_zoom_callback(self, zoom_confirm_callback, zoom_cancel_callback):
        """ ズーム確定・キャンセル時のコールバックを設定 """
        self.zoom_confirm_callback = zoom_confirm_callback
        self.zoom_cancel_callback = zoom_cancel_callback

    def zoom_confirmed(self, x, y, w, h, angle):
        """ ズーム確定 """
        self.logger.log(LogLevel.DEBUG, "Canvas zoom_confirmed called", {"x": x, "y": y, "w": w, "h": h, "angle": angle})
        if self.zoom_confirm_callback:
            self.zoom_confirm_callback(x, y, w, h, angle)

    def zoom_cancelled(self):
        """ ズームキャンセル """
        self.logger.log(LogLevel.DEBUG, "ズームキャンセル時のコールバック開始")
        if hasattr(self, 'zoom_cancel_callback') and self.zoom_cancel_callback:
            self.zoom_cancel_callback()

    def update_canvas(self, fractal_image, params):
        """ キャンバス更新 """
        self.ax.clear()
        self.ax.axis('off') # 座標軸は非表示
        self.fig.subplots_adjust(left=0, right=1, top=1, bottom=0)  # キャンバスのパディングを削除
        self.ax.set_position((0.0, 0.0, 1.0, 1.0))  # キャンバスの位置を調整
        aspect_ratio = fractal_image.shape[1] / fractal_image.shape[0]  # 画像のアスペクト比を取得
        width = params["width"]  # 幅を取得
        height = width / aspect_ratio  # アスペクト比を維持するために高さを計算
        self.ax.set_aspect("auto")  # 縦横比を自動調整
        self.ax.imshow(fractal_image, extent=(
            params["center_x"] - width / 2,
            params["center_x"] + width / 2,
            params["center_y"] - height / 2,
            params["center_y"] + height / 2
        ), origin="lower")
        self.fig.patch.set_visible(False)
        self.canvas.draw()
