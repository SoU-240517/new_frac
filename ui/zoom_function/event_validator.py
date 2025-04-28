from dataclasses import dataclass
from matplotlib.axes import Axes
from matplotlib.backend_bases import MouseEvent, KeyEvent
from typing import Optional
from .debug_logger import DebugLogger
from .enums import LogLevel
from .rect_manager import RectManager

@dataclass
class ValidationResult:
    """イベント検証結果を格納するデータクラス
    - イベントの検証結果（真偽値）を保持する
    - イベントの種類（マウス、キーボード）に応じて必要な情報を持つ
    Attributes:
        is_in_axes (bool): イベントが指定されたAxes内で発生したか
        has_button (bool): マウスボタン情報があるか (MouseEventのみ該当)
        has_coords (bool): xdata, ydata 座標情報があるか
        has_rect (bool): ズーム領域があるか (未使用)
    """
    is_in_axes: bool = False
    has_button: bool = False
    has_coords: bool = False
    has_rect: bool = False

    @property
    def is_fully_valid(self) -> bool:
        """全ての主要なチェックが有効か
        Returns:
            bool: 全ての主要なチェックが有効か
        Notes:
            - has_button は on_motion などでは不要な場合があるため、
              is_fully_valid に含めるかはユースケースによる
            - ここでは基本的な描画操作に必要な is_in_axes と has_coords を基準とする
        """
        return self.is_in_axes and self.has_coords

    @property
    def is_press_valid(self) -> bool:
        """マウスプレスイベントとして基本的な要件を満たすか
        Returns:
            bool: 基本的な要件を満たすか
        """
        return self.is_in_axes and self.has_button and self.has_coords

class EventValidator:
    """イベントの妥当性を検証するクラス
    - イベントの種類に応じて必要な情報の有無を検証する
    - 検証結果を ValidationResult で返す
    Attributes:
        logger: ログ出力用の DebugLogger インスタンス
    Notes:
        - MouseEvent, KeyEvent などのイベントを扱う
    """
    def __init__(self, logger: DebugLogger):
        self.logger = logger

    def validate_event(self, event, ax: Axes) -> ValidationResult:
        """イベントの妥当性を検証する
        - イベントの種類に応じて必要な情報の有無を検証する
        Args:
            event: MouseEvent または KeyEvent オブジェクト
            ax: Matplotlib の Axes オブジェクト
        Returns:
            ValidationResult: 検証結果を格納したオブジェクト
        Raises:
            TypeError: サポートされていないイベント型の場合
        """
        result = ValidationResult()

        if isinstance(event, KeyEvent):
            result.is_in_axes = (event.inaxes == ax)
            result.has_coords = False  # KeyEvent は座標情報を持たない
            result.has_button = False # KeyEvent はボタン情報を持たない
            if not result.is_in_axes:
                self.logger.log(LogLevel.DEBUG, f"イベントが期待されるAxes外で発生: {event}")
        elif isinstance(event, MouseEvent):
            self._validate_axes(event, ax, result)
            self._validate_button(event, result)
            self._validate_coordinates(event, result)
        else:
            raise TypeError(f"Unsupported event type: {type(event)}")

        return result

    def _validate_axes(self, event: MouseEvent, ax: Axes, result: ValidationResult) -> None:
        """イベントが発生したAxesが期待されたものであるかを検証
        Args:
            event (MouseEvent): マウスイベント
            ax (Axes): Matplotlib の Axes オブジェクト
            result (ValidationResult): 検証結果を格納するオブジェクト
        """
        result.is_in_axes = (event.inaxes == ax)

    def _validate_button(self, event: MouseEvent, result: ValidationResult) -> None:
        """マウスボタン情報の有無を検証
        Args:
            event (MouseEvent): マウスイベント
            result (ValidationResult): 検証結果を格納するオブジェクト
        """
        result.has_button = (event.button is not None)

    def _validate_coordinates(self, event: MouseEvent, result: ValidationResult) -> None:
        """座標情報の有無を検証
        Args:
            event (MouseEvent): マウスイベント
            result (ValidationResult): 検証結果を格納するオブジェクト
        """
        result.has_coords = (event.xdata is not None and event.ydata is not None)
