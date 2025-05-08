from dataclasses import dataclass
from matplotlib.axes import Axes
from matplotlib.backend_bases import MouseEvent, KeyEvent
from typing import Optional
from debug import DebugLogger, LogLevel

@dataclass
class ValidationResult:
    """イベント検証結果を格納するデータクラス

    イベントの妥当性を検証し、必要な情報を保持するためのデータクラスです。
    マウスイベントとキーボードイベントの両方に対応しています。

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
            - KeyEvent の場合は has_button は常に False となる
        """
        return self.is_in_axes and self.has_coords

    @property
    def is_press_valid(self) -> bool:
        """マウスプレスイベントとして基本的な要件を満たすか

        Returns:
            bool: 基本的な要件を満たすか

        Notes:
            - マウスプレスイベントとして有効な条件は：
              1. イベントが指定されたAxes内で発生していること
              2. マウスボタン情報が存在すること
              3. 座標情報が存在すること
        """
        return self.is_in_axes and self.has_button and self.has_coords

class EventValidator:
    """イベントの妥当性を検証するクラス

    Matplotlibのイベント（MouseEvent, KeyEvent）の妥当性を検証し、
    検証結果を ValidationResult として返すクラスです。

    Attributes:
        logger: ログ出力用の DebugLogger インスタンス

    Notes:
        - MouseEvent: マウスクリック、ドラッグ、ホイールなどのイベント
        - KeyEvent: キーボード入力イベント
        - 検証対象は主に描画操作に関連するイベント
    """
    def __init__(self, logger: DebugLogger):
        self.logger = logger

    def validate_event(self, event, ax: Axes) -> ValidationResult:
        """イベントの妥当性を検証する

        イベントの種類に応じて必要な情報の有無を検証し、
        検証結果を ValidationResult として返します。

        Args:
            event: MouseEvent または KeyEvent オブジェクト
            ax: Matplotlib の Axes オブジェクト

        Returns:
            ValidationResult: 検証結果を格納したオブジェクト

        Raises:
            TypeError: サポートされていないイベント型の場合

        Notes:
            - KeyEvent の場合は座標情報（has_coords）は常に False となる
            - MouseEvent の場合は座標情報とボタン情報の両方が必要
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

        イベントが指定されたAxes内で発生したかを検証し、
        結果を ValidationResult に格納します。

        Args:
            event (MouseEvent): マウスイベント
            ax (Axes): Matplotlib の Axes オブジェクト
            result (ValidationResult): 検証結果を格納するオブジェクト
        """
        result.is_in_axes = (event.inaxes == ax)

    def _validate_button(self, event: MouseEvent, result: ValidationResult) -> None:
        """マウスボタン情報の有無を検証

        マウスイベントのボタン情報が存在するかを検証し、
        結果を ValidationResult に格納します。

        Args:
            event (MouseEvent): マウスイベント
            result (ValidationResult): 検証結果を格納するオブジェクト
        """
        result.has_button = (event.button is not None)

    def _validate_coordinates(self, event: MouseEvent, result: ValidationResult) -> None:
        """座標情報の有無を検証

        マウスイベントの座標情報（xdata, ydata）が存在するかを検証し、
        結果を ValidationResult に格納します。

        Args:
            event (MouseEvent): マウスイベント
            result (ValidationResult): 検証結果を格納するオブジェクト
        """
        result.has_coords = (event.xdata is not None and event.ydata is not None)
