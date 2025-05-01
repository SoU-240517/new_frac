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
