import tkinter as tk
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

class FractalCanvas:
    def __init__(self, parent):
        self.parent = parent
        self.fig = Figure(figsize=(6, 6), dpi=100)
        self.ax = self.fig.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.parent)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def update_canvas(self, fractal_image, params):
        self.ax.clear()
        # 表示範囲は -2 ～ 2 として描画（必要に応じて調整）
        self.ax.imshow(fractal_image, extent=[-2, 2, -2, 2], origin="lower", aspect="equal")
        self.ax.set_title(f"{params['fractal_type']}set")
        self.fig.tight_layout()
        self.canvas.draw()
