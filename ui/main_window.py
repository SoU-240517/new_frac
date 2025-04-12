import tkinter as tk
import numpy as np
from tkinter import ttk
from ui.canvas import FractalCanvas
from ui.parameter_panel import ParameterPanel
from fractal.render import render_fractal # render_fractal が rotation パラメータを扱えると仮定
from .zoom_function.debug_logger import DebugLogger
from .zoom_function.enums import LogLevel

class MainWindow:
    """ フラクタル描画アプリケーションのメインウィンドウクラス """
    def __init__(self, root, logger: DebugLogger):
        """ フラクタル描画アプリケーションのメインウィンドウ初期化（ズーム操作の状態管理も行う） """
        self.logger = logger
        self.logger.log(LogLevel.INIT, "MainWindow")

        self.root = root # Tkinter ルートウィンドウ
        self.root.title("フラクタル描画アプリケーション")
        self.root.geometry("1200x800")

        self.zoom_params = { # ズームパラメータに rotation を追加
            "center_x": 0.0,
            "center_y": 0.0,
            "width": 4.0,
            "height": 4.0, # 初期高さも幅と同じにする（後で縦横比で調整される）
            "rotation": 0.0 # 回転角度を追加
        }
        self.prev_zoom_params = None # ズームパラメータ：直前

        # メインフレームとして PanedWindow（可変分割ウィンドウ：横方向に並ぶ）を作成し、
        # その中にキャンバスフレームとパラメータパネルフレームを配置
        # キャンバスフレームは描画領域、パラメータパネルフレームは操作パネル
        self.main_frame = ttk.PanedWindow(root, orient=tk.HORIZONTAL)
        self.main_frame.pack(fill=tk.BOTH, expand=True) # メインフレームをルートウィンドウに追加
        self.canvas_frame = ttk.Frame(self.main_frame) # キャンバスフレームを作成
        self.main_frame.add(self.canvas_frame, weight=3) # パネルウィンドウに配置
        self.control_frame = ttk.Frame(self.main_frame) # コントロールフレームを作成
        self.main_frame.add(self.control_frame, weight=1) # パネルウィンドウに配置

        self.fractal_canvas = FractalCanvas(self.canvas_frame, self.logger)
        self.parameter_panel = ParameterPanel(self.control_frame, self.update_fractal, reset_callback=self.reset_zoom, logger=self.logger)

        self.logger.log(LogLevel.DEBUG, "コールバック初期化開始：on_zoom_confirm、on_zoom_cancel")
        self.fractal_canvas.set_zoom_callback(self.on_zoom_confirm, self.on_zoom_cancel)

        self.logger.log(LogLevel.DEBUG, "フラクタルキャンバスの初期化開始")
        self.update_fractal() # 初回描画

    def update_fractal(self, *args):
        """ 最新パラメータにズーム情報を上書きしてフラクタルを再描画 """
        self.logger.log(LogLevel.DEBUG, "描画パラメータ取得開始")
        panel_params = self.parameter_panel.get_parameters()

        # 描画パラメータに現在のズーム情報（回転含む）をマージ
        current_params = self.zoom_params.copy()
        current_params.update(panel_params) # パネル設定で上書き（max_iterなど）

        self.logger.log(LogLevel.DEBUG, "取得パラメータにてフラクタル描画開始")
        # render_fractal が rotation キーを解釈できる前提
        fractal_image = render_fractal(current_params, self.logger)

        self.logger.log(LogLevel.INFO, "キャンバス更新開始")
        self.fractal_canvas.update_canvas(fractal_image, current_params) # キャンバスを更新

    # on_zoom_confirm のシグネチャを (x, y, w, h, angle) に変更
    def on_zoom_confirm(self, x: float, y: float, w: float, h: float, angle: float):
        """ ズーム確定時のコールバック（縦横比を調整し、ズームレベルに応じて反復回数を自動調整） """
        # 矩形の中心を計算
        center_x = x + w / 2
        center_y = y + h / 2

        self.logger.log(LogLevel.DEBUG, "ズーム確定", {
            "rect_x": x, # 矩形の左下x (回転前)
            "rect_y": y, # 矩形の左下y (回転前)
            "rect_w": w, # 矩形の幅 (回転前)
            "rect_h": h, # 矩形の高さ (回転前)
            "center_x": center_x,
            "center_y": center_y,
            "angle": angle
        })

        # ズーム確定前の状態を保存（キャンセル機能用）
        self.prev_zoom_params = self.zoom_params.copy()

        # 縦横比補正 (幅を基準に高さを調整)
        aspect_ratio = self.fractal_canvas.fig.get_size_inches()[0] / self.fractal_canvas.fig.get_size_inches()[1]
        new_width = w # 選択された矩形の幅をそのまま使用
        new_height = new_width / aspect_ratio # 縦横比を維持するように高さを計算

        # ズームレベルに応じて `max_iterations` を増やす
        # 幅の変化率でズームファクターを計算
        zoom_factor = self.zoom_params["width"] / new_width if new_width > 0 else 1
        current_max_iter = int(self.parameter_panel.max_iter_var.get())
        # ズームインした場合のみ反復回数を増やす（上限あり）
        if zoom_factor > 1:
             # 対数的な増加、最低でも現在の値、上限1000
             new_max_iterations = min(1000, max(current_max_iter, int(current_max_iter + 50 * np.log2(zoom_factor))))
        else:
             new_max_iterations = current_max_iter # ズームアウト時は変更しない

        self.logger.log(LogLevel.DEBUG, "ズームパラメータを調整", {
            "aspect_ratio": aspect_ratio,
            "new_width": new_width,
            "new_height": new_height,
            "zoom_factor": zoom_factor,
            "current_max_iter": current_max_iter,
            "new_max_iterations": new_max_iterations
        })

        # 新しいズームパラメータを設定 (回転角度も含む)
        self.zoom_params = {
            "center_x": center_x,
            "center_y": center_y,
            "width": new_width,
            "height": new_height,
            "rotation": angle # 回転角度を設定
        }

        self.parameter_panel.max_iter_var.set(str(new_max_iterations))  # 反復回数をUIに反映
        self.update_fractal() # 新しいパラメータで再描画

    def on_zoom_cancel(self):
        """ ズームキャンセル時のコールバック """
        #self.logger.log(LogLevel.DEBUG, "Zoom cancelled")
        # キャンセル時は特に何もしない（ZoomSelector側で矩形はクリアされる）
        # 必要であれば prev_zoom_params を使って前の描画状態に戻すことも可能。
        # ズームキャンセルは、ズーム領域編集のキャンセルと、ズーム領域確定後のキャンセルの2種類がある。
        # ここでは、ズーム領域編集のキャンセル時に呼ばれることを想定。
        # if self.prev_zoom_params is not None:
        #     self.logger.log(LogLevel.DEBUG, "Restoring previous zoom parameters", context={"prev_zoom": self.prev_zoom_params})
        #     self.zoom_params = self.prev_zoom_params.copy()
        #     self.update_fractal()
        #     self.prev_zoom_params = None
        # else:
        #     self.logger.log(LogLevel.DEBUG, "No previous zoom parameters to restore.")
        pass # 何もしない

    def reset_zoom(self):
        """ 操作パネルの「描画リセット」ボタン押下時の処理（ズームパラメータを初期状態に戻して再描画） """
        self.logger.log(LogLevel.DEBUG, "描画リセット")
        self.zoom_params = { # rotation もリセット
            "center_x": 0.0,
            "center_y": 0.0,
            "width": 4.0,
            "height": 4.0, # 初期高さもリセット
            "rotation": 0.0 # 回転角度もリセット
        }
        self.prev_zoom_params = None
        # 必要であれば、パラメータパネルの反復回数なども初期値に戻す
        # self.parameter_panel.max_iter_var.set("100") # 例
        self.update_fractal() # 初期状態で再描画
