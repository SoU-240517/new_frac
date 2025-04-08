import tkinter as tk
from ui.main_window import MainWindow
from ui.zoom_function.debug_logger import DebugLogger
from ui.zoom_function.enums import LogLevel

if __name__ == "__main__":
    logger = DebugLogger() # Logger インスタンスを作成
    logger.log(LogLevel.INIT, "App START")
    root = tk.Tk()
    app = MainWindow(root, logger)
    root.mainloop()
    logger.log(LogLevel.INIT, "App FIN")
