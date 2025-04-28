==============================
# MODULE_INFO:
cursor_manager.py

## MODULE_PURPOSE
マウスカーソルの形状を操作状態に応じて変更するクラス

## CLASS_DEFINITION:
名前: CursorManager
役割:
- イベントと状態に基づいてカーソル形状を更新する
- カーソルの状態を管理する
親クラス: なし

## DEPENDENCIES
tkinter (tk): UIフレームワーク
matplotlib.backend_bases.MouseEvent: MatplotlibのMouseEvent
typing: 型ヒント
ui.zoom_function.debug_logger.DebugLogger: デバッグログ管理
ui.zoom_function.enums.LogLevel: ログレベル定義
ui.zoom_function.enums.ZoomState: ズーム状態のEnum
ui.zoom_function.event_validator.EventValidator: イベント検証
ui.zoom_function.zoom_selector.ZoomSelector: ズーム選択 (遅延インポート)
ui.zoom_function.zoom_state_handler.ZoomStateHandler: ズーム状態管理 (遅延インポート)

## CLASS_ATTRIBUTES
self.zoom_selector: ZoomSelector - ZoomSelectorインスタンス
self.logger: DebugLogger - ログ出力用DebugLoggerインスタンス
self.validator: EventValidator - イベント検証用EventValidatorインスタンス
self._current_cursor: str - 現在のカーソル
self._canvas_widget: tk.Widget - カーソル操作対象のキャンバスウィジェット
CURSORS: dict - カーソル定義

## METHOD_SIGNATURES
def __init__(self, zoom_selector: 'ZoomSelector', logger: DebugLogger) -> None
機能: コンストラクタ。ZoomSelectorとロガーの設定、イベントバリデーターの初期化、キャンバスウィジェットの取得

def cursor_update(self, event: Optional[MouseEvent], state: ZoomState, near_corner_index: Optional[int] = None, is_rotating: bool = False) -> None
機能: イベントと状態に基づいてカーソル形状を更新

def _should_update_cursor(self, event: MouseEvent) -> bool
機能: カーソル更新が必要かを判定

def _determine_cursor(self, event: MouseEvent, state: ZoomState, near_corner_index: Optional[int], is_rotating: bool) -> str
機能: カーソルの種類を決定

def _update_cursor(self, new_cursor: str, state: ZoomState) -> None
機能: カーソルを更新

def set_default_cursor(self) -> None
機能: カーソルをデフォルトに戻す

## CORE_EXECUTION_FLOW
__init__ -> cursor_update -> _should_update_cursor, _determine_cursor, _update_cursor, set_default_cursor

## KEY_LOGIC_PATTERNS
- カーソル管理: 状態に応じたカーソル変更
- イベント処理: イベントに基づいたカーソル更新
- エラーハンドリング: Tkinterウィジェット取得失敗時のエラー処理

## CRITICAL_BEHAVIORS
- カーソル更新の正確性
- 状態とカーソルの整合性
- エラー発生時の適切なログ出力

==============================
# MODULE_INFO:
debug_logger.py

## MODULE_PURPOSE
デバッグ用のログ出力を管理するクラス

## CLASS_DEFINITION:
名前: DebugLogger
役割:
- ログの出力処理を行う
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
self.debug_enabled: bool - デバッグログ出力を有効にするかどうか
self.start_time: float - ログ出力開始時刻
self.project_root: str - プロジェクトルートディレクトリのパス

## METHOD_SIGNATURES
def __init__(self, debug_enabled: bool = True) -> None
機能: コンストラクタ。クラスの初期化、ログ出力開始時刻の記録、プロジェクトルートディレクトリのパスを取得

def log(self, level: LogLevel, message: str, context: Optional[Dict[str, Any]] = None, force: bool = False) -> None
機能: ログを出力する（外部呼び出し用）

def _log_internal(self, level: LogLevel, message: str, context: Optional[Dict[str, Any]] = None, force: bool = False, stacklevel: int = 3) -> None
機能: ログ出力の内部実装

def _get_caller_info(self, stacklevel: int) -> Tuple[str, str, int]
機能: 呼び出し元の情報を取得する

def _get_color(self, level: LogLevel) -> str
機能: ログレベルに応じた色を取得する

def _get_project_root(self) -> str
機能: プロジェクトルートのパスを取得する

def _format_context(self, context: Dict[str, Any]) -> str
機能: コンテキスト情報を整形する

## CORE_EXECUTION_FLOW
__init__ -> log -> _log_internal -> _get_caller_info, _get_color, _get_project_root, _format_context

## KEY_LOGIC_PATTERNS
- ログ出力: レベルに応じたログ出力
- コンテキスト管理: ログにコンテキスト情報を付加
- エラーハンドリング: ログ出力失敗時のエラー処理

## CRITICAL_BEHAVIORS
- ログの正確性と詳細さ
- ログレベルに応じた適切な出力
- パス解決の正確性

==============================
# MODULE_INFO:
enums.py

## MODULE_PURPOSE
Enum (列挙型) の定義

## CLASS_DEFINITION:
名前: ZoomState
役割: ズームセレクタの状態を定義するEnum
親クラス: enum.Enum

名前: LogLevel
役割: ログレベルを定義するEnum
親クラス: enum.Enum

## DEPENDENCIES
enum.Enum, enum.auto

## CLASS_ATTRIBUTES
ZoomState:
- NO_RECT: 矩形がない、または確定済み
- CREATE: 矩形を作成中 (ドラッグ中)
- EDIT: 矩形を編集中
- ON_MOVE: 矩形を移動中
- RESIZING: 矩形をリサイズ中
- ROTATING: 矩形を回転中

LogLevel:
- INIT: 初期化処理
- CALL: メソッド呼出し元
- DEBUG: デバッグ
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
- Enumによる状態とレベルの定義

## CRITICAL_BEHAVIORS
- 状態とレベルの正確な表現

==============================
# MODULE_INFO:
event_handler_core.py

## MODULE_PURPOSE
マウス/キーボードイベントを処理し、適切な操作に変換するクラス

## CLASS_DEFINITION:
名前: EventHandler
役割:
- matplotlib のイベントを処理し、各コンポーネントに指示を出す
- イベントの種類と現在の状態に応じて、具体的な処理を行うクラスに処理を委譲する（振り分ける）
親クラス: なし

## DEPENDENCIES
matplotlib.backend_bases.MouseEvent: マウスイベント
matplotlib.backend_bases.MouseButton: マウスボタン
matplotlib.backend_bases.KeyEvent: キーボードイベント
typing: 型ヒント
ui.zoom_function.enums.LogLevel: ログレベル定義
ui.zoom_function.enums.ZoomState: ズーム状態のEnum
ui.zoom_function.event_handlers_private.EventHandlersPrivate: イベント処理の実装詳細
ui.zoom_function.event_handlers_utils.EventHandlersUtils: ユーティリティ関数群
ui.zoom_function.cursor_manager.CursorManager: カーソル管理 (遅延インポート)
ui.zoom_function.debug_logger.DebugLogger: デバッグログ (遅延インポート)
ui.zoom_function.event_validator.EventValidator: イベント検証 (遅延インポート)
ui.zoom_function.rect_manager.RectManager: 矩形描画 (遅延インポート)
ui.zoom_function.zoom_selector.ZoomSelector: 矩形選択 (遅延インポート)
ui.zoom_function.zoom_state_handler.ZoomStateHandler: ズーム状態管理 (遅延インポート)

## CLASS_ATTRIBUTES
self.logger: DebugLogger - デバッグログ出力用ロガー
self.zoom_selector: ZoomSelector - ZoomSelectorインスタンス
self.state_handler: ZoomStateHandler - ZoomStateHandlerインスタンス
self.rect_manager: RectManager - RectManagerインスタンス
self.cursor_manager: CursorManager - CursorManagerインスタンス
self.validator: EventValidator - EventValidatorインスタンス
self.canvas: FigureCanvasTkAgg - matplotlibの描画領域
self.private_handlers: EventHandlersPrivate - イベント処理の実装詳細
self.utils: EventHandlersUtils - ユーティリティ関数群
_create_logged: bool - 矩形作成ログ出力フラグ
_move_logged: bool - 矩形移動ログ出力フラグ
_resize_logged: bool - 矩形リサイズログ出力フラグ
_rotate_logged: bool - 矩形回転ログ出力フラグ
_cid_press: Optional[int] - マウスボタン押下イベント接続ID
_cid_release: Optional[int] - マウスボタン解放イベント接続ID
_cid_motion: Optional[int] - マウス移動イベント接続ID
_cid_key_press: Optional[int] - キー押下イベント接続ID
_cid_key_release: Optional[int] - キー解放イベント接続ID
start_x: Optional[float] - 矩形作成開始時のX座標
start_y: Optional[float] - 矩形作成開始時のY座標
move_start_x: Optional[float] - 矩形移動開始時のマウスX座標
move_start_y: Optional[float] - 矩形移動開始時のマウスY座標
rect_start_pos: Optional[Tuple[float, float]] - 矩形移動開始時の矩形左下座標
resize_corner_index: Optional[int] - リサイズ中の角のインデックス
fixed_corner_pos: Optional[Tuple[float, float]] - リサイズ中の固定された対角の座標
_alt_pressed: bool - Altキーが押されているか
rotate_start_mouse_pos: Optional[Tuple[float, float]] - 回転開始時のマウス座標
rotate_center: Optional[Tuple[float, float]] - 回転中心座標
previous_vector_angle: Optional[float] - 前回のベクトル角度
edit_history: List[Optional[Dict[str, Any]]] - Undo用編集履歴
ROTATION_THRESHOLD: float - 回転時の振動を調整するための閾値
ROTATION_SENSITIVITY: float - 回転感度
ROTATION_THROTTLE_INTERVAL: float - 回転処理のスロットリング間隔
_last_rotation_update_time: float - 最後に回転処理を実行した時刻

## METHOD_SIGNATURES
def __init__(self, zoom_selector: 'ZoomSelector', state_handler: 'ZoomStateHandler', rect_manager: 'RectManager', cursor_manager: 'CursorManager', validator: 'EventValidator', logger: 'DebugLogger', canvas) -> None
機能: コンストラクタ。各コンポーネントのインスタンス化と初期化

def connect(self) -> None
機能: 全イベントハンドラを接続

def on_press(self, event: MouseEvent) -> None
機能: マウスボタン押下イベントのディスパッチャ

def on_motion(self, event: MouseEvent) -> None
機能: マウス移動イベントのディスパッチャ

def on_release(self, event: MouseEvent) -> None
機能: マウスボタン解放イベントのディスパッチャ

def on_key_press(self, event: KeyEvent) -> None
機能: キーボード押下イベントのディスパッチャ

def on_key_release(self, event: KeyEvent) -> None
機能: キーボード解放イベントのディスパッチャ

def reset_internal_state(self) -> None
機能: 全ての内部状態と編集履歴をリセット

def clear_edit_history(self) -> None
機能: 編集履歴をクリア

## CORE_EXECUTION_FLOW
__init__ -> connect -> 各種イベントハンドラ (on_press, on_motion, on_release, on_key_press, on_key_release)
必要に応じて reset_internal_state, clear_edit_history

## KEY_LOGIC_PATTERNS
- イベント駆動: マウス/キーボードイベントに基づく処理
- 状態管理: ズーム状態に応じた処理分岐
- 委譲: 具体的な処理をprivate_handlers, utilsに委譲
- Undo/Redo: 編集履歴によるUndo/Redo

## CRITICAL_BEHAVIORS
- イベント処理の正確性と応答性
- 状態遷移の整合性
- 内部状態のリセットと編集履歴の管理


==============================
# MODULE_INFO:
event_handlers_private.py

## MODULE_PURPOSE
EventHandler から呼び出され、具体的なマウス/キーボードイベント処理を行うクラス

## CLASS_DEFINITION:
名前: EventHandlersPrivate
役割:
- 矩形の作成、移動、リサイズ、回転などの具体的な操作を実行する
- EventHandler インスタンスを通じて、他のコンポーネントや状態にアクセスする
親クラス: なし

## DEPENDENCIES
matplotlib.backend_bases.MouseEvent: マウスイベント
matplotlib.backend_bases.MouseButton: マウスボタン
matplotlib.backend_bases.KeyEvent: キーボードイベント
typing: 型ヒント
ui.zoom_function.enums.LogLevel: ログレベル定義
ui.zoom_function.enums.ZoomState: ズーム状態のEnum
ui.zoom_function.event_handler_core.EventHandler: 親クラス (遅延インポート)

## CLASS_ATTRIBUTES
self.core: EventHandler - 親であるEventHandlerインスタンス

## METHOD_SIGNATURES
def __init__(self, core: 'EventHandler') -> None
機能: コンストラクタ。親であるEventHandlerインスタンスを設定

def handle_press_no_rect_left(self, event: MouseEvent) -> None
機能: NO_RECT状態で左クリックされた際の処理（矩形作成開始）

def handle_press_edit_left(self, event: MouseEvent) -> None
機能: EDIT状態で左クリックされた際の処理（矩形の移動またはリサイズ開始）

def handle_press_edit_right(self, event: MouseEvent) -> None
機能: EDIT状態で右クリックされた際の処理（矩形の回転開始）

def handle_motion_create(self, event: MouseEvent) -> None
機能: 矩形作成中のマウス移動処理（矩形の描画更新）

def handle_motion_move(self, event: MouseEvent) -> None
機能: 矩形移動中のマウス移動処理（矩形の移動更新）

def handle_motion_resize(self, event: MouseEvent) -> None
機能: 矩形リサイズ中のマウス移動処理（矩形のリサイズ更新）

def handle_motion_rotate(self, event: MouseEvent) -> None
機能: 矩形回転中のマウス移動処理（矩形の回転更新）

def handle_release_create(self, event: MouseEvent) -> None
機能: 矩形作成終了時の処理（矩形確定、状態遷移）

def handle_release_move(self, event: MouseEvent) -> None
機能: 矩形移動終了時の処理（状態遷移）

def handle_release_resize(self, event: MouseEvent) -> None
機能: 矩形リサイズ終了時の処理（状態遷移、編集履歴更新）

def handle_release_rotate(self, event: MouseEvent) -> None
機能: 矩形回転終了時の処理（状態遷移、編集履歴更新）

def handle_key_esc(self, event: KeyEvent) -> None
機能: Escキー押下時の処理（操作のキャンセルまたはUndo）

def handle_key_alt_press(self, event: KeyEvent) -> None
機能: Altキー押下時の処理（回転操作の補助）

def handle_key_alt_release(self, event: KeyEvent) -> None
機能: Altキー解放時の処理（回転操作の終了）

## CORE_EXECUTION_FLOW
__init__ -> 各種イベントハンドラ (handle_press_*, handle_motion_*, handle_release_*, handle_key_*)

## KEY_LOGIC_PATTERNS
- イベント処理: マウス/キーボードイベントに基づく処理
- 状態管理: ズーム状態に応じた処理分岐
- 矩形操作: 矩形の作成、移動、リサイズ、回転

## CRITICAL_BEHAVIORS
- 矩形操作の正確性と応答性
- 状態遷移の整合性
- 操作キャンセルとUndoの正確性

==============================
# MODULE_INFO:
event_handlers_utils.py

## MODULE_PURPOSE
EventHandler から呼び出され、補助的な機能を提供するクラス

## CLASS_DEFINITION:
名前: EventHandlersUtils
役割:
- 角度計算などの共通処理
- 編集履歴の管理 (Undo/Redo)
- 各種内部状態のリセット
親クラス: なし

## DEPENDENCIES
math: 角度計算
typing: 型ヒント
ui.zoom_function.enums.LogLevel: ログレベル定義
ui.zoom_function.enums.ZoomState: ズーム状態のEnum
ui.zoom_function.event_handler_core.EventHandler: 親クラス (遅延インポート)

## CLASS_ATTRIBUTES
self.core: EventHandler - 親であるEventHandlerインスタンス

## METHOD_SIGNATURES
def __init__(self, core: 'EventHandler') -> None
機能: コンストラクタ。親であるEventHandlerインスタンスを設定

def _calculate_angle(self, cx: float, cy: float, px: float, py: float) -> float
機能: 中心点から点へのベクトル角度を計算

def _normalize_angle_diff(self, angle1: float, angle2: float) -> float
機能: 角度の差分を-180から180度の範囲に正規化

def _throttle_rotation_update(self, current_time: float) -> bool
機能: 回転処理の実行間隔を制御

def push_edit_history(self, action: str, old_rect_data: Optional[Dict[str, Any]], new_rect_data: Dict[str, Any]) -> None
機能: 編集履歴を保存

def _undo_or_cancel_edit(self) -> None
機能: 編集操作をUndoまたはキャンセル

def reset_internal_state(self) -> None
機能: 全ての内部状態と編集履歴をリセット

def _reset_create_state(self) -> None
機能: 矩形作成関連の内部状態をリセット

def _reset_move_state(self) -> None
機能: 矩形移動関連の内部状態をリセット

def _reset_resize_state(self) -> None
機能: 矩形リサイズ関連の内部状態をリセット

def _reset_rotate_state(self) -> None
機能: 矩形回転関連の内部状態をリセット

def clear_edit_history(self) -> None
機能: 編集履歴をクリア

## CORE_EXECUTION_FLOW
__init__ -> 各種ユーティリティメソッド (_calculate_angle, _normalize_angle_diff, _throttle_rotation_update, push_edit_history, _undo_or_cancel_edit)
必要に応じて reset_internal_state とその関連メソッド

## KEY_LOGIC_PATTERNS
- 角度計算: ベクトル角度の計算と正規化
- 編集履歴: Undo/Redoのための編集履歴管理
- 状態リセット: 各操作状態のリセット

## CRITICAL_BEHAVIORS
- 角度計算の正確性
- 編集履歴の整合性と効率的な管理
- 内部状態のリセットの完全性

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
ui.zoom_function.rect_manager.RectManager: RectManager (未使用)

## CLASS_ATTRIBUTES
(特になし)

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


==============================
# MODULE_INFO:
rect_manager.py

## MODULE_PURPOSE
ズーム領域の矩形（Rectangle）を管理（作成、移動、リサイズ、回転）するクラス

## CLASS_DEFINITION:
名前: RectManager
役割:
- ズーム領域を作成する
- ズーム領域を移動する
- ズーム領域をリサイズする
- ズーム領域を回転する
親クラス: なし

## DEPENDENCIES
matplotlib.patches: 図形描画
matplotlib.transforms: 座標変換
matplotlib.axes: Axesオブジェクト
numpy: 数値計算
typing: 型ヒント
ui.zoom_function.debug_logger.DebugLogger: デバッグログ
ui.zoom_function.enums.LogLevel: ログレベル定義

## CLASS_ATTRIBUTES
self.rect: Optional[patches.Rectangle] - ズーム領域の矩形パッチ
self._angle: float - 矩形の回転角度（度数法）
self._last_valid_size_px: Optional[Tuple[float, float]] - 最後に有効だった矩形のピクセルサイズ
MIN_WIDTH_PX: int - 矩形の最小幅（ピクセル）
MIN_HEIGHT_PX: int - 矩形の最小高さ（ピクセル）
ASPECT_RATIO_W_H: float - 目標とするアスペクト比 (幅 / 高さ)

## METHOD_SIGNATURES
def __init__(self, ax: Axes, logger: DebugLogger) -> None
機能: コンストラクタ。Axesとロガーを設定

def draw_rect(self, x: float, y: float, width: float, height: float) -> None
機能: 矩形を描画する

def update_rect(self, x: float, y: float, width: float, height: float) -> None
機能: 矩形を更新する

def move_rect(self, dx: float, dy: float) -> None
機能: 矩形を移動する

def resize_rect(self, x: float, y: float, width: float, height: float) -> None
機能: 矩形をリサイズする

def rotate_rect(self, center_x: float, center_y: float, angle: float) -> None
機能: 矩形を回転する

def get_rect_props(self) -> Optional[Dict[str, Any]]
機能: 矩形のプロパティを取得する

def get_rect(self) -> Optional[patches.Rectangle]
機能: 矩形オブジェクトを取得する

def _check_pixel_size(self, x: float, y: float, width: float, height: float) -> Tuple[bool, float, float]
機能: 指定された矩形のピクセルサイズを計算し、有効性を判定する

## CORE_EXECUTION_FLOW
__init__ -> draw_rect, update_rect, move_rect, resize_rect, rotate_rect, get_rect_props, get_rect, _check_pixel_size

## KEY_LOGIC_PATTERNS
- 矩形操作: 矩形の作成、移動、リサイズ、回転
- 座標変換: データ座標とピクセル座標の変換
- アスペクト比維持: リサイズ時のアスペクト比維持

## CRITICAL_BEHAVIORS
- 矩形操作の正確性と効率性
- 座標変換の正確性
- アスペクト比維持の正確性

==============================
# MODULE_INFO:
zoom_selector.py

## MODULE_PURPOSE
ズーム領域の描画と編集を管理する主要クラス

## CLASS_DEFINITION:
名前: ZoomSelector
役割:
- マウス操作によるズーム領域の描画
- 描画したズーム領域の編集（リサイズ、回転）
- ズーム操作の状態管理
親クラス: なし

## DEPENDENCIES
matplotlib.transforms: 座標変換
matplotlib.patches: 図形描画
matplotlib.axes: Axesオブジェクト
numpy: 数値計算
typing: 型ヒント
ui.zoom_function.cursor_manager.CursorManager: カーソル管理
ui.zoom_function.debug_logger.DebugLogger: デバッグログ
ui.zoom_function.enums.LogLevel: ログレベル定義
ui.zoom_function.enums.ZoomState: ズーム状態のEnum
ui.zoom_function.event_handler_core.EventHandler: イベント処理
ui.zoom_function.event_validator.EventValidator: イベント検証
ui.zoom_function.rect_manager.RectManager: 矩形管理
ui.zoom_function.zoom_state_handler.ZoomStateHandler: ズーム状態管理

## CLASS_ATTRIBUTES
self.ax: Axes - MatplotlibのAxesオブジェクト
self.on_zoom_confirm: Callable - ズーム確定時に呼び出すコールバック関数
self.on_zoom_cancel: Callable - ズームキャンセル時に呼び出すコールバック関数
self.logger: DebugLogger - デバッグログ
self.state_handler: ZoomStateHandler - ズーム状態管理
self.rect_manager: RectManager - 矩形管理
self.validator: EventValidator - イベント検証
self.cursor_manager: CursorManager - カーソル管理
self.event_handler: EventHandler - イベント処理

## METHOD_SIGNATURES
def __init__(self, ax: Axes, on_zoom_confirm: Callable, on_zoom_cancel: Callable, logger: DebugLogger) -> None
機能: コンストラクタ。各コンポーネントの初期化と設定

def start_zoom(self) -> EventHandler
機能: ズーム操作を開始する

def confirm_zoom(self) -> None
機能: ズーム操作を確定する

def cancel_zoom(self) -> None
機能: ズーム操作をキャンセルする

def get_rect_props(self) -> Optional[dict]
機能: 矩形のプロパティを取得する

def pointer_near_corner(self, event) -> Optional[int]
機能: マウスポインタが矩形の角に近いかを判定する

def cursor_inside_rect(self, event) -> bool
機能: マウスポインタが矩形の内側にあるかを判定する

def _validate_event(self, event) -> bool
機能: イベントのバリデーション

def _validate_rect_properties(self, rect_props) -> bool
機能: 矩形プロパティのバリデーション

## CORE_EXECUTION_FLOW
__init__ -> start_zoom -> confirm_zoom, cancel_zoom, get_rect_props, pointer_near_corner, cursor_inside_rect, _validate_event, _validate_rect_properties

## KEY_LOGIC_PATTERNS
- ズーム操作: ズーム領域の描画、編集、確定、キャンセル
- イベント処理: マウスイベントの処理と検証
- 状態管理: ズーム操作の状態管理

## CRITICAL_BEHAVIORS
- ズーム操作の正確性と応答性
- イベント処理の正確性
- 状態管理の整合性

==============================
# MODULE_INFO:
zoom_state_handler.py

## MODULE_PURPOSE
ズーム操作の状態を管理するクラス

## CLASS_DEFINITION:
名前: ZoomStateHandler
役割:
- ズーム状態の保持と更新
- 状態変更の通知
親クラス: なし

## DEPENDENCIES
typing: 型ヒント
ui.zoom_function.debug_logger.DebugLogger: デバッグログ
ui.zoom_function.enums.LogLevel: ログレベル定義
ui.zoom_function.enums.ZoomState: ズーム状態のEnum

## CLASS_ATTRIBUTES
self._state: ZoomState - 現在のズーム状態
self.logger: DebugLogger - デバッグログ
self._event_handler: Optional[EventHandlerProtocol] - 状態変更イベントを処理するハンドラー
self._canvas: Optional[CanvasProtocol] - 画面描画を行うキャンバス

## METHOD_SIGNATURES
def __init__(self, initial_state: ZoomState, logger: DebugLogger, event_handler: Optional[EventHandlerProtocol] = None, canvas: Optional[CanvasProtocol] = None) -> None
機能: コンストラクタ。初期状態、ロガー、イベントハンドラー、キャンバスを設定

@property
def state(self) -> ZoomState
機能: 現在の状態を取得

def update_state(self, new_state: ZoomState, context: Optional[Dict[str, Any]] = None) -> None
機能: 状態を更新する

def _notify_state_change(self, old_state: ZoomState, new_state: ZoomState, context: Optional[Dict[str, Any]] = None) -> None
機能: 状態変更を通知する

## CORE_EXECUTION_FLOW
__init__ -> update_state -> _notify_state_change

## KEY_LOGIC_PATTERNS
- 状態管理: ズーム操作の状態遷移管理
- イベント通知: 状態変更を関係するコンポーネントに通知

## CRITICAL_BEHAVIORS
- 状態遷移の正確性と整合性
- 状態変更通知の正確性
