==============================
# MODULE_INFO:
__init__.py

## MODULE_PURPOSE
coloring.non_divergent パッケージの初期化ファイル

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
収束速度の計算
速度を0-1の範囲に正規化
ガンマ補正を適用して色の遷移を調整
正規化された値をカラーマップに適用し、0-255の範囲に変換

## KEY_LOGIC_PATTERNS
収束速度に基づく着色
ガンマ補正による視覚的な調整

## CRITICAL_BEHAVIORS
非発散領域の着色処理

==============================
# MODULE_INFO:
derivative.py

## MODULE_PURPOSE
非発散領域を微分係数で着色する

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
機能: 非発散領域を微分係数で着色する

## CORE_EXECUTION_FLOW
マンデルブロ集合の微分係数を計算
微分係数の対数を計算
0-1の範囲に正規化
ガンマ補正を適用して色の遷移を調整
正規化された値をカラーマップに適用し、0-255の範囲に変換

## KEY_LOGIC_PATTERNS
微分係数に基づく着色
対数変換とガンマ補正による視覚的な強調

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
生成されたパターンを0-1の範囲に正規化
正規化された値をカラーマップに適用し、0-255の範囲に変換

## KEY_LOGIC_PATTERNS
複素数値の座標成分を用いた干渉パターンの生成
NumPy配列操作による効率的な処理

## CRITICAL_BEHAVIORS
非発散領域の着色処理

==============================
# MODULE_INFO:
fractal_texture.py

## MODULE_PURPOSE
非発散領域をフラクタルテクスチャで着色する

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
機能: 非発散領域をマルチオクターブノイズを使用したフラクタルテクスチャで着色する

## CORE_EXECUTION_FLOW
ノイズ生成関数を定義
非発散点の複素数座標を取得
マルチオクターブノイズを生成（異なるスケールと重みでノイズを生成し、組み合わせる）
ノイズ値を0-1の範囲に正規化
正規化された値をカラーマップに適用し、0-255の範囲に変換

## KEY_LOGIC_PATTERNS
マルチオクターブノイズによるテクスチャ生成
異なるスケールのノイズを合成

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
機能: 指定されたパラメータに基づいてグラデーションを計算し、非発散領域に着色する

## CORE_EXECUTION_FLOW
グラデーションを計算
非発散領域にグラデーションを適用

## KEY_LOGIC_PATTERNS
グラデーションの種類（線形または放射状）、サイズ、位置をパラメータで指定
非発散領域へのグラデーション適用

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
機能: 非発散領域の反復回数の分布を均等化し、その結果を用いて着色を行う

## CORE_EXECUTION_FLOW
非発散領域の反復回数のヒストグラムを計算
ヒストグラムの累積分布関数（CDF）を計算し、0-1の範囲に正規化
ガンマ補正を適用して色の遷移を調整
正規化されたCDFを使用して反復回数を新しい値にマッピング
正規化された値をカラーマップに適用し、0-255の範囲に変換

## KEY_LOGIC_PATTERNS
ヒストグラム平坦化による色の均等化
ガンマ補正による視覚的な調整

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
機能: 各ピクセルの複素数値から内部距離を計算し、それに基づいて色を割り当てる

## CORE_EXECUTION_FLOW
z_valsの絶対値を計算
対数を取って正規化
0-1の範囲に正規化
カラーマップを適用

## KEY_LOGIC_PATTERNS
複素数値の絶対値に基づく内部距離の計算
対数変換による正規化

## CRITICAL_BEHAVIORS
非発散領域の着色処理


==============================
# MODULE_INFO:
orbit_trap_circle.py

## MODULE_PURPOSE
非発散領域を軌道トラップ（円）で着色する

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
機能: 複素数の軌道が特定の形状（この場合は円）に近づいた距離を計算し、その距離に基づいて着色を行う

## CORE_EXECUTION_FLOW
複素数の絶対値からトラップ円との距離を計算
距離を0-1の範囲に正規化
正規化された値をカラーマップに適用し、0-255の範囲に変換

## KEY_LOGIC_PATTERNS
軌道トラップを用いた着色
NumPy配列操作による効率的な処理

## CRITICAL_BEHAVIORS
非発散領域の着色処理

==============================
# MODULE_INFO:
palam_c_z.py

## MODULE_PURPOSE
非発散領域をパラメータCまたは最終的な複素数Zの値の角度で着色する

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
機能: 非発散領域をパラメータCの角度または最終的な複素数Zの値の角度を使用して着色する

## CORE_EXECUTION_FLOW
Julia集合の場合、複素数Cの角度（偏角）を計算して正規化し、カラーマップで着色
Mandelbrot集合の場合、黒で塗りつぶすか、別のデフォルト色を使用

## KEY_LOGIC_PATTERNS
Julia集合とMandelbrot集合で異なる着色処理
複素数の角度情報の利用

## CRITICAL_BEHAVIORS
非発散領域の着色処理

==============================
# MODULE_INFO:
phase_symmetry.py

## MODULE_PURPOSE
非発散領域を位相対称性に基づいて着色する

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
機能: 複素数の位相（角度）における対称性を用いて非発散領域を着色する

## CORE_EXECUTION_FLOW
複素数の位相（角度）を取得
角度を0-1の範囲に正規化
正規化された値をカラーマップに適用し、0-255の範囲に変換

## KEY_LOGIC_PATTERNS
複素数の位相に基づく対称性の利用
NumPy配列操作による効率的な処理

## CRITICAL_BEHAVIORS
非発散領域の着色処理

==============================
# MODULE_INFO:
quantum_entanglement.py

## MODULE_PURPOSE
非発散領域を量子もつれ風のパターンで着色する

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
機能: 複素数の実部と虚部を用いて量子的なパターンを生成し、非発散領域を着色する

## CORE_EXECUTION_FLOW
複素数の実部と虚部を抽出
実部と虚部の分布を標準化
量子的なパターンを生成
生成されたパターンを0-1の範囲に正規化
正規化された値をカラーマップに適用し、0-255の範囲に変換

## KEY_LOGIC_PATTERNS
複素数の実部と虚部を用いた量子的なパターン生成
NumPy配列操作と数学関数によるパターン計算

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
機能: フラクタル集合の非発散領域を指定された単色で塗りつぶす

## CORE_EXECUTION_FLOW
非発散領域を示すマスク配列に基づいて、指定された単色で塗りつぶす

## KEY_LOGIC_PATTERNS
単色塗りつぶし処理
マスク配列による領域指定

## CRITICAL_BEHAVIORS
非発散領域の着色処理
