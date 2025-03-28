import numpy as np
import matplotlib.patches as patches
import matplotlib.transforms as transforms
from enum import Enum, auto

class ZoomState(Enum):                    # ズーム操作の状態を表す列挙型
    NO_ZOOM_AREA = auto()                 # ズーム領域無し（矩形が存在しない）
    CREATE = auto()                       # ズーム領域新規作成モード（左ボタン ONで開始）
    WAIT_NOKEY_ZOOM_AREA_EXISTS = auto()  # ズーム領域有り（キー入力無し）
    MOVE = auto()                         # 領域移動モード（矩形内で左ドラッグ）
    WAIT_SHIFT_RESIZE = auto()            # リサイズ待機モード（shift ON）
    RESIZE = auto()                       # リサイズモード（shift＋左ドラッグ）
    WAIT_ALT_ROTATE = auto()              # 回転待機モード（alt ON）
    ROTATE = auto()                       # 回転モード（alt＋左ドラッグ）

class ZoomSelector:
    def __init__(self, ax, on_zoom_confirm, on_zoom_cancel):
        """
        ax: 対象の matplotlib Axes
        on_zoom_confirm: ズーム確定時のコールバック（zoom_params を引数に取る）
        on_zoom_cancel: ズームキャンセル時のコールバック
        """
        self.ax = ax
        self.canvas = ax.figure.canvas
        self.on_zoom_confirm = on_zoom_confirm
        self.on_zoom_cancel = on_zoom_cancel

        self.state = ZoomState.NO_ZOOM_AREA  # 初期状態：NO_ZOOM_AREA を設定

        self.rect = None         # 現在のズーム矩形（存在すれば領域有り）
        self.last_rect = None    # 直前の描画情報（キャンセル用）
        self.press = None        # ドラッグ開始時の情報（移動・リサイズ・回転共通）
        self.start_x = None      # 新規作成開始時の x 座標
        self.start_y = None      # 新規作成開始時の y 座標

        self.current_key = None  # 現在 ON のキー（'shift' または 'alt'）
        key_state = {"Shift": False, "Alt": False}
        self.angle = 0.0         # 現在の回転角（度）
        self.rot_base = 0.0      # 回転開始時の角度
        self.last_cursor_state = "arrow"

        # イベントハンドラ接続
        self.cid_press       = self.canvas.mpl_connect('button_press_event', self.on_press)
        self.cid_release     = self.canvas.mpl_connect('button_release_event', self.on_release)
        self.cid_motion      = self.canvas.mpl_connect('motion_notify_event', self.on_motion)
        self.cid_key_press   = self.canvas.mpl_connect("key_press_event", self.on_key_press)
        self.cid_key_release = self.canvas.mpl_connect("key_release_event", self.on_key_release)

    def on_press(self, event):
        if event.inaxes != self.ax:  # 描画領域外：メソッド終了
            return

        if self.state == ZoomState.NO_ZOOM_AREA:  # on_press：NO_ZOOM_AREA の場合の処理
            if event.button == 1:
                self.state = ZoomState.CREATE  # on_press：ズーム領域無し、左ボタン ON：CREATE へ変更
                self.start_x, self.start_y = event.xdata, event.ydata
                self.rect = patches.Rectangle(
                    (self.start_x, self.start_y), 0, 0,
                    edgecolor='white', facecolor='none', linestyle='solid'
                )
                self.ax.add_patch(self.rect)
            elif event.button == 2:  # 中ボタン ON でズーム取り消し（直前情報があれば復元、なければ何もしない）
                self._handle_cancel()

        elif self.state == ZoomState.WAIT_NOKEY_ZOOM_AREA_EXISTS:  # on_press：WAIT_NOKEY_ZOOM_AREA_EXISTS の場合の処理
            if event.button == 1 and self._cursor_inside_rect(event):  # 左ボタン ON 、矩形内
                self.state = ZoomState.MOVE  # on_press：矩形内で左ボタン ON：MOVE へ変更
                self.press = (self.rect.get_xy(), event.xdata, event.ydata)  # 移動開始位置を記録
            elif event.button == 3 and self._cursor_inside_rect(event):  # 右ボタン ON → 領域確定
                self.confirm_zoom()
            elif event.button == 2:  # 中ボタン ON → キャンセル
                self._handle_cancel()

        elif self.state == ZoomState.WAIT_SHIFT_RESIZE:  # on_press：WAIT_SHIFT_RESIZE の場合の処理
            if event.button == 1 and self._pointer_near_corner(event):
                self.state = ZoomState.RESIZE  # on_press：矩形内で左ボタン ON：RESIZE へ変更
                self.press = self._prepare_resize(event)  # リサイズモードの準備を行う

        elif self.state == ZoomState.WAIT_ALT_ROTATE:  # on_press：WAIT_ALT_ROTATE の場合の処理
            if event.button == 1 and self._pointer_near_corner(event):
                self.state = ZoomState.ROTATE  # on_press：矩形内で左ボタン ON：ROTATE へ変更
                cx, cy = self._get_rect_center()
                initial_angle = np.degrees(np.arctan2(event.ydata - cy, event.xdata - cx))
                self.rot_base = self.angle
                self.press = (cx, cy, initial_angle)

        self.canvas.draw()

    def on_motion(self, event):
        if event.inaxes != self.ax:
            return

        if self.state == ZoomState.CREATE:  # on_motion：CREATE ならドラッグで矩形のサイズを更新
            dx = event.xdata - self.start_x
            dy = event.ydata - self.start_y
            new_x = min(self.start_x, event.xdata)
            new_y = min(self.start_y, event.ydata)
            self.rect.set_xy((new_x, new_y))
            self.rect.set_width(abs(dx))
            self.rect.set_height(abs(dy))

        elif self.state == ZoomState.MOVE:  # on_motion：移動モードならドラッグで矩形の位置を更新
            orig_xy, press_x, press_y = self.press
            dx = event.xdata - press_x
            dy = event.ydata - press_y
            new_xy = (orig_xy[0] + dx, orig_xy[1] + dy)
            self.rect.set_xy(new_xy)

        elif self.state == ZoomState.RESIZE:  # on_motion：リサイズモードならドラッグで矩形のサイズを更新
            (corner_name, fixed, orig_x, orig_y, orig_width, orig_height, press_x, press_y) = self.press
            new_x = min(fixed[0], event.xdata)
            new_y = min(fixed[1], event.ydata)
            self.rect.set_xy((new_x, new_y))
            self.rect.set_width(abs(fixed[0] - event.xdata))
            self.rect.set_height(abs(fixed[1] - event.ydata))

        elif self.state == ZoomState.ROTATE:  # on_motion：回転モードならドラッグで矩形の回転を更新
            if self.press is None:
                return
            cx, cy, initial_angle = self.press
            current_angle = np.degrees(np.arctan2(event.ydata - cy, event.xdata - cx))
            angle_diff = current_angle - initial_angle
            new_angle = self.rot_base + angle_diff
            self.angle = new_angle
            t = transforms.Affine2D().rotate_deg_around(cx, cy, new_angle) + self.ax.transData
            self.rect.set_transform(t)

        # カーソルの更新（状態と位置に応じて）
        self.update_cursor(event)
        self.canvas.draw()

    def on_release(self, event):
        if event.inaxes != self.ax:
            return

        if self.state == ZoomState.CREATE:  # on_release：CREATE が完了した場合の処理
            dx = event.xdata - self.start_x
            dy = event.ydata - self.start_y
            if dx != 0 and dy != 0:
                new_x = min(self.start_x, event.xdata)
                new_y = min(self.start_y, event.ydata)
                self.rect.set_xy((new_x, new_y))
                self.rect.set_width(abs(dx))
                self.rect.set_height(abs(dy))
                self.state = ZoomState.WAIT_NOKEY_ZOOM_AREA_EXISTS  # on_release：矩形作成完了：WAIT_NOKEY_ZOOM_AREA_EXISTS へ変更
            else:
                self._clear_rectangle()
                self.state = ZoomState.NO_ZOOM_AREA  # on_release：矩形が未作成：NO_ZOOM_AREA へ変更

        elif self.state in (ZoomState.MOVE):  # on_release：移動モード完了の場合の処理
            self.press = None
            self.state = ZoomState.WAIT_NOKEY_ZOOM_AREA_EXISTS  # on_release：移動完了：WAIT_NOKEY_ZOOM_AREA_EXISTS へ変更

        elif self.state in (ZoomState.RESIZE):  # on_release：リサイズモードが完了した場合の処理
            self.press = None
            # shift ON なら、WAIT_SHIFT_RESIZE に遷移
            if event.key == 'shift':
                self.state = ZoomState.WAIT_SHIFT_RESIZE  # on_release：リサイズ完了、shift ON：WAIT_SHIFT_RESIZE へ変更
            else:
                self.state = ZoomState.WAIT_NOKEY_ZOOM_AREA_EXISTS  # on_release：リサイズ完了、shift OFF：WAIT_NOKEY_ZOOM_AREA_EXISTS へ変更

        elif self.state in (ZoomState.ROTATE):  # on_release：回転モードが完了した場合の処理
            self.press = None
            # alt ON なら、WAIT_ALT_ROTATE に遷移
            if event.key == 'alt':
                self.state = ZoomState.WAIT_ALT_ROTATE  # on_release：回転完了、alt ON：WAIT_ALT_ROTATE へ変更
            else:
                self.state = ZoomState.WAIT_NOKEY_ZOOM_AREA_EXISTS  # on_release：回転完了、alt OFF：WAIT_NOKEY_ZOOM_AREA_EXISTS へ変更

        self.canvas.draw()

    def on_key_press(self, event):
        # キー割り込みは、ズーム領域が存在する状態または移動中のみ有効
        if self.state == ZoomState.WAIT_NOKEY_ZOOM_AREA_EXISTS and event.key in ['shift', 'alt']:  # on_key_press：キー割り込み条件
            self.current_key = event.key

            if event.key == 'shift':  # shift ON → リサイズモードへ（マウスカーソルが角に近いかチェック）
                if self._pointer_near_corner(event):  # マウスカーソルが角許容範囲内の場合
                    self.state = ZoomState.WAIT_SHIFT_RESIZE  # on_key_press：shift ON、カーソルが角許容範囲内：WAIT_SHIFT_RESIZE へ変更

            elif event.key == 'alt':  # alt ON → 回転モードへ（マウスカーソルが角に近いかチェック）
                if self._pointer_near_corner(event):  # マウスカーソルが角許容範囲内の場合
                    self.state = ZoomState.WAIT_ALT_ROTATE  # on_key_press：alt ON、カーソルが角許容範囲内：WAIT_ALT_ROTATE へ変更

        self.update_cursor(event)
        self.canvas.draw()

    def on_key_release(self, event):
        if self.current_key == event.key:
            self.current_key = None
            if self.state in (ZoomState.WAIT_SHIFT_RESIZE, ZoomState.RESIZE, ZoomState.WAIT_ALT_ROTATE, ZoomState.ROTATE):  # キー割り込みで入ったモードの場合、解除して待機状態へ戻す
                self.state = ZoomState.WAIT_NOKEY_ZOOM_AREA_EXISTS  # on_key_release：キー割り込みが解除された場合：WAIT_NOKEY_ZOOM_AREA_EXISTS へ変更
        self.update_cursor(event)
        self.canvas.draw()

    def confirm_zoom(self):
        """
        右ボタン ON による確定時に、矩形情報からズームパラメータを生成しコールバック呼び出し
        """
        if self.rect is None:
            return
        x, y = self.rect.get_xy()
        width = self.rect.get_width()
        height = self.rect.get_height()
        center_x = x + width / 2.0
        center_y = y + height / 2.0
        zoom_params = {
            "center_x": center_x,
            "center_y": center_y,
            "width": abs(width),
            "height": abs(height),
            "rotation": self.angle
        }
        self._clear_rectangle()
        if self.on_zoom_confirm:
            self.on_zoom_confirm(zoom_params)
        self.state = ZoomState.NO_ZOOM_AREA  # confirm_zoom：ズーム確定後：NO_ZOOM_AREA へ変更

    def _handle_cancel(self):
        """
        中ボタン ON またはキャンセル操作で、直前の描画情報があれば復元、
        無い場合は矩形を削除してコールバックを呼び出す
        """
        if self.last_rect and self.rect:
            x, y, width, height = self.last_rect
            self.rect.set_xy((x, y))
            self.rect.set_width(width)
            self.rect.set_height(height)
            self.state = ZoomState.WAIT_NOKEY_ZOOM_AREA_EXISTS  # _handle_cancel：ズームキャンセル後、矩形無し：WAIT_NOKEY_ZOOM_AREA_EXISTS へ変更
        else:
            self._clear_rectangle()
            if self.on_zoom_cancel:
                self.on_zoom_cancel()
                self.state = ZoomState.NO_ZOOM_AREA  # _handle_cancel：ズームキャンセル後、矩形無し：NO_ZOOM_AREA へ変更

    def _clear_rectangle(self):
        if self.rect is not None:
            self.rect.remove()
            self.rect = None
        self.canvas.get_tk_widget().config(cursor="arrow")
        self.canvas.draw()

    def _get_rect_center(self):
        x, y = self.rect.get_xy()
        width = self.rect.get_width()
        height = self.rect.get_height()
        return (x + width / 2.0, y + height / 2.0)

    def _pointer_near_corner(self, event):
        """
        マウス位置が矩形の角に近いかどうかを判定する
        許容範囲 tol = 0.1 * min(width, height)（ただし min が 0 の場合は 0.2）
        """
        if self.rect is None:
            return False
        x, y = self.rect.get_xy()
        width = self.rect.get_width()
        height = self.rect.get_height()
        tol = 0.1 * min(width, height) if min(width, height) != 0 else 0.2
        corners = [(x, y), (x + width, y), (x, y + height), (x + width, y + height)]
        for cx, cy in corners:
            if np.hypot(event.xdata - cx, event.ydata - cy) < tol:
                return True
        return False

    def _prepare_resize(self, event):
        """
        マウス位置から最も近い角を選定し、対角固定のため固定すべき点を求める。
        戻り値は、対角固定のための固定点の座標と名前
        """
        # 矩形の現在の位置・サイズを保存
        x, y = self.rect.get_xy()
        width = self.rect.get_width()
        height = self.rect.get_height()
        # 角の名前と座標を取得
        corners = {
            'bottom_left': (x, y),
            'bottom_right': (x + width, y),
            'top_left': (x, y + height),
            'top_right': (x + width, y + height)
        }
        nearest_corner = None
        min_dist = float('inf')
        nearest_key = None  # 最も近い角の名前を保存する変数
        for key, (cx, cy) in corners.items():
            dist = np.hypot(event.xdata - cx, event.ydata - cy)
            if dist < min_dist:
                min_dist = dist
                nearest_corner = (cx, cy)
                nearest_key = key
        # 固定する対角の点を設定（例：bottom_left の場合は top_right が固定点）
        if nearest_key == 'bottom_left':
            fixed = (x + width, y + height)
        elif nearest_key == 'bottom_right':
            fixed = (x, y + height)
        elif nearest_key == 'top_left':
            fixed = (x + width, y)
        elif nearest_key == 'top_right':
            fixed = (x, y)
        return (nearest_key, fixed, x, y, width, height, event.xdata, event.ydata)

    def _cursor_inside_rect(self, event):
        """マウスカーソルが矩形内部にあるかどうか"""
        if self.rect is None:
            return False
        contains, _ = self.rect.contains(event)
        return contains

    def update_cursor(self, event):
        """
        各状態およびカーソル位置に応じたカーソル形状を設定する。
         - ズーム領域無しや新規作成中は arrow
         - 移動中なら fleur
         - リサイズ中は、角近傍なら crosshair、それ以外は arrow
         - 回転中は、角近傍なら exchange、それ以外は arrow
        """
        cursor = "arrow"
        if self.state in (ZoomState.NO_ZOOM_AREA, ZoomState.CREATE):  # update_cursor：NO_ZOOM_AREA か CREATE 場合の処理
            cursor = "arrow"
        elif self.state == ZoomState.MOVE:  # update_cursor：MOVE の場合の処理
            cursor = "fleur"
        # WAIT_SHIFT_RESIZE か RESIZE の場合は、角近傍なら crosshair、それ以外は arrow
        elif self.state in (ZoomState.WAIT_SHIFT_RESIZE, ZoomState.RESIZE):  # update_cursor：WAIT_SHIFT_RESIZE ＆ RESIZE の場合の処理
            cursor = "crosshair" if self._pointer_near_corner(event) else "arrow"
        # WAIT_ALT_ROTATE か ROTATE の場合は、角近傍なら exchange、それ以外は arrow
        elif self.state in (ZoomState.WAIT_ALT_ROTATE, ZoomState.ROTATE):  # update_cursor：WAIT_ALT_ROTATE ＆ ROTATE の場合の処理
            cursor = "exchange" if self._pointer_near_corner(event) else "arrow"
        elif self.state == ZoomState.WAIT_NOKEY_ZOOM_AREA_EXISTS:  # update_cursor：WAIT_NOKEY_ZOOM_AREA_EXISTSの場合の処理
            cursor = "fleur" if self._cursor_inside_rect(event) else "arrow"
        else:
            cursor = "arrow"

        self.canvas.get_tk_widget().config(cursor=cursor)  # カーソルの形状を更新
        self.last_cursor_state = cursor
