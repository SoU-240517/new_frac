import matplotlib.patches as patches
from matplotlib.axes import Axes
from typing import Optional, Tuple
from .debug_logger import DebugLogger
from .enums import LogLevel

class RectManager:
    """ 矩形(Rectangle)の描画と管理を行うクラス """
    def __init__(self, ax: Axes, logger: DebugLogger):
        self.logger = logger
        self.logger.log(LogLevel.INIT, "Initializing RectManager")
        self.ax = ax
        self.rect: Optional[patches.Rectangle] = None # 現在描画中の矩形オブジェクト

    def get_rect(self) -> Optional[patches.Rectangle]:
        """ 現在の矩形オブジェクトを取得 """
        self.logger.log(LogLevel.METHOD, "get_rect")
        return self.rect

    def create_rect_start(self, x: float, y: float):
        """ 新しい矩形の描画を開始 """
        self.logger.log(LogLevel.METHOD, "create_rect_start")
        if self.rect: # もし古い矩形が残っていたら消す
            self.clear()
        # 見た目を点線にする例
        self.rect = patches.Rectangle((x, y), 0, 0, linewidth=1, edgecolor='red', facecolor='none', linestyle='--')
        self.ax.add_patch(self.rect)
        self.logger.log(LogLevel.DEBUG, "Rectangle creation started", {"x": x, "y": y})

    def update_creation(self, start_x: float, start_y: float, current_x: float, current_y: float):
        """ ドラッグ中に矩形のサイズと位置を更新 """
        self.logger.log(LogLevel.METHOD, "update_creation")
        if not self.rect:
            return
        width = current_x - start_x
        height = current_y - start_y
        # 左上起点で幅と高さを設定
        self.rect.set_bounds(start_x, start_y, width, height)

    def finalize_creation(self, start_x: float, start_y: float, end_x: float, end_y: float) -> bool:
        """ 矩形の作成を完了 (マウスボタンを離した時) """
        self.logger.log(LogLevel.METHOD, "finalize_creation")
        if not self.rect:
            return False

        width = abs(end_x - start_x)
        height = abs(end_y - start_y)
        # 左下の座標を計算
        x = min(start_x, end_x)
        y = min(start_y, end_y)

        if width < 1e-6 or height < 1e-6: # 幅か高さがほぼゼロなら無効
            self.logger.log(LogLevel.WARNING, "Rectangle too small, clearing.", {"w": width, "h": height})
            self.clear()
            return False
        else:
            self.rect.set_bounds(x, y, width, height)
            # 見た目を実線に戻す例
            self.rect.set_linestyle('-')
            self.logger.log(LogLevel.INFO, "Rectangle finalized", {"x": x, "y": y, "w": width, "h": height})
            return True

    def clear(self):
        """ 矩形を削除 """
        self.logger.log(LogLevel.METHOD, "clear")
        if self.rect:
            self.rect.remove()
            self.rect = None
            self.logger.log(LogLevel.DEBUG, "Rectangle cleared")

    def get_properties(self) -> Optional[Tuple[float, float, float, float]]:
        """ 現在の矩形のプロパティ (x, y, width, height) を取得 """
        self.logger.log(LogLevel.METHOD, "get_properties")
        if self.rect:
            return (self.rect.get_x(), self.rect.get_y(),
                    self.rect.get_width(), self.rect.get_height())
        return None
