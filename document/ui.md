==============================
# MODULE_INFO:
main_window.py

## MODULE_PURPOSE
フラクタル描画アプリケーションのメインウィンドウと、フラクタル描画に必要なUIコンポーネントの初期化、配置、およびフラクタル描画処理を管理するモジュール

## CLASS_DEFINITION:
名前: MainWindow
役割: Tkinterウィンドウの作成、フラクタル描画用キャンバス、パラメータ設定パネル、ステータスバーなどのUIコンポーネントの初期化と配置、およびフラクタル描画処理、ズーム機能、パラメータ変更処理などの制御を行うクラス
親クラス: なし

## DEPENDENCIES
tkinter (tk, ttk): UIフレームワーク
numpy (np): 数値計算
threading: 非同期処理
typing: 型ヒント
json: 設定ファイル読み込み
os: ファイルパス操作
ui.canvas.FractalCanvas: フラクタル描画キャンバス
ui.parameter_panel.ParameterPanel: パラメータ設定パネル
fractal.render.render_fractal: フラクタル生成関数
.status_bar.StatusBarManager: ステータスバー管理
.zoom_function.debug_logger.DebugLogger: ログ管理
.zoom_function.enums.LogLevel: ログレベル定義

## CLASS_ATTRIBUTES
self.logger: DebugLogger - デバッグログ管理インスタンス
self.root: tk.Tk - Tkinterルートウィンドウ (アプリケーションのメインウィンドウ)
self.config (dict): config.json から読み込んだ設定データ
self.ui_settings (dict): config['ui_settings'] のショートカット
self.canvas_frame: ttk.Frame - キャンバス配置フレーム (フラクタル描画領域を配置)
self.parameter_frame: ttk.Frame - パラメータパネル配置フレーム (パラメータ設定UIを配置)
self.fractal_canvas: FractalCanvas - フラクタルを描画するキャンバス
self.parameter_panel: ParameterPanel - パラクトルパラル (フラクタルのパラメータを設定)
self.status_bar_manager: StatusBarManager - ステータスバー管理 (アプリケーションの状態を表示)
self.zoom_params: dict - ズーム操作パラメータ {center_x, center_y, width, height, rotation} (現在の表示領域)
self.prev_zoom_params: dict | None - 前回のズームパラメータ（キャンセル用、初期値はNone）
self.is_drawing: bool - 描画中フラグ (フラクタル描画処理が実行中かどうかを示す)
self.draw_thread: Thread | None - フラクタル描画スレッド (初期値はNone)

## METHOD_SIGNATURES
def __init__(self, root: tk.Tk, logger: DebugLogger) -> None
機能: コンストラクタ。ルートウィンドウとロガーを受け取り、初期設定を行う（設定ファイルの読み込み、UIコンポーネントのセットアップ、ズームパラメータの初期化、初期描画開始）

def load_config(logger: DebugLogger, config_path="config.json") -> dict
機能: 設定ファイル (JSON) を読み込む。ファイルが見つからない場合やエラーが発生した場合は空の辞書を返す

def _setup_root_window(self) -> None
機能: ルートウィンドウの基本設定を行う（タイトル、初期サイズ設定）

def _setup_components(self) -> None
機能: UIコンポーネント（ステータスバー、パラメータパネル、キャンバスフレーム）の初期化を行う

def _setup_status_bar(self) -> None
機能: ステータスバーを初期化し、ルートウィンドウの下部に配置する

def _setup_zoom_params(self) -> None
機能: ズーム操作に関するパラメータを初期化する（初期ズームパラメータを設定ファイルから読み込む）

def _setup_parameter_frame(self) -> None
機能: パラメータパネルを配置するフレームを初期化し、ルートウィンドウの右側に配置する

def _setup_canvas_frame(self) -> None
機能: フラクタル描画領域を配置するキャンバスフレームを初期化し、ルートウィンドウの左側に配置する

def _start_initial_drawing(self) -> None
機能: アプリケーション起動時の初期描画を開始する（ステータスバー表示、別スレッドで描画開始）

def update_fractal(self) -> None
機能: フラクタルを再描画する。描画中の場合は新しい描画要求を無視する

def _update_fractal_thread(self) -> None
機能: フラクタル更新処理を別スレッドで実行する（パラメータ取得、フラクタル生成、キャンバス更新、ステータスバー更新）

def _merge_zoom_and_panel_params(self, panel_params: dict) -> Dict[str, Any]
機能: ズームパラメータとパラメータパネルのパラメータを結合する

def on_zoom_confirm(self, x: float, y: float, w: float, h: float, angle: float) -> None
機能: ズーム操作確定時のコールバック関数。新しいズームパラメータを計算し、フラクタルを再描画する。ズームファクターに応じて最大イテレーション回数を調整する。

def _calculate_max_iterations(self, current_max_iter: int, zoom_factor: float) -> int
機能: ズームファクターに基づいてフラクタル計算の最大イテレーション回数を計算する。

def on_zoom_cancel(self) -> None
機能: ズーム操作キャンセル時のコールバック関数。直前のズームパラメータに戻してフラクタルを再描画する。

def reset_zoom(self) -> None
機能: 操作パネルの「描画リセット」ボタン押下時の処理。ズームパラメータを初期状態に戻し、フラクタルを再描画する。

def _on_canvas_frame_configure(self, event) -> None
機能: キャンバスフレームのリサイズ時に、内部の Matplotlib Figure のサイズを調整し、16:9 の縦横比を維持する。

## CORE_EXECUTION_FLOW
__init__ → load_config → _setup_root_window → _setup_components (_setup_status_bar, _setup_parameter_frame, _setup_canvas_frame) → _setup_zoom_params → _start_initial_drawing → _update_fractal_thread → render_fractal → FractalCanvas.update_canvas
ユーザーによるパラメータ変更やズーム操作 → update_fractal または on_zoom_confirm または reset_zoom → _update_fractal_thread → ...
イベントループによる各種メソッド呼び出し
_on_canvas_frame_configure によるキャンバスフレームのリサイズ処理

## KEY_LOGIC_PATTERNS
非同期処理: メインスレッドとは別にフラクタル描画 (_update_fractal_thread)
パラメータ合成: ズームパラメータとパネルパラメータの結合 (_merge_zoom_and_panel_params)
エラーハンドリング: try-except構造でエラーをログ出力
アスペクト比維持: `_on_canvas_frame_configure` メソッドで16:9アスペクト比を維持
コールバック関数: ズーム操作などのイベント処理 (on_zoom_confirm, on_zoom_cancel)
UIスレッドと描画スレッドの分離
設定ファイルからの読み込み (load_config)

## CRITICAL_BEHAVIORS
スレッド管理: is_drawingフラグによる描画状態管理
状態保存: prev_zoom_paramsによるズーム状態保存
ダイナミックパラメータ調整: ズーム率に応じた反復回数の変更 (_calculate_max_iterations)
アスペクト比維持: `_on_canvas_frame_configure` メソッドで、キャンバスフレームのリサイズ時に描画領域が常に16:9の縦横比を保つように調整する
パラメータ取得エラー時の描画中断処理 (_update_fractal_thread)


==============================
# MODULE_INFO:
canvas.py

## MODULE_PURPOSE
フラクタル画像の表示と更新、ズーム機能の制御、ユーザーインターフェースの描画を行うクラスを定義するモジュール

## CLASS_DEFINITION:
名前: FractalCanvas
役割:
- MatplotlibのFigureとAxesを管理し、フラクタル画像を描画・更新する。
- ズーム選択機能（ZoomSelector）を初期化・管理し、ズーム操作のコールバックを処理する。
- キャンバスの背景色を設定する。
親クラス: なし

## DEPENDENCIES
numpy (np): 数値計算
tkinter (tk): UIフレームワーク
matplotlib.backends.backend_tkagg.FigureCanvasTkAgg: MatplotlibのFigureをTkinterキャンバスに埋め込む
matplotlib.figure.Figure: MatplotlibのFigure
typing: 型ヒント (Callable, Optional, Dict, Tuple)
ui.zoom_function.debug_logger.DebugLogger: デバッグログ管理
ui.zoom_function.enums.LogLevel: ログレベル定義
ui.zoom_function.zoom_selector.ZoomSelector: ズーム選択機能 (遅延インポート)

## CLASS_ATTRIBUTES
self.fig: matplotlib.figure.Figure - MatplotlibのFigureオブジェクト
self.ax: matplotlib.axes._subplots.AxesSubplot - MatplotlibのAxesオブジェクト
self.canvas: matplotlib.backends.backend_tkagg.FigureCanvasTkAgg - Tkinterに埋め込まれたMatplotlibキャンバスウィジェット
self.zoom_confirm_callback: Callable - ズーム確定時に呼び出すコールバック関数
self.zoom_cancel_callback: Callable - ズームキャンセル時に呼び出すコールバック関数
self.logger: DebugLogger - デバッグログを管理するLoggerインスタンス
self.parent: tk.Tk or ttk.Frame - Tkinterの親ウィジェット
self.config: Dict[str, float] - ZoomSelectorに渡すための設定データ
self.facecolor: str - キャンバスの背景色

## METHOD_SIGNATURES
def __init__(self, master: tk.Tk, width: int, height: int, logger: DebugLogger, zoom_confirm_callback: Callable, zoom_cancel_callback: Callable, config: Dict[str, float]) -> None
機能: コンストラクタ。FigureとAxesの初期化、ズーム機能の設定と初期化（ZoomSelectorインスタンス生成）、背景色の設定を行う。設定データを受け取る。

def _setup_figure(self, width: int, height: int) -> None
機能: MatplotlibのFigureとAxesを設定し、FigureCanvasTkAggを使用してTkinterキャンバスに埋め込む。初期サイズと背景色を設定する。

def set_zoom_callback(self, zoom_confirm_callback: Callable, zoom_cancel_callback: Callable) -> None
機能: ズーム確定・キャンセル時の外部コールバック関数を設定する。

def _setup_zoom(self) -> None
機能: ZoomSelectorのインスタンスを作成し、ズームイベントのコールバック（zoom_confirmed, zoom_cancelled）を設定する。

def _set_black_background(self) -> None
機能: AxesとFigureの背景色を黒に設定し、キャンバスを再描画する。

def zoom_confirmed(self, x: float, y: float, w: float, h: float, angle: float) -> None
機能: ZoomSelectorからのズーム確定通知を受け取り、設定されているズーム確定コールバック関数 (`self.zoom_confirm_callback`) を引数付きで呼び出す。

def zoom_cancelled(self) -> None
機能: ZoomSelectorからのズームキャンセル通知を受け取り、設定されているズームキャンセルコールバック関数 (`self.zoom_cancel_callback`) を呼び出す。

def update_canvas(self, fractal_image: np.ndarray, params: Dict[str, float]) -> None
機能: 新しいフラクタル画像と描画パラメータを受け取り、Axesをクリアして画像を再描画する。描画範囲はパラメータと16:9のアスペクト比に基づいて計算される。

def reset_zoom_selector(self) -> None
機能: 管理しているZoomSelectorインスタンスの `reset` メソッドを呼び出し、ズーム選択状態を初期状態に戻す。

## CORE_EXECUTION_FLOW
__init__ (config受け取り含む) → _setup_figure, set_zoom_callback, _setup_zoom (ZoomSelector生成), _set_black_background
外部からの描画更新要求 (例: MainWindowからの update_canvas 呼び出し) → Axesクリア・設定 → 描画範囲計算 → imshow (画像描画) → canvas.draw()
ZoomSelectorからのイベント通知 (zoom_confirmed, zoom_cancelled) → 対応するコールバック関数呼び出し
外部からのズームセレクタのリセット要求 (例: MainWindowからの reset_zoom_selector 呼び出し) → zoom_selector.reset() 呼び出し

## KEY_LOGIC_PATTERNS
- MatplotlibのTkinterへの埋め込み: FigureCanvasTkAggによるMatplotlib描画領域の統合
- コールバック関数: ズーム確定・キャンセル時の外部処理との連携
- ズーム機能の委譲: ZoomSelectorクラスへのズーム操作管理の委譲
- 画像描画と更新: Axesへの画像の描画と描画範囲の設定
- アスペクト比の維持: update_canvas内での描画範囲計算時のアスペクト比維持
- 設定データの受け渡し: コンストラクタで受け取ったconfigをZoomSelectorに渡す

## CRITICAL_BEHAVIORS
- フラクタル画像の正確かつ効率的な描画と更新
- ズーム確定・キャンセル時のコールバックの正確な呼び出し
- ズーム選択機能（ZoomSelector）の適切な初期化と連携
- 描画範囲計算におけるアスペクト比の正確な維持
- Matplotlibオブジェクト（Figure, Axes, Canvas）の適切な管理と設定


==============================
# MODULE_INFO:
parameter_panel.py

## MODULE_PURPOSE
フラクタル生成用のパラメータを設定するパネルを定義するモジュール

## CLASS_DEFINITION:
名前: ParameterPanel
役割:
- フラクタル生成に必要なパラメータを設定するためのUI要素を提供する
- パラメータの取得と管理
- 描画更新およびリセットのコールバック関数を呼び出す
親クラス: なし

## DEPENDENCIES
matplotlib.pyplot (plt): カラーバー生成
numpy (np): 数値計算
tkinter (tk, ttk): UIフレームワーク
PIL.Image, PIL.ImageTk: 画像処理
typing: 型ヒント
ui.zoom_function.debug_logger.DebugLogger: デバッグログ管理
ui.zoom_function.enums.LogLevel: ログレベル定義

## CLASS_ATTRIBUTES
self.parent: ttk.Frame - 親ウィジェット
self.update_callback: Callable - 描画更新コールバック関数
self.reset_callback: Callable - 描画リセットコールバック関数
self.logger: DebugLogger - デバッグロガーインスタンス
self.render_mode: str - 描画モード ("quick" or "full", デフォルトは "quick")
self.fractal_type_var: tk.StringVar - フラクタルタイプの選択
self.formula_var: tk.StringVar - 数式表示
self.max_iter_var: tk.StringVar - 最大反復回数
self.z_real_var: tk.StringVar - Z (実部)
self.z_imag_var: tk.StringVar - Z (虚部)
self.c_real_var: tk.StringVar - C (実部)
self.c_imag_var: tk.StringVar - C (虚部)
self.diverge_algo_var: tk.StringVar - 発散部着色アルゴリズム
self.diverge_colormap_var: tk.StringVar - 発散部カラーマップ
self.non_diverge_algo_var: tk.StringVar - 非発散部着色アルゴリズム
self.non_diverge_colormap_var: tk.StringVar - 非発散部カラーマップ
self.colormaps: list - カラーマップリスト
self.diverge_algorithms: list - 発散部アルゴリズムリスト
self.non_diverge_algorithms: list - 非発散部アルゴリズムリスト
self.COLORBAR_WIDTH: int - カラーバー幅
self.COLORBAR_HEIGHT: int - カラーバー高さ
self.config: Dict[str, Any] - 設定データ

## METHOD_SIGNATURES
def __init__(self, parent, update_callback, reset_callback, logger: DebugLogger, config: Dict[str, Any]) -> None
機能: コンストラクタ。パネルのセットアップ、カラーバーの初期化を行う。設定データを受け取る。

def _setup_panel(self) -> None
機能: パネルのセットアップを行う。各セクションのセットアップ、パネルのレイアウト設定。

def _setup_fractal_type_section(self) -> None
機能: フラクタルタイプセクションのセットアップを行う。ラベルとコンボボックスの追加、イベントバインド、初期値を設定ファイルから読み込む。

def _setup_formula_section(self) -> None
機能: 数式表示セクションのセットアップを行う。数式表示ラベルの追加、数式の初期表示。

def _setup_parameter_section(self) -> None
機能: パラメータ表示セクションのセットアップを行う。各パラメータのラベルと入力欄の追加、イベントバインド、初期値を設定ファイルから読み込む。

def _setup_diverge_section(self) -> None
機能: 発散部セクションのセットアップを行う。各ウィジェットの追加と設定、イベントバインド、初期値とリストを設定ファイルから読み込む。カラーバー表示用ラベルも追加。

def _setup_non_diverge_section(self) -> None
機能: 非発散部セクションのセットアップを行う。各ウィジェットの追加と設定、イベントバインド、初期値とリストを設定ファイルから読み込む。カラーバー表示用ラベルも追加。

def _setup_buttons(self) -> None
機能: ボタンのセットアップを行う。描画ボタンと描画リセットボタンの追加、各ボタンのコールバック設定。

def _add_label(self, text: str, row: int, col: int, columnspan: int = 1, padx: int = 10, pady: int = 2) -> None
機能: ラベルを追加し、グリッドレイアウトに配置する。

def _add_entry(self, row: int, col: int, var: tk.StringVar, padx: int = 10, pady: int = 2) -> ttk.Entry
機能: エントリー（入力欄）を追加し、グリッドレイアウトに配置する。

def _add_combobox(self, row: int, col: int, var: tk.StringVar, values: list[str], width: Optional[int] = None, padx: int = 10, pady: int = 2) -> ttk.Combobox
機能: コンボボックス（選択リスト）を追加し、グリッドレイアウトに配置する。

def _add_button(self, text: str, row: int, col: int, colspan: int, command: Callable) -> ttk.Button
機能: ボタンを追加し、グリッドレイアウトに配置する。

def _common_callback(self, event=None) -> None
機能: 共通コールバック関数。パラメータ変更時に描画モードをクイックに設定し、描画更新コールバックを呼び出す。カラーバーと数式表示も更新する。

def _create_colorbar_image(self, cmap_name: str) -> ImageTk.PhotoImage
機能: 指定されたカラーマップ名でカラーバー画像を生成する。

def _update_colorbars(self, *args) -> None
機能: 発散部と非発散部のカラーバーを更新する。

def _show_formula_display(self) -> None
機能: 選択されたフラクタルタイプに応じて数式表示を更新する。

def _get_parameters(self) -> dict[str, Any] | None
機能: パネル上のウィジェットから現在のパラメータを取得し、辞書として返す。数値変換エラーが発生した場合は None を返す。最大反復回数が0以下の場合は補正を行う。

## CORE_EXECUTION_FLOW
__init__ → _setup_panel (_setup_fractal_type_section, _setup_formula_section, _setup_parameter_section, _setup_diverge_section, _setup_non_diverge_section, _setup_buttons) → _update_colorbars (初期表示)
ユーザー操作 (入力、コンボボックス選択、ボタンクリック) → _common_callback またはボタンの直接コールバック → _get_parameters → update_callback または reset_callback
_common_callback → _update_colorbars, _show_formula_display

## KEY_LOGIC_PATTERNS
UI構築: Tkinterウィジェットの配置と設定 (gridレイアウト)
コールバック: イベント駆動型のUI更新 (_common_callback, ボタンコールバック)
パラメータ管理: パラメータの取得と検証 (_get_parameters)
カラーバー表示: Matplotlibによるカラーバー生成とTkinterへの統合 (_create_colorbar_image, _update_colorbars)
設定ファイル: config.jsonからの初期値読み込みとリスト取得
描画モード管理: "quick" と "full" モードの切り替え

## CRITICAL_BEHAVIORS
パラメータ入力: 各ウィジェットからのパラメータ取得と検証
コールバック: パラメータ変更時の描画更新処理のトリガー
エラーハンドリング: パラメータ変換エラー発生時の対応 (_get_parameters で None を返す)
リソース管理: Matplotlibオブジェクト（カラーバー画像）の生成
状態管理: render_mode による描画モードの追跡


==============================
# MODULE_INFO:
status_bar.py

## MODULE_PURPOSE
ステータスバーの表示とアニメーションを管理するクラス

## CLASS_DEFINITION:
名前: StatusBarManager
役割: ステータスバーの表示とアニメーション、描画時間の計測と表示、アニメーション状態の管理を行うクラス
親クラス: なし

## DEPENDENCIES
tkinter (tk, ttk): UIフレームワーク
threading: 非同期処理
time: 時間計測
typing: 型ヒント
.zoom_function.debug_logger.DebugLogger: ログ管理
.zoom_function.enums.LogLevel: ログレベル定義

## CLASS_ATTRIBUTES
_TIME_FORMAT: str - 時間表示のフォーマット文字列
_ANIMATION_INTERVAL: float - アニメーションの間隔 (秒)
_TIME_UPDATE_INTERVAL: int - 時間更新の間隔 (ミリ秒)
root: tk.Tk - Tkinterのルートウィンドウ
status_frame: ttk.Frame - ステータスバーを配置するフレーム
logger: DebugLogger - デバッグログを管理するLogger
_draw_start_time: Optional[float] - 描画開始時刻
_status_timer_id: Optional[str] - 時間更新タイマーID
status_label: ttk.Label - ステータス表示用のラベル
_animation_state: AnimationState - アニメーション状態を管理するインスタンス

## METHOD_SIGNATURES
def __init__(self, root: tk.Tk, status_frame: ttk.Frame, logger: DebugLogger) -> None
機能: コンストラクタ。ステータスバーの初期化とアニメーション状態の設定を行う

def start_animation(self) -> None
機能: ステータスバーの描画中アニメーションを開始する

def _start_animation_thread(self) -> None
機能: アニメーション用スレッドを開始する

def _run_animation(self) -> None
機能: アニメーションスレッドのメインループ。アニメーション状態が続く限り、ドットアニメーションを更新し続ける

def _update_label_text(self, animation_text: str) -> None
機能: ステータスラベルのテキストを更新する

def _calculate_elapsed_time(self) -> tuple[int, int, int]
機能: 経過時間を分、秒、ミリ秒に変換する

def _format_time(self, minutes: int, seconds: int, milliseconds: int) -> str
機能: 時間表示をフォーマットする

def _schedule_time_update(self) -> None
機能: 時間更新をスケジュールする

def _update_time(self) -> None
機能: 時間表示を更新し、次の更新をスケジュールする

def _cancel_time_update(self) -> None
機能: 時間更新タイマーをキャンセルする

def stop_animation(self, final_message: str = "完了") -> None
機能: アニメーションを停止し、最終メッセージを表示する

def _wait_for_thread(self) -> None
機能: アニメーションスレッドの終了を待機する

def _show_final_message(self, message: str) -> None
機能: 最終メッセージを表示する

def _reset_state(self) -> None
機能: 状態をリセットする

def set_text(self, text: str) -> None
機能: ステータスバーに任意のテキストを設定する

## CLASS_DEFINITION:
名前: AnimationState
役割: アニメーションの状態を管理するクラス
親クラス: なし

## CLASS_ATTRIBUTES
thread: Optional[threading.Thread] - アニメーションを実行するスレッド
is_running: bool - アニメーションが実行中かどうかを示すフラグ
dots: int - アニメーションのドット数
max_dots: int - アニメーションの最大ドット数

## METHOD_SIGNATURES
def __init__(self) -> None
機能: コンストラクタ。アニメーションの状態を初期化する

def start(self) -> None
機能: アニメーションを開始する

def stop(self) -> None
機能: アニメーションを停止する

def reset(self) -> None
機能: 状態をリセットする

## CORE_EXECUTION_FLOW
ステータスバーの初期化 → アニメーション開始/停止 → 時間更新 → テキスト更新

## KEY_LOGIC_PATTERNS
時間管理: 経過時間の計測とフォーマット
非同期処理: アニメーションのスレッド実行
状態管理: アニメーションの状態遷移

## CRITICAL_BEHAVIORS
アニメーションの正確な時間管理
スレッドの安全な開始と停止
状態の適切なリセット
