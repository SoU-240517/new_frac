import tkinter as tk
from base.main_window import MainWindow
from debug.debug_logger import DebugLogger
from debug.enum_debug import LogLevel

if __name__ == "__main__":
    logger = DebugLogger() # DebugLogger クラスのインスタンスを作成

    logger.log(LogLevel.INFO, "App START")
    root = tk.Tk() # Tkinter ルートウィンドウを作成

    logger.log(LogLevel.INIT, "MainWindow クラスのインスタンス作成開始")
    app = MainWindow(root, logger)

    logger.log(LogLevel.DEBUG, "Tkinter のメインイベントループを開始")
    root.mainloop()

    logger.log(LogLevel.INFO, "App FIN")
