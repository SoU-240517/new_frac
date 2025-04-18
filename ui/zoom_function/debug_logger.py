import inspect
import os
import time
from typing import Optional, Dict, Any
from rich import print as rprint
from rich.markup import escape
from enum import Enum
from .enums import LogLevel

class DebugLogger:
    """ デバッグログを出力するクラス """
    def __init__(self, debug_enabled=True):
        self.debug_enabled = debug_enabled
        self.start_time = time.time()
        logger_dir = os.path.dirname(__file__)
        self.project_root = os.path.abspath(os.path.join(logger_dir, '..', '..'))
        # 自分自身の初期化ログを出力 (呼出し元情報は __init__ 自身になる)
        self._log_internal(LogLevel.INIT, "DebugLogger", force=True, stacklevel=1)

    def log(
            self, level: LogLevel,
            message: str,
            context: Optional[Dict[str, Any]] = None,
            force: bool = False):
        """ ログを出力 (外部び出し用) """
        if not self.debug_enabled and not force and level == LogLevel.DEBUG:
            return
        # 呼出し元を正しく特定するため stacklevel=2
        self._log_internal(level, message, context, force, stacklevel=2)

    def _log_internal(
            self, level: LogLevel,
            message: str,
            context: Optional[Dict[str, Any]] = None,
            force: bool = False,
            stacklevel: int = 1): # スタックレベルを指定可能にする
        """ ログ出力の内部実装 """
        # 呼出し元の情報を取得
        caller_frame_record = None # 呼出し元のフレーム情報
        file_path = "unknown"
        line_no = 0
        func_name = "unknown"
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
                func_name = caller_frame_record.function # 関数名を取得
        except Exception as e:
             print(f"[DebugLogger Error] Failed to get caller info: {e}")
        finally:
            pass
        elapsed_time = time.time() - self.start_time
        color_map = {
            LogLevel.INIT: "grey50",
            LogLevel.DEBUG: "grey50",
            LogLevel.CALL: "green",
            LogLevel.SUCCESS: "blue",
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
        log_prefix = f"[{elapsed_time:.3f}s] {level_name}:"
        location = f"[{func_name}: {file_path}:{line_no}]"
        escaped_message = escape(message)
        escaped_location = escape(location)
        log_message = f"[grey50]{log_prefix}[/grey50][{color}] {escaped_message} [/{color}][grey50]{escaped_location}[/grey50]"
        if context:
            log_message = f"[grey50]{log_prefix}[/grey50][{color}] {escaped_message} | {self._format_context(context)} [/{color}][grey50]{escaped_location}[/grey50]"
        rprint(log_message)

    def _format_context(self, context: Dict[str, Any]) -> str:
        """ コンテキスト情報を整形 """
        items = [] # 空のリスト items を初期化
        for k, v in context.items(): # context のキー（k）と値（v）を1つずつ取得し、それぞれ処理する
            if isinstance(v, float): # 値 v が浮動小数点型（float）の場合
                items.append(f"{k} = {v:.3f}") # 小数点以下3桁までのフォーマットに整形
            elif isinstance(v, Enum): # 値 v が列挙型（Enum）の場合
                items.append(f"{k} = {v.name}") # v.name プロパティ（列挙値の名前）を使用して整形
            else:
                items.append(f"{k} = {v}") # 浮動小数点型や列挙型でない場合、そのまま文字列として追加
        return ", ".join(items) # items リスト内のすべての文字列をカンマ区切りで結合、1つの文字列として返す
