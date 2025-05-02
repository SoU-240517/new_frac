==============================
# MODULE_INFO:
__init__.py

## MODULE_PURPOSE
Validatorモジュールパッケージの初期化と公開インターフェースの定義

## CLASS_DEFINITION:
(クラス定義なし)

## DEPENDENCIES
- event_validator.EventValidator: イベント検証機能

## CLASS_ATTRIBUTES
(クラス属性なし)

## METHOD_SIGNATURES
(メソッドなし)

## CORE_EXECUTION_FLOW
1. パッケージの初期化
2. 必要なモジュールのインポート
3. 公開インターフェースの定義
4. パッケージバージョンの設定

## KEY_LOGIC_PATTERNS
- パッケージの公開インターフェース定義
- モジュールのインポート管理
- イベント検証機能の公開

## CRITICAL_BEHAVIORS
- イベント検証機能の正しく公開
- モジュール間の依存関係の管理
- インターフェースの一貫性維持


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
debug: DebugLogger, LogLevel

## CLASS_ATTRIBUTES
self.logger: DebugLogger - デバッグログ出力用ロガー

## METHOD_SIGNATURES
def __init__(self, logger: 'DebugLogger') -> None
機能: コンストラクタ。ロガーを設定

def validate_event(self, event: MouseEvent | KeyEvent, ax: Axes) -> ValidationResult
機能: イベントを検証し、検証結果を返す。サポートされていないイベント型の場合、TypeErrorを発生させる

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
- イベントタイプ別検証: MouseEventとKeyEventのそれぞれに対応した検証ロジック
- エラーハンドリング: サポートされていないイベント型の検出と処理

## CRITICAL_BEHAVIORS
- イベント検証の正確性
- 検証結果の適切な格納と提供
- サポートされていないイベント型の適切なエラーハンドリング
- 検証結果の一貫性維持
