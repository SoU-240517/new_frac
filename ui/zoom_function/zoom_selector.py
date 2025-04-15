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
                                canvas=self.canvas)
        self.rect_manager = RectManager(ax, self.logger)
        # canvas.get_tk_widget() で Tkinter ウィジェットを取得
        # getattr を使用して Tk ウィジェットを安全に取得する
        # 利用できない場合はデフォルトで None になる
        tk_widget = getattr(self.canvas, 'get_tk_widget', lambda: None)()
        self.cursor_manager = CursorManager(tk_widget, self.logger)
        # Validator インスタンスを生成して EventHandler に渡す
        self.validator = EventValidator()
        self.event_handler = EventHandler(self,
                                          self.state_handler,
                                          self.rect_manager,
                                          self.cursor_manager,
                                          self.validator, # 生成したインスタンスを渡す
                                          self.logger,
                                          self.canvas)
        # CursorManager に ZoomSelector の参照を設定
        self.cursor_manager.set_zoom_selector(self)
        # StateHandler に EventHandler の参照を設定
        self.state_handler.event_handler = self.event_handler
        self.logger.log(LogLevel.INIT, "イベント接続")
        self.connect_events()

    def connect_events(self):
        """ イベントハンドラの接続（マウスモーション以外の全て） """
        self.logger.log(LogLevel.CALL, "接続開始：イベントハンドラ（マウス移動以外全て）")
        self.event_handler.connect()
        self.cursor_manager.set_default_cursor()

    def disconnect_events(self):
        """ 全イベントハンドラの切断 ★★★ 未使用 ★★★ """
        self.logger.log(LogLevel.CALL, "切断開始：全イベントハンドラ")
        self.event_handler.disconnect()
        self.logger.log(LogLevel.CALL, "切断時にデフォルトのカーソルを設定")
        self.cursor_manager.set_default_cursor()

    def cursor_inside_rect(self, event) -> bool:
        """ マウスカーソル位置がズーム領域内か判定する (キャッシュを使用) """
        if self._cached_rect_patch is None:
            self.logger.log(LogLevel.CALL, "ズーム領域のキャッシュなし：キャッシュを作成")
            self._cached_rect_patch = self.rect_manager.get_patch()
        if self._cached_rect_patch is not None:
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
            self.on_zoom_confirm(x, y, w, h, rotation_angle)
            self.rect_manager.delete_rect()
            self.invalidate_rect_cache()
            self.logger.log(LogLevel.INFO, "状態変更：NO_RECT")
            self.state_handler.update_state(ZoomState.NO_RECT, {"action": "決定"})
            self.cursor_manager.set_default_cursor()
        else:
            self.logger.log(LogLevel.WARNING, "決定不可：ズーム領域なし")

    def cancel_rect(self):
        """ ズーム領域を削除 """
        self.rect_manager.delete_rect()
        self.logger.log(LogLevel.INFO, "ズーム領域削除完了")

    def cancel_zoom(self):
        """ ズーム領域を削除してコールバックする """
        self.logger.log(LogLevel.INFO, "ズームキャンセル：コールバック呼出し")
        self.on_zoom_cancel()

    def reset(self):
        """ ZoomSelectorの状態をリセット """
        self.logger.log(LogLevel.CALL, "ZoomSelector リセット処理開始")
        self.rect_manager.delete_rect()
        self.invalidate_rect_cache()
        self.logger.log(LogLevel.INFO, "状態変更：NO_RECT")
        self.state_handler.update_state(ZoomState.NO_RECT, {"action": "リセット"})
        self.event_handler.reset_internal_state()
        self.cursor_manager.set_default_cursor()

    def invalidate_rect_cache(self):
        """ ズーム領域のキャッシュを無効化する """
        if self._cached_rect_patch is not None:
            self._cached_rect_patch = None

    def pointer_near_corner(self, event) -> Optional[int]:
        """
        マウスカーソルがズーム領域の角に近いかどうかを判定し、
        近い場合はその角のインデックス (0-3) を返す
        - 許容範囲 tol は矩形の短辺の10% (最小0.02)
        - 角のインデックス: 0:左上, 1:右上, 2:左下, 3:右下 (回転前の定義に基づく)
        """
        # ZoomSelector が持つ validator インスタンスを使用
        validation_result = self.validator.validate_event(event, self.ax, self.logger)
        # 角の判定には Axes 内で座標があることが必要 (is_fully_valid でチェック)
        if not validation_result.is_fully_valid:
            return None
        rect_props = self.rect_manager.get_properties()
        center = self.rect_manager.get_center()
        angle_deg = self.rect_manager.get_rotation()
        if rect_props is None or center is None:
            self.logger.log(LogLevel.DEBUG, "角判定不可: ズーム領域または中心なし")
            return None
        x, y, width, height = rect_props
        cx, cy = center
        angle_rad = np.radians(angle_deg)
        # 回転前の角の座標 (中心からの相対座標)
        half_w, half_h = width / 2, height / 2
        corners_relative = [
            (-half_w, -half_h), # 左下 (描画上の左上に対応する場合あり) -> インデックス2相当？
            ( half_w, -half_h), # 右下 -> インデックス3相当？
            (-half_w,  half_h), # 左上 -> インデックス0相当？
            ( half_w,  half_h)  # 右上 -> インデックス1相当？
        ]
        # Note: Rectangleの(x,y)は左下だが、
        # リサイズハンドルは視覚的な左上から0,1,2,3としたい場合が多い
        # EventHandler 側の corner_index の意味と合わせる必要がある
        # ここでは EventHandler の期待 (0:左上, 1:右上, 2:左下, 3:右下) に合わせるため、
        # 座標リストの順序を調整する
        corners_unrotated_relative = [
            (-half_w,  half_h), # 左上 (Index 0)
            ( half_w,  half_h), # 右上 (Index 1)
            (-half_w, -half_h), # 左下 (Index 2)
            ( half_w, -half_h)  # 右下 (Index 3)
        ]
        # 回転後の絶対座標を計算
        cos_a, sin_a = np.cos(angle_rad), np.sin(angle_rad)
        rotated_corners = []
        for rel_x, rel_y in corners_unrotated_relative:
            rotated_x = rel_x * cos_a - rel_y * sin_a + cx
            rotated_y = rel_x * sin_a + rel_y * cos_a + cy
            rotated_corners.append((rotated_x, rotated_y))
        # 許容範囲の計算
        abs_width = abs(width)
        abs_height = abs(height)
        # width または height が 0 の場合に備える
        if abs_width < 1e-9 or abs_height < 1e-9:
             min_dim = 0.0
        else:
            min_dim = min(abs_width, abs_height)
        tol = max(0.1 * min_dim, 0.02) # 短辺の10% or 最小許容範囲
        # 各回転後コーナーとの距離を計算
        for i, (corner_x, corner_y) in enumerate(rotated_corners):
            # event.xdata/ydata は検証済みなので None でないはず
            distance = np.hypot(event.xdata - corner_x, event.ydata - corner_y)
            if distance < tol:
                self.logger.log(LogLevel.DEBUG, f"カーソルに近い角 {i} (距離: {distance:.3f} < 許容範囲: {tol:.3f})")
                return i # 近い角のインデックスを返す
        return None # どの角にも近くない
