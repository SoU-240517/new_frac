import inspect
import os
import time
from typing import Optional, Dict, Any, Tuple
from rich import print as rprint
from rich.markup import escape
from enum import Enum
from .enums import LogLevel

class DebugLogger:
    """デバッグ用のログ出力を管理するクラス
    - 役割:
        - ログ出力
    """

    def __init__(self, debug_enabled: bool = True):
        """DebugLogger クラスのコンストラクタ（親: main）
        Args:
            debug_enabled (bool, optional): デバッグログ出力を有効化するかどうか. Defaults to True.
        """
        self.debug_enabled = debug_enabled
        self.start_time = time.time()
        self.project_root = self._get_project_root()
        self._log_internal(LogLevel.INIT, "DebugLogger", force=True)

    def log(self,
            level: LogLevel,
            message: str,
            context: Optional[Dict[str, Any]] = None,
            force: bool = False
    ) -> None:
        """ ログを出力（外部び出し用）
        Args:
            level (LogLevel): ログレベル
            message (str): ログメッセージ
            context (Optional[Dict[str, Any]], optional): コンテキスト情報. Defaults to None.
            force (bool, optional): 強制的にログを出力するかどうか. Defaults to False.
        """
        if not self.debug_enabled and not force and level == LogLevel.DEBUG:
            return
        self._log_internal(level, message, context, force)

    def _log_internal(
            self,
            level: LogLevel,
            message: str,
            context: Optional[Dict[str, Any]] = None,
            force: bool = False,
            stacklevel: int = 3
    ) -> None:
        """ログ出力の内部実装
        Args:
            level (LogLevel): ログレベル
            message (str): ログメッセージ
            context (Optional[Dict[str, Any]], optional): コンテキスト情報. Defaults to None.
            force (bool, optional): 強制的にログを出力するかどうか. Defaults to False.
            stacklevel (int, optional): スタックレベル. Defaults to 3.
        """
        try:
            caller_info = self._get_caller_info(stacklevel)
            elapsed_time = time.time() - self.start_time
            color = self._get_color(level)
            level_name = level.name

            log_prefix = f"[{elapsed_time:.3f}s] {level_name}"
            location = f"[{caller_info[0]}: {caller_info[1]}:{caller_info[2]}]"

            escaped_message = escape(message)
            escaped_location = escape(location)

            if context:
                formatted_context = self._format_context(context)
                log_message = f"[grey50]{log_prefix}[/grey50][{color}] {escaped_message} | {formatted_context} [/{color}][grey50]{escaped_location}[/grey50]"
            else:
                log_message = f"[grey50]{log_prefix}[/grey50][{color}] {escaped_message} [/{color}][grey50]{escaped_location}[/grey50]"

            rprint(log_message)

        except Exception as e:
            print(f"[DebugLogger Error] Failed to log: {e}")

    def _get_caller_info(self, stacklevel: int) -> Tuple[str, str, int]:
        """呼出し元の情報を取得
        Args:
            stacklevel (int): スタックレベル
        Returns:
            Tuple[str, str, int]: 呼出し元の関数名、ファイル名、行番号
        """
        try:
            stack = inspect.stack()
            if len(stack) > stacklevel:
                frame = stack[stacklevel]
                abs_path = os.path.abspath(frame.filename)
                try:
                    relative_path = os.path.relpath(abs_path, self.project_root)
                    file_path = relative_path.replace('\\', '/')
                except ValueError:
                    file_path = os.path.basename(abs_path)
                return frame.function, file_path, frame.lineno
            return "unknown", "unknown", 0
        except Exception:
            return "unknown", "unknown", 0

    def _get_color(self, level: LogLevel) -> str:
        """ログレベルに応じた色を取得
        Args:
            level (LogLevel): ログレベル
        Returns:
            str: 色名
        """
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
        return color_map.get(level, "white")

    def _get_project_root(self) -> str:
        """プロジェクトルートのパスを取得
        Returns:
            str: プロジェクトルートのパス
        """
        logger_dir = os.path.dirname(__file__)
        return os.path.abspath(os.path.join(logger_dir, '..', '..'))

    def _format_context(self, context: Dict[str, Any]) -> str:
        """コンテキスト情報を整形
        Args:
            context (Dict[str, Any]): コンテキスト情報
        Returns:
            str: 整形後のコンテキスト情報
        """
        items = []
        for k, v in context.items():
            if isinstance(v, float):
                items.append(f"{k} = {v:.3f}")
            elif isinstance(v, Enum):
                items.append(f"{k} = {v.name}")
            else:
                items.append(f"{k} = {v}")
        return ", ".join(items)
