==============================
# MODULE_INFO:
__init__.py

## MODULE_PURPOSE
Julia集合の計算機能を提供するパッケージの初期化と公開インターフェースの定義

## CLASS_DEFINITION:
(クラス定義なし)

## DEPENDENCIES
- julia.py

## CLASS_ATTRIBUTES
(クラス属性なし)

## METHOD_SIGNATURES
- compute_julia(Z: np.ndarray, C: complex, max_iter: int, logger: DebugLogger)

## CORE_EXECUTION_FLOW
- Julia集合の計算機能をパッケージとして公開
- 複素数グリッドとパラメータからジュリア集合を計算
- 反復計算による収束/発散判定
- 計算結果の辞書形式での返却

## KEY_LOGIC_PATTERNS
- ジュリア集合の反復計算
- 収束/発散の判定
- パフォーマンス最適化（NumPyを使用）

## CRITICAL_BEHAVIORS
- ジュリア集合の高速計算
- 収束/発散の正確な判定
- 計算結果の効率的な返却


==============================
# MODULE_INFO:
julia.py

## MODULE_PURPOSE
ジュリア集合の計算ロジックを実装するモジュール。指定された複素グリッドとパラメータに基づき、各点の反復回数、収束マスク、最終Z値を計算する。

## CLASS_DEFINITION:
(クラス定義なし)

## DEPENDENCIES
numpy (np): 数値計算
debug.DebugLogger: デバッグログ管理
typing: 型ヒント (Dict, np.ndarray)

## CLASS_ATTRIBUTES
(クラス属性なし)

## METHOD_SIGNATURES
def compute_julia(
    Z: np.ndarray,  # 複素数のグリッド
    C: complex,     # ジュリア集合のパラメータ
    max_iter: int,  # 最大反復回数
    logger: DebugLogger  # デバッグログ用
) -> Dict[str, np.ndarray]
機能: ジュリア集合の計算を実行する。入力の複素グリッド `Z` とパラメータ `C` に対して、`max_iter` 回の反復計算を行い、各点の反復回数、収束マスク、最終Z値を計算して辞書で返す。

## CORE_EXECUTION_FLOW
1. グリッドの形状取得
2. 初期化（反復回数、現在のZ値、マスク、最終Z値）
3. 反復計算ループ（最大反復回数まで）
   - マスク更新
   - 発散判定
   - ジュリア集合の反復式適用
   - 発散点の反復回数記録
4. 収束点の反復回数設定
5. 結果の辞書化

## KEY_LOGIC_PATTERNS
- ジュリア集合計算: z = z^2 + C の反復式を用いた計算
- 発散判定: |z| > 2 を基準とした発散点の判定
- ベクトル化計算: NumPyを用いたグリッド全体の並列計算
- マスクベースの計算: NumPyのブロードキャストとマスク操作を活用

## CRITICAL_BEHAVIORS
- 反復計算と発散判定の正確性
- 最大反復回数までの計算完了
- 計算結果（反復回数、マスク、最終Z値）の正確な出力
- NumPyによる効率的な計算
- 発散した点の早期検出と計算の最適化


==============================
# MODULE_INFO:
__init__.py

## MODULE_PURPOSE
マンデルブロ集合関連機能を提供するパッケージの初期化と公開インターフェースの定義。主な機能としてマンデルブロ集合の計算、パラメータ管理、カラーマッピング、レンダリングを提供する。

## CLASS_DEFINITION:
(クラス定義なし)

## DEPENDENCIES
- mandelbrot.py: マンデルブロ集合の計算ロジック

## CLASS_ATTRIBUTES
- __version__: パッケージのバージョン情報

## METHOD_SIGNATURES
- compute_mandelbrot(Z: np.ndarray, max_iter: int, logger: DebugLogger)

## CORE_EXECUTION_FLOW
1. パッケージの初期化
2. 必要なモジュールのインポート
3. 公開インターフェースの定義
4. パッケージバージョンの設定

## KEY_LOGIC_PATTERNS
- パッケージの公開インターフェース定義
- モジュールのインポート管理
- バージョン管理

## CRITICAL_BEHAVIORS
- マンデルブロ集合計算機能の正しく公開
- パッケージバージョンの正確な管理
- インターフェースの一貫性維持


==============================
# MODULE_INFO:
mandelbrot.py

## MODULE_PURPOSE
マンデルブロ集合の計算ロジックを実装するモジュール。指定された複素グリッドと初期値に基づき、各点の反復回数、収束マスク、最終Z値を計算する。

## CLASS_DEFINITION:
(クラス定義なし)

## DEPENDENCIES
numpy (np): 数値計算
debug.DebugLogger: デバッグログ管理
typing: 型ヒント (Dict, np.ndarray)

## CLASS_ATTRIBUTES
(クラス属性なし)

## METHOD_SIGNATURES
def compute_mandelbrot(
    Z: np.ndarray,  # 複素数のグリッド
    Z0: complex,    # 初期値
    max_iter: int,  # 最大反復回数
    logger: DebugLogger  # デバッグログ用
) -> Dict[str, np.ndarray]
機能: マンデルブロ集合の計算を実行する。入力の複素グリッド `Z` (各点がパラメータ c に対応) と初期値 `Z0` に対して、`max_iter` 回の反復計算を行い、各点の反復回数、収束マスク、最終Z値を計算して辞書で返す。

## CORE_EXECUTION_FLOW
1. グリッドの形状取得
2. 初期化（反復回数、現在のZ値、パラメータc、マスク、最終Z値）
3. 反復計算ループ（最大反復回数まで）
   - マスク更新
   - 発散判定
   - マンデルブロ集合の反復式適用
   - 発散点の反復回数記録
4. 収束点の反復回数設定
5. 結果の辞書化

## KEY_LOGIC_PATTERNS
- マンデルブロ集合計算: z = z^2 + c の反復式を用いた計算 (c はグリッド上の点に対応)
- 発散判定: |z| > 2 を基準とした発散点の判定
- ベクトル化計算: NumPyを用いたグリッド全体の並列計算
- マスクベースの計算: NumPyのブロードキャストとマスク操作を活用

## CRITICAL_BEHAVIORS
- 反復計算と発散判定の正確性
- 最大反復回数までの計算完了
- 計算結果（反復回数、マスク、最終Z値）の正確な出力
- NumPyによる効率的な計算
- 発散した点の早期検出と計算の最適化