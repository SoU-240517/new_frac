from enum import Enum, auto
import matplotlib.patches as patches

class ZoomState(Enum):
    """ズーム操作の状態を表す列挙型"""
    NO_RECT = auto()           # ズーム領域なし
    CREATE = auto()            # ズーム領域の新規作成モード

class ZoomSelector:
    def __init__(self, ax, on_zoom_confirm, on_zoom_cancel):
        """
        ズームセレクターのインスタンスを作成する
        Args:
            ax: 対象の matplotlib Axes
            on_zoom_confirm: ズーム確定時のコールバック（zoom_params を引数に取る）
            on_zoom_cancel: ズームキャンセル時のコールバック
        """
        print("START : __init__.ZoomSelector")
        self.ax = ax  # 描画対象の Axes オブジェクト
        self.canvas = ax.figure.canvas  # キャンバスオブジェクト
        self.on_zoom_confirm = on_zoom_confirm  # ズーム確定時のコールバック
        self.on_zoom_cancel = on_zoom_cancel  # ズームキャンセル時のコールバック
        self.start_x = None  # ドラッグ開始時のx座標
        self.start_y = None  # ドラッグ開始時のy座標
        self.rect = None  # ズーム領域：現在（構造は matplotlib.patches.Rectangle）
        self._state = ZoomState.NO_RECT  # 内部状態変数（アンダースコア付き）

        # イベントハンドラ接続
        self.cid_press       = self.canvas.mpl_connect('button_press_event', self.on_press)
        self.cid_release     = self.canvas.mpl_connect('button_release_event', self.on_release)
        self.cid_motion      = self.canvas.mpl_connect('motion_notify_event', self.on_motion)

    # プロパティの定義 -------------------------------------------------------------------------------------------------------------------

    @property
    def state(self):
        """
        ゲッター：ズーム操作の現在の状態を返すだけ
        Returns:
            ZoomState: 現在のズーム操作の状態
        """
        return self._state

    @state.setter
    def state(self, new_state):
        """
        セッター：新しい状態（new_state）が現在の状態（self._state）と異なる場合にのみ、状態を更新する
        Args:
            new_state (ZoomState): 新しい状態
        Returns:
            None
        """
        old_state = self._state  # 現在の状態を old_state に記録
        if old_state == new_state:  # 状態が変化していなければ、メソッド終了
            return
        self._state = new_state  # ズーム操作の状態に変化がある場合は、現在の状態を更新

    # on_press 関連 ---------------------------------------------------------------------------------------------------------------------

    def on_press(self, event):
        """マウスボタン押下時の処理"""
        state_handlers = {
            ZoomState.NO_RECT: self._handle_no_rect_press,
        }
        if self.state in state_handlers:
            state_handlers[self.state](event)

        self.canvas.draw()

    def _handle_no_rect_press(self, event):
        """マウスボタン押下：ズーム領域なし"""
        if event.button == 1:
            self.state = ZoomState.CREATE
            self._begin_rect_set(event)

    def _begin_rect_set(self, event):
        """ズーム領域作成時の初期化処理"""
        self.start_x, self.start_y = event.xdata, event.ydata  # ズーム領域開始点のマウス位置を記録

        self.rect = patches.Rectangle(  # 取得した情報でズーム領域を作成（左押下直後なので、幅と高さはゼロ）
            (self.start_x, self.start_y), 0, 0,
            edgecolor='white', facecolor='none', linestyle='solid'
        )

        self.ax.add_patch(self.rect)  # ズーム領域をキャンバスに追加

    def on_motion(self, event):
        """マウス移動時の処理"""
        state_handlers = {
            ZoomState.CREATE: self._update_rect,
        }

        if self.state in state_handlers:  # ズーム状態と対応するメソッドがある場合、それを実行
            state_handlers[self.state](event)

        self.canvas.draw()

    def _update_rect(self, event):
        """ズーム領域の更新"""
        diff_x = event.xdata - self.start_x
        diff_y = event.ydata - self.start_y

        self.rect.set_bounds(
            min(self.start_x, event.xdata),
            min(self.start_y, event.ydata),
            abs(diff_x),
            abs(diff_y)
        )

    def on_release(self, event):
        """マウスボタン開放時の処理"""
        state_handlers = {
            ZoomState.CREATE: self._handle_create_release,
        }

        if self.state in state_handlers:
            state_handlers[self.state](event)

        self.canvas.draw()

    def _handle_create_release(self, event):
        """ズーム領域作成時のマウスボタン開放時の処理"""
        self._finalize_rect(event)
        self.state = ZoomState.NO_RECT

    def _finalize_rect(self, event):
        """ズーム領域の作成を確定"""
        end_x, end_y = event.xdata, event.ydata

        diff_x = end_x - self.start_x
        diff_y = end_y - self.start_y

        if diff_x == 0 or diff_y == 0:
            self._clear_rect()
            self.state = ZoomState.NO_RECT
            return

        new_x = self.start_x if diff_x > 0 else end_x
        new_y = self.start_y if diff_y > 0 else end_y
        width = abs(diff_x)
        height = abs(diff_y)

        self.rect.set_bounds(new_x, new_y, width, height)

    def _clear_rect(self):
        """ズーム領域をクリア"""
        self.rect.remove()  # ズーム領域の削除
        self.start_x = self.start_y = None  # 開始座標リセット

        self.canvas.draw()
