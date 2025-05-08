import matplotlib.patches as patches
import matplotlib.transforms as transforms
import numpy as np
from matplotlib.axes import Axes
from typing import Optional, Tuple, Dict, Any
from debug import DebugLogger, LogLevel

class RectManager:
    """ズーム領域の矩形（Rectangle）を管理するクラス

    ズーム領域の作成、移動、リサイズ、回転などの操作を管理します。
    ピクセル単位での最小サイズ制限とアスペクト比の維持をサポートします。

    Attributes:
        ax (Axes): Matplotlib の Axes オブジェクト
        logger (DebugLogger): ログ出力用の DebugLogger インスタンス
        rect (Optional[patches.Rectangle]): ズーム領域の矩形パッチ
        _angle (float): 矩形の回転角度（度数法）
        _last_valid_size_px (Optional[Tuple[float, float]]): 最後に有効だった矩形のピクセルサイズ
        min_width_px (int): 矩形の最小許容幅 (ピクセル単位)
        min_height_px (int): 矩形の最小許容高さ (ピクセル単位)
        aspect_ratio_w_h (float): 矩形の目標アスペクト比 (幅 / 高さ)
    """

    def __init__(
        self,
        ax: Axes,
        logger: DebugLogger,
        config: Dict[str, Any]
    ):
        """RectManager クラスのコンストラクタ

        Args:
            ax (Axes): Matplotlib の Axes オブジェクト
            logger (DebugLogger): ログ出力用の DebugLogger インスタンス
            config (Dict[str, Any]): 設定データを含む辞書
                必要な設定キー:
                - zoom_rect_min_width_px: 矩形の最小許容幅 (ピクセル単位)
                - zoom_rect_min_height_px: 矩形の最小許容高さ (ピクセル単位)
                - zoom_rect_aspect_ratio: 矩形の目標アスペクト比 (幅 / 高さ)
                - edit_edge_color: 編集中のエッジ色
                - edit_edge_linestyle: 編集中のエッジスタイル
                - fix_edge_color: 確定時のエッジ色
                - fix_edge_linestyle: 確定時のエッジスタイル
        """
        self.logger = logger
        self.ax = ax
        self.rect: Optional[patches.Rectangle] = None
        self._angle: float = 0.0

        # 直前の有効なサイズを保持 (ドラッグ中に無効サイズになった場合に使用)
        self._last_valid_size_px: Optional[Tuple[float, float]] = None

        # 設定ファイルから矩形関連の設定を読み込む
        self.ui_settings = config.get("ui_settings", {})

        # フォールバック用のデフォルト値を設定
        default_min_width = 5
        default_min_height = 5
        default_aspect_ratio = 16 / 9

        # インスタンス変数として設定値を保存
        self.min_width_px = self.ui_settings.get("zoom_rect_min_width_px", default_min_width)
        self.min_height_px = self.ui_settings.get("zoom_rect_min_height_px", default_min_height)
        self.aspect_ratio_w_h = self.ui_settings.get("zoom_rect_aspect_ratio", default_aspect_ratio)

        # 読み込んだ値のバリデーション (例: 0以下でないか)
        if self.min_width_px <= 0:
            self.logger.log(LogLevel.WARNING, f"設定ファイルの zoom_rect_min_width_px ({self.min_width_px}) が無効。デフォルト値 ({default_min_width}) を使用")
            self.min_width_px = default_min_width
        if self.min_height_px <= 0:
            self.logger.log(LogLevel.WARNING, f"設定ファイルの zoom_rect_min_height_px ({self.min_height_px}) が無効。デフォルト値 ({default_min_height}) を使用")
            self.min_height_px = default_min_height
        if self.aspect_ratio_w_h <= 0:
             self.logger.log(LogLevel.WARNING, f"設定ファイルの zoom_rect_aspect_ratio ({self.aspect_ratio_w_h}) が無効。デフォルト値 ({default_aspect_ratio}) を使用")
             self.aspect_ratio_w_h = default_aspect_ratio

        self.logger.log(LogLevel.DEBUG, f"初期設定 RectManager: min_w = {self.min_width_px} px, min_h = {self.min_height_px} px, aspect = {self.aspect_ratio_w_h:.4f}")

    def get_rect(self) -> Optional[patches.Rectangle]:
        """現在のズーム領域の矩形パッチを取得

        Returns:
            Optional[patches.Rectangle]: 現在のズーム領域の Rectangle オブジェクト。
            ズーム領域が存在しない場合は None を返します。
        """
        return self.rect

    def setup_rect(self, x: float, y: float) -> None:
        """ズーム領域の初期設定

        初期状態の矩形を作成し、指定された位置に配置します。

        Args:
            x (float): 矩形左上の x 座標 (データ座標)
            y (float): 矩形左上の y 座標 (データ座標)
        """
        self.delete_rect()
        self.rect = patches.Rectangle(
            (x, y), 0, 0,
            linewidth=1, edgecolor='gray', facecolor='none', linestyle='--', visible=True)
        self.ax.add_patch(self.rect)
        self._angle = 0.0
        self._last_valid_size_px = None # 新規作成時はリセット
        self.logger.log(LogLevel.SUCCESS, "初期のズーム領域設置完了", {"x": x, "y": y})

    def _calculate_rect_geometry(self,
                                 ref_x: float, ref_y: float,
                                 target_x: float, target_y: float
                                 ) -> Tuple[float, float, float, float]:
        """基準点と目標点から、アスペクト比を維持した矩形の位置とサイズを計算

        Args:
            ref_x (float): 基準点の x 座標 (データ座標)
            ref_y (float): 基準点の y 座標 (データ座標)
            target_x (float): 目標点の x 座標 (データ座標)
            target_y (float): 目標点の y 座標 (データ座標)

        Returns:
            Tuple[float, float, float, float]: (左下 x, 左下 y, 幅, 高さ)
            アスペクト比を維持した矩形の位置とサイズを返します。
        """
        # マウスの移動量を計算
        dx = target_x - ref_x
        dy = target_y - ref_y

        # 幅と高さをアスペクト比に基づいて計算
        # 幅の移動量の方がアスペクト比に対して大きいか等しい場合
        # アスペクト比をインスタンス変数から読み込む
        if abs(dx) >= abs(dy) * self.aspect_ratio_w_h:
            width = abs(dx)
            # アスペクト比が0でないことを確認
            height = width / self.aspect_ratio_w_h if self.aspect_ratio_w_h > 0 else 0
        else: # 高さの移動量の方がアスペクト比に対して大きい場合
            height = abs(dy)
            # アスペクト比をインスタンス変数から読み込む
            width = height * self.aspect_ratio_w_h

        # 矩形の左下座標 (x, y) を計算
        if dx >= 0: # target_x が ref_x より右にある場合
            x = ref_x
        else: # target_x が ref_x より左にある場合
            x = ref_x - width

        if dy >= 0: # target_y が ref_y より上にある場合
            y = ref_y
        else: # target_y が ref_y より下にある場合
            y = ref_y - height

        return x, y, width, height

    def setting_rect_size(self, start_x: float, start_y: float, current_x: float, current_y: float) -> None:
    # setting_rect_size は _calculate_rect_geometry と _check_pixel_size を使うので、
    # これらの内部でインスタンス変数を使うように変更されていれば、このメソッド自体は変更不要
        """ズーム領域のサイズと位置を更新

        ピクセルサイズチェックを行い、有効なサイズの場合は矩形を更新します。

        Args:
            start_x (float): ドラッグ開始点の x 座標 (データ座標)
            start_y (float): ドラッグ開始点の y 座標 (データ座標)
            current_x (float): 現在のマウス x 座標 (データ座標)
            current_y (float): 現在のマウス y 座標 (データ座標)
        """
        if not self.rect:
            self.logger.log(LogLevel.ERROR, "ズーム領域なし：サイズ更新不可")
            return

        # データ座標での幅、高さ、左下座標の計算 (内部で self.aspect_ratio_w_h を使用)
        x, y, width, height = self._calculate_rect_geometry(start_x, start_y, current_x, current_y)

        # ピクセルサイズチェック (内部で self.min_width_px, self.min_height_px を使用)
        is_valid, px_width, px_height = self._check_pixel_size(x, y, width, height)

        if is_valid:
            # 有効なサイズの場合、矩形を更新し、サイズをキャッシュ
            self.rect.set_width(width)
            self.rect.set_height(height)
            self.rect.set_xy((x, y))
            self._angle = 0.0 # 作成中は回転しない
            self.rect.set_transform(self.ax.transData)
            self._last_valid_size_px = (px_width, px_height) # 有効なピクセルサイズを記録
            self.logger.log(LogLevel.DEBUG, f"サイズ更新(有効): px_w={px_width:.1f}, px_h={px_height:.1f}")
        else:
            # 無効なサイズの場合、ログを出力し、矩形は更新しない
            self.logger.log(LogLevel.INFO, f"サイズ更新中止(無効): px_w={px_width:.1f}, px_h={px_height:.1f}")

    def edge_change_editing(self) -> None:
        """ズーム領域のエッジを編集中のスタイルに変更

        エッジの色と線種を編集中のスタイルに変更します。
        設定ファイルからエッジの色と線種を読み込みます。
        """
        if not self.rect:
            self.logger.log(LogLevel.ERROR, "ズーム領域なし：エッジ変更不可")
            return

        color = self.ui_settings.get("edit_edge_color", "gray")
        style = self.ui_settings.get("edit_edge_linestyle", "--")

        self.rect.set_edgecolor(color)
        self.rect.set_linestyle(style)

    def edge_change_finishing(self) -> None:
        """ズーム領域のエッジを確定時のスタイルに変更

        エッジの色と線種を確定時のスタイルに変更します。
        設定ファイルからエッジの色と線種を読み込みます。
        """
        if not self.rect:
            self.logger.log(LogLevel.ERROR, "ズーム領域なし：エッジ変更不可")
            return

        color = self.ui_settings.get("fix_edge_color", "white")
        style = self.ui_settings.get("fix_edge_linestyle", "-")

        self.rect.set_edgecolor(color)
        self.rect.set_linestyle(style)

    def resize_rect_from_corners(self,
                                 fixed_x_rotated: float, fixed_y_rotated: float,
                                 current_x: float, current_y: float
                                 ) -> None:
    # resize_rect_from_corners も内部で _calculate_rect_geometry と _check_pixel_size を使うため、変更不要
        """固定された回転後の角と現在のマウス位置からズーム領域を更新

        回転考慮のリサイズ操作を行い、ピクセルサイズチェックを行います。

        Args:
            fixed_x_rotated (float): 固定された回転後の x 座標 (データ座標)
            fixed_y_rotated (float): 固定された回転後の y 座標 (データ座標)
            current_x (float): 現在のマウス x 座標 (データ座標)
            current_y (float): 現在のマウス y 座標 (データ座標)
        """
        if not self.rect:
            self.logger.log(LogLevel.ERROR, "リサイズ不可：ズーム領域なし")
            return
        center = self.get_center()
        if not center:
            self.logger.log(LogLevel.ERROR, "リサイズ不可：中心座標なし")
            return

        # --- 座標逆回転---
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

        # 回転前の座標系で新しい矩形を計算 (内部で self.aspect_ratio_w_h を使用)
        new_x, new_y, new_width, new_height = self._calculate_rect_geometry(
            fixed_x_unrotated, fixed_y_unrotated, current_x_unrotated, current_y_unrotated
        )

        # --- ピクセルサイズチェック --- (内部で self.min_width_px 等を使用)
        is_valid, px_width, px_height = self._check_pixel_size(new_x, new_y, new_width, new_height)

        if is_valid:
            # 有効なら矩形プロパティを設定し、回転を適用
            self.rect.set_width(new_width)
            self.rect.set_height(new_height)
            self.rect.set_xy((new_x, new_y))
            self._apply_rotation() # 角度は変更しないのでそのまま適用
            self._last_valid_size_px = (px_width, px_height) # 有効なピクセルサイズを記録
            self.logger.log(LogLevel.DEBUG, f"リサイズ計算(有効): px_w={px_width:.1f}, px_h={px_height:.1f}, data_x={new_x:.2f}, data_y={new_y:.2f}, data_w={new_width:.2f}, data_h={new_height:.2f}")
        else:
            # サイズが無効なら更新しない
            self.logger.log(LogLevel.INFO, f"リサイズ中止(無効): px_w={px_width:.1f}, px_h={px_height:.1f}")

        self.logger.log(LogLevel.DEBUG, f"リサイズ計算(回転前): x={new_x:.2f}, y={new_y:.2f}, w={new_width:.2f}, h={new_height:.2f}")
        # 最後に現在の回転角度を再適用 (is_valid の場合のみ適用される)
        # self._apply_rotation() # is_valid チェック内で適用済み

    def is_valid_size_in_pixels(self, width_px: float, height_px: float) -> bool:
        """指定されたピクセル幅と高さが有効か (最小ピクセルサイズ以上か)

        Returns:
            bool: 幅と高さが最小ピクセルサイズ以上か
        """
        # 最小サイズをインスタンス変数から読み込む
        is_valid = width_px >= self.min_width_px and height_px >= self.min_height_px
        if not is_valid:
            # ログにもインスタンス変数の最小値を表示
            self.logger.log(LogLevel.WARNING, f"無効なピクセルサイズ：px_w={width_px:.1f} (<{self.min_width_px}), px_h={height_px:.1f} (<{self.min_height_px})")
        return is_valid

    def is_last_calculated_size_valid(self) -> bool:
        """最後に setting_rect_size または resize_rect_from_corners で計算・キャッシュされたピクセルサイズが有効かどうかを返す

        Returns:
            bool: 最後の計算結果が有効なサイズだったか
        """
        if self._last_valid_size_px:
            # is_valid_size_in_pixels を使って再検証 (内部で self.min_width_px 等を使用)
            return self.is_valid_size_in_pixels(self._last_valid_size_px[0], self._last_valid_size_px[1])
        # キャッシュがない場合は無効とみなす
        self.logger.log(LogLevel.DEBUG, "最後の有効ピクセルサイズキャッシュなし")
        return False

    def _temporary_creation(self, start_x: float, start_y: float, end_x: float, end_y: float) -> bool:
        """ズーム領域作成完了時の処理 (ピクセルサイズチェックあり)

        Returns:
            bool: 作成成功か (サイズが有効か)
        """
        if not self.rect:
            self.logger.log(LogLevel.ERROR, "ズーム領域作成不可：ズーム領域なし")
            return False # Indicate failure

        # データ座標での幅、高さ、左下座標の計算
        x, y, width, height = self._calculate_rect_geometry(start_x, start_y, end_x, end_y)

        # ピクセルサイズチェック
        is_valid, px_width, px_height = self._check_pixel_size(x, y, width, height)

        if not is_valid:
            # 作成完了時にサイズが無効だった場合
            self.logger.log(LogLevel.WARNING, f"ズーム領域作成不可：最終ピクセルサイズ無効 px_w={px_width:.1f}, px_h={px_height:.1f}")
            # RectManager 内で削除するか、EventHandler 側で削除するかは要検討。
            # ここでは False を返して EventHandler 側での削除を期待する。
            # self.delete_rect() # ここで削除しても良いかもしれない
            return False # 失敗を示す

        color = self.ui_settings.get("fix_edge_color", "white")
        style = self.ui_settings.get("fix_edge_linestyle", "-")

        # --- サイズが有効な場合、最終的な矩形プロパティを設定 ---
        self.rect.set_width(width)
        self.rect.set_height(height)
        self.rect.set_xy((x, y))
        self._angle = 0.0
        self.rect.set_transform(self.ax.transData)
        self.rect.set_edgecolor(color)
        self.rect.set_linestyle(style)
        self.rect.set_visible(True)
        self._last_valid_size_px = (px_width, px_height) # 最終有効サイズ
        self.logger.log(LogLevel.SUCCESS, "ズーム領域作成完了", {"x": x, "y": y, "w": width, "h": height, "px_w": px_width, "px_h": px_height})
        return True # Indicate success

    def move_rect_to(self, new_x: float, new_y: float):
        """ズーム領域を移動する

        Args:
            new_x (float): 矩形左上の x 座標
            new_y (float): 矩形左上の y 座標
        """
        if not self.rect:
            self.logger.log(LogLevel.ERROR, "ズーム領域移動不可：ズーム領域なし")
            return

        self.rect.set_xy((new_x, new_y)) # ズーム領域の基本位置を更新
        self._apply_rotation() # 現在の回転角度を再適用 (中心が変わるため)

    def delete_rect(self) -> None:
        """ズーム領域を削除する"""
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
                self._last_valid_size_px = None # キャッシュもクリア
        else:
            self.logger.log(LogLevel.WARNING, "ズーム領域なし：削除スキップ")

    def get_properties(self) -> Optional[Tuple[float, float, float, float]]:
        """ズーム領域のプロパティ (x, y, width, height) を取得 (回転前の値)

        Returns:
            Optional[Tuple[float, float, float, float]]: (x, y, width, height)。矩形がない場合は None
        """
        if self.rect:
            # 注意: これらは回転前のズーム領域の基本的な幅と高さを返す
            return (self.rect.get_x(), self.rect.get_y(),
                    self.rect.get_width(), self.rect.get_height())
        return None

    # --- Undo/Redo 用メソッド ---
    def get_state(self) -> Optional[Dict[str, Any]]:
    # get_state, set_state は状態の保存・復元用。
    # 最小サイズやアスペクト比自体は config から読むので、state に含める必要はない。
    # _last_valid_size_px は含めておくべき。
        """現在の状態 (Undo用) を取得

        Returns:
            Optional[Dict[str, Any]]: 状態データ。矩形がない場合は None
        """
        props = self.get_properties()
        if props and self.rect: # rect が存在することも確認
            x, y, width, height = props
            # 状態に最後に有効だったピクセルサイズも保存
            last_valid_px = self._last_valid_size_px if self._last_valid_size_px else (0, 0)
            return {
                "x": x,
                "y": y,
                "width": width,
                "height": height,
                "angle": self._angle,
                "visible": self.rect.get_visible(),
                "edgecolor": self.rect.get_edgecolor(),
                "linestyle": self.rect.get_linestyle(),
                "last_valid_width_px": last_valid_px[0],
                "last_valid_height_px": last_valid_px[1],
            }
        # 矩形がない場合
        self.logger.log(LogLevel.WARNING, "矩形が存在しないため状態取得で None を返す")
        return None

    def set_state(self, state: Optional[Dict[str, Any]]):
        """指定された状態に矩形を復元 (Undo/Redo用)

        Args:
            state (Optional[Dict[str, Any]]): 状態データ
        """
        if not state:
            self.logger.log(LogLevel.WARNING, "Undo/Redo 不可：状態データなし、削除された状態へ復元")
            self.delete_rect()
            return

        color = self.ui_settings.get("fix_edge_color", "white")
        style = self.ui_settings.get("fix_edge_linestyle", "-")

        x = state.get("x")
        y = state.get("y")
        width = state.get("width")
        height = state.get("height")
        angle = state.get("angle", 0.0)
        visible = state.get("visible", True) # デフォルトは表示
        edgecolor = state.get("edgecolor", "white") # デフォルトは白
        linestyle = state.get("linestyle", "-") # デフォルトは実線
        last_valid_w_px = state.get("last_valid_width_px")
        last_valid_h_px = state.get("last_valid_height_px")

        # 必須パラメータのチェック
        if None in [x, y, width, height]:
             self.logger.log(LogLevel.ERROR, f"Undo/Redo 失敗：必須データ (x,y,w,h) が不足 {state}")
             # 状態データが無効なら矩形を削除する（安全策）
             self.delete_rect()
             return

        # --- 復元時もピクセルサイズチェックを行う ---
        # (内部で self.min_width_px, self.min_height_px を使用)
        if last_valid_w_px is not None and last_valid_h_px is not None:
             is_valid = self.is_valid_size_in_pixels(last_valid_w_px, last_valid_h_px)
             px_width, px_height = last_valid_w_px, last_valid_h_px
        else:
             is_valid, px_width, px_height = self._check_pixel_size(x, y, width, height)

        if not is_valid:
            self.logger.log(LogLevel.WARNING, f"Undo/Redo: 矩形復元スキップ（ピクセルサイズ無効 px_w={px_width:.1f}, px_h={px_height:.1f}）")
            self.delete_rect()
            return
        # --- チェックここまで ---

        # --- 矩形の作成または更新 ---
        # if not self.is_valid_size_in_pixels(width, height): # サイズが有効かチェック # is_valid でチェック済み
        #     self.logger.log(LogLevel.WARNING, f"Undo: 矩形復元スキップ（サイズ無効 w={width:.4f}, h={height:.4f}）")
        #     # 無効なサイズが指定された場合も、現在の矩形を削除する
        #     self.delete_rect()
        #     return
        if not self.rect: # 矩形が存在しない場合は作成
             self.rect = patches.Rectangle((x, y), width, height,
                                         linewidth=1, edgecolor=edgecolor, facecolor='none',
                                         linestyle=linestyle, visible=False) # 最初は非表示
             self.ax.add_patch(self.rect)
             self.logger.log(LogLevel.INFO, "Undo/Redo: 矩形が存在しなかったので新規作成")
        else: # 矩形が存在する場合、プロパティを設定
            self.rect.set_x(x)
            self.rect.set_y(y)
            self.rect.set_width(width)
            self.rect.set_height(height)
            self.rect.set_edgecolor(edgecolor) # エッジの色を復元
            self.rect.set_linestyle(linestyle) # 線のスタイルを復元
        self._angle = angle # 角度を設定
        self.rect.set_visible(visible) # 可視状態を復元
        # 復元したピクセルサイズをキャッシュに設定
        self._last_valid_size_px = (px_width, px_height)
        # 最後に回転を適用
        self._apply_rotation()
        self.logger.log(LogLevel.SUCCESS, "Undo/Redo: ズーム領域を復元完了", state)

    def get_center(self) -> Optional[Tuple[float, float]]:
        """ズーム領域の中心座標を取得 (回転前の座標系)

        Returns:
            Optional[Tuple[float, float]]: 中心座標 (x, y)。矩形がない、または幅/高さが0の場合は None
        """
        props = self.get_properties()
        if props:
            x, y, w, h = props
            if w <= 0 or h <= 0: # 幅や高さが 0 の場合も考慮
                self.logger.log(LogLevel.INFO, f"幅({w})または高さ({h})が 0 以下")
                return None
            center_x = x + w / 2
            center_y = y + h / 2
            return center_x, center_y
        return None

    def get_rotated_corners(self) -> Optional[list[Tuple[float, float]]]:
        """回転後の四隅の絶対座標を取得する

        Returns:
            Optional[list[Tuple[float, float]]]: 四隅の絶対座標 [(x1, y1), (x2, y2), (x3, y3), (x4, y4)]。
            矩形がない、プロパティがない、中心がない、または幅/高さが0の場合は None
        """
        props = self.get_properties()
        center = self.get_center()

        # 矩形がない、またはサイズが0の場合もNoneを返すように修正
        if not self.rect or props is None or center is None or props[2] <= 0 or props[3] <= 0:
            self.logger.log(LogLevel.WARNING, "回転後の角取得不可：矩形、プロパティ、中心のいずれか、またはサイズが 0")
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
        self._angle = angle % 360 # 0-360度の範囲に正規化
        self._apply_rotation()

    def _apply_rotation(self):
        """現在の角度に基づいて回転変換を適用する"""
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
            Optional[patches.Rectangle]: パッチオブジェクト。存在しない場合は None
        """
        return self.rect

    # --- 追加: ピクセルサイズ計算とチェックを行うヘルパーメソッド ---
    def _check_pixel_size(self, x: float, y: float, width: float, height: float) -> Tuple[bool, float, float]:
        """指定されたデータ座標の矩形のピクセルサイズを計算し、有効性を判定する

        Args:
            x (float): 矩形の左下 x 座標 (データ座標)
            y (float): 矩形の左下 y 座標 (データ座標)
            width (float): 矩形の幅 (データ座標)
            height (float): 矩形の高さ (データ座標)

        Returns:
            Tuple[bool, float, float]: (サイズが有効か, 計算されたピクセル幅, 計算されたピクセル高さ)
        """
        if width <= 0 or height <= 0:
            # データ座標でサイズが 0 以下なら明らかに無効
            return False, 0.0, 0.0

        try:
            # 矩形の対角線の2点 (左下、右上) をデータ座標で定義
            corner1_data = (x, y)
            corner2_data = (x + width, y + height)

            # 2点をピクセル座標に変換
            # 座標変換が利用可能かチェック (Axes が描画済みか)
            if not self.ax or not hasattr(self.ax, 'transData'):
                # キャッシュされた最後の有効なサイズを使用
                if self._last_valid_size_px:
                    return True, *self._last_valid_size_px
                self.logger.log(LogLevel.WARNING, "ピクセルサイズチェック不可: Axes が無効")
                return False, 0.0, 0.0 # 変換できない場合は無効とする

            corners_px = self.ax.transData.transform([corner1_data, corner2_data])
            corner1_px = corners_px[0]
            corner2_px = corners_px[1]

            # ピクセル座標での幅と高さを計算 (絶対値を取る)
            px_width = abs(corner2_px[0] - corner1_px[0])
            px_height = abs(corner2_px[1] - corner1_px[1])

            # ピクセルサイズが有効かチェック (インスタンス変数を使用)
            is_valid = self.is_valid_size_in_pixels(px_width, px_height)
            return is_valid, px_width, px_height

        except Exception as e:
            # 座標変換などでエラーが発生した場合
            self.logger.log(LogLevel.ERROR, f"ピクセルサイズチェック中にエラー: {e}")
            return False, 0.0, 0.0
