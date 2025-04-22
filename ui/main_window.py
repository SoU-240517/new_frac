import tkinter as tk
import numpy as np
import threading
from tkinter import ttk
from ui.canvas import FractalCanvas
from ui.parameter_panel import ParameterPanel
from fractal.render import render_fractal
from .status_bar import StatusBarManager
from .zoom_function.debug_logger import DebugLogger
from .zoom_function.enums import LogLevel

class MainWindow:
    """アプリケーションのメインウィンドウクラス
    - 役割:
        - アプリケーションのメインウィンドウを管理する
        - UIの初期化、イベント処理、フラクタル描画の制御を行う
    """
    def __init__(self, root, logger: DebugLogger):
        """MainWindow クラスのコンストラクタ

        Args:
            root (tkinter.Tk): Tkinter ルートウィンドウ
            logger (DebugLogger): ログ出力用の DebugLogger インスタンス
        """
        self.logger = logger
        self._setup_ui(root)
        self._setup_event_handlers()
        self._setup_initial_state()
        self._start_initial_render()

    def _setup_ui(self, root):
        """UIの初期設定を行う"""
        self.root = root
        self.root.title("フラクタル描画アプリケーション")
        self.root.geometry("1200x800")

        # --- パラメータパネルフレームの作成と配置 (pack で右側固定) ---
        self.parameter_frame = ttk.Frame(root, width=300) # 作成（width=300）
        # 右側に幅 300px 固定で配置、Y方向にのみ引き伸ばす
        # expand=False でウィンドウリサイズ時に幅が変わらないようにする
        self.parameter_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=(0, 5), pady=5, expand=False) # 配置
        # widthで指定した幅を維持するため、フレーム内のウィジェットサイズに合わせてフレームサイズが変わるのを防ぐ
        self.parameter_frame.pack_propagate(False) # フレームのサイズを固定

        # --- キャンバスフレームの作成と配置 (pack で残り領域) ---
        self.canvas_frame = ttk.Frame(root) # 作成
        # 左側の残りスペース全体に配置、両方向に引き伸ばす
        # expand=True でウィンドウリサイズ時に残りスペースを埋めるように広がる
        self.canvas_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(5, 0), pady=5) # 配置

        # キャンバスフレームのリサイズイベントをバインド
        # <Configure> イベントが発生すると、_on_canvas_frame_configure メソッドが呼ばれる
        self.canvas_frame.bind("<Configure>", self._on_canvas_frame_configure)

        # FractalCanvas のインスタンスを作成、保持
        # 親を canvas_frame に設定 (PanedWindow を使わないため直接 root の子フレームになる)
        self.logger.log(LogLevel.INIT, "FractalCanvas 初期化開始")
        self.fractal_canvas = FractalCanvas(
            self.canvas_frame,
            width=1067,
            height=600,
            logger=self.logger,
            zoom_confirm_callback=self.on_zoom_confirm, # 確定用コールバックをキャンバスに渡す
            zoom_cancel_callback=self.on_zoom_cancel) # キャンセル用コールバックをキャンバスに渡す

        # ParameterPanel のインスタンスを作成、保持
        # 親を parameter_frame に設定
        self.logger.log(LogLevel.INIT, "ParameterPanel 初期化開始")
        self.parameter_panel = ParameterPanel(
            self.parameter_frame, # 親ウィジェットを更新
            self.update_fractal, # パラメータ変更時のコールバックとしてMainWindowのupdate_fractalを渡す
            reset_callback=self.reset_zoom, # リセット用コールバックをパラメータパネルに渡す
            logger=self.logger)

        # ステータスバーのフレームを作成、配置
        status_frame = ttk.Frame(self.root) # 作成
        status_frame.pack(fill=tk.X, side=tk.BOTTOM, pady=(0, 5))
        # StatusBarManager のインスタンスを作成、保持
        self.logger.log(LogLevel.INIT, "StatusBarManager 初期化開始")
        self.status_bar_manager = StatusBarManager(
            self.root,
            status_frame,
            self.logger)

    def update_fractal(self):
        """フラクタルの更新を要求する"""
        if self.is_drawing:
            self.logger.log(LogLevel.INFO, "描画中スキップ：前回の描画が未完了")
            return

        self.is_drawing = True
        self.status_bar_manager.start_animation()
        self.logger.log(LogLevel.INFO, "新しい描画スレッドを開始")
        self._start_render_thread()

    def _update_fractal_thread(self):
        """フラクタルの更新処理を別のスレッドで実行"""
        try:
            self.logger.log(LogLevel.CALL, "描画パラメータ：取得開始（スレッド内）")
            panel_params = self.parameter_panel._get_parameters()
            current_params = self.zoom_params.copy()
            current_params.update(panel_params)

            self.logger.log(LogLevel.CALL, "フラクタル計算と着色処理を開始（スレッド内）")
            fractal_image = render_fractal(current_params, self.logger)

            self.logger.log(LogLevel.CALL, "メインスレッドでキャンバス更新要求（スレッド内）")
            self.root.after(0, lambda: self._update_canvas(fractal_image, current_params))

        except Exception as e:
            self.logger.log(LogLevel.ERROR, f"フラクタル更新スレッドエラー: {str(e)}")
            self.status_bar_manager.stop_animation(f"エラー: {str(e)}")
            self.is_drawing = False

    def _update_canvas(self, fractal_image, params):
        """キャンバスの更新を行う"""
        try:
            self.fractal_canvas.update_canvas(fractal_image, params)
            self.status_bar_manager.stop_animation("完了")
        except Exception as e:
            self.logger.log(LogLevel.ERROR, f"キャンバス更新エラー: {str(e)}")
            self.status_bar_manager.stop_animation(f"エラー: {str(e)}")
        finally:
            self.is_drawing = False

    def on_zoom_confirm(self, x: float, y: float, w: float, h: float, angle: float):
        """ズーム確定時の処理"""
        center_x = x + w / 2
        center_y = y + h / 2

        self.logger.log(LogLevel.SUCCESS, "ズーム確定矩形情報", {
            "rect_x": x, "rect_y": y, "rect_w": w, "rect_h": h,
            "center_x": center_x, "center_y": center_y, "angle": angle})

        self.prev_zoom_params = self.zoom_params.copy()

        new_width = w
        new_height = new_width * (9 / 16)

        zoom_factor = self.zoom_params["width"] / new_width if new_width > 0 else 1
        current_max_iter = int(self.parameter_panel.max_iter_var.get())

        new_max_iterations = current_max_iter
        if zoom_factor > 1:
            new_max_iterations = min(1000, max(
                current_max_iter,
                int(current_max_iter + 50 * np.log2(zoom_factor))))

        self.logger.log(LogLevel.SUCCESS, "新しいズームパラメータ計算結果", {
            "zoom_factor": zoom_factor,
            "new_width": new_width,
            "new_height": new_height,
            "current_max_iter": current_max_iter,
            "new_max_iterations": new_max_iterations,
            "new_center_x": center_x,
            "new_center_y": center_y,
            "new_rotation": angle})

        self.zoom_params.update({
            "center_x": center_x,
            "center_y": center_y,
            "width": new_width,
            "height": new_height,
            "rotation": angle
        })

        self.parameter_panel.max_iter_var.set(str(new_max_iterations))
        self.update_fractal()

    def on_zoom_cancel(self):
        """ズームキャンセル時の処理"""
        if self.prev_zoom_params is not None:
            self.logger.log(LogLevel.DEBUG, "直前のズームパラメータに戻す")
            self.zoom_params = self.prev_zoom_params.copy()
            self.update_fractal()
            self.prev_zoom_params = None
        else:
            self.logger.log(LogLevel.INFO, "キャンセル処理スキップ：直前のパラメータなし")

    def reset_zoom(self):
        """操作パネルの「描画リセット」ボタン押下時の処理"""
        self.zoom_params = {
            "center_x": 0.0,
            "center_y": 0.0,
            "width": 4.0,
            "height": 4.0,
            "rotation": 0.0
        }
        self.prev_zoom_params = None
        self.parameter_panel.max_iter_var.set("100")
        self.logger.log(LogLevel.CALL, "ZoomSelector の状態リセット開始")
        self.fractal_canvas.reset_zoom_selector()
        self.update_fractal()

    def _on_canvas_frame_configure(self, event):
        """キャンバスフレームのリサイズ時に Matplotlib Figure のサイズを更新し、16:9 の縦横比を維持する"""
        frame_width_pixels = event.width
        frame_height_pixels = event.height

        if frame_width_pixels <= 0 or frame_height_pixels <= 0:
            self.logger.log(LogLevel.DEBUG, "Figure サイズ更新スキップ：フレームサイズが無効なため")
            return

        target_aspect = 16 / 9

        frame_aspect = frame_width_pixels / frame_height_pixels if frame_height_pixels > 0 else float('inf')

        if frame_aspect > target_aspect:
            new_height_pixels = frame_height_pixels
            new_width_pixels = int(new_height_pixels * target_aspect)
            self.logger.log(LogLevel.DEBUG, f"横長フレーム：高さを基準に Figure サイズ計算 ({new_width_pixels}x{new_height_pixels})")
        else:
            new_width_pixels = frame_width_pixels
            new_height_pixels = int(new_width_pixels / target_aspect) if target_aspect > 0 else frame_height_pixels
            self.logger.log(LogLevel.DEBUG, f"縦長/同等フレーム：幅を基準に Figure サイズ計算 ({new_width_pixels}x{new_height_pixels})")

        dpi = self.fractal_canvas.fig.get_dpi() if self.fractal_canvas and hasattr(self.fractal_canvas, 'fig') and self.fractal_canvas.fig else 100

        new_width_inches = new_width_pixels / dpi
        new_height_inches = new_height_pixels / dpi

        try:
            if self.fractal_canvas and hasattr(self.fractal_canvas, 'fig') and self.fractal_canvas.fig:
                self.fractal_canvas.fig.set_size_inches(new_width_inches, new_height_inches, forward=True)
                self.logger.log(LogLevel.SUCCESS, f"Matplotlib Figure サイズ更新完了: {new_width_inches:.2f}x{new_height_inches:.2f}インチ ({new_width_pixels}x{new_height_pixels}ピクセル)")
            else:
                self.logger.log(LogLevel.ERROR, "FractalCanvas または Figure が利用不可（Figure サイズ更新スキップ）")
        except Exception as e:
            self.logger.log(LogLevel.ERROR, f"Matplotlib Figure サイズ更新中にエラー: {e}")
