import tkinter as tk
from turtle import back
import numpy as np
import threading
import time
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
        """メインウィンドウクラスのコンストラクタ

        Args:
            root (tkinter.Tk): Tkinter ルートウィンドウ
            logger (DebugLogger): ログ出力用の DebugLogger インスタンス
        """
        self.logger = logger

        self._init_root_window(root)

		# ズーム操作用パラメータ
        self.zoom_params = {
            "center_x": 0.0, "center_y": 0.0, "width": 4.0, "height": 4.0, "rotation": 0.0}
        self.prev_zoom_params = None

        self.logger.log(LogLevel.INIT, "コールバック設定開始")
        self.fractal_canvas.set_zoom_callback(self.on_zoom_confirm, self.on_zoom_cancel)

        # 非同期処理用変数
        self.is_drawing = False
        self.draw_thread = None

        # アプリケーション起動時の最初の描画スレッド開始前に、ステータスバーアニメーションを開始
        # ここでは初期表示のみStatusBarManagerに任せます。
        # 実際の描画開始時のアニメーションはupdate_fractal内で開始されます。
        self.logger.log(LogLevel.DEBUG, "ステータスバーテキスト設定要求")
        self.status_bar_manager.set_text("準備中...") # StatusBarManagerのメソッドで初期テキストを設定

        # フラクタル描画スレッドを作成後、開始する
        self.logger.log(LogLevel.DEBUG, "非同期でフラクタル描画開始")
        # アプリケーション起動時はupdate_fractalを経由せず直接スレッドを開始するので、
        # ここでアニメーションを開始します。
        self.status_bar_manager.start_animation() # アプリケーション起動時のアニメーション開始
        self.draw_thread = threading.Thread(target=self._update_fractal_thread, daemon=True) # Daemonスレッドとして作成
        self.draw_thread.start() # フラクタル描画スレッドを開始

    def _init_root_window(self, root):
        """メインウィンドウの初期化

        Args:
            root (tkinter.Tk): Tkinter ルートウィンドウ
        """
        # Tkinter ルートウィンドウの初期化
        self.root = root
        self.root.title("フラクタル描画アプリケーション")
        self.root.geometry("1200x800")

        # メインフレーム
        self.main_frame = ttk.PanedWindow(root, orient=tk.HORIZONTAL) # 作成
        self.main_frame.pack(fill=tk.BOTH, expand=True) # 配置

        # キャンバスフレーム
        self.canvas_frame = ttk.Frame(self.main_frame) # 作成
        self.main_frame.add(self.canvas_frame, weight=4) # 配置
        # キャンバスフレームのリサイズイベントをバインド
        # <Configure> イベントが発生すると、_on_canvas_frame_configure メソッドが呼ばれる
        self.canvas_frame.bind("<Configure>", self._on_canvas_frame_configure)

        # FractalCanvas のインスタンスを作成し、保持
        # widthとheight は Tkinter ウィジェットの初期サイズに影響
        self.logger.log(LogLevel.INIT, "FractalCanvas 初期化開始")
        self.fractal_canvas = FractalCanvas(
            self.canvas_frame,
            width=1067, # これらの初期サイズはキャンバスウィジェット自体のサイズに影響するが、
            height=600, # Matplotlib Figure のサイズは _on_canvas_frame_configure で制御される
            logger=self.logger,
            zoom_confirm_callback=self.on_zoom_confirm, # 確定用コールバックをキャンバスに渡す
            zoom_cancel_callback=self.on_zoom_cancel) # キャンセル用コールバックをキャンバスに渡す

        # ParameterPanel のインスタンスを作成し、保持
        self.parameter_frame = ttk.Frame(self.main_frame) # 作成
        self.main_frame.add(self.parameter_frame, weight=1) # 配置
        self.logger.log(LogLevel.INIT, "ParameterPanel 初期化開始")
        self.parameter_panel = ParameterPanel(
            self.parameter_frame,
            self.update_fractal, # パラメータ変更時のコールバックとしてMainWindowのupdate_fractalを渡す
            reset_callback=self.reset_zoom, # リセット用コールバックをパラメータパネルに渡す
            logger=self.logger)

        # ステータスバー用のフレームを作成し、配置
        status_frame = ttk.Frame(self.root) # 作成
        status_frame.pack(fill=tk.X, side=tk.BOTTOM) # 配置

        # StatusBarManager のインスタンスを作成し、保持
        self.logger.log(LogLevel.INIT, "StatusBarManager 初期化開始")
        self.status_bar_manager = StatusBarManager(
            self.root,
            status_frame,
            self.logger)

    def update_fractal(self):
        """最新パラメータにズーム情報を上書きしてフラクタルを再描画（非同期処理を開始）"""
        # 既に描画中の場合は新しい描画を開始しない
        if self.is_drawing:
             self.logger.log(LogLevel.INFO, "描画中スキップ：前回の描画が完了してない")
             return

        self.is_drawing = True
        # 描画開始時にステータスバーアニメーションを開始
        self.status_bar_manager.start_animation() # <-- StatusBarManagerのメソッドを呼び出す

        self.logger.log(LogLevel.INFO, "新しい描画スレッドを開始")
        # スレッドのターゲットとしてインスタンスメソッドを指定
        self.draw_thread = threading.Thread(target=self._update_fractal_thread, daemon=True)
        self.draw_thread.start()

    def _update_fractal_thread(self):
        """フラクタル更新の実際の処理（別スレッドで実行される）"""
        try:
            self.logger.log(LogLevel.CALL, "描画パラメータ：取得開始（スレッド内）")
            panel_params = self.parameter_panel._get_parameters()

            # ズーム操作によるパラメータとパラメータパネルの設定を結合
            current_params = self.zoom_params.copy()
            current_params.update(panel_params) # パラメータパネルの設定で上書き（max_iterなど）

            self.logger.log(LogLevel.CALL, "フラクタル計算と着色処理を開始（スレッド内）")
            fractal_image = render_fractal(current_params, self.logger)

            self.logger.log(LogLevel.CALL, "メインスレッドでキャンバス更新要求（スレッド内）")
            # Tkinterのウィジェット操作は必ずメインスレッドで行う必要があるため、root.after を使用し、
            # update_canvas メソッドをメインスレッドで実行するようにスケジュールします。
            self.root.after(0, lambda: self.fractal_canvas.update_canvas(fractal_image, current_params))

            # アニメーションと時間計測を停止し、最終メッセージを表示
            # 時間計算とステータス表示はStatusBarManagerに任せます
            self.status_bar_manager.stop_animation("完了") # <-- StatusBarManagerのメソッドを呼び出す

        except Exception as e: # 例外処理
            self.logger.log(LogLevel.ERROR, f"フラクタル更新スレッドエラー: {str(e)}")
            # エラー発生時もアニメーションを停止し、エラーメッセージを表示
            # エラーメッセージの表示もStatusBarManagerに任せます
            self.status_bar_manager.stop_animation(f"エラー: {str(e)}") # <-- StatusBarManagerのメソッドを呼び出す
        finally: # 描画スレッドの終了処理
            # is_drawing フラグをリセット
            self.is_drawing = False

    def on_zoom_confirm(self, x: float, y: float, w: float, h: float, angle: float):
        """ズーム確定時のコールバック（ZoomSelectorから呼ばれる）
        - 縦横比を考慮して新しいズームパラメータを計算し、フラクタルを再描画
        - 矩形の中心座標を回転前の座標系に変換

        Args:
            x (float): 矩形左上の x 座標 (データ座標系)
            y (float): 矩形左上の y 座標 (データ座標系)
            w (float): 矩形の幅 (データ座標系)
            h (float): 矩形の高さ (データ座標系)
            angle (float): 矩形の回転角度 (度)
        """
        # ズーム矩形の中心座標を計算（回転前の座標系）
        center_x = x + w / 2
        center_y = y + h / 2

        self.logger.log(LogLevel.SUCCESS, "ズーム確定矩形情報", {
            "rect_x": x, "rect_y": y, "rect_w": w, "rect_h": h,
            "center_x": center_x, "center_y": center_y, "angle": angle
        })

        # ズーム確定前の現在のズームパラメータを保存（ズーム確定キャンセル用）
        self.prev_zoom_params = self.zoom_params.copy()

        # 新しいズームパラメータ（中心座標、幅、高さ、回転角度）を計算
        # 幅は選択された矩形の幅を使用
        new_width = w
        # 高さは、キャンバスの現在の縦横比（16:9になるように調整されているはず）に合わせて計算
        # canvas.pyのupdate_canvasでheight = width * (9 / 16) と計算しているので、
        # ここでもその比率を維持するように、選択されたwidthに対する高さを計算します。
        new_height = new_width * (9 / 16) # <-- 16:9の縦横比を維持

        # ズームファクターを計算（幅の変化率から）
        # これを使って最大反復回数を調整します。
        zoom_factor = self.zoom_params["width"] / new_width if new_width > 0 else 1
        current_max_iter = int(self.parameter_panel.max_iter_var.get()) # 現在の最大反復回数を取得

        # ズームインした場合（zoom_factor > 1）のみ反復回数を増やす（上限あり）
        new_max_iterations = current_max_iter # デフォルトは現在の値
        if zoom_factor > 1:
            # ズームファクターに基づいて反復回数を増加させるロジック
            # 例: 対数スケールで増加させる（調整可能）
            new_max_iterations = min(1000, max(current_max_iter, int(current_max_iter + 50 * np.log2(zoom_factor))))
            self.logger.log(LogLevel.DEBUG, f"ズームインによる反復回数増加: {current_max_iter} -> {new_max_iterations}")
        else:
             self.logger.log(LogLevel.DEBUG, f"ズームアウトまたは移動のみ: 反復回数変更なし ({current_max_iter})")


        self.logger.log(LogLevel.SUCCESS, "新しいズームパラメータ計算結果", {
            "zoom_factor": zoom_factor, "new_width": new_width, "new_height": new_height,
            "current_max_iter": current_max_iter, "new_max_iterations": new_max_iterations,
            "new_center_x": center_x, "new_center_y": center_y, "new_rotation": angle})

        # 新しいズームパラメータを設定
        self.zoom_params = {
            "center_x": center_x,
            "center_y": center_y,
            "width": new_width,
            "height": new_height, # このheightはrender_fractalでの計算範囲の高さ設定に使用されます
            "rotation": angle}

        # 計算された新しい最大反復回数をパラメータパネルに反映
        self.parameter_panel.max_iter_var.set(str(new_max_iterations))

        # 新しいパラメータでフラクタルを再描画
        self.update_fractal()

    def on_zoom_cancel(self):
        """ズームキャンセル時のコールバック（ZoomSelectorから呼ばれる）
        - ズーム確定前の状態に戻して再描画
        """
        self.logger.log(LogLevel.INFO, "ズームキャンセル処理開始")
        if self.prev_zoom_params is not None:
            self.logger.log(LogLevel.DEBUG, "直前のズームパラメータに戻します")
            # 保存しておいた確定前のズームパラメータに戻す
            self.zoom_params = self.prev_zoom_params.copy()
            # 戻したパラメータでフラクタルを再描画
            self.update_fractal()
            # 確定前パラメータをクリア
            self.prev_zoom_params = None
        else:
            self.logger.log(LogLevel.INFO, "ズーム確定前のパラメータがないため、キャンセル処理はスキップしました。")

    def reset_zoom(self):
        """操作パネルの「描画リセット」ボタン押下時の処理
        （ズームパラメータを初期状態に戻して再描画）
        """
        self.logger.log(LogLevel.DEBUG, "描画リセットボタンのメソッド開始")
        # ズームパラメータを初期値にリセット
        self.zoom_params = {
            "center_x": 0.0, "center_y": 0.0, "width": 4.0, "height": 4.0, "rotation": 0.0}
        # 確定前パラメータもクリア
        self.prev_zoom_params = None
        # 最大反復回数も初期値に戻す
        self.parameter_panel.max_iter_var.set("100")
        self.logger.log(LogLevel.CALL, "ZoomSelector の状態リセット開始")
        # ZoomSelectorの状態もリセット（矩形などを消去）
        self.fractal_canvas.reset_zoom_selector()
        # 初期パラメータでフラクタルを再描画
        self.update_fractal()


    def _on_canvas_frame_configure(self, event):
        """キャンバスフレームのリサイズ時にMatplotlib Figureのサイズを更新し、16:9の縦横比を維持する"""
        # キャンバスフレームの新しいピクセルサイズを取得
        frame_width_pixels = event.width
        frame_height_pixels = event.height

        # サイズが無効（0以下）の場合は処理をスキップ
        if frame_width_pixels <= 0 or frame_height_pixels <= 0:
            self.logger.log(LogLevel.DEBUG, "フレームサイズが無効なため、Figureサイズ更新をスキップ")
            return

        # 目標の縦横比 (幅 / 高さ)
        target_aspect = 16 / 9

        # 現在のフレームの縦横比を計算（ゼロ除算を防ぐ）
        frame_aspect = frame_width_pixels / frame_height_pixels if frame_height_pixels > 0 else float('inf')

        # どちらを基準にFigureサイズを決定するか判断
        if frame_aspect > target_aspect:
            # フレームが目標より横長の場合、フレームの高さを基準にFigureサイズを計算
            new_height_pixels = frame_height_pixels
            new_width_pixels = int(new_height_pixels * target_aspect)
            self.logger.log(LogLevel.DEBUG, f"横長フレーム: 高さを基準にFigureサイズ計算 ({new_width_pixels}x{new_height_pixels})")
        else:
            # フレームが目標より縦長、または同じ縦横比の場合、フレームの幅を基準にFigureサイズを計算
            new_width_pixels = frame_width_pixels
             # 目標縦横比が0でないことを確認して計算（ゼロ除算を防ぐ）
            new_height_pixels = int(new_width_pixels / target_aspect) if target_aspect > 0 else frame_height_pixels
            self.logger.log(LogLevel.DEBUG, f"縦長/同等フレーム: 幅を基準にFigureサイズ計算 ({new_width_pixels}x{new_height_pixels})")

        # MatplotlibのFigureサイズをインチ単位で計算 (dpi=100を仮定、FractalCanvasで設定されている)
        # Figureのget_dpi()メソッドで実際のdpiを取得可能ですが、初期化時のdpi=100を使用
        dpi = self.fractal_canvas.fig.get_dpi() if self.fractal_canvas and hasattr(self.fractal_canvas, 'fig') and self.fractal_canvas.fig else 100

        new_width_inches = new_width_pixels / dpi
        new_height_inches = new_height_pixels / dpi

        # Figureのサイズを更新
        try:
            if self.fractal_canvas and hasattr(self.fractal_canvas, 'fig') and self.fractal_canvas.fig:
                # MatplotlibのFigureサイズを更新。forward=TrueでFigureCanvasTkAggに通知し、再描画を促す。
                # これによりTkinterキャンバスウィジェットのサイズもFigureサイズに合うように調整されます。
                self.fractal_canvas.fig.set_size_inches(new_width_inches, new_height_inches, forward=True)
                self.logger.log(LogLevel.SUCCESS, f"Matplotlib Figure サイズ更新完了: {new_width_inches:.2f}x{new_height_inches:.2f}インチ ({new_width_pixels}x{new_height_pixels}ピクセル)")
                # Figureサイズ変更によりAxesの表示も自動的に更新されるはずですが、必要に応じて
                # self.fractal_canvas.canvas.draw_idle() を追加しても良いかもしれません。（ただしパフォーマンス注意）
            else:
                self.logger.log(LogLevel.ERROR, "FractalCanvas または Figure が利用不可（Figure サイズ更新スキップ）")
        except Exception as e:
            self.logger.log(LogLevel.ERROR, f"Matplotlib Figure サイズ更新中にエラー: {e}")
