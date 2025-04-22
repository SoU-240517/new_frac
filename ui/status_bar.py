import tkinter as tk
from tkinter import ttk
import threading
import time
from typing import Optional
from .zoom_function.debug_logger import DebugLogger
from .zoom_function.enums import LogLevel

class StatusBarManager:
    """
    ステータスバーの表示とアニメーションを管理するクラス
    - 役割:
        - ステータスバーの表示とアニメーションを管理
    """
    _TIME_FORMAT = "[{:>3}分 {:>2}秒] "  # 時間表示のフォーマット
    _ANIMATION_INTERVAL = 0.1  # アニメーションの間隔（秒）
    _TIME_UPDATE_INTERVAL = 1000  # 時間更新の間隔（ミリ秒）

    def __init__(self, root: tk.Tk, status_frame: ttk.Frame, logger: DebugLogger):
        """StatusBarManager のコンストラクタ

        Args:
            root (tkinter.Tk): Tkinter ルートウィンドウ
            status_frame (ttk.Frame): ステータスバーを配置するフレーム
            logger (DebugLogger): ログ出力用の DebugLogger インスタンス
        """
        self.root = root
        self.status_frame = status_frame
        self.logger = logger

        self._draw_start_time: Optional[float] = None
        self._status_timer_id: Optional[str] = None

        self.status_label = ttk.Label(
            self.status_frame,
            text=self._format_time(0, 0) + "準備中...",
            width=25
        )
        self.status_label.pack(side=tk.LEFT, padx=5, pady=2)

        self._animation_state = AnimationState()

    def start_animation(self) -> None:
        """ステータスバーの描画中アニメーションを開始"""
        if self._animation_state.is_running:
            self.logger.log(LogLevel.ERROR, "アニメーションは既に実行中")
            return

        self._animation_state.start()
        self._draw_start_time = time.perf_counter()
        self._schedule_time_update()
        self._start_animation_thread()

    def _start_animation_thread(self) -> None:
        """アニメーション用スレッドを開始"""
        try:
            self.logger.log(LogLevel.DEBUG, "ステータスアニメーションスレッドを開始")
            self._animation_state.thread = threading.Thread(
                target=self._run_animation,
                daemon=True
            )
            self._animation_state.thread.start()
        except Exception as e:
            self.logger.log(LogLevel.ERROR, f"アニメーションスレッドの開始失敗: {e}")
            self._animation_state.stop()

    def _run_animation(self) -> None:
        """アニメーションスレッドのメインループ"""
        while self._animation_state.is_running:
            self._animation_state.dots = (self._animation_state.dots + 1) % (self._animation_state.max_dots + 1)
            self._update_label_text(f"描画中{'.' * self._animation_state.dots}")
            time.sleep(self._ANIMATION_INTERVAL)

    def _update_label_text(self, animation_text: str) -> None:
        """ステータスラベルのテキストを更新"""
        if self._draw_start_time is not None:
            minutes, seconds = self._calculate_elapsed_time()
            time_str = self._format_time(minutes, seconds)
            self.status_label.config(text=time_str + animation_text)
        else:
            self.status_label.config(text=self._format_time(0, 0) + animation_text)

    def _calculate_elapsed_time(self) -> tuple[int, int]:
        """経過時間を分と秒に変換"""
        elapsed_time = time.perf_counter() - self._draw_start_time
        minutes = int(elapsed_time // 60)
        seconds = int(elapsed_time % 60)
        return minutes, seconds

    def _format_time(self, minutes: int, seconds: int) -> str:
        """時間表示をフォーマット"""
        return self._TIME_FORMAT.format(minutes, seconds)

    def _schedule_time_update(self) -> None:
        """時間更新をスケジュール"""
        if self._animation_state.is_running:
            self._status_timer_id = self.root.after(
                self._TIME_UPDATE_INTERVAL,
                self._update_time
            )
        else:
            self._cancel_time_update()

    def _update_time(self) -> None:
        """時間表示を更新し、次の更新をスケジュール"""
        if self._animation_state.is_running and self._draw_start_time is not None:
            minutes, seconds = self._calculate_elapsed_time()
            self._update_label_text(f"描画中{'.' * self._animation_state.dots}")
            self._schedule_time_update()

    def _cancel_time_update(self) -> None:
        """時間更新タイマーをキャンセル"""
        if self._status_timer_id:
            self.root.after_cancel(self._status_timer_id)
            self._status_timer_id = None

    def stop_animation(self, final_message: str = "完了") -> None:
        """アニメーションを停止し、最終メッセージを表示"""
        if self._animation_state.is_running:
            self.logger.log(LogLevel.DEBUG, "ステータスアニメーション停止開始")
            self._animation_state.stop()
            self._wait_for_thread()
            self._cancel_time_update()
            self._show_final_message(final_message)
            self._reset_state()
            self.logger.log(LogLevel.SUCCESS, "ステータスアニメーション停止処理完了")

    def _wait_for_thread(self) -> None:
        """アニメーションスレッドの終了を待機"""
        if self._animation_state.thread and self._animation_state.thread.is_alive():
            self.logger.log(LogLevel.DEBUG, "アニメーションスレッドの終了を待機...")
            self._animation_state.thread.join(timeout=0.2)
            if self._animation_state.thread.is_alive():
                self.logger.log(LogLevel.DEBUG, "アニメーションスレッドが終了不可 (タイムアウト)")
            else:
                self.logger.log(LogLevel.SUCCESS, "アニメーションスレッド停止完了")

    def _show_final_message(self, message: str) -> None:
        """最終メッセージを表示"""
        if self._draw_start_time is not None:
            minutes, seconds = self._calculate_elapsed_time()
            time_str = self._format_time(minutes, seconds)
            self.root.after(0, lambda: self.status_label.config(text=time_str + message))

    def _reset_state(self) -> None:
        """状態をリセット"""
        self._animation_state.reset()
        self._draw_start_time = None

    def set_text(self, text: str) -> None:
        """ステータスバーに任意のテキストを設定"""
        if self._animation_state.is_running:
            self.stop_animation(final_message="")
        self.root.after(0, lambda: self.status_label.config(text=text))

class AnimationState:
    """アニメーションの状態を管理するクラス"""
    def __init__(self):
        self.thread: Optional[threading.Thread] = None
        self.is_running: bool = False
        self.dots: int = 0
        self.max_dots: int = 10

    def start(self) -> None:
        """アニメーションを開始"""
        self.is_running = True
        self.dots = 0

    def stop(self) -> None:
        """アニメーションを停止"""
        self.is_running = False

    def reset(self) -> None:
        """状態をリセット"""
        self.thread = None
        self.is_running = False
        self.dots = 0
