==============================
# MODULE_INFO:
__init__.py

## MODULE_PURPOSE
divergentパッケージの初期化と公開インターフェースの定義

## CLASS_DEFINITION:
(クラス定義なし)

## DEPENDENCIES
- angle.py
- distance.py
- histogram.py
- linear.py
- logarithmic.py
- orbit_trap.py
- potential.py
- smoothing.py

## CLASS_ATTRIBUTES
(クラス属性なし)

## METHOD_SIGNATURES
(メソッドなし)

## CORE_EXECUTION_FLOW
- パッケージの公開インターフェースを定義
- 各着色アルゴリズム関数をインポート

## KEY_LOGIC_PATTERNS
- 発散点の着色アルゴリズムの公開
- モジュール間の依存関係管理

## CRITICAL_BEHAVIORS
- 発散点の着色アルゴリズムの正確な公開
- モジュール間の依存関係の維持


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
typing: 型ヒント (Dict, Tuple)
matplotlib.colors.Colormap: カラーマップ
debug.DebugLogger: デバッグログ管理
debug.LogLevel: ログレベル定義
coloring.utils: ユーティリティ関数

## CLASS_ATTRIBUTES
(クラス属性なし)

## METHOD_SIGNATURES
def apply_angle_coloring(
    colored: np.ndarray,
    divergent_mask: np.ndarray,
    z_vals: np.ndarray,
    cmap_func: Colormap,
    params: Dict,
    logger: DebugLogger
) -> None
機能: 複素数の偏角を計算し、カラーマップを用いて着色する
引数:
- colored: 出力先のRGBA配列 (形状: (h, w, 4), dtype=float32)
- divergent_mask: 発散した点のマスク配列 (形状: (h, w), dtype=bool)
- z_vals: 各点での複素数の値を持つ配列 (形状: (h, w), dtype=complex)
- cmap_func: 発散領域の着色に使うカラーマップ関数
- params: 使用しない
- logger: デバッグ用ロガー

## CORE_EXECUTION_FLOW
偏角計算 → 正規化 → カラーマップ適用

## KEY_LOGIC_PATTERNS
- 偏角計算: np.angle()による角度計算と正規化
- カラーマップ適用: 発散点にカラーマップを適用
- 発散点のみの着色: divergent_maskを使用
- RGBA変換: 0〜1の範囲を0〜255に変換

## CRITICAL_BEHAVIORS
- 偏角計算の正確性
- 正規化の正確性
- カラーマップ適用の正確性
- 発散点の適切な着色
- RGBA変換の正確性


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
typing: 型ヒント (Dict, Tuple)
matplotlib.colors.Colormap: カラーマップ
debug.DebugLogger: デバッグログ管理
debug.LogLevel: ログレベル定義
coloring.utils: ユーティリティ関数

## CLASS_ATTRIBUTES
(クラス属性なし)

## METHOD_SIGNATURES
def apply_distance_coloring(
    colored: np.ndarray,
    divergent_mask: np.ndarray,
    z_vals: np.ndarray,
    cmap_func: Colormap,
    params: Dict,
    logger: DebugLogger
) -> None
機能: 発散領域に対して、原点からの距離に基づいたカラーリングを適用する
引数:
- colored: 出力先のRGBA配列 (形状: (h, w, 4), dtype=float32)
- divergent_mask: 発散した点のマスク配列 (形状: (h, w), dtype=bool)
- z_vals: 各点での複素数の値を持つ配列 (形状: (h, w), dtype=complex)
- cmap_func: 発散領域の着色に使うカラーマップ関数
- params: 使用しない
- logger: デバッグ用ロガー

## CORE_EXECUTION_FLOW
距離計算 → 正規化 → カラーマップ適用

## KEY_LOGIC_PATTERNS
- 距離計算: np.abs()による複素数の絶対値計算
- 正規化: 最小値と最大値による正規化
- 発散点のみの着色: divergent_maskを使用
- 特殊ケース処理:
  - 距離が全て同じ場合: 0.5の値を使用
  - 発散点がない場合: 全て0に設定
- RGBA変換: 0〜1の範囲を0〜255に変換

## CRITICAL_BEHAVIORS
- 距離計算の正確性
- 正規化の正確性
- 発散点の適切な着色
- 特殊ケースの適切な処理
- RGBA変換の正確性


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
typing: 型ヒント (Dict, Tuple)
matplotlib.colors.Colormap: カラーマップ
debug.DebugLogger: デバッグログ管理
debug.LogLevel: ログレベル定義

## CLASS_ATTRIBUTES
(クラス属性なし)

## METHOD_SIGNATURES
def apply_histogram_flattening(
    colored: np.ndarray,
    divergent_mask: np.ndarray,
    iterations: np.ndarray,
    cmap_func: Colormap,
    params: Dict,
    logger: DebugLogger
) -> None
機能: 発散領域に対して、ヒストグラム平坦化に基づくカラーリングを適用する
引数:
- colored: 出力先のRGBA配列 (形状: (h, w, 4), dtype=float32)
- divergent_mask: 発散した点のマスク配列 (形状: (h, w), dtype=bool)
- iterations: 各点での反復回数を持つ配列 (形状: (h, w), dtype=int)
- cmap_func: 発散領域の着色に使うカラーマップ関数
- params: 計算パラメータを含む辞書。'max_iterations'キーが必要
- logger: デバッグ用ロガー

## CORE_EXECUTION_FLOW
ヒストグラム計算 → 累積分布関数計算 → カラーマップ適用

## KEY_LOGIC_PATTERNS
- ヒストグラム計算: np.histogramによる確率密度関数の計算
- 累積分布関数計算: cumsumによる累積和計算と正規化
- リマッピング: np.interpによる線形補間
- 発散点のみの着色: divergent_maskを使用
- RGBA変換: 0〜1の範囲を0〜255に変換

## CRITICAL_BEHAVIORS
- ヒストグラム計算の正確性
- 累積分布関数計算の正確性
- リマッピングの正確性
- 発散点の適切な着色
- RGBA変換の正確性


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
debug.DebugLogger: デバッグログ管理
debug.LogLevel: ログレベル定義
coloring.utils: ユーティリティ関数

## CLASS_ATTRIBUTES
(クラス属性なし)

## METHOD_SIGNATURES
def apply_linear_mapping(
    colored: np.ndarray,
    divergent_mask: np.ndarray,
    iterations: np.ndarray,
    cmap_func: Colormap,
    params: Dict,
    logger: DebugLogger
) -> None
機能: 発散領域に対して、反復回数に基づく線形マッピングでカラーリングを適用する
引数:
- colored: 出力先のRGBA配列 (形状: (h, w, 4), dtype=float32)
- divergent_mask: 発散した点のマスク配列 (形状: (h, w), dtype=bool)
- iterations: 各点での反復回数を持つ配列 (形状: (h, w), dtype=int)
- cmap_func: 発散領域の着色に使うカラーマップ関数
- params: 計算パラメータを含む辞書。'max_iterations'キーが必要
- logger: デバッグ用ロガー

## CORE_EXECUTION_FLOW
反復回数の正規化 → カラーマップ適用

## KEY_LOGIC_PATTERNS
- 反復回数の正規化: Normalizeによる1からmax_iterationsの範囲への正規化
- カラーマップ適用: 正規化された値にカラーマップを適用
- 発散点のみの着色: divergent_maskを使用
- 特殊ケース処理: 発散点がない場合の適切な処理
- RGBA変換: 0〜1の範囲を0〜255に変換

## CRITICAL_BEHAVIORS
- 反復回数の正規化の正確性
- カラーマップ適用の正確性
- 発散点の適切な着色
- 特殊ケースの適切な処理
- RGBA変換の正確性


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
debug.DebugLogger: デバッグログ
debug.LogLevel: ログレベル定義
coloring.utils._normalize_and_color: 正規化と着色

## CLASS_ATTRIBUTES
(クラス属性なし)

## METHOD_SIGNATURES
def apply_logarithmic_mapping(
    colored: np.ndarray,
    divergent_mask: np.ndarray,
    iterations: np.ndarray,
    cmap_func: Colormap,
    params: Dict,
    logger: DebugLogger
) -> None
機能: 発散領域に対して、反復回数の対数に基づくカラーリングを適用する
引数:
- colored: 出力先のRGBA配列 (形状: (h, w, 4), dtype=float32)
- divergent_mask: 発散した点のマスク配列 (形状: (h, w), dtype=bool)
- iterations: 各点での反復回数を持つ配列 (形状: (h, w), dtype=int)
- cmap_func: 発散領域の着色に使うカラーマップ関数
- params: 計算パラメータを含む辞書。'max_iterations'キーが必要
- logger: デバッグ用ロガー

## CORE_EXECUTION_FLOW
対数計算 → 正規化 → カラーマップ適用

## KEY_LOGIC_PATTERNS
- 対数計算: np.log()による対数計算
- 正規化: Normalizeによる正規化
- 発散点のみの着色: divergent_maskを使用
- 特殊ケース処理:
  - 発散点がない場合の処理
  - max_iterations <= 1の場合の調整
  - log(0)による-infやnanの処理
  - 有限値の除外処理
- エラーハンドリング: 計算エラー時の適切な処理
- RGBA変換: 0〜1の範囲を0〜255に変換

## CRITICAL_BEHAVIORS
- 対数計算の正確性
- 正規化の正確性
- 無限値や NaN の除外処理の正確性
- 発散点の適切な着色
- 特殊ケースの適切な処理
- エラーハンドリングの正確性
- RGBA変換の正確性


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
debug.DebugLogger: デバッグログ
debug.LogLevel: ログレベル定義
coloring.utils._normalize_and_color: 正規化と着色

## CLASS_ATTRIBUTES
(クラス属性なし)

## METHOD_SIGNATURES
def apply_orbit_trap(
    colored: np.ndarray,
    divergent_mask: np.ndarray,
    iterations: np.ndarray,
    z_vals: np.ndarray,
    cmap_func: Colormap,
    params: Dict,
    logger: DebugLogger
) -> None
機能: 発散領域に対して、軌道トラップ法に基づくカラーリングを適用する
引数:
- colored: 出力先のRGBA配列 (形状: (h, w, 4), dtype=float32)
- divergent_mask: 発散した点のマスク配列 (形状: (h, w), dtype=bool)
- iterations: 各点での反復回数を持つ配列 (形状: (h, w), dtype=int)
- z_vals: 各点での複素数の値を持つ配列 (形状: (h, w), dtype=complex)
- cmap_func: 発散領域の着色に使うカラーマップ関数
- params: 軌道トラップのパラメータを含む辞書
  - trap_type (str, optional): トラップの形状。'circle', 'square', 'cross', 'triangle' のいずれか。デフォルトは 'circle'
  - trap_size (float, optional): トラップのサイズ。デフォルトは 0.5
  - trap_position (Tuple[float, float], optional): トラップの中心座標 (x, y)。デフォルトは (0.0, 0.0)
- logger: デバッグ用ロガー

## CORE_EXECUTION_FLOW
トラップ中心の複素数変換 → トラップ形状に応じた距離計算 → 正規化 → カラーマップ適用

## KEY_LOGIC_PATTERNS
- トラップ中心の複素数変換: 複素数を使用
- トラップ形状に応じた距離計算:
  - 円形トラップ: np.abs()による距離計算
  - 正方形トラップ: np.maximumによる距離計算
  - 十字トラップ: np.minimumによる距離計算
  - 三角形トラップ: np.cos()による角度補正付き距離計算
- 正規化: 最小値と最大値による正規化
- 特殊ケース処理:
  - 発散点がない場合の処理
  - 無限大距離の処理
  - デバッグログの出力
- RGBA変換: 0〜1の範囲を0〜255に変換

## CRITICAL_BEHAVIORS
- トラップ中心の複素数変換の正確性
- トラップ形状ごとの距離計算の正確性
- 正規化の正確性
- 特殊ケースの適切な処理
- デバッグログの正確な出力
- RGBA変換の正確性


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
debug.DebugLogger: デバッグログ
debug.LogLevel: ログレベル定義
coloring.utils._normalize_and_color: 正規化と着色

## CLASS_ATTRIBUTES
(クラス属性なし)

## METHOD_SIGNATURES
def apply_potential(
    colored: np.ndarray,
    divergent_mask: np.ndarray,
    z_vals: np.ndarray,
    cmap_func: Colormap,
    params: Dict,
    logger: DebugLogger
) -> None
機能: 発散領域に対して、ポテンシャル関数法に基づくカラーリングを適用する
引数:
- colored: 出力先のRGBA配列 (形状: (h, w, 4), dtype=float32)
- divergent_mask: 発散した点のマスク配列 (形状: (h, w), dtype=bool)
- z_vals: 各点での複素数の値を持つ配列 (形状: (h, w), dtype=complex)
- cmap_func: 発散領域の着色に使うカラーマップ関数
- params: 使用しない
- logger: デバッグ用ロガー

## CORE_EXECUTION_FLOW
ポテンシャル計算 → 正規化 → カラーマップ適用 → 発散していない点の黒への設定

## KEY_LOGIC_PATTERNS
- ポテンシャル計算: np.log()による対数計算とlog(2)の補正
- 正規化: 最小値と最大値による正規化
- 発散点のみの着色: divergent_maskを使用
- 発散していない点の処理: 黒に設定
- RGBA変換: 0〜1の範囲を0〜255に変換

## CRITICAL_BEHAVIORS
- ポテンシャル計算の正確性
- 正規化の正確性
- 発散していない点の黒への設定の正確性
- RGBA変換の正確性


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
debug.DebugLogger: デバッグログ
debug.LogLevel: ログレベル定義
coloring.utils._smooth_iterations: スムージング処理
coloring.utils._normalize_and_color: 正規化と着色
coloring.utils.fast_smoothing: 高速スムージング処理
coloring.utils.ColorAlgorithmError: 例外クラス

## CLASS_ATTRIBUTES
(クラス属性なし)

## METHOD_SIGNATURES
def apply_smoothing(
    colored: np.ndarray,
    divergent_mask: np.ndarray,
    iterations: np.ndarray,
    z_vals: np.ndarray,
    cmap_func: Colormap,
    params: Dict,
    smoothing_method: str,
    logger: DebugLogger
) -> None
機能: 発散領域に対して、指定されたスムージングメソッドを用いて反復回数に基づくカラーリングを適用する
引数:
- colored: 着色結果を格納するRGBA配列 (形状: (height, width, 4), dtype=float32)
- divergent_mask: 発散した点のマスク (形状: (height, width), dtype=bool)
- iterations: 元の反復回数配列 (形状: (height, width), dtype=int)
- z_vals: 計算終了時の複素数値配列 (形状: (height, width), dtype=complex)
- cmap_func: 発散部分用のカラーマップ関数
- params: 計算パラメータ辞書 (現在は未使用だが将来的な拡張のため)
- smoothing_method (str): 使用するスムージングの種類 ('standard', 'fast', 'exponential')
- logger: デバッグログを出力するためのロガーインスタンス

## CORE_EXECUTION_FLOW
スムージング処理 → 有限値の抽出 → 正規化 → カラーマップ適用

## KEY_LOGIC_PATTERNS
- スムージング処理: _smooth_iterationsを使用
- 有限値の抽出: divergent_maskとnp.isfiniteを使用
- 正規化: _normalize_and_colorを使用
- 発散点のみの着色: divergent_maskを使用
- エラーハンドリング:
  - ColorAlgorithmErrorの処理
  - 予期しないエラーの処理
  - 有効なスムージング値がない場合の処理
  - vminとvmaxが近い場合の処理
- RGBA変換: 0〜1の範囲を0〜255に変換

## CRITICAL_BEHAVIORS
- スムージングメソッドごとの正確性
- 有限値の抽出の正確性
- 正規化の正確性
- 例外処理の適切性
- RGBA変換の正確性
