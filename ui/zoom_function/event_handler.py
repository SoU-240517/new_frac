from matplotlib.backend_bases import Event, MouseButton
from typing import Optional, TYPE_CHECKING

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
    def __init__(self, selector: 'ZoomSelector', state_handler: 'ZoomStateHandler',
                 rect_manager: 'RectManager', cursor_manager: 'CursorManager',
                 validator: 'EventValidator', logger: 'DebugLogger', canvas):
        print("初期化 : CLASS→ EventHandler : FILE→ event_handler.py")
        self.selector = selector
        self.state_handler = state_handler
        self.rect_manager = rect_manager
        self.cursor_manager = cursor_manager
        self.validator = validator
        self.logger = logger
        self.canvas = canvas

        # イベント接続ID
        self._cid_press: Optional[int] = None
        self._cid_release: Optional[int] = None
        self._cid_motion: Optional[int] = None
        self._cid_key_press: Optional[int] = None

        # ドラッグ開始位置
        self.start_x: Optional[float] = None
        self.start_y: Optional[float] = None

    def connect(self):
        """ イベントハンドラを接続 """
        print("接続 : connect : CLASS→ EventHandler : FILE→ event_handler.py")
        if self._cid_press is None:
            self._cid_press = self.canvas.mpl_connect('button_press_event', self.on_press)
            self._cid_release = self.canvas.mpl_connect('button_release_event', self.on_release)
            self._cid_motion = self.canvas.mpl_connect('motion_notify_event', self.on_motion)
            self._cid_key_press = self.canvas.mpl_connect('key_press_event', self.on_key_press)
            self.logger.log(LogLevel.INFO, "Event handlers connected.")

    def disconnect(self):
        """ イベントハンドラを切断 """
        print("切断 : disconnect : CLASS→ EventHandler : FILE→ event_handler.py")
        if self._cid_press is not None:
            self.canvas.mpl_disconnect(self._cid_press)
            self.canvas.mpl_disconnect(self._cid_release)
            self.canvas.mpl_disconnect(self._cid_motion)
            self.canvas.mpl_disconnect(self._cid_key_press)
            self._cid_press = None
            self._cid_release = None
            self._cid_motion = None
            self._cid_key_press = None
            self.logger.log(LogLevel.INFO, "Event handlers disconnected.")

    def on_press(self, event: Event):
        """ マウスボタンが押された時の処理 """
        print("マウスボタン押下 : on_press : CLASS→ EventHandler : FILE→ event_handler.py")
         # event.xdata や event.ydata が None の場合があるため、先にチェック
        if event.xdata is None or event.ydata is None:
            return
        # validate_basic の中で event.button is not None はチェック済み
        if not self.validator.validate_basic(event, self.selector.ax) or event.button != MouseButton.LEFT:
            return # 対象Axes外、または左ボタン以外は無視

        state = self.state_handler.get_state()
        self.logger.log(LogLevel.DEBUG, "Mouse press detected", {"button": event.button, "x": event.xdata, "y": event.ydata, "state": state})

        if state == ZoomState.NO_RECT:
            # 矩形作成開始
            self.start_x, self.start_y = event.xdata, event.ydata
            self.rect_manager.create_rect_start(self.start_x, self.start_y)
            self.state_handler.update_state(ZoomState.CREATE)
            self.cursor_manager.update(event)
            self.canvas.draw_idle() # 再描画を要求

    def on_motion(self, event: Event):
        """ マウスが動いた時の処理 """
        print("マウス移動 : on_motion : CLASS→ EventHandler : FILE→ event_handler.py")
        if event.inaxes != self.selector.ax and self.state_handler.get_state() != ZoomState.CREATE:
             return
        # ドラッグ中でも座標が取れないことがある(ウィンドウ外など)
        if event.xdata is None or event.ydata is None:
            return

        state = self.state_handler.get_state()

        if state == ZoomState.CREATE:
            if self.start_x is not None and self.start_y is not None:
                # 矩形を作成中なら更新
                self.rect_manager.update_creation(self.start_x, self.start_y, event.xdata, event.ydata)
                self.canvas.draw_idle() # 再描画を要求

    def on_release(self, event: Event):
        """ マウスボタンが離された時の処理 """
        print("マウスボタン離す : on_release : CLASS→ EventHandler : FILE→ event_handler.py")
        # validate_basic はボタンチェックを含むので不要だが、念のため
        if event.button != MouseButton.LEFT:
            return
        # 座標が取れない場合がある(ウィンドウ外で離した場合など)
        if event.xdata is None or event.ydata is None:
             # ドラッグ開始点があれば、そこで終了したとみなすか、キャンセルするか？
             # 今回はキャンセル扱い（何もしないで状態を戻す）にする
             if self.state_handler.get_state() == ZoomState.CREATE:
                  self.logger.log(LogLevel.WARNING, "Mouse released outside axes during creation, cancelling.")
                  self.selector.cancel_zoom() # キャンセル処理を呼ぶ
             return


        state = self.state_handler.get_state()
        self.logger.log(LogLevel.DEBUG, "Mouse release detected", {"button": event.button, "x": event.xdata, "y": event.ydata, "state": state})

        if state == ZoomState.CREATE:
            if self.start_x is not None and self.start_y is not None:
                # 矩形作成完了
                success = self.rect_manager.finalize_creation(self.start_x, self.start_y, event.xdata, event.ydata)
                if success:
                    self.selector.confirm_zoom() # ログ出力とコールバック呼び出し
                else:
                    self.state_handler.update_state(ZoomState.NO_RECT)

            self.start_x = None
            self.start_y = None
            self.cursor_manager.update(event)
            self.canvas.draw_idle()

    def on_key_press(self, event: Event):
        """ キーボードが押された時の処理 """
        print("キーボタン押下 : on_key_press : CLASS→ EventHandler : FILE→ event_handler.py")
        self.logger.log(LogLevel.DEBUG, "Key press detected", {"key": event.key})
        if event.key == 'escape':
            state = self.state_handler.get_state()
            if state == ZoomState.CREATE:
                self.logger.log(LogLevel.INFO, "Rectangle creation cancelled by ESC.")
                # cancel_zoomの中で clear や状態更新が行われる
                self.selector.cancel_zoom()
                self.canvas.draw_idle() # 再描画を要求

    def reset_internal_state(self):
        """ イベントハンドラ内部の状態をリセット """
        print("イベントハンドラ内部状態リセット : reset_internal_state : CLASS→ EventHandler : FILE→ event_handler.py")
        self.start_x = None
        self.start_y = None
        self.logger.log(LogLevel.DEBUG, "EventHandler internal state reset.")
