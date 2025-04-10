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
        self.zoom_selector = zoom_selector # ZoomSelectorのインスタンスを保持
        self.state_handler = state_handler
        self.rect_manager = rect_manager
        self.cursor_manager = cursor_manager
        self.validator = validator
        self.logger = logger
        self.canvas = canvas

        # ログ出力フラグ
        self._create_logged = False
        self._move_logged = False

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
        self.rect_start_pos: Optional[Tuple[float, float]] = None # 移動開始時の矩形左下座標 (x, y)

    def _connect_motion(self):
        """ motion_notify_event を接続 """
        if self._cid_motion is None: # モーションが切断されている場合は接続
            self._cid_motion = self.canvas.mpl_connect('motion_notify_event', self.on_motion)
            self.logger.log(LogLevel.DEBUG, "motion_notify_event Connected.")

    def _disconnect_motion(self):
        """ motion_notify_event を切断 """
        if self._cid_motion is not None: # モーションが接続されている場合は切断
            self.canvas.mpl_disconnect(self._cid_motion)
            self._cid_motion = None
            self.logger.log(LogLevel.DEBUG, "motion_notify_event Disconnected.")

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

        self._disconnect_motion()

        if self._cid_key_press is not None: # キーボード押下イベントが接続されている場合は切断
            # キーボードイベントは切断しない場合もあるので、Noneにするだけ
            self.canvas.mpl_disconnect(self._cid_key_press)
            self._cid_key_press = None

    def on_press(self, event: MouseEvent):
        """ マウスボタンが押された時の処理 """
        if not self.validator.validate_basic(event, self.zoom_selector.ax, self.logger):
            self.logger.log(LogLevel.DEBUG, "Verification failed.: Apply basic event")
            return
        self.logger.log(LogLevel.DEBUG, "Verification passed.: Apply basic event")

        if event.xdata is None or event.ydata is None:
            self.logger.log(LogLevel.DEBUG, "No coordinate data. Press events ignored.")
            return
        self.logger.log(LogLevel.DEBUG, "Coordinate data available. Processing continues.")

        state = self.state_handler.get_state()
        self.logger.log(LogLevel.DEBUG, "Current state.", {"state": state.name})

        if state == ZoomState.NO_RECT:
            if event.button == MouseButton.LEFT:
                # 矩形作成開始
                self.logger.log(LogLevel.INFO, "State changed to CREATE.")
                self.state_handler.update_state(ZoomState.CREATE, {"action": "create_start"})

                self.logger.log(LogLevel.INFO, "Begins a new rectangle.", {
                    "button": event.button, "x": event.xdata, "y": event.ydata, "state": state})
                self.start_x, self.start_y = event.xdata, event.ydata

                self.logger.log(LogLevel.DEBUG, "Setup initial state of rectangle.", {"x": self.start_x, "y": self.start_y})
                self.rect_manager.setup_rect(self.start_x, self.start_y)

                self.logger.log(LogLevel.DEBUG, "Rectangle cache clear.")
                self.zoom_selector.invalidate_rect_cache() # キャッシュを無効化

                self._connect_motion() # 移動中のマウス追跡を開始

                self.logger.log(LogLevel.INFO, "Cursor update.")
                self.cursor_manager.cursor_update(event)

                self._create_logged = False # 新規作成ログフラグをリセット
                self.canvas.draw_idle()

        elif state == ZoomState.EDIT:
            if event.button == MouseButton.LEFT and self.zoom_selector.cursor_inside_rect(event):
                # 矩形移動開始
                # ... (移動開始時には矩形自体は変更されないので、キャッシュ無効化は不要) ...
                self.logger.log(LogLevel.INFO, "State changed to MOVE.")
                self.state_handler.update_state(ZoomState.MOVE, {"action": "move_start"})

                self.move_start_x, self.move_start_y = event.xdata, event.ydata # 移動開始時のマウス座標

                self.logger.log(LogLevel.DEBUG, "Get rect properties.")
                rect_props = self.rect_manager.get_properties() # 矩形のプロパティを取得 (x, y, width, height)

                if rect_props:
                    self.rect_start_pos = (rect_props[0], rect_props[1]) # (x, y)

                self._connect_motion()

                self.logger.log(LogLevel.INFO, "Cursor update.")
                self.cursor_manager.cursor_update(event) # カーソル形状を更新 (fleurなど)

                self._move_logged = False # 移動ログフラグをリセット

    def on_motion(self, event: MouseEvent) -> None:
        """ マウスが動いた時の処理 """
        if event.inaxes != self.zoom_selector.ax:
            # カーソルがAxes外に出た場合の処理
            self.logger.log(LogLevel.DEBUG, "Mouse moved outside axes. Motion events ignored.")
            return
        if event.xdata is None or event.ydata is None:
            # カーソルがAxes外に出た場合の処理
            self.logger.log(LogLevel.DEBUG, "No coordinate data. Motion events ignored.")
            return

        state = self.state_handler.get_state()
        self.logger.log(LogLevel.DEBUG, "Current state.", {"state": state.name})

        if state == ZoomState.CREATE:
            if event.button == MouseButton.LEFT:
                # 矩形作成中のサイズ更新
                if self.start_x is not None and self.start_y is not None:
                    if not self._create_logged:
                        self.logger.log(LogLevel.INFO, "Rectangle updating during creation.")
                        self._create_logged = True
                    self.rect_manager.update_rect_size(self.start_x, self.start_y, event.xdata, event.ydata)
                    self.logger.log(LogLevel.DEBUG, "Update: Rect size...")

                    self.logger.log(LogLevel.DEBUG, "Rectangle cache clear.")
                    self.zoom_selector.invalidate_rect_cache() # キャッシュを無効化

                self.canvas.draw_idle()
        elif state == ZoomState.EDIT:
            # 編集モード中はカーソル形状の更新のみ
            self.logger.log(LogLevel.INFO, "Cursor update.")
            self.cursor_manager.cursor_update(event)
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
                    self.logger.log(LogLevel.DEBUG, "Move rectangle to.", {"x": new_rect_x, "y": new_rect_y})

                    self.logger.log(LogLevel.DEBUG, "Rectangle cache clear.")
                    self.zoom_selector.invalidate_rect_cache()

                    self.canvas.draw_idle()

    def on_release(self, event: MouseEvent) -> None:
        """ マウスボタンが離された時の処理 """
        state = self.state_handler.get_state()
        self.logger.log(LogLevel.DEBUG, "Current state.", {"state": state.name})

        # 座標が取れない場合の処理 (Axes外でのリリースなど)
        if event.xdata is None or event.ydata is None:
            if state == ZoomState.CREATE:
                self.logger.log(LogLevel.WARNING, "Mouse released outside axes during creation, cancelling.")
                self._disconnect_motion()

                self.logger.log(LogLevel.INFO, "Zoom operation cancelled.")
                self.zoom_selector.cancel_zoom()

            elif state == ZoomState.MOVE:
                # 移動中にAxes外でリリースされた場合、移動を完了させるかキャンセルするかは仕様による
                # ここでは移動を完了させる（EDIT状態に戻す）
                self.logger.log(LogLevel.WARNING, "Mouse released outside axes during move, finalizing move.")

                self.logger.log(LogLevel.INFO, "State changed to EDIT.")
                self.state_handler.update_state(ZoomState.EDIT, {"action": "move_end"})

                self._disconnect_motion()

                self.logger.log(LogLevel.DEBUG, "Resets internal state related to movement.")
                self._reset_move_state() # 移動関連の変数をリセット

                self.logger.log(LogLevel.INFO, "Cursor update.")
                self.cursor_manager.cursor_update(event) # カーソルを更新

                self.logger.log(LogLevel.DEBUG, "Rectangle cache clear.")
                self.zoom_selector.invalidate_rect_cache() # 必要であれば追加

            return

        # 通常のリリース処理
        if state == ZoomState.CREATE:
            if event.button == MouseButton.LEFT:
                # 矩形作成完了
#                self._disconnect_motion()
                if self.start_x is not None and self.start_y is not None: # 開始座標がある場合

                    self.logger.log(LogLevel.DEBUG, "Get rect properties.")
                    rect_props = self.rect_manager.get_properties()

                    # 矩形を確定させる
                    if rect_props and self.rect_manager.is_valid_size(rect_props[2], rect_props[3]):

                        self.logger.log(LogLevel.INFO, "Temporary rectangle creation completed.", {
                            "button": event.button, "x": event.xdata, "y": event.ydata, "state": state})
                        self.rect_manager.temporary_creation(self.start_x, self.start_y, event.xdata, event.ydata)

                        self.logger.log(LogLevel.DEBUG, "Rectangle cache clear.")
                        self.zoom_selector.invalidate_rect_cache()

                        self.logger.log(LogLevel.INFO, "State changed to EDIT.")
                        self.state_handler.update_state(ZoomState.EDIT, {"action": "create_end"})
                    else:
                        # 矩形が小さすぎるなどで作成失敗した場合は矩形を消す
                        self.logger.log(LogLevel.WARNING, "Rectangle creation failed (e.g., too small).")

                        self.logger.log(LogLevel.INFO, "State changed to NO_RECT.")
                        self.state_handler.update_state(ZoomState.NO_RECT, {"action": "create_fail"})

                        self.logger.log(LogLevel.INFO, "Clearing rectangle due to invalid size.")
                        self.rect_manager.clear()

                        self.logger.log(LogLevel.DEBUG, "Rectangle cache clear.")
                        self.zoom_selector.invalidate_rect_cache()

                else:
                    # 開始座標がない異常系 (通常は起こらないはず)
                    self.logger.log(LogLevel.ERROR, "Cannot finalize rectangle, start coordinates are missing.")
                    self.logger.log(LogLevel.INFO, "State changed to NO_RECT.")
                    self.state_handler.update_state(ZoomState.NO_RECT, {"action": "create_error"})

                # 状態リセット
                self.start_x = None
                self.start_y = None
                self._create_logged = False

                self.logger.log(LogLevel.INFO, "Cursor update.")
                self.cursor_manager.cursor_update(event)

                self.canvas.draw_idle()

        elif state == ZoomState.MOVE:
            if event.button == MouseButton.LEFT:
                # 矩形移動完了
                self.logger.log(LogLevel.INFO, "Rectangle move finished.", {
                    "button": event.button, "x": event.xdata, "y": event.ydata, "state": state})

                self.logger.log(LogLevel.INFO, "State changed to EDIT.")
                self.state_handler.update_state(ZoomState.EDIT, {"action": "move_end"})

                self.logger.log(LogLevel.DEBUG, "Resets internal state related to movement.")
                self._reset_move_state() # 移動関連の変数をリセット

                self.logger.log(LogLevel.INFO, "Cursor update.")
                self.cursor_manager.cursor_update(event) # カーソルを更新 (EDIT状態のカーソルへ)

                self.logger.log(LogLevel.DEBUG, "Rectangle cache clear.")
                self.zoom_selector.invalidate_rect_cache() # 必要であれば追加

                self.canvas.draw_idle()

    def on_key_press(self, event: MouseEvent):
        """ キーボードが押された時の処理 """
        self.logger.log(LogLevel.INFO, "Key press detected", {"key": event.key})

        if event.key == 'escape': # ESCキーが押された場合
            state = self.state_handler.get_state()
            self.logger.log(LogLevel.DEBUG, "Current state.", {"state": state.name})

            if state is ZoomState.EDIT:
                self.logger.log(LogLevel.INFO, f"Operation cancelled by ESC key in state: {state.name}.")

                self._disconnect_motion()

                self.logger.log(LogLevel.INFO, "Zoom operation cancelled.")
                self.zoom_selector.cancel_zoom() # cancel_zoom で状態リセットと矩形クリア

                self.logger.log(LogLevel.DEBUG, "Resets internal state related to movement.")
                self._reset_move_state() # 移動状態もリセット

                self.logger.log(LogLevel.INFO, "State changed to NO_RECT.")
                self.state_handler.update_state(ZoomState.NO_RECT, {"action": "create_end"})

                self.canvas.draw_idle()

    def reset_internal_state(self):
        """ イベントハンドラ内部の状態をリセット """
        self.start_x = None
        self.start_y = None
        self._reset_move_state() # 移動関連の状態もリセット
        self._create_logged = False
        self._move_logged = False
        self._disconnect_motion() # 念のため motion も切断
        pass

    def _reset_move_state(self):
        """ 移動関連の内部状態をリセット """
        self.move_start_x = None
        self.move_start_y = None
        self.rect_start_pos = None
        self._move_logged = False
