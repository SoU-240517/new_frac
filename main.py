import tkinter as tk
from ui.main_window import MainWindow
from ui.zoom_function.debug_logger import DebugLogger
from ui.zoom_function.enums import LogLevel

if __name__ == "__main__":
    logger = DebugLogger() # DebugLogger クラスのインスタンスを作成
    logger.log(LogLevel.INFO, "App START")
    root = tk.Tk() # Tkinter ルートウィンドウを作成
    logger.log(LogLevel.DEBUG, "MainWindow クラスのインスタンスを作成")
    app = MainWindow(root, logger)
    logger.log(LogLevel.DEBUG, "Tkinter のメインイベントループを開始")
    root.mainloop()
    logger.log(LogLevel.INFO, "App FIN")
