==============================
# MODULE_INFO:
debug_logger.py

## MODULE_PURPOSE
デバッグ用のログ出力を管理するクラス

## CLASS_DEFINITION:
名前: DebugLogger
役割:
- ログの出力処理を行う
- 設定ファイルに基づいてログレベルのフィルタリングを行う
親クラス: なし

## DEPENDENCIES
inspect: 呼び出し元の情報取得
os: パス操作
time: 時間計測
typing: 型ヒント
rich.print: リッチテキスト出力
rich.markup.escape: エスケープ処理
enum.Enum: Enum型
ui.zoom_function.enums.LogLevel: ログレベル定義

## CLASS_ATTRIBUTES
self.debug_enabled: bool - デバッグ関連の機能を有効にするフラグ (設定ファイルから)
self.min_log_level: LogLevel - 表示する最小ログレベル (設定ファイルから)
self.start_time: float - ログ出力開始時刻
self.project_root: str - プロジェクトルートディレクトリのパス

## METHOD_SIGNATURES
def __init__(self, debug_enabled: bool = True, min_level_str: Optional[str] = "DEBUG") -> None
機能: コンストラクタ。クラスの初期化、ログ出力開始時刻の記録、プロジェクトルートディレクトリのパスを取得、表示する最小ログレベルを設定する。

def log(self, level: LogLevel, message: str, context: Optional[Dict[str, Any]] = None, force: bool = False) -> None
機能: ログを出力する（外部呼び出し用）。デバッグが無効、またはログレベルが設定された最小レベルより低い場合は出力しない（force=True の場合は除く）。

def _log_internal(self, level: LogLevel, message: str, context: Optional[Dict[str, Any]] = None, force: bool = False, stacklevel: int = 3) -> None
機能: ログ出力の内部実装。ログの出力形式を整形し、`rprint` で出力する。エラー発生時は標準出力する。

def _get_caller_info(self, stacklevel: int) -> Tuple[str, str, int]
機能: 呼び出し元の関数名、ファイル名（プロジェクトルートからの相対パス）、行番号を取得する。

def _get_color(self, level: LogLevel) -> str
機能: ログレベルに応じた色名を取得する。

def _get_project_root(self) -> str
機能: プロジェクトルートのパスを取得する。

def _format_context(self, context: Dict[str, Any]) -> str
機能: コンテキスト情報を文字列に整形する。数値やEnumなどの特定の型を考慮してフォーマットする。

## CORE_EXECUTION_FLOW
__init__ -> log (フィルタリング) -> _log_internal -> _get_caller_info, _get_color, _get_project_root, _format_context

## KEY_LOGIC_PATTERNS
- ログ出力: レベルと設定に基づいたログ出力
- ログレベルフィルタリング: 設定された最小レベルによるログ表示の制御
- コンテキスト管理: ログにコンテキスト情報を付加
- エラーハンドリング: ログ出力失敗時のエラー処理
- 呼び出し元情報取得: inspectによる関数名、ファイル名、行番号の取得

## CRITICAL_BEHAVIORS
- ログの正確性と詳細さ
- ログレベルフィルターの正確な適用
- パス解決（プロジェクトルート相対パス）の正確性
- コンテキスト情報の適切な整形
- ロガー自体で発生したエラーのフォールバック処理


==============================
# MODULE_INFO:
enum_debug.py

## MODULE_PURPOSE
Enum (列挙型) の定義

## CLASS_DEFINITION:
名前: LogLevel
役割: ログレベルを定義するEnum
親クラス: enum.Enum

## DEPENDENCIES
enum.Enum: Enum型
enum.auto: 自動値割り当て

## CLASS_ATTRIBUTES
ZoomState:

LogLevel:
- DEBUG: デバッグ
- INIT: 初期化処理
- CALL: メソッド呼出し元
- SUCCESS: 成功
- INFO: 情報
- WARNING: 警告
- ERROR: エラー
- CRITICAL: 致命的

## METHOD_SIGNATURES
(Enum クラスのため、特筆すべきメソッドはない)

## CORE_EXECUTION_FLOW
Enum定義のみ

## KEY_LOGIC_PATTERNS
- Enumによるレベルの定義

## CRITICAL_BEHAVIORS
- レベルの正確な表現
