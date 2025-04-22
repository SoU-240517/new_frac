from typing import Optional, Dict, Any, Protocol
from .debug_logger import DebugLogger
from .enums import ZoomState, LogLevel

class CanvasProtocol(Protocol):
    """Canvasのインターフェースを定義"""
    def draw_idle(self) -> None: ...

class EventHandlerProtocol(Protocol):
    """イベントハンドラーのインターフェースを定義"""
    def on_state_changed(self, old_state: ZoomState, new_state: ZoomState) -> None: ...

class ZoomStateHandler:
    """ズーム操作の状態を管理するクラス

    Attributes:
        _state (ZoomState): 現在のズーム状態
        logger (DebugLogger): デバッグログ用のインスタンス
        _event_handler (Optional[EventHandlerProtocol]): イベントハンドラー
        _canvas (Optional[CanvasProtocol]): キャンバス

    Methods:
        get_state: 現在の状態を取得
        update_state: 状態を更新
        _notify_state_change: 状態変更を通知
    """

    def __init__(
        self, 
        initial_state: ZoomState, 
        logger: DebugLogger, 
        event_handler: Optional[EventHandlerProtocol] = None, 
        canvas: Optional[CanvasProtocol] = None
    ):
        """ズーム状態管理クラスの初期化

        Args:
            initial_state (ZoomState): 初期状態
            logger (DebugLogger): ログ出力用の DebugLogger インスタンス
            event_handler (Optional[EventHandlerProtocol]): イベントハンドラー
            canvas (Optional[CanvasProtocol]): キャンバス
        """
        self.logger = logger
        self._state: ZoomState = initial_state
        self._event_handler = event_handler
        self._canvas = canvas

    @property
    def state(self) -> ZoomState:
        """現在の状態を取得"""
        return self._state

    def update_state(self, new_state: ZoomState, context: Optional[Dict[str, Any]] = None) -> None:
        """状態を更新

        Args:
            new_state (ZoomState): 更新後の状態
            context (Optional[Dict[str, Any]]): 更新の理由を記録するコンテキスト情報
        """
        if self._state == new_state:
            return

        old_state = self._state
        self._state = new_state

        self._notify_state_change(old_state, new_state, context)

    def _notify_state_change(self, old_state: ZoomState, new_state: ZoomState, context: Optional[Dict[str, Any]] = None) -> None:
        """状態変更を通知

        Args:
            old_state (ZoomState): 変更前の状態
            new_state (ZoomState): 変更後の状態
            context (Optional[Dict[str, Any]]): 追加のコンテキスト情報
        """
        log_context = {"旧": old_state.name, "新": new_state.name}
        if context:
            log_context.update(context)
        
        self.logger.log(LogLevel.SUCCESS, "状態更新成功", log_context)

        if self._event_handler:
            self._event_handler.on_state_changed(old_state, new_state)

        if self._canvas:
            self._canvas.draw_idle()  # draw_idleを使用して非同期描画
