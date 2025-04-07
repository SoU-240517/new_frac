from typing import Optional, Dict, Any
from .enums import ZoomState, LogLevel
from .debug_logger import DebugLogger

class ZoomStateHandler:
    """ ZoomSelectorの状態を管理するクラス """
    def __init__(self, initial_state: ZoomState, logger: DebugLogger):
        print('\033[34m'+'INI: ZoomStateHandler: zoom_state_handler.py'+'\033[0m')
        self._state: ZoomState = initial_state
        self.logger = logger
        self.logger.log(LogLevel.INFO, f"Initial state: {self._state.name}")

    def get_state(self) -> ZoomState:
        """ 現在の状態を取得 """
        print('\033[32m'+'get_state: ZoomStateHandler: zoom_state_handler.py'+'\033[0m')
        return self._state

    def update_state(self, new_state: ZoomState, context: Optional[Dict[str, Any]] = None):
        """ 状態を更新 """
        print('\033[32m'+'update_state: ZoomStateHandler: zoom_state_handler.py'+'\033[0m')
        if self._state == new_state:
            return # 状態が変わらない場合は何もしない

        old_state_name = self._state.name
        self._state = new_state
        log_context = {"old_state": old_state_name, "new_state": new_state.name}
        if context:
            log_context.update(context)
        self.logger.log(LogLevel.INFO, "State changed", log_context)
