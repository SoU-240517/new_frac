from typing import Optional, Dict, Any
from .debug_logger import DebugLogger
from .enums import ZoomState, LogLevel

class ZoomStateHandler:
    """ ZoomSelectorの状態を管理するクラス """
    def __init__(self, initial_state: ZoomState, logger: DebugLogger, event_handler=None, canvas=None):
        self.logger = logger
        self.logger.log(LogLevel.INIT, "ZoomStateHandler")
        self._state: ZoomState = initial_state
        self.event_handler = event_handler
        self.canvas = canvas

    def get_state(self) -> ZoomState:
        """ 現在の状態を取得 """
        self.logger.log(LogLevel.INFO, "Get status.", {"state": self._state.name})
        return self._state

    def update_state(self, new_state: ZoomState, context: Optional[Dict[str, Any]] = None):
        """ 状態を更新 """
        if self._state == new_state:
            return

        old_state_name = self._state.name
        self._state = new_state

        log_context = {"old_state": old_state_name, "new_state": new_state.name}
        if context:
            log_context.update(context) # コンテキストをログコンテキストに追加
        self.logger.log(LogLevel.INFO, "State changed.", log_context)

        # NO_RECT状態になったらモーションイベントを切断
#        if new_state == ZoomState.NO_RECT:
#            if self.event_handler and hasattr(self.event_handler, '_cid_motion') and self.event_handler._cid_motion is not None:
#                self.canvas.mpl_disconnect(self.event_handler._cid_motion)
#                self.event_handler._cid_motion = None
        # CREATE状態になったらモーションイベントを再接続
#        elif new_state == ZoomState.CREATE and self.event_handler and self.event_handler._cid_motion is None:
#            self.event_handler._cid_motion = self.canvas.mpl_connect('motion_notify_event', self.event_handler.on_motion)
