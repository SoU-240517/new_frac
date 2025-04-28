==============================
# MODULE_INFO:
ui/main_window.py

## MODULE_PURPOSE
フラクタル描画アプリケーションのメインウィンドウと、フラクタク描画に必要なUIコンポーネントの初期化、配置、およびフラクタル描画処理を管理するモジュール

## CLASS_DEFINITION:
名前: MainWindow
役割: Tkinterウィンドウの作成、フラクタル描画用キャンバス、パラメータ設定パネル、ステータスバーなどのUIコンポーネントの初期化と配置、およびフラクタル描画処理、ズーム機能、パラメータ変更処理などの制御を行うクラス
親クラス: なし

## DEPENDENCIES
tkinter (tk, ttk): UIフレームワーク
numpy (np): 数値計算
threading: 非同期処理
typing: 型ヒント
ui.canvas.FractalCanvas: フラクタル描画キャンバス
ui.parameter_panel.ParameterPanel: パラメータ設定パネル
fractal.render.render_fractal: フラクタル生成関数
.status_bar.StatusBarManager: ステータスバー管理
.zoom_function.debug_logger.DebugLogger: ログ管理
.zoom_function.enums.LogLevel: ログレベル定義

## CLASS_ATTRIBUTES
self.logger: DebugLogger - デバッグログ管理インスタンス
self.root: tk.Tk - Tkinterルートウィンドウ (アプリケーションのメインウィンドウ)
self.canvas_frame: ttk.Frame - キャンバス配置フレーム (フラクタル描画領域を配置)
self.parameter_frame: ttk.Frame - パラメータパネル配置フレーム (パラメータ設定UIを配置)
self.fractal_canvas: FractalCanvas - フラクタルを描画するキャンバス
self.parameter_panel: ParameterPanel - パラメータ管理パネル (フラクタルのパラメータを設定)
self.status_bar_manager: StatusBarManager - ステータスバー管理 (アプリケーションの状態を表示)
self.zoom_params: dict - ズーム操作パラメータ {center_x, center_y, width, height, rotation} (現在の表示領域)
self.prev_zoom_params: dict - 前回のズームパラメータ（キャンセル用）
self.is_drawing: bool - 描画中フラグ (フラクタル描画処理が実行中かどうかを示す)
self.draw_thread: Thread - フラクタル描画スレッド

## METHOD_SIGNATURES
def __init__(self, root: tk.Tk, logger: DebugLogger) -> None
機能 コンストラクタ。ルートウィンドウとロガーを受け取り、初期設定を行う

def _setup_root_window(self) -> None
機能 ルートウィンドウの基本設定を行う

def _setup_components(self) -> None
機能 UIコンポーネントを初期化する

def _setup_status_bar(self) -> None
機能 ステータスバーを初期化し、配置する

def _setup_parameter_frame(self) -> None
機能 パラメータパネルを配置するフレームを初期化し、配置する

def _setup_canvas_frame(self) -> None
機能 フラクタル描画領域を配置するキャンバスフレームを初期化し、配置する

def _start_initial_drawing(self) -> None
機能 アプリケーション起動時の初期描画を開始する

def update_fractal(self) -> None
機能 フラクタルを再描画する

def _update_fractal_thread(self) -> None
機能 フラクタル更新処理を別スレッドで実行する

def _merge_zoom_and_panel_params(self, panel_params: dict) -> dict
機能 ズームパラメータとパラメータパネルのパラメータを結合する

def on_zoom_confirm(self, x: float, y: float, w: float, h: float, angle: float) -> None
機能 ズーム操作確定時のコールバック関数

def _calculate_max_iterations(self, current_max_iter: int, zoom_factor: float) -> int
機能 ズームファクターに基づいて最大イテレーション回数を計算する

def on_zoom_cancel(self) -> None
機能 ズーム操作キャンセル時のコールバック関数

def reset_zoom(self) -> None
機能 操作パネルの「描画リセット」ボタン押下時の処理

def _on_canvas_frame_configure(self, event) -> None
機能 キャンバスフレームのリサイズ時に、内部の Matplotlib Figure のサイズを調整し、16:9 の縦横比を維持する

## CORE_EXECUTION_FLOW
__init__ → 各種セットアップメソッド → _start_initial_drawing → ユーザーによるパラメータ変更やズーム操作 → update_fractal → _update_fractal_thread → render_fractal → キャンバス更新
イベントループによる各種メソッド呼び出し

## KEY_LOGIC_PATTERNS
非同期処理: メインスレッドとは別にフラクタル描画
パラメータ合成: ズームパラメータとパネルパラメータの結合
エラーハンドリング: try-except構造でエラーをログ出力
UI管理: 16:9アスペクト比維持設計
コールバック関数: ズーム操作などのイベント処理
UIスレッドと描画スレッドの分離

## CRITICAL_BEHAVIORS
スレッド管理: is_drawingフラグによる描画状態管理
状態保存: prev_zoom_paramsによるズーム状態保存
ダイナミックパラメータ調整: ズーム率に応じた反復回数の変更
アスペクト比維持: キャンバスフレームのリサイズ時に、描画領域が常に16:9の縦横比を保つように調整する


==============================
# MODULE_INFO:
ui/canvas.py

## MODULE_PURPOSE
フラクタル画像の表示と更新、ズーム機能の制御、ユーザーインターフェースの描画を行うクラスを定義するモジュール

## CLASS_DEFINITION:
名前: FractalCanvas
役割:
- フラクタル画像の表示と更新を管理
- ズーム機能の制御
- ユーザーインターフェースの描画
親クラス: なし

## DEPENDENCIES
numpy (np): 数値計算
tkinter (tk): UIフレームワーク
matplotlib.backends.backend_tkagg.FigureCanvasTkAgg: MatplotlibのFigureをTkinterキャンバスに埋め込む
matplotlib.figure.Figure: MatplotlibのFigure
typing: 型ヒント
ui.zoom_function.debug_logger.DebugLogger: デバッグログ管理
ui.zoom_function.enums.LogLevel: ログレベル定義
ui.zoom_function.zoom_selector.ZoomSelector: ズーム選択機能 (遅延インポート)

## CLASS_ATTRIBUTES
self.fig: matplotlib.figure.Figure - MatplotlibのFigure
self.ax: matplotlib.axes._subplots.AxesSubplot - MatplotlibのAxes
self.canvas: matplotlib.backends.backend_tkagg.FigureCanvasTkAgg - Tkinterのキャンバス
self.zoom_selector: ui.zoom_function.zoom_selector.ZoomSelector - ズーム選択機能を管理するZoomSelector
self.zoom_confirm_callback: Callable - ズーム確定時のコールバック関数
self.zoom_cancel_callback: Callable - ズームキャンセル時のコールバック関数
self.logger: ui.zoom_function.debug_logger.DebugLogger - デバッグログを管理するLogger
self.parent: tk.Tk - Tkinterの親ウィジェット

## METHOD_SIGNATURES
def __init__(self, master: tk.Tk, width: int, height: int,  logger: DebugLogger, zoom_confirm_callback: Callable, zoom_cancel_callback: Callable) -> None
機能 コンストラクタ。FigureとAxesの初期化、ズーム機能の設定、背景色の設定を行う

def _setup_figure(self, width: int, height: int) -> None
機能 MatplotlibのFigureとAxesの設定、Tkinterキャンバスの設定を行う

def set_zoom_callback(self, zoom_confirm_callback: Callable, zoom_cancel_callback: Callable) -> None
機能 ズーム確定・キャンセル時のコールバックを設定する

def _setup_zoom(self) -> None
機能 ズーム機能の設定と初期化を行う

def _set_black_background(self) -> None
機能 キャンバスの背景を黒に設定する

def zoom_confirmed(self, x: float, y: float, w: float, h: float, angle: float) -> None
機能 ズーム確定時の処理。ズーム選択範囲のパラメータを受け取り、コールバック関数を呼び出す

def zoom_cancelled(self) -> None
機能 ズームキャンセル時の処理。ズームキャンセル時にコールバック関数を呼び出す

def update_canvas(self, fractal_image: np.ndarray, params: Dict[str, float]) -> None
機能 フラクタル画像の更新を行う。新しいフラクタル画像を描画する

def reset_zoom_selector(self) -> None
機能 ズームセレクタのリセットを行う。ズーム選択状態を初期状態に戻す

## CORE_EXECUTION_FLOW
__init__ → _setup_figure, set_zoom_callback, _setup_zoom, _set_black_background
ユーザー操作（ズーム、更新） → zoom_confirmed, zoom_cancelled, update_canvas
必要に応じて reset_zoom_selector

## KEY_LOGIC_PATTERNS
- コールバック関数: ズーム確定・キャンセル時に外部の処理を呼び出す
- Matplotlibの埋め込み:  FigureCanvasTkAggを使用してMatplotlibのFigureをTkinterに統合
- 背景色の設定:  一貫したUIのためにキャンバスとFigureの背景色を黒に設定
- アスペクト比の維持:  フラクタル描画時に16:9のアスペクト比を維持

## CRITICAL_BEHAVIORS
- ズーム機能: 選択範囲に基づくフラクタル画像の再描画
- コールバック:  ズーム操作とアプリケーションロジックの分離
- キャンバス更新:  新しいフラクタル画像の描画とパラメータ反映
- リソース管理:  Matplotlibオブジェクトの適切な初期化と設定


==============================
# MODULE_INFO:
ui/parameter_panel.py

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
.zoom_function.debug_logger.DebugLogger: デバッグログ管理
.zoom_function.enums.LogLevel: ログレベル定義

## CLASS_ATTRIBUTES
self.parent: tk.Tk - 親ウィジェット
self.update_callback: Callable - 描画更新コールバック関数
self.reset_callback: Callable - 描画リセットコールバック関数
self.logger: DebugLogger - デバッグロガーインスタンス
self.render_mode: str - 描画モード ("quick" or "full")
self.fractal_type_var: tk.StringVar - フラクタルタイプの選択
self.formula_var: tk.StringVar - 数式表示
self.formula_label: ttk.Label - 数式表示ラベル
self.max_iter_var: tk.StringVar - 最大反復回数
self.z_real_var: tk.StringVar - Z (実部)
self.z_imag_var: tk.StringVar - Z (虚部)
self.c_real_var: tk.StringVar - C (実部)
self.c_imag_var: tk.StringVar - C (虚部)
self.diverge_algo_var: tk.StringVar - 発散部着色アルゴリズム
self.diverge_colorbar_label: tk.Label - 発散部カラーバー表示ラベル
self.diverge_colormap_var: tk.StringVar - 発散部カラーマップ
self.non_diverge_algo_var: tk.StringVar - 非発散部着色アルゴリズム
self.non_diverge_colorbar_label: tk.Label - 非発散部カラーバー表示ラベル
self.non_diverge_colormap_var: tk.StringVar - 非発散部カラーマップ
self._fractal_type_row: int - フラクタルタイプ選択行
self._formula_row: int - 数式表示行
self._param_section_last_row: int - パラメータセクション最終行
self._diverge_section_last_row: int - 発散部セクション最終行
self._non_diverge_section_last_row: int - 非発散部セクション最終行
self.colormaps: list - カラーマップリスト
self.diverge_algorithms: list - 発散部アルゴリズムリスト
self.non_diverge_algorithms: list - 非発散部アルゴリズムリスト
self.COLORBAR_WIDTH: int - カラーバー幅
self.COLORBAR_HEIGHT: int - カラーバー高さ

## METHOD_SIGNATURES
def __init__(self, parent, update_callback, reset_callback, logger: DebugLogger) -> None
機能 コンストラクタ。パネルのセットアップ、カラーバーの初期化

def _setup_panel(self) -> None
機能 パネルのセットアップ。各セクションのセットアップ、パネルのレイアウト設定

def _setup_fractal_type_section(self) -> None
機能 フラクタルタイプセクションのセットアップ。ラベルとコンボボックスの追加、イベントバインド

def _setup_formula_section(self) -> None
機能 数式表示セクションのセットアップ。数式表示ラベルの追加、数式の初期表示

def _setup_parameter_section(self) -> None
機能 パラメータ表示セクションのセットアップ。各パラメータのラベルと入力欄の追加、イベントバインド

def _setup_diverge_section(self) -> None
機能 発散部セクションのセットアップ。各ウィジェットの追加と設定、イベントバインド

def _setup_non_diverge_section(self) -> None
機能 非発散部セクションのセットアップ。各ウィジェットの追加と設定、イベントバインド

def _setup_buttons(self) -> None
機能 ボタンのセットアップ。描画ボタンと描画リセットボタンの追加、各ボタンのコールバック設定

def _add_label(self, text, row, col, columnspan=1, padx=10, pady=2) -> None
機能 ラベルを追加する

def _add_entry(self, row, col, var, padx=10, pady=2) -> ttk.Entry
機能 入力欄を追加する

def _add_combobox(self, row, col, var, values, width=None, padx=10, pady=2) -> ttk.Combobox
機能 コンボボックスを追加する

def _add_button(self, text, row, col, colspan, command) -> ttk.Button
機能 ボタンを追加する

def _common_callback(self, event=None) -> None
機能 共通のコールバック関数。描画モードをクイックに設定、描画更新コールバックを呼び出し、カラーバーを更新

def _create_colorbar_image(self, cmap_name: str) -> ImageTk.PhotoImage
機能 カラーバー画像を生成する

def _update_colorbars(self, *args) -> None
機能 カラーバーを更新する。発散部と非発散部のカラーバー画像を生成し、ラベルに設定する

def _show_formula_display(self) -> None
機能 数式を表示する。選択されたフラクタルタイプに応じて数式を更新する

def _get_parameters(self) -> dict
機能 パラメータを取得する。パネル上のウィジェットから現在のパラメータを取得し、辞書として返す

## CORE_EXECUTION_FLOW
__init__ → _setup_panel → 各セクションのセットアップ → ボタンのセットアップ
ユーザー操作（パラメータ変更、ボタンクリック） → 各コールバック関数 → 描画更新/リセット

## KEY_LOGIC_PATTERNS
- コールバック関数: パラメータ変更時に外部の描画処理を呼び出す
- UI要素の整理: 各セクションごとにUI要素をグループ化
- カラーバーの動的生成: 選択されたカラーマップに基づいてカラーバー画像を生成
- パラメータの辞書化:  現在のパラメータを辞書形式で取得

## CRITICAL_BEHAVIORS
- パラメータ入力とUI:  各種パラメータの入力と選択UIの提供
- コールバック:  パラメータ変更時の描画更新処理の実行
- カラーバーの更新:  選択されたカラーマップに応じたカラーバーの表示
- パラメータの取得:  現在のパラメータを辞書として取得し、外部に提供


==============================
# MODULE_INFO:
ui/status_bar.py

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
_animation_state: AnimationState - アニメーション状態を管理するAnimationState

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
