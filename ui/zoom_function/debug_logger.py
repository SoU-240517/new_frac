import time
import inspect
import os
from typing import Optional, Dict, Any
from .enums import LogLevel
from rich import print as rprint
from rich.markup import escape
from enum import Enum

class DebugLogger:
    """ デバッグログを出力するクラス """
    def __init__(self, debug_enabled=True):
        self.debug_enabled = debug_enabled
        self.start_time = time.time()
        logger_dir = os.path.dirname(__file__)
        self.project_root = os.path.abspath(os.path.join(logger_dir, '..', '..'))

        # 自分自身の初期化ログを出力 (呼び出し元情報は __init__ 自身になる)
        self._log_internal(LogLevel.INIT, "DebugLogger initialized", force=True, stacklevel=1)

    def log(
            self, level: LogLevel,
            message: str,
            context: Optional[Dict[str, Any]] = None,
            force: bool = False):
        """ ログを出力 (外部呼び出し用) """
        if not self.debug_enabled and not force and level == LogLevel.DEBUG:
            return

        # 呼び出し元を正しく特定するため stacklevel=2
        self._log_internal(level, message, context, force, stacklevel=2)

    def _log_internal(
            self, level: LogLevel,
            message: str,
            context: Optional[Dict[str, Any]] = None,
            force: bool = False,
            stacklevel: int = 1): # スタックレベルを指定可能にする
        """ ログ出力の内部実装 """
        # 呼び出し元の情報を取得
        caller_frame_record = None
        file_path = "unknown"
        line_no = 0

        try:
            stack = inspect.stack()
            if len(stack) > stacklevel:
                 caller_frame_record = stack[stacklevel] # stacklevel番目のフレーム情報を取得

            if caller_frame_record:
                abs_path = os.path.abspath(caller_frame_record.filename)
                try:
                    relative_path = os.path.relpath(abs_path, self.project_root)
                    file_path = relative_path.replace('\\', '/')
                except ValueError:
                    file_path = os.path.basename(abs_path)
                line_no = caller_frame_record.lineno

        except Exception as e:
             print(f"[DebugLogger Error] Failed to get caller info: {e}")
        finally:
            pass

        elapsed_time = time.time() - self.start_time
        color_map = {
            LogLevel.INIT: "grey50",
            LogLevel.METHOD: "green",
            LogLevel.DEBUG: "blue",
            LogLevel.INFO: "white",
            LogLevel.WARNING: "yellow",
            LogLevel.ERROR: "red",
            LogLevel.CRITICAL: "bold red",
        }
        try:
            color = color_map.get(level, "white")
            level_name = level.name
        except AttributeError as e:
            color = "white"
            level_name = "UNKNOWN_LEVEL"

        log_prefix = f"[{elapsed_time:.3f}s][{level_name}]"
        location = f"[{file_path}:{line_no}]"
        escaped_message = escape(message)
        escaped_location = escape(location)

        log_message = f"[{color}]{log_prefix} {escaped_message}: {escaped_location}[/{color}]"
        if context:
            log_message += f" [{color}]| Context: {self._format_context(context)}[/{color}]"

        rprint(log_message)

    def _format_context(self, context: Dict[str, Any]) -> str:
        """ コンテキスト情報を整形 """
        items = []
        for k, v in context.items():
            if isinstance(v, float):
                items.append(f"{k}={v:.3f}")
            elif isinstance(v, Enum):
                items.append(f"{k}={v.name}") # Enum の場合は .name を使用
            else:
                items.append(f"{k}={v}")
        return ", ".join(items)
