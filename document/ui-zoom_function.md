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
matplotlib.backend_bases.Event: MatplotlibのEvent
typing: 型ヒント
ui.zoom_function.debug_logger.DebugLogger: デバッグログ管理
ui.zoom_function.enums.LogLevel: ログレベル定義
ui.zoom_function.enums.ZoomState: ズーム状態のEnum
ui.zoom_function.event_validator.EventValidator: イベント検証
ui.zoom_function.zoom_selector.ZoomSelector: ズーム選択 (遅延インポート)

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
enum_rect.py

## MODULE_PURPOSE
Enum (列挙型) の定義

## CLASS_DEFINITION:
名前: ZoomState
役割: ズームセレクタの状態を定義するEnum
親クラス: enum.Enum

## DEPENDENCIES
enum.Enum: Enum型
enum.auto: 自動値割り当て

## CLASS_ATTRIBUTES
ZoomState:
- NO_RECT: 矩形がない、または確定済み
- CREATE: 矩形を作成中 (ドラッグ中)
- EDIT: 矩形を編集中
- ON_MOVE: 矩形を移動中
- RESIZING: 矩形をリサイズ中
- ROTATING: 矩形を回転中

## METHOD_SIGNATURES
(Enum クラスのため、特筆すべきメソッドはない)

## CORE_EXECUTION_FLOW
Enum定義のみ

## KEY_LOGIC_PATTERNS
- Enumによる状態の定義

## CRITICAL_BEHAVIORS
- 状態の正確な表現


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
typing: 型ヒント (Optional, TYPE_CHECKING, Tuple, List, Dict, Any)
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
self.config: Dict[str, Any] - config.json から読み込んだ設定データ
self.zoom_selector: ZoomSelector - ZoomSelectorインスタンス
self.state_handler: ZoomStateHandler - ZoomStateHandlerインスタンス
self.rect_manager: RectManager - RectManagerインスタンス
self.cursor_manager: CursorManager - CursorManagerインスタンス
self.validator: EventValidator - EventValidatorインスタンス
self.canvas: FigureCanvasTkAgg - matplotlibの描画領域
self.private_handlers: EventHandlersPrivate - イベント処理の実装詳細
self.utils: EventHandlersUtils - ユーティリティ関数群
self._create_logged: bool - 矩形作成ログ出力フラグ
self._move_logged: bool - 矩形移動ログ出力フラグ
self._resize_logged: bool - 矩形リサイズログ出力フラグ
self._rotate_logged: bool - 矩形回転ログ出力フラグ
self._cid_press: Optional[int] - マウスボタン押下イベント接続ID
self._cid_release: Optional[int] - マウスボタン解放イベント接続ID
self._cid_motion: Optional[int] - マウス移動イベント接続ID
self._cid_key_press: Optional[int] - キー押下イベント接続ID
self._cid_key_release: Optional[int] - キー解放イベント接続ID
self.start_x: Optional[float] - 矩形作成開始時のX座標 (データ座標)
self.start_y: Optional[float] - 矩形作成開始時のY座標 (データ座標)
self.move_start_x: Optional[float] - 矩形移動開始時のマウスX座標 (データ座標)
self.move_start_y: Optional[float] - 矩形移動開始時のマウスY座標 (データ座標)
self.rect_start_pos: Optional[Tuple[float, float]] - 矩形移動開始時の矩形左下座標 (データ座標)
self.resize_corner_index: Optional[int] - リサイズ中の角のインデックス (0-3)
self.fixed_corner_pos: Optional[Tuple[float, float]] - リサイズ中の固定された対角の座標 (データ座標)
self._alt_pressed: bool - Altキーが押されているか
self.rotate_start_mouse_pos: Optional[Tuple[float, float]] - 回転開始時のマウス座標 (データ座標)
self.rotate_center: Optional[Tuple[float, float]] - 回転中心座標 (データ座標)
self.previous_vector_angle: Optional[float] - 前回のベクトル角度 (度単位)
self.edit_history: List[Optional[Dict[str, Any]]] - Undo用編集履歴
self.rotation_threshold: float - 回転更新の閾値 (度、設定ファイルから読み込み)
self.rotation_sensitivity: float - 回転感度係数 (設定ファイルから読み込み)
self.rotation_throttle_interval: float - 回転処理のスロットリング間隔 (秒、設定ファイルから読み込み)
self._last_rotation_update_time: float - 最後に回転処理を実行した時刻 (タイムスタンプ)

## METHOD_SIGNATURES
def __init__(self, zoom_selector: 'ZoomSelector', state_handler: 'ZoomStateHandler', rect_manager: 'RectManager', cursor_manager: 'CursorManager', validator: 'EventValidator', logger: 'DebugLogger', canvas, config: Dict[str, Any]) -> None
機能: コンストラクタ。各コンポーネントのインスタンス化と初期化、設定データの読み込みとバリデーションを行う。

def connect(self) -> None
機能: 全イベントハンドラをmatplotlibのキャンバスイベントと接続する。

def on_press(self, event: MouseEvent) -> None
機能: マウスボタン押下イベントのディスパッチャ。イベント検証後、現在の状態とボタンに応じて適切なハンドラメソッドを呼び出す。

def on_motion(self, event: MouseEvent) -> None
機能: マウス移動イベントのディスパッチャ。イベント検証後、現在の状態に応じて適切なハンドラメソッドを呼び出す。

def on_release(self, event: MouseEvent) -> None
機能: マウスボタン解放イベントのディスパッチャ。イベント検証後、現在の状態に応じて適切なハンドラメソッドを呼び出す。操作終了後の状態遷移、キャッシュ無効化、カーソル更新、キャンバス再描画を行う。

def on_key_press(self, event: KeyEvent) -> None
機能: キーボード押下イベントのディスパッチャ。キーに応じて適切なハンドラメソッドを呼び出す。Altキー押下時はカーソルを更新する。

def on_key_release(self, event: KeyEvent) -> None
機能: キーボード解放イベントのディスパッチャ。キーに応じて適切なハンドラメソッドを呼び出す。Altキー解放時はカーソルを更新する。

def reset_internal_state(self) -> None
機能: 全ての内部状態と編集履歴をリセットする。Utilsクラスに処理を委譲する。

def clear_edit_history(self) -> None
機能: 編集履歴をクリアする。Utilsクラスに処理を委譲する。

## CORE_EXECUTION_FLOW
__init__ (config読み込み, バリデーション含む) -> connect (イベント接続)
イベント発生 (on_press, on_motion, on_release, on_key_press, on_key_release) -> validator.validate_event (検証) -> 状態に応じた private_handlers のメソッド呼び出し
操作終了 (on_releaseなど) -> state_handler.update_state (状態更新) -> zoom_selector.invalidate_rect_cache (キャッシュ無効化) -> cursor_manager.cursor_update (カーソル更新) -> canvas.draw_idle (再描画)
Escキー押下 -> private_handlers._handle_key_escape (Undoまたはキャンセル)
Altキー押下/解放 -> private_handlers.handle_key_alt_press/release, cursor_manager.cursor_update, canvas.draw_idle
reset_internal_state -> utils.reset_internal_state
clear_edit_history -> utils.clear_edit_history

## KEY_LOGIC_PATTERNS
- イベント駆動: マウス/キーボードイベントに基づく処理
- 状態管理: ズーム状態に応じた処理分岐
- 委譲: 具体的な処理をprivate_handlers, utilsに委譲
- Undo/Redo: 編集履歴によるUndo/Redo (Utilsが管理)
- 設定ファイルからの読み込み: 回転関連パラメータをconfigから読み込み
- イベント検証: EventValidatorによるイベントの事前検証

## CRITICAL_BEHAVIORS
- イベント処理の正確性と応答性
- 状態遷移の整合性
- 内部状態のリセットと編集履歴の管理の正確性
- 設定パラメータの読み込みとバリデーション
- Altキーによる回転操作のハンドリング
- 操作終了時の後処理 (状態更新、再描画など)


==============================
# MODULE_INFO:
event_handlers_private.py

## MODULE_PURPOSE
EventHandler から呼び出され、具体的なマウス/キーボードイベント処理を行うクラス

## CLASS_DEFINITION:
名前: EventHandlersPrivate
役割:
- 矩形の作成、移動、リサイズ、回転などの具体的な操作を実行する。
- EventHandler インスタンスを通じて、他のコンポーネントや状態にアクセスする。
親クラス: なし

## DEPENDENCIES
matplotlib.backend_bases.MouseEvent: マウスイベント
matplotlib.backend_bases.MouseButton: マウスボタン
matplotlib.backend_bases.KeyEvent: キーボードイベント
typing: 型ヒント (Optional, TYPE_CHECKING, Tuple, List, Dict, Any)
ui.zoom_function.enums.LogLevel: ログレベル定義
ui.zoom_function.enums.ZoomState: ズーム状態のEnum
ui.zoom_function.event_handler_core.EventHandler: 親クラス (遅延インポート、型ヒント用)

## CLASS_ATTRIBUTES
self.core: EventHandler - 親であるEventHandlerインスタンス

## METHOD_SIGNATURES
def __init__(self, core: 'EventHandler') -> None
機能: コンストラクタ。親であるEventHandlerインスタンスを設定する。

def handle_press_no_rect_left(self, event: MouseEvent) -> None
機能: NO_RECT 状態で左クリックされた際の処理。矩形作成状態に移行し、矩形を初期化、始点を記録する。

def dispatch_press_edit_left(self, event: MouseEvent) -> None
機能: EDIT 状態で左クリックされた際の処理。Altキーの状態とクリック位置に応じて、回転、リサイズ、または移動の開始処理を分岐する。

def _handle_press_edit_start_rotating(self, event: MouseEvent, corner_index: int) -> None
機能: EDIT 状態 + Alt + 角で左クリックされた際の処理。回転の中心点と開始角度を計算し、回転状態に移行する。編集履歴を保存する。

def _handle_press_edit_start_resizing(self, event: MouseEvent, corner_index: int) -> None
機能: EDIT 状態 + 角で左クリックされた際の処理。リサイズの固定点を設定し、リサイズ状態に移行する。矩形のエッジスタイルを変更し、編集履歴を保存する。

def _handle_press_edit_start_moving(self, event: MouseEvent) -> None
機能: EDIT 状態 + 内部で左クリックされた際の処理。矩形の移動開始点を記録し、移動状態に移行する。矩形のエッジスタイルを変更し、編集履歴を保存する。

def handle_press_edit_right_confirm(self, event: MouseEvent) -> None
機能: EDIT 状態で右クリックされた際の処理。ズーム選択を確定し、状態をNO_RECTに戻す。

def handle_motion_create(self, event: MouseEvent) -> None
機能: CREATE 状態でのマウス移動処理。開始点と現在のマウス位置から矩形のサイズを更新し、描画を更新する。

def handle_motion_edit(self, event: MouseEvent) -> None
機能: EDIT 状態でのマウス移動処理。マウスの位置に応じてカーソルを更新する。

def handle_motion_move(self, event: MouseEvent) -> None
機能: ON_MOVE 状態でのマウス移動処理。移動開始点からの相対距離に応じて矩形を移動し、描画を更新する。

def handle_motion_resizing(self, event: MouseEvent) -> None
機能: RESIZING 状態でのマウス移動処理。固定点と現在のマウス位置から矩形をリサイズし、描画を更新する。

def handle_motion_rotating(self, event: MouseEvent) -> None
機能: ROTATING 状態でのマウス移動処理。回転中心とマウスの移動から回転角度を計算し、矩形を回転する（スロットリングなし）。

def handle_release_create(self, event: MouseEvent, is_outside: bool) -> ZoomState
機能: CREATE 状態でのマウス解放処理。軸外でのリリースまたは有効なサイズでのリリースに応じて、作成完了またはキャンセル処理を行う。次の状態を返す。

def handle_release_move(self, event: MouseEvent) -> ZoomState
機能: ON_MOVE 状態でのマウス解放処理。矩形の移動を確定し、状態を更新する。次の状態を返す。

def handle_release_resizing(self, event: MouseEvent) -> ZoomState
機能: RESIZING 状態でのマウス解放処理。矩形のリサイズを確定、または無効なリサイズの場合Undoを実行し、状態を更新する。次の状態を返す。

def handle_release_rotating(self, event: MouseEvent) -> ZoomState
機能: ROTATING 状態でのマウス解放処理。矩形の回転を確定し、状態を更新する。次の状態を返す。

def _handle_key_escape(self, event: KeyEvent) -> None
機能: Escapeキー押下処理。現在の状態に応じて、ズーム確定キャンセル、Undo、または編集キャンセル処理を行う。

def handle_key_alt_press(self, event: KeyEvent) -> None
機能: Altキー押下処理。Altキーの状態を管理する。

def handle_key_alt_release(self, event: KeyEvent) -> None
機能: Altキー解放処理。Altキーの状態を管理する。

## CORE_EXECUTION_FLOW
__init__ -> EventHandlerからのイベントハンドラ呼び出し (handle_press_*, handle_motion_*, handle_release_*, handle_key_*) -> coreインスタンスを通じて他のコンポーネント (utils._add_history, state_handler.update_state, rect_manager.setup_rect, zoom_selector.invalidate_rect_cache, cursor_manager.cursor_update, rect_manager.edge_change_editing/finishing, rect_manager.move_rect_to, rect_manager.resize_rect_from_corners, rect_manager.set_rotation, rect_manager._temporary_creation, rect_manager.delete_rect, utils._undo_last_edit, utils._reset_*_state, utils._undo_or_cancel_edit) を操作

## KEY_LOGIC_PATTERNS
- イベント処理: マウス/キーボードイベントに基づく具体的な操作の実行
- 状態に応じた処理分岐: 現在のズーム状態に基づいた操作の実行
- 矩形操作: 矩形の作成、移動、リサイズ、回転の各ロジック実装
- 親クラスへのアクセス: `self.core` を通じた他のコンポーネントの状態やメソッドへのアクセス
- 編集履歴の連携: 操作開始時に履歴を保存、操作終了時やキャンセル時に履歴を操作

## CRITICAL_BEHAVIORS
- 各ズーム操作（作成、移動、リサイズ、回転）の正確な実行ロジック
- 操作開始・終了時の状態遷移と他のコンポーネントへの適切な指示
- 無効な操作やキャンセル時の正確な状態復帰またはリセット
- 編集履歴への操作の正確な記録とUndo/Redoへの対応
- Altキーとマウス操作の組み合わせによる回転処理のハンドリング


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

def _add_history(self, state: Optional[Dict[str, Any]]) -> None
機能: 編集履歴に状態を追加

def _remove_last_history(self) -> Optional[Dict[str, Any]]
機能: 最後の履歴を削除し、削除された状態情報を返す

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
__init__ -> 各種ユーティリティメソッド (_calculate_angle, _normalize_angle_diff, _add_history, _remove_last_history, _undo_or_cancel_edit)
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
rect_manager.py

## MODULE_PURPOSE
ズーム領域の矩形（Rectangle）を管理するクラス
- ズーム領域を作成、移動、リサイズ、回転を実装

## CLASS_DEFINITION:
名前: RectManager
役割:
- ズーム領域の矩形パッチを作成、更新、削除
- 矩形のジオメトリ計算（アスペクト比維持、ピクセルサイズチェック）
- 矩形の回転変換処理
親クラス: なし

## DEPENDENCIES
matplotlib.patches: 図形描画
matplotlib.transforms: 座標変換
matplotlib.axes.Axes: Axesオブジェクト
numpy: 数値計算
typing: 型ヒント
ui.zoom_function.debug_logger.DebugLogger: デバッグログ管理
ui.zoom_function.enums.LogLevel: ログレベル定義

## CLASS_ATTRIBUTES
self.ax: Axes - 矩形を描画するAxesオブジェクト
self.rect: Optional[patches.Rectangle] - ズーム領域の矩形パッチ
self._angle: float - 矩形の回転角度（度数法）
self.min_width_px: float - 最小幅（ピクセル）
self.min_height_px: float - 最小高さ（ピクセル）
self.aspect_ratio_w_h: float - アスペクト比（幅/高さ）
self._last_valid_size_px: Optional[Tuple[float, float]] - 最後に有効だったサイズ

## METHOD_SIGNATURES
def __init__(self, ax: Axes, logger: DebugLogger, config: Dict[str, Any]) -> None
機能: コンストラクタ。設定値の初期化、ログ設定

def setup_rect(self, x: float, y: float) -> None
機能: 初期のズーム領域を作成

def _calculate_rect_geometry(self, ref_x: float, ref_y: float, target_x: float, target_y: float) -> Tuple[float, float, float, float]
機能: 基準点と目標点から矩形のジオメトリを計算

def setting_rect_size(self, start_x: float, start_y: float, current_x: float, current_y: float) -> None
機能: ズーム領域のサイズと位置を更新（作成中）

def resize_rect_from_corners(self, fixed_x_rotated: float, fixed_y_rotated: float, current_x: float, current_y: float) -> None
機能: 固定された回転後の角と現在のマウス位置から矩形をリサイズ

def move_rect_to(self, new_x: float, new_y: float) -> None
機能: 矩形を指定された座標に移動

def set_rotation(self, angle: float) -> None
機能: 矩形を指定された角度で回転

def is_valid_size_in_pixels(self, width_px: float, height_px: float) -> bool
機能: 矩形のピクセルサイズが有効かを検証

def _check_pixel_size(self, x: float, y: float, width: float, height: float) -> Tuple[bool, float, float]
機能: 矩形のピクセルサイズを計算し、有効性を判定

def _temporary_creation(self, start_x: float, start_y: float, end_x: float, end_y: float) -> bool
機能: ズーム領域作成完了時の処理（ピクセルサイズチェックあり）

def delete_rect(self) -> None
機能: ズーム領域を削除

def get_properties(self) -> Optional[Tuple[float, float, float, float]]
機能: ズーム領域のプロパティ（x, y, width, height）を取得

def get_state(self) -> Optional[Dict[str, Any]]
機能: 現在の状態（Undo用）を取得

def set_state(self, state: Optional[Dict[str, Any]]) -> None
機能: 指定された状態に矩形を復元（Undo/Redo用）

def get_center(self) -> Optional[Tuple[float, float]]
機能: ズーム領域の中心座標を取得

def get_rotated_corners(self) -> Optional[list[Tuple[float, float]]]
機能: 回転後の四隅の絶対座標を取得

def get_rotation(self) -> float
機能: 現在の回転角度を取得

def get_patch(self) -> Optional[patches.Rectangle]
機能: ズーム領域パッチオブジェクトを取得

## CORE_EXECUTION_FLOW
__init__ -> setup_rect -> _calculate_rect_geometry -> setting_rect_size, resize_rect_from_corners, move_rect_to, set_rotation -> _check_pixel_size, is_valid_size_in_pixels

## KEY_LOGIC_PATTERNS
- 矩形ジオメトリ計算: アスペクト比維持、ピクセルサイズチェック
- 回転変換: 座標変換と矩形更新
- サイズ制限: 最小サイズチェックと無効サイズの処理
- Undo/Redo: 状態の保存と復元

## CRITICAL_BEHAVIORS
- 矩形ジオメトリ計算の正確性
- 回転変換の正確な適用
- サイズ制限の正確な適用
- Undo/Redo 機能の正確性


==============================
# MODULE_INFO:
zoom_selector.py

## MODULE_PURPOSE
ズーム領域の描画と編集を管理する主要クラス

## CLASS_DEFINITION:
名前: ZoomSelector
役割:
- ズーム操作に必要な各コンポーネント（状態ハンドラ、矩形マネージャ、カーソルマネージャ、イベントハンドラ）を初期化・管理する。
- マウス操作によるズーム領域の描画、編集（リサイズ、回転）をイベントハンドラに委譲して実現する。
- ズーム確定時とキャンセル時の外部コールバック関数を管理・呼び出す。
- マウスカーソルが矩形の角や内部に近いかの判定を行う。
親クラス: なし

## DEPENDENCIES
matplotlib.transforms: 座標変換
matplotlib.patches: 図形描画
matplotlib.axes: Axesオブジェクト
numpy: 数値計算
typing: 型ヒント (Callable, Optional, Tuple, Dict, Any)
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
self.canvas: FigureCanvasTkAgg - Matplotlibの描画領域キャンバス
self.on_zoom_confirm: Callable - ズーム確定時に呼び出すコールバック関数
self.on_zoom_cancel: Callable - ズームキャンセル時に呼び出すコールバック関数
self.logger: DebugLogger - デバッグログ出力用ロガー
self.config: Dict[str, Any] - 設定データを含む辞書 (コンストラクタ引数に追加されている)
self.state_handler: ZoomStateHandler - ズーム操作の状態を管理するZoomStateHandlerインスタンス
self.rect_manager: RectManager - ズーム領域の矩形描画と変形を管理するRectManagerインスタンス
self.cursor_manager: CursorManager - カーソルの表示を管理するCursorManagerインスタンス
self.validator: EventValidator - イベントの検証を行うEventValidatorインスタンス
self.event_handler: EventHandler - マウス/キーボードイベントを処理するEventHandlerインスタンス
self._cached_rect_patch: Optional[patches.Rectangle] - 最後に描画された矩形パッチのキャッシュ
self._last_cursor_inside_state: Optional[bool] - 最後に記録されたカーソルが矩形内にあるかの状態

## METHOD_SIGNATURES
def __init__(self, ax: Axes, on_zoom_confirm: Callable[[float, float, float, float, float], None], on_zoom_cancel: Callable[[], None], logger: DebugLogger, config: Dict[str, Any]) -> None
機能: コンストラクタ。Axes、コールバック関数、ロガー、設定データを受け取り、各コンポーネントの初期化と設定、イベント接続を行う。

def _initialize_components(self, ax: Axes, logger: DebugLogger) -> None
機能: 各依存コンポーネント（状態ハンドラ、矩形マネージャ、カーソルマネージャ、イベントハンドラ、イベントバリデータ）のインスタンスを生成し、必要な設定を行う。

def _setup_callbacks(self, on_zoom_confirm: Callable, on_zoom_cancel: Callable) -> None
機能: ズーム確定時とキャンセル時に呼び出す外部コールバック関数をインスタンス変数に保持する。

def _initialize_state_handler(self) -> None
機能: ZoomStateHandlerのインスタンスを初期状態とロガー、キャンバス、EventHandlerとともに生成する。

def _initialize_rect_manager(self) -> None
機能: RectManagerのインスタンスをAxes、ロガー、設定データとともに生成する。

def _initialize_cursor_manager(self) -> None
機能: CursorManagerのインスタンスを自身(ZoomSelector)とロガーとともに生成する。

def _initialize_event_handler(self) -> None
機能: EventValidatorとEventHandlerのインスタンスを生成し、EventHandlerに他のコンポーネントと設定データを設定する。

def _connect_events(self) -> None
機能: EventHandlerの `connect` メソッドを呼び出し、Matplotlibイベントとの接続を開始する。デフォルトカーソルを設定する。

def cursor_inside_rect(self, event) -> bool
機能: マウスカーソル位置が現在のズーム領域内にあるか（表示されている矩形パッチに対して）を判定する。キャッシュを活用する。

def _has_valid_rect_cache(self) -> bool
機能: 矩形パッチのキャッシュが有効かを確認し、必要に応じて更新をトリガーする。

def _update_rect_cache(self) -> None
機能: RectManagerから最新の矩形パッチを取得し、内部キャッシュを更新する。

def confirm_zoom(self) -> None
機能: 現在のズーム領域のプロパティを取得し、設定されているズーム確定コールバック関数 (`self.on_zoom_confirm`) を呼び出して結果を通知する。その後、関連する内部状態と矩形をクリーンアップする。

def _validate_rect_properties(self, rect_props) -> bool
機能: 矩形プロパティ（特に幅と高さ）が有効かどうかを検証する内部ヘルパーメソッド。

def _handle_zoom_confirmation(self, x, y, w, h, rotation_angle) -> None
機能: ズーム確定コールバックの呼び出しと、確定後のクリーンアップ処理を実行する。

def _cleanup_after_zoom(self) -> None
機能: ズーム確定後の共通クリーンアップ処理。矩形削除、キャッシュ無効化、カーソルリセット、EventHandler内部状態リセットを行う。

def cancel_zoom(self) -> None
機能: ズーム確定操作をキャンセルする。共通クリーンアップ処理を実行し、設定されているズームキャンセルコールバック関数 (`self.on_zoom_cancel`) を呼び出す。

def reset(self) -> None
機能: ZoomSelector全体の状態を初期状態に戻す。共通クリーンアップ処理と、状態ハンドラ、EventHandlerの内部状態リセットを行う。

def _cleanup_zoom(self) -> None
機能: ズーム確定/キャンセル時の共通クリーンアップ処理。編集履歴クリア、矩形削除、キャッシュ無効化を行う。

def invalidate_rect_cache(self) -> None
機能: ズーム領域の矩形パッチキャッシュを無効化する。

def pointer_near_corner(self, event) -> Optional[int]
機能: マウスカーソルが矩形の角（回転後の座標系で、ピクセル単位の許容範囲内）に近いかを判定する。近い角のインデックスを返す。

def _validate_event(self, event) -> bool
機能: イベントが処理に必要な基本的な情報（Axes内、座標など）を持っているかを検証する内部ヘルパーメソッド。EventValidatorを使用する。

## CORE_EXECUTION_FLOW
__init__ (config受け取り含む) -> _initialize_components (_initialize_state_handler, _initialize_rect_manager, _initialize_cursor_manager, _initialize_event_handler (EventValidator含む)) -> _setup_callbacks -> _connect_events (event_handler.connect(), cursor_manager.set_default_cursor())
外部からのズーム確定要求 (例: EventHandlerからの confirm_zoom 呼び出し) -> confirm_zoom -> _handle_zoom_confirmation (on_zoom_confirm コールバック呼び出し) -> _cleanup_after_zoom (_cleanup_zoom, cursor_manager.set_default_cursor(), event_handler.reset_internal_state())
外部からのズームキャンセル要求 (例: EventHandlerからの cancel_zoom 呼び出し) -> cancel_zoom -> _cleanup_zoom -> on_zoom_cancel コールバック呼び出し -> cursor_manager.set_default_cursor()
外部からのリセット要求 (例: FractalCanvasからの reset 呼び出し) -> reset -> _cleanup_zoom -> state_handler.update_state -> event_handler.reset_internal_state -> cursor_manager.set_default_cursor()
イベント発生 (event_handlerが処理) -> event_handler から pointer_near_corner, cursor_inside_rect, invalidate_rect_cache などの呼び出し
pointer_near_corner -> rect_manager.get_rotated_corners, rect_manager.get_properties, ax.transData.transform, _validate_event, _validate_rect_properties
cursor_inside_rect -> _has_valid_rect_cache -> _update_rect_cache -> rect_manager.get_patch, rect_patch.contains(event)

## KEY_LOGIC_PATTERNS
- コンポーネント統合: ズーム操作関連の複数のクラス（State, Rect, Cursor, Event）をまとめて管理・連携させる
- イベント駆動処理の委譲: イベント処理の詳細はEventHandlerに任せる
- コールバック管理: 外部（MainWindowなど）からのズーム確定・キャンセルコールバックの管理と呼び出し
- 状態管理の連携: StateHandlerを通じたズーム状態の更新と追跡
- 矩形管理の連携: RectManagerを通じた矩形の描画、更新、プロパティ取得
- カーソル管理の連携: CursorManagerを通じたカーソル形状の制御
- 座標計算と判定: 矩形に対するマウス位置の判定（角に近いか、内部か）
- キャッシュ管理: 矩形パッチの参照をキャッシュし、必要に応じて更新/無効化する
- クリーンアップ処理: ズーム操作終了後やリセット時の状態とリソースの後処理
- 設定データの受け渡し: コンストラクタで受け取ったconfigを子コンポーネントに渡す

## CRITICAL_BEHAVIORS
- 各コンポーネントが正しく初期化され、相互に連携すること
- マウス操作（作成、移動、リサイズ、回転）がイベントハンドラを通じて正確に実行されること
- ズーム確定/キャンセル時に適切な外部コールバック関数が正確なパラメータで呼び出されること
- 矩形パッチのキャッシュが正確に管理され、常に最新の状態を反映していること
- マウス位置に対する角判定および内部判定がピクセル座標系で正確に行われること
- ズーム操作終了後やリセット時に状態とリソースが適切にクリーンアップされること
- 設定データが各コンポーネントに正しく伝搬・利用されること


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
