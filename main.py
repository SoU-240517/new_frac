import tkinter as tk
from ui.main_window import MainWindow
from ui.zoom_function.debug_logger import DebugLogger
from ui.zoom_function.enums import LogLevel

if __name__ == "__main__":
    logger = DebugLogger() # Logger インスタンスを作成
    logger.log(LogLevel.INFO, "App START")
    root = tk.Tk() # Tkinter ルートウィンドウを作成
    app = MainWindow(root, logger) # MainWindow インスタンスを作成
    root.mainloop() #  Tkinter ルートウィンドウでイベントループを開始
    logger.log(LogLevel.INFO, "App FIN")
