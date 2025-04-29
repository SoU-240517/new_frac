==============================
# MODULE_INFO:
__init__.py

## MODULE_PURPOSE
coloring パッケージの初期化

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
cache.py

## MODULE_PURPOSE
フラクタル画像のキャッシュ管理クラス。計算済みのフラクタル画像を保存し、再利用することで描画パフォーマンスを向上させる。

## CLASS_DEFINITION:
名前: ColorCache
役割:
- フラクタル画像の計算結果を、関連するパラメータをキーとしてメモリ上にキャッシュする。
- 指定されたパラメータに対応するキャッシュデータが存在するか検索する。
- キャッシュが最大サイズを超えた場合、古いアイテムを削除する（LRU風）。
- キャッシュの最大サイズは設定ファイルから読み込む。
親クラス: なし

## DEPENDENCIES
numpy (np): 数値計算
typing: 型ヒント (Dict, Optional, Any)
ui.zoom_function.debug_logger.DebugLogger: デバッグログ管理
ui.zoom_function.enums.LogLevel: ログレベル定義

## CLASS_ATTRIBUTES
self.cache: dict - キャッシュデータを保持する辞書 (OrderedDictに近い挙動)
self.max_size: int - キャッシュの最大サイズ (設定ファイルから読み込む)
self.logger: DebugLogger - デバッグログを記録するためのロガー

## METHOD_SIGNATURES
def __init__(self, config: Dict[str, Any], logger: Optional[DebugLogger] = None) -> None
機能: コンストラクタ。クラスの初期化、キャッシュの最大サイズの設定ファイルからの読み込み、ロガーの設定を行う。設定データを受け取る。

def _create_cache_key(self, params: dict) -> str
機能: キャッシュに使用するキーを、描画パラメータ (位置、サイズ、回転、最大反復回数、フラクタルタイプ、C値、Z0値、着色アルゴリズム、カラーマップ) から生成する。

def get_cache(self, params: dict) -> Optional[np.ndarray]
機能: 指定されたパラメータに対応するキャッシュデータが存在するかを検索し、存在すればそのデータを返す。キャッシュヒット・ミスをログ出力する。

def put_cache(self, params: dict, data: np.ndarray) -> None
機能: 指定されたパラメータと画像データをキャッシュに保存する。キャッシュが最大サイズを超えている場合は、最も古いアイテムを削除する（LRU風の挙動）。キャッシュ無効時は保存をスキップする。

def clear_cache(self) -> None
機能: キャッシュの内容を全て削除する。

## CORE_EXECUTION_FLOW
__init__ (config受け取り含む)
get_cache (呼び出し) → _create_cache_key → cache辞書検索
put_cache (呼び出し) → _create_cache_key → キャッシュサイズチェック → cache辞書保存/更新 → 古いアイテム削除 (必要であれば)

## KEY_LOGIC_PATTERNS
- キャッシュ管理: dictによるキャッシュの保存、検索、削除
- キー生成: 描画パラメータからのユニークなキー生成 (_create_cache_key)
- LRU戦略: 最大サイズ超過時の最も古いアイテム削除
- 設定ファイルからの読み込み: キャッシュ最大サイズをconfigから取得
- ログ記録: キャッシュヒット・ミス、保存・削除などの操作ログ出力

## CRITICAL_BEHAVIORS
- キャッシュキー生成の正確性（同一パラメータで同一キーが生成されること）
- キャッシュヒット判定とデータ取得の正確性
- 最大サイズ超過時の古いアイテム削除処理の正確性
- キャッシュ無効設定時の保存スキップ
- 設定パラメータ（最大サイズ）の正確な読み込みと適用


==============================
# MODULE_INFO:
gradient.py

## MODULE_PURPOSE
画像処理用のグラデーションパターン生成

## CLASS_DEFINITION:
(クラス定義なし)

## DEPENDENCIES
numpy: 数値計算
ui.zoom_function.debug_logger.DebugLogger: デバッグログ
ui.zoom_function.enums.LogLevel: ログレベル定義

## CLASS_ATTRIBUTES
(クラス属性なし)

## METHOD_SIGNATURES
def compute_gradient(shape, logger: DebugLogger) -> np.ndarray
機能: 画像サイズに基づいた2Dグラデーションを計算

## CORE_EXECUTION_FLOW
compute_gradient

## KEY_LOGIC_PATTERNS
- グラデーション生成: 放射状グラデーションの計算
- 配列操作: numpyを使った効率的な配列処理

## CRITICAL_BEHAVIORS
- グラデーション生成の正確性
- 計算効率


==============================
# MODULE_INFO:
manager.py

## MODULE_PURPOSE
フラクタル計算結果（反復回数、収束マスク、最終Z値）を受け取り、指定された着色アルゴリズムとカラーマップを使用して画像データを生成するモジュール。キャッシュ管理も行う。

## CLASS_DEFINITION:
(クラス定義なし)

## DEPENDENCIES
matplotlib.pyplot (plt): カラーマップ取得に使用
numpy (np): 数値計算
time: 時間計測
typing: 型ヒント (Dict, Callable, Any)
ui.zoom_function.debug_logger.DebugLogger: デバッグログ管理
ui.zoom_function.enums.LogLevel: ログレベル定義
.utils: ユーティリティ関数、例外クラス
.cache.ColorCache: キャッシュ管理クラス
.gradient: グラデーション計算関連
.divergent: 発散部着色アルゴリズム関連
.non_divergent: 非発散部着色アルゴリズム関連

## CLASS_ATTRIBUTES
ALGORITHM_MAPS (Dict): 各着色アルゴリズム名とそれに対応する関数のマッピング辞書
DEFAULT_DIVERGENT_ALGO_NAME (str): デフォルトの発散部アルゴリズム名
DEFAULT_NON_DIVERGENT_ALGO_NAME (str): デフォルトの非発散部アルゴリズム名

## METHOD_SIGNATURES
def _get_algorithm_function(algorithm_name: str, algorithm_type: str, logger: DebugLogger) -> Callable
機能: 指定されたアルゴリズム名に対応する関数をALGORITHM_MAPSから取得する。見つからない場合はデフォルトアルゴリズムを試みる。

def colorize(iterations: np.ndarray, z_values: np.ndarray, mask: np.ndarray, params: Dict[str, Any], color_params: Dict[str, Any], cache: ColorCache, config: Dict[str, Any], logger: DebugLogger) -> np.ndarray
機能: フラクタル計算結果を着色するメイン関数。キャッシュを確認し、存在すればキャッシュデータを使用。存在しない場合は、発散部と非発散部それぞれに対して指定されたアルゴリズムとカラーマップを適用して着色し、結果をキャッシュに保存して返す。エラー発生時はエラー画像を生成する。設定データとColorCacheインスタンスを受け取る。

## CORE_EXECUTION_FLOW
colorize (config, cache受け取り含む) → cache.get_cache → (キャッシュヒットの場合) キャッシュデータ返却
(キャッシュミスの場合) → _get_algorithm_function (発散部) → 発散部アルゴリズム実行 → _get_algorithm_function (非発散部) → 非発散部アルゴリズム実行 (マスク適用) → 結果合成 → cache.put_cache → 最終画像データ

## KEY_LOGIC_PATTERNS
- 着色アルゴリズム選択: アルゴリズム名から対応関数を取得 (_get_algorithm_function)
- キャッシュ利用: ColorCacheクラスによるキャッシュの取得と保存
- 領域分割と個別処理: マスクによる発散部と非発散部の分離と個別アルゴリズム適用
- 結果合成: 発散部と非発散部の着色結果の結合
- エラーハンドリング: 着色処理中の例外捕捉とエラー画像の生成
- 設定ファイルからの読み込み: デフォルトアルゴリズム名をconfigから取得（ALGORITHM_MAPSに直接含まれていないが、設定ファイルで指定される可能性を示唆）
- 依存モジュールのインポートと利用: divergent, non_divergent モジュール内の関数呼び出し

## CRITICAL_BEHAVIORS
- 指定されたアルゴリズム関数を正確に取得できること（デフォルトへのフォールバック含む）
- キャッシュが正しく機能し、効率的に利用されること
- 発散部と非発散部がマスクに基づいて正確に分離され、それぞれに適切な処理が適用されること
- 個別処理結果が正しく合成され、最終画像データが生成されること
- エラー発生時に適切に処理され、異常終了しないこと（エラー画像の生成）
- 設定パラメータ（デフォルトアルゴリズム名）の適用


==============================
# MODULE_INFO:
utils.py

## MODULE_PURPOSE
色付け処理のためのユーティリティ関数群

## CLASS_DEFINITION:
クラス: ColorAlgorithmError
役割:
- 色付けアルゴリズム関連のエラーを処理する例外クラス
親クラス: Exception

## DEPENDENCIES
numpy: 数値計算
matplotlib.colors: カラーマップ
typing: 型ヒント
ui.zoom_function.debug_logger.DebugLogger: デバッグログ
ui.zoom_function.enums.LogLevel: ログレベル定義

## CLASS_ATTRIBUTES
(クラス属性なし)

## METHOD_SIGNATURES
def _normalize_and_color(values: np.ndarray, cmap: Colormap, vmin: Optional[float] = None, vmax: Optional[float] = None) -> np.ndarray
機能: 値を正規化し、カラーマップを適用してRGBA配列を返す

def fast_smoothing(z: np.ndarray, iters: np.ndarray, out: np.ndarray) -> None
機能: 高速スムージングアルゴリズム（インプレース処理）

def smoothing(z: np.ndarray, iters: np.ndarray, method: str, logger: DebugLogger) -> np.ndarray
機能: 反復回数のスムージングを行う

## CORE_EXECUTION_FLOW
_normalize_and_color, fast_smoothing, smoothing

## KEY_LOGIC_PATTERNS
- 正規化と着色: 値の正規化とカラーマップ適用
- スムージング: 反復回数のスムージング処理
- 例外処理: 色付けアルゴリズム関連のエラーハンドリング

## CRITICAL_BEHAVIORS
- 正規化と着色の正確性
- スムージング処理の正確性と効率
- エラーハンドリングの適切さ
