import numpy as np # extentの計算にnp.ndarrayが使われる可能性があるのでインポート
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
        # FigureのfigsizeはMainWindowのリサイズイベントで動的に変更されますが、初期値として設定します。
        # dpiは解像度であり、ピクセル計算に使用されます。
        self.fig = Figure(figsize=(width/100, height/100), dpi=100, facecolor='black') # Matplotlib の Figure オブジェクトを作成
        # サブプロット（Axes）の設定
        self.ax = self.fig.add_subplot(111, facecolor='black') # Figure に Axes を追加
        self.ax.axis('off')

        # Matplotlib の図を Tkinter で表示するためのキャンバス
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.parent) # 作成
        self.canvas.get_tk_widget().configure(bg='black') # 背景色を黒に設定
        # fill=tk.BOTH, expand=True で親フレームいっぱいに広がる設定
        # aspect 比の維持は Figure のサイズと Axes で設定で
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True) # 配置

        # ズーム機能の設定
        self.set_zoom_callback(zoom_confirm_callback, zoom_cancel_callback) # 受取ったコールバックを保持
        from ui.zoom_function.zoom_selector import ZoomSelector # ZoomSelector を遅延インポート
        # ZoomSelector のインスタンスを作成し、保持
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
        # このメソッドはZoomSelectorから呼ばれますが、MainWindowのon_zoom_confirmに処理を委譲しているため
        # ここでの直接的な座標変換や描画更新は不要です。
        # ただし、ログ出力や、MainWindowへのコールバック呼び出しは適切です。
        if self.zoom_confirm_callback:
            # ZoomSelectorから渡される x, y, w, h, angle はRectManagerが管理する矩形の情報に基づいています。
            # これらは通常、回転前のデータ座標系の情報ですが、angleは回転角度を示します。
            # MainWindowのon_zoom_confirmで、これらの情報と現在のFigureの縦横比を使って新しい表示領域のパラメータを計算します。
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
        self.ax.clear() # 現在のAxesの内容をクリア
        self.ax.axis('off') # 軸を非表示に

        # AxesがFigure全体を占めるように位置を設定（念のため再度設定）
        self.fig.subplots_adjust(left=0, right=1, top=1, bottom=0)
        self.ax.set_position([0, 0, 1, 1])

        # 表示したい領域の幅と高さを計算
        # widthはparams["width"]（データ座標系での幅）を使用します。
        width = params["width"]
        # heightは、目標とする16:9の縦横比に基づいて計算します。
        # width / height = 16 / 9 より height = width * (9 / 16)
        height = width * (9 / 16)
        self.logger.log(LogLevel.DEBUG, f"描画範囲の計算: width={width:.4f}, height={height:.4f} (目標16:9)")

        # Axesの縦横比を設定。
        # 'auto'はAxesのboxのアスペクト比とextentのアスペクト比を一致させようとします。
        # Figureのサイズを16:9にしているので、Axesも16:9になり、extentもそれに合わせることで、
        # 期待通りの表示が得られるはずです。
        self.ax.set_aspect("auto")

        # imshowで画像を描画し、表示範囲 (extent) を設定
        # extent = [x_min, x_max, y_min, y_max]
        # 中心座標と幅、高さからextentを計算します。
        x_min = params["center_x"] - width / 2
        x_max = params["center_x"] + width / 2
        y_min = params["center_y"] - height / 2
        y_max = params["center_y"] + height / 2

        self.ax.imshow(fractal_image, extent=(x_min, x_max, y_min, y_max), origin="lower")

        # Figureの背景を非表示に（Axesのfacecolorが使用されます）
        self.fig.patch.set_visible(False)

        # キャンバスを再描画
        self.canvas.draw()

    def reset_zoom_selector(self):
        """ZoomSelector の状態をリセットする"""
        if self.zoom_selector:
            self.logger.log(LogLevel.CALL, "ZoomSelector のリセットを呼出し")
            self.zoom_selector.reset()
