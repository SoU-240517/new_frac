==============================
# MODULE_INFO:
__init__.py

## MODULE_PURPOSE
coloring パッケージの初期化と公開インターフェースの定義

## CLASS_DEFINITION:
(クラス定義なし)

## DEPENDENCIES
- manager.py
- gradient.py
- utils.py
- cache.py

## CLASS_ATTRIBUTES
(クラス属性なし)

## METHOD_SIGNATURES
(メソッドなし)

## CORE_EXECUTION_FLOW
- パッケージの公開インターフェースを定義
- 必要なモジュールから主要な機能をインポート

## KEY_LOGIC_PATTERNS
- パッケージとしての機能公開
- モジュール間の依存関係管理

## CRITICAL_BEHAVIORS
- フラクタルのカラーリング機能を提供
- 発散型と非発散型のカラーリングをサポート
- グラデーション計算と高速スムージングの提供
- カラーキャッシュ機能の提供


==============================
# MODULE_INFO:
cache.py

## MODULE_PURPOSE
フラクタル画像のキャッシュ管理クラス。計算済みのフラクタル画像を保存し、再利用することで描画パフォーマンスを向上させる。

## CLASS_DEFINITION:
名前: ColorCache
役割:
- 既に計算されたフラクタル画像の再利用を可能にする
- キャッシュの保存、取得、管理を行う
- キャッシュが最大サイズを超えた場合、古いアイテムを削除する（LRU風）
- キャッシュの最大サイズは設定ファイルから読み込む
親クラス: なし

## DEPENDENCIES
numpy (np): 数値計算
typing: 型ヒント (Dict, Optional, Any)
debug.DebugLogger: デバッグログ管理
debug.LogLevel: ログレベル定義

## CLASS_ATTRIBUTES
self.cache: dict - キャッシュデータを保持する辞書
self.max_size: int - キャッシュの最大サイズ (設定ファイルから読み込む)
self.logger: DebugLogger - デバッグログを記録するためのロガー

## METHOD_SIGNATURES
def __init__(self, config: Dict[str, Any], logger: Optional[DebugLogger] = None) -> None
機能: コンストラクタ。クラスの初期化、キャッシュの最大サイズの設定ファイルからの読み込み、ロガーの設定を行う。設定データを受け取る。

def _create_cache_key(self, params: Dict) -> str
機能: キャッシュに使用するキーを、描画パラメータから生成する。パラメータのソートと文字列化を行い、エラーハンドリングも含む。

def get_cache(self, params: Dict) -> Optional[np.ndarray]
機能: 指定されたパラメータに対応するキャッシュデータが存在するかを検索し、存在すればそのデータを返す。キャッシュヒット・ミスをログ出力する。

def put_cache(self, params: Dict, data: np.ndarray) -> None
機能: 指定されたパラメータと画像データをキャッシュに保存する。キャッシュが最大サイズを超えている場合は、最も古いアイテムを削除する（LRU風の挙動）。キャッシュ無効時は保存をスキップする。

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
- キャッシュキーの堅牢性: エラーハンドリング付きのキー生成処理

## CRITICAL_BEHAVIORS
- キャッシュキー生成の正確性（同一パラメータで同一キーが生成されること）
- キャッシュヒット判定とデータ取得の正確性
- 最大サイズ超過時の古いアイテム削除処理の正確性
- キャッシュ無効設定時の保存スキップ
- 設定パラメータ（最大サイズ）の正確な読み込みと適用
- エラーハンドリング: キャッシュキー生成時のTypeError等の適切な処理


==============================
# MODULE_INFO:
gradient.py

## MODULE_PURPOSE
画像処理用のグラデーションパターン生成

## CLASS_DEFINITION:
(クラス定義なし)

## DEPENDENCIES
numpy (np): 数値計算
debug.DebugLogger: デバッグログ管理
debug.LogLevel: ログレベル定義

## CLASS_ATTRIBUTES
(クラス属性なし)

## METHOD_SIGNATURES
def compute_gradient(shape, logger: DebugLogger) -> np.ndarray
機能: 画像サイズに基づいた2Dグラデーションを計算。画像の中心から外側に向かって放射状に変化する2Dグラデーションを生成する。

## CORE_EXECUTION_FLOW
compute_gradient

## KEY_LOGIC_PATTERNS
- グラデーション生成: 画像の中心から外側に向かって放射状に変化する2Dグラデーション
- 距離計算: ユークリッド距離を使用した中心からの距離計算
- 正規化: 最大距離で正規化された距離値の生成
- デバッグログ: 計算プロセスの詳細なログ記録
- 中心座標補正: 奇数サイズの画像の場合、中心座標を0.5ピクセル分シフト

## CRITICAL_BEHAVIORS
- グラデーション生成の正確性
- 計算効率
- デバッグログの正確性
- エラーハンドリング: 不正なshape値に対するバリデーション
- 中心座標の補正処理の正確性


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
debug.DebugLogger: デバッグログ管理
debug.LogLevel: ログレベル定義
.utils: ユーティリティ関数、例外クラス
.gradient: グラデーション計算関連
.cache.ColorCache: キャッシュ管理クラス
plugins.coloring.divergent: 発散部着色アルゴリズム関連
plugins.coloring.non_divergent: 非発散部着色アルゴリズム関連

## CLASS_ATTRIBUTES
(クラス属性なし)

## METHOD_SIGNATURES
def _load_algorithms_from_config(config: Dict) -> tuple[Dict[str, Callable], Dict[str, Callable]]
機能: 設定ファイルからアルゴリズム定義を読み込み、関数オブジェクトに変換する。

def apply_coloring_algorithm(results: Dict, params: Dict, logger: DebugLogger, config: Dict[str, Any]) -> np.ndarray
機能: フラクタル計算結果を着色するメイン関数。キャッシュを確認し、存在すればキャッシュデータを使用。存在しない場合は、発散部と非発散部それぞれに対して指定されたアルゴリズムとカラーマップを適用して着色し、結果をキャッシュに保存して返す。エラー発生時はエラー画像を生成する。設定データとColorCacheインスタンスを受け取る。

## CORE_EXECUTION_FLOW
apply_coloring_algorithm (config受け取り含む) → cache.get_cache → (キャッシュヒットの場合) キャッシュデータ返却
(キャッシュミスの場合) → _load_algorithms_from_config → 発散部アルゴリズム実行 → 非発散部アルゴリズム実行 (マスク適用) → 結果合成 → cache.put_cache → 最終画像データ

## KEY_LOGIC_PATTERNS
- アルゴリズム動的読み込み: 設定ファイルからアルゴリズムを動的に読み込む
- キャッシュ管理: 着色結果のキャッシュと再利用
- エラーハンドリング: アルゴリズムの存在チェックと適切なエラーメッセージ
- デバッグログ: アルゴリズム適用プロセスの詳細なログ記録
- アルゴリズム選択: 発散部/非発散部それぞれに適切なアルゴリズムの選択と適用
- マスク処理: 発散マスクと非発散マスクの適切な生成と適用
- グラデーション計算: 非発散部着色のためのグラデーション値の事前計算

## CRITICAL_BEHAVIORS
- アルゴリズムの正しい動的読み込み
- キャッシュの効率的な管理
- エラーハンドリングの正確性
- デバッグログの正確性
- アルゴリズム選択の正確性
- マスク処理の正確性
- グラデーション計算の正確性


==============================
# MODULE_INFO:
utils.py

## MODULE_PURPOSE
色付け処理のためのユーティリティ関数群

## CLASS_DEFINITION:
クラス: ColorAlgorithmError
役割:
- 着色アルゴリズム関連のエラーを処理する例外クラス
- 着色処理中に発生するエラーを扱う
- 主に、不正なアルゴリズム指定、計算値範囲エラー、パラメータ不整合で発生
親クラス: Exception

## DEPENDENCIES
numpy (np): 数値計算
matplotlib.colors: カラーマップ
typing: 型ヒント (Optional)
debug.DebugLogger: デバッグログ管理
debug.LogLevel: ログレベル定義

## CLASS_ATTRIBUTES
(クラス属性なし)

## METHOD_SIGNATURES
def _normalize_and_color(values: np.ndarray, cmap: Colormap, vmin: Optional[float] = None, vmax: Optional[float] = None) -> np.ndarray
機能: 値を正規化し、カラーマップを適用してRGBA配列を返す。NaN/Infの扱いは未定義で、呼び出し側で処理が必要。

def _smooth_iterations(z: np.ndarray, iters: np.ndarray, method: str = 'standard') -> np.ndarray
機能: 反復回数のスムージング処理を行う。複素数配列と反復回数配列を入力し、指定された方法で反復回数をスムージング。

def fast_smoothing(z: np.ndarray, iters: np.ndarray, out: np.ndarray) -> None
機能: 高速スムージングアルゴリズム（インプレース処理）。高速な手法で反復回数のスムージングを行い、結果は `out` 配列に直接格納される。

## CORE_EXECUTION_FLOW
_normalize_and_color, _smooth_iterations, fast_smoothing

## KEY_LOGIC_PATTERNS
- 正規化とカラーマップ適用: 値を正規化し、指定されたカラーマップを適用
- スムージング処理: 反復回数のスムージング処理
- エラーハンドリング: 不正な入力値に対する適切な処理
- デバッグログ: 計算プロセスの詳細なログ記録
- NaN/Infの適切な処理: 数値計算時の特殊値の適切な処理
- スムージング方法の多様性: standard, fast, exponential の3種類のスムージング方法の実装

## CRITICAL_BEHAVIORS
- 正規化の正確性
- スムージング処理の正確性
- エラーハンドリングの正確性
- デバッグログの正確性
- NaN/Inf処理の正確性
- スムージング方法選択の正確性
