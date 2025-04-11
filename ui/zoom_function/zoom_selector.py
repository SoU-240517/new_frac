from matplotlib.axes import Axes
from typing import Callable
import numpy as np
from .enums import ZoomState, LogLevel
from .event_validator import EventValidator
from .zoom_state_handler import ZoomStateHandler
from .rect_manager import RectManager
from .cursor_manager import CursorManager
from .debug_logger import DebugLogger
from .event_handler import EventHandler

class ZoomSelector:
    """ マウスドラッグで矩形を描画する機能を持つクラス"""
    def __init__(self,
                ax: Axes,
                on_zoom_confirm: Callable[[float, float, float, float], None],
                on_zoom_cancel: Callable[[], None],
                logger: DebugLogger):

        self.logger = logger # logger をインスタンス変数として保持
        self.logger.log(LogLevel.INIT, "ZoomSelector")
        self.ax = ax # 描画対象の Axes オブジェクト
        self.canvas = ax.figure.canvas # 描画対象の Figure の Canvas オブジェクト
        self.on_zoom_confirm = on_zoom_confirm # ユーザーが指定するコールバック関数
        self.on_zoom_cancel = on_zoom_cancel # ユーザーが指定するコールバック関数
        self._cached_rect_props = None # 矩形情報のキャッシュ

        # --- 各コンポーネントの初期化 ---
        self.state_handler = ZoomStateHandler(
                                initial_state=ZoomState.NO_RECT,
                                logger=self.logger,
                                canvas=self.canvas)

        self.rect_manager = RectManager(ax, self.logger)
        self.cursor_manager = CursorManager(self.canvas, self.state_handler, self, self.logger)
        self.validator = EventValidator()

        # EventHandler に他のコンポーネントへの参照を渡す
        self.event_handler = EventHandler(self,
                                        self.state_handler,
                                        self.rect_manager,
                                        self.cursor_manager,
                                        self.validator,
                                        self.logger, # 引数で受け取った logger を渡す
                                        self.canvas)

        self.state_handler.event_handler = self.event_handler # StateHandler に EventHandler の参照を設定
        # --- 初期化ここまで ---

        self.logger.log(LogLevel.CALL, "Connect events in initial state.")
        self.connect_events()

    def connect_events(self):
        """ イベントハンドラの接続 """
        self.logger.log(LogLevel.CALL, "Connect event handler.")
        self.event_handler.connect() # EventHandlerに他のコンポーネントへの参照を渡す

        self.logger.log(LogLevel.CALL, "Cursor update.")
        self.cursor_manager.cursor_update()

    def disconnect_events(self):
        """ イベントハンドラの切断 """
        self.logger.log(LogLevel.CALL, "All event handlers disconnected.")
        self.event_handler.disconnect() # EventHandlerに他のコンポーネントへの参照を渡す

        self.logger.log(LogLevel.CALL, "Cursor reset.")
        self.cursor_manager.cursor_reset()

    def cursor_inside_rect(self, event) -> bool:
        """ マウスカーソル位置がズーム領域内か判定する (キャッシュを使用) """
        if self._cached_rect_props is None:
            self.logger.log(LogLevel.CALL, "Rectangle cache miss. Fetching rectangle properties.")
            self.logger.log(LogLevel.CALL, "Gets the current rectangle information.")
            self._cached_rect_props = self.rect_manager.get_rect()

        if self._cached_rect_props is not None:
            contains, _ = self._cached_rect_props.contains(event)
            return contains

        # キャッシュ更新後も None の場合（get_rect が None を返した場合）
        self.logger.log(LogLevel.WARNING, "No rectangle properties available even after cache update.")
        return False

    def confirm_zoom(self):
        """ ズーム領域決定 """
        self.logger.log(LogLevel.CALL, "Get property.")
        # rect_managerから最新のプロパティを取得
        rect_props_tuple = self.rect_manager.get_properties()

        if rect_props_tuple:
            self.logger.log(LogLevel.INFO, "Zoom rectangle confirmed. Callback Invocation.", {
                "x": rect_props_tuple[0], "y": rect_props_tuple[1], "w": rect_props_tuple[2], "h": rect_props_tuple[3]})
            self.on_zoom_confirm(rect_props_tuple[0], rect_props_tuple[1], rect_props_tuple[2], rect_props_tuple[3])

            self.logger.log(LogLevel.INFO, "State changed to NO_RECT.")
            self.state_handler.update_state(ZoomState.NO_RECT, {"action": "confirm"})

            self.logger.log(LogLevel.INFO, "Cursor update.")
            self.cursor_manager.cursor_update()
            self.invalidate_rect_cache() # 矩形がなくなったのでキャッシュをクリア
        else:
            self.logger.log(LogLevel.WARNING, "Confirm attempted but no valid rectangle exists.")

    def cancel_zoom(self):
        """ (内部用) キャンセル時に呼ばれる (主にESCキー or 外部からの呼び出し) """
        self.logger.log(LogLevel.CALL, "Rectangle cleared.")
        self.rect_manager.clear()

        self.logger.log(LogLevel.CALL, "Rectangle cache clear.")
        self.invalidate_rect_cache() # 矩形がクリアされたのでキャッシュをクリア

        self.logger.log(LogLevel.INFO, "State changed to NO_RECT.")
        self.state_handler.update_state(ZoomState.NO_RECT, {"action": "cancel"})

        self.logger.log(LogLevel.CALL, "EventHandler internal state reset.")
        self.event_handler.reset_internal_state() # 開始座標などもリセット

        self.logger.log(LogLevel.INFO, "Cursor update.")
        self.cursor_manager.cursor_update()

        self.logger.log(LogLevel.INFO, "Zoom rectangle canceled. Callback Invocation.")
        self.on_zoom_cancel()

    def reset(self):
        """ ZoomSelectorの状態をリセット """
        self.logger.log(LogLevel.CALL, "Rectangle cleared.")
        self.rect_manager.clear()

        self.logger.log(LogLevel.CALL, "Rectangle cache clear.")
        self.invalidate_rect_cache() # 矩形がクリアされたので、キャッシュもクリア

        self.logger.log(LogLevel.INFO, "State changed to NO_RECT.")
        self.state_handler.update_state(ZoomState.NO_RECT, {"action": "reset"})

        self.logger.log(LogLevel.INFO, "Resets the internal state of the event handler.")
        self.event_handler.reset_internal_state()

        self.logger.log(LogLevel.INFO, "Cursor update.")
        self.cursor_manager.cursor_update()

        # reset時もキャンセルコールバックを呼ぶか、あるいは別のコールバックを用意するかは設計次第
        # self.on_zoom_cancel()

    def invalidate_rect_cache(self):
        """ 矩形情報のキャッシュを無効化する """
        if self._cached_rect_props is not None:
            self._cached_rect_props = None

    def pointer_near_corner(self, event):
        """
        マウスカーソルがズーム領域の角に近いかどうかを判定し、近い場合はその角のインデックスを返す
        - 許容範囲 tol は矩形の短辺の10% (最小0.2)。
        - **角のインデックス:** 0:左上, 1:右上, 2:左下, 3:右下
        """
        rect_props_tuple = self.rect_manager.get_properties()
        if rect_props_tuple is None:
            self.logger.log(LogLevel.ERROR, "No rectangle exists.")
            return None # 矩形がない場合は None

        x, y, width, height = rect_props_tuple

        if event.xdata is None or event.ydata is None: # イベント座標がNoneの場合は判定不可
            self.logger.log(LogLevel.ERROR, "Pointer event coordinates are None (likely outside axes).")
            return None

        # 幅や高さが負の場合も考慮して、実際の左上、右下座標を計算
        x0 = min(x, x + width)
        y0 = min(y, y + height)
        x1 = max(x, x + width)
        y1 = max(y, y + height)
        abs_width = x1 - x0
        abs_height = y1 - y0

        min_dim = min(abs_width, abs_height) # 許容範囲の計算（短辺の10%、ただし最小値は設定）

        # 画面上のピクセル単位での許容範囲を考慮した方が良い場合もある
        # ここではデータ座標系での相対的な許容範囲としていうる
        tol = max(0.1 * min_dim, 0.02) # 短辺の10% or 最小許容範囲（値は調整が必要な場合あり）
        self.logger.log(LogLevel.DEBUG, f"Rectangle dimensions: w={abs_width:.2f}, h={abs_height:.2f}. Tolerance: {tol:.2f}")

        # 角の座標リスト (左上, 右上, 左下, 右下)
        corners = [(x0, y0), (x1, y0), (x0, y1), (x1, y1)]

        for i, (cx, cy) in enumerate(corners):
            distance = np.hypot(event.xdata - cx, event.ydata - cy)
            self.logger.log(LogLevel.DEBUG, f"Corner {i} ({cx:.2f}, {cy:.2f}), Distance: {distance:.2f}")
            if distance < tol:
                self.logger.log(LogLevel.SUCCESS, f"Pointer is near corner {i}.")
                return i # 近い角のインデックスを返す

        self.logger.log(LogLevel.DEBUG, "Pointer is not near any corner.")
        return None # どの角にも近くない場合は None
