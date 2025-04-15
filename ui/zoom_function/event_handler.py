import math # 角度計算
import numpy as np # 角度の正規化で使用
from matplotlib.backend_bases import MouseEvent, MouseButton, KeyEvent
from typing import Optional, TYPE_CHECKING, Tuple, List, Dict, Any
from .enums import LogLevel, ZoomState

# 他のクラスの型ヒントのためにインポート (循環参照回避)
if TYPE_CHECKING:
    from .zoom_selector import ZoomSelector
    from .zoom_state_handler import ZoomStateHandler
    from .rect_manager import RectManager
    from .cursor_manager import CursorManager
    from .event_validator import EventValidator
    from .debug_logger import DebugLogger

class EventHandler:
    """ matplotlib のイベントを処理し、各コンポーネントに指示を出すクラス """
    # --- ズーム領域回転時の振動を調整するためのパラメータ ---
    # この値以下の角度変化（度単位）は無視して更新しない
    ROTATION_THRESHOLD = 2.6  # 例: 0.1度。大きくすると鈍感になるが、カクつく可能性もある
    # 角度変化の感度係数 (0.0 < 値 <= 1.0)。1.0で変更なし。小さくすると鈍くなる
    ROTATION_SENSITIVITY = 1.3 # 例: 0.8。値を小さくすると滑らかになるが、追従性が落ちる
    # --- パラメータここまで ---
    # --- スロットリングの設定 ---
    ROTATION_THROTTLE_INTERVAL = 1 / 60  # 秒 (60fps相当に制限)
    _last_rotation_update_time = 0 # 最後に回転処理を実行した時刻
    # --- スロットリングここまで ---

    def __init__(self,
                 zoom_selector: 'ZoomSelector',
                 state_handler: 'ZoomStateHandler',
                 rect_manager: 'RectManager',
                 cursor_manager: 'CursorManager',
                 validator: 'EventValidator',
                 logger: 'DebugLogger',
                 canvas):
        self.logger = logger
        self.logger.log(LogLevel.INIT, "EventHandler")
        # --- 依存コンポーネント ---
        self.zoom_selector = zoom_selector
        self.state_handler = state_handler
        self.rect_manager = rect_manager
        self.cursor_manager = cursor_manager
        self.validator = validator
        self.canvas = canvas
		# --- 内部状態 ---
        # ログ出力フラグ
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
        # --- Undo 用の編集履歴 ---
        self.edit_history: List[Optional[Dict[str, Any]]] = [] # 矩形の状態を保存するリスト
		# --- 内部状態ここまで ---

    # --- イベント接続/切断 ---
    def connect(self):
        """ イベントハンドラを接続 """
        if self._cid_press is None: # すでに接続されている場合は何もしない
            self.logger.log(LogLevel.CALL, "接続開始：全イベントハンドラ")
            self._cid_press = self.canvas.mpl_connect('button_press_event', self.on_press)
            self._cid_release = self.canvas.mpl_connect('button_release_event', self.on_release)
            self._cid_key_press = self.canvas.mpl_connect('key_press_event', self.on_key_press)
            self._cid_key_release = self.canvas.mpl_connect('key_release_event', self.on_key_release)

    def disconnect(self):
        """ イベントハンドラを切断 """
        self.logger.log(LogLevel.CALL, "イベントハンドラ切断開始")
        if self._cid_press is not None: # マウスボタン押下イベントが接続されている場合は切断
            self.canvas.mpl_disconnect(self._cid_press)
            self._cid_press = None
        if self._cid_release is not None: # マウスボタンリリースイベントが接続されている場合は切断
            self.canvas.mpl_disconnect(self._cid_release)
            self._cid_release = None
        self._disconnect_motion()
        if self._cid_key_press is not None: # キーボード押下イベントが接続されている場合は切断
            self.canvas.mpl_disconnect(self._cid_key_press)
            self._cid_key_press = None
        if self._cid_key_release is not None: # キーリリース切断を追加
            self.canvas.mpl_disconnect(self._cid_key_release)
            self._cid_key_release = None
        self._alt_pressed = False # 切断時にAltキー状態をリセット

    def _connect_motion(self):
        """ motion_notify_event を接続 """
        if self._cid_motion is None: # モーションが切断されている場合は接続
            self.logger.log(LogLevel.CALL, "接続開始：motion_notify_event")
            self._cid_motion = self.canvas.mpl_connect('motion_notify_event', self.on_motion)

    def _disconnect_motion(self):
        """ motion_notify_event を切断 """
        if self._cid_motion is not None: # モーションが接続されている場合は切断
            self.logger.log(LogLevel.CALL, "切断開始：motion_notify_event")
            self.canvas.mpl_disconnect(self._cid_motion)
            self._cid_motion = None
    # --- イベント接続/切断 ここまで ---

    # --- イベント処理メソッド (ディスパッチャ) ---
    def on_press(self, event: MouseEvent):
        """ マウスボタン押下イベントのディスパッチャ """
        validation_result = self.validator.validate_event(event, self.zoom_selector.ax, self.logger)
        if not validation_result.is_press_valid:
            self.logger.log(LogLevel.DEBUG, "on_press: 基本検証失敗のため処理中断")
            return
        state = self.state_handler.get_state()
        self.logger.log(LogLevel.CALL, f"on_press: 状態={state.name}, ボタン={event.button}")
        # 状態とボタンに応じてハンドラを呼び出し
        if state == ZoomState.NO_RECT:
            if event.button == MouseButton.LEFT:
                self._handle_press_no_rect_left(event)
        elif state == ZoomState.EDIT:
            if event.button == MouseButton.LEFT:
                self._dispatch_press_edit_left(event)
            elif event.button == MouseButton.RIGHT:
                self._handle_press_edit_right_confirm(event)
        # 他の状態 (CREATE中など) でのPressは基本的に無視 or 特定の処理

    def on_motion(self, event: MouseEvent):
        """ マウス移動イベントのディスパッチャ """
        validation_result = self.validator.validate_event(event, self.zoom_selector.ax, self.logger)
        if not (validation_result.is_in_axes and validation_result.has_coords):
            self.logger.log(LogLevel.DEBUG, "on_motion: Axes外または座標無効のため処理中断")
            return
        state = self.state_handler.get_state()
        self.logger.log(LogLevel.CALL, f"on_motion: 状態={state.name}")
        # 状態に応じてハンドラを呼び出し
        if state == ZoomState.CREATE:
            if event.button == MouseButton.LEFT: # ドラッグ中か確認
                self._handle_motion_create(event)
        elif state == ZoomState.EDIT:
            self._handle_motion_edit(event)
        elif state == ZoomState.ON_MOVE:
            if event.button == MouseButton.LEFT:
                self._handle_motion_move(event)
        elif state == ZoomState.RESIZING:
            if event.button == MouseButton.LEFT:
                self._handle_motion_resizing(event)
        elif state == ZoomState.ROTATING:
            if event.button == MouseButton.LEFT:
                self._handle_motion_rotating(event)

    def on_release(self, event: MouseEvent):
        """ マウスボタン解放イベントのディスパッチャ """
        validation_result = self.validator.validate_event(event, self.zoom_selector.ax, self.logger)
        is_outside = not validation_result.has_coords # 軸外でのリリースか
        state = self.state_handler.get_state()
        self.logger.log(LogLevel.CALL, f"on_release: 状態={state.name}, ボタン={event.button}, 軸外={is_outside}")
        operation_ended = False
        final_state_to_set = ZoomState.EDIT # デフォルトは操作完了後のEDIT状態
        # 状態に応じてハンドラを呼び出し
        if state == ZoomState.CREATE:
            if event.button == MouseButton.LEFT:
                final_state_to_set = self._handle_release_create(event, is_outside)
                operation_ended = True
        elif state == ZoomState.ON_MOVE:
            if event.button == MouseButton.LEFT:
                final_state_to_set = self._handle_release_move(event)
                operation_ended = True
        elif state == ZoomState.RESIZING:
            if event.button == MouseButton.LEFT:
                final_state_to_set = self._handle_release_resizing(event)
                operation_ended = True
        elif state == ZoomState.ROTATING:
            if event.button == MouseButton.LEFT:
                final_state_to_set = self._handle_release_rotating(event)
                operation_ended = True
        # 操作が終了した場合の共通後処理
        if operation_ended:
            self.logger.log(LogLevel.INFO, f"操作終了: 新しい状態へ遷移 -> {final_state_to_set.name}")
            self.state_handler.update_state(final_state_to_set, {"action": f"{state.name} 終了"})
            self.zoom_selector.invalidate_rect_cache()
            # Altキーの状態も考慮してカーソルを更新
            self.cursor_manager.cursor_update(event, state=final_state_to_set, is_rotating=self._alt_pressed)
            self.canvas.draw_idle()

    def on_key_press(self, event: KeyEvent):
        """ キーボード押下イベントのディスパッチャ """
        self.logger.log(LogLevel.CALL, f"on_key_press: キー={event.key}")
        if event.key == 'escape':
            self._handle_key_escape(event)
        elif event.key == 'alt':
            self._handle_key_alt_press(event)
        # 他のキー処理が必要なら追加
        # 必要であればここでカーソル更新を強制する
        # self.cursor_manager.cursor_update(None, state=state, is_rotating=True)

    def on_key_release(self, event: KeyEvent):
        """ キーボード解放イベントのディスパッチャ """
        self.logger.log(LogLevel.CALL, f"on_key_release: キー={event.key}")
        if event.key == 'alt':
            self._handle_key_alt_release(event)
        # 他のキー処理が必要なら追加
        # 必要であればここでカーソル更新を強制する
        # self.cursor_manager.cursor_update(None, state=state, is_rotating=False)
    # --- イベント処理メソッド (ディスパッチャ) ここまで ---

    # --- プライベートハンドラメソッド ---
    # --- Press イベントハンドラ ---
    def _handle_press_no_rect_left(self, event: MouseEvent):
        """ NO_RECT 状態で左クリック: 矩形作成開始 """
        self.logger.log(LogLevel.INFO, "ハンドラ: _handle_press_no_rect_left (矩形作成開始)")
        self.state_handler.update_state(ZoomState.CREATE, {"action": "作成開始"})
        if event.xdata is None or event.ydata is None: return # 型ガード
        self.start_x, self.start_y = event.xdata, event.ydata
        self.rect_manager.setup_rect(self.start_x, self.start_y)
        self.zoom_selector.invalidate_rect_cache()
        self._connect_motion()
        self.cursor_manager.cursor_update(event, state=self.state_handler.get_state())
        self._create_logged = False
        self.canvas.draw_idle()
        self.add_history(None) # 矩形がない状態を履歴に追加

    def _dispatch_press_edit_left(self, event: MouseEvent):
        """ EDIT 状態で左クリック: 回転/リサイズ/移動の開始を判定してディスパッチ """
        corner_index = self.zoom_selector.pointer_near_corner(event)
        is_inside = self.zoom_selector.cursor_inside_rect(event)
        if self._alt_pressed and corner_index is not None:
            self._handle_press_edit_start_rotating(event, corner_index)
        elif not self._alt_pressed and corner_index is not None:
            self._handle_press_edit_start_resizing(event, corner_index)
        elif not self._alt_pressed and is_inside:
            self._handle_press_edit_start_moving(event)
        # else: 角でも内側でもない場合は何もしない

    def _handle_press_edit_start_rotating(self, event: MouseEvent, corner_index: int):
        """ EDIT 状態 + Alt + 角で左クリック: 回転開始 """
        self.logger.log(LogLevel.INFO, f"ハンドラ: _handle_press_edit_start_rotating (角 {corner_index})")
        current_state_for_history = self.rect_manager.get_state() # 履歴追加のため先に取得
        center = self.rect_manager.get_center()
        if center and event.xdata is not None and event.ydata is not None:
            self.add_history(current_state_for_history) # 成功しそうなので履歴追加
            self.rotate_center = center
            self.rotate_start_mouse_pos = (event.xdata, event.ydata)
            start_vector_angle = self._calculate_angle(center[0], center[1], event.xdata, event.ydata)
            self.previous_vector_angle = start_vector_angle
            self.logger.log(LogLevel.CALL, f"回転開始パラメータ: 中心={center}, 開始角度={start_vector_angle:.2f}")
            self.state_handler.update_state(ZoomState.ROTATING, {"action": "回転開始", "角": corner_index})
            self._connect_motion()
            self.cursor_manager.cursor_update(event, state=self.state_handler.get_state(), near_corner_index=corner_index, is_rotating=True)
            self._rotate_logged = False
            # 回転開始時はスタイル変更はしない
            # self.canvas.draw_idle() # 不要
        else:
            self.logger.log(LogLevel.ERROR, "回転不可：中心座標またはイベント座標なし")

    def _handle_press_edit_start_resizing(self, event: MouseEvent, corner_index: int):
        """ EDIT 状態 + 角で左クリック: リサイズ開始 """
        self.logger.log(LogLevel.INFO, f"ハンドラ: _handle_press_edit_start_resizing (角 {corner_index})")
        current_state_for_history = self.rect_manager.get_state() # 履歴追加のため先に取得
        rotated_corners = self.rect_manager.get_rotated_corners()
        if rotated_corners:
            self.add_history(current_state_for_history) # 成功しそうなので履歴追加
            self.state_handler.update_state(ZoomState.RESIZING, {"action": "リサイズ開始", "角": corner_index})
            self.resize_corner_index = corner_index
            self.rect_manager.edge_change_editing() # スタイル変更
            fixed_corner_idx = 3 - corner_index
            self.fixed_corner_pos = rotated_corners[fixed_corner_idx]
            self.logger.log(LogLevel.CALL, f"リサイズ開始パラメータ: 固定角(回転後)={self.fixed_corner_pos}")
            self._connect_motion()
            self.cursor_manager.cursor_update(event, state=self.state_handler.get_state(), near_corner_index=self.resize_corner_index, is_rotating=False)
            self._resize_logged = False
            self.canvas.draw_idle() # スタイル変更を反映
        else:
            self.logger.log(LogLevel.ERROR, "リサイズ不可：回転後の角座標を取得できず")

    def _handle_press_edit_start_moving(self, event: MouseEvent):
        """ EDIT 状態 + 内部で左クリック: 移動開始 """
        self.logger.log(LogLevel.INFO, "ハンドラ: _handle_press_edit_start_moving")
        current_state_for_history = self.rect_manager.get_state() # 履歴追加のため先に取得
        rect_props = self.rect_manager.get_properties()
        if rect_props and event.xdata is not None and event.ydata is not None:
            self.add_history(current_state_for_history) # 成功しそうなので履歴追加
            self.state_handler.update_state(ZoomState.ON_MOVE, {"action": "移動開始"})
            self.rect_manager.edge_change_editing() # スタイル変更
            self.move_start_x, self.move_start_y = event.xdata, event.ydata
            self.rect_start_pos = (rect_props[0], rect_props[1]) # 回転前の左下座標
            self.logger.log(LogLevel.CALL, f"移動開始パラメータ: マウス=({self.move_start_x:.2f}, {self.move_start_y:.2f}), 矩形左下={self.rect_start_pos}")
            self._connect_motion()
            self.cursor_manager.cursor_update(event, state=self.state_handler.get_state(), is_rotating=False)
            self._move_logged = False
            self.canvas.draw_idle() # スタイル変更を反映
        else:
            self.logger.log(LogLevel.ERROR, "移動不可：矩形プロパティまたはイベント座標なし")

    def _handle_press_edit_right_confirm(self, event: MouseEvent):
        """ EDIT 状態で右クリック: ズーム確定 """
        self.logger.log(LogLevel.INFO, "ハンドラ: _handle_press_edit_right_confirm (ズーム確定)")
        self.zoom_selector.confirm_zoom() # ZoomSelectorに処理を委譲
    # --- Press イベントハンドラ ここまで ---

    # --- Motion イベントハンドラ ---
    def _handle_motion_create(self, event: MouseEvent):
        """ CREATE 状態でのマウス移動: 矩形サイズ更新 """
        if self.start_x is not None and self.start_y is not None and event.xdata is not None and event.ydata is not None:
            # self.logger.log(LogLevel.CALL, "ハンドラ: _handle_motion_create (作成中)") # ログが多すぎる
            self.rect_manager.setting_rect_size(self.start_x, self.start_y, event.xdata, event.ydata)
            self.canvas.draw_idle()

    def _handle_motion_edit(self, event: MouseEvent):
        """ EDIT 状態でのマウス移動: カーソル更新 """
        # self.logger.log(LogLevel.CALL, "ハンドラ: _handle_motion_edit (カーソル更新)") # ログが多すぎる
        corner_index = self.zoom_selector.pointer_near_corner(event)
        # is_inside = self.zoom_selector.cursor_inside_rect(event) # cursor_update内で判定される
        self.cursor_manager.cursor_update(event, state=ZoomState.EDIT, near_corner_index=corner_index, is_rotating=self._alt_pressed)

    def _handle_motion_move(self, event: MouseEvent):
        """ ON_MOVE 状態でのマウス移動: 矩形移動 """
        if not self._move_logged:
            self.logger.log(LogLevel.INFO, "ハンドラ: _handle_motion_move (移動中)")
            self._move_logged = True
        if self.move_start_x is not None and self.move_start_y is not None and \
           self.rect_start_pos is not None and event.xdata is not None and event.ydata is not None:
            dx = event.xdata - self.move_start_x
            dy = event.ydata - self.move_start_y
            new_rect_x = self.rect_start_pos[0] + dx
            new_rect_y = self.rect_start_pos[1] + dy
            self.rect_manager.move_rect_to(new_rect_x, new_rect_y)
            self.zoom_selector.invalidate_rect_cache() # 移動中はキャッシュを無効化
            self.canvas.draw_idle()

    def _handle_motion_resizing(self, event: MouseEvent):
        """ RESIZING 状態でのマウス移動: 矩形リサイズ """
        if not self._resize_logged:
            self.logger.log(LogLevel.INFO, f"ハンドラ: _handle_motion_resizing (リサイズ中 - 角 {self.resize_corner_index})")
            self._resize_logged = True
        if self.fixed_corner_pos is not None and event.xdata is not None and event.ydata is not None:
            fixed_x_rotated, fixed_y_rotated = self.fixed_corner_pos
            current_x, current_y = event.xdata, event.ydata
            self.rect_manager.resize_rect_from_corners(fixed_x_rotated, fixed_y_rotated, current_x, current_y)
            self.zoom_selector.invalidate_rect_cache() # リサイズ中はキャッシュを無効化
            self.canvas.draw_idle()

    def _handle_motion_rotating(self, event: MouseEvent):
        """ ROTATING 状態でのマウス移動: 矩形回転 """
        if not self._rotate_logged:
            self.logger.log(LogLevel.INFO, "ハンドラ: _handle_motion_rotating (回転中)")
            self._rotate_logged = True
        if self.rotate_center and self.previous_vector_angle is not None and \
           event.xdata is not None and event.ydata is not None:
            current_vector_angle = self._calculate_angle(
                self.rotate_center[0], self.rotate_center[1], event.xdata, event.ydata)
            delta_angle = self._normalize_angle_diff(current_vector_angle, self.previous_vector_angle)

            if abs(delta_angle) > self.ROTATION_THRESHOLD:
                adjusted_delta_angle = delta_angle * self.ROTATION_SENSITIVITY
                current_rect_angle = self.rect_manager.get_rotation()
                new_angle = current_rect_angle + adjusted_delta_angle
                self.rect_manager.set_rotation(new_angle)
                self.previous_vector_angle = current_vector_angle # 次回のために更新
                self.logger.log(LogLevel.DEBUG, f"回転 delta:{delta_angle:.2f} adj:{adjusted_delta_angle:.2f} new:{new_angle:.2f}")
                self.zoom_selector.invalidate_rect_cache() # 回転中はキャッシュを無効化
                self.canvas.draw_idle()
            # else: 閾値以下の変化は無視
    # --- Motion イベントハンドラ ここまで ---

    # --- Release イベントハンドラ ---
    def _handle_release_create(self, event: MouseEvent, is_outside: bool) -> ZoomState:
        """ CREATE 状態でのマウス解放: 作成完了またはキャンセル """
        self.logger.log(LogLevel.INFO, "ハンドラ: _handle_release_create")
        self._disconnect_motion() # モーション切断
        final_state = ZoomState.NO_RECT # デフォルトはキャンセル

        if is_outside:
            self.logger.log(LogLevel.WARNING, "作成キャンセル: 軸外でリリース")
            self.rect_manager.delete_rect()
            self.remove_last_history() # 作成前の状態(None)の履歴を削除
        elif event.button == MouseButton.LEFT:
            if self.start_x is not None and self.start_y is not None and \
               event.xdata is not None and event.ydata is not None:
                # 最終的なサイズで確定を試みる
                if self.rect_manager.temporary_creation(self.start_x, self.start_y, event.xdata, event.ydata):
                    self.logger.log(LogLevel.INFO, "作成成功")
                    final_state = ZoomState.EDIT # 成功したらEDIT状態へ
                    # 履歴はpressで追加済み
                else:
                    self.logger.log(LogLevel.WARNING, "作成失敗: 最終サイズが無効")
                    self.rect_manager.delete_rect() # 失敗したので削除
                    self.remove_last_history() # 履歴も削除
            else:
                self.logger.log(LogLevel.ERROR, "作成失敗: 座標情報不備")
                self.rect_manager.delete_rect() # 念のため削除
                self.remove_last_history() # 履歴も削除

        self._reset_create_state() # 作成関連の内部状態をリセット
        return final_state

    def _handle_release_move(self, event: MouseEvent) -> ZoomState:
        """ ON_MOVE 状態でのマウス解放: 移動完了 """
        self.logger.log(LogLevel.INFO, "ハンドラ: _handle_release_move (移動完了)")
        self.rect_manager.edge_change_finishing() # スタイルを戻す
        self._disconnect_motion()
        self._reset_move_state()
        return ZoomState.EDIT # 移動後はEDIT状態へ

    def _handle_release_resizing(self, event: MouseEvent) -> ZoomState:
        """ RESIZING 状態でのマウス解放: リサイズ完了またはキャンセル/Undo """
        self.logger.log(LogLevel.INFO, "ハンドラ: _handle_release_resizing (リサイズ完了)")
        self.rect_manager.edge_change_finishing() # スタイルを戻す
        self._disconnect_motion()
        final_state = ZoomState.EDIT # デフォルトはEDIT状態

        # リサイズ完了後も矩形が有効かチェック
        rect_props = self.rect_manager.get_properties()
        if not (rect_props and self.rect_manager.is_valid_size(rect_props[2], rect_props[3])):
            self.logger.log(LogLevel.WARNING, "リサイズ中断: 無効なサイズになったためUndo試行")
            self.undo_last_edit() # 最後の有効な状態に戻す
            if not self.rect_manager.get_rect(): # Undoの結果、矩形が消えた場合
                final_state = ZoomState.NO_RECT

        self._reset_resize_state()
        return final_state

    def _handle_release_rotating(self, event: MouseEvent) -> ZoomState:
        """ ROTATING 状態でのマウス解放: 回転完了 """
        self.logger.log(LogLevel.INFO, "ハンドラ: _handle_release_rotating (回転完了)")
        # スタイル変更は回転中にはないので戻す必要なし
        self._disconnect_motion()
        self._reset_rotate_state()
        return ZoomState.EDIT # 回転後はEDIT状態へ
    # --- Release イベントハンドラ ここまで ---

    # --- Key イベントハンドラ ---
    def _handle_key_escape(self, event: KeyEvent):
        """ Escapeキー押下処理 """
        self.logger.log(LogLevel.INFO, "ハンドラ: _handle_key_escape")
        state = self.state_handler.get_state()
        if state is ZoomState.NO_RECT:
            self.logger.log(LogLevel.DEBUG, "ESC: NO_RECT -> ズーム確定キャンセル呼び出し")
            self.zoom_selector.cancel_zoom() # MainWindow側の処理を呼び出す
        elif state is ZoomState.EDIT:
            self.logger.log(LogLevel.DEBUG, "ESC: EDIT -> Undo/編集キャンセル呼び出し")
            self.undo_or_cancel_edit() # Undoまたは編集キャンセル
        elif state in [ZoomState.CREATE, ZoomState.ON_MOVE, ZoomState.RESIZING, ZoomState.ROTATING]:
             self.logger.log(LogLevel.DEBUG, f"ESC: {state.name} -> 操作キャンセル呼び出し")
             # ドラッグ操作中にESCが押された場合もキャンセル
             self.undo_or_cancel_edit()

    def _handle_key_alt_press(self, event: KeyEvent):
        """ Altキー押下処理 """
        if not self._alt_pressed:
            self.logger.log(LogLevel.INFO, "ハンドラ: _handle_key_alt_press (回転モード有効化)")
            self._alt_pressed = True
            # EDIT状態ならカーソル更新の必要性を示唆 (実際の更新はmotionで)
            if self.state_handler.get_state() == ZoomState.EDIT:
                self.logger.log(LogLevel.DEBUG, "Alt押下: EDIT状態。次回motionでカーソル更新")
                # 強制更新が必要ならここで cursor_manager.cursor_update を呼ぶ

    def _handle_key_alt_release(self, event: KeyEvent):
        """ Altキー解放処理 """
        if self._alt_pressed:
            self.logger.log(LogLevel.INFO, "ハンドラ: _handle_key_alt_release (回転モード無効化)")
            self._alt_pressed = False
            # EDIT状態ならカーソル更新の必要性を示唆 (実際の更新はmotionで)
            if self.state_handler.get_state() == ZoomState.EDIT:
                self.logger.log(LogLevel.DEBUG, "Alt解放: EDIT状態。次回motionでカーソル更新")
                # 強制更新が必要ならここで cursor_manager.cursor_update を呼ぶ
    # --- Key イベントハンドラ ここまで ---
    # --- プライベートハンドラメソッド ここまで ---

    # --- Undo 関連メソッド ---
    def add_history(self, state: Optional[Dict[str, Any]]):
        """ 編集履歴に状態を追加 """
        # None (矩形がない状態) を履歴に追加することも許可する
        self.edit_history.append(state)
        self.logger.log(LogLevel.DEBUG, f"履歴追加: 現在の履歴数={len(self.edit_history)}")
        # メモリリークを防ぐため、履歴数に上限を設けることも検討
        # MAX_HISTORY = 100
        # if len(self.edit_history) > MAX_HISTORY:
        #     self.edit_history.pop(0) # 古い履歴を削除

    def remove_last_history(self):
        """ 最後の履歴を削除 """
        if self.edit_history:
            removed = self.edit_history.pop()
            self.logger.log(LogLevel.DEBUG, f"最後の履歴削除: 削除後の履歴数={len(self.edit_history)}")
            return removed
        return None

    def clear_edit_history(self):
        """ 編集履歴をクリア """
        self.edit_history.clear()
        self.logger.log(LogLevel.INFO, "編集履歴クリア完了")

    def undo_last_edit(self):
        """ 最後に行った編集操作を元に戻す """
        if len(self.edit_history) > 0: # 履歴が1つ以上あればUndo可能
            # 現在の状態は破棄し、一つ前の状態を取り出す
            prev_state = self.edit_history.pop()
            self.logger.log(LogLevel.INFO, "Undo実行", {"復元前の履歴数": len(self.edit_history) + 1})
            self.rect_manager.set_state(prev_state) # 状態を復元
            self.zoom_selector.invalidate_rect_cache()
            # Undo後もEDIT状態なのでカーソル更新
            self.cursor_manager.cursor_update(None, state=ZoomState.EDIT, is_rotating=self._alt_pressed)
            self.canvas.draw_idle()
        else:
            self.logger.log(LogLevel.WARNING, "Undo不可: 編集履歴なし")

    def undo_or_cancel_edit(self):
        """ ESCキーによるUndoまたは編集キャンセル """
        if len(self.edit_history) > 1: # 初期状態 + 1回以上の編集履歴があればUndo
            self.undo_last_edit()
        elif len(self.edit_history) == 1: # 矩形作成直後などの場合
            self.logger.log(LogLevel.INFO, "ESC -> Undo履歴なし: ズーム領域編集キャンセル実行")
            self.clear_edit_history() # 履歴クリア
            self._disconnect_motion()
            self.zoom_selector.cancel_rect() # 矩形削除 (ZoomSelector側)
            self.reset_internal_state() # 内部状態リセット (ここで再度履歴クリアされる)
            self.state_handler.update_state(ZoomState.NO_RECT, {"action": "ESCによる編集キャンセル"})
            self.cursor_manager.set_default_cursor()
            self.canvas.draw_idle()
        else: # 履歴0の場合 (通常EDITではないはず)
            self.logger.log(LogLevel.WARNING, "ESC -> 履歴0だがキャンセル試行")
            self._disconnect_motion()
            self.zoom_selector.cancel_rect()
            self.reset_internal_state()
            self.state_handler.update_state(ZoomState.NO_RECT, {"action": "ESCによる編集キャンセル(履歴0)"})
            self.cursor_manager.set_default_cursor()
            self.canvas.draw_idle()
    # --- Undo 関連メソッド ここまで ---

    # --- ヘルパーメソッド ---
    def _calculate_angle(self, cx: float, cy: float, px: float, py: float) -> float:
        """ 中心点から点へのベクトル角度を計算 (度, -180から180) """
        return math.degrees(math.atan2(py - cy, px - cx))

    def _normalize_angle_diff(self, angle1: float, angle2: float) -> float:
        """ 角度差を -180度から180度の範囲に正規化 """
        diff = angle1 - angle2
        while diff <= -180: diff += 360
        while diff > 180: diff -= 360
        return diff
    # --- ヘルパーメソッド ここまで ---

    # --- 状態リセットメソッド群 ---
    def reset_internal_state(self):
        """ 全ての内部状態と編集履歴をリセット """
        self._reset_create_state()
        self._reset_move_state()
        self._reset_resize_state()
        self._reset_rotate_state()
        self._alt_pressed = False
        self.clear_edit_history() # 編集履歴もクリア
        self._disconnect_motion() # マウスモーションも切断
        self.logger.log(LogLevel.INFO, "EventHandler の内部状態と編集履歴をリセット完了")

    def _reset_create_state(self):
        self.start_x = None
        self.start_y = None
        self._create_logged = False

    def _reset_move_state(self):
        self.move_start_x = None
        self.move_start_y = None
        self.rect_start_pos = None
        self._move_logged = False

    def _reset_resize_state(self):
        self.resize_corner_index = None
        self.fixed_corner_pos = None
        self._resize_logged = False

    def _reset_rotate_state(self):
        self.rotate_start_mouse_pos = None
        self.rotate_center = None
        self.previous_vector_angle = None
        self._rotate_logged = False
    # --- 状態リセットメソッド群 ここまで ---
