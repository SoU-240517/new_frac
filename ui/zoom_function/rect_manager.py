from hmac import new
from math import e
import matplotlib.patches as patches
from matplotlib.axes import Axes
from typing import Optional, Tuple
from .debug_logger import DebugLogger
from .enums import LogLevel

class RectManager:
    """ ズーム領域の描画と管理を行うクラス """
    def __init__(self,
                 ax: Axes,
                 logger: DebugLogger):

        self.logger = logger
        self.logger.log(LogLevel.INIT, "RectManager")
        self.ax = ax
        self.rect: Optional[patches.Rectangle] = None # 現在描画中のズーム領域オブジェクト

    def get_rect(self) -> Optional[patches.Rectangle]:
        """ 現在のズーム領域を取得 """
        return self.rect

    def setup_rect(self, x: float, y: float):
        """ ズーム領域の初期状態をセットアップ """
        self.clear() # 既存の矩形があれば削除
        self.rect = patches.Rectangle(
            (x, y), 0, 0,
            linewidth=1, edgecolor='white', facecolor='none', linestyle='--') # 点線
        self.ax.add_patch(self.rect)

    def update_rect_size(self, start_x: float, start_y: float, current_x: float, current_y: float):
        """ ドラッグ中にズーム領域のサイズを更新 (主に矩形作成時に使用) """
        if not self.rect:
            return
        width = current_x - start_x
        height = current_y - start_y
        # set_bounds は（x, y, width, height）を設定する
        # start_x, start_y が左下になるとは限らないため、必要に応じて調整
        new_x = min(start_x, current_x)
        new_y = min(start_y, current_y)
        new_width = abs(width)
        new_height = abs(height)
        self.rect.set_bounds(new_x, new_y, new_width, new_height)

    def update_rect_from_corners(self, corner1_x: float, corner1_y: float, corner2_x: float, corner2_y: float):
        """ 2つの対角座標から矩形を更新（主にリサイズ時に使用）"""
        if not self.rect:
            return
        new_x = min(corner1_x, corner2_x)
        new_y = min(corner1_y, corner2_y)
        new_width = abs(corner1_x - corner2_x)
        new_height = abs(corner1_y - corner2_y)
        self.rect.set_bounds(new_x, new_y, new_width, new_height)
        self.logger.log(LogLevel.DEBUG, f"Updated rect from corners: ({new_x:.2f}, {new_y:.2f}), w={new_width:.2f}, h={new_height:.2f}")


    def is_valid_size(self, width: float, height: float, min_threshold: float = 1e-6) -> bool:
        """ 矩形の幅と高さが有効か（小さすぎないか）をチェック """
        # 幅と高さが両方とも閾値より大きい場合に有効とする
        is_valid = abs(width) > min_threshold and abs(height) > min_threshold
        if not is_valid:
            self.logger.log(LogLevel.DEBUG, f"Invalid size check: width={width}, height={height}, threshold={min_threshold}")
        return is_valid

    def temporary_creation(self, start_x: float, start_y: float, end_x: float, end_y: float) -> bool:
        """ 仮のズーム領域を確定し、実線に変更 """
        width = abs(end_x - start_x)
        height = abs(end_y - start_y)

        # 左下の座標を計算
        x = min(start_x, end_x)
        y = min(start_y, end_y)

        if self.rect:
            # サイズが有効かチェック
            if self.is_valid_size(width, height):
                self.rect.set_bounds(x, y, width, height)
                self.rect.set_linestyle('-') # 実線に変更
                self.logger.log(LogLevel.SUCCESS, f"Finalized temporary rectangle: ({x:.2f}, {y:.2f}), w={width:.2f}, h={height:.2f}")
                return True
            else:
                self.logger.log(LogLevel.WARNING, "Temporary creation failed: Invalid size.")
                self.clear() # 無効なサイズならクリア
                return False
        else:
            # rect オブジェクトが存在しない場合（通常は setup_rect が呼ばれているはず）
            self.logger.log(LogLevel.ERROR, "Cannot finalize rectangle, rect object does not exist.")
            return False

    def move_rect_to(self, new_x: float, new_y: float) -> None:
        """ ズーム領域を指定された座標に移動 """
        if self.rect:
                self.rect.set_xy((new_x, new_y)) # 左下の座標を更新
                self.logger.log(LogLevel.DEBUG, f"Moved rectangle to ({new_x:.2f}, {new_y:.2f})")

    def clear(self):
        """ ズーム領域を削除 """
        if self.rect:
            try:
                self.rect.remove()
                self.logger.log(LogLevel.DEBUG, "Rectangle removed from axes.")
            except ValueError:
                # すでに削除されている場合など
                self.logger.log(LogLevel.WARNING, "Failed to remove rectangle (possibly already removed).")
            finally:
                self.rect = None


    def get_properties(self) -> Optional[Tuple[float, float, float, float]]:
        """ 現在のズーム領域のプロパティ（x, y, width, height）を取得 """
        if self.rect:
            # Rectangle のプロパティは常に width >= 0, height >= 0 となるように
            # set_bounds で調整されているはずだが、念のため確認
            x = self.rect.get_x()
            y = self.rect.get_y()
            w = self.rect.get_width()
            h = self.rect.get_height()
            return (x, y, w, h)
        return None
