from typing import Optional, Dict, Any, Protocol
from debug import DebugLogger, LogLevel
from .enum_rect import ZoomState

class CanvasProtocol(Protocol):
    """Canvasのインターフェースを定義
    - 画面描画を行うクラスが実装すべきメソッドを規定
    - ズーム操作時の画面更新に使用される
    
    Example:
        class MyCanvas:
            def draw_idle(self) -> None:
                # 画面を再描画する処理
                pass
    """
    def draw_idle(self) -> None: ...

class EventHandlerProtocol(Protocol):
    """イベントハンドラーのインターフェースを定義
    - 状態変更イベントを処理するクラスが実装すべきメソッドを規定
    - ズーム状態の変更を監視し、必要な処理を行う
    
    Example:
        class MyEventHandler:
            def on_state_changed(self, old_state: ZoomState, new_state: ZoomState) -> None:
                # 状態変更時の処理
                pass
    """
    def on_state_changed(self, old_state: ZoomState, new_state: ZoomState) -> None: ...

class ZoomStateHandler:
    """ズーム操作の状態を管理するクラス
    - ズーム状態の保持と更新、状態変更の通知を行う
    - イベント駆動型の状態管理を実現
    
    Attributes:
        _state (ZoomState): 現在のズーム状態
        logger (DebugLogger): デバッグログ出力用のインスタンス
        _event_handler (Optional[EventHandlerProtocol]): 状態変更イベントを処理するハンドラー
        _canvas (Optional[CanvasProtocol]): 画面描画を行うキャンバス
    
    Example:
        # 使用例
        logger = DebugLogger()
        handler = ZoomStateHandler(initial_state=ZoomState.NORMAL, logger=logger)
        handler.update_state(ZoomState.ZOOM_IN)
    """

    def __init__(
        self,
        initial_state: ZoomState,
        logger: DebugLogger,
        event_handler: Optional[EventHandlerProtocol] = None,
        canvas: Optional[CanvasProtocol] = None
    ):
        """ZoomStateHandler のコンストラクタ
        
        Args:
            initial_state (ZoomState): 初期状態
            logger (DebugLogger): ログ出力用の DebugLogger インスタンス
            event_handler (Optional[EventHandlerProtocol]): 
                状態変更イベントを処理するハンドラー
                None を指定するとイベント通知は行われない
            canvas (Optional[CanvasProtocol]): 
                画面描画を行うキャンバス
                None を指定すると画面更新は行われない
        """
        self.logger = logger
        self._state: ZoomState = initial_state
        self._event_handler = event_handler
        self._canvas = canvas

        self.logger.log(LogLevel.INIT, "ZoomStateHandler クラスのインスタンスを作成成功")

    @property
    def state(self) -> ZoomState:
        """現在の状態を取得
        
        Returns:
            ZoomState: 現在のズーム状態を返す
            状態は ZoomState クラスで定義された列挙型の値を返す
        """
        return self._state

    def update_state(self, new_state: ZoomState, context: Optional[Dict[str, Any]] = None) -> None:
        """状態を更新する
        - 現在の状態と異なる場合に状態を更新し、状態変更を通知する
        
        Args:
            new_state (ZoomState): 更新後の状態
            context (Optional[Dict[str, Any]]): 
                更新の理由や追加情報
                デバッグログに出力される
        
        Example:
            # 状態を更新
            handler.update_state(ZoomState.ZOOM_IN, context={"理由": "ユーザー操作"})
        """
        if self._state == new_state:
            return

        old_state = self._state
        self._state = new_state

        self._notify_state_change(old_state, new_state, context)

    def _notify_state_change(self, old_state: ZoomState, new_state: ZoomState, context: Optional[Dict[str, Any]] = None) -> None:
        """状態変更を通知する
        - 状態変更をログに出力し、イベントハンドラーとキャンバスに通知する
        
        Args:
            old_state (ZoomState): 変更前の状態
            new_state (ZoomState): 変更後の状態
            context (Optional[Dict[str, Any]]): 
                追加のコンテキスト情報
                デバッグログに出力される
        """
        log_context = {"旧": old_state.name, "新": new_state.name}
        if context:
            log_context.update(context)

        self.logger.log(LogLevel.SUCCESS, "状態更新成功", log_context)

        if self._event_handler:
            self._event_handler.on_state_changed(old_state, new_state)

        if self._canvas:
            self._canvas.draw_idle()
