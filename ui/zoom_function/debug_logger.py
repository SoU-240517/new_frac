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
    - ログの出力処理を行う
    Attributes:
        debug_enabled (bool): デバッグログ出力を有効にするかどうか
        start_time (float): ログ出力開始時刻
        project_root (str): プロジェクトルートディレクトリのパス
    """

    def __init__(self, debug_enabled: bool = True):
        """DebugLogger クラスのコンストラクタ
        - クラスの初期化を行う
        - ログ出力開始時刻を記録し、プロジェクトルートディレクトリのパスを取得する
        Args:
            debug_enabled (bool, optional): デバッグログ出力を有効にするかどうか。デフォルトは True
        """
        self.debug_enabled = debug_enabled
        self.start_time = time.time()
        self.project_root = self._get_project_root()
        self._log_internal(LogLevel.INIT, "DebugLogger", force=True) # 内部ログ出力

    def log(self,
            level: LogLevel,
            message: str,
            context: Optional[Dict[str, Any]] = None,
            force: bool = False
    ) -> None:
        """ログを出力する（外部呼び出し用）
        - デバッグログが無効かつログレベルが DEBUG の場合は、ログ出力を行わない
        Args:
            level (LogLevel): ログレベル
            message (str): ログメッセージ
            context (Optional[Dict[str, Any]], optional): コンテキスト情報。デフォルトは None
            force (bool, optional): 強制的にログを出力するかどうか。デフォルトは False
        """
        if not self.debug_enabled and not force and level == LogLevel.DEBUG:
            return
        self._log_internal(level, message, context, force) # 内部ログ出力

    def _log_internal(
            self,
            level: LogLevel,
            message: str,
            context: Optional[Dict[str, Any]] = None,
            force: bool = False,
            stacklevel: int = 3
    ) -> None:
        """ログ出力の内部実装
        - ログの出力形式を整形し、`rprint` で出力する
        - エラー発生時は、エラーメッセージを標準出力する
        Args:
            level (LogLevel): ログレベル
            message (str): ログメッセージ
            context (Optional[Dict[str, Any]], optional): コンテキスト情報。デフォルトは None
            force (bool, optional): 強制的にログを出力するかどうか。デフォルトは False
            stacklevel (int, optional): 呼び出し元のスタックレベル。デフォルトは 3
        """
        try:
            caller_info = self._get_caller_info(stacklevel) # 呼び出し元の情報を取得
            elapsed_time = time.time() - self.start_time # 経過時間を計算
            color = self._get_color(level) # ログレベルに応じた色を取得
            level_name = level.name # ログレベル名を取得

            log_prefix = f"[{elapsed_time:.3f}s] {level_name}" # ログプレフィックスを生成
            location = f"[{caller_info[0]}: {caller_info[1]}:{caller_info[2]}]" # ログ出力位置情報を生成

            escaped_message = escape(message) # ログメッセージをエスケープ
            escaped_location = escape(location) # ログ出力位置情報をエスケープ

            if context:
                formatted_context = self._format_context(context) # コンテキスト情報を整形
                log_message = f"[grey50]{log_prefix}[/grey50][{color}] {escaped_message} | {formatted_context} [/{color}][grey50]{escaped_location}[/grey50]" # コンテキスト情報がある場合のログメッセージを生成
            else:
                log_message = f"[grey50]{log_prefix}[/grey50][{color}] {escaped_message} [/{color}][grey50]{escaped_location}[/grey50]" # コンテキスト情報がない場合のログメッセージを生成

            rprint(log_message) # ログメッセージを出力

        except Exception as e:
            print(f"[DebugLogger Error] Failed to log: {e}") # エラーメッセージを出力

    def _get_caller_info(self, stacklevel: int) -> Tuple[str, str, int]:
        """呼び出し元の情報を取得する
        - 呼び出し元の関数名、ファイル名、行番号を取得する
        Args:
            stacklevel (int): 呼び出し元のスタックレベル
        Returns:
            Tuple[str, str, int]: 呼び出し元の関数名、ファイル名、行番号。取得できない場合は "unknown", "unknown", 0 を返す
        """
        try:
            stack = inspect.stack() # 現在のスタックフレームを取得
            if len(stack) > stacklevel:
                frame = stack[stacklevel] # 指定されたスタックレベルのフレームを取得
                abs_path = os.path.abspath(frame.filename) # 絶対パスを取得
                try:
                    relative_path = os.path.relpath(abs_path, self.project_root) # 相対パスを取得
                    file_path = relative_path.replace('\\', '/') # パス区切り文字を置換
                except ValueError:
                    file_path = os.path.basename(abs_path) # ファイル名のみを取得
                return frame.function, file_path, frame.lineno # 関数名、ファイルパス、行番号を返す
            return "unknown", "unknown", 0 # 取得できない場合は "unknown", "unknown", 0 を返す
        except Exception:
            return "unknown", "unknown", 0 # エラーが発生した場合も "unknown", "unknown", 0 を返す

    def _get_color(self, level: LogLevel) -> str:
        """ログレベルに応じた色を取得する
        - ログレベルに対応する色名を返す
        Args:
            level (LogLevel): ログレベル
        Returns:
            str: ログレベルに対応する色名
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
        return color_map.get(level, "white") # ログレベルに対応する色名を返す。対応する色がない場合は "white" を返す

    def _get_project_root(self) -> str:
        """プロジェクトルートのパスを取得する
        - 現在のファイルのディレクトリから2階層上のディレクトリの絶対パスを返す
        Returns:
            str: プロジェクトルートのパス
        """
        logger_dir = os.path.dirname(__file__) # 現在のファイルのディレクトリパスを取得
        return os.path.abspath(os.path.join(logger_dir, '..', '..')) # プロジェクトルートの絶対パスを返す

    def _format_context(self, context: Dict[str, Any]) -> str:
        """コンテキスト情報を整形する
        - コンテキスト情報を文字列に整形する
        Args:
            context (Dict[str, Any]): コンテキスト情報
        Returns:
            str: 整形後のコンテキスト情報
        """
        items = []
        for k, v in context.items():
            if isinstance(v, float):
                items.append(f"{k} = {v:.3f}") # float型の場合、小数点以下3桁まで表示
            elif isinstance(v, Enum):
                items.append(f"{k} = {v.name}") # Enum型の場合、名前を表示
            else:
                items.append(f"{k} = {v}") # その他の型の場合、そのまま表示
        return ", ".join(items) # カンマ区切りで文字列を結合
