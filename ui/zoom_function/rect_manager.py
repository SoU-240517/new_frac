import matplotlib.patches as patches
import matplotlib.transforms as transforms
import numpy as np
from matplotlib.axes import Axes
from typing import Optional, Tuple, Dict, Any
from .debug_logger import DebugLogger
from .enums import LogLevel

class RectManager:
    """ズーム領域の矩形（Rectangle）を管理（作成、移動、リサイズ、回転）するクラス
    - 役割:
        - ズーム領域を作成
        - ズーム領域を移動
        - ズーム領域をリサイズ
        - ズーム領域を回転
    """
    MIN_WIDTH = 0.01 # 許容される最小幅 (データ座標系)
    MIN_HEIGHT = 0.01 # 許容される最小高さ (データ座標系)
    ASPECT_RATIO_W_H = 16 / 9 # 目標とするアスペクト比 (幅 / 高さ)

    def __init__(self,
                 ax: Axes,
                 logger: DebugLogger):
        """ズーム領域管理のコンストラクタ（親: ZoomSelector）

        Args:
            ax (Axes): Matplotlib の Axes オブジェクト
            logger (DebugLogger): ログ出力用の DebugLogger インスタンス
        """
        self.logger = logger
        self.ax = ax
        self.rect: Optional[patches.Rectangle] = None
        self._angle: float = 0.0

    def get_rect(self) -> Optional[patches.Rectangle]:
        """現在のズーム領域を取得

        Args:
            ax (Axes): Matplotlib の Axes オブジェクト

        Returns:
            Optional[patches.Rectangle]: 現在のズーム領域の Rectangle オブジェクト
        """
        return self.rect

    def setup_rect(self, x: float, y: float):
        """新しいズーム領域の初期設定 (設置サイズ 0：回転なし)

        Args:
            x (float): 矩形左上の x 座標
            y (float): 矩形左上の y 座標
        """
        self.delete_rect() # 古い矩形を消す
        self.rect = patches.Rectangle(
            (x, y), 0, 0,
            linewidth=1, edgecolor='gray', facecolor='none', linestyle='--', visible=True)
        self.ax.add_patch(self.rect)
        self._angle = 0.0 # 角度リセット
        self.logger.log(LogLevel.SUCCESS, "初期のズーム領域設置完了", {"x": x, "y": y})

    def setting_rect_size(self, start_x: float, start_y: float, current_x: float, current_y: float):
        """ズーム領域のサイズと位置を更新 (作成中：回転なし)

        Args:
            start_x (float): 矩形左上の x 座標
            start_y (float): 矩形左上の y 座標
            current_x (float): 矩形右下の x 座標
            current_y (float): 矩形右下の y 座標
        """
        if not self.rect:
            self.logger.log(LogLevel.ERROR, "ズーム領域なし：サイズ更新不可")
            return

        # マウスの移動量を計算
        dx = current_x - start_x
        dy = current_y - start_y

        # 幅と高さをアスペクト比に基づいて計算
        # 幅の移動量の方がアスペクト比に対して大きいか等しい場合
        if abs(dx) >= abs(dy) * self.ASPECT_RATIO_W_H:
            width = abs(dx)
            height = width / self.ASPECT_RATIO_W_H
        else: # 高さの移動量の方がアスペクト比に対して大きい場合
            height = abs(dy)
            width = height * self.ASPECT_RATIO_W_H

        # 矩形の左下座標 (x, y) を計算
        if dx >= 0: # current_x が start_x より右にあるか (dx >= 0)
            x = start_x
        else: # current_x が start_x より左にある (dx < 0)
            x = start_x - width

        if dy >= 0: # current_y が start_y より上にあるか (dy >= 0)
            y = start_y
        else: # current_y が start_y より下にある (dy < 0)
            y = start_y - height

        self.rect.set_width(width)
        self.rect.set_height(height)
        self.rect.set_xy((x, y))
        self._angle = 0.0 # 作成中は回転しないので角度は0、変換も単純な transData
        self.rect.set_transform(self.ax.transData)

    def edge_change_editing(self):
        """ズーム領域のエッジ変更 (灰色：破線)"""
        if not self.rect:
            self.logger.log(LogLevel.ERROR, "ズーム領域なし：エッジ変更不可")
            return

        self.rect.set_edgecolor('gray')
        self.rect.set_linestyle('--')

    def edge_change_finishing(self):
        """ズーム領域のエッジ変更 (白：実線)"""
        if not self.rect:
            self.logger.log(LogLevel.ERROR, "ズーム領域なし：エッジ変更不可")
            return

        self.rect.set_edgecolor('white')
        self.rect.set_linestyle('-')

    def resize_rect_from_corners(self, fixed_x_rotated: float, fixed_y_rotated: float, current_x: float, current_y: float):
        """固定された回転後の角と現在のマウス位置からズーム領域を更新 (リサイズ中、回転考慮)

        Args:
            fixed_x_rotated (float): 固定された回転後の x 座標
            fixed_y_rotated (float): 固定された回転後の y 座標
            current_x (float): 現在のマウス x 座標
            current_y (float): 現在のマウス y 座標
        """
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
        # 幅と高さの変化量を計算
        dx_unrotated = current_x_unrotated - fixed_x_unrotated
        dy_unrotated = current_y_unrotated - fixed_y_unrotated

        # 新しい幅と高さをアスペクト比に基づいて計算
        # 幅の変化量の方がアスペクト比に対して大きいか等しい場合
        if abs(dx_unrotated) >= abs(dy_unrotated) * self.ASPECT_RATIO_W_H:
            new_width = abs(dx_unrotated)
            new_height = new_width / self.ASPECT_RATIO_W_H
        else: # 高の変化量の方がアスペクト比に対して大きい場合
            new_height = abs(dy_unrotated)
            new_width = new_height * self.ASPECT_RATIO_W_H

        # 新しい左下座標 (new_x, new_y) を計算
        # current_x_unrotated が fixed_x_unrotated より右にあるか (dx_unrotated >= 0)
        if dx_unrotated >= 0:
            new_x = fixed_x_unrotated
        else: # current_x_unrotated が fixed_x_unrotated より左にある (dx_unrotated < 0)
            new_x = fixed_x_unrotated - new_width
        # current_y_unrotated が fixed_y_unrotated より上にあるか (dy_unrotated >= 0)
        if dy_unrotated >= 0:
            new_y = fixed_y_unrotated
        else: # current_y_unrotated が fixed_y_unrotated より下にある (dy_unrotated < 0)
            new_y = fixed_y_unrotated - new_height

        # サイズチェック
        if not self.is_valid_size(new_width, new_height):
             self.logger.log(LogLevel.DEBUG, f"リサイズ中止：無効なサイズ w={new_width:.4f}, h={new_height:.4f}")
             return # サイズが無効なら更新しない

        # --- 矩形プロパティを設定 (まだ回転は適用しない) ---
        self.rect.set_width(new_width)
        self.rect.set_height(new_height)
        self.rect.set_xy((new_x, new_y))
        # --- 設定ここまで ---

        self.logger.log(LogLevel.DEBUG, f"リサイズ計算(回転前): x={new_x:.2f}, y={new_y:.2f}, w={new_width:.2f}, h={new_height:.2f}")
        # 最後に現在の回転角度を再適用
        self._apply_rotation()

    def is_valid_size(self, width: float, height: float) -> bool:
        """指定された幅と高さが有効か (最小サイズ以上か)

        Args:
            width (float): 幅
            height (float): 高さ

        Returns:
            bool: 幅と高さが最小サイズ以上か
        """
        is_valid = width >= self.MIN_WIDTH and height >= self.MIN_HEIGHT
        if not is_valid:
            self.logger.log(LogLevel.DEBUG, f"無効なサイズ：w={width:.4f} (<{self.MIN_WIDTH}), h={height:.4f} (<{self.MIN_HEIGHT})")
        return is_valid

    def _temporary_creation(self, start_x: float, start_y: float, end_x: float, end_y: float) -> bool:
        """ズーム領域作成完了

        Args:
            start_x (float): 矩形左上の x 座標
            start_y (float): 矩形左上の y 座標
            end_x (float): 矩形右下の x 座標
            end_y (float): 矩形右下の y 座標

        Returns:
            bool: 作成成功か
        """
        if not self.rect:
            self.logger.log(LogLevel.ERROR, "ズーム領域作成不可：ズーム領域なし")
            return False # Indicate failure

        # マウスの移動量を計算
        dx = end_x - start_x
        dy = end_y - start_y

        # 幅と高さをアスペクト比に基づいて計算 (setting_rect_size と同じロジック)
        if abs(dx) >= abs(dy) * self.ASPECT_RATIO_W_H:
            width = abs(dx)
            height = width / self.ASPECT_RATIO_W_H
        else:
            height = abs(dy)
            width = height * self.ASPECT_RATIO_W_H

        # 矩形の左下座標 (x, y) を計算
        if dx >= 0:
            x = start_x
        else:
            x = start_x - width
        if dy >= 0:
            y = start_y
        else:
            y = start_y - height

        # 作成完了時にもサイズチェック
        if not self.is_valid_size(width, height):
            self.logger.log(LogLevel.WARNING, f"ズーム領域作成不可：最終サイズが無効 w={width:.4f}, h={height:.4f}")
            return False # 失敗を示すために False を返す（EventHandler側で削除処理を期待）
        self.rect.set_width(width)
        self.rect.set_height(height)
        self.rect.set_xy((x, y))
        self._angle = 0.0

        # 作成完了時は回転がないので、単純な transData を設定
        self.rect.set_transform(self.ax.transData)
        self.rect.set_edgecolor('white')
        self.rect.set_linestyle('-')
        self.rect.set_visible(True)
        self.logger.log(LogLevel.INFO, "ズーム領域作成完了", {"x": x, "y": y, "w": width, "h": height})
        return True # Indicate success

    def move_rect_to(self, new_x: float, new_y: float):
        """ズーム領域を移動

        Args:
            new_x (float): 矩形左上の x 座標
            new_y (float): 矩形左上の y 座標
        """
        if not self.rect:
            self.logger.log(LogLevel.ERROR, "ズーム領域移動不可：ズーム領域なし")
            return

        self.rect.set_xy((new_x, new_y)) # ズーム領域の基本位置を更新
        self._apply_rotation() # 現在の回転角度を再適用 (中心が変わるため)

    def delete_rect(self):
        """ズーム領域を削除"""
        if self.rect:
            try:
                # パッチがまだAxesに追加されているか確認
                if self.rect in self.ax.patches:
                    self.rect.remove()
                    self.logger.log(LogLevel.SUCCESS, "ズーム領域削除完了 (remove)")
                else:
                     # すでに追加されていない（remove済みか、非表示のみ）場合は何もしない
                     self.logger.log(LogLevel.DEBUG, "ズーム領域は既に削除済み、または非表示")
            except Exception as e:
                 # remove中に予期せぬエラーが発生した場合
                 self.logger.log(LogLevel.ERROR, f"ズーム領域削除中にエラー: {e}")
            finally:
                self.rect = None # 参照をクリア
                self._angle = 0.0 # 角度もリセット
        else:
            self.logger.log(LogLevel.DEBUG, "ズーム領域なし：削除スキップ")

    def get_properties(self) -> Optional[Tuple[float, float, float, float]]:
        """ズーム領域のプロパティ (x, y, width, height) を取得 (回転前の値)

        Returns:
            Tuple[float, float, float, float]: (x, y, width, height) or None
        """
        if self.rect:
            # 注意: これらは回転前のズーム領域の基本的な幅と高さを返す
            return (self.rect.get_x(), self.rect.get_y(),
                    self.rect.get_width(), self.rect.get_height())
        return None

    # --- Undo/Redo 用メソッド ---
    def get_state(self) -> Optional[Dict[str, Any]]:
        """現在の状態 (Undo用) を取得

        Returns:
            Dict[str, Any]: 状態データ
        """
        props = self.get_properties()
        if props and self.rect: # rect が存在することも確認
            x, y, width, height = props
            return {
                "x": x,
                "y": y,
                "width": width,
                "height": height,
                "angle": self._angle,
                "visible": self.rect.get_visible(), # 可視状態も保存
                "edgecolor": self.rect.get_edgecolor(), # エッジの色も保存
                "linestyle": self.rect.get_linestyle() # 線のスタイルも保存
            }
        # 矩形がない場合も None を返すことを明示
        elif not self.rect:
             self.logger.log(LogLevel.DEBUG, "get_state: 矩形が存在しないため None を返します")
             return None

    def set_state(self, state: Optional[Dict[str, Any]]):
        """指定された状態に矩形を復元 (Undo用)

        Args:
            state (Optional[Dict[str, Any]]): 状態データ
        """
        if not state:
            self.logger.log(LogLevel.WARNING, "Undo不可：状態データなし、または削除された状態")
            self.delete_rect() # 状態がない場合、矩形を削除する
            return

        x = state.get("x")
        y = state.get("y")
        width = state.get("width")
        height = state.get("height")
        angle = state.get("angle", 0.0)
        visible = state.get("visible", True) # デフォルトは表示
        edgecolor = state.get("edgecolor", "white") # デフォルトは白
        linestyle = state.get("linestyle", "-") # デフォルトは実線

        # 必須パラメータのチェック
        if None in [x, y, width, height]:
             self.logger.log(LogLevel.ERROR, f"Undo失敗：無効な状態データ {state}")
             # 状態データが無効なら矩形を削除する（安全策）
             self.delete_rect()
             return

        # --- 矩形の作成または更新 ---
        if not self.is_valid_size(width, height): # サイズが有効かチェック
            self.logger.log(LogLevel.WARNING, f"Undo: 矩形復元スキップ（サイズ無効 w={width:.4f}, h={height:.4f}）")
            # 無効なサイズが指定された場合も、現在の矩形を削除する
            self.delete_rect()
            return
        if not self.rect: # 矩形が存在しない場合は作成
             self.rect = patches.Rectangle((x, y), width, height,
                                         linewidth=1, edgecolor=edgecolor, facecolor='none',
                                         linestyle=linestyle, visible=False) # 最初は非表示
             self.ax.add_patch(self.rect)
             self.logger.log(LogLevel.DEBUG, "Undo: 矩形が存在しなかったので新規作成")
        else: # 矩形が存在する場合、プロパティを設定
            self.rect.set_x(x)
            self.rect.set_y(y)
            self.rect.set_width(width)
            self.rect.set_height(height)
            self.rect.set_edgecolor(edgecolor) # エッジの色を復元
            self.rect.set_linestyle(linestyle) # 線のスタイルを復元
        self._angle = angle # 角度を設定
        self.rect.set_visible(visible) # 可視状態を復元
        # 最後に回転を適用
        self._apply_rotation()
        self.logger.log(LogLevel.DEBUG, "Undo: 矩形状態を復元", state)
    # --- ここまで Undo/Redo 用メソッド ---

    def get_center(self) -> Optional[Tuple[float, float]]:
        """ズーム領域の中心座標を取得 (回転前の座標系)

        Returns:
            Optional[Tuple[float, float]]: 中心座標 (x, y) or None
        """
        props = self.get_properties()
        if props:
            x, y, w, h = props
            if w <= 0 or h <= 0: # 幅や高さが0の場合も考慮
                self.logger.log(LogLevel.DEBUG, f"get_center: 幅({w})または高さ({h})が0以下")
                return None
            center_x = x + w / 2
            center_y = y + h / 2
            return center_x, center_y
        return None

    def get_rotated_corners(self) -> Optional[list[Tuple[float, float]]]:
        """回転後の四隅の絶対座標を取得する

        Returns:
            Optional[list[Tuple[float, float]]]: 四隅の絶対座標 [(x1, y1), (x2, y2), (x3, y3), (x4, y4)] or None
        """
        props = self.get_properties()
        center = self.get_center()

        # 矩形がない、またはサイズが0の場合もNoneを返すように修正
        if not self.rect or props is None or center is None or props[2] <= 0 or props[3] <= 0:
            self.logger.log(LogLevel.DEBUG, "回転後の角取得不可：矩形、プロパティ、中心のいずれか、またはサイズが0")
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
        """現在の回転角度を取得 (度単位)

        Returns:
            float: 回転角度 (度単位)
        """
        return self._angle

    def set_rotation(self, angle: float):
        """ズーム領域の回転角度を設定 (度単位)

        Args:
            angle (float): 回転角度 (度単位)
        """
        if not self.rect:
            self.logger.log(LogLevel.ERROR, "ズーム領域回転不可：ズーム領域なし")
            return
        self._angle = angle % 360 # 0-360度の範囲に正規化（-180から180にする場合は調整）
        self._apply_rotation()

    def _apply_rotation(self):
        """現在の角度に基づいて回転変換を適用"""
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
        """ズーム領域パッチオブジェクトを取得

        Returns:
            Optional[patches.Rectangle]: パッチオブジェクト or None
        """
        return self.rect
