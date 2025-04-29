from matplotlib.backend_bases import MouseEvent, MouseButton, KeyEvent
from typing import Optional, TYPE_CHECKING, Tuple, List, Dict, Any
from .enums import LogLevel, ZoomState

if TYPE_CHECKING:
    from .event_handler_core import EventHandler

class EventHandlersPrivate:
    """EventHandler から呼び出され、具体的なマウス/キーボードイベント処理を行うクラス
    - 矩形の作成、移動、リサイズ、回転などの具体的な操作を実行する
    - EventHandler インスタンスを通じて、他のコンポーネントや状態にアクセスする
    Attributes:
        core: 親である EventHandler インスタンス
    """

    # --- コンストラクタ ---
    def __init__(self, core: 'EventHandler'):
        """EventHandlersPrivate クラスのコンストラクタ
        Args:
            core: 親である EventHandler インスタンス
        """
        self.core = core

    # --- プライベートハンドラメソッド ---
    # --- Press イベントハンドラ ---
    def handle_press_no_rect_left(self, event: MouseEvent) -> None:
        """NO_RECT 状態で左クリック：矩形作成開始
        - 矩形作成状態に移行し、矩形を描画する始点を記録する
        - 矩形を初期化し、キャンバスを更新する
        Args:
            event: MouseEvent オブジェクト
        """
        self.core.state_handler.update_state(ZoomState.CREATE, {"action": "ズーム領域設置開始"})
        # イベント座標がNoneの場合は処理を中断
        if event.xdata is None or event.ydata is None: return
        # 始点を記録し、矩形を初期化
        self.core.start_x, self.core.start_y = event.xdata, event.ydata
        self.core.rect_manager.setup_rect(self.core.start_x, self.core.start_y)
        self.core.zoom_selector.invalidate_rect_cache()
        # カーソルを更新し、キャンバスを再描画
        self.core.cursor_manager.cursor_update(
            event,
            state=self.core.state_handler.state
        )
        self.core._create_logged = False
        self.core.canvas.draw_idle()
        self.core.utils._add_history(None)

    def dispatch_press_edit_left(self, event: MouseEvent) -> None:
        """EDIT 状態で左クリック：回転/リサイズ/移動の開始を判定
        - Altキーの状態とクリック位置に応じて、回転、リサイズ、または移動の処理を分岐する
        Args:
            event: MouseEvent オブジェクト
        """
        # クリック位置が矩形の角に近いかを判定
        corner_index = self.core.zoom_selector.pointer_near_corner(event)
        # クリック位置が矩形の内側かを判定
        is_inside = self.core.zoom_selector.cursor_inside_rect(event)

        # Altキーが押されている場合、回転処理を開始
        if self.core._alt_pressed and corner_index is not None:
            self._handle_press_edit_start_rotating(event, corner_index)
        # Altキーが押されておらず、角に近い場合、リサイズ処理を開始
        elif not self.core._alt_pressed and corner_index is not None:
            self._handle_press_edit_start_resizing(event, corner_index)
        # Altキーが押されておらず、矩形の内側をクリックした場合、移動処理を開始
        elif not self.core._alt_pressed and is_inside:
            self._handle_press_edit_start_moving(event)
        # どの条件にも合致しない場合は何もしない

    def _handle_press_edit_start_rotating(self, event: MouseEvent, corner_index: int) -> None:
        """EDIT 状態 + Alt + 角で左クリック: 回転開始
        - 回転の中心点と開始角度を計算し、回転状態に移行する
        Args:
            event: MouseEvent オブジェクト
            corner_index: 回転開始する角のインデックス
        """
        # 現在の矩形状態を保存
        current_state_for_history = self.core.rect_manager.get_state()
        # 矩形の中心座標を取得
        center = self.core.rect_manager.get_center()
        # 中心座標とイベント座標が有効な場合に回転処理を開始
        if center and event.xdata is not None and event.ydata is not None:
            self.core.utils._add_history(current_state_for_history)
            self.core.rotate_center = center
            self.core.rotate_start_mouse_pos = (event.xdata, event.ydata)
            # 回転開始角度を計算
            start_vector_angle = self.core.utils._calculate_angle(center[0], center[1], event.xdata, event.ydata)
            self.core.previous_vector_angle = start_vector_angle
            self.core.logger.log(LogLevel.DEBUG, f"回転開始パラメータ: 中心={center}, 開始角度={start_vector_angle:.2f}")
            self.core.state_handler.update_state(ZoomState.ROTATING, {"action": "回転開始", "角": corner_index})
            self.core.cursor_manager.cursor_update(
                event,
                state=self.core.state_handler.state,
                near_corner_index=corner_index,
                is_rotating=True
            )
            self.core._rotate_logged = False
        else:
            self.core.logger.log(LogLevel.ERROR, "回転不可：中心座標またはイベント座標なし")

    def _handle_press_edit_start_resizing(self, event: MouseEvent, corner_index: int) -> None:
        """EDIT 状態 + 角で左クリック：リサイズ開始
        - リサイズの固定点を設定し、リサイズ状態に移行する
        Args:
            event: MouseEvent オブジェクト
            corner_index: リサイズ開始する角のインデックス
        """
        # 現在の矩形状態を保存
        current_state_for_history = self.core.rect_manager.get_state()
        # 回転後の角座標を取得
        rotated_corners = self.core.rect_manager.get_rotated_corners()
        # 回転後の角座標が存在する場合にリサイズ処理を開始
        if rotated_corners:
            self.core.utils._add_history(current_state_for_history)
            self.core.state_handler.update_state(ZoomState.RESIZING, {"action": "リサイズ開始", "角": corner_index})
            self.core.resize_corner_index = corner_index
            self.core.rect_manager.edge_change_editing()
            # 固定する角のインデックスを計算し、座標を保存
            fixed_corner_idx = 3 - corner_index
            self.core.fixed_corner_pos = rotated_corners[fixed_corner_idx]
            self.core.logger.log(LogLevel.DEBUG, f"リサイズ開始パラメータ: 固定角(回転後)={self.core.fixed_corner_pos[0]:.2f}, {self.core.fixed_corner_pos[1]:.2f}")
            self.core.cursor_manager.cursor_update(
                event,
                state=self.core.state_handler.state,
                near_corner_index=self.core.resize_corner_index,
                is_rotating=False
            )
            self.core._resize_logged = False
            self.core.canvas.draw_idle()
        else:
            self.core.logger.log(LogLevel.ERROR, "リサイズ不可：回転後の角座標を取得できず")

    def _handle_press_edit_start_moving(self, event: MouseEvent) -> None:
        """EDIT 状態 + 内部で左クリック: 移動開始
        - 矩形の移動開始点を記録し、移動状態に移行する
        Args:
            event: MouseEvent オブジェクト
        """
        # 現在の矩形状態を保存
        current_state_for_history = self.core.rect_manager.get_state()
        # 矩形のプロパティを取得
        rect_props = self.core.rect_manager.get_properties()
        # 矩形のプロパティとイベント座標が有効な場合に移動処理を開始
        if rect_props and event.xdata is not None and event.ydata is not None:
            self.core.utils._add_history(current_state_for_history)
            self.core.state_handler.update_state(ZoomState.ON_MOVE, {"action": "移動開始"})
            self.core.rect_manager.edge_change_editing()
            # 親のインスタンス変数に開始座標を保存
            self.core.move_start_x, self.core.move_start_y = event.xdata, event.ydata
            # 親のインスタンス変数に矩形開始位置を保存
            self.core.rect_start_pos = (rect_props[0], rect_props[1])
            self.core.logger.log(LogLevel.DEBUG, f"移動開始パラメータ: マウス=({self.core.move_start_x:.2f}, {self.core.move_start_y:.2f}), 矩形左下=({self.core.rect_start_pos[0]:.2f}, {self.core.rect_start_pos[1]:.2f})")
            self.core.cursor_manager.cursor_update(
                event,
                state=self.core.state_handler.state,
                is_rotating=False
            )
            self.core._move_logged = False
            self.core.canvas.draw_idle()
        else:
            self.core.logger.log(LogLevel.ERROR, "移動不可：矩形プロパティまたはイベント座標なし")

    def handle_press_edit_right_confirm(self, event: MouseEvent) -> None:
        """EDIT 状態で右クリック: ズーム確定
        - ズーム選択を確定し、状態をNO_RECTに戻す
        Args:
            event: MouseEvent オブジェクト
        """
        self.core.zoom_selector.confirm_zoom()
        self.core.state_handler.update_state(ZoomState.NO_RECT, {"action": "ズーム確定完了"})
    # --- Press イベントハンドラ ここまで ---

    # --- Motion イベントハンドラ ---
    def handle_motion_create(self, event: MouseEvent) -> None:
        """CREATE 状態でのマウス移動: 矩形サイズ更新
        - 開始点と現在のマウス位置から矩形のサイズを更新し、描画を更新する
        Args:
            event: MouseEvent オブジェクト
        """
        # 開始座標と現在のマウス座標が有効な場合に矩形サイズを更新
        if self.core.start_x is not None and self.core.start_y is not None and \
            event.xdata is not None and event.ydata is not None:

            self.core.rect_manager.setting_rect_size(
                self.core.start_x, self.core.start_y, event.xdata, event.ydata)
            self.core.canvas.draw_idle()

    def handle_motion_edit(self, event: MouseEvent) -> None:
        """EDIT 状態でのマウス移動: カーソル更新
        - マウスの位置に応じてカーソルを更新する
        Args:
            event: MouseEvent オブジェクト
        """
        # マウスカーソルを更新
        corner_index = self.core.zoom_selector.pointer_near_corner(event)
        self.core.cursor_manager.cursor_update(
            event,
            state=self.core.state_handler.state,
            near_corner_index=corner_index,
            is_rotating=self.core._alt_pressed)

    def handle_motion_move(self, event: MouseEvent) -> None:
        """ON_MOVE 状態でのマウス移動: 矩形移動
        - 移動開始点からの相対距離に応じて矩形を移動し、描画を更新する
        Args:
            event: MouseEvent オブジェクト
        """
        # 移動ログを出力
        if not self.core._move_logged:
            self.core._move_logged = True

        # 移動開始座標と矩形の開始位置、現在のマウス座標が有効な場合に矩形を移動
        if self.core.move_start_x is not None and self.core.move_start_y is not None and \
           self.core.rect_start_pos is not None and event.xdata is not None and \
            event.ydata is not None:

            dx = event.xdata - self.core.move_start_x
            dy = event.ydata - self.core.move_start_y
            new_rect_x = self.core.rect_start_pos[0] + dx
            new_rect_y = self.core.rect_start_pos[1] + dy
            self.core.rect_manager.move_rect_to(new_rect_x, new_rect_y)
            self.core.zoom_selector.invalidate_rect_cache()
            self.core.canvas.draw_idle()

    def handle_motion_resizing(self, event: MouseEvent) -> None:
        """RESIZING 状態でのマウス移動: リサイズ
        - 固定点と現在のマウス位置から矩形をリサイズし、描画を更新する
        Args:
            event: MouseEvent オブジェクト
        """
        # リサイズログを出力
        if not self.core._resize_logged:
            self.core._resize_logged = True

        # 固定角座標と現在のマウス座標が有効な場合に矩形をリサイズ
        if self.core.fixed_corner_pos is not None and event.xdata is not None and \
            event.ydata is not None:

            fixed_x_rotated, fixed_y_rotated = self.core.fixed_corner_pos
            current_x, current_y = event.xdata, event.ydata
            self.core.rect_manager.resize_rect_from_corners(
                fixed_x_rotated, fixed_y_rotated, current_x, current_y)
            self.core.zoom_selector.invalidate_rect_cache()
            self.core.canvas.draw_idle()

    def handle_motion_rotating(self, event: MouseEvent) -> None:
        """ROTATING 状態でのマウス移動: 矩形回転
        - 回転中心とマウスの移動から回転角度を計算し、矩形を回転する
        Args:
            event: MouseEvent オブジェクト
        """
        # 回転ログを出力
        if not self.core._rotate_logged:
            self.core._rotate_logged = True

        # 回転中心、前回の角度、現在のマウス座標が有効な場合に回転処理を実行
        if self.core.rotate_center and self.core.previous_vector_angle is not None and \
           event.xdata is not None and event.ydata is not None:

            # 現在の角度を計算
            current_vector_angle = self.core.utils._calculate_angle(
                self.core.rotate_center[0], self.core.rotate_center[1], event.xdata, event.ydata)
            # 角度の変化量を計算
            delta_angle = self.core.utils._normalize_angle_diff(
                current_vector_angle,
                self.core.previous_vector_angle)

            # 角度変化が閾値を超えた場合に矩形を回転
            if abs(delta_angle) > self.core.rotation_threshold:
                adjusted_delta_angle = delta_angle * self.core.rotation_sensitivity
                current_rect_angle = self.core.rect_manager.get_rotation()
                new_angle = current_rect_angle + adjusted_delta_angle
                self.core.rect_manager.set_rotation(new_angle)
                self.core.previous_vector_angle = current_vector_angle
                self.core.logger.log(LogLevel.DEBUG, f"回転 delta:{delta_angle:.2f} adj:{adjusted_delta_angle:.2f} new:{new_angle:.2f}")
                self.core.zoom_selector.invalidate_rect_cache()
                self.core.canvas.draw_idle()
    # --- Motion イベントハンドラ ここまで ---

    # --- Release イベントハンドラ ---
    def handle_release_create(self, event: MouseEvent, is_outside: bool) -> ZoomState:
        """CREATE 状態でのマウス解放: 作成完了またはキャンセル
        - 軸外でのリリース、または左クリックのリリースで処理を分岐
        - 状態を更新する
        Args:
            event: MouseEvent オブジェクト
            is_outside: リリースが軸外で行われたか
        Returns:
            ZoomState: 次の状態 (NO_RECT または EDIT)
        """
        final_state = ZoomState.NO_RECT # デフォルトはキャンセル
        # 軸外でリリースされた場合はキャンセル
        if is_outside:
            self.core.logger.log(LogLevel.WARNING, "作成キャンセル: 軸外でリリース")
            self.core.rect_manager.delete_rect()
            self.core.utils._remove_last_history()
        # 左クリックがリリースされた場合、矩形が有効なサイズであれば作成完了
        elif event.button == MouseButton.LEFT:
            # 親のインスタンス変数から開始座標を取得
            if self.core.start_x is not None and self.core.start_y is not None and \
               event.xdata is not None and event.ydata is not None:
                if self.core.rect_manager._temporary_creation(
                    self.core.start_x, self.core.start_y, event.xdata, event.ydata):

                    self.core.logger.log(LogLevel.SUCCESS, "作成成功")
                    final_state = ZoomState.EDIT
                else:
                    self.core.logger.log(LogLevel.WARNING, "作成失敗: 最終サイズが無効")
                    self.core.rect_manager.delete_rect()
                    self.core.utils._remove_last_history()
            else:
                self.core.logger.log(LogLevel.ERROR, "作成失敗: 座標情報不備")

        self.core.utils._reset_create_state() # 作成関連の内部状態をリセット
        return final_state

    def handle_release_move(self, event: MouseEvent) -> ZoomState:
        """ON_MOVE 状態でのマウス解放: 移動完了
        - 矩形の移動を確定し、状態を更新する
        Args:
            event: MouseEvent オブジェクト
        Returns:
            ZoomState: 次の状態 (EDIT)
        """
        self.core.logger.log(LogLevel.SUCCESS, "移動完了：後処理開始")
        self.core.rect_manager.edge_change_finishing()
        self.core.utils._reset_move_state()
        return ZoomState.EDIT

    def handle_release_resizing(self, event: MouseEvent) -> ZoomState:
        """RESIZING 状態でのマウス解放: リサイズ完了またはキャンセル/Undo
        - 矩形のリサイズを確定、または無効なリサイズの場合Undoを実行し、状態を更新する
        Args:
            event: MouseEvent オブジェクト
        Returns:
            ZoomState: 次の状態 (EDIT または NO_RECT)
        """
        self.core.logger.log(LogLevel.SUCCESS, "リサイズ完了：後処理開始")
        self.core.rect_manager.edge_change_finishing()
        final_state = ZoomState.EDIT
        # rect_props = self.core.rect_manager.get_properties() # 不要になる
        # 最後に計算されたピクセルサイズが有効かチェック
        if not self.core.rect_manager.is_last_calculated_size_valid():
            self.core.logger.log(LogLevel.WARNING, "リサイズ中断: 無効なサイズになったためUndo試行")
            self.core.utils._undo_last_edit()
            if not self.core.rect_manager.get_rect(): # Undoの結果、矩形が消えた場合
                final_state = ZoomState.NO_RECT

        self.core.utils._reset_resize_state()
        return final_state

    def handle_release_rotating(self, event: MouseEvent) -> ZoomState:
        """ROTATING 状態でのマウス解放: 回転完了
        - 矩形の回転を確定し、状態を更新する
        Args:
            event: MouseEvent オブジェクト
        Returns:
            ZoomState: 次の状態 (EDIT)
        """
        self.core.logger.log(LogLevel.SUCCESS, "回転完了：後処理開始")
        self.core.utils._reset_rotate_state()
        return ZoomState.EDIT
    # --- Release イベントハンドラ ここまで ---

    # --- Key イベントハンドラ ---
    def _handle_key_escape(self, event: KeyEvent) -> None:
        """Escapeキー押下処理
        - 現在の状態に応じて、ズーム確定キャンセル、Undo、編集キャンセルなどの処理を行う
        Args:
            event: KeyEvent オブジェクト
        """
        # 親の state_handler から現在の状態を取得
        state = self.core.state_handler.state
        if state is ZoomState.NO_RECT:
            self.core.logger.log(LogLevel.CALL, "ESC: NO_RECT -> ズーム確定キャンセル呼出し")
            self.core.zoom_selector.cancel_zoom() # MainWindow側の処理を呼び出す
        elif state is ZoomState.EDIT:
            self.core.logger.log(LogLevel.CALL, "ESC: EDIT -> Undo/編集キャンセル呼出し")
            self.core.utils._undo_or_cancel_edit() # Undoまたは編集キャンセル
        elif state in [ZoomState.CREATE, ZoomState.ON_MOVE, ZoomState.RESIZING, ZoomState.ROTATING]:
             self.core.logger.log(LogLevel.CALL, f"ESC: {state.name} -> 操作キャンセル呼出し")
             # ドラッグ操作中にESCが押された場合もキャンセル
             self.core.utils._undo_or_cancel_edit()

    def handle_key_alt_press(self, event: KeyEvent) -> None:
        """Altキー押下処理
        - Altキーの状態を管理する
        - EDIT状態の場合、ログ出力を行う
        Args:
            event: KeyEvent オブジェクト
        """
        # 親の _alt_pressed 状態を確認・更新
        if not self.core._alt_pressed: # Altキーが押されていなかったら
            self.core._alt_pressed = True
            if self.core.state_handler.state == ZoomState.EDIT:
                self.core.logger.log(LogLevel.DEBUG, "Alt押下: EDIT状態")

    def handle_key_alt_release(self, event: KeyEvent) -> None:
        """Altキー解放処理
        - Altキーの状態を管理する
        - EDIT状態の場合、ログ出力を行う
        Args:
            event: KeyEvent オブジェクト
        """
        # 親の _alt_pressed 状態を確認・更新
        if self.core._alt_pressed: # Altキーが押されていたら
            self.core._alt_pressed = False
            if self.core.state_handler.state == ZoomState.EDIT:
                self.core.logger.log(LogLevel.DEBUG, "Alt解放: EDIT状態")
    # --- Key イベントハンドラ ここまで ---
