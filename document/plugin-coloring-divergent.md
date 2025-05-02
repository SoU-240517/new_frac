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
- 複素数の偏角を計算し、カラーマップを用いて着色する

## CLASS_DEFINITION:
(クラス定義なし)

## DEPENDENCIES
numpy (np): 数値計算
typing: 型ヒント (Dict)
matplotlib.colors.Colormap: カラーマップ
ui.zoom_function.debug_logger.DebugLogger: デバッグログ管理
ui.zoom_function.enums.LogLevel: ログレベル定義

## CLASS_ATTRIBUTES
(クラス属性なし)

## METHOD_SIGNATURES
def apply_angle_coloring(colored: np.ndarray, divergent_mask: np.ndarray, z_vals: np.ndarray, cmap_func: Colormap, params: Dict, logger: DebugLogger) -> None
機能: 複素数の偏角を計算し、カラーマップを用いて着色する

## CORE_EXECUTION_FLOW
偏角計算 → 正規化 → カラーマップ適用

## KEY_LOGIC_PATTERNS
- 偏角計算: 複素数の角度を計算し、正規化
- カラーマップ適用: 発散点にカラーマップを適用
- 発散点のみの着色: divergent_maskを使用

## CRITICAL_BEHAVIORS
- 偏角計算の正確性
- カラーマップ適用の正確性
- 発散点の適切な着色


==============================
# MODULE_INFO:
distance.py

## MODULE_PURPOSE
発散領域に対して、原点からの距離に基づいたカラーリングを適用する
- 発散した点の原点からの距離を計算し、その距離に基づいて色を付ける

## CLASS_DEFINITION:
(クラス定義なし)

## DEPENDENCIES
numpy (np): 数値計算
typing: 型ヒント (Dict)
matplotlib.colors.Colormap: カラーマップ
ui.zoom_function.debug_logger.DebugLogger: デバッグログ管理
ui.zoom_function.enums.LogLevel: ログレベル定義

## CLASS_ATTRIBUTES
(クラス属性なし)

## METHOD_SIGNATURES
def apply_distance_coloring(colored: np.ndarray, divergent_mask: np.ndarray, z_vals: np.ndarray, cmap_func: Colormap, params: Dict, logger: DebugLogger) -> None
機能: 発散領域に対して、原点からの距離に基づいたカラーリングを適用する

## CORE_EXECUTION_FLOW
距離計算 → 正規化 → カラーマップ適用

## KEY_LOGIC_PATTERNS
- 距離計算: 発散点と原点との距離を計算
- 正規化: 最小値と最大値による正規化
- 発散点のみの着色: divergent_maskを使用

## CRITICAL_BEHAVIORS
- 距離計算の正確性
- 正規化の正確性
- 発散点の適切な着色


==============================
# MODULE_INFO:
histogram.py

## MODULE_PURPOSE
発散領域に対して、ヒストグラム平坦化に基づくカラーリングを適用する
- 発散領域の反復回数のヒストグラムを計算し、累積分布関数に基づいて色を割り当てる

## CLASS_DEFINITION:
(クラス定義なし)

## DEPENDENCIES
numpy (np): 数値計算
typing: 型ヒント (Dict)
matplotlib.colors.Colormap: カラーマップ
ui.zoom_function.debug_logger.DebugLogger: デバッグログ管理
ui.zoom_function.enums.LogLevel: ログレベル定義

## CLASS_ATTRIBUTES
(クラス属性なし)

## METHOD_SIGNATURES
def apply_histogram_flattening(colored: np.ndarray, divergent_mask: np.ndarray, iterations: np.ndarray, cmap_func: Colormap, params: Dict, logger: DebugLogger) -> None
機能: 発散領域に対して、ヒストグラム平坦化に基づくカラーリングを適用する

## CORE_EXECUTION_FLOW
ヒストグラム計算 → 累積分布関数計算 → カラーマップ適用

## KEY_LOGIC_PATTERNS
- ヒストグラム計算: 発散領域の反復回数の分布を計算
- 累積分布関数計算: ヒストグラムに基づいて累積分布関数を計算
- 発散点のみの着色: divergent_maskを使用

## CRITICAL_BEHAVIORS
- ヒストグラム計算の正確性
- 累積分布関数計算の正確性
- 発散点の適切な着色


==============================
# MODULE_INFO:
linear.py

## MODULE_PURPOSE
発散領域に対して、反復回数に基づく線形マッピングでカラーリングを適用する
- 発散領域の各点に対して、その反復回数を線形に正規化し、カラーマップを用いて色を決定する

## CLASS_DEFINITION:
(クラス定義なし)

## DEPENDENCIES
numpy (np): 数値計算
typing: 型ヒント (Dict)
matplotlib.colors.Normalize: 正規化
matplotlib.colors.Colormap: カラーマップ
ui.zoom_function.debug_logger.DebugLogger: デバッグログ管理
ui.zoom_function.enums.LogLevel: ログレベル定義

## CLASS_ATTRIBUTES
(クラス属性なし)

## METHOD_SIGNATURES
def apply_linear_mapping(colored: np.ndarray, divergent_mask: np.ndarray, iterations: np.ndarray, cmap_func: Colormap, params: Dict, logger: DebugLogger) -> None
機能: 発散領域に対して、反復回数に基づく線形マッピングでカラーリングを適用する

## CORE_EXECUTION_FLOW
反復回数の正規化 → カラーマップ適用

## KEY_LOGIC_PATTERNS
- 反復回数の正規化: 発散領域の反復回数を1からmax_iterationsの範囲に正規化
- カラーマップ適用:ELSE: 正規化された値にカラーマップを適用
- 発散点のみの着色: divergent_maskを使用

## CRITICAL_BEHAVIORS
- 反復回数の正規化の正確性
- カラーマップ適用の正確性
- 発散点の適切な着色


==============================
# MODULE_INFO:
logarithmic.py

## MODULE_PURPOSE
発散領域に対して、反復回数の対数に基づくカラーリングを適用する
- 発散領域の各点に対して、その反復回数の対数をとり、カラーマップを用いて色を決定する

## CLASS_DEFINITION:
(クラス定義なし)

## DEPENDENCIES
numpy: 数値計算
matplotlib.colors.Colormap: カラーマップ
matplotlib.colors.Normalize: 正規化
typing: 型ヒント
ui.zoom_function.debug_logger.DebugLogger: デバッグログ
ui.zoom_function.enums.LogLevel: ログレベル定義
coloring.utils._normalize_and_color: 正規化と着色

## CLASS_ATTRIBUTES
(クラス属性なし)

## METHOD_SIGNATURES
def apply_logarithmic_mapping(colored: np.ndarray, divergent_mask: np.ndarray, iterations: np.ndarray, cmap_func: Colormap, params: Dict, logger: DebugLogger) -> None
機能: 発散領域に対して、反復回数の対数に基づくカラーリングを適用する

## CORE_EXECUTION_FLOW
対数計算 → 正規化 → カラーマップ適用

## KEY_LOGIC_PATTERNS
- 対数計算: np.log()を使用
- 正規化: Normalizeを使用
- 発散点のみの着色: divergent_maskを使用

## CRITICAL_BEHAVIORS
- 対数計算の正確性
- 正規化の正確性
- 無限値や NaN の除外処理の正確性


==============================
# MODULE_INFO:
orbit_trap.py

## MODULE_PURPOSE
発散領域に対して、軌道トラップ法に基づくカラーリングを適用する
- 複素数列がある特定の領域（トラップ）にどれだけ近づくかに基づいて色を付ける

## CLASS_DEFINITION:
(クラス定義なし)

## DEPENDENCIES
numpy: 数値計算
matplotlib.colors.Colormap: カラーマップ
typing: 型ヒント
ui.zoom_function.debug_logger.DebugLogger: デバッグログ
ui.zoom_function.enums.LogLevel: ログレベル定義
coloring.utils._normalize_and_color: 正規化と着色

## CLASS_ATTRIBUTES
(クラス属性なし)

## METHOD_SIGNATURES
def apply_orbit_trap(colored: np.ndarray, divergent_mask: np.ndarray, iterations: np.ndarray, z_vals: np.ndarray, cmap_func: Colormap, params: Dict, logger: DebugLogger) -> None
機能: 発散領域に対して、軌道トラップ法に基づくカラーリングを適用する

## CORE_EXECUTION_FLOW
トラップ中心の複素数変換 → トラップ形状に応じた距離計算 → 正規化 → カラーマップ適用

## KEY_LOGIC_PATTERNS
- トラップ中心の複素数変換: 複素数を使用
- トラップ形状に応じた距離計算（三角関数は三角形トラップで使用）
- 正規化: 最小値と最大値による正規化

## CRITICAL_BEHAVIORS
- トラップ中心の複素数変換の正確性
- トラップ形状ごとの距離計算の正確性
- 正規化の正確性


==============================
# MODULE_INFO:
potential.py

## MODULE_PURPOSE
発散領域に対して、ポテンシャル関数法に基づくカラーリングを適用する
- ポテンシャル関数を用いて発散の度合いを計算し、カラーマップで着色する

## CLASS_DEFINITION:
(クラス定義なし)

## DEPENDENCIES
numpy: 数値計算
matplotlib.colors.Colormap: カラーマップ
typing: 型ヒント
ui.zoom_function.debug_logger.DebugLogger: デバッグログ
ui.zoom_function.enums.LogLevel: ログレベル定義
coloring.utils._normalize_and_color: 正規化と着色

## CLASS_ATTRIBUTES
(クラス属性なし)

## METHOD_SIGNATURES
def apply_potential(colored: np.ndarray, divergent_mask: np.ndarray, z_vals: np.ndarray, cmap_func: Colormap, params: Dict, logger: DebugLogger) -> None
機能: 発散領域に対して、ポテンシャル関数法に基づくカラーリングを適用する

## CORE_EXECUTION_FLOW
ポテンシャル計算 → 正規化 → カラーマップ適用 → 発散していない点の黒への設定

## KEY_LOGIC_PATTERNS
- ポテンシャル計算: 対数を使用
- 正規化: 最小値と最大値による正規化
- 発散点のみの着色: divergent_maskを使用
- 発散していない点の処理: 黒に設定

## CRITICAL_BEHAVIORS
- ポテンシャル計算の正確性
- 正規化の正確性
- 発散していない点の黒への設定の正確性


==============================
# MODULE_INFO:
smoothing.py

## MODULE_PURPOSE
発散領域に対して、指定されたスムージングメソッドを用いて反復回数に基づくカラーリングを適用する
- スムージング処理を行い、その結果を用いてカラーマップで着色する

## CLASS_DEFINITION:
(クラス定義なし)

## DEPENDENCIES
numpy: 数値計算
matplotlib.colors.Colormap: カラーマップ
typing: 型ヒント
ui.zoom_function.debug_logger.DebugLogger: デバッグログ
ui.zoom_function.enums.LogLevel: ログレベル定義
coloring.utils._smooth_iterations: スムージング処理
coloring.utils._normalize_and_color: 正規化と着色
coloring.utils.fast_smoothing: 高速スムージング処理
coloring.utils.ColorAlgorithmError: 例外クラス

## CLASS_ATTRIBUTES
(クラス属性なし)

## METHOD_SIGNATURES
def apply_smoothing(colored: np.ndarray, divergent_mask: np.ndarray, iterations: np.ndarray, z_vals: np.ndarray, cmap_func: Colormap, params: Dict, smoothing_method: str, logger: DebugLogger) -> None
機能: 発散領域に対して、指定されたスムージングメソッドを用いて反復回数に基づくカラーリングを適用する

## CORE_EXECUTION_FLOW
スムージング処理 → 有限値の抽出 → 正規化 → カラーマップ適用

## KEY_LOGIC_PATTERNS
- スムージング処理: _smooth_iterationsを使用
- 有限値の抽出: divergent_maskとnp.isfiniteを使用
- 正規化: _normalize_and_colorを使用
- 発散点のみの着色: divergent_maskを使用

## CRITICAL_BEHAVIORS
- スムージングメソッドごとの正確性
- 有限値の抽出の正確性
- 正規化の正確性
- 例外処理の適切性
