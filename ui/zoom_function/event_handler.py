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
    # --- 設定ここまで ---

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
        self.zoom_selector = zoom_selector
        self.state_handler = state_handler
        self.rect_manager = rect_manager
        self.cursor_manager = cursor_manager
        self.cursor_manager.set_zoom_selector(zoom_selector)
        self.validator = validator
        self.logger = logger
        self.canvas = canvas
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
        self._rotate_logged = False
        # --- Undo 用の編集履歴 ---
        self.edit_history: List[Optional[Dict[str, Any]]] = [] # 矩形の状態を保存するリスト
        # --- ここまで Undo 用 ---

    def connect(self):
        """ イベントハンドラを接続 """
        if self._cid_press is None: # すでに接続されている場合は何もしない
            self._cid_press = self.canvas.mpl_connect('button_press_event', self.on_press)
            self._cid_release = self.canvas.mpl_connect('button_release_event', self.on_release)
            self._cid_key_press = self.canvas.mpl_connect('key_press_event', self.on_key_press)
            self._cid_key_release = self.canvas.mpl_connect('key_release_event', self.on_key_release)
            self.logger.log(LogLevel.CALL, "接続完了：全イベントハンドラ")

    def disconnect(self):
        """ イベントハンドラを切断 """
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
        self.logger.log(LogLevel.CALL, "イベントハンドラ切断完了")

    def _connect_motion(self):
        """ motion_notify_event を接続 """
        if self._cid_motion is None: # モーションが切断されている場合は接続
            self._cid_motion = self.canvas.mpl_connect('motion_notify_event', self.on_motion)
            self.logger.log(LogLevel.CALL, "接続完了：motion_notify_event")

    def _disconnect_motion(self):
        """ motion_notify_event を切断 """
        if self._cid_motion is not None: # モーションが接続されている場合は切断
            self.canvas.mpl_disconnect(self._cid_motion)
            self._cid_motion = None
            self.logger.log(LogLevel.CALL, "切断完了：motion_notify_event")

    def on_press(self, event: MouseEvent):
        """ マウスボタンが押された時の処理 """
        validation_result = self.validator.validate_event(event, self.zoom_selector.ax, self.logger)
        # マウスプレスに必要な全ての条件を満たしているかチェック
        if not validation_result.is_press_valid:
             self.logger.log(LogLevel.DEBUG, "基本検証失敗：処理中断")
             return
        self.logger.log(LogLevel.CALL, "検証成功：処理続行")
        state = self.state_handler.get_state()
        self.logger.log(LogLevel.CALL, "状態取得", {"結果": state.name})
        if state == ZoomState.NO_RECT:
            if event.button == MouseButton.LEFT:
                # ズーム領域作成開始
                self.logger.log(LogLevel.INFO, "ズーム領域作成のメソッド開始")
                self.logger.log(LogLevel.CALL, "状態変更 to CREATE.")
                self.state_handler.update_state(ZoomState.CREATE, {"action": "作成開始"})
                self.logger.log(LogLevel.CALL, "始点取得開始", {"x": event.xdata, "y": event.ydata})
                self.start_x, self.start_y = event.xdata, event.ydata
                self.logger.log(LogLevel.INFO, "ズーム領域の初期状態を作成開始：始点", {"x": self.start_x, "y": self.start_y})
                self.rect_manager.setup_rect(self.start_x, self.start_y)
                self.logger.log(LogLevel.DEBUG, "ズーム領域のキャッシュ無効化開始")
                self.zoom_selector.invalidate_rect_cache()
                self._connect_motion()
                self.logger.log(LogLevel.CALL, "カーソル更新")
                self.cursor_manager.cursor_update(event, state=self.state_handler.get_state())
                self._create_logged = False # 新規作成ログフラグをリセット
                self.canvas.draw_idle()
                # --- Undo 用: 作成開始前の状態 (None) を履歴に追加 ---
                self.add_history(None) # 矩形がない状態を記録
                # --- ここまで Undo 用 ---
        elif state == ZoomState.EDIT:
            if event.button == MouseButton.LEFT:
                corner_index = self.zoom_selector.pointer_near_corner(event)

                # --- Undo 用: 編集操作の開始前に状態を保存 ---
                should_add_history = False
                if self._alt_pressed and corner_index is not None: # 回転開始
                    should_add_history = True
                elif not self._alt_pressed and corner_index is not None: # リサイズ開始
                    should_add_history = True
                elif not self._alt_pressed and self.zoom_selector.cursor_inside_rect(event): # 移動開始
                    should_add_history = True

                if should_add_history:
                    current_state = self.rect_manager.get_state()
                    self.add_history(current_state)
                # --- ここまで Undo 用 ---

                if self._alt_pressed and corner_index is not None:
                    self.logger.log(LogLevel.INFO, f"回転開始：角 {corner_index}.")
                    center = self.rect_manager.get_center()
                    if center:
                        self.rotate_center = center
                        self.rotate_start_mouse_pos = (event.xdata, event.ydata) # 開始位置は記録しておく（将来使うかも）
                        # 回転開始時のベクトル角度を previous_vector_angle に保存
                        start_vector_angle = self._calculate_angle(
                            center[0], center[1], event.xdata, event.ydata)
                        self.previous_vector_angle = start_vector_angle
                        self.logger.log(LogLevel.CALL, f"回転開始：中心 = {center}, 開始ベクトル角度={start_vector_angle:.2f}")
                        self.logger.log(LogLevel.INFO, "状態変更：ROTATING")
                        self.state_handler.update_state(ZoomState.ROTATING, {"action": "回転開始", "角": corner_index})
                        self._connect_motion()
                        self.logger.log(LogLevel.INFO, "カーソル更新（回転モード）")
                        self.cursor_manager.cursor_update(event, state=self.state_handler.get_state(), near_corner_index=corner_index, is_rotating=True)
                        self._rotate_logged = False
                    else:
                        self.logger.log(LogLevel.ERROR, "回転不可：ズーム領域の中心を取得できず")
                        # --- Undo 用: 履歴を元に戻す (操作が開始できなかった場合) ---
                        if should_add_history: self.remove_last_history()
                        # --- ここまで Undo 用 ---
                elif not self._alt_pressed and corner_index is not None:
                    self.logger.log(LogLevel.INFO, f"リサイズ開始：角 {corner_index}.")
                    self.logger.log(LogLevel.INFO, "状態変更：RESIZING.")
                    self.state_handler.update_state(ZoomState.RESIZING, {"action": "リサイズ開始", "角": corner_index})
                    self.resize_corner_index = corner_index
                    self.rect_manager.edge_change_editing()
                    rotated_corners = self.rect_manager.get_rotated_corners()
                    self.canvas.draw_idle()
                    # --- 固定角の計算 (回転後座標を使用) ---
                    rotated_corners = self.rect_manager.get_rotated_corners() # 回転後の角座標を取得
                    if rotated_corners:
                        fixed_corner_idx = 3 - corner_index # 対角のインデックス (0<->3, 1<->2)
                        self.fixed_corner_pos = rotated_corners[fixed_corner_idx] # 回転後の対角座標を保存
                        self.logger.log(LogLevel.CALL, f"固定する角 {fixed_corner_idx} at {self.fixed_corner_pos} (rotated)")
                        self._connect_motion()
                        self.cursor_manager.cursor_update(event, state=self.state_handler.get_state(), near_corner_index=self.resize_corner_index, is_rotating=False)
                        self._resize_logged = False
                        self.canvas.draw_idle() # スタイル変更を反映
                    else:
                        self.logger.log(LogLevel.ERROR, "リサイズ不可：回転後の角を取得できず")
                        self._reset_resize_state()
                        self.state_handler.update_state(ZoomState.EDIT, {"action": "リサイズ開始失敗"})
                        # --- Undo 用: 履歴を元に戻す (操作が開始できなかった場合) ---
                        if should_add_history: self.remove_last_history()
                        # --- ここまで Undo 用 ---
                elif not self._alt_pressed and self.zoom_selector.cursor_inside_rect(event):
                    self.logger.log(LogLevel.INFO, "状態変更：MOVE.")
                    self.state_handler.update_state(ZoomState.ON_MOVE, {"action": "移動開始"})
                    self.rect_manager.edge_change_editing() # スタイル変更
                    self.move_start_x, self.move_start_y = event.xdata, event.ydata
                    rect_props = self.rect_manager.get_properties()
                    if rect_props:
                        self.rect_start_pos = (rect_props[0], rect_props[1]) # (x, y)
                        self._connect_motion()
                        self.cursor_manager.cursor_update(event, state=self.state_handler.get_state(), is_rotating=False)
                        self._move_logged = False
                        self.canvas.draw_idle() # スタイル変更を反映
                    else:
                        self.logger.log(LogLevel.ERROR, "移動不可：矩形プロパティ取得失敗")
                        self._reset_move_state()
                        self.state_handler.update_state(ZoomState.EDIT, {"action": "移動開始失敗"})
                        # --- Undo 用: 履歴を元に戻す (操作が開始できなかった場合) ---
                        if should_add_history: self.remove_last_history()
                        # --- ここまで Undo 用 ---
                # else: # 角でも内側でもない場合 (何もしない)
                    # --- Undo 用: 操作が開始されなかったので履歴を削除 ---
                    # if should_add_history: self.remove_last_history() # 不要な場合もあるが念のため
                    # --- ここまで Undo 用 ---
                    # pass

            elif event.button == MouseButton.RIGHT:
                self.logger.log(LogLevel.INFO, "右クリック検出：ズーム確定処理開始")
                self.zoom_selector.confirm_zoom() # 確定時に履歴はクリアされる

    def on_motion(self, event: MouseEvent) -> None:
        """ マウスが動いた時の処理 """
        validation_result = self.validator.validate_event(event, self.zoom_selector.ax, self.logger)
        # モーションイベントでは、Axes内で座標があることが重要 (ボタン情報は通常不要)
        if not (validation_result.is_in_axes and validation_result.has_coords):
             # is_fully_valid を使っても良い
             # if not validation_result.is_fully_valid:
             self.logger.log(LogLevel.DEBUG, "on_motion: Axes外または座標無効のため処理中断")
             return
        state = self.state_handler.get_state()
        self.logger.log(LogLevel.CALL, "状態取得", {"状態": state.name})
        if state == ZoomState.CREATE:
            if event.button == MouseButton.LEFT:
                # ズーム領域作成中のサイズ更新
                if self.start_x is not None and self.start_y is not None:
                    self.logger.log(LogLevel.CALL, "新規作成中...")
                    self.rect_manager.setting_rect_size(self.start_x, self.start_y, event.xdata, event.ydata)
                    self.canvas.draw_idle()
        elif state == ZoomState.EDIT:
            self.logger.log(LogLevel.CALL, "近い角チェック開始")
            corner_index = self.zoom_selector.pointer_near_corner(event)
            self.logger.log(LogLevel.INFO, "カーソル更新")
            self.cursor_manager.cursor_update(event, state=state, near_corner_index=corner_index, is_rotating=self._alt_pressed)
        elif state == ZoomState.ON_MOVE:
            if event.button == MouseButton.LEFT:
                if not self._move_logged:
                    self.logger.log(LogLevel.INFO, "ズーム領域移動開始", {
                        "ボタン": event.button, "x": event.xdata, "y": event.ydata, "状態": state})
                    self._move_logged = True
                if self.move_start_x is not None and self.move_start_y is not None and self.rect_start_pos is not None:
                    dx = event.xdata - self.move_start_x
                    dy = event.ydata - self.move_start_y
                    new_rect_x = self.rect_start_pos[0] + dx
                    new_rect_y = self.rect_start_pos[1] + dy
                    self.rect_manager.move_rect_to(new_rect_x, new_rect_y)
                    self.logger.log(LogLevel.CALL, "移動中...", {"x": new_rect_x, "y": new_rect_y})
                    self.logger.log(LogLevel.CALL, "ズーム領域：キャッシュ無効化開始")
                    self.zoom_selector.invalidate_rect_cache()
                    self.canvas.draw_idle()
        elif state == ZoomState.RESIZING:
            if event.button == MouseButton.LEFT:
                if not self._resize_logged:
                    self.logger.log(LogLevel.INFO, "ズーム領域リサイズ中...", {
                        "ボタン": event.button, "x": event.xdata, "y": event.ydata, "状態": state, "角": self.resize_corner_index})
                    self._resize_logged = True
                if self.fixed_corner_pos is not None:
                    fixed_x_rotated, fixed_y_rotated = self.fixed_corner_pos # 回転後の固定角座標
                    current_x, current_y = event.xdata, event.ydata
                    # 回転を考慮したリサイズメソッドを呼び出す
                    self.rect_manager.resize_rect_from_corners(fixed_x_rotated, fixed_y_rotated, current_x, current_y)
                    self.logger.log(LogLevel.CALL, f"リサイズ中: 固定角(回転後)={fixed_x_rotated:.2f},{fixed_y_rotated:.2f} マウス={current_x:.2f},{current_y:.2f}")
                    self.logger.log(LogLevel.CALL, "ズーム領域：キャッシュ無効化開始")
                    self.zoom_selector.invalidate_rect_cache()
                    self.canvas.draw_idle()
        elif state == ZoomState.ROTATING:
            if event.button == MouseButton.LEFT and self.rotate_center and self.previous_vector_angle is not None:
                if not self._rotate_logged:
                    self._rotate_logged = True
                current_vector_angle = self._calculate_angle(
                    self.rotate_center[0], self.rotate_center[1], event.xdata, event.ydata)
                delta_angle = self._normalize_angle_diff(current_vector_angle, self.previous_vector_angle)
                # 閾値チェック: 小さすぎる変化は無視する
                if abs(delta_angle) > self.ROTATION_THRESHOLD:
                    # 感度調整: 計算された変化量を調整
                    adjusted_delta_angle = delta_angle * self.ROTATION_SENSITIVITY
                    current_rect_angle = self.rect_manager.get_rotation()
                    new_angle = current_rect_angle + adjusted_delta_angle
                    self.rect_manager.set_rotation(new_angle)
                    # 重要: 次回の計算のために保存するのは「調整前の」角度
                    # これにより、感度調整による遅延が累積しないようにする
                    self.previous_vector_angle = current_vector_angle
                    self.logger.log(LogLevel.DEBUG, f"回転 delta:{delta_angle:.2f} adj:{adjusted_delta_angle:.2f} new:{new_angle:.2f}")
                    self.zoom_selector.invalidate_rect_cache()
                    self.canvas.draw_idle()
                else:
                    # 閾値以下の変化なので何もしない
                    # previous_vector_angle も更新しないことで、次の有意な変化を待つ
                    self.logger.log(LogLevel.DEBUG, f"回転 delta:{delta_angle:.2f} <= 閾値、スキップ")
                    pass

    def on_release(self, event: MouseEvent) -> None:
        """ マウスボタンが離された時の処理 """
        validation_result = self.validator.validate_event(event, self.zoom_selector.ax, self.logger)
        is_outside = not validation_result.has_coords
        state = self.state_handler.get_state()
        self.logger.log(LogLevel.CALL, "ボタンリリース処理前に状態取得完了", {"状態": state})

        # 操作終了時の共通処理
        operation_ended = False
        final_state_to_set = ZoomState.EDIT # デフォルトは編集完了状態

        if state == ZoomState.CREATE:
            operation_ended = True
            self.logger.log(LogLevel.INFO, "ズーム領域作成完了処理開始")
#            self._disconnect_motion() # モーション切断
            if is_outside:
                self.logger.log(LogLevel.WARNING, "キャンセル：作成中に軸の外側でマウスボタンリリース")
                self.rect_manager.delete_rect() # 作成中の矩形を削除
                final_state_to_set = ZoomState.NO_RECT
                # --- Undo 用: 作成がキャンセルされたので履歴も元に戻す ---
                self.remove_last_history()
                # --- ここまで Undo 用 ---
            elif event.button == MouseButton.LEFT:
                if self.start_x is not None and self.start_y is not None and event.xdata is not None and event.ydata is not None:
                    # 最終的なサイズが有効か再度チェック
                    if self.rect_manager.temporary_creation(self.start_x, self.start_y, event.xdata, event.ydata):
                        self.logger.log(LogLevel.INFO, "ズーム領域作成成功")
                        final_state_to_set = ZoomState.EDIT
                        # --- Undo 用: 作成完了したので、最終状態を履歴に追加するか検討 ---
                        # 今回は操作開始時に履歴を追加したので、ここでは何もしない
                        # --- ここまで Undo 用 ---
                    else: # temporary_creation が False を返した場合 (サイズ無効)
                        self.logger.log(LogLevel.WARNING, "ズーム領域作成失敗：最終サイズが無効")
                        self.rect_manager.delete_rect() # 失敗したので削除
                        final_state_to_set = ZoomState.NO_RECT
                        # --- Undo 用: 作成が失敗したので履歴も元に戻す ---
                        self.remove_last_history()
                        # --- ここまで Undo 用 ---
                else: # 開始座標や終了座標が無効な場合
                    self.logger.log(LogLevel.ERROR, "ズーム領域作成不可：座標情報不備")
                    self.rect_manager.delete_rect() # 念のため削除
                    final_state_to_set = ZoomState.NO_RECT
                    # --- Undo 用: 作成が失敗したので履歴も元に戻す ---
                    self.remove_last_history()
                    # --- ここまで Undo 用 ---
            self._reset_create_state()

        elif state == ZoomState.ON_MOVE:
            if event.button == MouseButton.LEFT:
                operation_ended = True
                self.rect_manager.edge_change_finishing() # スタイルを戻す
                self.logger.log(LogLevel.INFO, "ズーム領域移動終了")
#                self._disconnect_motion()
                self._reset_move_state()
                final_state_to_set = ZoomState.EDIT
                # --- Undo 用: 移動完了、履歴は操作開始時に追加済み ---

        elif state == ZoomState.RESIZING:
            if event.button == MouseButton.LEFT:
                operation_ended = True
                self.rect_manager.edge_change_finishing() # スタイルを戻す
                self.logger.log(LogLevel.INFO, "ズーム領域リサイズ終了")
#                self._disconnect_motion()
                # リサイズ完了後も矩形が有効かチェック
                rect_props = self.rect_manager.get_properties()
                if rect_props and self.rect_manager.is_valid_size(rect_props[2], rect_props[3]):
                    self.logger.log(LogLevel.INFO, "リサイズ成功")
                    final_state_to_set = ZoomState.EDIT
                    # --- Undo 用: リサイズ完了、履歴は操作開始時に追加済み ---
                else:
                    self.logger.log(LogLevel.WARNING, "リサイズ中断：無効なサイズになった可能性")
                    # ここで元の状態に戻すか、削除するかは仕様による
                    # 今回は直前の履歴に戻す (Undo相当)
                    self.undo_last_edit() # 最後の有効な状態に戻す試み
                    if not self.rect_manager.get_rect(): # Undoの結果、矩形が消えた場合
                        final_state_to_set = ZoomState.NO_RECT
                    else:
                        final_state_to_set = ZoomState.EDIT # Undo後の状態でEDITへ
                self._reset_resize_state()
        elif state == ZoomState.ROTATING:
            if event.button == MouseButton.LEFT:
                operation_ended = True
                self.logger.log(LogLevel.INFO, "ズーム領域回転終了")
#                self._disconnect_motion()
                self._reset_rotate_state()
                final_state_to_set = ZoomState.EDIT
                # --- Undo 用: 回転完了、履歴は操作開始時に追加済み ---

        # 操作が終了した場合の共通処理
        if operation_ended:
            new_state_for_log = final_state_to_set.name
            self.logger.log(LogLevel.INFO, f"状態変更 to {new_state_for_log}.")
            self.state_handler.update_state(final_state_to_set, {"action": f"{state.name} 終了"})
            self.zoom_selector.invalidate_rect_cache()
            self.cursor_manager.cursor_update(event, state=final_state_to_set, is_rotating=self._alt_pressed)
            self.canvas.draw_idle()

    def on_key_press(self, event: KeyEvent):
        """ キーボードが押された時の処理 """
        state = self.state_handler.get_state()
        self.logger.log(LogLevel.CALL, f"キー押下 ({event.key}) 時の状態取得", {"状態": state.name})

        if event.key == 'escape':
            if state is ZoomState.NO_RECT:
                # 矩形がない場合は、ズーム確定のキャンセル (MainWindow側の処理を呼び出す)
                self.logger.log(LogLevel.INFO, "ESC キー: NO_RECT状態 -> ズーム確定キャンセル処理開始")
                self.zoom_selector.cancel_zoom() # MainWindow の on_zoom_cancel を呼び出す
            elif state is ZoomState.EDIT:
                # 矩形編集中は Undo または編集キャンセル
                self.logger.log(LogLevel.INFO, f"ESC キー: EDIT状態 -> Undo/編集キャンセル処理開始")
                self.undo_or_cancel_edit() # Undo またはキャンセルを実行
            elif state in [ZoomState.CREATE, ZoomState.ON_MOVE, ZoomState.RESIZING, ZoomState.ROTATING]:
                 # ドラッグ操作中にESCが押された場合もキャンセル扱いにする
                 self.logger.log(LogLevel.INFO, f"ESC キー: {state.name}状態 -> 操作キャンセル")
                 self.undo_or_cancel_edit() # UndoしてEDITに戻すか、キャンセルする

        elif event.key == 'alt':
            if not self._alt_pressed:
                self.logger.log(LogLevel.INFO, "Altキー押下検出：回転モード有効化")
                self._alt_pressed = True
                if state == ZoomState.EDIT:
                    self.logger.log(LogLevel.DEBUG, "EDIT状態でAlt押下。次のマウス移動でカーソル更新")
                    # 必要であればここでカーソル更新を強制する
                    # self.cursor_manager.cursor_update(None, state=state, is_rotating=True)

    def on_key_release(self, event: KeyEvent):
        """ キーボードのキーが離された時の処理 """
        if event.key == 'alt':
            if self._alt_pressed:
                self.logger.log(LogLevel.INFO, "Altキー解放検出：回転モード無効化")
                self._alt_pressed = False
                state = self.state_handler.get_state()
                if state == ZoomState.EDIT:
                    self.logger.log(LogLevel.DEBUG, "EDIT状態でAlt解放。次のマウス移動でカーソル更新")
                    # 必要であればここでカーソル更新を強制する
                    # self.cursor_manager.cursor_update(None, state=state, is_rotating=False)

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
        """ 最後の履歴を削除（操作がキャンセルされた場合など） """
        if self.edit_history:
            removed_state = self.edit_history.pop()
            self.logger.log(LogLevel.DEBUG, f"最後の履歴を削除: 削除後の履歴数={len(self.edit_history)}")
            return removed_state
        return None

    def clear_edit_history(self):
        """ 編集履歴をクリア """
        self.edit_history.clear()
        self.logger.log(LogLevel.INFO, "編集履歴クリア完了")

    def undo_last_edit(self):
        """ 最後に行った編集操作 (移動/リサイズ/回転) を元に戻す """
        if len(self.edit_history) > 0: # 履歴が1つ以上あればUndo可能
            # 現在の状態は破棄し、一つ前の状態を取り出す
            prev_state = self.edit_history.pop()
            self.logger.log(LogLevel.INFO, "Undo実行: 履歴から状態を復元", {"履歴数（実行後）": len(self.edit_history)})
            self.rect_manager.set_state(prev_state)
            self.zoom_selector.invalidate_rect_cache()
            self.canvas.draw_idle()
             # Undo後もEDIT状態を維持 (状態遷移はここでは行わない)
            # カーソル更新が必要な場合がある
            self.cursor_manager.cursor_update(None, state=ZoomState.EDIT, is_rotating=self._alt_pressed)
        else:
            self.logger.log(LogLevel.WARNING, "Undo不可: 編集履歴なし")

    def undo_or_cancel_edit(self):
        """ ESCキーが押されたときの処理 (Undo または 編集キャンセル) """
        if len(self.edit_history) > 1: # 履歴が2つ以上あれば (初期状態 + 1回以上の編集) Undo
            self.undo_last_edit()
             # カーソル更新はundo_last_edit内で行われる
        elif len(self.edit_history) == 1: # 履歴が1つ (矩形作成直後など) ならキャンセル
            self.logger.log(LogLevel.INFO, "ESC -> Undo履歴なし: ズーム領域編集キャンセルを実行")
            self.clear_edit_history() # 最後の履歴もクリア
            self._disconnect_motion()
            self.zoom_selector.cancel_rect() # 矩形を削除
            self.zoom_selector.invalidate_rect_cache()
            self.reset_internal_state() # 内部状態リセット (ここで履歴もクリアされる)
            self.state_handler.update_state(ZoomState.NO_RECT, {"action": "ESCによる編集キャンセル"})
            self.cursor_manager.set_default_cursor()
            self.canvas.draw_idle()
        else: # 履歴が0の場合 (通常はEDIT状態ではないはずだが念のため)
             self.logger.log(LogLevel.WARNING, "ESC -> EDIT状態だが履歴なし: 念のためキャンセル処理")
             self._disconnect_motion()
             self.zoom_selector.cancel_rect()
             self.zoom_selector.invalidate_rect_cache()
             self.reset_internal_state()
             self.state_handler.update_state(ZoomState.NO_RECT, {"action": "ESCによる編集キャンセル(履歴0)"})
             self.cursor_manager.set_default_cursor()
             self.canvas.draw_idle()

    def _calculate_angle(self, cx: float, cy: float, px: float, py: float) -> float:
        """ 中心点(cx, cy)から点(px, py)へのベクトル角度を計算（度単位, -180 から 180） """
        return math.degrees(math.atan2(py - cy, px - cx))

    def _normalize_angle_diff(self, angle1: float, angle2: float) -> float:
        """ 2つの角度の差を計算し、-180度から180度の範囲に正規化する """
        diff = angle1 - angle2
        while diff <= -180: diff += 360
        while diff > 180: diff -= 360
        return diff

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
