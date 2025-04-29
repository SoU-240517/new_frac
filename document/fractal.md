==============================
# MODULE_INFO:
render.py

## MODULE_PURPOSE
フラクタル画像生成エンジン。ズームレベルに応じた動的解像度計算、複素グリッド生成、フラクタル計算の実行（Julia集合、Mandelbrot集合）、スーパーサンプリングによる着色処理、ダウンサンプリングを行うモジュール。

## CLASS_DEFINITION:
(クラス定義なし)

## DEPENDENCIES
numpy (np): 数値計算
time: 時間計測
coloring.manager: 着色処理管理
fractal.fractal_types.julia: ジュリア集合計算関数
fractal.fractal_types.mandelbrot: マンデルブロ集合計算関数
ui.zoom_function.debug_logger.DebugLogger: デバッグログ管理
ui.zoom_function.enums.LogLevel: ログレベル定義
typing: 型ヒント (Dict, Any, Tuple)

## CLASS_ATTRIBUTES
(クラス属性なし)

## METHOD_SIGNATURES
def _calculate_dynamic_resolution(width: float, config: Dict[str, Any], logger: DebugLogger) -> int
機能: ズームレベルに応じて描画解像度を動的に計算する。設定ファイルからパラメータを読み込む。

def _create_complex_grid(params: Dict[str, Any], width: int, height: int, logger: DebugLogger) -> np.ndarray
機能: 描画範囲パラメータ、指定された幅、高さに基づいて複素グリッド (np.ndarray) を作成する。回転も考慮する。

def _create_fractal_grid(params: Dict[str, Any], super_resolution_x: int, super_resolution_y: int, logger: DebugLogger) -> Dict[str, np.ndarray]
機能: フラクタル計算用の複素グリッドを作成し、選択されたフラクタルタイプ（JuliaまたはMandelbrot）に基づいてフラクタル集合の計算を実行する。計算結果（反復回数、マスク、最終Z値）を返す。

def _downsample_image(high_res_image: np.ndarray, target_width: int, target_height: int, sample_x: int, sample_y: int, logger: DebugLogger) -> np.ndarray
機能: 高解像度の画像データを指定されたサンプル数でダウンサンプリングする。

def render_fractal(render_mode: str, params: Dict[str, Any], color_params: Dict[str, Any], config: Dict[str, Any], logger: DebugLogger) -> np.ndarray
機能: フラクタル画像を生成するメイン関数。動的解像度計算、複素グリッド生成、フラクタル計算、着色、ダウンサンプリングを実行し、最終的な画像データを返す。設定データを受け取る。

## CORE_EXECUTION_FLOW
render_fractal (config受け取り含む) → _calculate_dynamic_resolution (config渡す) → _create_complex_grid → _create_fractal_grid → manager.colorize (着色) → _downsample_image (必要であれば) → 最終画像データ

## KEY_LOGIC_PATTERNS
- 動的解像度制御: ズームレベルと設定に基づいた解像度調整 (_calculate_dynamic_resolution)
- 複素グリッド生成: 描画範囲パラメータと回転を考慮したグリッド作成 (_create_complex_grid)
- フラクタル計算実行: 選択されたフラクタルタイプに応じた計算関数の呼び出し (_create_fractal_grid)
- 着色処理: coloring.manager モジュールへの委譲
- スーパーサンプリングとダウンサンプリング: _downsample_image による画像の平滑化
- 設定ファイルからの読み込み: _calculate_dynamic_resolution で設定を読み込む
- エラーハンドリング: 着色処理中のエラーを捕捉し、エラー画像を返す

## CRITICAL_BEHAVIORS
- 動的解像度計算の正確性
- 複素グリッド生成における描画範囲と回転の正確なマッピング
- フラクタル計算関数への正確なパラメータ引き渡し
- 着色処理とダウンサンプリングの正確性
- エラー発生時の適切なフォールバック処理（エラー画像の生成）
- 設定パラメータの読み込みと適用


==============================
# MODULE_INFO:
julia.py

## MODULE_PURPOSE
ジュリア集合の計算ロジックを実装するモジュール。指定された複素グリッドとパラメータに基づき、各点の反復回数、収束マスク、最終Z値を計算する。

## CLASS_DEFINITION:
(クラス定義なし)

## DEPENDENCIES
numpy (np): 数値計算
ui.zoom_function.debug_logger.DebugLogger: デバッグログ管理
ui.zoom_function.enums.LogLevel: ログレベル定義
typing: 型ヒント (Dict, np.ndarray)

## CLASS_ATTRIBUTES
(クラス属性なし)

## METHOD_SIGNATURES
def compute_julia(Z: np.ndarray, C: complex, max_iter: int, logger: DebugLogger) -> Dict[str, np.ndarray]
機能: ジュリア集合の計算を実行する。入力の複素グリッド `Z` とパラメータ `C` に対して、`max_iter` 回の反復計算を行い、各点の反復回数、収束マスク、最終Z値を計算して辞書で返す。

## CORE_EXECUTION_FLOW
compute_julia (反復計算ループ)

## KEY_LOGIC_PATTERNS
- ジュリア集合計算: z = z^2 + C の反復式を用いた計算
- 発散判定: |z| > 2 を基準とした発散点の判定
- ベクトル化計算: NumPyを用いたグリッド全体の並列計算

## CRITICAL_BEHAVIORS
- 反復計算と発散判定の正確性
- 最大反復回数までの計算完了
- 計算結果（反復回数、マスク、最終Z値）の正確な出力
- NumPyによる効率的な計算


==============================
# MODULE_INFO:
mandelbrot.py

## MODULE_PURPOSE
マンデルブロ集合の計算ロジックを実装するモジュール。指定された複素グリッドと初期値に基づき、各点の反復回数、収束マスク、最終Z値を計算する。

## CLASS_DEFINITION:
(クラス定義なし)

## DEPENDENCIES
numpy (np): 数値計算
ui.zoom_function.debug_logger.DebugLogger: デバッグログ管理
ui.zoom_function.enums.LogLevel: ログレベル定義
typing: 型ヒント (Dict, np.ndarray)

## CLASS_ATTRIBUTES
(クラス属性なし)

## METHOD_SIGNATURES
def compute_mandelbrot(Z: np.ndarray, Z0: complex, max_iter: int, logger: DebugLogger) -> Dict[str, np.ndarray]
機能: マンデルブロ集合の計算を実行する。入力の複素グリッド `Z` (各点がパラメータ c に対応) と初期値 `Z0` に対して、`max_iter` 回の反復計算を行い、各点の反復回数、収束マスク、最終Z値を計算して辞書で返す。

## CORE_EXECUTION_FLOW
compute_mandelbrot (反復計算ループ)

## KEY_LOGIC_PATTERNS
- マンデルブロ集合計算: z = z^2 + c の反復式を用いた計算 (c はグリッド上の点に対応)
- 発散判定: |z| > 2 を基準とした発散点の判定
- ベクトル化計算: NumPyを用いたグリッド全体の並列計算

## CRITICAL_BEHAVIORS
- 反復計算と発散判定の正確性
- 最大反復回数までの計算完了
- 計算結果（反復回数、マスク、最終Z値）の正確な出力
- NumPyによる効率的な計算
