from ui.main_window import MainWindow
import tkinter as tk

if __name__ == "__main__":
    root = tk.Tk()  # Tkinter のルートウィンドウを作成
    app = MainWindow(root)  # MainWindow のインスタンスを作成
    root.mainloop()  # Tkinter のメインループを開始
