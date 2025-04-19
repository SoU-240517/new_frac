import tkinter as tk
import numpy as np
import threading
import time
from tkinter import ttk
from ui.canvas import FractalCanvas
from ui.parameter_panel import ParameterPanel
from fractal.render import render_fractal
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

        self.init_root_window(root)

		# ズーム操作用パラメータ
        self.zoom_params = {
            "center_x": 0.0, "center_y": 0.0, "width": 4.0, "height": 4.0, "rotation": 0.0}
        self.prev_zoom_params = None

        self.logger.log(LogLevel.INIT, "コールバック設定")

        self.fractal_canvas.set_zoom_callback(self.on_zoom_confirm, self.on_zoom_cancel)

        # 非同期処理用変数
        self.is_drawing = False
        self.draw_thread = None

        self.logger.log(LogLevel.INFO, "非同期でフラクタル描画を開始")

        # 編集ここから ----------
        # アプリケーション起動時の最初の描画スレッド開始前に、ステータスバーアニメーションを開始
        self._start_status_animation()
        self.logger.log(LogLevel.DEBUG, "__init__: _start_status_animation() を呼び出しました") # 追加ログ

        # 最初のフラクタル描画スレッドを作成し、開始
        self.draw_thread = threading.Thread(target=self._update_fractal_thread, daemon=True)
        self.logger.log(LogLevel.DEBUG, "__init__: 描画スレッドを作成しました") # 追加ログ
        self.draw_thread.start()
        self.logger.log(LogLevel.DEBUG, "__init__: 描画スレッドを開始しました") # 追加ログ
        # 編集ここまで ----------

        self.logger.log(LogLevel.INFO, "非同期でフラクタル描画を開始")
        # スレッドのターゲットとしてインスタンスメソッドを指定
        self.draw_thread = threading.Thread(target=self._update_fractal_thread, daemon=True)
        self.draw_thread.start()

    def init_root_window(self, root):
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
        self.main_frame.add(self.canvas_frame, weight=3)

        # キャンバスフレームのリサイズイベントをバインド
        # <Configure> イベントが発生すると、_on_canvas_frame_configure メソッドが呼ばれる
        self.canvas_frame.bind("<Configure>", self._on_canvas_frame_configure)

        self.logger.log(LogLevel.INIT, "FractalCanvas 初期化開始")
        # FractalCanvasの初期化。widthとheightはTkinterウィジェットの初期サイズに影響
        self.fractal_canvas = FractalCanvas(
            self.canvas_frame,
            width=800, # これらの初期サイズはキャンバスウィジェット自体のサイズに影響しますが、
            height=600, # Matplotlib Figureのサイズは_on_canvas_frame_configureで制御されます。
            logger=self.logger,
            zoom_confirm_callback=self.on_zoom_confirm, # 確定用コールバックをキャンバスに渡す
            zoom_cancel_callback=self.on_zoom_cancel) # キャンセル用コールバックをキャンバスに渡す


        # パラメータフレーム
        self.parameter_frame = ttk.Frame(self.main_frame) # 作成
        self.main_frame.add(self.parameter_frame, weight=1) # 配置
        self.logger.log(LogLevel.INIT, "ParameterPanel 初期化開始")
        self.parameter_panel = ParameterPanel(
            self.parameter_frame,
            self.update_fractal, # パラメータ変更時のコールバックとしてMainWindowのupdate_fractalを渡す
            reset_callback=self.reset_zoom, # リセット用コールバックをパラメータパネルに渡す
            logger=self.logger)


        # ステータスバー
        self.status_frame = ttk.Frame(self.root) # 作成
        self.status_frame.pack(fill=tk.X, side=tk.BOTTOM) # 配置

        # ステータスバーのラベル
        self.status_label = ttk.Label(self.status_frame, text="準備中...") # 作成
        self.status_label.pack(side=tk.LEFT, padx=5, pady=2) # 配置

        # ステータスバーの文字アニメーション用変数
        self.animation_thread = None
        self.animation_running = False
        self.animation_dots = 0
        self.animation_max_dots = 5

    def update_fractal(self):
        """最新パラメータにズーム情報を上書きしてフラクタルを再描画（非同期処理を開始）"""
        # 既に描画中の場合は新しい描画を開始しない
        if self.is_drawing:
             self.logger.log(LogLevel.INFO, "描画中スキップ：前回の描画が完了していません")
             return

        self.is_drawing = True
        self._start_status_animation()

        # スレッドが終了しているか確認し、新しいスレッドを作成して開始
        # if self.draw_thread is None or not self.draw_thread.is_alive(): # __init__で開始しているので通常はalive
        self.logger.log(LogLevel.INFO, "新しい描画スレッドを開始")
        # スレッドのターゲットとしてインスタンスメソッドを指定
        self.draw_thread = threading.Thread(target=self._update_fractal_thread, daemon=True)
        self.draw_thread.start()


    def _update_fractal_thread(self):
        """フラクタル更新の実際の処理（別スレッドで実行される）"""
        try:
            self.logger.log(LogLevel.CALL, "描画パラメータ：取得開始 (スレッド内)")
            # パラメータパネルから最新の設定を取得
            panel_params = self.parameter_panel.get_parameters()
            # ズーム操作によるパラメータとパラメータパネルの設定を結合
            current_params = self.zoom_params.copy()
            current_params.update(panel_params) # パラメータパネルの設定で上書き（max_iterなど）

            self.logger.log(LogLevel.CALL, "フラクタル描画開始 (スレッド内)")
            # フラクタル計算と着色処理を実行
            fractal_image = render_fractal(current_params, self.logger)

            self.logger.log(LogLevel.CALL, "メインスレッドでキャンバス更新要求 (スレッド内)")
            # Tkinterのウィジェット操作は必ずメインスレッドで行う必要があるため、root.afterを使用
            # update_canvas メソッドをメインスレッドで実行するようにスケジュール
            self.root.after(0, lambda: self.fractal_canvas.update_canvas(fractal_image, current_params))

            self.logger.log(LogLevel.CALL, "メインスレッドでステータスアニメーション停止要求 (スレッド内)")
            # ステータスアニメーション停止もメインスレッドで実行するようにスケジュール
            self.root.after(0, lambda: self._stop_status_animation())

        except Exception as e: # 例外処理
            self.logger.log(LogLevel.ERROR, f"フラクタル更新スレッドエラー: {str(e)}")
            # エラー発生時もステータスアニメーションを停止
            self.root.after(0, lambda: self._stop_status_animation())
        finally: # 描画スレッドの終了処理
            # is_drawing フラグをリセット
            self.is_drawing = False
            self.logger.log(LogLevel.INFO, "描画スレッド終了")


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
        self.logger.log(LogLevel.SUCCESS, "ズーム確定処理開始")

        # ズーム矩形の中心座標を計算（回転前の座標系）
        center_x = x + w / 2
        center_y = y + h / 2

        self.logger.log(LogLevel.DEBUG, "ズーム確定矩形情報", {
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
            "new_center_x": center_x, "new_center_y": center_y, "new_rotation": angle
            })

        # 新しいズームパラメータを設定
        self.zoom_params = {
            "center_x": center_x,
            "center_y": center_y,
            "width": new_width,
            "height": new_height, # このheightはrender_fractalでの計算範囲の高さ設定に使用されます
            "rotation": angle
        }

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

    def _start_status_animation(self):
        """ステータスバーの描画中アニメーションを開始"""
        self.logger.log(LogLevel.DEBUG, "_start_status_animation 実行") # 追加ログ
        # 既にアニメーションが実行中の場合は何もしない
        if self.animation_running:
             self.logger.log(LogLevel.DEBUG, "_start_status_animation: アニメーションは既に実行中です")
             return

        self.animation_running = True # アニメーション実行中フラグをTrueに
        self.animation_dots = 0
        self.logger.log(LogLevel.DEBUG, "_start_status_animation: アニメーション実行フラグをTrueに設定しました") # 追加ログ

        self.logger.log(LogLevel.DEBUG, "_start_status_animation: アニメーションスレッドを作成します") # 追加ログ
        # アニメーション用のスレッドを作成
        self.animation_thread = threading.Thread(
            target=self._status_animation_thread, # このメソッドがスレッドで実行されるターゲット
            daemon=True) # メインスレッド終了時に一緒に終了

        self.logger.log(LogLevel.DEBUG, "_start_status_animation: アニメーションスレッドのstart()を呼び出します") # 追加ログ
        # スレッドを開始
        try:
            self.animation_thread.start()
            self.logger.log(LogLevel.DEBUG, "_start_status_animation: アニメーションスレッドのstart()呼び出しに成功しました") # 追加ログ
        except Exception as e:
            self.logger.log(LogLevel.ERROR, f"_start_status_animation: アニメーションスレッドの開始に失敗しました: {e}") # 追加ログ
            self.animation_running = False # スレッド開始に失敗したらフラグを戻す


        self.logger.log(LogLevel.DEBUG, "_start_status_animation 完了") # 追加ログ

    def _status_animation_thread(self):
        """ステータスバーのアニメーションを更新するスレッドの処理"""
        self.logger.log(LogLevel.DEBUG, "_status_animation_thread 開始: アニメーションスレッドが実行されました") # 追加ログ
        while self.animation_running:
            self.logger.log(LogLevel.DEBUG, "_status_animation_thread ループ実行中") # 追加ログ
            # ドットの数を増やす (最大数に達したら0に戻る)
            self.animation_dots = (self.animation_dots + 1) % (self.animation_max_dots + 1)
            dots = "." * self.animation_dots
            # TkinterのLabel更新はメインスレッドで行う必要があるため、root.afterを使用
            self.logger.log(LogLevel.DEBUG, f"_status_animation_thread: root.after でテキスト更新をスケジュール ({dots})") # 追加ログ
            self.root.after(0, lambda: self.status_label.config(text=f"描画中{dots}"))
            # 一定時間待機してアニメーションの間隔を調整
            time.sleep(0.1)
        self.logger.log(LogLevel.DEBUG, "_status_animation_thread: アニメーション実行ループ終了") # 追加ログ
        # アニメーション終了後、ステータスを「完了」に更新
        self.logger.log(LogLevel.DEBUG, "_status_animation_thread: root.after で完了表示をスケジュール") # 追加ログ
        self.root.after(0, lambda: self.status_label.config(text="完了"))
        self.logger.log(LogLevel.DEBUG, "_status_animation_thread 終了") # 追加ログ

    def _stop_status_animation(self):
        """ステータスバーの描画中アニメーションを停止"""
        self.logger.log(LogLevel.DEBUG, "_stop_status_animation 実行") # 追加ログ
        if self.animation_running:
            self.logger.log(LogLevel.DEBUG, "_stop_status_animation: アニメーション停止要求フラグをセットします") # 追加ログ
            self.animation_running = False
            # アニメーションスレッドが終了するのを待つ (短い処理なのですぐに終わるはず)
            if self.animation_thread and self.animation_thread.is_alive():
                self.logger.log(LogLevel.DEBUG, "_stop_status_animation: アニメーションスレッドのjoinを待ちます") # 追加ログ
                self.animation_thread.join(timeout=0.5) # タイムアウトを設定
                if self.animation_thread.is_alive():
                    self.logger.log(LogLevel.WARNING, "_stop_status_animation: ステータスアニメーションスレッドが終了しませんでした。")
                else:
                    self.logger.log(LogLevel.DEBUG, "_stop_status_animation: アニメーションスレッドが正常に終了しました。") # 追加ログ

            self.animation_thread = None # スレッド参照をクリア
            self.logger.log(LogLevel.DEBUG, "_stop_status_animation 完了: アニメーション停止処理が完了しました") # 追加ログ
        else:
             self.logger.log(LogLevel.DEBUG, "_stop_status_animation: アニメーションは実行されていませんでした") # 追加ログ

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
                self.logger.log(LogLevel.SUCCESS, f"Matplotlib Figureサイズ更新完了: {new_width_inches:.2f}x{new_height_inches:.2f}インチ ({new_width_pixels}x{new_height_pixels}ピクセル)")
                # Figureサイズ変更によりAxesの表示も自動的に更新されるはずですが、必要に応じて
                # self.fractal_canvas.canvas.draw_idle() を追加しても良いかもしれません。（ただしパフォーマンス注意）
            else:
                self.logger.log(LogLevel.ERROR, "FractalCanvasまたはFigureが利用できません。Figureサイズ更新をスキップしました。")
        except Exception as e:
            self.logger.log(LogLevel.ERROR, f"Matplotlib Figureサイズ更新中にエラー: {e}")
