import matplotlib.patches as patches
import numpy as np
from matplotlib.axes import Axes
from typing import Callable, Optional, Dict, Any
from debug import DebugLogger, LogLevel
from validator import EventValidator
from .cursor_manager import CursorManager
from .enum_rect import ZoomState
from .event_handler_core import EventHandler
from .rect_manager import RectManager
from .zoom_state_handler import ZoomStateHandler

class ZoomSelector:
    """ズーム領域の描画と編集を管理する主要クラス
    - マウス操作によるズーム領域の描画
    - 描画したズーム領域の編集（リサイズ、回転）
    - ズーム操作の状態管理
    """

    def __init__(self,
                ax: Axes,
                on_zoom_confirm: Callable[[float, float, float, float, float], None],
                on_zoom_cancel: Callable[[], None],
                logger: DebugLogger,
                config: Dict[str, Any]
    ):
        """ZoomSelector クラスのコンストラクタ
        - ZoomSelectorの初期化
        - 各コンポーネントの初期化と設定
        Args:
            ax: Matplotlib の Axes オブジェクト
            on_zoom_confirm: ズーム確定時に呼び出すコールバック関数。引数として (x, y, w, h, rotation_angle) を取る
            on_zoom_cancel: ズームキャンセル時に呼び出すコールバック関数。引数はなし
            logger: ログ出力用の DebugLogger インスタンス
            config: 設定データを含む辞書
        """
        self.config = config
        self._initialize_components(ax, logger)
        self._setup_callbacks(on_zoom_confirm, on_zoom_cancel)
        self._connect_events()

    def _initialize_components(self, ax: Axes, logger: DebugLogger) -> None:
        """コンポーネントの初期化
        - 各コンポーネント（状態ハンドラ、矩形マネージャ、カーソルマネージャ、イベントハンドラ）の初期化を行う
        - クラス内で使用する変数の初期化
        Args:
            ax: Matplotlib の Axes オブジェクト
            logger: ログ出力用の DebugLogger インスタンス
        """
        self.logger = logger
        self.ax = ax
        self.canvas = ax.figure.canvas

        # キャッシュ初期化
        self._cached_rect_patch: Optional[patches.Rectangle] = None # 最後に描画された矩形パッチをキャッシュ
        self._last_cursor_inside_state: Optional[bool] = None # 最後に記録されたカーソルが矩形内にあるかの状態

        # 依存コンポーネントの初期化
        self._initialize_state_handler()
        self._initialize_rect_manager()
        self._initialize_cursor_manager()
        self._initialize_event_handler()

    def _setup_callbacks(self, on_zoom_confirm, on_zoom_cancel) -> None:
        """コールバック関数の設定
        - ズーム確定時とキャンセル時に呼び出すコールバック関数を登録する
        Args:
            on_zoom_confirm: ズーム確定時に呼び出すコールバック関数
            on_zoom_cancel: ズームキャンセル時に呼び出すコールバック関数
        """
        self.on_zoom_confirm = on_zoom_confirm
        self.on_zoom_cancel = on_zoom_cancel

    def _initialize_state_handler(self) -> None:
        """ZoomStateHandlerの初期化
        - ズーム操作の状態を管理する ZoomStateHandler のインスタンスを生成する
        """
        self.logger.log(LogLevel.INIT, "ZoomStateHandler クラスのインスタンスを作成")
        self.state_handler = ZoomStateHandler(
            initial_state=ZoomState.NO_RECT,
            logger=self.logger,
            canvas=self.canvas
        )

    def _initialize_rect_manager(self) -> None:
        """RectManagerの初期化
        - ズーム領域の矩形描画と変形を管理する RectManager のインスタンスを生成する
        """
        self.logger.log(LogLevel.INIT, "RectManager クラスのインスタンスを作成")
        self.rect_manager = RectManager(self.ax, self.logger, self.config)

    def _initialize_cursor_manager(self) -> None:
        """CursorManagerの初期化
        - カーソルの表示を管理する CursorManager のインスタンスを生成する
        """
        self.logger.log(LogLevel.INIT, "CursorManager クラスのインスタンスを作成")
        self.cursor_manager = CursorManager(self, self.logger)

    def _initialize_event_handler(self) -> None:
        """EventHandlerの初期化
        - マウスイベントを処理する EventHandler のインスタンスを生成し、各コンポーネントとの連携を設定する
        """
        self.logger.log(LogLevel.INIT, "EventHandler クラスのインスタンスを作成")
        self.validator = EventValidator(self.logger)
        self.event_handler = EventHandler(
            self,
            self.state_handler,
            self.rect_manager,
            self.cursor_manager,
            self.validator,
            self.logger,
            self.canvas,
            self.config
        )
        self.state_handler.event_handler = self.event_handler

    def _connect_events(self) -> None:
        """イベントハンドラの接続
        - 各種イベントをイベントハンドラに接続し、マウス操作を監視する
        """
        self.logger.log(LogLevel.CALL, "全イベント接続開始")
        self.event_handler.connect()
        self.cursor_manager.set_default_cursor()

    def cursor_inside_rect(self, event) -> bool:
        """マウスカーソル位置がズーム領域内にあるか判定
        - マウスカーソルが現在ズーム領域内にあるかどうかを判定する
        Args:
            event: MouseEvent オブジェクト
        Returns:
            bool: カーソルがズーム領域内にある場合は True, それ以外は False
        """
        if not self._has_valid_rect_cache():
            return False

        rect_patch = self._cached_rect_patch
        if rect_patch is None or not rect_patch.get_visible():
            return False

        contains, _ = rect_patch.contains(event)
        if contains != self._last_cursor_inside_state:
            self.logger.log(LogLevel.DEBUG, f"カーソル：ズーム領域 {'内' if contains else '外'}")
            self._last_cursor_inside_state = contains

        return contains

    def _has_valid_rect_cache(self) -> bool:
        """有効な矩形キャッシュがあるか確認
        - 矩形キャッシュが有効かどうかを確認し、必要であれば更新する
        Returns:
            bool: 有効な矩形キャッシュがある場合は True, それ以外は False
        """
        if self._cached_rect_patch is None:
            self._update_rect_cache()
        return self._cached_rect_patch is not None

    def _update_rect_cache(self) -> None:
        """矩形キャッシュを更新
        - RectManager から最新の矩形パッチを取得してキャッシュを更新する
        """
        self._cached_rect_patch = self.rect_manager.get_patch()
        self.logger.log(LogLevel.SUCCESS, "ズーム領域キャッシュ更新完了")

    def confirm_zoom(self) -> None:
        """ズーム確定処理
        - 現在のズーム領域を確定し、コールバック関数を呼び出して結果を通知する
        """
        self.logger.log(LogLevel.DEBUG, "ズーム確定処理開始")

        # 矩形プロパティを取得
        rect_props = self.rect_manager.get_properties()
        if rect_props is None:
            self.logger.log(LogLevel.WARNING, "決定不可：ズーム領域なし")
            return

        x, y, w, h = rect_props
        rotation_angle = self.rect_manager.get_rotation()

        self._handle_zoom_confirmation(x, y, w, h, rotation_angle)

    def _validate_rect_properties(self, rect_props) -> bool:
        """矩形プロパティのバリデーション
        - 矩形プロパティが有効かどうかを検証する
        Args:
            rect_props: 矩形プロパティ (x, y, w, h)
        Returns:
            bool: バリデーションが成功した場合は True, それ以外は False
        """
        if rect_props is None or rect_props[2] <= 0 or rect_props[3] <= 0:
            self.logger.log(LogLevel.WARNING, "角判定不可: 矩形プロパティ無効またはサイズゼロ")
            return False
        return True

    def _handle_zoom_confirmation(self, x, y, w, h, rotation_angle) -> None:
        """ズーム確定の実際の処理
        - ズーム確定時のコールバック関数を呼び出し、内部状態をリセットする
        Args:
            x: 矩形の左下の x 座標
            y: 矩形の左下の y 座標
            w: 矩形の幅
            h: 矩形の高さ
            rotation_angle: 矩形の回転角度
        """
        self.event_handler.clear_edit_history()
        self.logger.log(LogLevel.CALL, "ズーム確定：コールバック呼出し", {
            "x": x, "y": y, "w": w, "h": h, "angle": rotation_angle
        })
        self.on_zoom_confirm(x, y, w, h, rotation_angle)
        self._cleanup_after_zoom()

    def _cleanup_after_zoom(self) -> None:
        """ズーム後のクリーンアップ処理
        - ズーム操作後の状態をリセットし、矩形を削除する
        """
        self.rect_manager.delete_rect()
        self.invalidate_rect_cache()
        self.cursor_manager.set_default_cursor()
        self.event_handler.reset_internal_state()
        self.logger.log(LogLevel.DEBUG, "ズーム後のクリーンアップ完了")

    def cancel_zoom(self) -> None:
        """ズーム確定操作をキャンセル
        - ズーム確定操作をキャンセルし、コールバック関数を呼び出して通知する
        """
        self._cleanup_zoom()
        self.logger.log(LogLevel.CALL, "ズーム確定キャンセル：コールバック呼出し")
        self.on_zoom_cancel()
        self.cursor_manager.set_default_cursor()

    def reset(self) -> None:
        """ZoomSelectorの状態をリセット
        - ZoomSelector の状態を初期状態に戻す
        """
        self._cleanup_zoom()
        self.state_handler.update_state(ZoomState.NO_RECT, {"action": "リセット"})
        self.event_handler.reset_internal_state()
        self.cursor_manager.set_default_cursor()

    def _cleanup_zoom(self) -> None:
        """共通のクリーンアップ処理
        - ズーム操作に関連する状態をリセットする（矩形の削除、キャッシュの無効化、編集履歴のクリア）
        """
        self.event_handler.clear_edit_history()
        self.rect_manager.delete_rect()
        self.invalidate_rect_cache()

    def invalidate_rect_cache(self) -> None:
        """ズーム領域のキャッシュを無効化
        - ズーム領域のキャッシュを無効化し、次の描画時に更新されるようにする
        """
        if self._cached_rect_patch is not None:
            self.logger.log(LogLevel.DEBUG, "ズーム領域キャッシュ無効化")
            self._cached_rect_patch = None

    def pointer_near_corner(self, event) -> Optional[int]:
        """マウスカーソルに近い角の判定 (ピクセル座標系で判定)
        - マウスカーソルが矩形のどの角に近いかを判定する
        Args:
            event: MouseEvent オブジェクト
        Returns:
            Optional[int]: 近い角のインデックス (0-3, 左下から時計回り) または None (どの角にも近くない場合)
        """
        # --- イベントと矩形の基本情報を検証 ---
        # Axes 内で、x, y 座標があるか基本的なチェック
        if not self._validate_event(event):
            return None

        # 回転後の角の座標 (データ座標系) を取得
        rotated_corners_data = self.rect_manager.get_rotated_corners()
        if rotated_corners_data is None:
            self.logger.log(LogLevel.DEBUG, "角判定不可: 回転後の角座標(データ)なし")
            return None

        # 矩形のプロパティ (幅、高さなど) を取得 (データ座標系)
        rect_props = self.rect_manager.get_properties()
        # 矩形が存在し、幅と高さが正であるかチェック
        if not self._validate_rect_properties(rect_props): # 内部でログ出力あり
            return None
        # --- 検証ここまで ---

        # --- ピクセル座標系での計算 ---
        try:
            # マウスのピクセル座標を取得
            # event.x, event.y は Figure 左下からのピクセル座標
            mouse_x_px, mouse_y_px = event.x, event.y
            if mouse_x_px is None or mouse_y_px is None:
                 self.logger.log(LogLevel.WARNING, "角判定不可: マウスのピクセル座標なし")
                 return None

            # 角のデータ座標をピクセル座標に変換
            # self.ax.transData.transform は (N, 2) の numpy 配列を返す
            rotated_corners_px = self.ax.transData.transform(rotated_corners_data)

            # 固定の許容範囲 (ピクセル単位) を設定
            # この値 (例: 10ピクセル) は必要に応じて調整してください
            tol_pixels = 10.0

            # 各角とマウスカーソルの距離をピクセル座標系で計算
            for i, (corner_x_px, corner_y_px) in enumerate(rotated_corners_px):
                distance_px = np.hypot(mouse_x_px - corner_x_px, mouse_y_px - corner_y_px)

                # 許容範囲内であれば、その角のインデックスを返す
                if distance_px < tol_pixels:
                    self.logger.log(LogLevel.DEBUG, f"角 {i} が近いと判定 (距離: {distance_px:.2f} px)", {"tolerance_px": tol_pixels})
                    return i # 近い角のインデックスを返す

            # どの角にも近くない場合は None を返す
            return None

        except Exception as e:
            # 座標変換などでエラーが発生した場合
            self.logger.log(LogLevel.ERROR, f"角判定中にエラー発生: {e}")
            return None

    def _validate_event(self, event) -> bool:
        """イベントのバリデーション
        - イベントが処理に必要な基本的な情報を持っているかを検証する
        Args:
            event: MouseEvent オブジェクト
        Returns:
            bool: イベントが有効な場合は True, それ以外は False
        """
        validation_result = self.validator.validate_event(event, self.ax)
        return validation_result.is_fully_valid

    def _validate_rect_properties(self, rect_props) -> bool:
        """矩形プロパティのバリデーション
        - 矩形プロパティが有効（幅と高さが正）かどうかを検証する
        Args:
            rect_props: 矩形プロパティ (x, y, w, h, angle)
        Returns:
            bool: 矩形プロパティが有効な場合は True, それ以外は False
        """
        if rect_props is None or rect_props[2] <= 0 or rect_props[3] <= 0:
            self.logger.log(LogLevel.DEBUG, "角判定不可: 矩形プロパティ無効またはサイズゼロ")
            return False
        return True
