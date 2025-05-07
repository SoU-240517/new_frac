"""
main.py

このファイルはアプリケーションのエントリーポイントです。
Tkinterを使用したGUIアプリケーションの起動と初期化を行います。

主な機能:
- 設定ファイルの読み込み
- デバッグロガーの初期化
- メインウィンドウの作成と起動
"""

import tkinter as tk
from core import MainWindow, load_config
from debug import DebugLogger, LogLevel

if __name__ == "__main__":

    # DebugLogger 用インスタンス作成（仮）
    temp_logger = DebugLogger(True, "DEBUG")  # デフォルト値使用

    # 設定ファイルの読み込み
    config = load_config(temp_logger, "config.json")

    # 設定内容から DebugLogger 用の情報取得
    logging_config = config.get("logging", {})

    logger = DebugLogger(
        debug_enabled=logging_config.get("debug_enabled", True),
        min_level_str=logging_config.get("min_level", "DEBUG")
    )

    root = tk.Tk()
    app = MainWindow(root, logger, config)
    root.mainloop()
