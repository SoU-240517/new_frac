import tkinter as tk
from tkinter import ttk
import threading
import time
from .zoom_function.debug_logger import DebugLogger
from .zoom_function.enums import LogLevel

class StatusBarManager:
    """
    ステータスバーの表示とアニメーションを管理するクラス

    Args:
        root (tkinter.Tk): Tkinter ルートウィンドウ
        status_frame (ttk.Frame): ステータスバーを表示するフレーム
        logger (DebugLogger): ログ出力用の DebugLogger インスタンス
    """
    def __init__(self, root: tk.Tk, status_frame: ttk.Frame, logger: DebugLogger):
        self.root = root # ステータスバーの表示元のルートウィンドウ
        self.status_frame = status_frame # ステータスバーを表示するフレーム
        self.logger = logger

        # 時間計測と表示のための変数
        self._draw_start_time: float | None = None # 描画開始時刻記録用 (floatまたはNone型)
        self._status_timer_id: str | None = None # root.afterでスケジュールされたタイマーのID (文字列またはNone型)
        # 時間表示のフォーマット文字列
        # 幅を固定するために使用（例: [ 100分 59秒] の幅）
        self._time_format = "[{:>3}分 {:>2}秒] "

        # ステータスバーのラベルウィジェットを作成
        # 時間表示分の幅を確保するために width オプションを指定
        self.status_label = ttk.Label(
            self.status_frame,
            text=self._time_format.format(0, 0) + "準備中...", # 作成
            width=25) # ある程度の幅（例: [ 999分 59秒] 描画中... が収まる程度）を確保
        self.status_label.pack(side=tk.LEFT, padx=5, pady=2) # 配置

        # ステータスバーの文字アニメーション用変数
        self.animation_thread: threading.Thread | None = None # アニメーション用スレッド (ThreadオブジェクトまたはNone型)
        self.animation_running: bool = False # アニメーション実行中確認フラグ (真偽値)
        self.animation_dots: int = 0 # ドットの数 (整数)
        self.animation_max_dots: int = 10 # ドットの最大数 (整数)

    def start_animation(self):
        """ステータスバーの描画中アニメーションを開始"""
        if self.animation_running: # 既にアニメーションが実行中の場合は何もしない
            self.logger.log(LogLevel.ERROR, "アニメーションは既に実行中")
            return

        self.logger.log(LogLevel.DEBUG, "ステータスアニメーション開始")
        self.animation_running = True
        self.animation_dots = 0

        # アニメーション用のスレッドを作成
        # スレッドのターゲットとしてインスタンスメソッドを指定
        self.animation_thread = threading.Thread(
            target=self._animation_thread_task,
            daemon=True) # プログラム終了時にスレッドも一緒に終了

        # 時間計測を開始
        self._draw_start_time = time.perf_counter() # 描画開始時刻を記録

        # 時間表示の更新をスケジュール
        self._schedule_time_update()

        # スレッドを開始
        try:
            self.animation_thread.start()
            self.logger.log(LogLevel.SUCCESS, "ステータスアニメーションスレッドを開始")
        except Exception as e:
            # スレッド開始に失敗した場合のエラー処理
            self.logger.log(LogLevel.ERROR, f"アニメーションスレッドの開始失敗: {e}")
            self.animation_running = False # スレッド開始に失敗したらフラグを戻す

    def _animation_thread_task(self):
        """ステータスバーのアニメーションを更新するスレッドの処理"""
        self.logger.log(LogLevel.DEBUG, "アニメーションスレッド タスク開始")
        while self.animation_running:
            self.animation_dots = (self.animation_dots + 1) % (self.animation_max_dots + 1)
            animation_text = f"描画中{'.' * self.animation_dots}"
            # TkinterのLabel 更新は必ずメインスレッドで行う必要があるため、root.afterを使用
            # root.after(0, ...) は、可能な限り早くメインスレッドで指定された関数を実行するように要求する
            # ラムダ式を使って、現在の animation_text の値を引数として _update_label_text に渡す
            self.root.after(0, lambda t=animation_text: self._update_label_text(t))
            # 一定時間待機してアニメーションの間隔を調整 (0.1秒)
            time.sleep(0.1)
        self.logger.log(LogLevel.DEBUG, "アニメーションスレッド タスク終了")

    def _update_label_text(self, animation_text: str):
        """
        ステータスラベルのテキストを更新（時間表示とアニメーションを組み合わせる）

        Args:
            animation_text (str): アニメーション部分のテキスト（例: "描画中..."）
        """
        if self._draw_start_time is not None:
            elapsed_time = time.perf_counter() - self._draw_start_time # 経過時間を計算
            # 経過時間を分と秒に変換
            minutes = int(elapsed_time // 60) # 60で割った商（分）
            seconds = int(elapsed_time % 60) # 60で割った余り（秒）
            # 時間表示の文字列を作成 (フォーマット済み)
            time_str = self._time_format.format(minutes, seconds)
            # 時間表示とアニメーションテキストを組み合わせてラベルを更新
            self.status_label.config(text=time_str + animation_text)
        else:
            # 描画開始前または終了後の場合、時間部分は0で表示し、アニメーションテキストのみ表示
            self.status_label.config(text=self._time_format.format(0, 0) + animation_text)

    def _schedule_time_update(self):
        """ステータスバーの時間表示更新をスケジュール"""
        if self.animation_running: # アニメーションが実行中の間のみスケジュールを継続
            # 1000ミリ秒（1秒）後に _update_time メソッドを実行するようにスケジュール
            # スケジュールされたタイマーのIDを記録しておくと、後でキャンセル可能
            self._status_timer_id = self.root.after(1000, self._update_time)
#           self.logger.log(LogLevel.DEBUG, "時間更新タイマーをスケジュール")
        else:
            # アニメーションが停止したら、実行中のタイマーがあればキャンセルする
            if self._status_timer_id:
                self.root.after_cancel(self._status_timer_id)
                self._status_timer_id = None # タイマーIDをクリア
#               self.logger.log(LogLevel.DEBUG, "時間更新タイマーを停止 (スケジュール停止)")

    def _update_time(self):
        """ステータスバーの時間表示を更新し、次の更新をスケジュール"""
        # アニメーションが実行中で、描画開始時刻が記録されている場合のみ処理を実行
        if self.animation_running and self._draw_start_time is not None:
            # 経過時間を計算
            elapsed_time = time.perf_counter() - self._draw_start_time
            minutes = int(elapsed_time // 60)
            seconds = int(elapsed_time % 60)
            # 時間表示と現在のドット数に基づいたアニメーションテキストを組み合わせてラベルを更新
            self._update_label_text(f"描画中{'.' * self.animation_dots}")
            # 次の1秒後の更新をスケジュール
            self._schedule_time_update()
        # else: アニメーション停止時や開始前は _schedule_time_update() でタイマーが停止される

    def stop_animation(self, final_message: str = "完了"):
        """
        ステータスバーの描画中アニメーションを停止し、最終メッセージを表示

        Args:
            final_message (str): アニメーション停止後に表示する最終メッセージ
        """
        if self.animation_running: # アニメーションが実行中の場合のみ停止処理を実行
            self.logger.log(LogLevel.DEBUG, "ステータスアニメーション停止開始")
            self.animation_running = False # アニメーション実行中フラグをFalseに設定

            # アニメーションスレッドが終了するのを待つ (短い処理なのですぐに終わるはず)
            if self.animation_thread and self.animation_thread.is_alive():
                self.logger.log(LogLevel.DEBUG, "アニメーションスレッドの終了を待機...")
                # スレッドが終了するのを待つためのタイムアウト付きjoin
                self.animation_thread.join(timeout=0.2) # タイムアウト値を設定
                if self.animation_thread.is_alive():
                    # タイムアウトしても警告は出す
                    self.logger.log(LogLevel.DEBUG, "ステータスアニメーションスレッドが終了不可 (タイムアウト)")
                else:
                    self.logger.log(LogLevel.SUCCESS, "ステータスアニメーションスレッド停止完了")

            # 時間更新タイマーをキャンセル
            if self._status_timer_id:
                self.root.after_cancel(self._status_timer_id)
                self._status_timer_id = None # タイマーIDをクリア
#               self.logger.log(LogLevel.DEBUG, "時間更新タイマーを停止 (stop_animation)")

            self.animation_thread = None # スレッド参照をクリア

            # 最終的な経過時間を計算し、ステータスバーに表示
            final_elapsed_time = 0.0
            if self._draw_start_time is not None:
                 final_elapsed_time = time.perf_counter() - self._draw_start_time

            minutes = int(final_elapsed_time // 60)
            seconds = int(final_elapsed_time % 60)
            final_time_str = self._time_format.format(minutes, seconds)

            # メインスレッドで最終メッセージを更新
            self.root.after(0, lambda: self.status_label.config(text=final_time_str + final_message))

            self._draw_start_time = None # 描画開始時刻をリセット
            self.logger.log(LogLevel.SUCCESS, "ステータスアニメーション停止処理完了")
        # else: アニメーションが実行されていなければ停止処理は不要
#           self.logger.log(LogLevel.DEBUG, "アニメーションは実行されていませんでした (停止スキップ)")

    def set_text(self, text: str):
        """
        ステータスバーに任意のテキストを設定する
        - 主に描画開始前やエラー表示などに使う
        """
        # アニメーションが実行中の場合は、まず停止する
        if self.animation_running:
             # アニメーションは停止し、最終メッセージは空文字列にする
             self.stop_animation(final_message="")

        # 時間表示部分を含めてテキストを設定
        # start_animation が呼ばれていない場合、_draw_start_time は None なので時間は 0 になる
        # ただし、set_text はアニメーションとは独立してテキストを設定するので、
        # 描画開始時刻に関わらず指定されたテキストを表示するようにします。
        # 例: status_bar_manager.set_text(status_bar_manager._time_format.format(0, 0) + "準備中...")
        self.root.after(0, lambda: self.status_label.config(text=text))
