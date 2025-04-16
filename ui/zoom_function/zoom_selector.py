from matplotlib.axes import Axes
from typing import Callable, Optional, Tuple
import numpy as np
import matplotlib.transforms as transforms # 回転計算用
from .enums import ZoomState, LogLevel
from .event_validator import EventValidator, ValidationResult
from .zoom_state_handler import ZoomStateHandler
from .rect_manager import RectManager
from .cursor_manager import CursorManager
from .debug_logger import DebugLogger
from .event_handler import EventHandler
import matplotlib.patches as patches # キャッシュの型ヒント用

class ZoomSelector:
    """ マウスドラッグで矩形を描画し、回転やリサイズを行う機能を持つクラス"""
    def __init__(self,
                 ax: Axes,
                 on_zoom_confirm: Callable[[float, float, float, float, float], None],
                 on_zoom_cancel: Callable[[], None],
                 logger: DebugLogger):
        self.logger = logger
        self.logger.log(LogLevel.INIT, "ZoomSelector")
        self.ax = ax
        self.canvas = ax.figure.canvas
        self.on_zoom_confirm = on_zoom_confirm
        self.on_zoom_cancel = on_zoom_cancel
        self._cached_rect_patch: Optional[patches.Rectangle] = None
        self.state_handler = ZoomStateHandler(
                               initial_state=ZoomState.NO_RECT,
                               logger=self.logger,
                               canvas=self.canvas) # canvas を渡す
        self.rect_manager = RectManager(ax, self.logger)
        tk_widget = getattr(self.canvas, 'get_tk_widget', lambda: None)()
        self.cursor_manager = CursorManager(tk_widget, self.logger)
        self.validator = EventValidator()
        self.event_handler = EventHandler(self,
                                          self.state_handler,
                                          self.rect_manager,
                                          self.cursor_manager,
                                          self.validator,
                                          self.logger,
                                          self.canvas) # canvas を渡す
        # CursorManager に ZoomSelector の参照を設定
        self.cursor_manager.set_zoom_selector(self)
        # StateHandler に EventHandler の参照を設定 (循環参照に注意しつつ)
        self.state_handler.event_handler = self.event_handler
        self.logger.log(LogLevel.INIT, "イベント接続")
        self.connect_events()

    def connect_events(self):
        """ イベントハンドラの接続（マウスモーション以外の全て） """
        self.logger.log(LogLevel.CALL, "接続開始：イベントハンドラ（マウス移動以外全て）")
        self.event_handler.connect()
        self.cursor_manager.set_default_cursor()

    def cursor_inside_rect(self, event) -> bool:
        """ マウスカーソル位置がズーム領域内か判定する (キャッシュを使用) """
        if self._cached_rect_patch is None:
            self.logger.log(LogLevel.CALL, "ズーム領域のキャッシュなし：キャッシュを作成")
            self._cached_rect_patch = self.rect_manager.get_patch()
        if self._cached_rect_patch is not None:
            # 矩形が見えない場合は False を返すように修正
            if not self._cached_rect_patch.get_visible():
                 self.logger.log(LogLevel.DEBUG, "カーソル：ズーム領域 外 (非表示)")
                 return False
            contains, _ = self._cached_rect_patch.contains(event)
            if contains:
                self.logger.log(LogLevel.DEBUG, "カーソル：ズーム領域 内")
                return True
            else:
                self.logger.log(LogLevel.DEBUG, "カーソル：ズーム領域 外")
                return False
        self.logger.log(LogLevel.DEBUG, "ズーム領域なし：カーソル判定不可")
        return False # キャッシュ更新後も None の場合

    def confirm_zoom(self):
        """ ズーム確定処理 """
        self.logger.log(LogLevel.CALL, "ズーム確定処理開始")
        rect_props_tuple = self.rect_manager.get_properties()
        rotation_angle = self.rect_manager.get_rotation()
        if rect_props_tuple:
            x, y, w, h = rect_props_tuple
            self.logger.log(LogLevel.INFO, "ズーム確定：コールバック呼出し", {
                "x": x, "y": y, "w": w, "h": h, "angle": rotation_angle})
            # --- 履歴クリアを追加 ---
            self.event_handler.clear_edit_history()
            # --- ここまで追加 ---
            self.on_zoom_confirm(x, y, w, h, rotation_angle) # コールバック呼び出し
            self.rect_manager.delete_rect() # 矩形削除
            self.invalidate_rect_cache() # キャッシュ無効化
            self.state_handler.update_state(ZoomState.NO_RECT, {"action": "ズーム確定完了"})
            self.cursor_manager.set_default_cursor() # カーソルをデフォルトに
            self.event_handler.reset_internal_state() # EventHandlerの状態もリセット
        else:
            self.logger.log(LogLevel.WARNING, "決定不可：ズーム領域なし")

    def cancel_rect(self):
        """ ズーム領域編集をキャンセルし、矩形を削除する """
        self.logger.log(LogLevel.INFO, "ズーム領域編集キャンセル開始")
        # --- 履歴クリアを追加 ---
        self.event_handler.clear_edit_history()
        # --- ここまで追加 ---
        self.rect_manager.delete_rect() # 矩形を削除
        self.invalidate_rect_cache() # キャッシュを無効化
        # 状態をNO_RECTに戻す必要があれば、EventHandler側で行うか、ここで明示的に行う
        # self.state_handler.update_state(ZoomState.NO_RECT, {"action": "編集キャンセル"}) # EventHandler側で行う想定
        # self.cursor_manager.set_default_cursor() # EventHandler側で行う想定
        self.logger.log(LogLevel.INFO, "ズーム領域編集キャンセル完了 (矩形削除)")

    def cancel_zoom(self):
        """ ズーム確定操作自体をキャンセルする（MainWindow側の処理を呼び出す） """
        self.logger.log(LogLevel.INFO, "ズーム確定キャンセル：コールバック呼出し")
        # --- 履歴クリアを追加 ---
        self.event_handler.clear_edit_history()
        # --- ここまで追加 ---
        self.rect_manager.delete_rect() # 存在する場合、矩形も削除
        self.invalidate_rect_cache()
        self.on_zoom_cancel() # MainWindow の on_zoom_cancel を呼び出す
        # 状態リセットなどは MainWindow 側で行われる想定

    def reset(self):
        """ ZoomSelectorの状態をリセット（描画リセットボタンなどから呼ばれる） """
        self.logger.log(LogLevel.CALL, "ZoomSelector リセット処理開始")
        # --- 履歴クリアを追加 ---
        self.event_handler.clear_edit_history()
        # --- ここまで追加 ---
        self.rect_manager.delete_rect()
        self.invalidate_rect_cache()
        self.state_handler.update_state(ZoomState.NO_RECT, {"action": "リセット"})
        self.event_handler.reset_internal_state() # EventHandlerの内部状態もリセット
        self.cursor_manager.set_default_cursor()
        # reset時には通常、MainWindow側で再描画がトリガーされる

    def invalidate_rect_cache(self):
        """ ズーム領域のキャッシュを無効化する """
        if self._cached_rect_patch is not None:
             self.logger.log(LogLevel.DEBUG, "ズーム領域キャッシュ無効化")
             self._cached_rect_patch = None

    def pointer_near_corner(self, event) -> Optional[int]:
        """
        マウスカーソルがズーム領域の角に近いかどうかを判定し、
        近い場合はその角のインデックス (0-3) を返す
        """
        validation_result = self.validator.validate_event(event, self.ax, self.logger)
        if not validation_result.is_fully_valid:
            return None

        # 回転後の角座標を取得
        rotated_corners = self.rect_manager.get_rotated_corners()
        if rotated_corners is None:
            self.logger.log(LogLevel.DEBUG, "角判定不可: 回転後の角座標なし")
            return None

        # 許容範囲の計算
        rect_props = self.rect_manager.get_properties()
        if rect_props is None or rect_props[2] <= 0 or rect_props[3] <= 0:
             self.logger.log(LogLevel.DEBUG, "角判定不可: 矩形プロパティ無効またはサイズゼロ")
             return None
        width, height = rect_props[2], rect_props[3]
        min_dim = min(width, height)
        # 画面上のピクセル単位での許容範囲を考慮した方が良い場合もある
        # 例: tol_pixels = 5
        # disp_coords = self.ax.transData.transform([(0,0), (min_dim, min_dim)])
        # dist_pixels = np.sqrt(((disp_coords[1] - disp_coords[0])**2).sum())
        # tol = tol_pixels * min_dim / dist_pixels if dist_pixels > 0 else 0.02
        tol = max(0.1 * min_dim, 0.02) # 短辺の10% or 最小許容範囲 (データ座標系)
        self.logger.log(LogLevel.DEBUG, f"角判定の許容範囲(tol): {tol:.4f}")


        # 各回転後コーナーとの距離を計算
        for i, (corner_x, corner_y) in enumerate(rotated_corners):
            if event.xdata is None or event.ydata is None: continue # 型ガード
            distance = np.hypot(event.xdata - corner_x, event.ydata - corner_y)
            if distance < tol:
                self.logger.log(LogLevel.DEBUG, f"カーソルに近い角 {i} (距離: {distance:.3f} < 許容範囲: {tol:.3f})")
                return i # 近い角のインデックスを返す

        return None # どの角にも近くない
