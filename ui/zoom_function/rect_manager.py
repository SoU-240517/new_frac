from hmac import new
from math import e
import matplotlib.patches as patches
from matplotlib.axes import Axes
from typing import Optional, Tuple
from .debug_logger import DebugLogger
from .enums import LogLevel

class RectManager:
    """ ズーム領域(Rectangle)の描画と管理を行うクラス """
    def __init__(self, ax: Axes, logger: DebugLogger):
        self.logger = logger
        self.logger.log(LogLevel.INIT, "RectManager")
        self.ax = ax
        self.rect: Optional[patches.Rectangle] = None # 現在描画中のズーム領域オブジェクト

    def get_rect(self) -> Optional[patches.Rectangle]:
        """ 現在のズーム領域を取得 """
        self.logger.log(LogLevel.DEBUG, "Gets the current rectangle information.")
        return self.rect

    def setup_rect(self, x: float, y: float):
        """ ズーム領域の初期状態をセットアップ """
        self.rect = patches.Rectangle(
            (x, y), 0, 0,
            linewidth=1, edgecolor='white', facecolor='none', linestyle='--') # 点線
        self.ax.add_patch(self.rect)


    def update_rect_size(self, start_x: float, start_y: float, current_x: float, current_y: float):
        """ ドラッグ中にズーム領域のサイズを更新 """
        if not self.rect:
            return
        width = current_x - start_x
        height = current_y - start_y
        self.rect.set_bounds(start_x, start_y, width, height) # 左上起点で幅と高さを設定
        self.logger.log(LogLevel.DEBUG, "Update: Rect size.")

    def is_valid_size(self, width: float, height: float) -> bool:
        """ 矩形の幅と高さが有効か (小さすぎないか) をチェック """
        is_valid = width <= 1e-6 or height <= 1e-6
        return is_valid

    def temporary_creation(self, start_x: float, start_y: float, end_x: float, end_y: float) -> bool:
        """ 仮のズーム領域を暫定 """
        width = abs(end_x - start_x)
        height = abs(end_y - start_y)
        # 左下の座標を計算
        x = min(start_x, end_x)
        y = min(start_y, end_y)

        if self.rect:
            self.rect.set_bounds(x, y, width, height)
            self.rect.set_linestyle('-') # 実線に変更
            self.logger.log(LogLevel.DEBUG, "Finalized temporary rectangle.", {"x": x, "y": y, "w": width, "h": height})
            return True
        else:
            # rect オブジェクトが存在しない場合 (通常は setup_rect が呼ばれているはず)
            self.logger.log(LogLevel.ERROR, "Cannot finalize rectangle, rect object does not exist.")
            return False

    def move_rect_to(self, new_x: float, new_y: float) -> None:
        """ ズーム領域を指定された座標に移動 """
        if self.rect:
            # --- 追加: 移動後のサイズもチェックする (オプション) ---
            # width = self.rect.get_width()
            # height = self.rect.get_height()
            # if self._is_valid_size(width, height): # サイズが変わらない移動なら不要かも
            # --- ここまで ---
                self.rect.set_xy((new_x, new_y)) # 左下の座標を更新
                self.logger.log(LogLevel.DEBUG, "Move rectangle to.", {"x": new_x, "y": new_y})

    def clear(self):
        """ ズーム領域を削除 """
        if self.rect:
            self.logger.log(LogLevel.DEBUG, "Rectangle cleared.")
            self.rect.remove()
            self.rect = None

    def get_properties(self) -> Optional[Tuple[float, float, float, float]]:
        """ 現在のズーム領域のプロパティ (x, y, width, height) を取得 """
        if self.rect:
            return (self.rect.get_x(), self.rect.get_y(),
                    self.rect.get_width(), self.rect.get_height())
        return None
