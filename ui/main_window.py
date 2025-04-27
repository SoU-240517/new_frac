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
    """MainWindow クラス
    - 役割:
        - UIコンポーネントの初期化と管理を行う
        - フラクタル描画を行う
    Attributes:
        canvas_frame: キャンバスを配置するフレーム
        root: Tkinterのルートウィンドウ
        logger: デバッグログを管理するLogger
        fractal_canvas: フラクタルを描画するキャンバス
        parameter_panel: パラメータを管理するパネル
        parameter_frame: パラメータパネルを配置するフレーム
        status_bar_manager: ステータスバーを管理するクラス
        zoom_params: ズーム操作のパラメータ
        prev_zoom_params: ズーム前のパラメータ（キャンセル用）
        is_drawing: 描画中かどうかのフラグ
        draw_thread: フラクタル描画スレッド
    """

    def __init__(self, root: tk.Tk, logger: DebugLogger):
        """MainWindow クラスのコンストラクタ
        Args:
            root: Tkinterのルートウィンドウ
            logger: デバッグログを管理するLogger
        """
        self.logger = logger
        self.root = root

        self._setup_root_window()
        self._setup_components()

        self.zoom_params = {
            "center_x": 0.0, # 中心X座標を調整
            "center_y": 0.0,  # 中心Y座標
            "width": 5.5,     # 幅を広くして多くのフラクタルを表示（16:9考慮）
            "height": 5.5 * (9/16), # 幅に合わせて高さを設定（不要だがconsistencyのために残す）
            "rotation": 0.0   # 回転角
        }

        self.prev_zoom_params = None

        self.is_drawing = False
        self.draw_thread = None

        self._start_initial_drawing()

    def _setup_root_window(self) -> None:
        """ルートウィンドウの基本設定を行う"""
        self.root.title("フラクタル描画アプリケーション")
        self.root.geometry("1200x800")

    def _setup_components(self) -> None:
        """UIコンポーネントの初期化を行う"""
        self._setup_status_bar()
        self._setup_parameter_frame()
        self._setup_canvas_frame()

    def _setup_status_bar(self) -> None:
        """ステータスバーの初期化を行う"""
        status_frame = ttk.Frame(self.root)
        status_frame.pack(fill=tk.X, side=tk.BOTTOM, pady=(0, 5))
        self.logger.log(LogLevel.INIT, "StatusBarManager クラスのインスタンスを作成")
        self.status_bar_manager = StatusBarManager(
            self.root,
            status_frame,
            self.logger
        )

    def _setup_parameter_frame(self) -> None:
        """パラメータパネルのフレームを初期化する"""
        self.parameter_frame = ttk.Frame(self.root, width=300)
        self.parameter_frame.pack(
            side=tk.RIGHT,
            fill=tk.Y,
            padx=(0, 5),
            pady=5,
            expand=False
        )
        self.parameter_frame.pack_propagate(False)

        self.logger.log(LogLevel.INIT, "ParameterPanel クラスのインスタンスを作成")
        self.parameter_panel = ParameterPanel(
            self.parameter_frame,
            self.update_fractal,
            reset_callback=self.reset_zoom,
            logger=self.logger
        )

    def _setup_canvas_frame(self) -> None:
        """キャンバスフレームの初期化を行う"""
        self.canvas_frame = ttk.Frame(self.root)
        self.canvas_frame.pack(
            side=tk.LEFT,
            fill=tk.BOTH,
            expand=True,
            padx=(5, 0),
            pady=5
        )

        self.canvas_frame.bind("<Configure>", self._on_canvas_frame_configure)

        self.logger.log(LogLevel.INIT, "FractalCanvas クラスのインスタンスを作成")
        self.fractal_canvas = FractalCanvas(
            self.canvas_frame,
            width=1067,
            height=600,
            logger=self.logger,
            zoom_confirm_callback=self.on_zoom_confirm,
            zoom_cancel_callback=self.on_zoom_cancel
        )

    def _start_initial_drawing(self) -> None:
        """アプリケーション起動時の初期描画を開始する"""
        self.logger.log(LogLevel.CALL, "ステータスバーテキスト設定要求")
        self.status_bar_manager.set_text("準備中...")

        self.logger.log(LogLevel.CALL, "非同期でフラクタル描画開始")
        self.status_bar_manager.start_animation()
        self.draw_thread = threading.Thread(
            target=self._update_fractal_thread,
            daemon=True
        )
        self.draw_thread.start()

    def update_fractal(self) -> None:
        """フラクタルを再描画する（非同期処理）"""
        if self.is_drawing:
            self.logger.log(LogLevel.WARNING, "描画中でスキップ：前回の描画が未完了")
            return

        self.is_drawing = True
        self.status_bar_manager.start_animation()

        self.logger.log(LogLevel.CALL, "新しい描画スレッドを開始")
        self.draw_thread = threading.Thread(
            target=self._update_fractal_thread,
            daemon=True
        )
        self.draw_thread.start()

    def _update_fractal_thread(self) -> None:
        """フラクタル更新の実際の処理（別スレッドで実行）"""
        try:
            self.logger.log(LogLevel.CALL, "描画パラメータ：取得開始（スレッド内）")
            panel_params = self.parameter_panel._get_parameters()
            current_params = self._merge_zoom_and_panel_params(panel_params)

            self.logger.log(LogLevel.CALL, "フラクタル計算と着色処理を開始（スレッド内）")
            fractal_image = render_fractal(current_params, self.logger)

            self.logger.log(LogLevel.CALL, "メインスレッドでキャンバス更新要求（スレッド内）")
            self.root.after(0, lambda: self.fractal_canvas.update_canvas(
                fractal_image, current_params
            ))

            self.status_bar_manager.stop_animation("完了")
        except Exception as e:
#            # スタックトレースを取得
#            import traceback
#            stack_trace = traceback.format_exc()

#            # ログ出力時にスタックトレースをコンテキストとして渡す
#            self.logger.log(LogLevel.ERROR, f"フラクタル更新スレッドエラー: {str(e)}",
#                            context={"stack_trace": stack_trace})
            self.logger.log(LogLevel.ERROR, f"フラクタル更新スレッドエラー: {str(e)}")
            self.status_bar_manager.stop_animation(f"エラー: {str(e)}")
        finally:
            self.is_drawing = False

#    def _merge_zoom_and_panel_params(self, panel_params: dict) -> dict:
#        """ズームパラメータとパネルパラメータを結合する
#        Args:
#            panel_params: パネルから取得したパラメータ
#        Returns:
#            dict: 結合されたパラメータ
#        """
#        current_params = self.zoom_params.copy()
#        current_params.update(panel_params)
#        return current_params

    def _merge_zoom_and_panel_params(self, panel_params: dict) -> dict:
        """ズームパラメータとパネルパラメータを結合する"""
        current_params = self.zoom_params.copy()
        current_params.update(panel_params)
        current_params["render_mode"] = self.parameter_panel.render_mode  # 描画モードを追加
        return current_params

    def on_zoom_confirm(self, x: float, y: float, w: float, h: float, angle: float) -> None:
        """ズーム確定時のコールバック
        Args:
            x: 矩形左上のx座標
            y: 矩形左上のy座標
            w: 矩形の幅
            h: 矩形の高さ
            angle: 矩形の回転角度
        """
        center_x = x + w / 2
        center_y = y + h / 2

        self.prev_zoom_params = self.zoom_params.copy()

        new_width = w
        new_height = new_width * (9 / 16)

        zoom_factor = self.zoom_params["width"] / new_width if new_width > 0 else 1
        current_max_iter = int(self.parameter_panel.max_iter_var.get())

        new_max_iterations = self._calculate_max_iterations(current_max_iter, zoom_factor)

        self.logger.log(
            LogLevel.SUCCESS,
            context={
                "zoom_factor": zoom_factor,
                "new_width": new_width,
                "new_height": new_height,
                "current_max_iter": current_max_iter,
                "new_max_iterations": new_max_iterations,
                "new_center_x": center_x,
                "new_center_y": center_y,
                "new_rotation": angle
            },
            message="新しいズームパラメータ"
        )

        self.zoom_params = {
            "center_x": center_x,
            "center_y": center_y,
            "width": new_width,
            "height": new_height,
            "rotation": angle
        }

        self.parameter_panel.max_iter_var.set(str(new_max_iterations))

        self.update_fractal()

    def _calculate_max_iterations(self, current_max_iter: int, zoom_factor: float) -> int:
        """ズームファクターに基づいて最大反復回数を計算する
        Args:
            current_max_iter: 現在の最大反復回数
            zoom_factor: ズームファクター
        Returns:
            int: 計算された新しい最大反復回数
        """
        if zoom_factor > 1:
            return min(1000, max(current_max_iter, int(current_max_iter + 50 * np.log2(zoom_factor))))
        return current_max_iter

    def on_zoom_cancel(self):
        """ズームキャンセル時のコールバック"""
        if self.prev_zoom_params is not None:
            self.logger.log(LogLevel.CALL, "直前のズームパラメータに戻す")
            self.zoom_params = self.prev_zoom_params.copy()
            self.update_fractal()
            self.prev_zoom_params = None
        else:
            self.logger.log(LogLevel.WARNING, "キャンセル処理をスキップ：直前のパラメータなし")

    def reset_zoom(self):
        """操作パネルの「描画リセット」ボタン押下時の処理"""
        self.zoom_params = {
            "center_x": 0.0, # 中心X座標を調整
            "center_y": 0.0,  # 中心Y座標
            "width": 5.5,     # 幅を広くして多くのフラクタルを表示（16:9考慮）
            "height": 5.5 * (9/16), # 幅に合わせて高さを設定（不要だがconsistencyのために残す）
            "rotation": 0.0   # 回転角
        }

        self.prev_zoom_params = None
        self.parameter_panel.max_iter_var.set("500")
        self.logger.log(LogLevel.CALL, "ZoomSelector の状態リセット開始")
        self.fractal_canvas.reset_zoom_selector()
        self.update_fractal()

    def _on_canvas_frame_configure(self, event):
        """キャンバスフレームのリサイズ時に Matplotlib Figure のサイズを更新し、16:9 の縦横比を維持する"""
        frame_width_pixels = event.width
        frame_height_pixels = event.height

        if frame_width_pixels <= 0 or frame_height_pixels <= 0:
            self.logger.log(LogLevel.INFO, "Figure サイズ更新をスキップ：フレームサイズが無効なため")
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
                self.logger.log(LogLevel.WARNING, "FractalCanvas または Figure が利用不可（Figure サイズ更新スキップ）")
        except Exception as e:
            self.logger.log(LogLevel.ERROR, f"Matplotlib Figure サイズ更新中にエラー: {e}")
