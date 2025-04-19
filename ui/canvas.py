import tkinter as tk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from .zoom_function.debug_logger import DebugLogger
from .zoom_function.enums import LogLevel

class FractalCanvas:
    """キャンバスクラス
    - 役割:
        - MatplotlibのFigureをTkinterに埋め込み、フラクタル描画を行うキャンバス
    """
    def __init__(self, master, width, height, logger, zoom_confirm_callback, zoom_cancel_callback):
        """キャンバスのコンストラクタ（親: MainWindow）

        Args:
            master (tkinter.Tk): Tkinter ルートウィンドウ
            width (int): キャンバスの幅
            height (int): キャンバスの高さ
            logger (DebugLogger): ログ出力用の DebugLogger インスタンス
            zoom_confirm_callback (function): ズーム確定時のコールバック関数: MainWindow.on_zoom_confirm
            zoom_cancel_callback (function): ズームキャンセル時のコールバック関数: MainWindow.on_zoom_cancel

        Returns:
            None
        """
        self.logger = logger
        self.parent = master

        # 図（Figure）の設定
        self.fig = Figure(figsize=(6, 6), dpi=100, facecolor='black') # Matplotlib の Figure オブジェクトを作成
        # サブプロット（Axes）の設定
        self.ax = self.fig.add_subplot(111, facecolor='black') # Figure に Axes を追加
        self.ax.axis('off')

        # Matplotlib の図を Tkinter で表示するためのキャンバス
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.parent) # 作成
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True) # 配置

        # ズーム機能の設定
        self.set_zoom_callback(zoom_confirm_callback, zoom_cancel_callback) # 受取ったコールバックを保持
        from ui.zoom_function.zoom_selector import ZoomSelector # ZoomSelector を遅延インポート
        self.logger.log(LogLevel.INIT, "ZoomSelector 初期化開始")
        self.zoom_selector = ZoomSelector(
            self.ax,
            on_zoom_confirm=zoom_confirm_callback,
            on_zoom_cancel=zoom_cancel_callback,
            logger=self.logger)
        self.logger.log(LogLevel.INIT, "キャンバス背景設定開始")

        self._set_black_background()

    def _set_black_background(self):
        """黒背景を設定"""
        self.ax.set_facecolor('black')
        self.fig.patch.set_facecolor('black')
#        self.ax.axis('off')
        self.fig.subplots_adjust(left=0, right=1, top=1, bottom=0)
        self.canvas.draw()

    def set_zoom_callback(self, zoom_confirm_callback, zoom_cancel_callback):
        """ズーム確定・キャンセル時のコールバックを設定"""
        self.zoom_confirm_callback = zoom_confirm_callback
        self.zoom_cancel_callback = zoom_cancel_callback

    def zoom_confirmed(self, x, y, w, h, angle):
        """ズーム確定

        Args:
            x (float): 矩形左上の x 座標
            y (float): 矩形左上の y 座標
            w (float): 矩形の幅
            h (float): 矩形の高さ
            angle (float): 矩形の回転角度
        """
        if self.zoom_confirm_callback:
            self.logger.log(LogLevel.SUCCESS, "ズーム確定時のコールバック呼出し", {"x": x, "y": y, "w": w, "h": h, "angle": angle})
            self.zoom_confirm_callback(x, y, w, h, angle)

    def zoom_cancelled(self):
        """ズームキャンセル"""
        if hasattr(self, 'zoom_cancel_callback') and self.zoom_cancel_callback:
            self.logger.log(LogLevel.SUCCESS, "ズームキャンセル時のコールバック呼出し")
            self.zoom_cancel_callback()

    def update_canvas(self, fractal_image, params):
        """キャンバス更新

        Args:
            fractal_image (np.ndarray): フラクタル画像
            params (dict): パラメータ辞書
        """
        self.ax.clear()
        self.ax.axis('off')
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
        """ZoomSelector の状態をリセットする"""
        if self.zoom_selector:
            self.logger.log(LogLevel.CALL, "ZoomSelector のリセットを呼出し")
            self.zoom_selector.reset()
