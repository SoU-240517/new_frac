import tkinter as tk
from ui.main_window import MainWindow
from ui.zoom_function.debug_logger import DebugLogger
from ui.zoom_function.enums import LogLevel

"""
生成AI用のコメント：
- ログ出力が多いが消さないこと（製作者が不慣れなのでコードの流れを追うために多く書いている）
- 矩形（ズーム領域）がある場合は、マウス移動イベントを切断しない（マウスカーソルの変更が必要なので）
- 以下の明確化について、現在のコード中では不適切な部分もあるが、順次、以下の状態に修正する。
- キャンセルの明確化：
    - ズーム確定キャンセル：
        ズーム領域によって再描画されたフラクタルを元に戻す。
        パラメータパネルの情報も元に戻す
    - ズーム領域キャンセル：
        ズーム領域を消す。
    - ズーム領域編集キャンセル：
        ズーム領域の編集操作（移動、リサイズ、回転）を、一つ前の編集状態に戻す。
- 確定の明確化：
    - ズーム確定：
        ズーム操作全般を確定し、パラメータパネルの情報を更新した上で、フラクタルを再描画する。
    - ズーム領域編集確定：
        移動、リサイズ、回転の編集操作をし終わった状態の EDIT 状態で、まだ編集は続けれる状態。
"""

if __name__ == "__main__":
    logger = DebugLogger() # Logger インスタンスを作成
    logger.log(LogLevel.INFO, "App START")
    root = tk.Tk() # Tkinter ルートウィンドウを作成
    app = MainWindow(root, logger) # MainWindow インスタンスを作成
    root.mainloop() #  Tkinter ルートウィンドウでイベントループを開始
    logger.log(LogLevel.INFO, "App FIN")
