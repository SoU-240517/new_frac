import tkinter as tk
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from .zoom_function.debug_logger import DebugLogger
from .zoom_function.enums import LogLevel

class FractalCanvas:
    """ フラクタル描画キャンバスクラス """

    def __init__(self, master, width, height, logger, zoom_confirm_callback, zoom_cancel_callback):
        """ キャンバス初期化（MatplotlibのFigure を Tkinter ウィジェットに埋め込む）"""
        self.logger = logger
        self.logger.log(LogLevel.INIT, "FractalCanvas")
        self.parent = master
        self.fig = Figure(figsize=(6, 6), dpi=100, facecolor='black')  # 背景黒に設定
        self.ax = self.fig.add_subplot(111, facecolor='black')  # 背景黒に設定
        self.ax.axis('off')  # 座標軸非表示

        # キャンバス設定
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.parent)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # 初期設定
        self.zoom_confirm_callback = zoom_confirm_callback
        self.zoom_cancel_callback = zoom_cancel_callback

        # ZoomSelector 初期化
        from ui.zoom_function.zoom_selector import ZoomSelector
        self.zoom_selector = ZoomSelector(
            self.ax,
            on_zoom_confirm=zoom_confirm_callback,
            on_zoom_cancel=zoom_cancel_callback,
            logger=self.logger
        )

        # 初期黒背景表示
        self.set_black_background()

    def set_black_background(self):
        """黒背景を設定"""
        self.ax.set_facecolor('black')
        self.fig.patch.set_facecolor('black')
        self.ax.axis('off')
        self.fig.subplots_adjust(left=0, right=1, top=1, bottom=0)
        self.canvas.draw()


    def set_zoom_callback(self, zoom_confirm_callback, zoom_cancel_callback):
        """ ズーム確定・キャンセル時のコールバックを設定 """
        self.zoom_confirm_callback = zoom_confirm_callback
        self.zoom_cancel_callback = zoom_cancel_callback

    def zoom_confirmed(self, x, y, w, h, angle):
        """ ズーム確定 """
        if self.zoom_confirm_callback:
            self.logger.log(LogLevel.SUCCESS, "ズーム確定時のコールバック呼出し", {"x": x, "y": y, "w": w, "h": h, "angle": angle})
            self.zoom_confirm_callback(x, y, w, h, angle)

    def zoom_cancelled(self):
        """ ズームキャンセル """
        if hasattr(self, 'zoom_cancel_callback') and self.zoom_cancel_callback:
            self.logger.log(LogLevel.SUCCESS, "ズームキャンセル時のコールバック呼出し")
            self.zoom_cancel_callback()

    def update_canvas(self, fractal_image, params) -> None:
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

    def reset_zoom_selector(self):
        """ ZoomSelector の状態をリセットする """
        if self.zoom_selector:
            self.logger.log(LogLevel.CALL, "ZoomSelector のリセットを呼出し")
            self.zoom_selector.reset()
