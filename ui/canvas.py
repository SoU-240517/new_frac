import numpy as np # extentの計算にnp.ndarrayが使われる可能性があるのでインポート
import tkinter as tk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from .zoom_function.debug_logger import DebugLogger
from .zoom_function.enums import LogLevel
from typing import Callable, Optional, Dict, Tuple

class FractalCanvas:
    """フラクタル描画用のキャンバスクラス

    キャンバスの主な機能：
    - MatplotlibのFigureをTkinterに埋め込み
    - フラクタル画像の表示と更新
    - ズーム機能の管理
    """

    def __init__(
        self, master: tk.Tk,
        width: int, height: int,
        logger: DebugLogger,
        zoom_confirm_callback: Callable, zoom_cancel_callback: Callable) -> None:
        """FractalCanvas クラスのコンストラクタ

        Args:
            master: Tkinterのルートウィンドウ
            width: キャンバスの幅（ピクセル）
            height: キャンバスの高さ（ピクセル）
            logger: デバッグログ用のLogger
            zoom_confirm_callback: ズーム確定時のコールバック関数
            zoom_cancel_callback: ズームキャンセル時のコールバック関数
        """
        self.logger = logger
        self.parent = master
        self._setup_figure(width, height)
        self.set_zoom_callback(zoom_confirm_callback, zoom_cancel_callback)
        self._setup_zoom()
        self._set_black_background()

    def _setup_figure(self, width: int, height: int) -> None:
        """MatplotlibのFigureとAxesの設定

        Args:
            width: キャンバスの幅（ピクセル）
            height: キャンバスの高さ（ピクセル）
        """
        # Figureの初期設定
        self.fig = Figure(
            figsize=(width/100, height/100),
            dpi=100,
            facecolor='black'
        )

        # Axesの設定
        self.ax = self.fig.add_subplot(111, facecolor='black')
        self.ax.axis('off')

        # Tkinterキャンバスの設定
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.parent)
        self.canvas.get_tk_widget().configure(bg='black')
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def set_zoom_callback(self, zoom_confirm_callback: Callable, zoom_cancel_callback: Callable) -> None:
        """ズーム確定・キャンセル時のコールバックを設定

        Args:
            zoom_confirm_callback: ズーム確定時のコールバック関数
            zoom_cancel_callback: ズームキャンセル時のコールバック関数
        """
        self.zoom_confirm_callback = zoom_confirm_callback
        self.zoom_cancel_callback = zoom_cancel_callback

    def _setup_zoom(self) -> None:
        """ズーム機能の設定"""
        from ui.zoom_function.zoom_selector import ZoomSelector
        self.logger.log(LogLevel.INIT, "ZoomSelector 初期化開始")
        self.zoom_selector = ZoomSelector(
            self.ax,
            on_zoom_confirm=self.zoom_confirmed,
            on_zoom_cancel=self.zoom_cancelled,
            logger=self.logger
        )

    def _set_black_background(self) -> None:
        """キャンバスの背景を黒に設定"""
        self.ax.set_facecolor('black')
        self.fig.patch.set_facecolor('black')
        self.canvas.draw()

    def zoom_confirmed(
        self,
        x: float, y: float,
        w: float, h: float,
        angle: float) -> None:
        """ズーム確定時の処理

        Args:
            x: 矩形左上のx座標
            y: 矩形左上のy座標
            w: 矩形の幅
            h: 矩形の高さ
            angle: 矩形の回転角度（度）
        """
        if self.zoom_confirm_callback:
            self.logger.log(
                LogLevel.SUCCESS,
                "ズーム確定時のコールバック呼出し",
                {"x": x, "y": y, "w": w, "h": h, "angle": angle}
            )
            self.zoom_confirm_callback(x, y, w, h, angle)

    def zoom_cancelled(self) -> None:
        """ズームキャンセル時の処理"""
        if hasattr(self, 'zoom_cancel_callback') and self.zoom_cancel_callback:
            self.logger.log(LogLevel.SUCCESS, "ズームキャンセル時のコールバック呼出し")
            self.zoom_cancel_callback()

    def update_canvas(
        self,
        fractal_image: np.ndarray,
        params: Dict[str, float]) -> None:
        """フラクタル画像の更新

        Args:
            fractal_image: フラクタル画像データ
            params: 描画パラメータ
                - center_x: 中心座標X
                - center_y: 中心座標Y
                - width: 描画範囲の幅
        """
        self.ax.clear()
        self.ax.axis('off')
        self.fig.subplots_adjust(left=0, right=1, top=1, bottom=0)
        self.ax.set_position([0, 0, 1, 1])

        # 16:9のアスペクト比を維持
        width = params["width"]
        height = width * (9 / 16)
        self.logger.log(LogLevel.DEBUG, f"描画範囲の計算: width={width:.4f}, height={height:.4f} (目標16:9)")

        self.ax.set_aspect("auto")

        # 描画範囲の計算
        x_min = params["center_x"] - width / 2
        x_max = params["center_x"] + width / 2
        y_min = params["center_y"] - height / 2
        y_max = params["center_y"] + height / 2

        self.ax.imshow(
            fractal_image,
            extent=(x_min, x_max, y_min, y_max),
            origin="lower"
        )

        self.fig.patch.set_visible(False)
        self.canvas.draw()

    def reset_zoom_selector(self) -> None:
        """ズームセレクタのリセット"""
        if self.zoom_selector:
            self.logger.log(LogLevel.CALL, "ZoomSelector のリセットを呼出し")
            self.zoom_selector.reset()
