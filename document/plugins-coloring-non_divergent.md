==============================
# MODULE_INFO:
__init__.py

## MODULE_PURPOSE
non_divergent パッケージの初期化ファイル

## CLASS_DEFINITION:
なし

## DEPENDENCIES
なし

## MODULE_ATTRIBUTES
なし

## METHOD_SIGNATURES
なし

## CORE_EXECUTION_FLOW
なし

## KEY_LOGIC_PATTERNS
なし

## CRITICAL_BEHAVIORS
なし


==============================
# MODULE_INFO:
chaotic_orbit.py

## MODULE_PURPOSE
非発散領域をカオス軌道で着色する

## CLASS_DEFINITION:
なし

## DEPENDENCIES
numpy (np)
typing
matplotlib.colors.Colormap
ui.zoom_function.debug_logger.DebugLogger
ui.zoom_function.enums.LogLevel

## MODULE_ATTRIBUTES
なし

## METHOD_SIGNATURES
def apply_chaotic_orbit(colored: np.ndarray, non_divergent_mask: np.ndarray, z_vals: np.ndarray, non_cmap_func: Colormap, params: Dict, logger: DebugLogger) -> None
機能: 非発散領域をカオス軌道で着色する

## CORE_EXECUTION_FLOW
非発散点の複素数値から極座標系の値を計算
カオス軌道の特徴を反映したRGB値の計算
RGB値を0-1の範囲に正規化し、255倍して8bitカラーバリューに変換

## KEY_LOGIC_PATTERNS
複素数の絶対値と偏角を用いたRGB値の計算
NumPy配列操作による効率的な処理

## CRITICAL_BEHAVIORS
非発散領域の着色処理


==============================
# MODULE_INFO:
complex_potential.py

## MODULE_PURPOSE
非発散領域を複素ポテンシャルで着色する

## CLASS_DEFINITION:
なし

## DEPENDENCIES
numpy (np)
typing
matplotlib.colors.Colormap
ui.zoom_function.debug_logger.DebugLogger
ui.zoom_function.enums.LogLevel

## MODULE_ATTRIBUTES
なし

## METHOD_SIGNATURES
def apply_complex_potential(colored: np.ndarray, non_divergent_mask: np.ndarray, z_vals: np.ndarray, non_cmap_func: Colormap, params: Dict, logger: DebugLogger) -> None
機能: 非発散領域を複素ポテンシャルで着色する

## CORE_EXECUTION_FLOW
複素数の絶対値の対数を計算（複素ポテンシャル）
0-1の範囲に正規化
複素数の角度（位相）を計算して正規化
正規化された値と角度効果を組み合わせ
正規化された値をカラーマップに適用し、0-255の範囲に変換

## KEY_LOGIC_PATTERNS
複素ポテンシャルと角度情報を組み合わせた着色
エラーハンドリングによる安定性の確保

## CRITICAL_BEHAVIORS
非発散領域の着色処理


==============================
# MODULE_INFO:
convergence_speed.py

## MODULE_PURPOSE
非発散領域を収束速度で着色する

## CLASS_DEFINITION:
なし

## DEPENDENCIES
numpy (np)
typing
matplotlib.colors.Colormap
ui.zoom_function.debug_logger.DebugLogger
ui.zoom_function.enums.LogLevel

## MODULE_ATTRIBUTES
なし

## METHOD_SIGNATURES
def apply_convergence_speed(colored: np.ndarray, non_divergent_mask: np.ndarray, z_vals: np.ndarray, non_cmap_func: Colormap, params: Dict, logger: DebugLogger) -> None
機能: 非発散領域を収束速度で着色する

## CORE_EXECUTION_FLOW
複素数の絶対値の逆数を計算（収束速度）
0-1の範囲に正規化
ガンマ補正を適用して色の遷移を調整
正規化された値をカラーマップに適用し、0-255の範囲に変換

## KEY_LOGIC_PATTERNS
収束速度に基づく着色
ガンマ補正による視覚効果の調整

## CRITICAL_BEHAVIORS
非発散領域の着色処理


==============================
# MODULE_INFO:
derivative.py

## MODULE_PURPOSE
非発散領域を導関数で着色する

## CLASS_DEFINITION:
なし

## DEPENDENCIES
numpy (np)
typing
matplotlib.colors.Colormap
ui.zoom_function.debug_logger.DebugLogger
ui.zoom_function.enums.LogLevel

## MODULE_ATTRIBUTES
なし

## METHOD_SIGNATURES
def apply_derivative_coloring(colored: np.ndarray, non_divergent_mask: np.ndarray, z_vals: np.ndarray, non_cmap_func: Colormap, params: Dict, logger: DebugLogger) -> None
機能: 非発散領域を導関数で着色する

## CORE_EXECUTION_FLOW
複素数の導関数を計算
絶対値を計算して正規化
ガンマ補正を適用
正規化された値をカラーマップに適用し、0-255の範囲に変換

## KEY_LOGIC_PATTERNS
導関数の絶対値に基づく着色
エラーハンドリングによる安定性の確保

## CRITICAL_BEHAVIORS
非発散領域の着色処理


==============================
# MODULE_INFO:
fourier_pattern.py

## MODULE_PURPOSE
非発散領域をフーリエ干渉パターンで着色する

## CLASS_DEFINITION:
なし

## DEPENDENCIES
numpy (np)
typing
matplotlib.colors.Colormap
ui.zoom_function.debug_logger.DebugLogger
ui.zoom_function.enums.LogLevel

## MODULE_ATTRIBUTES
なし

## METHOD_SIGNATURES
def apply_fourier_pattern(colored: np.ndarray, non_divergent_mask: np.ndarray, z_vals: np.ndarray, non_cmap_func: Colormap, params: Dict, logger: DebugLogger) -> None
機能: 非発散領域をフーリエ干渉パターンで着色する

## CORE_EXECUTION_FLOW
非発散領域の複素数値の座標成分を取得
複数の正弦波および余弦波を組み合わせた干渉パターンを生成
正規化された値をカラーマップに適用し、0-255の範囲に変換

## KEY_LOGIC_PATTERNS
フーリエ変換に基づく干渉パターンの生成
複数の周波数成分の合成

## CRITICAL_BEHAVIORS
非発散領域の着色処理


==============================
# MODULE_INFO:
fractal_texture.py

## MODULE_PURPOSE
非発散領域をフラクタルテクスチャで Ascendinglyで着色する

## CLASS_DEFINITION:
なし

## DEPENDENCIES
numpy (np)
typing
matplotlib.colors.Colormap
ui.zoom_function.debug_logger.DebugLogger
ui.zoom_function.enums.LogLevel

## MODULE_ATTRIBUTES
なし

## METHOD_SIGNATURES
def apply_fractal_texture(colored: np.ndarray, non_divergent_mask: np.ndarray, z_vals: np.ndarray, non_cmap_func: Colormap, params: Dict, logger: DebugLogger) -> None
機能: 非発散領域をフラクタルテクスチャで着色する

## CORE_EXECUTION_FLOW
マルチオクターブノイズの生成
複数の周波数成分の合成
正規化された値をカラーマップに適用し、0-255の範囲に変換

## KEY_LOGIC_PATTERNS
マルチオクターブノイズによるテクスチャ生成
周波数成分の重み付け

## CRITICAL_BEHAVIORS
非発散領域の着色処理


==============================
# MODULE_INFO:
gradient_based.py

## MODULE_PURPOSE
非発散領域にグラデーションを適用して着色する

## CLASS_DEFINITION:
なし

## DEPENDENCIES
numpy (np)
typing
matplotlib.colors.Colormap
ui.zoom_function.debug_logger.DebugLogger
ui.zoom_function.enums.LogLevel
gradient.compute_gradient

## MODULE_ATTRIBUTES
なし

## METHOD_SIGNATURES
def apply_gradient_based(colored: np.ndarray, non_divergent_mask: np.ndarray, iterations: np.ndarray, gradient_values: np.ndarray, non_cmap_func: Colormap, params: Dict, logger: DebugLogger) -> None
機能: 非発散領域にグラデーションを適用して着色する

## CORE_EXECUTION_FLOW
グラデーションの計算
非発散領域にグラデーションを適用
正規化された値をカラーマップに適用し、0-255の範囲に変換

## KEY_LOGIC_PATTERNS
グラデーションの計算
パラメータによるグラデーションの制御

## CRITICAL_BEHAVIORS
非発散領域の着色処理


==============================
# MODULE_INFO:
histogram_equalization.py

## MODULE_PURPOSE
非発散領域をヒストグラム平坦化によって着色する

## CLASS_DEFINITION:
なし

## DEPENDENCIES
numpy (np)
typing
matplotlib.colors.Colormap
ui.zoom_function.debug_logger.DebugLogger
ui.zoom_function.enums.LogLevel

## MODULE_ATTRIBUTES
なし

## METHOD_SIGNATURES
def apply_histogram_equalization(colored: np.ndarray, non_divergent_mask: np.ndarray, iterations: np.ndarray, non_cmap_func: Colormap, params: Dict, logger: DebugLogger) -> None
機能: 非発散領域をヒストグラム平坦化によって着色する

## CORE_EXECUTION_FLOW
反復回数のヒストグラムの計算
累積分布関数の生成
ガンマ補正を適用
正規化された値をカラーマップに適用

## KEY_LOGIC_PATTERNS
ヒストグラム平坦化
累積分布関数の使用

## CRITICAL_BEHAVIORS
非発散領域の着色処理


==============================
# MODULE_INFO:
internal_distance.py

## MODULE_PURPOSE
非発散領域を内部距離に基づいて着色する

## CLASS_DEFINITION:
なし

## DEPENDENCIES
numpy (np)
typing
matplotlib.colors.Colormap
ui.zoom_function.debug_logger.DebugLogger
ui.zoom_function.enums.LogLevel

## MODULE_ATTRIBUTES
なし

## METHOD_SIGNATURES
def apply_internal_distance(colored: np.ndarray, non_divergent_mask: np.ndarray, z_vals: np.ndarray, non_cmap_func: Colormap, params: Dict, logger: DebugLogger) -> None
機能: 非発散領域を内部距離に基づいて着色する

## CORE_EXECUTION_FLOW
複素数の絶対値の計算
対数を取って正規化
正規化された値をカラーマップに適用

## KEY_LOGIC_PATTERNS
内部距離の計算
エラーハンドリングによる安定性の確保

## CRITICAL_BEHAVIORS
非発散領域の着色処理


==============================
# MODULE_INFO:
orbit_trap_circle.py

## MODULE_PURPOSE
非発散領域を軌道トラップ(円)で着色する

## CLASS_DEFINITION:
なし

## DEPENDENCIES
numpy (np)
typing
matplotlib.colors.Colormap
ui.zoom_function.debug_logger.DebugLogger
ui.zoom_function.enums.LogLevel

## MODULE_ATTRIBUTES
なし

## METHOD_SIGNATURES
def apply_orbit_trap_circle(colored: np.ndarray, non_divergent_mask: np.ndarray, z_vals: np.ndarray, non_cmap_func: Colormap, params: Dict, logger: DebugLogger) -> None
機能: 非発散領域を軌道トラップ(円)で着色する

## CORE_EXECUTION_FLOW
複素数の絶対値からトラップ円との距離を計算
距離を0-1の範囲に正規化
ガンマ補正を適用して明るさを調整
正規化された値をカラーマップに適用し、0-255の範囲に変換

## KEY_LOGIC_PATTERNS
軌道トラップの計算
距離に基づく着色

## CRITICAL_BEHAVIORS
非発散領域の着色処理


==============================
# MODULE_INFO:
palam_c_z.py

## MODULE_PURPOSE
非発散領域をパラメータ-C-Z法で着色する

## CLASS_DEFINITION:
なし

## DEPENDENCIES
numpy (np)
typing
matplotlib.colors.Colormap
ui.zoom_function.debug_logger.DebugLogger
ui.zoom_function.enums.LogLevel

## MODULE_ATTRIBUTES
なし

## METHOD_SIGNATURES
def apply_parameter_coloring(colored: np.ndarray, non_divergent_mask: np.ndarray, z_vals: np.ndarray, non_cmap_func: Colormap, params: Dict, logger: DebugLogger) -> None
機能: 非発散領域をパラメータ-C-Z法で着色する

## CORE_EXECUTION_FLOW
複素数の絶対値と偏角の計算
正規化とガンマ補正を適用
正規化された値をカラーマップに適用

## KEY_LOGIC_PATTERNS
パラメータ-C-Z法による着色
複素数の性質の利用

## CRITICAL_BEHAVIORS
非発散領域の着色処理


==============================
# MODULE_INFO:
phase_symmetry.py

## MODULE_PURPOSE
非発散領域を位相対称性で着色する

## CLASS_DEFINITION:
なし

## DEPENDENCIES
numpy (np)
typing
matplotlib.colors.Colormap
ui.zoom_function.debug_logger.DebugLogger
ui.zoom_function.enums.LogLevel

## MODULE_ATTRIBUTES
なし

## METHOD_SIGNATURES
def apply_phase_symmetry(colored: np.ndarray, non_divergent_mask: np.ndarray, z_vals: np.ndarray, non_cmap_func: Colormap, params: Dict, logger: DebugLogger) -> None
機能: 非発散領域を位相対称性で着色する

## CORE_EXECUTION_FLOW
複素数の偏角の計算
対称性に基づく着色値の生成
正規化とガンマ補正を適用
正規化された値をカラーマップに適用

## KEY_LOGIC_PATTERNS
位相対称性の利用
複素数の性質の利用

## CRITICAL_BEHAVIORS
非発散領域の着色処理


==============================
# MODULE_INFO:
quantum_entanglement.py

## MODULE_PURPOSE
非発散領域を量子絡み合いを模倣した方法で着色する

## CLASS_DEFINITION:
なし

## DEPENDENCIES
numpy (np)
typing
matplotlib.colors.Colormap
ui.zoom_function.debug_logger.DebugLogger
ui.zoom_function.enums.LogLevel

## MODULE_ATTRIBUTES
なし

## METHOD_SIGNATURES
def apply_quantum_entanglement(colored: np.ndarray, non_divergent_mask: np.ndarray, z_vals: np.ndarray, non_cmap_func: Colormap, params: Dict, logger: DebugLogger) -> None
機能: 非発散領域を量子絡み合いを模倣した方法で着色する

## CORE_EXECUTION_FLOW
複素数の絶対値と偏角の計算
量子状態の模倣
正規化とガンマ補正を適用
正規化された値をカラーマップに適用

## KEY_LOGIC_PATTERNS
量子絡み合いの模倣
複素数の性質の利用

## CRITICAL_BEHAVIORS
非発散領域の着色処理


==============================
# MODULE_INFO:
solid_color.py

## MODULE_PURPOSE
非発散領域を単色で着色する

## CLASS_DEFINITION:
なし

## DEPENDENCIES
numpy (np)
typing
ui.zoom_function.debug_logger.DebugLogger
ui.zoom_function.enums.LogLevel

## MODULE_ATTRIBUTES
なし

## METHOD_SIGNATURES
def apply_solid_color(colored: np.ndarray, non_divergent_mask: np.ndarray, params: Dict, logger: DebugLogger) -> None
機能: 非発散領域を単色で着色する

## CORE_EXECUTION_FLOW
マスク配列を使用して単色で非発散領域を塗りつぶす

## KEY_LOGIC_PATTERNS
単色塗りつぶし処理
マスク配列による領域指定

## CRITICAL_BEHAVIORS
非発散領域の着色処理
