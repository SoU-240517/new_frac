from dataclasses import dataclass
from matplotlib.axes import Axes
from matplotlib.backend_bases import MouseEvent
from typing import Optional
from .debug_logger import DebugLogger
from .enums import LogLevel
from .rect_manager import RectManager

@dataclass
class ValidationResult:
    """イベント検証結果を格納するデータクラス"""
    is_in_axes: bool = False   # イベントが指定されたAxes内で発生したか
    has_button: bool = False  # マウスボタン情報があるか (MouseEventのみrelevant)
    has_coords: bool = False  # xdata, ydata 座標情報があるか
    has_rect: bool = False  # ズーム領域があるか

    @property
    def is_fully_valid(self) -> bool:
        """全ての主要なチェックが有効か（ここでは is_in_axes と has_coords）"""
        # 注意: has_button は on_motion などでは不要な場合があるため、
        # is_fully_valid に含めるかはユースケースによる
        # ここでは基本的な描画操作に必要な is_in_axes と has_coords を基準とする
        return self.is_in_axes and self.has_coords

    @property
    def is_press_valid(self) -> bool:
        """マウスプレスイベントとして基本的な要件を満たすか"""
        return self.is_in_axes and self.has_button and self.has_coords

class EventValidator:
    """イベントの妥当性を検証するクラス
    - 役割:
        - 基本的なイベント検証をまとめて行い、結果を ValidationResult で返す
    """
    @staticmethod
    def validate_event(event: MouseEvent, ax: Axes, logger: DebugLogger) -> ValidationResult:
        """
        基本的なイベント検証をまとめて行い、結果を ValidationResult で返す（失敗項目はログを出力）
        """
        result = ValidationResult() # 検証結果を格納するオブジェクトを初期化
        # 1. Axes内かチェック
        result.is_in_axes = (event.inaxes == ax)
        if not result.is_in_axes:
            logger.log(LogLevel.WARNING, "検証失敗: イベントが期待されるAxes外で発生")
        # 2. ボタン情報があるかチェック (MouseEventのみ)
        #    KeyEvent など他のイベントタイプを将来的に扱う場合は event の型チェックが必要
        if isinstance(event, MouseEvent):
            result.has_button = (event.button is not None)
            if not result.has_button:
                logger.log(LogLevel.DEBUG, "検証情報: マウスボタン情報なし")
        else:
            result.has_button = False # MouseEvent以外はボタン情報なしとする
        # 3. 座標情報があるかチェック
        result.has_coords = (event.xdata is not None and event.ydata is not None)
        if not result.has_coords:
            logger.log(LogLevel.WARNING, "検証失敗: イベント座標データ(xdata/ydata)なし")
        return result # すべてのチェックが終わったら結果オブジェクトを返す
