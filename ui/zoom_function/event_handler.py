import math # 角度計算
from matplotlib.backend_bases import MouseEvent, MouseButton, KeyEvent
from typing import Optional, TYPE_CHECKING, Tuple
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
        self.rotate_start_vector_angle: Optional[float] = None # 回転開始時の中心からマウスへのベクトル角度 ★修正: 変数名変更★
        self.rect_initial_angle: Optional[float] = None # 回転開始時の矩形の角度
        self.rotate_center: Optional[Tuple[float, float]] = None # 回転中心座標

    def connect(self):
        """ イベントハンドラを接続 """
        if self._cid_press is None: # すでに接続されている場合は何もしない
            self._cid_press = self.canvas.mpl_connect('button_press_event', self.on_press)
            self._cid_release = self.canvas.mpl_connect('button_release_event', self.on_release)
            self._cid_key_press = self.canvas.mpl_connect('key_press_event', self.on_key_press)
            self._cid_key_release = self.canvas.mpl_connect('key_release_event', self.on_key_release) # キーリリース接続を追加
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

        elif state == ZoomState.EDIT:
            if event.button == MouseButton.LEFT:
                # マウスカーソルがズーム領域の角の近くか判定
                corner_index = self.zoom_selector.pointer_near_corner(event)
                if self._alt_pressed and corner_index is not None:
                    # --- 回転開始処理 ---
                    self.logger.log(LogLevel.INFO, f"回転開始：角 {corner_index}.")
                    center = self.rect_manager.get_center()
                    if center:
                        self.rotate_center = center
                        self.rotate_start_mouse_pos = (event.xdata, event.ydata)
                        # 回転開始時の、中心からマウスカーソルへの角度を計算
                        self.rotate_start_vector_angle = self._calculate_angle(
                            center[0], center[1], event.xdata, event.ydata
                        )
                        # 回転開始時の矩形の角度を取得
                        self.rect_initial_angle = self.rect_manager.get_rotation() # [103] 正しい
                        self.logger.log(LogLevel.CALL, f"回転開始：中心 = {center}, mouse_angle={self.rotate_start_vector_angle:.2f}, rect_angle={self.rect_initial_angle:.2f}")

                        self.logger.log(LogLevel.INFO, "状態変更：ROTATING")
                        self.state_handler.update_state(ZoomState.ROTATING, {"action": "回転開始", "角": corner_index})

                        self._connect_motion()
                        self.logger.log(LogLevel.INFO, "カーソル更新（回転モード）")
                        # is_rotating=True を渡す
                        self.cursor_manager.cursor_update(event, state=self.state_handler.get_state(), near_corner_index=corner_index, is_rotating=True)
                        self._rotate_logged = False # 回転ログフラグリセット
                    else:
                        self.logger.log(LogLevel.ERROR, "回転不可：ズーム領域の中心を取得できず")
                    # --- 回転開始処理ここまで ---

                elif not self._alt_pressed and corner_index is not None:
                    # --- リサイズ開始処理 ---
                    self.logger.log(LogLevel.INFO, f"リサイズ開始：角 {corner_index}.")
                    self.logger.log(LogLevel.INFO, "状態変更：RESIZING.")
                    self.state_handler.update_state(ZoomState.RESIZING, {"action": "リサイズ開始", "角": corner_index})
                    self.resize_corner_index = corner_index

                    self.rect_manager.edge_change_editing()
                    self.canvas.draw_idle()

                    # --- 固定角の計算 (回転後座標を使用) ---
                    rotated_corners = self.rect_manager.get_rotated_corners() # 回転後の角座標を取得
                    if rotated_corners:
                        fixed_corner_idx = 3 - corner_index # 対角のインデックス (0<->3, 1<->2)
                        self.fixed_corner_pos = rotated_corners[fixed_corner_idx] # 回転後の対角座標を保存
                        self.logger.log(LogLevel.CALL, f"固定する角 {fixed_corner_idx} at {self.fixed_corner_pos} (rotated)")
                    else: # フォールバックまたはエラー
                        self.logger.log(LogLevel.ERROR, "リサイズ不可：回転後の角を取得できず")
                        self._reset_resize_state()
                        self.state_handler.update_state(ZoomState.EDIT, {"action": "リサイズ開始失敗"})
                        return # リサイズ処理を中断
                    # --- 固定角の計算ここまで ---

                    self._connect_motion()
                    self.logger.log(LogLevel.INFO, "カーソル更新（リサイズモード）")
                    self.cursor_manager.cursor_update(event, state=self.state_handler.get_state(), near_corner_index=self.resize_corner_index, is_rotating=False)
                    self._resize_logged = False
                    # --- リサイズ開始処理ここまで ---

                elif not self._alt_pressed and self.zoom_selector.cursor_inside_rect(event):
                    # ズーム領域移動開始
                    self.logger.log(LogLevel.INFO, "状態変更：MOVE.")
                    self.state_handler.update_state(ZoomState.ON_MOVE, {"action": "移動開始"})

                    self.rect_manager.edge_change_editing()
                    self.canvas.draw_idle()

                    self.move_start_x, self.move_start_y = event.xdata, event.ydata
                    rect_props = self.rect_manager.get_properties()
                    if rect_props:
                        # 注意: 回転を考慮しない場合、この座標は不正確になる可能性
                        self.rect_start_pos = (rect_props[0], rect_props[1]) # (x, y)

                    self._connect_motion()
                    self.logger.log(LogLevel.INFO, "カーソル更新")
                    self.cursor_manager.cursor_update(event, state=self.state_handler.get_state(), is_rotating=False) # 移動カーソル
                    self._move_logged = False

            elif event.button == MouseButton.RIGHT:
                # ズーム確定
                self.logger.log(LogLevel.INFO, "右クリック検出：ズーム確定処理開始")
                self.zoom_selector.confirm_zoom()

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
                    # ここでは、ズーム領域のキャッシュクリアはしない。マウスリリース時に行う。
                self.canvas.draw_idle()

        elif state == ZoomState.EDIT:
            self.logger.log(LogLevel.CALL, "近い角チェック開始")
            corner_index = self.zoom_selector.pointer_near_corner(event)
            self.logger.log(LogLevel.INFO, "カーソル更新")
            self.cursor_manager.cursor_update(event, state=state, near_corner_index=corner_index, is_rotating=self._alt_pressed)

        elif state == ZoomState.ON_MOVE:
            if event.button == MouseButton.LEFT:
                # ズーム領域移動中の処理
                if not self._move_logged:
                    self.logger.log(LogLevel.INFO, "ズーム領域移動開始", {
                        "ボタン": event.button, "x": event.xdata, "y": event.ydata, "状態": state})
                    self._move_logged = True

                if self.move_start_x is not None and self.move_start_y is not None and self.rect_start_pos is not None:
                    # マウスの移動量を計算
                    dx = event.xdata - self.move_start_x
                    dy = event.ydata - self.move_start_y
                    # 新しい矩形の左下座標を計算
                    new_rect_x = self.rect_start_pos[0] + dx
                    new_rect_y = self.rect_start_pos[1] + dy
                    # 矩形を移動
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
            if event.button == MouseButton.LEFT and self.rotate_center and self.rotate_start_vector_angle is not None and self.rect_initial_angle is not None:
                # --- 回転中の処理 ---
                if not self._rotate_logged:
                    self.logger.log(LogLevel.INFO, "ズーム領域回転中...", {
                        "ボタン": event.button, "x": event.xdata, "y": event.ydata, "状態": state})
                    self._rotate_logged = True

                # 現在のマウス位置から中心への角度を計算
                current_vector_angle = self._calculate_angle(
                    self.rotate_center[0], self.rotate_center[1], event.xdata, event.ydata
                )
                # 回転開始時の角度からの差分を計算
                angle_diff = current_vector_angle - self.rotate_start_vector_angle
                # 新しい矩形の角度 = 開始時の角度 + 差分
                new_angle = self.rect_initial_angle + angle_diff

                self.rect_manager.set_rotation(new_angle)
                self.logger.log(LogLevel.CALL, f"回転中... 新角度: {new_angle:.2f}")

                self.logger.log(LogLevel.CALL, "ズーム領域：キャッシュ無効化開始")
                self.zoom_selector.invalidate_rect_cache()

                self.canvas.draw_idle()

    def on_release(self, event: MouseEvent) -> None:
        """ マウスボタンが離された時の処理 """
        validation_result = self.validator.validate_event(event, self.zoom_selector.ax, self.logger)

        # リリース時は、座標があるかどうかだけを気にする場合など、要件に応じてチェック
        # 例えば、軸外でのリリースも許容するなら is_in_axes はチェックしないなど。
        # ここでは例として座標があるかだけチェック
        if not validation_result.has_coords:
             self.logger.log(LogLevel.INFO, "on_release: 座標無効でマウスリリース（処理中断または継続）")
             # return するか、以降のロジックで is_outside として扱う
             # is_outside = not validation_result.has_coords # 例

        state = self.state_handler.get_state() # 処理前の状態を保持
        self.logger.log(LogLevel.CALL, "ボタンリリース処理前に状態取得完了", {"状態": state})

        is_outside = not validation_result.has_coords # 検証結果を利用

        if state == ZoomState.CREATE:
            self.logger.log(LogLevel.INFO, "ズーム領域作成完了処理開始：作成関連の内部状態をリセット")
            self.logger.log(LogLevel.INFO, "リセット：作成関連の内部状態")

            if is_outside:
                self.logger.log(LogLevel.WARNING, "キャンセル：作成中に軸の外側でマウスボタンリリース")
                self.logger.log(LogLevel.CALL, "切断：motion_notify_event")
                self._disconnect_motion()
                self.logger.log(LogLevel.INFO, "キャンセル：ズーム領域作成")
                self.zoom_selector.cancel_zoom()
                return

            if event.button == MouseButton.LEFT:
                if self.start_x is not None and self.start_y is not None: # 開始座標がある場合
                    # リリースポイントが有効かどうかを確認（is_outside チェックで既に実行されているが、型チェッカーに必要）
                    if event.xdata is not None and event.ydata is not None: # リリースポイントが有効な場合
                        # 最終的なサイズを計算する
                        potential_width = abs(event.xdata - self.start_x)
                        potential_height = abs(event.ydata - self.start_y)

                        # 最終的なサイズが有効かどうかを確認
                        if self.rect_manager.is_valid_size(potential_width, potential_height):
                            self.logger.log(LogLevel.INFO, "ズーム領域作成終了", {
                                "button": event.button, "x": event.xdata, "y": event.ydata, "state": state})
                            # 最後の座標でサイズを確定させる（すでにmotionで更新されているが念のため）
                            self.rect_manager.temporary_creation(self.start_x, self.start_y, event.xdata, event.ydata)
                            self.logger.log(LogLevel.CALL, "ズーム領域：キャッシュ無効化開始")
                            self.zoom_selector.invalidate_rect_cache()
                            self.logger.log(LogLevel.INFO, "状態変更 to EDIT.")
                            self.state_handler.update_state(ZoomState.EDIT, {"action": "作成終了"})
                        else: # 最終サイズが無効なので作成をキャンセル
                            self.logger.log(LogLevel.WARNING, "ズーム領域作成失敗：最終サイズが無効")
                            self.logger.log(LogLevel.INFO, "状態変更 to NO_RECT.")
                            self.state_handler.update_state(ZoomState.NO_RECT, {"action": "作成失敗"})
                            self.rect_manager.delete_rect()
                            self.logger.log(LogLevel.CALL, "ズーム領域：キャッシュ無効化開始")
                            self.zoom_selector.invalidate_rect_cache()
                    else: # この else は、event.xdata/ydata が None であることに対応する
                        # is_outside チェックは先ほど返されるはずなので、作成をキャンセルする
                        self.logger.log(LogLevel.WARNING, "ズーム領域作成失敗：解放座標が無効")
                        self.logger.log(LogLevel.INFO, "状態変更 to NO_RECT.")
                        self.state_handler.update_state(ZoomState.NO_RECT, {"action": "作成失敗"})
                        self.rect_manager.delete_rect()
                        self.logger.log(LogLevel.CALL, "ズーム領域：キャッシュ無効化開始")
                        self.zoom_selector.invalidate_rect_cache()
                else:
                    self.logger.log(LogLevel.ERROR, "ズーム領域作成不可：開始座標なし")
                    self.logger.log(LogLevel.INFO, "状態変更 to NO_RECT.")
                    self.state_handler.update_state(ZoomState.NO_RECT, {"action": "作成失敗"})
                    # 存在する可能性のある四角形をクリアする（無いはずだが）
                    if self.rect_manager.get_properties():
                        self.rect_manager.delete_rect()
                        self.logger.log(LogLevel.CALL, "ズーム領域：キャッシュ無効化開始")
                        self.zoom_selector.invalidate_rect_cache()

                self._reset_create_state() # 作成関連の状態をリセット
                self.logger.log(LogLevel.INFO, "カーソル更新")
                self.cursor_manager.cursor_update(event, state=self.state_handler.get_state())
                self.canvas.draw_idle()

        elif state == ZoomState.ON_MOVE:
            if event.button == MouseButton.LEFT:
                self.rect_manager.edge_change_finishing()
                self.logger.log(LogLevel.INFO, "ズーム領域移動終了", {
                    "ボタン": event.button, "x": event.xdata, "y": event.ydata, "状態": state})
                self.logger.log(LogLevel.INFO, "状態変更 to EDIT.")
                self.state_handler.update_state(ZoomState.EDIT, {"action": "移動終了"})
                self.logger.log(LogLevel.CALL, "切断：motion_notify_event")
                self.logger.log(LogLevel.CALL, "リセット：移動関連の内部状態")
                self._reset_move_state()
                self.logger.log(LogLevel.INFO, "カーソル更新")
                self.cursor_manager.cursor_update(event, state=self.state_handler.get_state())
                self.logger.log(LogLevel.CALL, "ズーム領域：キャッシュ無効化開始")
                self.zoom_selector.invalidate_rect_cache()
                self.canvas.draw_idle()
                self._reset_move_state()

        elif state == ZoomState.RESIZING:
            if event.button == MouseButton.LEFT:
                self.logger.log(LogLevel.INFO, "ズーム領域リサイズ終了", {
                    "ボタン": event.button, "x": event.xdata, "y": event.ydata, "状態": state})
                self.rect_manager.edge_change_finishing()
                # リサイズ完了後も矩形が有効かチェック（小さくなりすぎなど）
                rect_props = self.rect_manager.get_properties()
                if rect_props and self.rect_manager.is_valid_size(rect_props[2], rect_props[3]):
                    self.logger.log(LogLevel.INFO, "リサイズ成功：状態変更 to EDIT")
                    self.state_handler.update_state(ZoomState.EDIT, {"action": "リサイズ終了"})
                else:
                    # リサイズの結果、矩形が無効になった場合はキャンセル扱いとするか、前の状態に戻すかは要検討
                    # ここではキャンセル（NO_RECT）にしている
                    self.logger.log(LogLevel.WARNING, "リサイズ中断：無効なサイズ")
                    self.logger.log(LogLevel.INFO, "状態変更 to NO_RECT.")
                    self.state_handler.update_state(ZoomState.NO_RECT, {"action": "リサイズ失敗"})
                    self.rect_manager.delete_rect()

                self.logger.log(LogLevel.CALL, "リセット：サイズ変更関連の内部状態")
                self._reset_resize_state()
                self.logger.log(LogLevel.CALL, "ズーム領域：キャッシュ無効化開始")
                self.zoom_selector.invalidate_rect_cache()
                self.logger.log(LogLevel.INFO, "カーソル更新")
                self.cursor_manager.cursor_update(event, state=self.state_handler.get_state())
                self.canvas.draw_idle()
                self._reset_resize_state()

        elif state == ZoomState.ROTATING:
            if event.button == MouseButton.LEFT:
                # --- 回転完了処理 ---
                self.logger.log(LogLevel.INFO, "ズーム領域回転終了", {
                    "ボタン": event.button, "x": event.xdata, "y": event.ydata, "状態": state})
                self.logger.log(LogLevel.INFO, "状態変更 to EDIT.")
                self.state_handler.update_state(ZoomState.EDIT, {"action": "回転終了"})
                self.logger.log(LogLevel.CALL, "切断：motion_notify_event")
                self._disconnect_motion()
                self.logger.log(LogLevel.CALL, "リセット：回転関連の内部状態")
                self._reset_rotate_state() # 回転状態をリセット
                self.logger.log(LogLevel.INFO, "カーソル更新")
                # Altキーの状態も渡す
                self.cursor_manager.cursor_update(event, state=self.state_handler.get_state(), is_rotating=self._alt_pressed)
                self.logger.log(LogLevel.CALL, "ズーム領域：キャッシュ無効化開始")
                self.zoom_selector.invalidate_rect_cache()
                self.canvas.draw_idle()

        # 最終的な状態でカーソルを更新
        final_state = self.state_handler.get_state() # 状態変更後の最終状態を取得
        self.logger.log(LogLevel.INFO, "カーソル更新開始：リリース時")
        self.cursor_manager.cursor_update(event, state=final_state, is_rotating=self._alt_pressed)
        self.canvas.draw_idle()

    def on_key_press(self, event: KeyEvent):
        """ キーボードが押された時の処理 """
        # キーイベントではマウス位置が不定なため、カーソル更新は on_motion に任せる
        # ESC でキャンセルした場合、ZoomSelector.cancel_zoom 内で set_default_cursor が呼ばれる
        if event.key == 'escape':
            state = self.state_handler.get_state()
            self.logger.log(LogLevel.CALL, "キー押下時の状態取得完了", {"状態": state.name})

            if state is ZoomState.EDIT:
                self.logger.log(LogLevel.INFO, f"ESC キー押下検出：ズーム領域キャンセル処理開始")
                self._disconnect_motion()
                self.zoom_selector.cancel_zoom()
                self.zoom_selector.invalidate_rect_cache()
                self.reset_internal_state()
                self.logger.log(LogLevel.INFO, "状態変更 to NO_RECT.")
                self.state_handler.update_state(ZoomState.NO_RECT, {"action": "ズーム領域キャンセル完了"})
                self.cursor_manager.set_default_cursor()
                self.canvas.draw_idle()

        # Alt キー処理 (回転モードの開始)
        elif event.key == 'alt':
            if not self._alt_pressed: # まだ押されていなければ
                self.logger.log(LogLevel.INFO, "Altキー押下検出：回転モード有効化")
                self._alt_pressed = True
                # EDIT状態の場合、カーソルを更新して回転の可能性を示す
                state = self.state_handler.get_state()
                if state == ZoomState.EDIT:
                    # モーションイベントがないとマウス位置が分からないため、
                    # connect_motion() または直近のイベント座標を使う必要があるが、
                    # ここでは on_motion が呼ばれた際に更新されることに期待する
                    self.logger.log(LogLevel.DEBUG, "EDIT状態でAlt押下。次のマウス移動でカーソル更新")
                    # 強制的に更新したい場合は工夫が必要
                    # self.cursor_manager.cursor_update(None, state=state, is_rotating=True) # イベントがない場合の例

    def on_key_release(self, event: KeyEvent):
        """ キーボードのキーが離された時の処理 """
        if event.key == 'alt':
            if self._alt_pressed: # 押されていた場合のみ
                self.logger.log(LogLevel.INFO, "Altキー解放検出：回転モード無効化")
                self._alt_pressed = False
                # EDIT状態の場合、カーソルを通常に戻す
                state = self.state_handler.get_state()
                if state == ZoomState.EDIT:
                     self.logger.log(LogLevel.DEBUG, "EDIT状態でAlt解放。次のマウス移動でカーソル更新")
                     # 強制的に更新したい場合は工夫が必要
                     # self.cursor_manager.cursor_update(None, state=state, is_rotating=False)

    def _calculate_angle(self, cx: float, cy: float, px: float, py: float) -> float:
        """ 中心点(cx, cy)から点(px, py)へのベクトル角度を計算（度単位） """
        return math.degrees(math.atan2(py - cy, px - cx))

    def reset_internal_state(self):
        """ 全ての内部状態をリセット """
        self._reset_create_state() # 移動関連の状態をリセット
        self._reset_move_state() # 移動関連の状態をリセット
        self._reset_resize_state() # リサイズ関連の状態をリセット
        self._reset_rotate_state() # 回転関連の状態をリセット
        self._alt_pressed = False # Altキーの状態をリセット
        self._disconnect_motion() # マウスモーションイベント切断

    def _reset_create_state(self):
        """ 作成関連の内部状態をリセット """
        self.start_x = None
        self.start_y = None
        self._create_logged = False

    def _reset_move_state(self):
        """ 移動関連の内部状態をリセット """
        self.move_start_x = None
        self.move_start_y = None
        self.rect_start_pos = None
        self._move_logged = False

    def _reset_resize_state(self):
        """ リサイズ関連の内部状態をリセット """
        self.resize_corner_index = None
        self.fixed_corner_pos = None
        self._resize_logged = False

    def _reset_rotate_state(self):
        """ 回転関連の内部状態をリセット """
        self.rotate_start_mouse_pos = None
        self.rotate_start_angle_vector = None
        self.rect_initial_angle = None
        self.rotate_center = None
        self._rotate_logged = False
