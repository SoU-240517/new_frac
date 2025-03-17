# ui/zoom_selector.py
import matplotlib.patches as patches
import numpy as np

class ZoomSelector:
    def __init__(self, ax, on_zoom_confirm, on_zoom_cancel):
        """
        ax: 対象の matplotlib Axes
        on_zoom_confirm: ズーム確定時に呼ばれるコールバック（zoom_paramsを引数に取る）
        on_zoom_cancel: ズームキャンセル時に呼ばれるコールバック
        """
        self.ax = ax
        self.canvas = ax.figure.canvas
        self.on_zoom_confirm = on_zoom_confirm
        self.on_zoom_cancel = on_zoom_cancel

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

        # まず回転ハンドル上かチェック
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
            if self.rect is None:
                # 新規矩形作成開始
                self.start_x, self.start_y = event.xdata, event.ydata
                self.rect = patches.Rectangle((self.start_x, self.start_y), 0, 0,
                                              edgecolor='white', facecolor='none', linestyle='-')
                self.ax.add_patch(self.rect)
                self.zoom_active = True
            else:
                # 既存矩形内なら移動開始（簡易実装）
                contains, _ = self.rect.contains(event)
                if contains:
                    self.press = (self.rect.get_xy(), event.xdata, event.ydata)
                else:
                    # 矩形外なら新規作成とする
                    self.start_x, self.start_y = event.xdata, event.ydata
                    self.rect.set_xy((self.start_x, self.start_y))
                    self.rect.set_width(0)
                    self.rect.set_height(0)
            self.canvas.draw()

    def on_motion(self, event):
        if not self.zoom_active or event.inaxes != self.ax:
            return

        # 回転モードの場合
        if self.press is not None and isinstance(self.press, tuple) and self.press[0] == 'rotate':
            _, center, _, _, start_angle = self.press
            dx = event.xdata - center[0]
            dy = event.ydata - center[1]
            new_angle = np.arctan2(dy, dx)
            self.angle = new_angle
            self.update_rotation_bar()
            self.canvas.draw()
            return

        if self.press is None:
            # 新規矩形作成中：幅・高さを更新
            x0, y0 = self.start_x, self.start_y
            dx = event.xdata - x0
            dy = event.ydata - y0
            self.rect.set_width(dx)
            self.rect.set_height(dy)
            self.update_rotation_bar()
        else:
            # 移動モード：矩形全体をドラッグ
            (orig_xy, xpress, ypress) = self.press
            dx = event.xdata - xpress
            dy = event.ydata - ypress
            new_xy = (orig_xy[0] + dx, orig_xy[1] + dy)
            self.rect.set_xy(new_xy)
            self.update_rotation_bar()
        self.canvas.draw()

    def on_release(self, event):
        self.press = None
        self.canvas.draw()

    def update_rotation_bar(self):
        """矩形の上辺中央に回転バーとハンドルを描画・更新する"""
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
            self.rotation_handle = self.ax.add_patch(patches.Circle(end_point, radius=bar_length*0.3, color='white'))
        else:
            self.rotation_handle.center = end_point
        self.canvas.draw()

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
        """中クリックによるキャンセル時の処理"""
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
