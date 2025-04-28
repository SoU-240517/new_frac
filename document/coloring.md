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
フラクタル画像のキャッシュ管理

## CLASS_DEFINITION:
名前: ColorCache
役割:
- 既に計算されたフラクタル画像の再利用を可能にする
- キャッシュの保存、取得、管理を行う
親クラス: なし

## DEPENDENCIES
numpy: 数値計算
typing: 型ヒント
ui.zoom_function.debug_logger.DebugLogger: デバッグログ
ui.zoom_function.enums.LogLevel: ログレベル定義

## CLASS_ATTRIBUTES
self.cache: dict - キャッシュデータを保持する辞書
self.max_size: int - キャッシュの最大サイズ
self.logger: DebugLogger - デバッグログ

## METHOD_SIGNATURES
def __init__(self, max_size: int = 100, logger: Optional[DebugLogger] = None) -> None
機能: コンストラクタ。キャッシュの最大サイズとロガーを設定

def _create_cache_key(self, params: Dict) -> str
機能: キャッシュキーを生成 (パラメータ辞書をソートして文字列化)

def get_cache(self, params: Dict) -> Optional[np.ndarray]
機能: キャッシュから画像データを取得

def put_cache(self, params: Dict, data: np.ndarray) -> None
機能: 画像データをキャッシュに保存

## CORE_EXECUTION_FLOW
__init__ -> _create_cache_key, get_cache, put_cache

## KEY_LOGIC_PATTERNS
- キャッシュ管理: 画像データの保存と取得
- キャッシュキー生成: パラメータに基づいたキー生成
- LRUキャッシュ: 最大サイズ超過時の古いアイテム削除

## CRITICAL_BEHAVIORS
- キャッシュの効率的な利用
- キー生成の正確性
- キャッシュサイズの管理

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
フラクタル画像の色付け処理を管理するクラス

## CLASS_DEFINITION:
(クラス定義なし)

## DEPENDENCIES
matplotlib.pyplot: プロットライブラリ
numpy: 数値計算
time: 時間計測
typing: 型ヒント
ui.zoom_function.debug_logger.DebugLogger: デバッグログ
ui.zoom_function.enums.LogLevel: ログレベル定義
coloring.utils: ユーティリティ関数
coloring.gradient: グラデーション生成
coloring.cache: キャッシュ管理
coloring.divergent.*: 発散色付けアルゴリズム
coloring.non_divergent.*: 非発散色付けアルゴリズム

## CLASS_ATTRIBUTES
(クラス属性なし)

## METHOD_SIGNATURES
def color_fractal(image_shape: tuple, iterations: np.ndarray, z_vals: np.ndarray, mask: np.ndarray, params: dict, cache: ColorCache, logger: DebugLogger) -> np.ndarray
機能: フラクタル画像に色を付ける

## CORE_EXECUTION_FLOW
color_fractal -> 各種色付けアルゴリズム

## KEY_LOGIC_PATTERNS
- 色付けアルゴリズム選択: パラメータに基づいたアルゴリズム選択
- 発散/非発散領域処理: マスクによる領域分割と個別処理
- キャッシュ利用: 計算結果のキャッシュ

## CRITICAL_BEHAVIORS
- アルゴリズム選択の正確性
- 領域分割と個別処理の正確性
- キャッシュの効率的な利用

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
