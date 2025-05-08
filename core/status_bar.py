import threading
import time
import tkinter as tk
from tkinter import ttk
from typing import Optional
from debug import DebugLogger, LogLevel

class StatusBarManager:
    """ステータスバーの表示とアニメーションを管理するクラス

    ステータスバーの表示とアニメーションを管理し、描画時間の計測と表示を行います。

    Attributes:
        _TIME_FORMAT (str): 時間表示のフォーマット文字列（分:秒:ミリ秒）
        _ANIMATION_INTERVAL (float): アニメーションの間隔（秒）
        _TIME_UPDATE_INTERVAL (int): 時間更新の間隔（ミリ秒）
        root (tk.Tk): Tkinterのルートウィンドウ
        status_frame (ttk.Frame): ステータスバーを配置するフレーム
        logger (DebugLogger): デバッグログを管理するLogger
        _draw_start_time (Optional[float]): 描画開始時刻
        _status_timer_id (Optional[str]): 時間更新タイマーID
        status_label (ttk.Label): ステータス表示用のラベル
        _animation_state (AnimationState): アニメーション状態を管理するAnimationState
    """
    _TIME_FORMAT = "[{:>3}分 {:02}秒 {:03}ms] " # 時間表示のフォーマット（分:秒:ミリ秒）
    _ANIMATION_INTERVAL = 0.1 # アニメーションの間隔（秒）
    _TIME_UPDATE_INTERVAL = 1000 # 時間更新の間隔（ミリ秒）

    def __init__(self, root: tk.Tk, status_frame: ttk.Frame, logger: DebugLogger):
        """StatusBarManager クラスのコンストラクタ

        Args:
            root (tk.Tk): Tkinterのルートウィンドウ
            status_frame (ttk.Frame): ステータスバーを配置するフレーム
            logger (DebugLogger): デバッグログを管理するLogger
        """
        self.root = root
        self.status_frame = status_frame
        self.logger = logger

        # 描画時間の計測用変数
        self._draw_start_time: Optional[float] = None

        # 時間更新タイマーID
        self._status_timer_id: Optional[str] = None

        # ステータスラベルの初期化
        self.status_label = ttk.Label(
            self.status_frame,
            text=self._format_time(0, 0, 0) + "準備中...",
            width=25
        )
        self.status_label.pack(side=tk.LEFT, padx=5, pady=2)

        # アニメーション状態の初期化
        self._animation_state = AnimationState()

    def start_animation(self) -> None:
        """ステータスバーの描画中アニメーションを開始

        - アニメーション状態を開始
        - 描画開始時刻を記録
        - 時間更新とアニメーションスレッドを開始

        Raises:
            ログ出力: アニメーションが既に実行中の場合
        """
        if self._animation_state.is_running:
            self.logger.log(LogLevel.ERROR, "ステータスアニメーションは既に実行中")
            return

        self._animation_state.start()
        self._draw_start_time = time.perf_counter()
        self._schedule_time_update()
        self._start_animation_thread()

    def _start_animation_thread(self) -> None:
        """アニメーション用スレッドを開始
        - アニメーションスレッドを作成し、開始する
        """
        try:
            self.logger.log(LogLevel.CALL, "ステータスアニメーションスレッドを開始")
            self._animation_state.thread = threading.Thread(
                target=self._run_animation,
                daemon=True
            )
            self._animation_state.thread.start()
        except Exception as e:
            self.logger.log(LogLevel.ERROR, "ステータスアニメーションスレッドの開始失敗", {"message": e})
            self._animation_state.stop()

    def _run_animation(self) -> None:
        """アニメーションスレッドのメインループ
        - アニメーション状態が続く限り、ドットアニメーションを更新し続ける
        """
        while self._animation_state.is_running:
            self._animation_state.dots = (self._animation_state.dots + 1) % (self._animation_state.max_dots + 1)
            self._update_label_text(f"描画中{'.' * self._animation_state.dots}")
            time.sleep(self._ANIMATION_INTERVAL)

    def _update_label_text(self, animation_text: str) -> None:
        """ステータスラベルのテキストを更新
        - 時間経過とアニメーションテキストを組み合わせて表示を更新

        Args:
            animation_text: アニメーション用のテキスト (ドットパターンなど)
        """
        if self._draw_start_time is not None:
            minutes, seconds, milliseconds = self._calculate_elapsed_time()
            time_str = self._format_time(minutes, seconds, milliseconds)
            self.status_label.config(text=time_str + animation_text)
        else:
            self.status_label.config(text=self._format_time(0, 0, 0) + animation_text)

    def _calculate_elapsed_time(self) -> tuple[int, int, int]:
        """経過時間を分、秒、ミリ秒に変換
        - 描画開始時刻から現在までの経過時間を計算し、分・秒・ミリ秒に変換

        Returns:
            tuple[int, int, int]: (分, 秒, ミリ秒)
        """
        elapsed_time = time.perf_counter() - self._draw_start_time
        minutes = int(elapsed_time // 60)
        seconds = int(elapsed_time % 60)
        milliseconds = int((elapsed_time - int(elapsed_time)) * 1000)
        return minutes, seconds, milliseconds

    def _format_time(self, minutes: int, seconds: int, milliseconds: int) -> str:
        """時間表示をフォーマット
        - 分・秒・ミリ秒を指定されたフォーマットに変換

        Args:
            minutes: 経過時間 (分)
            seconds: 経過時間 (秒)
            milliseconds: 経過時間 (ミリ秒)

        Returns:
            str: フォーマットされた時間表示文字列
        """
        return self._TIME_FORMAT.format(minutes, seconds, milliseconds)

    def _schedule_time_update(self) -> None:
        """時間更新をスケジュール
        - アニメーションが実行中であれば、時間更新をスケジュールする
        - 実行中でなければ、時間更新をキャンセルする
        """
        if self._animation_state.is_running:
            self._status_timer_id = self.root.after(
                self._TIME_UPDATE_INTERVAL,
                self._update_time
            )
        else:
            self._cancel_time_update()

    def _update_time(self) -> None:
        """時間表示を更新し、次の更新をスケジュール
        - アニメーションが実行中で、描画開始時刻が設定されていれば、時間表示を更新し、次の更新をスケジュールする
        """
        if self._animation_state.is_running and self._draw_start_time is not None:
            minutes, seconds, milliseconds = self._calculate_elapsed_time()
            self._update_label_text(f"描画中{'.' * self._animation_state.dots}")
            self._schedule_time_update()

    def _cancel_time_update(self) -> None:
        """時間更新タイマーをキャンセル
        - 時間更新タイマーが設定されていれば、キャンセルする
        """
        if self._status_timer_id:
            self.logger.log(LogLevel.DEBUG, "タイマーキャンセル")
            self.root.after_cancel(self._status_timer_id)
            self._status_timer_id = None

    def stop_animation(self, final_message: str = "完了") -> None:
        """アニメーションを停止し、最終メッセージを表示

        - アニメーションを停止
        - スレッドの終了を待機
        - 時間更新をキャンセル
        - 最終メッセージを表示
        - 状態をリセット

        Args:
            final_message (str, optional): 最終メッセージ. Defaults to "完了"
        """
        if self._animation_state.is_running:
            self._animation_state.stop()
            self._wait_for_thread()
            self._cancel_time_update()
            self._show_final_message(final_message)
            self._reset_state()
            self.logger.log(LogLevel.SUCCESS, "ステータスアニメーション停止成功")

    def _wait_for_thread(self) -> None:
        """アニメーションスレッドの終了を待機
        - アニメーションスレッドが実行中であれば、終了を待機する
        - タイムアウトしても終了しない場合は、警告ログを出力する
        """
        if self._animation_state.thread and self._animation_state.thread.is_alive():
            self.logger.log(LogLevel.DEBUG, "ステータスアニメーションスレッドの終了を待機...")
            self._animation_state.thread.join(timeout=0.2)
            if self._animation_state.thread.is_alive():
                self.logger.log(LogLevel.WARNING, "ステータスアニメーションスレッドが終了不可 (タイムアウト)")
            else:
                self.logger.log(LogLevel.SUCCESS, "ステータスアニメーションスレッド停止成功")

    def _show_final_message(self, message: str) -> None:
        """最終メッセージを表示
        - 描画開始時刻が設定されていれば、経過時間を含めたメッセージを表示する

        Args:
            message (str): 表示するメッセージ
        """
        if self._draw_start_time is not None:
            minutes, seconds, milliseconds = self._calculate_elapsed_time()
            time_str = self._format_time(minutes, seconds, milliseconds)
            self.root.after(0, lambda: self.status_label.config(text=time_str + message))

    def _reset_state(self) -> None:
        """状態をリセット
        - アニメーション状態と描画開始時刻をリセットする
        """
        self._animation_state.reset()
        self._draw_start_time = None

    def set_text(self, text: str) -> None:
        """ステータスバーに任意のテキストを設定
        - アニメーション実行中であれば停止し、指定されたテキストを表示する

        Args:
            text (str): 表示するテキスト
        """
        if self._animation_state.is_running:
            self.stop_animation(final_message="")
        self.root.after(0, lambda: self.status_label.config(text=text))

class AnimationState:
    """アニメーションの状態を管理するクラス
    Attributes:
        thread: アニメーションを実行するスレッド
        is_running: アニメーションが実行中かどうかを示すフラグ
        dots: アニメーションのドット数
        max_dots: アニメーションの最大ドット数
    """
    def __init__(self):
        """AnimationState クラスのコンストラクタ（親: MainWindow）
        - アニメーションの状態を初期化する
        """
        self.thread: Optional[threading.Thread] = None
        self.is_running: bool = False
        self.dots: int = 0
        self.max_dots: int = 10

    def start(self) -> None:
        """アニメーションを開始
        - アニメーション実行中フラグをTrueにし、ドット数をリセットする
        """
        self.is_running = True
        self.dots = 0

    def stop(self) -> None:
        """アニメーションを停止
        - アニメーション実行中フラグをFalseにする
        """
        self.is_running = False

    def reset(self) -> None:
        """状態をリセット
        - アニメーションの状態を初期状態に戻す
        """
        self.thread = None
        self.is_running = False
        self.dots = 0
