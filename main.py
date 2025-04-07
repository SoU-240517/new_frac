import tkinter as tk
from ui.main_window import MainWindow

if __name__ == "__main__":
    print('\033[34m'+'START : main.py'+'\033[0m')
    root = tk.Tk()  # Tkinter のルートウィンドウを作成
    app = MainWindow(root)  # MainWindow のインスタンスを作成
    root.mainloop()  # Tkinter のメインループを開始
