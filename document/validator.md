==============================
# MODULE_INFO:
event_validator.py

## MODULE_PURPOSE
イベントの検証を行うクラス

## CLASS_DEFINITION:
名前: EventValidator
役割:
- イベントが発生したAxesが期待されたものであるかを検証
- マウスボタン情報や座標情報の有無を検証
親クラス: なし

## DEPENDENCIES
dataclasses.dataclass: データクラス
matplotlib.axes.Axes: Axesオブジェクト
matplotlib.backend_bases.MouseEvent: マウスイベント
matplotlib.backend_bases.KeyEvent: キーボードイベント
typing: 型ヒント
ui.zoom_function.debug_logger.DebugLogger: デバッグログ
ui.zoom_function.enums.LogLevel: ログレベル定義

## CLASS_ATTRIBUTES
self.logger: DebugLogger - デバッグログ出力用ロガー

## METHOD_SIGNATURES
def __init__(self, logger: 'DebugLogger') -> None
機能: コンストラクタ。ロガーを設定

def validate_event(self, event: MouseEvent | KeyEvent, ax: Axes) -> ValidationResult
機能: イベントを検証し、検証結果を返す

def _validate_axes(self, event: MouseEvent, ax: Axes, result: ValidationResult) -> None
機能: イベントが発生したAxesが期待されたものであるかを検証

def _validate_button(self, event: MouseEvent, result: ValidationResult) -> None
機能: マウスボタン情報の有無を検証

def _validate_coordinates(self, event: MouseEvent, result: ValidationResult) -> None
機能: 座標情報の有無を検証

## CORE_EXECUTION_FLOW
__init__ -> validate_event -> _validate_axes, _validate_button, _validate_coordinates

## KEY_LOGIC_PATTERNS
- イベント検証: イベントの種類と内容に応じた検証
- データクラス: 検証結果の格納

## CRITICAL_BEHAVIORS
- イベント検証の正確性
- 検証結果の適切な格納と提供
