from ui.main_window import MainWindow
import tkinter as tk

# アプリケーションのエントリーポイント。
# メインの Tkinter ウィンドウを初期化し、
# メインのアプリケーション ウィンドウを作成し、
# イベント ループを開始します。
if __name__ == "__main__":
    root = tk.Tk()
    app = MainWindow(root)
    root.mainloop()
