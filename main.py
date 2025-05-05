import tkinter as tk
from core import MainWindow, load_config
from debug import DebugLogger, LogLevel

if __name__ == "__main__":

    # 最小限の要素で仮の DebugLogger 用インスタンスを作る。load_config でロガーを使うので。
    # 仮とはいっても config.json でのロガー用設定は True と DEBUG だけなので、
    # 今後ロガー用の設定要素が増えなければ、正式な DebugLogger インスタンスを作る必要はない。
    # load_config 内では print を使うという方法もある。
    # 主に、こういうやり方もあるという勉強用でやっている。
    temp_logger = DebugLogger(True, "DEBUG")  # デフォルト値使用
    temp_logger.log(LogLevel.INIT, "DebugLogger(仮) クラスのインスタンス作成成功")

    temp_logger.log(LogLevel.INIT, "設定ファイル読込開始 (DebugLogger(仮)を使用)")
    config = load_config(temp_logger, "config.json")
    # -------------------------------------------------------------------------------

    # 設定ファイルからログ設定を取得
    logging_config = config.get("logging", {})

    temp_logger.log(LogLevel.INIT, "DebugLogger クラスのインスタンス作成開始")
    logger = DebugLogger(
        debug_enabled=logging_config.get("debug_enabled", True),
        min_level_str=logging_config.get("min_level", "DEBUG")
    )

    logger.log(LogLevel.INFO, "App START: Tkinter ルートウィンドウを作成")
    root = tk.Tk()

    logger.log(LogLevel.INIT, "MainWindow クラスのインスタンス作成開始")
    app = MainWindow(root, logger, config)

    logger.log(LogLevel.DEBUG, "Tkinter のメインイベントループを開始")
    root.mainloop()

    logger.log(LogLevel.INFO, "App FIN")
