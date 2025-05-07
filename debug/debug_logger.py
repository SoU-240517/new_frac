import inspect
import os
import time
from enum import Enum
from rich import print as rprint
from rich.markup import escape
from typing import Optional, Dict, Any, Tuple
from .enum_debug import LogLevel

class DebugLogger:
    """
    デバッグ用のログ出力を管理するクラス

    このクラスは、アプリケーションのデバッグログを管理し、
    設定ファイルに基づいてログレベルのフィルタリングを行います。
    ログは rich ライブラリを使用してカラーフォーマットで出力されます。

    Attributes:
        debug_enabled (bool): デバッグ関連の機能を有効にするフラグ
        min_log_level (LogLevel): 表示する最小ログレベル
        start_time (float): ログ出力開始時刻
        project_root (str): プロジェクトルートディレクトリのパス
    """

    def __init__(self, debug_enabled: bool, min_level_str: str):
        """
        DebugLogger クラスのコンストラクタ

        初期化時に以下の処理を行います：
        1. デバッグ設定の初期化
        2. ログ出力開始時刻の記録
        3. プロジェクトルートディレクトリの取得
        4. 最小ログレベルの設定

        Args:
            debug_enabled (bool): デバッグ機能を有効にするか
            min_level_str (str): 表示する最小ログレベルの文字列

        Raises:
            KeyError: 無効なログレベル文字列が指定された場合
        """
        # 設定ファイルから渡された値で属性を設定
        self.debug_enabled = debug_enabled
        self.min_log_level = min_level_str # 最小ログレベルを設定
        self.start_time = time.time()
        self.project_root = self._get_project_root()

        if min_level_str:
            try:
                # 文字列を LogLevel Enum に変換
                self.min_log_level = LogLevel[min_level_str.upper()]
            except KeyError:
                # 無効な文字列が指定された場合は警告を出し、デフォルト (DEBUG) を使用
                self._log_internal(
                    LogLevel.WARNING,
                    f"無効なログレベル '{min_level_str}' が指定されました。デフォルトの DEBUG レベルを使用します。",
                    force=True, # この警告は常に出す
                    stacklevel=2 # 呼び出し元を調整
                )
                self.min_log_level = LogLevel.DEBUG

        # 初期化完了ログ (force=True で必ず表示)
        self._log_internal(
            LogLevel.INIT,
            f"DebugLogger クラスのインスタンス作成成功：debug_enabled={self.debug_enabled}, min_level={self.min_log_level.name}",
            force=True,
            stacklevel=2 # 呼び出し元を調整
        )

    def log(self,
            level: LogLevel,
            message: str,
            context: Optional[Dict[str, Any]] = None,
            force: bool = False
    ) -> None:
        """
        ログを出力する（外部呼び出し用）

        デバッグログが無効かつログレベルが DEBUG の場合は、
        ログ出力を行いません。

        Args:
            level (LogLevel): ログレベル
            message (str): ログメッセージ
            context (Optional[Dict[str, Any]], optional):
                追加のコンテキスト情報。デフォルトは None
            force (bool, optional):
                強制的にログを出力するかどうか。デフォルトは False
        """
        # 最小ログレベルでフィルタリング
        # force=True の場合を除き、メッセージのレベルが設定された最小レベルより低い場合は出力しない
        if not force and level.value < self.min_log_level.value:
             return # 表示レベルに満たない場合はここで処理を終了

        # 内部ログ出力関数を呼び出す (スタックレベルを調整)
        self._log_internal(level, message, context, force, stacklevel=3)

    def _log_internal(
            self,
            level: LogLevel,
            message: str,
            context: Optional[Dict[str, Any]] = None,
            force: bool = False, # force引数はフィルタリングに使われたので、ここでは不要だが残しておく
            stacklevel: int = 3
    ) -> None:
        """
        ログ出力の内部実装

        ログの出力形式を整形し、rich.printを使用して出力します。
        エラー発生時は、エラーメッセージを標準出力します。

        Args:
            level (LogLevel): ログレベル
            message (str): ログメッセージ
            context (Optional[Dict[str, Any]], optional):
                追加のコンテキスト情報。デフォルトは None
            force (bool, optional):
                強制的にログを出力するかどうか。デフォルトは False
            stacklevel (int, optional):
                呼び出し元のスタックレベル。デフォルトは 3

        Raises:
            Exception: ログ出力時に予期せぬエラーが発生した場合
        """
        try:
            # 呼び出し元の情報を取得 (stacklevel はこの関数を呼ぶ階層に応じて調整が必要)
            caller_info = self._get_caller_info(stacklevel)
            elapsed_time = time.time() - self.start_time # 経過時間を計算
            color = self._get_color(level) # ログレベルに応じた色を取得
            level_name = level.name # ログレベル名を取得

            # ログメッセージの構築 (変更なし)
            log_prefix = f"[{elapsed_time:.3f}s] {level_name:<8}" # レベル名を固定幅にすると見やすいかも
            location = f"[{caller_info[0]}: {caller_info[1]}:{caller_info[2]}]"
            escaped_message = escape(message)
            escaped_location = escape(location)

            if context:
                formatted_context = self._format_context(context) # コンテキスト情報を整形
                log_message = f"[grey50]{log_prefix}[/grey50][{color}] {escaped_message} | {formatted_context} [/{color}][grey50]{escaped_location}[/grey50]"
            else:
                log_message = f"[grey50]{log_prefix}[/grey50][{color}] {escaped_message} [/{color}][grey50]{escaped_location}[/grey50]"

            # rich print で出力
            rprint(log_message)

        except Exception as e:
            # ロガー自体でエラーが発生した場合のフォールバック出力
            print(f"[DebugLogger Error] Failed to log message: '{message}'. Error: {e}")

    def _get_caller_info(self, stacklevel: int) -> Tuple[str, str, int]:
        """
        呼び出し元の情報を取得する

        呼び出し元の関数名、ファイル名、行番号を取得します。
        プロジェクトルートからの相対パスを表示します。

        Args:
            stacklevel (int): 呼び出し元のスタックレベル

        Returns:
            Tuple[str, str, int]:
                (関数名, ファイルパス, 行番号)のタプル
                取得できない場合は ("unknown", "unknown", 0) を返す

        Raises:
            Exception: inspect.stack()で予期せぬエラーが発生した場合
        """
        try:
            stack = inspect.stack()
            # スタックレベルが範囲内か確認
            if len(stack) > stacklevel:
                frame = stack[stacklevel]
                abs_path = os.path.abspath(frame.filename)
                try:
                    # プロジェクトルートからの相対パスを試みる
                    relative_path = os.path.relpath(abs_path, self.project_root)
                    # Windows パス区切り文字を '/' に統一
                    file_path = relative_path.replace('\\', '/')
                except ValueError:
                     # プロジェクトルート外の場合はファイル名のみ表示
                    file_path = os.path.basename(abs_path)
                return frame.function, file_path, frame.lineno
            return "unknown", "unknown", 0 # スタック情報が不足
        except Exception as e:
             # inspect で予期せぬエラーが発生した場合
            print(f"[DebugLogger Error] Failed to get caller info: {e}")
            return "error", "error", 0

    def _get_color(self, level: LogLevel) -> str:
        """
        ログレベルに応じた色を取得する

        各ログレベルに対応する色を返します。
        色のマッピングは以下の通りです：
        - DEBUG: グレー
        - INIT: 水色
        - CALL: 緑
        - SUCCESS: 青
        - INFO: 白
        - WARNING: 黄
        - ERROR: 赤
        - CRITICAL: 赤（強調）

        Args:
            level (LogLevel): ログレベル

        Returns:
            str: ログレベルに対応する色名
        """
        color_map = {
            LogLevel.DEBUG: "grey50",
            LogLevel.INIT: "dim cyan",
            LogLevel.CALL: "green",
            LogLevel.SUCCESS: "bold blue",
            LogLevel.INFO: "white",
            LogLevel.WARNING: "yellow",
            LogLevel.ERROR: "red",
            LogLevel.CRITICAL: "bold red on white",
        }
        return color_map.get(level, "white")

    def _get_project_root(self) -> str:
        """
        プロジェクトルートのパスを取得する

        現在のファイルのディレクトリから2階層上のディレクトリの
        絶対パスを返します。

        Returns:
            str: プロジェクトルートのパス
        """
        # 現在のファイル (__file__) の場所に基づいてルートを決定
        logger_dir = os.path.dirname(__file__)
        # debug_logger.py が core/ にあると仮定して1階層上がる
        project_root = os.path.abspath(os.path.join(logger_dir, '..'))
        return project_root

    def _format_context(self, context: Dict[str, Any]) -> str:
        """
        コンテキスト情報を整形する

        コンテキスト情報を文字列に整形し、ログ出力に適した形式に
        変換します。

        Args:
            context (Dict[str, Any]): コンテキスト情報

        Returns:
            str: 整形後のコンテキスト情報
        """
        items = []
        for k, v in context.items():
            # repr を使うとより詳細な情報が得られる場合があるが、長くなりすぎる可能性も
            # formatted_v = repr(v)
            if isinstance(v, float):
                formatted_v = f"{v:.3f}" # 小数点以下3桁
            elif isinstance(v, Enum):
                formatted_v = v.name # Enum は名前
            # elif isinstance(v, np.ndarray):
            #     formatted_v = f"ndarray(shape={v.shape}, dtype={v.dtype})" # numpy 配列は形状と型
            else:
                # 長すぎる文字列は省略するなどしても良い
                formatted_v = str(v)
            items.append(f"{escape(str(k))}={escape(formatted_v)}") # キーもエスケープ
        return ", ".join(items)
