from matplotlib.backend_bases import MouseEvent, MouseButton
from typing import Optional, TYPE_CHECKING, Tuple
from .enums import LogLevel

# 他のクラスの型ヒントのためにインポート (循環参照回避)
if TYPE_CHECKING:
    from .zoom_selector import ZoomSelector
    from .zoom_state_handler import ZoomStateHandler
    from .rect_manager import RectManager
    from .cursor_manager import CursorManager
    from .event_validator import EventValidator
    from .debug_logger import DebugLogger

# Enumは直接インポート
from .enums import ZoomState, LogLevel

class EventHandler:
    """ matplotlibのイベントを処理し、各コンポーネントに指示を出すクラス """
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
        self.validator = validator
        self.logger = logger
        self.canvas = canvas

        # ログ出力フラグ
        self._create_logged = False
        self._move_logged = False
        self._resize_logged = False

        # イベント接続ID
        self._cid_press: Optional[int] = None
        self._cid_release: Optional[int] = None
        self._cid_motion: Optional[int] = None
        self._cid_key_press: Optional[int] = None

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

    def _connect_motion(self):
        """ motion_notify_event を接続 """
        if self._cid_motion is None: # モーションが切断されている場合は接続
            self._cid_motion = self.canvas.mpl_connect('motion_notify_event', self.on_motion)
            self.logger.log(LogLevel.CALL, "motion_notify_event Connected.")

    def _disconnect_motion(self):
        """ motion_notify_event を切断 """
        if self._cid_motion is not None: # モーションが接続されている場合は切断
            self.canvas.mpl_disconnect(self._cid_motion)
            self._cid_motion = None
            self.logger.log(LogLevel.CALL, "motion_notify_event Disconnected.")

    def connect(self):
        """ イベントハンドラを接続 """
        if self._cid_press is None: # すでに接続されている場合は何もしない
            self._cid_press = self.canvas.mpl_connect('button_press_event', self.on_press)
            self._cid_release = self.canvas.mpl_connect('button_release_event', self.on_release)
            self._cid_key_press = self.canvas.mpl_connect('key_press_event', self.on_key_press)

    def disconnect(self):
        """ イベントハンドラを切断 """
        if self._cid_press is not None: # マウスボタン押下イベントが接続されている場合は切断
            self.canvas.mpl_disconnect(self._cid_press)
            self._cid_press = None

        if self._cid_release is not None: # マウスボタンリリースイベントが接続されている場合は切断
            self.canvas.mpl_disconnect(self._cid_release)
            self._cid_release = None

        self.logger.log(LogLevel.CALL, "motion_notify_event Disconnected.")
        self._disconnect_motion()

        if self._cid_key_press is not None: # キーボード押下イベントが接続されている場合は切断
            self.canvas.mpl_disconnect(self._cid_key_press)
            self._cid_key_press = None

    def on_press(self, event: MouseEvent):
        """ マウスボタンが押された時の処理 """
        # ... (基本的な検証は変更なし) ...
        if not self.validator.validate_basic(event, self.zoom_selector.ax, self.logger):
            self.logger.log(LogLevel.DEBUG, "Verification failed.: Apply basic event")
            return
        self.logger.log(LogLevel.DEBUG, "Verification passed.: Apply basic event")

        if event.xdata is None or event.ydata is None:
            self.logger.log(LogLevel.CALL, "No coordinate data. Press events ignored.")
            return
        self.logger.log(LogLevel.CALL, "Coordinate data available. Processing continues.")

        state = self.state_handler.get_state()
        self.logger.log(LogLevel.CALL, "Get state.", {"state": state.name})

        if state == ZoomState.NO_RECT:
            if event.button == MouseButton.LEFT:
                # 矩形作成開始
                self.logger.log(LogLevel.INFO, "State changed to CREATE.")
                self.state_handler.update_state(ZoomState.CREATE, {"action": "create_start"})

                self.logger.log(LogLevel.CALL, "Begins a new rectangle.", {
                    "button": event.button, "x": event.xdata, "y": event.ydata, "state": state})
                self.start_x, self.start_y = event.xdata, event.ydata

                self.logger.log(LogLevel.INFO, "Setup initial state of rectangle.", {"x": self.start_x, "y": self.start_y})
                self.rect_manager.setup_rect(self.start_x, self.start_y)

                self.logger.log(LogLevel.CALL, "Rectangle cache clear.")
                self.zoom_selector.invalidate_rect_cache() # キャッシュを無効化

                self._connect_motion() # 移動中のマウス追跡を開始

                self.logger.log(LogLevel.INFO, "Cursor update.")
                self.cursor_manager.cursor_update(event)

                self._create_logged = False # 新規作成ログフラグをリセット
                self.canvas.draw_idle()


        elif state == ZoomState.EDIT:
            if event.button == MouseButton.LEFT:
                # マウスカーソルがズーム領域の角の近くか判定
                corner_index = self.zoom_selector.pointer_near_corner(event)
                if corner_index is not None:
                    # リサイズ開始
                    self.logger.log(LogLevel.INFO, f"Resize started from corner {corner_index}.")
                    self.logger.log(LogLevel.INFO, "State changed to RESIZING.")
                    self.state_handler.update_state(ZoomState.RESIZING, {"action": "resize_start", "corner": corner_index})
                    self.resize_corner_index = corner_index

                    # 固定される対角の座標を計算して保持
                    rect_props = self.rect_manager.get_properties()
                    if rect_props:
                        x, y, w, h = rect_props
                        x0, y0 = min(x, x + w), min(y, y + h)
                        x1, y1 = max(x, x + w), max(y, y + h)
                        corners = [(x0, y0), (x1, y0), (x0, y1), (x1, y1)]
                        # 対角のインデックス（0<->3, 1<->2）
                        fixed_corner_idx = 3 - corner_index
                        self.fixed_corner_pos = corners[fixed_corner_idx]
                        self.logger.log(LogLevel.CALL, f"Fixed corner {fixed_corner_idx} at {self.fixed_corner_pos}")

                    self._connect_motion()

                    self.logger.log(LogLevel.INFO, "Cursor update.")
                    self.cursor_manager.cursor_update(event, near_corner_index=self.resize_corner_index)
                    self._resize_logged = False # リサイズログフラグをリセット

                elif self.zoom_selector.cursor_inside_rect(event):
                    # 矩形移動開始
                    self.logger.log(LogLevel.INFO, "State changed to MOVE.")
                    self.state_handler.update_state(ZoomState.MOVE, {"action": "move_start"})

                    self.move_start_x, self.move_start_y = event.xdata, event.ydata # 移動開始時のマウス座標
                    rect_props = self.rect_manager.get_properties()
                    if rect_props:
                        self.rect_start_pos = (rect_props[0], rect_props[1]) # (x, y)

                    self._connect_motion()
                    self.logger.log(LogLevel.INFO, "Cursor update.")
                    self.cursor_manager.cursor_update(event) # 移動カーソル
                    self._move_logged = False

    def on_motion(self, event: MouseEvent) -> None:
        """ マウスが動いた時の処理 """
        if event.inaxes != self.zoom_selector.ax:
            self.logger.log(LogLevel.CALL, "Mouse moved outside axes. Motion events ignored.")
            return
        if event.xdata is None or event.ydata is None:
            self.logger.log(LogLevel.CALL, "No coordinate data. Motion events ignored.")
            return

        state = self.state_handler.get_state()
        self.logger.log(LogLevel.CALL, "Get state.", {"state": state.name})

        if state == ZoomState.CREATE:
            if event.button == MouseButton.LEFT:
                # 矩形作成中のサイズ更新
                if self.start_x is not None and self.start_y is not None:
                    if not self._create_logged:
                        self.logger.log(LogLevel.INFO, "Rectangle updating during creation.")
                        self._create_logged = True
                    self.rect_manager.update_rect_size(self.start_x, self.start_y, event.xdata, event.ydata)
                    self.logger.log(LogLevel.CALL, "Update: Rect size...")

                    self.logger.log(LogLevel.CALL, "Rectangle cache clear.")
                    self.zoom_selector.invalidate_rect_cache() # キャッシュを無効化

                self.canvas.draw_idle()

        elif state == ZoomState.EDIT:
            self.logger.log(LogLevel.CALL, "Checking if pointer is near a corner.")
            corner_index = self.zoom_selector.pointer_near_corner(event)
            self.logger.log(LogLevel.INFO, "Cursor update.")
            self.cursor_manager.cursor_update(event, near_corner_index=corner_index)

        elif state == ZoomState.MOVE:
            if event.button == MouseButton.LEFT:
                # 矩形移動中の処理
                if not self._move_logged:
                    self.logger.log(LogLevel.INFO, "Rectangle move started.", {
                        "button": event.button, "x": event.xdata, "y": event.ydata, "state": state})
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
                    self.logger.log(LogLevel.CALL, "Move rectangle to.", {"x": new_rect_x, "y": new_rect_y})

                    self.logger.log(LogLevel.CALL, "Rectangle cache clear.")
                    self.zoom_selector.invalidate_rect_cache()

                    self.canvas.draw_idle()

        elif state == ZoomState.RESIZING:
            if event.button == MouseButton.LEFT:
                # 矩形リサイズ中の処理
                if not self._resize_logged:
                    self.logger.log(LogLevel.INFO, "Rectangle resize started.", {
                        "button": event.button, "x": event.xdata, "y": event.ydata, "state": state, "corner": self.resize_corner_index})
                    self._resize_logged = True

                if self.fixed_corner_pos is not None:
                    fixed_x, fixed_y = self.fixed_corner_pos
                    current_x, current_y = event.xdata, event.ydata

                    # 固定点と現在のマウス位置から矩形を更新
                    self.rect_manager.update_rect_from_corners(fixed_x, fixed_y, current_x, current_y)
                    self.logger.log(LogLevel.CALL, f"Update rect from fixed corner ({fixed_x:.2f}, {fixed_y:.2f}) to mouse ({current_x:.2f}, {current_y:.2f})")

                    self.logger.log(LogLevel.CALL, "Rectangle cache clear.")
                    self.zoom_selector.invalidate_rect_cache()

                    self.canvas.draw_idle()

    def on_release(self, event: MouseEvent) -> None:
        """ マウスボタンが離された時の処理 """
        state = self.state_handler.get_state()
        self.logger.log(LogLevel.CALL, "Get state.", {"state": state.name})

        # 座標が取れない場合の処理（Axes外でのリリースなど）
        is_outside = event.xdata is None or event.ydata is None

        if state == ZoomState.CREATE:
            if is_outside:
                self.logger.log(LogLevel.WARNING, "Mouse released outside axes during creation, cancelling.")
                self.logger.log(LogLevel.CALL, "motion_notify_event Disconnected.")
                self._disconnect_motion()
                self.logger.log(LogLevel.INFO, "Zoom operation cancelled.")
                self.zoom_selector.cancel_zoom()
                return

            if event.button == MouseButton.LEFT:
                if self.start_x is not None and self.start_y is not None:
                    # リリースポイントが有効かどうかを確認します（is_outside チェックで既に実行されていますが、型チェッカーに必要です）
                    if event.xdata is not None and event.ydata is not None:
                        # 最終的なサイズを計算する
                        potential_width = abs(event.xdata - self.start_x)
                        potential_height = abs(event.ydata - self.start_y)

                        # 最終的なサイズが有効かどうかを確認します
                        if self.rect_manager.is_valid_size(potential_width, potential_height):
                            self.logger.log(LogLevel.INFO, "Temporary rectangle creation completed.", {
                                "button": event.button, "x": event.xdata, "y": event.ydata, "state": state})
                            # 最後の座標でサイズを確定させる（すでにmotionで更新されているが念のため）
                            self.rect_manager.temporary_creation(self.start_x, self.start_y, event.xdata, event.ydata) # Now safe
                            self.logger.log(LogLevel.CALL, "Rectangle cache clear.")
                            self.zoom_selector.invalidate_rect_cache()
                            self.logger.log(LogLevel.INFO, "State changed to EDIT.")
                            self.state_handler.update_state(ZoomState.EDIT, {"action": "create_end"})
                        else:
                            # 最終サイズが無効なので作成をキャンセル
                            self.logger.log(LogLevel.WARNING, "Rectangle creation failed (final size invalid).")
                            self.logger.log(LogLevel.INFO, "State changed to NO_RECT.")
                            self.state_handler.update_state(ZoomState.NO_RECT, {"action": "create_fail"})
                            self.rect_manager.clear()
                            self.logger.log(LogLevel.CALL, "Rectangle cache clear.")
                            self.zoom_selector.invalidate_rect_cache()
                    else:
                        # この else は、event.xdata/ydata が None であることに対応します。
                        # is_outside チェックは先ほど返されるはずです。作成をキャンセルします。
                        self.logger.log(LogLevel.WARNING, "Rectangle creation failed (release coordinates invalid).")
                        self.logger.log(LogLevel.INFO, "State changed to NO_RECT.")
                        self.state_handler.update_state(ZoomState.NO_RECT, {"action": "create_fail"})
                        self.rect_manager.clear()
                        self.logger.log(LogLevel.CALL, "Rectangle cache clear.")
                        self.zoom_selector.invalidate_rect_cache()
                else:
                    self.logger.log(LogLevel.ERROR, "Cannot finalize rectangle, start coordinates are missing.")
                    self.logger.log(LogLevel.INFO, "State changed to NO_RECT.")
                    self.state_handler.update_state(ZoomState.NO_RECT, {"action": "create_error"})
                    # 存在する可能性のある四角形をクリアします
                    if self.rect_manager.get_properties():
                        self.rect_manager.clear()
                        self.logger.log(LogLevel.CALL, "Rectangle cache clear.")
                        self.zoom_selector.invalidate_rect_cache()

                self._reset_create_state() # 作成関連の状態をリセット
                self.logger.log(LogLevel.INFO, "Cursor update.")
                self.cursor_manager.cursor_update(event)
                self.canvas.draw_idle()


        elif state == ZoomState.MOVE:
            if event.button == MouseButton.LEFT:
                self.logger.log(LogLevel.INFO, "Rectangle move finished.", {
                    "button": event.button, "x": event.xdata, "y": event.ydata, "state": state})
                self.logger.log(LogLevel.INFO, "State changed to EDIT.")
                self.state_handler.update_state(ZoomState.EDIT, {"action": "move_end"})
                self.logger.log(LogLevel.CALL, "motion_notify_event Disconnected.")
                self.logger.log(LogLevel.CALL, "Resets internal state related to movement.")
                self._reset_move_state()
                self.logger.log(LogLevel.INFO, "Cursor update.")
                self.cursor_manager.cursor_update(event)
                self.logger.log(LogLevel.CALL, "Rectangle cache clear.")
                self.zoom_selector.invalidate_rect_cache()
                self.canvas.draw_idle()

        elif state == ZoomState.RESIZING:
            if event.button == MouseButton.LEFT:
                self.logger.log(LogLevel.INFO, "Rectangle resize finished.", {
                    "button": event.button, "x": event.xdata, "y": event.ydata, "state": state})

                # リサイズ完了後も矩形が有効かチェック（小さくなりすぎなど）
                rect_props = self.rect_manager.get_properties()
                if rect_props and self.rect_manager.is_valid_size(rect_props[2], rect_props[3]):
                    self.logger.log(LogLevel.INFO, "State changed to EDIT.")
                    self.state_handler.update_state(ZoomState.EDIT, {"action": "resize_end"})
                    self.logger.log(LogLevel.CALL, "Resize successful, returning to EDIT state.")
                else:
                    # リサイズの結果、矩形が無効になった場合はキャンセル扱いとするか、前の状態に戻すかは要検討
                    # ここではキャンセル（NO_RECT）にしている
                    self.logger.log(LogLevel.WARNING, "Rectangle resize resulted in invalid size, cancelling.")
                    self.logger.log(LogLevel.INFO, "State changed to NO_RECT.")
                    self.state_handler.update_state(ZoomState.NO_RECT, {"action": "resize_fail"})
                    self.rect_manager.clear() # 矩形をクリア

                self.logger.log(LogLevel.CALL, "Resets the internal state related to resizing.")
                self._reset_resize_state() # リサイズ関連の状態をリセット
                self.logger.log(LogLevel.CALL, "Rectangle cache clear.")
                self.zoom_selector.invalidate_rect_cache() # キャッシュクリア
                self.logger.log(LogLevel.INFO, "Cursor update.")
                self.cursor_manager.cursor_update(event) # カーソルを更新
                self.canvas.draw_idle()

    def on_key_press(self, event: MouseEvent):
        """ キーボードが押された時の処理 """
        self.logger.log(LogLevel.INFO, "Key press detected", {"key": event.key})

        if event.key == 'escape': # ESCキーが押された場合
            state = self.state_handler.get_state()
            self.logger.log(LogLevel.CALL, "Get state.", {"state": state.name})

            if state is ZoomState.EDIT:
                self.logger.log(LogLevel.INFO, f"Operation cancelled by ESC key in state: {state.name}.")

                self._disconnect_motion()

                self.logger.log(LogLevel.INFO, "Zoom operation cancelled.")
                self.zoom_selector.cancel_zoom() # cancel_zoom で状態リセットと矩形クリア

                self.logger.log(LogLevel.CALL, "Resets internal state related to movement.")
                self._reset_move_state() # 移動状態もリセット

                self.logger.log(LogLevel.INFO, "State changed to NO_RECT.")
                self.state_handler.update_state(ZoomState.NO_RECT, {"action": "create_end"})

                self.canvas.draw_idle()

    def reset_internal_state(self):
        """ イベントハンドラ内部の状態をリセット """
        self.start_x = None
        self.start_y = None
        self.logger.log(LogLevel.CALL, "Resets internal state related to movement.")
        self._reset_move_state() # 移動関連の状態もリセット
        self.logger.log(LogLevel.CALL, "Resets the internal state related to resizing.")
        self._reset_resize_state() # リサイズ関連の状態もリセット
        self._create_logged = False
        self._move_logged = False
        self._resize_logged = False # リサイズログフラグもリセット
        self._disconnect_motion() # 念のため motion も切断
        pass

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

    def _reset_create_state(self):
        """ 作成関連の内部状態をリセット """
        self.start_x = None
        self.start_y = None
        self._create_logged = False
