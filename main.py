import tkinter as tk
from ui.main_window import MainWindow

if __name__ == "__main__":
    print("START : main.py")
    root = tk.Tk()  # Tkinter のルートウィンドウを作成
    app = MainWindow(root)  # MainWindow のインスタンスを作成
    root.mainloop()  # Tkinter のメインループを開始
