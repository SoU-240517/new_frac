import math # 角度計算で使用
from typing import Optional, TYPE_CHECKING, Dict, Any
from .enums import LogLevel, ZoomState

if TYPE_CHECKING:
    from .event_handler_core import EventHandler
#    from .cursor_manager import CursorManager
#    from .debug_logger import DebugLogger
#    from .rect_manager import RectManager
#    from .zoom_selector import ZoomSelector

class EventHandlersUtils:
    """EventHandler から呼び出され、補助的な機能（計算、Undo、状態リセットなど）を提供するクラス
    - 役割:
        - 角度計算などの共通処理を行う
        - 編集履歴の管理（Undo/Redo機能の基盤）を行う
        - 各種内部状態のリセット処理を行う
        - 親である EventHandler インスタンスを通じて、必要な情報にアクセスする
    """

    def __init__(self, core: 'EventHandler'):
        """ユーティリティハンドラのコンストラクタ

        Args:
            core: 親である EventHandler インスタンス
        """
        # 親である EventHandler のインスタンスを保持
        self.core = core # 親インスタンスへの参照

    # --- ヘルパーメソッド ---
    # event_handler.py にあった計算関連のメソッドをここに移動した
    def _calculate_angle(self, cx: float, cy: float, px: float, py: float) -> float:
        """中心点から点へのベクトル角度を計算 (度, -180から180)
        Args:
            cx (float): 中心点 x 座標
            cy (float): 中心点 y 座標
            px (float): 点 x 座標
            py (float): 点 y 座標
        Returns:
            float: ベクトル角度 (度, -180から180)
        """
        # このメソッドは親の情報を使わない計算だが、ユーティリティとしてここにまとめる
        return math.degrees(math.atan2(py - cy, px - cx))

    def _normalize_angle_diff(self, angle1: float, angle2: float) -> float:
        """角度差を -180度から180度の範囲に正規化
        Args:
            angle1 (float): 角度1
            angle2 (float): 角度2
        Returns:
            float: 正規化した角度差
        """
        # このメソッドは親の情報を使わない計算だが、ユーティリティとしてここにまとめる
        diff = angle1 - angle2
        while diff <= -180: diff += 360
        while diff > 180: diff -= 360
        return diff
    # --- ヘルパーメソッド ここまで ---

    # --- Undo 関連メソッド ---
    # event_handler.py にあった Undo 関連のメソッドをここに移動した
    def _add_history(self, state: Optional[Dict[str, Any]]):
        """編集履歴に状態を追加

        Args:
            state (Optional[Dict[str, Any]]): 状態情報
        """
        self.core.edit_history.append(state) # 親の edit_history リストに状態を追加（core を通じてアクセス）
        # 親の logger にログ出力依頼（core を通じてアクセス）
        self.core.logger.log(LogLevel.DEBUG, f"履歴追加: 現在の履歴数={len(self.core.edit_history)}")
        # メモリリークを防ぐため、履歴数に上限を設けることも検討（コメントアウトはそのまま）
        # MAX_HISTORY = 100
        # if len(self.core.edit_history) > MAX_HISTORY: # core を通じてアクセス
        #     self.core.edit_history.pop(0) # core を通じてアクセス（古い履歴を削除）

    def _remove_last_history(self):
        """最後の履歴を削除

        Returns:
            Optional[Dict[str, Any]]: 削除された状態情報
        """
        if self.core.edit_history:
             # 親の edit_history リストから最後の要素を削除（core を通じてアクセス）
            removed = self.core.edit_history.pop()
            self.core.logger.log(LogLevel.DEBUG, f"最後の履歴削除: 削除後の履歴数={len(self.core.edit_history)}")
            return removed
        return None

    # clear_edit_history は EventHandlerCore に残し、そこからこのメソッドを呼び出す形にする
    # 元の clear_edit_history メソッドの本体をここに移動した
    def clear_edit_history(self):
        """編集履歴をクリア"""
        self.core.edit_history.clear() # 親の edit_history リストをクリア（core を通じてアクセス）
        self.core.logger.log(LogLevel.SUCCESS, "編集履歴クリア完了")

    def _undo_last_edit(self):
        """ 最後に行った編集操作を元に戻す """
        # 親の edit_history リストの数をチェック（core を通じてアクセス）
        if len(self.core.edit_history) > 0: # 履歴が1つ以上あれば Undo 可能
            prev_state = self.core.edit_history.pop() # 現在の状態は破棄し、一つ前の状態を取り出す
            self.core.logger.log(LogLevel.DEBUG, "Undo実行", {"復元前の履歴数": len(self.core.edit_history) + 1})
            self.core.rect_manager.set_state(prev_state) # 親の rect_manager に状態復元を依頼
            self.core.zoom_selector.invalidate_rect_cache() # 親の zoom_selector にキャッシュ無効化を依頼
            # Undo 後も EDIT 状態なのでカーソル更新（親の cursor_manager にカーソル更新を依頼）
            self.core.cursor_manager.cursor_update(None, state=ZoomState.EDIT, is_rotating=self.core._alt_pressed)
            self.core.canvas.draw_idle() # 親の canvas に再描画を依頼
        else:
            self.core.logger.log(LogLevel.WARNING, "Undo不可: 編集履歴なし")

    def _undo_or_cancel_edit(self):
        """ ESCキーによるUndoまたは編集キャンセル """
        # 親の edit_history リストの数をチェック
        if len(self.core.edit_history) > 1: # 初期状態 + 1回以上の編集履歴があれば Undo
            self._undo_last_edit()
        elif len(self.core.edit_history) == 1: # 矩形作成直後などの場合
            self.core.logger.log(LogLevel.DEBUG, "ESC -> Undo履歴なし: ズーム領域編集キャンセル実行")
            self.clear_edit_history() # 履歴クリア
            self.core.zoom_selector.cancel_zoom() # ズームキャンセルを依頼 (ZoomSelector側)
            self.reset_internal_state() # 内部状態リセット (ここで再度履歴クリアされる)
            self.core.state_handler.update_state(ZoomState.NO_RECT, {"action": "ESCによる編集キャンセル"})
            self.core.cursor_manager.set_default_cursor()
            self.core.canvas.draw_idle()
        else: # 履歴 0 の場合 (通常 EDIT ではないはず)
            self.core.logger.log(LogLevel.WARNING, "履歴 0：キャンセル試行")
            self.core.zoom_selector.cancel_zoom() # ズームキャンセルを依頼
            self.reset_internal_state()
            self.core.state_handler.update_state(ZoomState.NO_RECT, {"action": "ESCによる編集キャンセル(履歴0)"})
            self.core.cursor_manager.set_default_cursor()
            self.core.canvas.draw_idle()
    # --- Undo 関連メソッド ここまで ---

    # --- 状態リセットメソッド群 ---
    # reset_internal_state は EventHandlerCore に残し、そこからこのメソッドを呼び出す形にする
    # 元の reset_internal_state メソッドの本体がここに移動した
    def reset_internal_state(self):
        """全ての内部状態と編集履歴をリセット"""
        self._reset_create_state()
        self._reset_move_state()
        self._reset_resize_state()
        self._reset_rotate_state()
        self.core._alt_pressed = False
        self.clear_edit_history()
        self.core.logger.log(LogLevel.SUCCESS, "EventHandler の内部状態と編集履歴をリセット完了")

    def _reset_create_state(self):
        self.core.start_x = None
        self.core.start_y = None
        self.core._create_logged = False

    def _reset_move_state(self):
        self.core.move_start_x = None
        self.core.move_start_y = None
        self.core.rect_start_pos = None
        self.core._move_logged = False

    def _reset_resize_state(self):
        self.core.resize_corner_index = None
        self.core.fixed_corner_pos = None
        self.core._resize_logged = False

    def _reset_rotate_state(self):
        self.core.rotate_start_mouse_pos = None
        self.core.rotate_center = None
        self.core.previous_vector_angle = None
        self.core._rotate_logged = False
    # --- 状態リセットメソッド群 ここまで ---
