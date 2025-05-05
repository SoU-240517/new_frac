import numpy as np
import tkinter as tk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from typing import Callable, Dict
from debug import DebugLogger, LogLevel

class FractalCanvas:
    """
    フラクタル画像の表示と更新を管理するクラス

    このクラスは、フラクタル画像の表示、ズーム操作、
    パン操作、回転操作などの機能を提供します。
    MatplotlibとTkinterを使用して、高品質なフラクタル画像を表示します。

    Attributes:
        fig (Figure): MatplotlibのFigureインスタンス
        ax (Axes): MatplotlibのAxesインスタンス
        canvas (FigureCanvasTkAgg): Tkinterのキャンバス
        zoom_selector (ZoomSelector): ズーム選択機能を管理するクラス
        zoom_confirm_callback (Callable): ズーム確定時のコールバック関数
        zoom_cancel_callback (Callable): ズームキャンセル時のコールバック関数
        logger (DebugLogger): デバッグログを管理するロガー
        parent (tk.Widget): Tkinterの親ウィジェット
        facecolor (str): キャンバスの背景色
    """

    def __init__(self,
                master: tk.Tk,
                width: int, height: int,
                logger: DebugLogger,
                zoom_confirm_callback: Callable, zoom_cancel_callback: Callable,
                config: Dict[str, float]
    ):
        """
        FractalCanvas クラスの初期化

        初期化時に以下の処理を行います：
        1. FigureとAxesの初期化
        2. ズーム機能の設定
        3. 背景色の設定

        Args:
            master (tk.Tk): Tkinterの親ウィジェット
            width (int): キャンバスの幅 (ピクセル)
            height (int): キャンバスの高さ (ピクセル)
            logger (DebugLogger): デバッグログ用のロガー
            zoom_confirm_callback (Callable): ズーム確定時のコールバック関数
            zoom_cancel_callback (Callable): ズームキャンセル時のコールバック関数
            config (Dict[str, float]): ZoomSelectorの設定

        Raises:
            ValueError: 設定ファイルの形式が不正な場合
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

        self.logger.log(LogLevel.INIT, "FractalCanvas クラスのインスタンス作成成功")

    def _setup_figure(self, width: int, height: int) -> None:
        """
        MatplotlibのFigureとAxesの設定

        Args:
            width (int): キャンバスの幅 (ピクセル)
            height (int): キャンバスの高さ (ピクセル)

        Raises:
            ValueError: DPIの設定が不正な場合
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
        """
        ズーム確定・キャンセル時のコールバックを設定

        Args:
            zoom_confirm_callback (Callable): ズーム確定時のコールバック関数
            zoom_cancel_callback (Callable): ズームキャンセル時のコールバック関数
        """
        self.zoom_confirm_callback = zoom_confirm_callback
        self.zoom_cancel_callback = zoom_cancel_callback

    def _setup_zoom(self) -> None:
        """
        ズーム機能の設定と初期化

        このメソッドは以下の処理を行います：
        1. ZoomSelectorのインスタンスを作成
        2. ズームイベントのコールバックを設定
        3. デバッグログの設定
        """
        # ZoomSelector を遅延インポート
        from ui.zoom_function.zoom_selector import ZoomSelector

        self.logger.log(LogLevel.INIT, "ZoomSelector クラスのインスタンスを作成開始")
        self.zoom_selector = ZoomSelector(
            self.ax,
            on_zoom_confirm=self.zoom_confirmed,
            on_zoom_cancel=self.zoom_cancelled,
            logger=self.logger,
            config=self.config
        )

    def _set_black_background(self) -> None:
        """
        キャンバスの背景を黒に設定

        このメソッドは以下の処理を行います：
        1. Axesの背景色を黒に設定
        2. Figureの背景色を黒に設定
        3. 変更を反映
        """
        self.ax.set_facecolor(self.facecolor)
        self.fig.patch.set_facecolor(self.facecolor)
        self.canvas.draw()

    def zoom_confirmed(
        self,
        x: float, y: float,
        w: float, h: float,
        angle: float) -> None:
        """
        ズーム確定時の処理

        Args:
            x (float): ズーム選択範囲の左上X座標
            y (float): ズーム選択範囲の左上Y座標
            w (float): ズーム選択範囲の幅
            h (float): ズーム選択範囲の高さ
            angle (float): ズーム選択範囲の回転角度 (度)

        Raises:
            AttributeError: コールバック関数が未設定の場合
        """
        if self.zoom_confirm_callback:
            self.logger.log(
                LogLevel.CALL,
                "ズーム確定時のコールバック呼出し",
                {"x": x, "y": y, "w": w, "h": h, "angle": angle}
            )
            self.zoom_confirm_callback(x, y, w, h, angle)

    def zoom_cancelled(self) -> None:
        """
        ズームキャンセル時の処理

        Raises:
            AttributeError: コールバック関数が未設定の場合
        """
        if hasattr(self, 'zoom_cancel_callback') and self.zoom_cancel_callback:
            self.logger.log(LogLevel.CALL, "ズームキャンセル時のコールバック呼出し")
            self.zoom_cancel_callback()

    def update_canvas(
        self,
        fractal_image: np.ndarray,
        params: Dict[str, float]) -> None:
        """
        フラクタル画像の更新

        Args:
            fractal_image (np.ndarray): フラクタル画像データ (NumPy配列)
            params (Dict[str, float]): 描画パラメータ
                - center_x: 中心座標X
                - center_y: 中心座標Y
                - width: 描画範囲の幅
                - height: 描画範囲の高さ
                - rotation: 回転角度

        Raises:
            ValueError: パラメータの形式が不正な場合
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
        """
        ズームセレクタのリセット
        - ズーム選択状態を初期状態に戻す
        """
        if self.zoom_selector:
            self.logger.log(LogLevel.CALL, "ZoomSelector のリセットを呼出し")
            self.zoom_selector.reset()
