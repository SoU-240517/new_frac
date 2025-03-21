# ui/zoom_selector.py
import matplotlib.patches as patches
import matplotlib.transforms as transforms
import numpy as np

class ZoomSelector:
    def __init__(self, ax, on_zoom_confirm, on_zoom_cancel):
        """
        ax: 対象の matplotlib Axes
        on_zoom_confirm: ズーム確定時に呼ばれるコールバック（zoom_paramsを引数に取る）
        on_zoom_cancel: ズームキャンセル時に呼ばれるコールバック
        """
        self.ax = ax  # ズーム選択を行うAxes
        self.canvas = ax.figure.canvas  # ズーム選択を行うFigureのCanvas
        self.on_zoom_confirm = on_zoom_confirm  # ズーム確定時のコールバック
        self.on_zoom_cancel = on_zoom_cancel  # ズームキャンセル時のコールバック
        self.mode = None            # 現在の操作モード（'create', 'move', 'resize', 'rotate'）
        self.saved_rect = None      # キャンセル時に復元するための直前の矩形情報

        self.rect = None            # ズーム矩形のパッチ
        self.zoom_active = False    # ズーム選択中フラグ
        self.press = None           # ドラッグ開始時の情報（移動 or 回転判定用）
        self.start_x = None         # 矩形作成開始点（x）
        self.start_y = None         # 矩形作成開始点（y）
        self.angle = 0.0            # 回転角（ラジアン）

        self.rotation_bar = None    # 回転バー（線）
        self.rotation_handle = None # 回転バー先端のハンドル（円）

        # イベントハンドラ接続
        self.cid_press = self.canvas.mpl_connect('button_press_event', self.on_press)
        self.cid_release = self.canvas.mpl_connect('button_release_event', self.on_release)
        self.cid_motion = self.canvas.mpl_connect('motion_notify_event', self.on_motion)

    def on_press(self, event):
        if event.inaxes != self.ax:
            return

        # 回転バーのクリック判定を修正
        if self.rotation_handle is not None:
            dx = event.xdata - self.rotation_handle.center[0]
            dy = event.ydata - self.rotation_handle.center[1]
            if np.hypot(dx, dy) < self.rotation_handle.radius:
                # 回転モード開始
                self.press = ('rotate', self.rotation_handle.center, event.xdata, event.ydata, self.angle)
                return

        # 中クリックでキャンセル
        if event.button == 2:
            self.cancel_zoom()
            return

        # 右クリックでズーム確定（矩形内なら）
        if event.button == 3:
            if self.rect is not None:
                contains, _ = self.rect.contains(event)
                if contains:
                    self.confirm_zoom()
                    return

        # 左クリックの場合
        if event.button == 1:
            if self.rect is not None:
                # 既存矩形の現在の位置・サイズを保存（キャンセル用）
                x, y = self.rect.get_xy()
                width = self.rect.get_width()
                height = self.rect.get_height()
                self.saved_rect = (x, y, width, height)

                # 角部付近かどうか判定（サイズ変更モード）
                corners = {
                    'bottom_left': (x, y),
                    'bottom_right': (x+width, y),
                    'top_left': (x, y+height),
                    'top_right': (x+width, y+height)
                }
                tol = 0.05 * min(width, height) if min(width, height) != 0 else 0.1
                for corner_name, (cx, cy) in corners.items():
                    if np.hypot(event.xdata - cx, event.ydata - cy) < tol:
                        # 固定する角は対角の角
                        if corner_name == 'bottom_left':
                            fixed = (x+width, y+height)
                        elif corner_name == 'bottom_right':
                            fixed = (x, y+height)
                        elif corner_name == 'top_left':
                            fixed = (x+width, y)
                        elif corner_name == 'top_right':
                            fixed = (x, y)
                        self.mode = 'resize'
                        self.press = (corner_name, fixed, x, y, width, height, event.xdata, event.ydata)
                        self.canvas.draw()
                        return

                # 矩形内なら移動モード
                contains, _ = self.rect.contains(event)
                if contains:
                    self.mode = 'move'
                    self.press = (self.rect.get_xy(), event.xdata, event.ydata)
                    self.canvas.draw()
                    return
                # それ以外は新規作成とする
                self.start_x, self.start_y = event.xdata, event.ydata
                self.rect.set_xy((self.start_x, self.start_y))
                self.rect.set_width(0)
                self.rect.set_height(0)
                self.mode = 'create'
            else:
                # 新規矩形作成開始
                self.start_x, self.start_y = event.xdata, event.ydata
                self.rect = patches.Rectangle((self.start_x, self.start_y), 0, 0,
                                            edgecolor='white', facecolor='none', linestyle='-')
                self.ax.add_patch(self.rect)
                self.zoom_active = True
                self.mode = 'create'
            self.canvas.draw()

    def on_motion(self, event):
        if not self.zoom_active or event.inaxes != self.ax:
            return

        # カーソル変更処理
        self.update_cursor(event)

        """
        # 回転モードの処理を修正
        if self.press is not None and isinstance(self.press, tuple) and self.press[0] == 'rotate':
            _, center, press_x, press_y, start_angle = self.press
            dx = event.xdata - center[0]
            dy = event.ydata - center[1]
            press_dx = press_x - center[0]
            press_dy = press_y - center[1]

            # 初回クリック時の角度と現在の角度の差分を求める
            initial_angle = np.arctan2(press_dy, press_dx)
            current_angle = np.arctan2(dy, dx)
            delta_angle = current_angle - initial_angle

            # 角度を更新
            self.angle = start_angle + delta_angle

            # 矩形の回転を適用
            self.apply_rotation()

            self.update_rotation_bar()
            self.canvas.draw()
            return
        """

        if self.mode == 'resize' and self.press is not None:
            # press: (corner_name, fixed, orig_x, orig_y, orig_width, orig_height, press_x, press_y)
            _, fixed, orig_x, orig_y, orig_width, orig_height, press_x, press_y = self.press
            new_x = min(fixed[0], event.xdata)
            new_y = min(fixed[1], event.ydata)
            new_width = abs(fixed[0] - event.xdata)
            new_height = abs(fixed[1] - event.ydata)
            self.rect.set_xy((new_x, new_y))
            self.rect.set_width(new_width)
            self.rect.set_height(new_height)
        elif self.mode == 'move' and self.press is not None:
            orig_xy, press_x, press_y = self.press
            dx = event.xdata - press_x
            dy = event.ydata - press_y
            new_xy = (orig_xy[0] + dx, orig_xy[1] + dy)
            self.rect.set_xy(new_xy)
        elif self.mode == 'create':
            dx = event.xdata - self.start_x
            dy = event.ydata - self.start_y
            new_x = min(self.start_x, event.xdata)
            new_y = min(self.start_y, event.ydata)
            new_width = abs(dx)
            new_height = abs(dy)

            self.rect.set_xy((new_x, new_y))
            self.rect.set_width(new_width)
            self.rect.set_height(new_height)
        #self.update_rotation_bar()  # 回転バーを更新
        self.canvas.draw()

    def on_release(self, event):
        if self.mode in ['resize', 'move', 'create'] and event.inaxes == self.ax:
            if self.mode == 'create':
                x0, y0 = self.start_x, self.start_y
                dx = event.xdata - x0
                dy = event.ydata - y0
                if dx != 0 and dy != 0:
                    new_x = min(x0, event.xdata)
                    new_y = min(y0, event.ydata)
                    new_width = abs(dx)
                    new_height = abs(dy)
                    self.rect.set_xy((new_x, new_y))
                    self.rect.set_width(new_width)
                    self.rect.set_height(new_height)
                    #self.update_rotation_bar()  # 回転バーを更新
            self.press = None
            self.mode = None
        self.canvas.draw()

    """
    def update_rotation_bar(self):
        矩形の上辺中央に回転バーとハンドルを描画・更新する
        if self.rect is None:
            return
        x, y = self.rect.get_xy()
        width = self.rect.get_width()
        height = self.rect.get_height()
        # 上辺中央の位置
        top_center = (x + width/2.0, y + height)
        # 回転バーの長さ（矩形サイズに依存、調整可能）
        bar_length = max(abs(width), abs(height)) * 0.1
        end_point = (top_center[0], top_center[1] + bar_length)
        if self.rotation_bar is None:
            self.rotation_bar, = self.ax.plot([top_center[0], end_point[0]],
                                              [top_center[1], end_point[1]], color='white')
        else:
            self.rotation_bar.set_data([top_center[0], end_point[0]],
                                       [top_center[1], end_point[1]])
        if self.rotation_handle is None:
            self.rotation_handle = self.ax.add_patch(patches.Circle(end_point, radius=bar_length*6.0, color='white'))
        else:
            self.rotation_handle.center = end_point
        self.canvas.draw()
    """

    """
    def apply_rotation(self):
        矩形の回転を適用する（正しく回転のみ行う）
        if self.rect is None:
            return

        x, y = self.rect.get_xy()
        width = self.rect.get_width()
        height = self.rect.get_height()
        center_x = x + width / 2
        center_y = y + height / 2

        # 回転変換を適用（中心を軸に回転）
        t = transforms.Affine2D().rotate_around(center_x, center_y, self.angle) + self.ax.transData
        self.rect.set_transform(t)

        # 回転バーの位置を更新
        self.update_rotation_bar()

        self.canvas.draw()
    """

    """
    def update_rotation_bar(self):
        矩形の回転に合わせて回転バーの位置も更新
        if self.rect is None:
            return

        x, y = self.rect.get_xy()
        width = self.rect.get_width()
        height = self.rect.get_height()
        center_x = x + width / 2.0
        center_y = y + height / 2.0

        # 矩形の上辺中央の位置を計算（回転後）
        top_center = (center_x, center_y + height / 2.0)

        # 回転行列を適用
        cos_theta = np.cos(self.angle)
        sin_theta = np.sin(self.angle)
        rotated_top_center = (
            center_x + (top_center[0] - center_x) * cos_theta - (top_center[1] - center_y) * sin_theta,
            center_y + (top_center[0] - center_x) * sin_theta + (top_center[1] - center_y) * cos_theta
        )

        # 回転バーの長さを調整
        bar_length = max(abs(width), abs(height)) * 0.1
        end_point = (rotated_top_center[0], rotated_top_center[1] + bar_length)

        # 回転バーを更新
        if self.rotation_bar is None:
            self.rotation_bar, = self.ax.plot([rotated_top_center[0], end_point[0]],
                                            [rotated_top_center[1], end_point[1]], color='white')
        else:
            self.rotation_bar.set_data([rotated_top_center[0], end_point[0]],
                                    [rotated_top_center[1], end_point[1]])

        # 回転ハンドル（円）を更新
        if self.rotation_handle is None:
            self.rotation_handle = self.ax.add_patch(patches.Circle(end_point, radius=bar_length * 6.0, color='white'))
        else:
            self.rotation_handle.center = end_point

        self.canvas.draw()
    """

    def update_cursor(self, event):
        """マウス位置に応じてカーソルを変更する"""
        if self.rect is None:
            return

        x, y = self.rect.get_xy()
        width = self.rect.get_width()
        height = self.rect.get_height()

        # 角の判定用（サイズ変更）
        corners = {
            'bottom_left': (x, y),
            'bottom_right': (x + width, y),
            'top_left': (x, y + height),
            'top_right': (x + width, y + height)
        }
        tol = 0.05 * min(width, height) if min(width, height) != 0 else 0.1

        for corner, (cx, cy) in corners.items():
            if np.hypot(event.xdata - cx, event.ydata - cy) < tol:
                self.canvas.get_tk_widget().config(cursor="crosshair")  # サイズ変更カーソル
                return

        # 矩形の内側（移動）
        contains, _ = self.rect.contains(event)
        if contains:
            self.canvas.get_tk_widget().config(cursor="fleur")  # 移動カーソル
            return

        """
        # 回転バーのチェック（修正）
        if self.rotation_handle is not None:
            dx = event.xdata - self.rotation_handle.center[0]
            dy = event.ydata - self.rotation_handle.center[1]
            if np.hypot(dx, dy) < self.rotation_handle.radius:
                self.canvas.get_tk_widget().config(cursor="exchange")  # 回転用のカーソル
                return
        """

        # デフォルトカーソル
        self.canvas.get_tk_widget().config(cursor="arrow")

    def confirm_zoom(self):
        """右クリックによるズーム確定時、矩形情報からズームパラメータを計算してコールバック呼出"""
        if self.rect is None:
            return
        x, y = self.rect.get_xy()
        width = self.rect.get_width()
        height = self.rect.get_height()
        # 矩形の中心を計算
        center_x = x + width / 2.0
        center_y = y + height / 2.0
        zoom_params = {"center_x": center_x, "center_y": center_y,
                       "width": abs(width), "height": abs(height),
                       "rotation": self.angle}
        self.clear_rectangle()
        if self.on_zoom_confirm:
            self.on_zoom_confirm(zoom_params)

    def cancel_zoom(self):
        if self.zoom_active and self.saved_rect is not None and self.rect is not None:
            # 未確定状態の場合、直前の矩形情報を復元
            x, y, width, height = self.saved_rect
            self.rect.set_xy((x, y))
            self.rect.set_width(width)
            self.rect.set_height(height)
            self.saved_rect = None
            self.canvas.draw()
        else:
            self.clear_rectangle()
            if self.on_zoom_cancel:
                self.on_zoom_cancel()

    def clear_rectangle(self):
        """矩形および回転バー・ハンドルを消去"""
        if self.rect is not None:
            self.rect.remove()
            self.rect = None
        if self.rotation_bar is not None:
            self.rotation_bar.remove()
            self.rotation_bar = None
        if self.rotation_handle is not None:
            self.rotation_handle.remove()
            self.rotation_handle = None
        self.zoom_active = False
        self.canvas.draw()
