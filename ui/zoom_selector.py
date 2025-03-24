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

        # イベントハンドラ接続
        self.cid_press = self.canvas.mpl_connect('button_press_event', self.on_press)  # マウスボタンが押されたときのイベント
        self.cid_release = self.canvas.mpl_connect('button_release_event', self.on_release)  # マウスボタンが離されたときのイベント
        self.cid_motion = self.canvas.mpl_connect('motion_notify_event', self.on_motion)  # マウスが移動したときのイベント

    def on_press(self, event):
        """ マウスボタンが押されたときのイベントハンドラ """
        if event.inaxes != self.ax:  # 選択されたAxesが異なる場合は無視
            return

        # 中クリックでキャンセル
        if event.button == 2:  # 中クリック（ボタン2）
            self.cancel_zoom()  # ズームキャンセル
            return

        # 右クリックでズーム確定（矩形内なら）
        if event.button == 3:
            if self.rect is not None:
                contains, _ = self.rect.contains(event)
                if contains:
                    self.confirm_zoom()
                    return

        # 左クリックの場合
        if event.button == 1:  # 左クリック
            if self.rect is not None:  # 矩形が存在する場合
                # 既存矩形の現在の位置・サイズを保存（キャンセル用）
                x, y = self.rect.get_xy()  # 矩形の左上座標
                width = self.rect.get_width()  # 矩形の幅
                height = self.rect.get_height()  # 矩形の高さ
                self.saved_rect = (x, y, width, height)  # 保存

                # 角部付近かどうか判定（サイズ変更モード）
                corners = {
                    'bottom_left': (x, y),
                    'bottom_right': (x+width, y),
                    'top_left': (x, y+height),
                    'top_right': (x+width, y+height)
                }
                tol = 0.05 * min(width, height) if min(width, height) != 0 else 0.1  # 許容誤差
                for corner_name, (cx, cy) in corners.items():  # 各角の座標
                    if np.hypot(event.xdata - cx, event.ydata - cy) < tol:  # 距離が許容誤差内なら
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
                        self.press = (corner_name, fixed, x, y, width, height, event.xdata, event.ydata)  # サイズ変更モードの情報を保存
                        self.canvas.draw()
                        return

                # 矩形内なら移動モード
                contains, _ = self.rect.contains(event)
                if contains:
                    self.mode = 'move'
                    self.press = (self.rect.get_xy(), event.xdata, event.ydata)  # 移動開始点と現在の座標を保存
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
                            edgecolor='white',
                            facecolor='none',
#                            facecolor='red',  # 赤色で表示（動作確認用）
#                            alpha=0.3,  # 透明度（動作確認用）
                            linestyle='solid'
                        )
                self.ax.add_patch(self.rect)
                self.zoom_active = True
                self.mode = 'create'
            self.canvas.draw()

    def on_motion(self, event):
        """ マウスが移動したときのイベントハンドラ """
        if not self.zoom_active or event.inaxes != self.ax:  # ズーム選択中でない、または選択されたAxesが異なる場合は無視
            return

        # カーソル変更処理
        self.update_cursor(event)

        if self.mode == 'resize' and self.press is not None:  # サイズ変更モード
            corner_name, fixed, orig_x, orig_y, orig_width, orig_height, press_x, press_y = self.press  # ドラッグ開始時の情報
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
#            self.rect.set_facecolor('blue')  # 再設定（動作確認用）
#            self.rect.set_alpha(0.3)  # 透明度を設定（動作確認用）
        self.canvas.draw()

    def on_release(self, event):
        """ マウスを離したときのイベントハンドラ """
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
            self.press = None
            self.mode = None
        self.canvas.draw()

    def update_cursor(self, event):
        """マウス位置に応じてカーソルを変更する"""
        print("update_cursor：開始")  # ← debug print★
        if self.rect is None:  # 矩形がない場合は通常のカーソル
            print("矩形無し：(cursor arrow)")  # ← debug print★
            self.canvas.get_tk_widget().config(cursor="arrow")  # 通常のカーソル
            return
        print("矩形有り")  # ← debug print★
        # 矩形がある場合は、矩形の座標とサイズを取得
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
        tol = 0.05 * min(width, height) if min(width, height) != 0 else 0.1  # 許容誤差
        # カーソルの更新
        for corner, (cx, cy) in corners.items():  # サイズ変更カーソル判定
            if np.hypot(event.xdata - cx, event.ydata - cy) < tol:  # サイズ変更カーソル判定
                self.canvas.get_tk_widget().config(cursor="crosshair")  # サイズ変更カーソル
                return
        # 矩形の内側（移動）
        contains, _ = self.rect.contains(event)  # 矩形の内側かどうか判定
        if contains:  # 矩形の内側の場合
            self.canvas.get_tk_widget().config(cursor="fleur")  # 移動カーソル
            return

        # デフォルトカーソル
        self.canvas.get_tk_widget().config(cursor="arrow")  # デフォルトカーソル

    def confirm_zoom(self):
        """右クリックによるズーム確定時、矩形情報からズームパラメータを計算してコールバック呼出"""
        if self.rect is None:  # 矩形がない場合は無視
            return
        # 矩形がある場合は、矩形の情報を取得
        x, y = self.rect.get_xy()
        width = self.rect.get_width()
        height = self.rect.get_height()
        # 矩形の中心を計算
        center_x = x + width / 2.0
        center_y = y + height / 2.0
        zoom_params = {"center_x": center_x, "center_y": center_y,
                       "width": abs(width), "height": abs(height),
                       "rotation": self.angle}
        self.clear_rectangle()  # 矩形を削除
        if self.on_zoom_confirm:  # コールバックが存在する場合のみ呼び出す
            self.on_zoom_confirm(zoom_params)

    def cancel_zoom(self):
        """中クリックによるズームキャンセル時、矩形情報をもとに戻す"""
        print("cancel_zoom：開始")  # ← debug print★
        if self.zoom_active and self.saved_rect is not None and self.rect is not None:  # 矩形が存在する場合のみ削除
            print("cancel_zoom: 矩形有り")  # ← debug print★
            x, y, width, height = self.saved_rect  # 保存した矩形の情報を取得
            self.rect.set_xy((x, y))  # 矩形の位置を設定
            self.rect.set_width(width)  # 矩形の幅を設定
            self.rect.set_height(height)  # 矩形の高さを設定
            self.saved_rect = None  # 保存した矩形の情報をクリア
            self.canvas.draw()
        else:  # 矩形が存在しない場合、コールバックを呼び出す
            print("cancel_zoom: 矩形無し")  # ← debug print★
            if self.on_zoom_cancel:  # コールバックが存在する場合のみ呼び出す
                print("コールバックがある")  # ← debug print★
                self.clear_rectangle()  # 矩形を削除
                self.zoom_active = False  # ズームモードを終了
                self.canvas.get_tk_widget().config(cursor="arrow")  # カーソルをデフォルトに戻す
                self.on_zoom_cancel()  # コールバックを呼び出す

    def clear_rectangle(self):
        """ 矩形を消去 """
        print("矩形消去：実行")  # ← debug print★
        if self.rect is not None:  # 矩形が存在する場合のみ削除
            print(f"矩形がある場合：{self.rect}")  # ← debug print★ (削除前の情報を出力)
            self.rect.remove()  # 矩形を削除
            self.rect = None  # 矩形をNoneに設定
        self.zoom_active = False  # ズームモードを終了
        self.canvas.get_tk_widget().config(cursor="arrow")  # カーソルをデフォルトに戻す
        self.canvas.draw()  # 描画を更新
        self.canvas.draw()  # 描画を更新
        print(f"矩形が無い場合：{self.rect}")  # ← debug print★ (削除後に None になっているか確認)
