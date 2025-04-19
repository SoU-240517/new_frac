from typing import Optional, Dict, Any
from .debug_logger import DebugLogger
from .enums import ZoomState, LogLevel

class ZoomStateHandler:
    """ズーム操作の状態（作成中/編集中など）を管理するクラス
    - 役割:
        - 状態を取得する
        - 状態を更新する
    """
    def __init__(self, initial_state: ZoomState, logger: DebugLogger, event_handler=None, canvas=None):
        self.logger = logger
        self._state: ZoomState = initial_state
        self.event_handler = event_handler
        self.canvas = canvas

    def get_state(self) -> ZoomState:
        """ 現在の状態を取得 """
        return self._state

    def update_state(self, new_state: ZoomState, context: Optional[Dict[str, Any]] = None):
        """ 状態を更新 """
        if self._state == new_state:
            return

        old_state_name = self._state.name
        self._state = new_state

        log_context = {"旧": old_state_name, "新": new_state.name}
        if context:
            log_context.update(context) # コンテキストをログコンテキストに追加
        self.logger.log(LogLevel.SUCCESS, "成功", log_context)
