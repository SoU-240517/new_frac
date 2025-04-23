import matplotlib.transforms as transforms
import matplotlib.patches as patches
import numpy as np
from matplotlib.axes import Axes
from typing import Callable, Optional, Tuple
from .cursor_manager import CursorManager
from .debug_logger import DebugLogger
from .enums import ZoomState, LogLevel
from .event_handler_core import EventHandler
from .event_validator import EventValidator, ValidationResult
from .rect_manager import RectManager
from .zoom_state_handler import ZoomStateHandler

class ZoomSelector:
    """ズーム領域の描画と編集を管理する主要クラス
    - 役割:
        - マウスドラッグでズーム領域を描画する
        - リサイズや回転を管理する
        - ズーム操作の状態管理を行う
    """

    def __init__(self,
                ax: Axes,
                on_zoom_confirm: Callable[[float, float, float, float, float], None],
                on_zoom_cancel: Callable[[], None],
                logger: DebugLogger
    ):
        """ZoomSelector クラスのコンストラクタ（親: FractalCanvas）
        Args:
            ax (Axes): Matplotlib の Axes オブジェクト
            on_zoom_confirm (Callable): ズーム確定時のコールバック関数
            on_zoom_cancel (Callable): ズームキャンセル時のコールバック関数
            logger (DebugLogger): ログ出力用の DebugLogger インスタンス
        """
        self._initialize_components(ax, logger)
        self._setup_callbacks(on_zoom_confirm, on_zoom_cancel)
        self._connect_events()

    def _initialize_components(self, ax: Axes, logger: DebugLogger) -> None:
        """コンポーネントの初期化を行う
        Args:
            ax (Axes): Matplotlib の Axes オブジェクト
            logger (DebugLogger): ログ出力用の DebugLogger インスタンス
        """
        self.logger = logger
        self.ax = ax
        self.canvas = ax.figure.canvas

        # キャッシュ初期化
        self._cached_rect_patch: Optional[patches.Rectangle] = None
        self._last_cursor_inside_state: Optional[bool] = None

        # 依存コンポーネントの初期化
        self._initialize_state_handler()
        self._initialize_rect_manager()
        self._initialize_cursor_manager()
        self._initialize_event_handler()

    def _setup_callbacks(self, on_zoom_confirm, on_zoom_cancel) -> None:
        """コールバック関数を設定する
        Args:
            on_zoom_confirm (Callable): ズーム確定時のコールバック関数
            on_zoom_cancel (Callable): ズームキャンセル時のコールバック関数
        """
        self.on_zoom_confirm = on_zoom_confirm
        self.on_zoom_cancel = on_zoom_cancel

    def _initialize_state_handler(self) -> None:
        """ZoomStateHandlerの初期化"""
        self.logger.log(LogLevel.INIT, "ZoomStateHandler クラスのインスタンスを作成")
        self.state_handler = ZoomStateHandler(
            initial_state=ZoomState.NO_RECT,
            logger=self.logger,
            canvas=self.canvas
        )

    def _initialize_rect_manager(self) -> None:
        """RectManagerの初期化"""
        self.logger.log(LogLevel.INIT, "RectManager クラスのインスタンスを作成")
        self.rect_manager = RectManager(self.ax, self.logger)

    def _initialize_cursor_manager(self) -> None:
        """CursorManagerの初期化"""
        self.logger.log(LogLevel.INIT, "CursorManager クラスのインスタンスを作成")
        self.cursor_manager = CursorManager(self, self.logger)

    def _initialize_event_handler(self) -> None:
        """EventHandlerの初期化"""
        self.logger.log(LogLevel.INIT, "EventHandler クラスのインスタンスを作成")
        self.validator = EventValidator(self.logger)
        self.event_handler = EventHandler(
            self,
            self.state_handler,
            self.rect_manager,
            self.cursor_manager,
            self.validator,
            self.logger,
            self.canvas
        )
        self.state_handler.event_handler = self.event_handler

    def _connect_events(self) -> None:
        """イベントハンドラの接続"""
        self.logger.log(LogLevel.CALL, "全イベント接続開始")
        self.event_handler.connect()
        self.cursor_manager.set_default_cursor()

    def cursor_inside_rect(self, event) -> bool:
        """マウスカーソル位置がズーム領域内か判定する

        Args:
            event: MouseEvent オブジェクト
        Returns:
            bool: カーソルがズーム領域内かどうか
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
        Returns:
            bool: 有効な矩形キャッシュがあるか
        """
        if self._cached_rect_patch is None:
            self._update_rect_cache()
        return self._cached_rect_patch is not None

    def _update_rect_cache(self) -> None:
        """矩形キャッシュを更新"""
        self._cached_rect_patch = self.rect_manager.get_patch()
        self.logger.log(LogLevel.SUCCESS, "ズーム領域キャッシュ更新完了")

    def confirm_zoom(self) -> None:
        """ズーム確定処理"""
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
        Args:
            rect_props: 矩形プロパティ
        Returns:
            bool: バリデーション結果
        """
        if rect_props is None or rect_props[2] <= 0 or rect_props[3] <= 0:
            self.logger.log(LogLevel.WARNING, "角判定不可: 矩形プロパティ無効またはサイズゼロ")
            return False
        return True

    def _handle_zoom_confirmation(self, x, y, w, h, rotation_angle) -> None:
        """ズーム確定の実際の処理
        Args:
            x: X 座標
            y: Y 座標
            w: 幅
            h: 高さ
            rotation_angle: 回転角度
        """
        self.event_handler.clear_edit_history()
        self.logger.log(LogLevel.CALL, "ズーム確定：コールバック呼出し", {
            "x": x, "y": y, "w": w, "h": h, "angle": rotation_angle
        })
        self.on_zoom_confirm(x, y, w, h, rotation_angle)
        self._cleanup_after_zoom()

    def _cleanup_after_zoom(self) -> None:
        """ズーム後のクリーンアップ処理"""
        self.rect_manager.delete_rect()
        self.invalidate_rect_cache()
        self.cursor_manager.set_default_cursor()
        self.event_handler.reset_internal_state()
        self.logger.log(LogLevel.DEBUG, "ズーム後のクリーンアップ完了")

    def cancel_zoom(self) -> None:
        """ズーム確定操作をキャンセル"""
        self._cleanup_zoom()
        self.logger.log(LogLevel.CALL, "ズーム確定キャンセル：コールバック呼出し")
        self.on_zoom_cancel()
        self.cursor_manager.set_default_cursor()

    def reset(self) -> None:
        """ZoomSelectorの状態をリセット"""
        self._cleanup_zoom()
        self.state_handler.update_state(ZoomState.NO_RECT, {"action": "リセット"})
        self.event_handler.reset_internal_state()
        self.cursor_manager.set_default_cursor()

    def _cleanup_zoom(self) -> None:
        """共通のクリーンアップ処理"""
        self.event_handler.clear_edit_history()
        self.rect_manager.delete_rect()
        self.invalidate_rect_cache()

    def invalidate_rect_cache(self) -> None:
        """ズーム領域のキャッシュを無効化"""
        if self._cached_rect_patch is not None:
            self.logger.log(LogLevel.DEBUG, "ズーム領域キャッシュ無効化")
            self._cached_rect_patch = None

    def pointer_near_corner(self, event) -> Optional[int]:
        """マウスカーソルに近い角の判定
        Args:
            event: MouseEvent オブジェクト
        Returns:
            Optional[int]: 近い角のインデックス (0-3) または None
        """
        if not self._validate_event(event):
            return None

        rotated_corners = self.rect_manager.get_rotated_corners()
        if rotated_corners is None:
            self.logger.log(LogLevel.DEBUG, "角判定不可: 回転後の角座標なし")
            return None

        rect_props = self.rect_manager.get_properties()
        if not self._validate_rect_properties(rect_props):
            return None

        width, height = rect_props[2], rect_props[3]
        min_dim = min(width, height)

        tol = max(0.1 * min_dim, 0.02) # 短辺の10% or 最小許容範囲 (データ座標系)

        for i, (corner_x, corner_y) in enumerate(rotated_corners):
            if event.xdata is None or event.ydata is None: continue # 型ガード
            distance = np.hypot(event.xdata - corner_x, event.ydata - corner_y)
            if distance < tol:
                return i # 近い角のインデックスを返す
        return None # どの角にも近くない

    def _validate_event(self, event) -> bool:
        """イベントのバリデーション
        Args:
            event: MouseEvent オブジェクト
        Returns:
            bool: 基本的な要件を満たすか
        """
        validation_result = self.validator.validate_event(event, self.ax)
        return validation_result.is_fully_valid

    def _validate_rect_properties(self, rect_props) -> bool:
        """矩形プロパティのバリデーション
        Args:
            rect_props: 矩形プロパティ (x, y, w, h, angle)
        Returns:
            bool: バリデーション結果
        """
        if rect_props is None or rect_props[2] <= 0 or rect_props[3] <= 0:
            self.logger.log(LogLevel.DEBUG, "角判定不可: 矩形プロパティ無効またはサイズゼロ")
            return False
        return True
