from encodings.punycode import T
from hmac import new
from math import e
import matplotlib.patches as patches
import matplotlib.transforms as transforms # transforms をインポート
from matplotlib.axes import Axes
from typing import Optional, Tuple
from .debug_logger import DebugLogger
from .enums import LogLevel

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
        self.rect: Optional[patches.Rectangle] = None # 現在描画中のズーム領域オブジェクト
        self._angle: float = 0.0 # 回転角度 (度単位) を追加

    def get_rect(self) -> Optional[patches.Rectangle]:
        """ 現在のズーム領域を取得 """
        return self.rect

    def setup_rect(self, x: float, y: float):
        """ 新しい矩形の初期設定 (サイズ 0 で作成) """
#        self.clear() # 既存の矩形があればクリア（矩形ありの状態で新規作成ま認めないのでクリア不要）
#        self._angle = 0.0 # 角度をリセット（初期化で設定済みなので、ここでの設定は不要）
        # 初期状態ではサイズ0、回転なしで作成
        self.rect = patches.Rectangle((x, y), 0, 0, linewidth=1, edgecolor='gray', facecolor='none', linestyle='--', visible=True)
        self.ax.add_patch(self.rect)
        self.logger.log(LogLevel.DEBUG, "初期のズーム領域設置完了", {"x": x, "y": y})

    def setting_rect_size(self, start_x: float, start_y: float, current_x: float, current_y: float):
        """ 矩形のサイズと位置を更新 (作成中) """
        if not self.rect:
            self.logger.log(LogLevel.ERROR, "ズーム領域なし：サイズ更新不可")
            return

        width = abs(current_x - start_x)
        height = abs(current_y - start_y)
        x = min(start_x, current_x)
        y = min(start_y, current_y)

        # 回転がない前提で矩形の基本プロパティを設定
        self.rect.set_width(width)
        self.rect.set_height(height)
        self.rect.set_xy((x, y))
        self.rect.set_visible(True) # サイズが決まったら表示
        # 回転は適用しない (作成中は回転なし)
        self.rect.set_transform(self.ax.transData)
        self.logger.log(LogLevel.DEBUG, "ズーム領域のサイズ/位置更新完了", {"x": x, "y": y, "w": width, "h": height})

    def edge_change_editing(self):
        """ 矩形のエッジを変更 (色とスタイル) """
        if not self.rect:
            self.logger.log(LogLevel.ERROR, "ズーム領域なし：エッジ変更不可")
            return

        self.rect.set_edgecolor('gray') # 色を灰色に変更
        self.rect.set_linestyle('--') # 破線に変更

    def edge_change_finishing(self):
        """ 矩形のエッジを変更 (色とスタイル) """
        if not self.rect:
            self.logger.log(LogLevel.ERROR, "ズーム領域なし：エッジ変更不可")
            return

        self.rect.set_edgecolor('white') # 色を白に変更
        self.rect.set_linestyle('-') # 実線に変更


    def resize_rect_from_corners(self, fixed_x: float, fixed_y: float, current_x: float, current_y: float):
        """ 固定された角と現在のマウス位置から矩形を更新 (リサイズ中) """
        if not self.rect:
            self.logger.log(LogLevel.ERROR, "リサイズ不可：ズーム領域なし")
            return

        # リサイズ中は回転を考慮しないシンプルな更新（回転は別途適用）
        width = abs(current_x - fixed_x)
        height = abs(current_y - fixed_y)
        x = min(fixed_x, current_x)
        y = min(fixed_y, current_y)

        # 矩形の基本プロパティを更新
        self.rect.set_width(width)
        self.rect.set_height(height)

        self.rect.set_xy((x, y))

        # 現在の回転角度を再適用
        self._apply_rotation()
        self.logger.log(LogLevel.CALL, "更新完了", {"x": x, "y": y, "w": width, "h": height, "angle": self._angle})

    def is_valid_size(self, width: float, height: float) -> bool:
        """ 指定された幅と高さが有効か (最小サイズ以上か) """
        is_valid = width >= self.MIN_WIDTH and height >= self.MIN_HEIGHT
        if not is_valid:
            self.logger.log(LogLevel.DEBUG, f"無効なサイズチェック: w={width:.4f} (<{self.MIN_WIDTH}), h={height:.4f} (<{self.MIN_HEIGHT})")
        return is_valid

    def temporary_creation(self, start_x: float, start_y: float, end_x: float, end_y: float) -> bool:
        """ ドラッグ終了時に矩形を最終確定 """
        if not self.rect:
            self.logger.log(LogLevel.ERROR, "長方形確定不可：ズーム領域なし")
            return False # Indicate failure

        width = abs(end_x - start_x)
        height = abs(end_y - start_y)
        x = min(start_x, end_x)
        y = min(start_y, end_y)

        # 最終的なプロパティを設定
        self.rect.set_width(width)
        self.rect.set_height(height)
        self.rect.set_xy((x, y))
        self._angle = 0.0 # 作成完了時は角度0
        self.rect.set_transform(self.ax.transData) # 回転なし
        self.rect.set_edgecolor('white') # 色を白に変更
        self.rect.set_linestyle('-') # 実線に変更
        self.rect.set_visible(True)
        self.logger.log(LogLevel.INFO, "ズーム領域情報：作成完了時", {"x": x, "y": y, "w": width, "h": height})
        return True # Indicate success

    def move_rect_to(self, new_x: float, new_y: float) -> None:
        """ 矩形を指定した左下座標に移動 """
        if not self.rect:
            self.logger.log(LogLevel.ERROR, "ズーム領域移動不可：ズーム領域なし")
            return

        # 矩形の基本位置を更新
        self.rect.set_xy((new_x, new_y))

        # 現在の回転角度を再適用 (中心が変わるため)
        self._apply_rotation()
        # self.logger.log(LogLevel.CALL, "Rectangle moved.", {"new_x": new_x, "new_y": new_y, "angle": self._angle}) # 頻繁すぎるログ

    def clear_rect(self):
        """ ズーム領域を削除 """
        if self.rect:
            # remove() の代わりに、Axesから削除する正しい方法を使用
            if self.rect in self.ax.patches:
                self.ax.patches.remove(self.rect)
            # または単に非表示にする
            self.rect.set_visible(False)
            self.rect = None
            self.logger.log(LogLevel.DEBUG, "ズーム領域を削除しました")
        else:
            self.logger.log(LogLevel.DEBUG, "ズーム領域なし：削除スキップ")

    def get_properties(self) -> Optional[Tuple[float, float, float, float]]:
        """ 矩形のプロパティ (x, y, width, height) を取得 (回転前の値) """
        if self.rect:
            # 注意: これらは回転前の矩形の基本的な幅と高さを返す
            return (self.rect.get_x(), self.rect.get_y(),
                    self.rect.get_width(), self.rect.get_height())
        return None

    def get_center(self) -> Optional[Tuple[float, float]]:
        """ 矩形の中心座標を取得 (回転前の座標系) """
        props = self.get_properties()
        if props:
            x, y, w, h = props
            center_x = x + w / 2
            center_y = y + h / 2
            return center_x, center_y
        return None

    def get_rotation(self) -> float:
        """ 現在の回転角度を取得 (度単位) """
        return self._angle

    def set_rotation(self, angle: float):
        """ 矩形の回転角度を設定 (度単位) """
        if not self.rect:
            self.logger.log(LogLevel.ERROR, "ズーム領域回転不可：ズーム領域なし")
            return
        self._angle = angle % 360 # 0-360度の範囲に正規化
        self._apply_rotation()
        # self.logger.log(LogLevel.CALL, f"Rotation set to {self._angle:.2f} degrees.") # 頻繁すぎるログ

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
        """ 矩形パッチオブジェクトを取得 """
        return self.rect
