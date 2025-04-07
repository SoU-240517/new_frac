import time
import inspect
import os
from typing import Optional, Dict, Any
from .enums import LogLevel

class DebugLogger:
    """ デバッグログを出力するクラス """
    def __init__(self, debug_enabled=True):
        print('\033[34m'+'INI: DebugLogger: debug_logger.py'+'\033[0m')
        self.debug_enabled = debug_enabled
        self.start_time = time.time()
        self.project_root = os.getcwd()  # プロジェクトルートを取得

    def log(
            self, level: LogLevel,
            message: str,
            context: Optional[Dict[str, Any]] = None,
            force: bool = False):
        """ ログを出力 """
        if not self.debug_enabled and not force and level == LogLevel.DEBUG:
            return

        # 呼び出し元の情報を取得
        caller = inspect.currentframe().f_back
        file_path = os.path.relpath(caller.f_code.co_filename, self.project_root)
        line_no = caller.f_lineno

        elapsed_time = time.time() - self.start_time
        log_prefix = f"[{elapsed_time:.3f}s][{level.name}]"
        log_message = f"{log_prefix} {message}"
        if context:
            log_message += f" | Context: {self._format_context(context)}: [{file_path}:{line_no}]"
        print(log_message)

    def _format_context(self, context: Dict[str, Any]) -> str:
        """ コンテキスト情報を整形 """
        print('\033[32m'+'_format_context: DebugLogger: debug_logger.py'+'\033[0m')
        items = []
        for k, v in context.items():
            if isinstance(v, float):
                items.append(f"{k}={v:.3f}")
            elif isinstance(v, Enum): # Enumもインポートが必要なので追加
                items.append(f"{k}={v.name}")
            else:
                items.append(f"{k}={v}")
        return ", ".join(items)

# Enum を _format_context で使うためにインポートしておく
from enum import Enum
