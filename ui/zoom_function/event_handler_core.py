from matplotlib.backend_bases import MouseEvent, MouseButton, KeyEvent
from typing import Optional, TYPE_CHECKING, Tuple, List, Dict, Any
from debug import LogLevel
from .enum_rect import ZoomState
from .event_handlers_private import EventHandlersPrivate
from .event_handlers_utils import EventHandlersUtils

# 型ヒント用インポート (循環参照回避)
if TYPE_CHECKING:
    from .cursor_manager import CursorManager
    from ...debug.debug_logger import DebugLogger
    from .event_validator import EventValidator
    from .rect_manager import RectManager
    from .zoom_selector import ZoomSelector
    from .zoom_state_handler import ZoomStateHandler

class EventHandler:
    """マウス/キーボードイベントを処理し、適切な操作に変換するクラス
    - matplotlib のイベントを処理し、各コンポーネントに指示を出す
    - イベントの種類と現在の状態に応じて、具体的な処理を行うクラスに処理を委譲する（振り分ける）
    Attributes:
        logger: デバッグログ出力用ロガー
        zoom_selector: ZoomSelector インスタンス。矩形選択処理を管理する
        state_handler: ZoomStateHandler インスタンス。状態遷移を管理する
        rect_manager: RectManager インスタンス。矩形描画を管理する
        cursor_manager: CursorManager インスタンス。カーソル表示を管理する
        validator: EventValidator インスタンス。イベントの検証を行う
        canvas: FigureCanvasTkAgg インスタンス。matplotlibの描画領域
        private_handlers: EventHandlersPrivate インスタンス。イベント処理の実装詳細
        utils: EventHandlersUtils インスタンス。ユーティリティ関数群
        _create_logged: 矩形作成ログ出力フラグ
        _move_logged: 矩形移動ログ出力フラグ
        _resize_logged: 矩形リサイズログ出力フラグ
        _rotate_logged: 矩形回転ログ出力フラグ
        _cid_press: マウスボタン押下イベント接続ID
        _cid_release: マウスボタン解放イベント接続ID
        _cid_motion: マウス移動イベント接続ID
        _cid_key_press: キー押下イベント接続ID
        _cid_key_release: キー解放イベント接続ID
        start_x: 矩形作成開始時のX座標
        start_y: 矩形作成開始時のY座標
        move_start_x: 矩形移動開始時のマウスX座標
        move_start_y: 矩形移動開始時のマウスY座標
        rect_start_pos: 矩形移動開始時の矩形左下座標
        resize_corner_index: リサイズ中の角のインデックス
        fixed_corner_pos: リサイズ中の固定された対角の座標
        _alt_pressed: Altキーが押されているか
        rotate_start_mouse_pos: 回転開始時のマウス座標
        rotate_center: 回転中心座標
        previous_vector_angle: 前回のベクトル角度
        edit_history: Undo用編集履歴
        rotation_threshold (float): 回転更新の閾値 (度、設定ファイルから)
        rotation_sensitivity (float): 回転感度係数 (設定ファイルから)
        rotation_throttle_interval (float): 回転処理のスロットリング間隔 (秒、設定ファイルから)
    """

    def __init__(self,
                zoom_selector: 'ZoomSelector',
                state_handler: 'ZoomStateHandler',
                rect_manager: 'RectManager',
                cursor_manager: 'CursorManager',
                validator: 'EventValidator',
                logger: 'DebugLogger',
                canvas,
                config: Dict[str, Any] # 追加: config.json のデータ
                ):
        """イベントハンドラのコンストラクタ

        Args:
            zoom_selector: ZoomSelector インスタンス。矩形選択処理を管理する
            state_handler: ZoomStateHandler インスタンス。状態遷移を管理する
            rect_manager: RectManager インスタンス。矩形描画を管理する
            cursor_manager: CursorManager インスタンス。カーソル表示を管理する
            validator: EventValidator インスタンス。イベントの検証を行う
            logger: DebugLogger インスタンス。デバッグログ出力用
            canvas: FigureCanvasTkAgg インスタンス。matplotlibの描画領域
            config (Dict[str, Any]): config.json から読み込んだ設定データ
        """
        self.logger = logger
        self.config = config

        # 依存コンポーネント
        self.zoom_selector = zoom_selector
        self.state_handler = state_handler
        self.rect_manager = rect_manager
        self.cursor_manager = cursor_manager
        self.validator = validator
        self.canvas = canvas

        # 分割した他のクラスのインスタンスを作成
        self.logger.log(LogLevel.INIT, "EventHandlersPrivate クラスのインスタンスを作成")
        # private_handlers や utils にも config を渡すか、
        # またはこれらのクラス内で self.core.config を参照するようにする
        # ここでは self.core.config を参照する想定で、引数追加はしない
        self.private_handlers = EventHandlersPrivate(self)
        self.logger.log(LogLevel.INIT, "EventHandlersUtils クラスのインスタンスを作成")
        self.utils = EventHandlersUtils(self)

        # --- 設定ファイルから読み込む値 ---
        ui_settings = self.config.get("ui_settings", {})
        # フォールバック用のデフォルト値を設定
        default_rotation_threshold = 2.0
        default_rotation_sensitivity = 1.0
        default_rotation_throttle_interval = 1 / 60 # 約60fps

        # インスタンス変数として設定値を保存
        self.rotation_threshold = ui_settings.get("rotation_threshold", default_rotation_threshold)
        self.rotation_sensitivity = ui_settings.get("rotation_sensitivity", default_rotation_sensitivity)
        self.rotation_throttle_interval = ui_settings.get("rotation_throttle_interval", default_rotation_throttle_interval)

        # 値のバリデーション (例: sensitivity は 0より大きく1以下)
        if not (0 < self.rotation_sensitivity <= 1.0):
            self.logger.log(LogLevel.WARNING, f"設定ファイルの rotation_sensitivity ({self.rotation_sensitivity}) が無効です (0<value<=1.0)。デフォルト値 ({default_rotation_sensitivity}) を使用します。")
            self.rotation_sensitivity = default_rotation_sensitivity
        if self.rotation_throttle_interval < 0:
             self.logger.log(LogLevel.WARNING, f"設定ファイルの rotation_throttle_interval ({self.rotation_throttle_interval}) が無効です (<0)。デフォルト値 ({default_rotation_throttle_interval}) を使用します。")
             self.rotation_throttle_interval = default_rotation_throttle_interval
        # threshold は負の値も許容するかもしれないので、バリデーションは緩め

        self.logger.log(LogLevel.DEBUG, f"回転設定: threshold={self.rotation_threshold}, sensitivity={self.rotation_sensitivity}, interval={self.rotation_throttle_interval:.5f}")
        # --- 設定ファイル読み込みここまで ---

        # --- 内部状態 ---
        # ログ出力フラグ（プライベートハンドラや utils に移動しても良いが、ここではコアに残しておく）
        self._create_logged = False
        self._move_logged = False
        self._resize_logged = False
        self._rotate_logged = False

        # イベント接続ID
        self._cid_press: Optional[int] = None
        self._cid_release: Optional[int] = None
        self._cid_motion: Optional[int] = None
        self._cid_key_press: Optional[int] = None
        self._cid_key_release: Optional[int] = None

        # ドラッグ開始位置 (矩形作成用)
        self.start_x: Optional[float] = None
        self.start_y: Optional[float] = None

        # 矩形移動用
        self.move_start_x: Optional[float] = None # 移動開始時のマウスX座標
        self.move_start_y: Optional[float] = None # 移動開始時のマウスY座標
        self.rect_start_pos: Optional[Tuple[float, float]] = None # 移動開始時の矩形左下座標（x, y）

        # 矩形リサイズ用
        self.resize_corner_index: Optional[int] = None # リサイズ中の角のインデックス（0-3）
        self.fixed_corner_pos: Optional[Tuple[float, float]] = None # リサイズ中の固定された対角の座標

        # 矩形回転用
        self._alt_pressed: bool = False # Altキーが押されているか
        self.rotate_start_mouse_pos: Optional[Tuple[float, float]] = None # 回転開始時のマウス座標
        self.rotate_center: Optional[Tuple[float, float]] = None # 回転中心座標
        self.previous_vector_angle: Optional[float] = None # 前回のベクトル角度

        # スロットリング用タイムスタンプ (インスタンス変数に)
        self._last_rotation_update_time: float = 0.0

        # Undo 用の編集履歴（履歴自体はutilsで管理するが、リストの変数はコアに残しておく）
        self.edit_history: List[Optional[Dict[str, Any]]] = []
		# --- 内部状態ここまで ---

    def connect(self):
    # connect, on_press, on_motion, on_release, on_key_press, on_key_release は
    # 内部で self.rotation_threshold 等を直接参照していなければ変更不要
    # (実際の使用箇所は private_handlers や utils にあるため、そちらの修正が必要)
        """全イベントハンドラを接続
        - 各種matplotlibイベントと、対応するハンドラメソッドを接続する
        """
        if self._cid_press is None: # すでに接続されている場合は何もしない
            self._cid_press = self.canvas.mpl_connect('button_press_event', self.on_press)
            self._cid_motion = self.canvas.mpl_connect('motion_notify_event', self.on_motion)
            self._cid_release = self.canvas.mpl_connect('button_release_event', self.on_release)
            self._cid_key_press = self.canvas.mpl_connect('key_press_event', self.on_key_press)
            self._cid_key_release = self.canvas.mpl_connect('key_release_event', self.on_key_release)
            self.logger.log(LogLevel.SUCCESS, "イベントハンドラ接続完了")

    # --- イベント処理メソッド (ディスパッチャ) ---
    def on_press(self, event: MouseEvent) -> None:
        """マウスボタン押下イベントのディスパッチャ
        - イベントの検証を行い、状態に応じて適切なハンドラを呼び出す
        Args:
            event: MouseEvent オブジェクト。発生したイベントの情報を含む
        """
        validation_result = self.validator.validate_event(event, self.zoom_selector.ax)
        if not validation_result.is_press_valid:
            # self.logger.log(LogLevel.ERROR, "基本検証失敗：処理中断") # ログレベル調整 or コメントアウト
            return

        state = self.state_handler.state
        # self.logger.log(LogLevel.DEBUG, f"状態取得完了：{state.name}, ボタン={event.button}") # ログレベル調整

        if state == ZoomState.NO_RECT:
            if event.button == MouseButton.LEFT:
                self.private_handlers.handle_press_no_rect_left(event)
        elif state == ZoomState.EDIT:
            if event.button == MouseButton.LEFT:
                # private_handlers に処理を委譲
                self.private_handlers.dispatch_press_edit_left(event)
            elif event.button == MouseButton.RIGHT:
                 # private_handlers に処理を委譲
                self.private_handlers.handle_press_edit_right_confirm(event)

    def on_motion(self, event: MouseEvent) -> None:
        """マウス移動イベントのディスパッチャ
        - イベントの検証を行い、状態に応じて適切なハンドラを呼び出す
        Args:
            event: MouseEvent オブジェクト。発生したイベントの情報を含む
        """
        # 頻繁に呼ばれるので、バリデーション失敗時のログは出さない方が良いかも
        validation_result = self.validator.validate_event(event, self.zoom_selector.ax)
        if not (validation_result.is_in_axes and validation_result.has_coords):
            # self.logger.log(LogLevel.WARNING, "Axes外または座標無効のため処理中断") # コメントアウト推奨
            # Axes外でもカーソル形状をデフォルトに戻すなどの処理は必要かもしれない
            # self.cursor_manager.set_default_cursor() # 例
            return

        state = self.state_handler.state
        # self.logger.log(LogLevel.DEBUG, f"状態取得完了：{state.name}") # ログレベル調整

        # 各状態に応じた private_handlers のメソッド呼び出し
        if state == ZoomState.CREATE:
            if event.button == MouseButton.LEFT: # ドラッグ中かチェック
                self.private_handlers.handle_motion_create(event)
        elif state == ZoomState.EDIT:
             # EDIT状態でのマウス移動 (ホバー処理など)
            self.private_handlers.handle_motion_edit(event)
        elif state == ZoomState.ON_MOVE:
            if event.button == MouseButton.LEFT:
                self.private_handlers.handle_motion_move(event)
        elif state == ZoomState.RESIZING:
            if event.button == MouseButton.LEFT:
                self.private_handlers.handle_motion_resizing(event)
        elif state == ZoomState.ROTATING:
             # ROTATING 状態ではどのボタンが押されているかは気にしない (Altキー押下中)
             # if event.button == MouseButton.LEFT: # このチェックは不要かも
             # 回転処理 (内部で throttle や sensitivity が使われる)
             self.private_handlers.handle_motion_rotating(event)

    def on_release(self, event: MouseEvent) -> None:
        """マウスボタン解放イベントのディスパッチャ
        - イベントの検証を行い、状態に応じて適切なハンドラを呼び出す
        Args:
            event: MouseEvent オブジェクト。発生したイベントの情報を含む
        """
        # 軸外リリースでも処理が必要な場合があるのでバリデーションは緩める
        validation_result = self.validator.validate_event(event, self.zoom_selector.ax)
        # is_outside は validation_result から直接取得せず、event.xdata/ydata が None かどうかで判定する方が確実
        is_outside = event.xdata is None or event.ydata is None

        state = self.state_handler.state
        self.logger.log(LogLevel.DEBUG, f"状態取得完了：{state.name}, ボタン={event.button}, 軸外={is_outside}")


        operation_ended = False
        final_state_to_set = ZoomState.EDIT # デフォルトは操作完了後のEDIT状態

        # 各状態に応じた private_handlers のメソッド呼び出し
        if state == ZoomState.CREATE:
            if event.button == MouseButton.LEFT:
                final_state_to_set = self.private_handlers.handle_release_create(event, is_outside)
                operation_ended = True
        elif state == ZoomState.ON_MOVE:
            if event.button == MouseButton.LEFT:
                final_state_to_set = self.private_handlers.handle_release_move(event)
                operation_ended = True
        elif state == ZoomState.RESIZING:
            if event.button == MouseButton.LEFT:
                final_state_to_set = self.private_handlers.handle_release_resizing(event)
                operation_ended = True
        elif state == ZoomState.ROTATING:
            # 回転は Alt キー + マウス移動で行うので、ボタン解放は直接関係ないことが多い
            # ただし、回転中にクリックしてドラッグする操作を実装している場合は必要
            # ここでは handle_release_rotating があると仮定
            # if event.button == MouseButton.LEFT: # 必要に応じてボタンチェック
            final_state_to_set = self.private_handlers.handle_release_rotating(event)
            operation_ended = True

        if operation_ended: # 操作が終了した場合の共通後処理
            # 状態遷移
            self.state_handler.update_state(final_state_to_set, {"action": f"{state.name} 操作終了"})
            # キャッシュ無効化 (ZoomSelector 側にメソッドがあると仮定)
            if hasattr(self.zoom_selector, 'invalidate_rect_cache'):
                 self.zoom_selector.invalidate_rect_cache()
            else:
                 self.logger.log(LogLevel.WARNING, "ZoomSelector に invalidate_rect_cache メソッドがありません。")

            # カーソル更新 (イベントオブジェクトを渡す)
            # Altキーの状態も反映させる
            corner_index = self.zoom_selector.pointer_near_corner(event) # リリース時の位置で判定
            self.cursor_manager.cursor_update(event, state=final_state_to_set, near_corner_index=corner_index, is_rotating=self._alt_pressed)
            # キャンバス再描画
            self.canvas.draw_idle()

    def on_key_press(self, event: KeyEvent) -> None:
        """キーボード押下イベントのディスパッチャ
        - キー入力に応じて特定の処理を呼び出す
        Args:
            event: KeyEvent オブジェクト。発生したイベントの情報を含む
        """
        # self.logger.log(LogLevel.DEBUG, f"キー押下: {event.key}") # ログ追加
        if event.key == 'escape':
            # private_handlers に処理を委譲
            self.private_handlers._handle_key_escape(event)
        elif event.key == 'alt':
             # 矩形がない場合は何もしない
            if not self.rect_manager.get_rect(): return
             # private_handlers に処理を委譲
            self.private_handlers.handle_key_alt_press(event)
            # カーソル更新のために角にいるか判定
            corner_index = self.zoom_selector.pointer_near_corner(event)
            # 状態を直接変更せず、カーソル更新に is_rotating フラグを渡す
            # self.state_handler.update_state(ZoomState.ROTATING) # 状態変更はしない方が良いかも
            self.cursor_manager.cursor_update(event, state=self.state_handler.state, near_corner_index=corner_index, is_rotating=self._alt_pressed) # 現在の状態で is_rotating=True に
            self.canvas.draw_idle()

    def on_key_release(self, event: KeyEvent) -> None:
        """キーボード解放イベントのディスパッチャ
        - キー解放に応じて特定の処理を呼び出す
        Args:
            event: KeyEvent オブジェクト。発生したイベントの情報を含む
        """
        # self.logger.log(LogLevel.DEBUG, f"キー解放: {event.key}") # ログ追加
        if event.key == 'alt':
            # 矩形がない場合は何もしない
            if not self.rect_manager.get_rect(): return
             # private_handlers に処理を委譲
            self.private_handlers.handle_key_alt_release(event)
             # カーソル更新のために角にいるか判定
            corner_index = self.zoom_selector.pointer_near_corner(event)
            # 状態が ROTATING になっていたら EDIT に戻すなどの処理が必要かもしれない
            # if self.state_handler.state == ZoomState.ROTATING:
            #     self.state_handler.update_state(ZoomState.EDIT)
            # カーソルを更新 (is_rotating=False に)
            self.cursor_manager.cursor_update(event, state=self.state_handler.state, near_corner_index=corner_index, is_rotating=self._alt_pressed)
            self.canvas.draw_idle()
    # --- イベント処理メソッド (ディスパッチャ) ここまで ---

    # --- 状態リセットメソッド ---
    def reset_internal_state(self):
        """全ての内部状態と編集履歴をリセット
        - 内部状態を初期化し、編集履歴をクリアする
        """
        # EventHandler の公開メソッドとして残しておく
        # ただし、内部での具体的なリセット処理は utils に依頼する
        self.utils.reset_internal_state()
    # --- 状態リセットメソッド ここまで ---

    # --- Undo 関連メソッド ---
    def clear_edit_history(self):
        """編集履歴をクリア
        - 内部に保持している編集履歴を削除する
        """
        # EventHandler の公開メソッドとして残しておく
        # ただし、内部での具体的なクリア処理は utils に依頼する
        self.utils.clear_edit_history()
    # --- Undo 関連メソッド ここまで ---
