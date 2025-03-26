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
        print("====== ZoomSelector の初期化開始:（def __init__）")  # ← debug log★
        # 前回の状態を保存する変数★
        self.last_cursor_state = None  # カーソル
        self.last_mode_state = None  # 移動
        # 現在の操作モード（'create', 'move', 'resize', 'rotate', 'rotate_drag'）
        self.mode = None
        # ズーム選択のパラメータ
        self.ax = ax  # Axes
        self.canvas = ax.figure.canvas  # FigureのCanvas
        self.on_zoom_confirm = on_zoom_confirm  # 確定時のコールバック
        self.on_zoom_cancel = on_zoom_cancel  # キャンセル時のコールバック
        self.zoom_active = False  # 選択中フラグ
        # ドラッグ開始時の情報（移動判定用）
        self.press = None
        # 矩形情報
        self.start_x = None  # 開始点（x）
        self.start_y = None  # 開始点（y）
        self.rect = None  # パッチ
        self.saved_rect = None  # 直前の情報
        # 回転用
        self.angle = 0.0  # 回転角（度）
        # イベントハンドラ接続
        self.cid_press = self.canvas.mpl_connect('button_press_event', self.on_press)  # マウスボタンが押された
        self.cid_release = self.canvas.mpl_connect('button_release_event', self.on_release)  # マウスボタンが離された
        self.cid_motion = self.canvas.mpl_connect('motion_notify_event', self.on_motion)  # マウスが移動した
        self.cid_key_press = self.canvas.mpl_connect("key_press_event", self.on_key_press)
        self.cid_key_release = self.canvas.mpl_connect("key_release_event", self.on_key_release)

    def on_key_press(self, event):
        """ Altキーが押されている場合は、回転モードに切り替える """
        # 直前の状態が回転モード以外の場合はデdebug logを出力。出力を制限するための処理
        if self.mode != "rotate":
            print("====== altキーが押された:（def on_key_press）")  # ← debug log★
        # altキーが押されていれば、回転モードに切り替えてカーソルを更新
        if event.key == "alt" and self.mode != "rotate":
            self.mode = "rotate"
            self.update_cursor(event)

    def on_key_release(self, event):
        """ Altキーを離したら通常モードに戻す """
        print("====== altキーが離された:（def on_key_release）")  # ← debug log★
        # altキーが離された場合は、回転モードを解除してカーソルを更新
        if event.key == "alt":
            self.mode = None
            self.update_cursor(event)

    def on_press(self, event):
        """ マウスボタンが押されたときのイベントハンドラ """
        print("====== マウスボタンが押された:（def on_press）")  # ← debug log★
        # 選択されたAxesが異なる場合は無視
        if event.inaxes != self.ax:
            return
        # 中クリックでキャンセル
        if event.button == 2:
            self.cancel_zoom()
            return
        # 右クリックでズーム確定（矩形内なら）
        if event.button == 3:
            if self.rect is not None:  # 矩形が存在する場合
                contains, _ = self.rect.contains(event)  # 矩形内かどうか判定
                if contains:  # 矩形内の場合
                    self.confirm_zoom()
                    return
        # 左クリックの場合
        if event.button == 1:
            # まずは矩形の有無とクリックされた場所からモードを判定する
            # 矩形が存在する場合
            if self.rect is not None:
                # 矩形の現在の位置・サイズを保存（キャンセルの準備）
                x, y = self.rect.get_xy()  # 左上座標
                width = self.rect.get_width()  # 幅
                height = self.rect.get_height()  # 高さ
                self.saved_rect = (x, y, width, height)  # 保存
                # 角の名前と座標を取得
                corners = {
                    'bottom_left': (x, y),
                    'bottom_right': (x+width, y),
                    'top_left': (x, y+height),
                    'top_right': (x+width, y+height)
                }
                # サイズ変更域の設定（他にも同様の設定あり）
                    # 幅と高さの最小値の 10% を許容誤差とする
                    # ただし、幅と高さの最小値が 0 の場合、許容誤差を 0.2 にする
                tol = 0.1 * min(width, height) if min(width, height) != 0 else 0.2
                # 各角の「名前」と「座標」を取得しつつループを回す
                for corner_name, (cx, cy) in corners.items():
#                    print(f"{corner_name}: ({cx}, {cy})")  # ← debug log★
                    # 距離がサイズ調整域以下なら、サイズ変更モードに切り替える
                        # マウスカーソルの座標と、角の座標の距離を計算する
                        # マウスカーソルの座標は、event.xdata, event.ydata で取得できる
                        # 距離は、hypot 関数で計算できる
                    if np.hypot(event.xdata - cx, event.ydata - cy) < tol:
                        print("self.mode : on_press 1 : ", self.mode)  # ← debug log★
                        # 回転モードの場合
                        if self.mode == "rotate":
                            # 左ドラッグによる回転開始
                            self.mode = "rotate_drag"
                            print("self.mode : on_press 2 : ", self.mode)  # ← debug log★
                            cx_rect = x + width/2
                            cy_rect = y + height/2
                            initial_angle = np.degrees(np.arctan2(event.ydata - cy_rect, event.xdata - cx_rect))
                            self.rot_base = self.angle
                            self.press = (cx_rect, cy_rect, initial_angle)
                            self.canvas.draw()
                            return
                        # サイズ変更モードの場合
                        else:
                            # 固定する角（対角）の設定
                            if corner_name == 'bottom_left':
                                fixed = (x+width, y+height)
                            elif corner_name == 'bottom_right':
                                fixed = (x, y+height)
                            elif corner_name == 'top_left':
                                fixed = (x+width, y)
                            elif corner_name == 'top_right':
                                fixed = (x, y)
                            self.mode = 'resize'
                            # 必要な情報を保存して、マウスモーションイベントを待つ
                            self.press = (corner_name, fixed, x, y, width, height, event.xdata, event.ydata)
                            self.canvas.draw()
                            return
                # マウスカーソルが矩形の内側かどうかを判定する
                    # self.rect.contains(event)
                        # event（マウスイベント）の座標が、矩形 self.rect の内部にあるかどうかを判定する。
                        # 戻り値: (True or False, 追加情報)
                    # contains, _ = ...
                        # contains → 矩形の内側なら True、外側なら False
                        # _ → 追加情報（今回は不要なので _ にして無視）
                contains, _ = self.rect.contains(event)
                # マウスカーソルが矩形の内側にある場合、移動モードに切り替える
                    # contains は True か False の 真偽値（ブール値）
                        # True の場合 → マウスカーソルが矩形の内側にある
                        # False の場合 → マウスカーソルが矩形の外にある
                    # contains == True のとき → 移動モードにする
                    # contains == False のとき → 何もしない
                if contains:
                    self.mode = 'move'
                    self.press = (self.rect.get_xy(), event.xdata, event.ydata)  # 移動開始点と現在の座標を保存
                    self.canvas.draw()
                    return
            # 矩形が存在しない場合は、新規で矩形を作成してズーム処理中にする
            else:
                self.start_x, self.start_y = event.xdata, event.ydata
                self.rect = patches.Rectangle((self.start_x, self.start_y), 0, 0,
                            edgecolor='white',
                            facecolor='none',
#                            facecolor='red',  # ← debug log★矩形内を赤色で表示
#                            alpha=0.3,  # ← debug log★透明度
                            linestyle='solid'
                        )
                self.ax.add_patch(self.rect)
                self.zoom_active = True
                self.mode = 'create'
            self.canvas.draw()

    def on_motion(self, event):
        """ マウスが移動したときのイベントハンドラ """
        # ズーム選択中でない、または選択されたAxesが異なる場合は何もしない
        if not self.zoom_active or event.inaxes != self.ax:
            return
        # カーソル変更処理を実行
        self.update_cursor(event)
        # カレントモードを初期化して、各条件に応じて現在のモードを取得 debug log★
        current_mode_state = None
        if self.mode == 'resize' and self.press is not None:
            current_mode_state = 'resize'
        elif self.mode == 'move' and self.press is not None:
            current_mode_state = 'move'
        elif self.mode == 'create':
            current_mode_state = 'create'
        # 現在のモードと前回のモードが異なる場合、状態が変化したと判断してログを出力  debug log★
        if current_mode_state != self.last_mode_state:
            print("====== マウスが移動した:（def on_motion）")
            if current_mode_state == 'resize':
                print("=== サイズ変更モード")
            elif current_mode_state == 'move':
                print("=== 移動モード")
            elif current_mode_state == 'create':
                print("=== 新規作成モード")
            self.last_mode_state = current_mode_state
        # 回転ドラッグ中 ＆ ドラッグ中の場合 ＆ 矩形が存在する場合、矩形を回転
#        print("event.xdata : on_motion : ", event.xdata)  # ← debug log★
#        print("event.ydata : on_motion : ", event.ydata)  # ← debug log★
        if self.mode == "rotate_drag" and self.press is not None and self.rect is not None:
            cx_rect, cy_rect, initial_angle = self.press
            current_angle = np.degrees(np.arctan2(event.ydata - cy_rect, event.xdata - cx_rect))
            angle_diff = current_angle - initial_angle
            new_angle = self.rot_base + angle_diff
            self.angle = new_angle
            t = transforms.Affine2D().rotate_deg_around(cx_rect, cy_rect, new_angle) + self.ax.transData
            self.rect.set_transform(t)
            self.canvas.draw()
            return
        # サイズ変更モード中、かつマウスが移動した場合、矩形のサイズを変更
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
        # 移動モード中、かつマウスが移動した場合、矩形の位置を更新
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
        print("====== マウスを離した:（def on_release）")  # ← debug log★
        # 現在のモードが指定された5種類のいずれか、かつイベントが self.ax 内で発生した場合に処理を実行
        if self.mode in ['resize', 'move', 'create', 'rotate', 'rotate_drag'] and event.inaxes == self.ax:
            # 新規作成モードの場合は、マウスが離されたら矩形を確定する
            if self.mode == 'create':
                x0, y0 = self.start_x, self.start_y
                dx = event.xdata - x0
                dy = event.ydata - y0
                # サイズが 0 以上の場合のみ矩形を作成
                if dx != 0 and dy != 0:
                    new_x = min(x0, event.xdata)
                    new_y = min(y0, event.ydata)
                    new_width = abs(dx)
                    new_height = abs(dy)
                    self.rect.set_xy((new_x, new_y))
                    self.rect.set_width(new_width)
                    self.rect.set_height(new_height)
                print("self.mode : on_release 1 : ", self.mode)  # ← debug log★
            # 回転ドラッグ中の場合、モードを通常の回転モードに戻す
            elif self.mode == 'rotate_drag':
                self.press = None
                self.mode = "rotate"
            # それ以外の場合、モードをNoneに設定
            self.press = None
            self.mode = None
            print("self.mode : on_release 2 : ", self.mode)  # ← debug log★
        self.canvas.draw()

    def update_cursor(self, event):
        """ マウス位置に応じてカーソルを変更する """
        # カーソル状態を初期化
        current_cursor_state = None
        # ◆　矩形がない場合は、通常のカーソルに変更
        if self.rect is None:
            current_cursor_state = "arrow"
            # カーソル状態が変化した場合のみプリント debug log★
            if self.last_cursor_state != current_cursor_state:
                print("====== 通常のカーソル（矩形無し）（def update_cursor）：矢印 arrow")
                self.canvas.get_tk_widget().config(cursor="arrow")
                self.last_cursor_state = current_cursor_state
                return
            return
        # ◆　以下は、矩形がある場合の処理
        # 矩形の座標とサイズを取得
        x, y = self.rect.get_xy()
        width = self.rect.get_width()
        height = self.rect.get_height()
        # 角を判定用（サイズ変更用）
        corners = {
            'bottom_left': (x, y),
            'bottom_right': (x + width, y),
            'top_left': (x, y + height),
            'top_right': (x + width, y + height)
        }
        # サイズ変更域の設定（他にも同様の設定あり）
        tol = 0.1 * min(width, height) if min(width, height) != 0 else 0.2
        # マウスイベントの座標データが存在しない場合は、何もしない
        if event.xdata is None or event.ydata is None:
            return
        # マウスカーソルが矩形の角にあるかどうかを判定する
        # 各角の「名前」と「座標」を取得しつつループを回す
        for corner, (cx, cy) in corners.items():
            # ◆　マウスカーソルと角の距離がサイズ調整域以下の場合に処理を実行
            # 距離がサイズ調整域以上の場合は何もしない
                # on_pressにもあるので、詳細はそちらを参照
            if np.hypot(event.xdata - cx, event.ydata - cy) < tol:
                # ◆　回転モードの場合（"rotate" および "rotate_drag" 共に対象）
                if self.mode in ["rotate", "rotate_drag"]:
                    current_cursor_state = "rotate"
                    # カーソル状態が変化した場合のみプリント  debug log★
                    if self.last_cursor_state != current_cursor_state:
                        print("====== カーソル変更（def update_cursor）：回転 exchange")  # debug log★
                        self.canvas.get_tk_widget().config(cursor="exchange")  # カーソルを回転カーソルに変更
                        self.last_cursor_state = current_cursor_state
                        return
                # ◆　サイズ変更モードの場合
                else:
                    current_cursor_state = "crosshair"
                    # カーソル状態が変化した場合のみプリント  debug log★
                    if self.last_cursor_state != current_cursor_state:
                        print("====== カーソル変更（def update_cursor）：十字 crosshair")
                        self.canvas.get_tk_widget().config(cursor="crosshair")
                        self.last_cursor_state = current_cursor_state
                        return
                    return
        # マウスカーソルが矩形の内側かどうかを判定する
            # on_pressにもあるので、詳細はそちらを参照
        contains, _ = self.rect.contains(event)
        # ◆　移動モードの場合（マウスカーソルが矩形の内側にある場合）
            # on_pressにも似たような部分があるので、詳細はそちらを参照
        if contains:
            current_cursor_state = "fleur"
            # カーソル状態が変化した場合のみプリント  debug log★
            if self.last_cursor_state != current_cursor_state:
                print("=== カーソル変更（def update_cursor）：移動 fleur")
                self.canvas.get_tk_widget().config(cursor="fleur")
                self.last_cursor_state = current_cursor_state
                return
            return
        # ◆　諸々の範囲外の場合
        # カーソル状態が変化した場合のみプリント  debug log★
        if self.last_cursor_state != "arrow":
            print("====== 通常のカーソル（諸々の範囲外）（def update_cursor）：矢印 arrow")
            self.canvas.get_tk_widget().config(cursor="arrow")
            self.last_cursor_state = "arrow"
            return

    def confirm_zoom(self):
        """ 右クリックによるズーム確定時、矩形情報からズームパラメータを計算してコールバック呼出 """
        print("====== ズーム確定:（def confirm_zoom）")  # ← debug log★
        # 矩形がない場合はなにもしない
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
        """ 中クリックによるズームキャンセル時、矩形情報をもとに戻す """
        print("====== ズームキャンセル:（def cancel_zoom）")  # ← debug log★
        # 矩形が確定される前＆保存された矩形情報がある＆現在の矩形も存在する場合に処理を実行
        if self.zoom_active and self.saved_rect is not None and self.rect is not None:
            print("=== ズーム中、セーブ情報あり、矩形有り")  # ← debug log★
            x, y, width, height = self.saved_rect  # 保存した矩形の情報を取得
            self.rect.set_xy((x, y))  # 矩形の位置を設定
            self.rect.set_width(width)  # 矩形の幅を設定
            self.rect.set_height(height)  # 矩形の高さを設定
            self.saved_rect = None  # 保存した矩形の情報をクリア
            self.canvas.draw()
        # それ以外の場合は、コールバックを呼び出す
        else:
            print("=== 矩形無し")  # ← debug log★
            # コールバックが存在する場合のみ呼び出す
            if self.on_zoom_cancel:
                print("コールバックがある")  # ← debug log★
                self.clear_rectangle()  # 矩形を削除
                self.zoom_active = False  # ズームモードを終了
                print("通常のカーソル（def cancel_zoom）：矢印 arrow")  # ← debug log★
                self.canvas.get_tk_widget().config(cursor="arrow")  # カーソルをデフォルトに戻す
                self.on_zoom_cancel()  # コールバックを呼び出す

    def clear_rectangle(self):
        """ 矩形を消去 """
        print("====== 矩形を消去:（def clear_rectangle）")  # ← debug log★
        # 矩形が存在する場合のみ削除
        if self.rect is not None:
            print(f"=== 矩形がある場合：{self.rect}")  # ← debug log★ (削除前の情報を出力)
            self.rect.remove()  # 矩形を削除
            self.rect = None  # 矩形をNoneに設定
        self.zoom_active = False  # ズームモードを終了
        print("通常のカーソル（def clear_rectangle）：矢印 arrow")  # ← debug log★
        self.canvas.get_tk_widget().config(cursor="arrow")  # カーソルをデフォルトに戻す
        self.canvas.draw()  # 描画を更新
        print(f"=== 矩形が無い場合：{self.rect}")  # ← debug log★ (削除後に None になっているか確認)
