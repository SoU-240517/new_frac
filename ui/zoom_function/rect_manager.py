import numpy as np
import matplotlib.patches as patches
import matplotlib.transforms as transforms
from matplotlib.axes import Axes
from typing import Optional, Tuple
from .debug_logger import DebugLogger
from .enums import LogLevel
#from encodings.punycode import T
#from hmac import new
#from math import e

class RectManager:
    """ ズーム領域を表す矩形 (Rectangle) の管理クラス """
    MIN_WIDTH = 0.01 # 許容される最小幅 (データ座標系)
    MIN_HEIGHT = 0.01 # 許容される最小高さ (データ座標系)

    def __init__(self,
                 ax: Axes,
                 logger: DebugLogger):

        self.logger = logger
        self.logger.log(LogLevel.INIT, "RectManager")

        self.ax = ax
        self.rect: Optional[patches.Rectangle] = None
        self._angle: float = 0.0

    def get_rect(self) -> Optional[patches.Rectangle]:
        """ 現在のズーム領域を取得 """
        return self.rect

    def setup_rect(self, x: float, y: float):
        """ 新しいズーム領域の初期設定 (設置サイズ 0：回転なし) """
        self.rect = patches.Rectangle(
            (x, y), 0, 0,
            linewidth=1, edgecolor='gray', facecolor='none', linestyle='--', visible=True)
        self.ax.add_patch(self.rect)
        self.logger.log(LogLevel.DEBUG, "初期のズーム領域設置完了", {"x": x, "y": y})

    def setting_rect_size(self, start_x: float, start_y: float, current_x: float, current_y: float):
        """ ズーム領域のサイズと位置を更新 (作成中：回転なし) """
        if not self.rect:
            self.logger.log(LogLevel.ERROR, "ズーム領域なし：サイズ更新不可")
            return

        width = abs(current_x - start_x)
        height = abs(current_y - start_y)
        x = min(start_x, current_x)
        y = min(start_y, current_y)

        self.rect.set_width(width)
        self.rect.set_height(height)
        self.rect.set_xy((x, y))
        self.rect.set_transform(self.ax.transData)

    def edge_change_editing(self):
        """ ズーム領域のエッジ変更 (灰色：破線) """
        if not self.rect:
            self.logger.log(LogLevel.ERROR, "ズーム領域なし：エッジ変更不可")
            return
        self.rect.set_edgecolor('gray')
        self.rect.set_linestyle('--')

    def edge_change_finishing(self):
        """ ズーム領域のエッジ変更 (白：実線) """
        if not self.rect:
            self.logger.log(LogLevel.ERROR, "ズーム領域なし：エッジ変更不可")
            return
        self.rect.set_edgecolor('white')
        self.rect.set_linestyle('-')

    def resize_rect_from_corners(self, fixed_x_rotated: float, fixed_y_rotated: float, current_x: float, current_y: float):
        """ 固定された回転後の角と現在のマウス位置からズーム領域を更新 (リサイズ中、回転考慮) """
        if not self.rect:
            self.logger.log(LogLevel.ERROR, "リサイズ不可：ズーム領域なし")
            return

        center = self.get_center()
        if not center:
            self.logger.log(LogLevel.ERROR, "リサイズ不可：中心座標なし")
            return

        cx, cy = center
        angle_rad = np.radians(self._angle) # 現在の回転角度 (ラジアン)
        cos_a = np.cos(-angle_rad) # 逆回転のための角度
        sin_a = np.sin(-angle_rad)

        # --- 座標を逆回転させて、回転前の座標系に戻す ---
        # 固定角
        fixed_x_rel = fixed_x_rotated - cx
        fixed_y_rel = fixed_y_rotated - cy
        fixed_x_unrotated = fixed_x_rel * cos_a - fixed_y_rel * sin_a + cx
        fixed_y_unrotated = fixed_x_rel * sin_a + fixed_y_rel * cos_a + cy

        # 現在のマウス位置
        current_x_rel = current_x - cx
        current_y_rel = current_y - cy
        current_x_unrotated = current_x_rel * cos_a - current_y_rel * sin_a + cx
        current_y_unrotated = current_x_rel * sin_a + current_y_rel * cos_a + cy
        # --- 逆回転ここまで ---

        # --- 回転前の座標系で新しい矩形を計算 ---
        new_width = abs(current_x_unrotated - fixed_x_unrotated)
        new_height = abs(current_y_unrotated - fixed_y_unrotated)
        new_x = min(fixed_x_unrotated, current_x_unrotated)
        new_y = min(fixed_y_unrotated, current_y_unrotated)
        # --- 計算ここまで ---

        # --- 矩形プロパティを設定 (まだ回転は適用しない) ---
        self.rect.set_width(new_width)
        self.rect.set_height(new_height)
        self.rect.set_xy((new_x, new_y))
        # --- 設定ここまで ---

        self.logger.log(LogLevel.DEBUG, f"リサイズ計算(回転前): x={new_x:.2f}, y={new_y:.2f}, w={new_width:.2f}, h={new_height:.2f}")

        # 最後に現在の回転角度を再適用
        self._apply_rotation()

    def is_valid_size(self, width: float, height: float) -> bool:
        """ 指定された幅と高さが有効か (最小サイズ以上か) """
        is_valid = width >= self.MIN_WIDTH and height >= self.MIN_HEIGHT
        if not is_valid:
            self.logger.log(LogLevel.DEBUG, f"無効なサイズチェック: w={width:.4f} (<{self.MIN_WIDTH}), h={height:.4f} (<{self.MIN_HEIGHT})")
        return is_valid

    def temporary_creation(self, start_x: float, start_y: float, end_x: float, end_y: float) -> bool:
        """ ズーム領域作成完了 """
        if not self.rect:
            self.logger.log(LogLevel.ERROR, "長方形確定不可：ズーム領域なし")
            return False # Indicate failure

        width = abs(end_x - start_x)
        height = abs(end_y - start_y)
        x = min(start_x, end_x)
        y = min(start_y, end_y)

        self.rect.set_width(width)
        self.rect.set_height(height)
        self.rect.set_xy((x, y))
        self._angle = 0.0
        self.rect.set_transform(self.ax.transData)
        self.rect.set_edgecolor('white')
        self.rect.set_linestyle('-')
        self.rect.set_visible(True)
        self.logger.log(LogLevel.INFO, "ズーム領域作成完了", {"x": x, "y": y, "w": width, "h": height})
        return True # Indicate success

    def move_rect_to(self, new_x: float, new_y: float) -> None:
        """ ズーム領域を移動 """
        if not self.rect:
            self.logger.log(LogLevel.ERROR, "ズーム領域移動不可：ズーム領域なし")
            return
        self.rect.set_xy((new_x, new_y)) # ズーム領域の基本位置を更新
        self._apply_rotation() # 現在の回転角度を再適用 (中心が変わるため)

    def delete_rect(self):
        """ ズーム領域を削除 """
        if self.rect:
            # remove() の代わりに、Axesから削除する正しい方法を使用
            if self.rect in self.ax.patches:
                self.ax.patches.remove(self.rect)
            # または単に非表示にする
            self.rect.set_visible(False)
            self.rect = None
            self.logger.log(LogLevel.DEBUG, "ズーム領域削除完了")
        else:
            self.logger.log(LogLevel.DEBUG, "ズーム領域なし：削除スキップ")

    def get_properties(self) -> Optional[Tuple[float, float, float, float]]:
        """ ズーム領域のプロパティ (x, y, width, height) を取得 (回転前の値) """
        if self.rect:
            # 注意: これらは回転前のズーム領域の基本的な幅と高さを返す
            return (self.rect.get_x(), self.rect.get_y(),
                    self.rect.get_width(), self.rect.get_height())
        return None

    def get_center(self) -> Optional[Tuple[float, float]]:
        """ ズーム領域の中心座標を取得 (回転前の座標系) """
        props = self.get_properties()
        if props:
            x, y, w, h = props
            center_x = x + w / 2
            center_y = y + h / 2
            return center_x, center_y
        return None

    def get_rotated_corners(self) -> Optional[list[Tuple[float, float]]]:
        """ 回転後の四隅の絶対座標を取得する """
        props = self.get_properties()
        center = self.get_center()
        if props is None or center is None:
            return None

        x, y, width, height = props
        cx, cy = center
        angle_rad = np.radians(self._angle)

        half_w, half_h = width / 2, height / 2
        # EventHandler の期待 (0:左上, 1:右上, 2:左下, 3:右下) に合わせる
        corners_unrotated_relative = [
            (-half_w,  half_h), # 左上 (Index 0)
            ( half_w,  half_h), # 右上 (Index 1)
            (-half_w, -half_h), # 左下 (Index 2)
            ( half_w, -half_h)  # 右下 (Index 3)
        ]

        cos_a, sin_a = np.cos(angle_rad), np.sin(angle_rad)
        rotated_corners = []
        for rel_x, rel_y in corners_unrotated_relative:
            rotated_x = rel_x * cos_a - rel_y * sin_a + cx
            rotated_y = rel_x * sin_a + rel_y * cos_a + cy
            rotated_corners.append((rotated_x, rotated_y))
        return rotated_corners

    def get_rotation(self) -> float:
        """ 現在の回転角度を取得 (度単位) """
        return self._angle

    def set_rotation(self, angle: float):
        """ ズーム領域の回転角度を設定 (度単位) """
        if not self.rect:
            self.logger.log(LogLevel.ERROR, "ズーム領域回転不可：ズーム領域なし")
            return
        self._angle = angle % 360 # 0-360度の範囲に正規化
        self._apply_rotation()

    def _apply_rotation(self):
        """ 現在の角度に基づいて回転変換を適用 """
        if not self.rect:
            return
        center = self.get_center()
        if center:
            cx, cy = center
            # アフィン変換を作成して適用
            transform = transforms.Affine2D().rotate_deg_around(cx, cy, self._angle)
            # データ座標系への変換と組み合わせる
            self.rect.set_transform(transform + self.ax.transData)
        else:
            # 中心が取得できない場合は通常のデータ座標変換のみ
            self.rect.set_transform(self.ax.transData)

    def get_patch(self) -> Optional[patches.Rectangle]:
        """ ズーム領域パッチオブジェクトを取得 """
        return self.rect
