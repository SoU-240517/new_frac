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
        print("====== ZoomSelector の初期化開始:（def __init__）")  # ← debug print★
        # 前回の状態を保存する変数★
        self.last_cursor_state = None  # カーソル
        self.last_motion_state = None  # 移動
        # 現在の操作モード（'create', 'move', 'resize'）
        self.mode = None
        # ズーム選択のパラメータ
        self.ax = ax  # Axes
        self.canvas = ax.figure.canvas  # FigureのCanvas
        self.on_zoom_confirm = on_zoom_confirm  # 確定時のコールバック
        self.on_zoom_cancel = on_zoom_cancel  # キャンセル時のコールバック
        self.zoom_active = False  # 選択中フラグ
        # ドラッグ開始時の情報（移動判定定用）
        self.press = None
        # 矩形情報
        self.start_x = None  # 開始点（x）
        self.start_y = None  # 開始点（y）
        self.rect = None  # パッチ
        self.saved_rect = None  # 直前の情報
        # イベントハンドラ接続
        self.cid_press = self.canvas.mpl_connect('button_press_event', self.on_press)  # マウスボタンが押された
        self.cid_release = self.canvas.mpl_connect('button_release_event', self.on_release)  # マウスボタンが離された
        self.cid_motion = self.canvas.mpl_connect('motion_notify_event', self.on_motion)  # マウスが移動した

    def on_press(self, event):
        """ マウスボタンが押されたときのイベントハンドラ """
        print("====== マウスボタンが押された:（def on_press）")  # ← debug print★

        # 選択されたAxesが異なる場合は無視
        if event.inaxes != self.ax:
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
            if self.rect is not None:  # 矩形が存在する場合
                # 矩形の現在の位置・サイズを保存（キャンセル用）
                x, y = self.rect.get_xy()  # 左上座標
                width = self.rect.get_width()  # の幅
                height = self.rect.get_height()  # 高さ
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
            else:
                # 新規矩形作成開始
                self.start_x, self.start_y = event.xdata, event.ydata
                self.rect = patches.Rectangle((self.start_x, self.start_y), 0, 0,
                            edgecolor='white',
                            facecolor='none',
#                            facecolor='red',  # 赤色で表示★動作確認用
#                            alpha=0.3,  # 透明度★動作確認用
                            linestyle='solid'
                        )
                self.ax.add_patch(self.rect)
                self.zoom_active = True
                self.mode = 'create'
            self.canvas.draw()

    def on_motion(self, event):
        """ マウスが移動したときのイベントハンドラ """

        # ズーム選択中でない、または選択されたAxesが異なる場合は無視
        if not self.zoom_active or event.inaxes != self.ax:
            return

        # カーソル変更処理
        self.update_cursor(event)

        # モードに応じた処理 debug print用★
        current_motion_state = None
        if self.mode == 'resize' and self.press is not None:
            current_motion_state = 'resize'
        elif self.mode == 'move' and self.press is not None:
            current_motion_state = 'move'
        elif self.mode == 'create':
            current_motion_state = 'create'

        # 状態が変化した場合のみプリント  debug print用★
        if current_motion_state != self.last_motion_state:
            print("====== マウスが移動した:（def on_motion）")
            if current_motion_state == 'resize':
                print("=== サイズ変更モード")
            elif current_motion_state == 'move':
                print("=== 移動モード")
            elif current_motion_state == 'create':
                print("=== 新規作成モード")
            self.last_motion_state = current_motion_state

        # サイズ変更モード
        if self.mode == 'resize' and self.press is not None:
            # ドラッグ中に矩形のサイズを更新
            corner_name, fixed, orig_x, orig_y, orig_width, orig_height, press_x, press_y = self.press  # ドラッグ開始時の情報
            new_x = min(fixed[0], event.xdata)
            new_y = min(fixed[1], event.ydata)
            new_width = abs(fixed[0] - event.xdata)
            new_height = abs(fixed[1] - event.ydata)
            self.rect.set_xy((new_x, new_y))
            self.rect.set_width(new_width)
            self.rect.set_height(new_height)
        # 移動モード
        elif self.mode == 'move' and self.press is not None:
            # ドラッグ中に矩形の位置を更新
            orig_xy, press_x, press_y = self.press
            dx = event.xdata - press_x
            dy = event.ydata - press_y
            new_xy = (orig_xy[0] + dx, orig_xy[1] + dy)
            self.rect.set_xy(new_xy)
        # 新規作成モード
        elif self.mode == 'create':
            # ドラッグ中に矩形の位置とサイズを更新
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
        print("====== マウスを離した:（def on_release）")  # ← debug print★
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
        # カーソル状態を保存
        current_cursor_state = None

        # 矩形がない場合は通常のカーソル
        if self.rect is None:
            current_cursor_state = "arrow"
            # カーソル状態が変化した場合のみプリント  debug print用★
            if self.last_cursor_state != current_cursor_state:
                print("====== カーソルを更新:（def update_cursor）")
                print("=== 通常のカーソル")
                self.canvas.get_tk_widget().config(cursor="arrow")
                self.last_cursor_state = current_cursor_state
                return
            return
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
        # 許容誤差
        tol = 0.05 * min(width, height) if min(width, height) != 0 else 0.1
        # 各角の判定
        for corner, (cx, cy) in corners.items():
            # サイズ変更範囲内であればカーソルを変更
            if np.hypot(event.xdata - cx, event.ydata - cy) < tol:
                current_cursor_state = "crosshair"
                # カーソル状態が変化した場合のみプリント  debug print用★
                if self.last_cursor_state != current_cursor_state:
                    print("====== カーソルを更新:（def update_cursor）")
                    print("=== カーソル変更：crosshair")
                    self.canvas.get_tk_widget().config(cursor="crosshair")
                    self.last_cursor_state = current_cursor_state
                    return
                return
        # 矩形の内側かどうか判定
        contains, _ = self.rect.contains(event)
        # 矩形の内側にあればカーソルを変更
        if contains:
            current_cursor_state = "fleur"
            # カーソル状態が変化した場合のみプリント  debug print用★
            if self.last_cursor_state != current_cursor_state:
                print("====== カーソルを更新:（def update_cursor）")
                print("=== カーソル変更：fleur")
                self.canvas.get_tk_widget().config(cursor="fleur")
                self.last_cursor_state = current_cursor_state
                return
            return
        # カーソル状態が変化した場合のみプリント  debug print用★
        if self.last_cursor_state != "arrow":
            print("====== カーソルを更新:（def update_cursor）")
            print("=== カーソルデフォルト：arrow")
            self.canvas.get_tk_widget().config(cursor="arrow")
            self.last_cursor_state = "arrow"
            return

    def confirm_zoom(self):
        """右クリックによるズーム確定時、矩形情報からズームパラメータを計算してコールバック呼出"""
        print("====== ズーム確定:（def confirm_zoom）")  # ← debug print★
        # 矩形がない場合は無視
        if self.rect is None:
            return
        # 矩形の情報を取得
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
        print("====== ズームキャンセル:（def cancel_zoom）")  # ← debug print★
        # 矩形が存在する場合のみ削除
        if self.zoom_active and self.saved_rect is not None and self.rect is not None:
            print("=== 矩形有り")  # ← debug print★
            x, y, width, height = self.saved_rect  # 保存した矩形の情報を取得
            self.rect.set_xy((x, y))  # 矩形の位置を設定
            self.rect.set_width(width)  # 矩形の幅を設定
            self.rect.set_height(height)  # 矩形の高さを設定
            self.saved_rect = None  # 保存した矩形の情報をクリア
            self.canvas.draw()
        # 矩形が存在しない場合、コールバックを呼び出す
        else:
            print("=== 矩形無し")  # ← debug print★
            # コールバックが存在する場合のみ呼び出す
            if self.on_zoom_cancel:
                print("コールバックがある")  # ← debug print★
                self.clear_rectangle()  # 矩形を削除
                self.zoom_active = False  # ズームモードを終了
                self.canvas.get_tk_widget().config(cursor="arrow")  # カーソルをデフォルトに戻す
                self.on_zoom_cancel()  # コールバックを呼び出す

    def clear_rectangle(self):
        """ 矩形を消去 """
        print("====== 矩形を消去:（def clear_rectangle）")  # ← debug print★
        # 矩形が存在する場合のみ削除
        if self.rect is not None:
            print(f"=== 矩形がある場合：{self.rect}")  # ← debug print★ (削除前の情報を出力)
            self.rect.remove()  # 矩形を削除
            self.rect = None  # 矩形をNoneに設定
        self.zoom_active = False  # ズームモードを終了
        self.canvas.get_tk_widget().config(cursor="arrow")  # カーソルをデフォルトに戻す
        self.canvas.draw()  # 描画を更新
        self.canvas.draw()  # 描画を更新
        print(f"=== 矩形が無い場合：{self.rect}")  # ← debug print★ (削除後に None になっているか確認)
