==============================
# MODULE_INFO:
render.py

## MODULE_PURPOSE
フラクタル画像生成エンジン

## CLASS_DEFINITION:
(クラス定義なし)

## DEPENDENCIES
numpy: 数値計算
time: 時間計測
coloring.manager: 色管理
fractal.fractal_types.julia: ジュリア集合計算
fractal.fractal_types.mandelbrot: マンデルブロ集合計算
ui.zoom_function.debug_logger.DebugLogger: デバッグログ
ui.zoom_function.enums.LogLevel: ログレベル定義

## CLASS_ATTRIBUTES
(クラス属性なし)

## METHOD_SIGNATURES
def _calculate_dynamic_resolution(width, base_res=600, min_res=400, max_res=1200)
機能: ズームレベルに応じて描画解像度を動的に計算

def _create_complex_grid(params, width, height, logger)
機能: 複素グリッドを作成

def _create_fractal_grid(params, super_resolution_x, super_resolution_y, logger)
機能: フラクタル計算用の複素グリッドを作成し、フラクタル集合を計算

def render_fractal(render_mode, params, color_params, logger)
機能: フラクタル画像を生成

## CORE_EXECUTION_FLOW
_calculate_dynamic_resolution -> _create_complex_grid -> _create_fractal_grid -> render_fractal

## KEY_LOGIC_PATTERNS
- 動的解像度制御: ズームレベルに応じた解像度調整
- フラクタル計算: ジュリア集合、マンデルブロ集合の計算
- レンダリング最適化: スーパーサンプリング

## CRITICAL_BEHAVIORS
- 解像度調整の正確性
- フラクタル計算の正確性
- レンダリング効率

==============================
# MODULE_INFO:
julia.py

## MODULE_PURPOSE
ジュリア集合の計算

## CLASS_DEFINITION:
(クラス定義なし)

## DEPENDENCIES
numpy: 数値計算
ui.zoom_function.debug_logger.DebugLogger: デバッグログ
ui.zoom_function.enums.LogLevel: ログレベル定義
typing: 型ヒント

## CLASS_ATTRIBUTES
(クラス属性なし)

## METHOD_SIGNATURES
def compute_julia(Z: np.ndarray, C: complex, max_iter: int,  logger: DebugLogger) -> Dict[str, np.ndarray]
機能: ジュリア集合の計算を実行

## CORE_EXECUTION_FLOW
compute_julia

## KEY_LOGIC_PATTERNS
- ジュリア集合計算: 複素グリッドとパラメータからジュリア集合を計算

## CRITICAL_BEHAVIORS
- ジュリア集合計算の正確性
- 計算効率

==============================
# MODULE_INFO:
mandelbrot.py

## MODULE_PURPOSE
マンデルブロ集合の計算

## CLASS_DEFINITION:
(クラス定義なし)

## DEPENDENCIES
numpy: 数値計算
ui.zoom_function.debug_logger.DebugLogger: デバッグログ
ui.zoom_function.enums.LogLevel: ログレベル定義
typing: 型ヒント

## CLASS_ATTRIBUTES
(クラス属性なし)

## METHOD_SIGNATURES
def compute_mandelbrot(Z: np.ndarray, Z0: complex, max_iter: int, logger: DebugLogger) -> Dict[str, np.ndarray]
機能: マンデルブロ集合の計算を実行

## CORE_EXECUTION_FLOW
compute_mandelbrot

## KEY_LOGIC_PATTERNS
- マンデルブロ集合計算: 複素グリッドと初期値からマンデルブロ集合を計算

## CRITICAL_BEHAVIORS
- マンデルブロ集合計算の正確性
- 計算効率
