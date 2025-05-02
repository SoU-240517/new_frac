==============================
# MODULE_INFO:
__init__.py

## MODULE_PURPOSE
non_divergent パッケージの初期化ファイル
- 非発散領域のカラーリングアルゴリズムを含むモジュールを公開する

## CLASS_DEFINITION:
なし

## DEPENDENCIES
なし

## MODULE_ATTRIBUTES
__version__: パッケージのバージョン番号

## METHOD_SIGNATURES
なし

## CORE_EXECUTION_FLOW
モジュールのインポート → __all__リストの設定

## KEY_LOGIC_PATTERNS
- モジュールのインポート: 各カラーリングアルゴリズムの関数をインポート
- __all__リスト: 公開する関数名のリストを定義

## CRITICAL_BEHAVIORS
- インポートの正確性
- __all__リストの正確性
- バージョン番号の正確性


==============================
# MODULE_INFO:
chaotic_orbit.py

## MODULE_PURPOSE
非発散領域をカオス軌道で着色する

## CLASS_DEFINITION:
なし

## DEPENDENCIES
numpy: 数値計算
matplotlib.colors.Colormap: カラーマップ
typing: 型ヒント
debug.DebugLogger: デバッグログ
debug.LogLevel: ログレベル定義

## MODULE_ATTRIBUTES
なし

## METHOD_SIGNATURES
def apply_chaotic_orbit(
    colored: np.ndarray,
    non_divergent_mask: np.ndarray,
    z_vals: np.ndarray,
    non_cmap_func: Colormap,
    params: Dict,
    logger: DebugLogger
) -> None
機能: 非発散領域をカオス軌道で着色する
引数:
- colored: 出力用のRGBA配列 (形状: (h, w, 4), dtype=float32)
- non_divergent_mask: 非発散点のマスク配列 (形状: (h, w), dtype=bool)
- z_vals: 複素数値の配列
- non_cmap_func: 非発散領域の着色に使用するカラーマップ関数
- params: 使用しない
- logger: デバッグ用ロガーインスタンス

## CORE_EXECUTION_FLOW
非発散点の複素数値から極座標系の値を計算 → カオス軌道の特徴を反映したRGB値の計算 → RGB値を0-1の範囲に正規化し、255倍して8bitカラーバリューに変換

## KEY_LOGIC_PATTERNS
- 極座標系への変換:
  - r: 複素数の絶対値（原点からの距離）
  - theta: 複素数の偏角（位相）
- RGB値の計算:
  - Red: np.sin(r * 5.0)**2
  - Green: (np.cos(theta * 3.0) + 1) / 2
  - Blue: (np.sin(r * 3.0 + theta * 2.0) + 1) / 2
- RGBA変換: 0〜1の範囲を0〜255に変換

## CRITICAL_BEHAVIORS
- 極座標系への変換の正確性
- RGB値計算の正確性
- RGBA変換の正確性


==============================
# MODULE_INFO:
complex_potential.py

## MODULE_PURPOSE
非発散領域を複素ポテンシャルで着色する

## CLASS_DEFINITION:
なし

## DEPENDENCIES
numpy: 数値計算
matplotlib.colors.Colormap: カラーマップ
typing: 型ヒント
debug.DebugLogger: デバッグログ
debug.LogLevel: ログレベル定義

## MODULE_ATTRIBUTES
なし

## METHOD_SIGNATURES
def apply_complex_potential(
    colored: np.ndarray,
    non_divergent_mask: np.ndarray,
    z_vals: np.ndarray,
    non_cmap_func: Colormap,
    params: Dict,
    logger: DebugLogger
) -> None
機能: 非発散領域を複素ポテンシャルで着色する
引数:
- colored: 出力用のRGBA配列 (形状: (h, w, 4), dtype=float32)
- non_divergent_mask: 非発散点のマスク配列 (形状: (h, w), dtype=bool)
- z_vals: 複素数値の配列
- non_cmap_func: 非発散領域の着色に使用するカラーマップ関数
- params: 使用しない
- logger: デバッグ用ロガーインスタンス

## CORE_EXECUTION_FLOW
複素数の絶対値の対数を計算（複素ポテンシャル） → 0-1の範囲に正規化 → 複素数の角度（位相）を計算して正規化 → 正規化された値と角度効果を組み合わせ → 正規化された値をカラーマップに適用し、0-255の範囲に変換

## KEY_LOGIC_PATTERNS
- 複素ポテンシャルの計算:
  - np.log()による対数計算
  - 1e-10の加算によるゼロ除算防止
  - np.nan_to_numによるNaNや無限大の処理
- 角度効果の計算:
  - np.angle()による角度計算
  - 2πによる正規化
- 組み合わせ処理:
  - normalizedと0.3 * angle_effectの加算
  - % 1.0による0-1範囲の確保
- RGBA変換: 0〜1の範囲を0〜255に変換

## CRITICAL_BEHAVIORS
- 複素ポテンシャルの計算の正確性
- 角度効果の計算の正確性
- 組み合わせ処理の正確性
- RGBA変換の正確性
- エラーハンドリングの適切性


==============================
# MODULE_INFO:
convergence_speed.py

## MODULE_PURPOSE
非発散領域を収束速度で着色する

## CLASS_DEFINITION:
なし

## DEPENDENCIES
numpy: 数値計算
matplotlib.colors.Colormap: カラーマップ
typing: 型ヒント
debug.DebugLogger: デバッグログ
debug.LogLevel: ログレベル定義

## MODULE_ATTRIBUTES
なし

## METHOD_SIGNATURES
def apply_convergence_speed(
    colored: np.ndarray,
    non_divergent_mask: np.ndarray,
    z_vals: np.ndarray,
    non_cmap_func: Colormap,
    params: Dict,
    logger: DebugLogger
) -> None
機能: 非発散領域を収束速度で着色する
引数:
- colored: 出力用のRGBA配列 (形状: (h, w, 4), dtype=float32)
- non_divergent_mask: 非発散点のマスク配列 (形状: (h, w), dtype=bool)
- z_vals: 複素数値の配列
- non_cmap_func: 非発散領域の着色に使用するカラーマップ関数
- params: 使用しない
- logger: デバッグ用ロガーインスタンス

## CORE_EXECUTION_FLOW
収束速度の計算 → 0-1の範囲に正規化 → ガンマ補正を適用して色の遷移を調整 → 正規化された値をカラーマップに適用し、0-255の範囲に変換

## KEY_LOGIC_PATTERNS
- 収束速度の計算:
  - 1/|z|による逆数計算
  - 1e-10の加算によるゼロ除算防止
- 正規化: 最小値と最大値による正規化
- ガンマ補正:
  - gamma = 1.5の設定
  - normalized ** (1/gamma)による補正
- RGBA変換: 0〜1の範囲を0〜255に変換

## CRITICAL_BEHAVIORS
- 収束速度の計算の正確性
- 正規化の正確性
- ガンマ補正の適切性
- RGBA変換の正確性


==============================
# MODULE_INFO:
derivative.py

## MODULE_PURPOSE
非発散領域を微分係数で着色する

## CLASS_DEFINITION:
なし

## DEPENDENCIES
numpy: 数値計算
matplotlib.colors.Colormap: カラーマップ
typing: 型ヒント
debug.DebugLogger: デバッグログ
debug.LogLevel: ログレベル定義

## MODULE_ATTRIBUTES
なし

## METHOD_SIGNATURES
def apply_derivative_coloring(
    colored: np.ndarray,
    non_divergent_mask: np.ndarray,
    z_vals: np.ndarray,
    non_cmap_func: Colormap,
    params: Dict,
    logger: DebugLogger
) -> None
機能: 非発散領域を微分係数で着色する
引数:
- colored: 出力用のRGBA配列 (形状: (h, w, 4), dtype=float32)
- non_divergent_mask: 非発散点のマスク配列 (形状: (h, w), dtype=bool)
- z_vals: 複素数値の配列
- non_cmap_func: 非発散領域の着色に使用するカラーマップ関数
- params: 使用しない
- logger: デバッグ用ロガーインスタンス

## CORE_EXECUTION_FLOW
微分係数の計算 → 対数計算 → 0-1の範囲に正規化 → ガンマ補正を適用 → 正規化された値をカラーマップに適用し、0-255の範囲に変換

## KEY_LOGIC_PATTERNS
- 微分係数の計算:
  - 2 * |z| * 0.5による計算
  - 0.5の係数による明るさ調整
- 対数計算:
  - np.log()による対数計算
  - 1e-10の加算によるゼロ除算防止
- 正規化: 最小値と最大値による正規化
- ガンマ補正:
  - gamma = 1.5の設定
  - normalized ** (1/gamma)による補正
- RGBA変換: 0〜1の範囲を0〜255に変換

## CRITICAL_BEHAVIORS
- 微分係数の計算の正確性
- 対数計算の正確性
- 正規化の正確性
- ガンマ補正の適切性
- RGBA変換の正確性


==============================
# MODULE_INFO:
fourier_pattern.py

## MODULE_PURPOSE
非発散領域をフーリエ干渉パターンで着色する

## CLASS_DEFINITION:
なし

## DEPENDENCIES
numpy: 数値計算
matplotlib.colors.Colormap: カラーマップ
typing: 型ヒント
debug.DebugLogger: デバッグログ
debug.LogLevel: ログレベル定義

## MODULE_ATTRIBUTES
なし

## METHOD_SIGNATURES
def apply_fourier_pattern(
    colored: np.ndarray,
    non_divergent_mask: np.ndarray,
    z_vals: np.ndarray,
    non_cmap_func: Colormap,
    params: Dict,
    logger: DebugLogger
) -> None
機能: 非発散領域をフーリエ干渉パターンで着色する
引数:
- colored: 出力用のRGBA配列 (形状: (h, w, 4), dtype=float32)
- non_divergent_mask: 非発散点のマスク配列 (形状: (h, w), dtype=bool)
- z_vals: 複素数値の配列
- non_cmap_func: 非発散領域の着色に使用するカラーマップ関数
- params: 使用しない
- logger: デバッグ用ロガーインスタンス

## CORE_EXECUTION_FLOW
非発散点の実部と虚部の取得 → 干渉パターンの生成 → 0-1の範囲に正規化 → 正規化された値をカラーマップに適用し、0-255の範囲に変換

## KEY_LOGIC_PATTERNS
- 干渉パターンの生成:
  - 実部と虚部の取得 (np.real, np.imag)
  - 正弦波と余弦波の組み合わせ:
    - np.sin(x * 10.0) * np.cos(y * 8.0)
    - np.sin(x * 5.0 + y * 3.0)
  - 周波数の選択: 10.0, 8.0, 5.0, 3.0
  - 干渉パターンの合成: 2つの波形の和を2で割る
- 正規化: 最小値と最大値による正規化
- RGBA変換: 0〜1の範囲を0〜255に変換

## CRITICAL_BEHAVIORS
- 干渉パターンの生成の正確性
- 正規化の正確性
- RGBA変換の正確性


==============================
# MODULE_INFO:
fractal_texture.py

## MODULE_PURPOSE
非発散領域をフラクタルテクスチャで Ascendinglyで着色する

## CLASS_DEFINITION:
なし

## DEPENDENCIES
numpy: 数値計算
matplotlib.colors.Colormap: カラーマップ
typing: 型ヒント
debug.DebugLogger: デバッグログ
debug.LogLevel: ログレベル定義

## MODULE_ATTRIBUTES
なし

## METHOD_SIGNATURES
def apply_fractal_texture(
    colored: np.ndarray,
    non_divergent_mask: np.ndarray,
    z_vals: np.ndarray,
    non_cmap_func: Colormap,
    params: Dict,
    logger: DebugLogger
) -> None
機能: 非発散領域をフラクタルテクスチャで着色する
引数:
- colored: 出力用のRGBA配列 (形状: (h, w, 4), dtype=float32)
- non_divergent_mask: 非発散点のマスク配列 (形状: (h, w), dtype=bool)
- z_vals: 複素数値の配列
- non_cmap_func: 非発散領域の着色に使用するカラーマップ関数
- params: 使用しない
- logger: デバッグ用ロガーインスタンス

## CORE_EXECUTION_FLOW
ノイズ生成関数の定義 → 非発散点の複素数座標の取得 → マルチオクターブノイズの生成 → 0-1の範囲に正規化 → 正規化された値をカラーマップに適用し、0-255の範囲に変換

## KEY_LOGIC_PATTERNS
- ノイズ生成:
  - noise関数の定義 (np.sin * np.cos)
  - スケールパラメータによる制御
- マルチオクターブノイズ:
  - 5.0: 基本周波数成分
  - 10.0: 第2周波数成分 (振幅0.5)
  - 20.0: 第3周波数成分 (振幅0.25)
  - 3つのノイズの和による合成
- 正規化: 最小値と最大値による正規化
- RGBA変換: 0〜1の範囲を0〜255に変換

## CRITICAL_BEHAVIORS
- ノイズ生成の正確性
- マルチオクターブノイズの合成の正確性
- 正規化の正確性
- RGBA変換の正確性


==============================
# MODULE_INFO:
gradient_based.py

## MODULE_PURPOSE
非発散領域にグラデーションを適用して着色する

## CLASS_DEFINITION:
なし

## DEPENDENCIES
numpy: 数値計算
matplotlib.colors.Colormap: カラーマップ
typing: 型ヒント
debug.DebugLogger: デバッグログ
debug.LogLevel: ログレベル定義
coloring.gradient.compute_gradient: グラデーション計算

## MODULE_ATTRIBUTES
なし

## METHOD_SIGNATURES
def apply_gradient_based(
    colored: np.ndarray,
    non_divergent_mask: np.ndarray,
    iterations: np.ndarray,
    gradient_values: np.ndarray,
    non_cmap_func: Colormap,
    params: Dict,
    logger: DebugLogger
) -> None
機能: 非発散領域にグラデーションを適用して着色する
引数:
- colored: 出力用のRGBA配列 (形状: (h, w, 4), dtype=float32)
- non_divergent_mask: 非発散点のマスク配列 (形状: (h, w), dtype=bool)
- iterations: 反復回数配列
- gradient_values: グラデーション値配列
- non_cmap_func: 非発散領域の着色に使用するカラーマップ関数
- params: グラデーションのパラメータ
  - gradient_type (str): グラデーションの種類 ('linear' または 'radial')
  - gradient_size (int): グラデーションのサイズ
  - gradient_position (Tuple[int, int]): グラデーションの中心座標 (x, y)
- logger: デバッグ用ロガーインスタンス

## CORE_EXECUTION_FLOW
グラデーションの計算 → 非発散領域にグラデーションを適用 → 正規化された値をカラーマップに適用し、0-255の範囲に変換

## KEY_LOGIC_PATTERNS
- グラデーション計算:
  - compute_gradient関数の使用
  - 形状に基づくグラデーション生成
- グラデーションパラメータ:
  - gradient_type: 'linear' または 'radial'
  - gradient_size: グラデーションのサイズ
  - gradient_position: グラデーションの中心座標
- RGBA変換: 0〜1の範囲を0〜255に変換

## CRITICAL_BEHAVIORS
- グラデーション計算の正確性
- グラデーションパラメータの適切な処理
- RGBA変換の正確性


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
debug.DebugLogger
debug.LogLevel

## MODULE_ATTRIBUTES
なし

## METHOD_SIGNATURES
def apply_histogram_equalization(
    colored: np.ndarray,
    non_divergent_mask: np.ndarray,
    iterations: np.ndarray,
    non_cmap_func: Colormap,
    params: Dict,
    logger: DebugLogger
) -> None
機能: 非発散領域をヒストグラム平坦化によって着色する

## CORE_EXECUTION_FLOW
1. 非発散領域の反復回数のヒストグラムを計算（256ビンを使用）
2. ヒストグラムの累積分布関数（CDF）を計算し、0-1の範囲に正規化
3. ガンマ補正（gamma=1.5）を適用して色の遷移を調整
4. 正規化されたCDFを使用して反復回数を新しい値にマッピング
5. 正規化された値をカラーマップに適用し、0-255の範囲に変換

## KEY_LOGIC_PATTERNS
- ヒストグラム平坦化による反復回数の均等化
- 累積分布関数（CDF）の使用による正規化
- ガンマ補正による色の遷移調整
- NumPyのinterp関数を使用した値のマッピング

## CRITICAL_BEHAVIORS
- 非発散領域の反復回数分布を均等化して可視化
- ガンマ補正による自然な色の遷移
- NumPyの高速な配列演算を活用した効率的な処理


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
debug.DebugLogger
debug.LogLevel

## MODULE_ATTRIBUTES
なし

## METHOD_SIGNATURES
def apply_internal_distance(
    colored: np.ndarray,
    non_divergent_mask: np.ndarray,
    z_vals: np.ndarray,
    non_cmap_func: Colormap,
    params: Dict,
    logger: DebugLogger
) -> None
機能: 非発散領域を内部距離に基づいて着色する

## CORE_EXECUTION_FLOW
1. 複素数値の絶対値を計算（0除算を避けるため微小値を加算）
2. 対数を取って正規化（対数の底は2を使用）
3. 0-1の範囲に正規化
4. 正規化された値をカラーマップに適用し、0-255の範囲に変換

## KEY_LOGIC_PATTERNS
- 内部距離の計算（複素数の絶対値を使用）
- NumPyのerrstateを使用したエラーハンドリング
- 対数スケールによる距離の正規化
- 境界近さの可視化（値が大きいほど境界に近い）

## CRITICAL_BEHAVIORS
- 非発散領域の内部距離を計算して可視化
- エラーハンドリングによる安定した計算
- 対数スケールによる効果的な距離表現
- 境界近さの正確な可視化


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
debug.DebugLogger
debug.LogLevel

## MODULE_ATTRIBUTES
なし

## METHOD_SIGNATURES
def apply_orbit_trap_circle(
    colored: np.ndarray,
    non_divergent_mask: np.ndarray,
    z_vals: np.ndarray,
    non_cmap_func: Colormap,
    params: Dict,
    logger: DebugLogger
) -> None
機能: 非発散領域を軌道トラップ(円)で着色する

## CORE_EXECUTION_FLOW
1. 複素数の絶対値からトラップ円との距離を計算（トラップ円の半径R=1.4）
2. 距離を0-1の範囲に正規化（1-（距離/最大距離））
3. ガンマ補正を適用して明るさを調整（gamma=1.0）
4. 正規化された値をカラーマップに適用し、0-255の範囲に変換

## KEY_LOGIC_PATTERNS
- 軌道トラップの計算（複素数の絶対値とトラップ円との距離）
- 距離の正規化（1-（距離/最大距離）の形式）
- ガンマ補正による明るさ調整
- トラップ円の半径による形状制御

## CRITICAL_BEHAVIORS
- 非発散領域の軌道トラップによる着色
- トラップ円との距離に基づく明るさ調整
- 半径1.4のトラップ円を使用した形状強調
- ガンマ補正による自然な明るさ遷移


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
debug.DebugLogger
debug.LogLevel

## MODULE_ATTRIBUTES
なし

## METHOD_SIGNATURES
def apply_parameter_coloring(
    colored: np.ndarray,
    non_divergent_mask: np.ndarray,
    z_vals: np.ndarray,
    non_cmap_func: Colormap,
    params: Dict,
    logger: DebugLogger
) -> None
機能: 非発散領域をパラメータ-C-Z法で着色する

## CORE_EXECUTION_FLOW
1. 着色アルゴリズムの選択（パラメータCまたはパラメータZ）
2. Julia集合の場合:
   - 複素数Cの偏角を計算（0-1の範囲に正規化）
   - カラーマップを使って色を取得
   - 非発散部分を同じ色で塗りつぶす
3. Mandelbrot集合の場合:
   - 黒で塗りつぶす（または指定されたデフォルト色）
4. パラメータZの場合:
   - Zの実部と虚部から偏角を計算（0-1の範囲に正規化）
   - カラーマップを使って色を取得
   - 非発散部分を塗りつぶす

## KEY_LOGIC_PATTERNS
- パラメータCによる着色（複素数Cの偏角を使用）
- パラメータZによる着色（最終的な複素数Zの偏角を使用）
- Julia集合とMandelbrot集合の異なる処理
- 偏角の正規化（0-1の範囲）
- カラーマップの適用

## CRITICAL_BEHAVIORS
- 非発散領域のパラメータ-C-Z法による着色
- Julia集合とMandelbrot集合の適切な着色処理
- 偏角に基づく色の変化
- カラーマップによる効果的な可視化


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
debug.DebugLogger
debug.LogLevel

## MODULE_ATTRIBUTES
なし

## METHOD_SIGNATURES
def apply_phase_symmetry(
    colored: np.ndarray,
    non_divergent_mask: np.ndarray,
    z_vals: np.ndarray,
    non_cmap_func: Colormap,
    params: Dict,
    logger: DebugLogger
) -> None
機能: 非発散領域を位相対称性で着色する

## CORE_EXECUTION_FLOW
1. 複素数の位相（角度）を取得（[-π, π)の範囲）
2. 位相を対称性の次数で正規化（symmetry_order=5）
   - 2πをsymmetry_orderで分割
   - 0-1の範囲に正規化
3. ガンマ補正を適用（gamma=1.5）
4. 正規化された値をカラーマップに適用し、0-255の範囲に変換

## KEY_LOGIC_PATTERNS
- 位相対称性の利用（symmetry_order=5による5重対称性）
- 複素数の位相（角度）の正規化
- ガンマ補正による色の遷移調整
- 対称性によるパターン生成

## CRITICAL_BEHAVIORS
- 非発散領域の位相対称性による着色
- 5重対称性によるパターン生成
- ガンマ補正による自然な色の遷移
- 位相に基づく効果的な可視化


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
debug.DebugLogger
debug.LogLevel

## MODULE_ATTRIBUTES
なし

## METHOD_SIGNATURES
def apply_quantum_entanglement(
    colored: np.ndarray,
    non_divergent_mask: np.ndarray,
    z_vals: np.ndarray,
    non_cmap_func: Colormap,
    params: Dict,
    logger: DebugLogger
) -> None
機能: 非発散領域を量子絡み合いを模倣した方法で着色する

## CORE_EXECUTION_FLOW
1. 複素数の実部と虚部の抽出
2. 値の標準化（scale=2.0）
3. 量子パターンの生成：
   - sin: 量子的な振動を表現
   - cos: 量子的な干渉を表現
   - arctan2: 量子的な位相関係を表現
4. NaN値の処理とスケーリング
5. ガンマ補正を適用（gamma=1.8）
6. 正規化された値をカラーマップに適用し、0-255の範囲に変換

## KEY_LOGIC_PATTERNS
- 量子絡み合いの模倣
- 複素数の実部と虚部の利用
- 量子的な振動と干渉の表現
- 位相関係の考慮
- NumPyのerrstateを使用した安定性確保

## CRITICAL_BEHAVIORS
- 非発散領域の量子絡み合い風パターンによる着色
- 量子的な振動と干渉の表現
- 位相関係に基づくパターン生成
- ガンマ補正による自然な色の遷移
- 安定性確保


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
debug.DebugLogger
debug.LogLevel

## MODULE_ATTRIBUTES
なし

## METHOD_SIGNATURES
def apply_solid_color(
    colored: np.ndarray,
    non_divergent_mask: np.ndarray,
    params: Dict,
    logger: DebugLogger
) -> None
機能: 非発散領域を単色で着色する

## CORE_EXECUTION_FLOW
1. マスク配列を使用して非発散領域を特定
2. 固定の黒色（R=0, G=0, B=0, A=255）で塗りつぶし
3. RGBA配列に直接色を代入

## KEY_LOGIC_PATTERNS
- 単色塗りつぶし処理（黒色固定）
- マスク配列による領域指定
- RGBA形式の色指定

## CRITICAL_BEHAVIORS
- 非発散領域の単色塗りつぶし
- 黒色（不透明）による着色
- マスク配列による効率的な処理
