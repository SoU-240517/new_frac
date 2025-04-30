import numpy as np
import tkinter as tk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from .zoom_function.debug_logger import DebugLogger
from .zoom_function.enums import LogLevel
from typing import Callable, Optional, Dict, Tuple

class FractalCanvas:
    """FractalCanvas クラス
    - フラクタル画像の表示と更新を管理
    - ズーム機能の制御
    - ユーザーインターフェースの描画
    Attributes:
        fig: MatplotlibのFigure
        ax: MatplotlibのAxes
        canvas: Tkinterのキャンバス
        zoom_selector: ズーム選択機能を管理するZoomSelector
        zoom_confirm_callback: ズーム確定時のコールバック関数
        zoom_cancel_callback: ズームキャンセル時のコールバック関数
        logger: デバッグログを管理するLogger
        parent: Tkinterの親ウィジェット
    """

    def __init__(self,
                master: tk.Tk,
                width: int, height: int,
                logger: DebugLogger,
                zoom_confirm_callback: Callable, zoom_cancel_callback: Callable,
                config: Dict[str, float]
    ):
        """FractalCanvas クラスのコンストラクタ
        - FigureとAxesの初期化
        - ズーム機能の設定
        - 背景色の設定

        Args:
            master: Tkinterの親ウィジェット
            width: キャンバスの幅 (ピクセル)
            height: キャンバスの高さ (ピクセル)
            logger: デバッグログ用のLogger
            zoom_confirm_callback: ズーム確定時のコールバック関数
            zoom_cancel_callback: ズームキャンセル時のコールバック関数
            config: ZoomSelectorの設定
        """
        self.logger = logger
        self.parent = master
        self.config = config
        self.facecolor = self.config.get("canvas_settings", {}).get("facecolor", "black")

        # FigureとAxesの初期化
        self._setup_figure(width, height)

        # ズーム機能の設定
        self.set_zoom_callback(zoom_confirm_callback, zoom_cancel_callback)
        self._setup_zoom()

        # 背景色の設定
        self._set_black_background()

    def _setup_figure(self, width: int, height: int) -> None:
        """MatplotlibのFigureとAxesの設定
        - Figureの設定
        - Axesの設定
        - Tkinterキャンバスの設定

        Args:
            width: キャンバスの幅 (ピクセル)
            height: キャンバスの高さ (ピクセル)
        """
        config_dpi = self.config.get("canvas_settings", {}).get("config_dpi", 100)

        # Figure の設定
        self.fig = Figure(
            figsize=(width/config_dpi, height/config_dpi), # DPI=100のためのサイズ調整
            dpi=config_dpi, # 1インチあたりのドット数
            facecolor=self.facecolor
        )

        # Axes の設定
        self.ax = self.fig.add_subplot(111, facecolor=self.facecolor)
        self.ax.axis('off')

        # Tkinter キャンバスの設定
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.parent)
        self.canvas.get_tk_widget().configure(bg=self.facecolor)
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
        """ズーム機能の設定と初期化
        - ZoomSelectorのインスタンスを作成
        - ズームイベントのコールバックを設定
        - デバッグログの設定
        """
        # ZoomSelector を遅延インポート
        from ui.zoom_function.zoom_selector import ZoomSelector

        self.logger.log(LogLevel.INIT, "ZoomSelector クラスのインスタンスを作成")
        self.zoom_selector = ZoomSelector(
            self.ax,
            on_zoom_confirm=self.zoom_confirmed,
            on_zoom_cancel=self.zoom_cancelled,
            logger=self.logger,
            config=self.config
        )

    def _set_black_background(self) -> None:
        """キャンバスの背景を黒に設定
        - Axesの背景色を黒に設定
        - Figureの背景色を黒に設定
        - 変更を反映
        """
        self.ax.set_facecolor(self.facecolor)
        self.fig.patch.set_facecolor(self.facecolor)
        self.canvas.draw()

    def zoom_confirmed(
        self,
        x: float, y: float,
        w: float, h: float,
        angle: float) -> None:
        """ズーム確定時の処理
        - ズーム選択範囲のパラメータを受け取り、コールバック関数を呼び出す

        Args:
            x: ズーム選択範囲の左上X座標
            y: ズーム選択範囲の左上Y座標
            w: ズーム選択範囲の幅
            h: ズーム選択範囲の高さ
            angle: ズーム選択範囲の回転角度 (度)
        """
        if self.zoom_confirm_callback:
            self.logger.log(
                LogLevel.CALL,
                "ズーム確定時のコールバック呼出し",
                {"x": x, "y": y, "w": w, "h": h, "angle": angle}
            )
            self.zoom_confirm_callback(x, y, w, h, angle)

    def zoom_cancelled(self) -> None:
        """ズームキャンセル時の処理
        - ズームキャンセル時にコールバック関数を呼び出す
        """
        if hasattr(self, 'zoom_cancel_callback') and self.zoom_cancel_callback:
            self.logger.log(LogLevel.CALL, "ズームキャンセル時のコールバック呼出し")
            self.zoom_cancel_callback()

    def update_canvas(
        self,
        fractal_image: np.ndarray,
        params: Dict[str, float]) -> None:
        """フラクタル画像の更新
        - 新しいフラクタル画像を描画する

        Args:
            fractal_image: フラクタル画像データ (NumPy配列)
            params: 描画パラメータ
                - center_x: 中心座標X
                - center_y: 中心座標Y
                - width: 描画範囲の幅
                - rotation: 回転角度
        """
        # Axesのクリアと設定
        self.ax.clear()
        self.ax.axis('off')
        self.fig.subplots_adjust(left=0, right=1, top=1, bottom=0)
        self.ax.set_position([0, 0, 1, 1])

        # 16:9のアスペクト比を維持するための計算
        width = params["width"]
        height = width * (9 / 16) # 16:9のアスペクト比を維持
        self.logger.log(LogLevel.SUCCESS, f"描画範囲の計算結果: width={width:.4f}, height={height:.4f} (目標16:9)")

        self.ax.set_aspect("auto") # アスペクト比を自動調整

        # 描画範囲の計算
        x_min = params["center_x"] - width / 2
        x_max = params["center_x"] + width / 2
        y_min = params["center_y"] - height / 2
        y_max = params["center_y"] + height / 2

        # 画像の描画
        self.ax.imshow(
            fractal_image,
            extent=(x_min, x_max, y_min, y_max), # 描画範囲の設定
            origin="lower" # 座標系の原点を左下に設定
        )

        self.fig.patch.set_visible(False) # Figureの余白を非表示
        self.canvas.draw() # 変更を反映

    def reset_zoom_selector(self) -> None:
        """ズームセレクタのリセット
        - ズーム選択状態を初期状態に戻す
        """
        if self.zoom_selector:
            self.logger.log(LogLevel.CALL, "ZoomSelector のリセットを呼出し")
            self.zoom_selector.reset()
