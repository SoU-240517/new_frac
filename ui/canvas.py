import tkinter as tk
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

class FractalCanvas:
    def __init__(self, parent):
        """
        フラクタル描画キャンバスを初期化します。
        マトリックス プロットを使用してフラクタルを描画し、
        キャンバスを Tkinter ウィジェットに関連付けます。
        フラクタル画像が更新されたときにキャンバスを更新します。

        引数:
            parent (tk.Widget): キャンバスを含む Tkinter ウィジェット。
        """
        self.parent = parent
        self.fig = Figure(figsize=(6, 6), dpi=100)
        self.ax = self.fig.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.parent)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def update_canvas(self, fractal_image, params):
        """
        キャンバスを更新し、指定されたフラクタル画像を描画します。
        指定された画像をキャンバスに表示し、フラクタルのタイプに基づいてタイトルを設定します。
        画像は [-2, 2] の範囲で描画され、アスペクト比を維持します。

        引数:
            fractal_image (numpy.ndarray): 描画するフラクタル画像
            params (dict): フラクタルのパラメータ（'fractal_type' キーを含む）
        """
        self.ax.clear()
        self.ax.axis('off')  # 座標軸を非表示にする
        self.fig.subplots_adjust(left=0, right=1, top=1, bottom=0)  # 追加：余白をなくす
        self.ax.set_position([0, 0, 1, 1])  # 追加：サブプロットをFigure全体に広げる
        # 表示範囲は -2 ～ 2 として描画（必要に応じて調整）
        self.ax.imshow(fractal_image, extent=[-2, 2, -2, 2], origin="lower", aspect="equal")
#        self.ax.set_title(f"{params['fractal_type']}set")
#        self.fig.tight_layout()
        # 余白をなくし、AxesをFigure全体に広げる
        self.fig.patch.set_visible(False)  # Figureの背景を非表示にする
        self.canvas.draw()
