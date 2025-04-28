==============================
# MODULE_INFO:
__init__.py

## MODULE_PURPOSE
coloring.divergent パッケージの初期化

## CLASS_DEFINITION:
(クラス定義なし)

## DEPENDENCIES
(依存関係なし)

## CLASS_ATTRIBUTES
(クラス属性なし)

## METHOD_SIGNATURES
(メソッドなし)

## CORE_EXECUTION_FLOW
(実行フローなし)

## KEY_LOGIC_PATTERNS
- パッケージ初期化

## CRITICAL_BEHAVIORS
- パッケージとして認識されるための空ファイル

==============================
# MODULE_INFO:
angle.py

## MODULE_PURPOSE
発散領域に対して、複素数の偏角に基づいたカラーリングを適用する

## CLASS_DEFINITION:
(クラス定義なし)

## DEPENDENCIES
numpy: 数値計算
typing: 型ヒント
matplotlib.colors.Colormap: カラーマップ
ui.zoom_function.debug_logger.DebugLogger: デバッグログ
ui.zoom_function.enums.LogLevel: ログレベル定義
coloring.utils._normalize_and_color: 正規化と着色

## CLASS_ATTRIBUTES
(クラス属性なし)

## METHOD_SIGNATURES
def apply_angle_coloring(colored: np.ndarray, divergent_mask: np.ndarray, z_vals: np.ndarray, cmap_func: Colormap, params: Dict, logger: DebugLogger) -> None
機能: 複素数の偏角を計算し、カラーマップを用いて着色する

## CORE_EXECUTION_FLOW
apply_angle_coloring

## KEY_LOGIC_PATTERNS
- 偏角計算: 複素数の角度を計算し、正規化
- カラーマッピング: 正規化された角度に基づいて色を割り当て

## CRITICAL_BEHAVIORS
- 偏角計算の正確性
- カラーマッピングの適切さ

==============================
# MODULE_INFO:
distance.py

## MODULE_PURPOSE
発散領域に対して、原点からの距離に基づいたカラーリングを適用する

## CLASS_DEFINITION:
(クラス定義なし)

## DEPENDENCIES
numpy: 数値計算
typing: 型ヒント
matplotlib.colors.Colormap: カラーマップ
ui.zoom_function.debug_logger.DebugLogger: デバッグログ
ui.zoom_function.enums.LogLevel: ログレベル定義
coloring.utils._normalize_and_color: 正規化と着色

## CLASS_ATTRIBUTES
(クラス属性なし)

## METHOD_SIGNATURES
def apply_distance_coloring(colored: np.ndarray, divergent_mask: np.ndarray, z_vals: np.ndarray, cmap_func: Colormap, params: Dict, logger: DebugLogger) -> None
機能: 発散した点の原点からの距離を計算し、その距離に基づいて色を付ける

## CORE_EXECUTION_FLOW
apply_distance_coloring

## KEY_LOGIC_PATTERNS
- 距離計算: 発散点と原点との距離を計算
- カラーマッピング: 計算された距離に基づいて色を割り当て

## CRITICAL_BEHAVIORS
- 距離計算の正確性
- カラーマッピングの適切さ

==============================
# MODULE_INFO:
histogram.py

## MODULE_PURPOSE
発散領域に対して、ヒストグラム平坦化に基づくカラーリングを適用する

## CLASS_DEFINITION:
(クラス定義なし)

## DEPENDENCIES
numpy: 数値計算
typing: 型ヒント
matplotlib.colors.Colormap: カラーマップ
ui.zoom_function.debug_logger.DebugLogger: デバッグログ
ui.zoom_function.enums.LogLevel: ログレベル定義

## CLASS_ATTRIBUTES
(クラス属性なし)

## METHOD_SIGNATURES
def apply_histogram_flattening(colored: np.ndarray, divergent_mask: np.ndarray, iterations: np.ndarray, cmap_func: Colormap, params: Dict, logger: DebugLogger) -> None
機能: 発散領域の反復回数のヒストグラムを計算し、累積分布関数に基づいて色を割り当てる

## CORE_EXECUTION_FLOW
apply_histogram_flattening

## KEY_LOGIC_PATTERNS
- ヒストグラム計算: 発散領域の反復回数の分布を計算
- ヒストグラム平坦化: 累積分布関数に基づく色の割り当て

## CRITICAL_BEHAVIORS
- ヒストグラム計算の正確性
- カラーマッピングの適切さ

==============================
# MODULE_INFO:
linear.py

## MODULE_PURPOSE
発散領域に対して、反復回数に基づく線形マッピングでカラーリングを適用する

## CLASS_DEFINITION:
(クラス定義なし)

## DEPENDENCIES
numpy: 数値計算
typing: 型ヒント
matplotlib.colors.Colormap: カラーマップ
ui.zoom_function.debug_logger.DebugLogger: デバッグログ
ui.zoom_function.enums.LogLevel: ログレベル定義
coloring.utils._normalize_and_color: 正規化と着色

## CLASS_ATTRIBUTES
(クラス属性なし)

## METHOD_SIGNATURES
def apply_linear_mapping(colored: np.ndarray, divergent_mask: np.ndarray, iterations: np.ndarray, cmap_func: Colormap, params: Dict, logger: DebugLogger) -> None
機能: 発散領域の各点に対して、その反復回数を線形に正規化し、カラーマップを用いて色を決定する

## CORE_EXECUTION_FLOW
apply_linear_mapping

## KEY_LOGIC_PATTERNS
- 反復回数の正規化: 発散領域の反復回数を0から1の範囲に正規化
- カラーマッピング: 正規化された反復回数に基づいて色を割り当て

## CRITICAL_BEHAVIORS
- 反復回数の正規化の正確性
- カラーマッピングの適切さ


==============================
# MODULE_INFO:
logarithmic.py

## MODULE_PURPOSE
発散領域に対して、反復回数の対数に基づいたカラーリングを適用する

## CLASS_DEFINITION:
(クラス定義なし)

## DEPENDENCIES
numpy: 数値計算
typing: 型ヒント
matplotlib.colors.Colormap: カラーマップ
ui.zoom_function.debug_logger.DebugLogger: デバッグログ
ui.zoom_function.enums.LogLevel: ログレベル定義
coloring.utils._normalize_and_color: 正規化と着色

## CLASS_ATTRIBUTES
(クラス属性なし)

## METHOD_SIGNATURES
def apply_logarithmic_mapping(colored: np.ndarray, divergent_mask: np.ndarray, iterations: np.ndarray, cmap_func: Colormap, params: Dict, logger: DebugLogger) -> None
機能: 発散領域の反復回数の対数を計算し、カラーマップを用いて色を決定する

## CORE_EXECUTION_FLOW
apply_logarithmic_mapping

## KEY_LOGIC_PATTERNS
- 反復回数の対数変換: 反復回数を対数スケールに変換
- カラーマッピング: 対数変換された反復回数に基づいて色を割り当て

## CRITICAL_BEHAVIORS
- 対数変換の正確性
- カラーマッピングの適切さ

==============================
# MODULE_INFO:
orbit_trap.py

## MODULE_PURPOSE
発散領域に対して、軌道トラップ法に基づくカラーリングを適用する

## CLASS_DEFINITION:
(クラス定義なし)

## DEPENDENCIES
numpy: 数値計算
typing: 型ヒント
matplotlib.colors.Colormap: カラーマップ
ui.zoom_function.debug_logger.DebugLogger: デバッグログ
ui.zoom_function.enums.LogLevel: ログレベル定義
coloring.utils._normalize_and_color: 正規化と着色

## CLASS_ATTRIBUTES
(クラス属性なし)

## METHOD_SIGNATURES
def apply_orbit_trap(colored: np.ndarray, divergent_mask: np.ndarray, iterations: np.ndarray, z_vals: np.ndarray, cmap_func: Colormap, params: Dict, logger: DebugLogger) -> None
機能: 複素数列がある特定の領域（トラップ）にどれだけ近づくかに基づいて色を付ける

## CORE_EXECUTION_FLOW
apply_orbit_trap

## KEY_LOGIC_PATTERNS
- 軌道トラップ計算: 複素数列とトラップ領域との距離を計算
- カラーマッピング: 計算された距離に基づいて色を割り当て

## CRITICAL_BEHAVIORS
- 軌道トラップ計算の正確性
- カラーマッピングの適切さ

==============================
# MODULE_INFO:
potential.py

## MODULE_PURPOSE
発散領域に対して、ポテンシャル関数法に基づくカラーリングを適用する

## CLASS_DEFINITION:
(クラス定義なし)

## DEPENDENCIES
numpy: 数値計算
typing: 型ヒント
matplotlib.colors.Colormap: カラーマップ
ui.zoom_function.debug_logger.DebugLogger: デバッグログ
ui.zoom_function.enums.LogLevel: ログレベル定義
coloring.utils._normalize_and_color: 正規化と着色

## CLASS_ATTRIBUTES
(クラス属性なし)

## METHOD_SIGNATURES
def apply_potential(colored: np.ndarray, divergent_mask: np.ndarray, z_vals: np.ndarray, cmap_func: Colormap, params: Dict, logger: DebugLogger) -> None
機能: ポテンシャル関数を用いて発散の度合いを計算し、カラーマップで着色する

## CORE_EXECUTION_FLOW
apply_potential

## KEY_LOGIC_PATTERNS
- ポテンシャル計算: 複素数列の発散速度をポテンシャル関数で評価
- カラーマッピング: 計算されたポテンシャル値に基づいて色を割り当て

## CRITICAL_BEHAVIORS
- ポテンシャル計算の正確性
- カラーマッピングの適切さ

==============================
# MODULE_INFO:
smoothing.py

## MODULE_PURPOSE
発散領域に対して、スムージングされた反復回数に基づくカラーリングを適用する

## CLASS_DEFINITION:
(クラス定義なし)

## DEPENDENCIES
numpy: 数値計算
typing: 型ヒント
matplotlib.colors.Colormap: カラーマップ
ui.zoom_function.debug_logger.DebugLogger: デバッグログ
ui.zoom_function.enums.LogLevel: ログレベル定義
coloring.utils._normalize_and_color: 正規化と着色
coloring.utils._smooth_iterations: スムージング計算
coloring.utils.fast_smoothing: 高速スムージング計算

## CLASS_ATTRIBUTES
(クラス属性なし)

## METHOD_SIGNATURES
def apply_smoothing(colored: np.ndarray, divergent_mask: np.ndarray, iterations: np.ndarray, z_vals: np.ndarray, cmap_func: Colormap, params: Dict, smoothing_method: str, logger: DebugLogger) -> None
機能: 指定されたスムージングメソッドを用いて反復回数を補正し、カラーマップで着色する

## CORE_EXECUTION_FLOW
apply_smoothing

## KEY_LOGIC_PATTERNS
- スムージング処理: 反復回数の不連続性を補正
- カラーマッピング: スムージングされた反復回数に基づいて色を割り当て

## CRITICAL_BEHAVIORS
- スムージング処理の正確性と適切さ
- カラーマッピングの適切さ
