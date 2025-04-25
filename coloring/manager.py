import matplotlib.pyplot as plt
import numpy as np
import time
from matplotlib.colors import Colormap
from typing import Dict, Optional

# ユーティリティ関数とエラークラスをインポート
from .utils import _normalize_and_color, _smooth_iterations, ColorAlgorithmError

# 各アルゴリズムモジュールから着色関数をインポート
# 発散部
from .divergent import linear as div_linear # 線形マッピング
# from .divergent import logarithmic as div_logarithmic # 例: 追加する場合
from .divergent import smoothing as div_smoothing     # 例: 追加する場合
# ... 他の発散アルゴリズムも同様にインポート

# 非発散部
from .non_divergent import solid_color as ndiv_solid # 単色
# from .non_divergent import gradient_based as ndiv_gradient # 例: 追加する場合
# ... 他の非発散アルゴリズムも同様にインポート

# gradient モジュール (グラデーション計算用)
from . import gradient

# UI関連のインポート (ロガーなど)
from ui.zoom_function.debug_logger import DebugLogger
from ui.zoom_function.enums import LogLevel

"""フラクタル画像の着色処理エンジン (管理・ディスパッチ担当)
このモジュールは、どの着色アルゴリズムを使用するかを決定し、
関連するモジュールを呼び出して実際の着色処理を実行します。
キャッシュ機能も管理します。
"""

class ColorCache:
    """フラクタル画像のキャッシュ管理クラス
    このクラスはフラクタル画像のキャッシュを管理し、既に計算された画像の再利用を可能にする
    Attributes:
        cache (dict): キャッシュデータを保持する辞書
        max_size (int): キャッシュの最大サイズ
        logger (DebugLogger): デバッグログを記録するためのロガー
    """
    def __init__(self, max_size: int = 100, logger: Optional[DebugLogger] = None):
        """ColorCache クラスのコンストラクタ
        Args:
            max_size (int): キャッシュの最大サイズ
            logger (DebugLogger): デバッグ用ロガー
        """
        self.cache = {}
        self.max_size = max_size
        # logger が None の場合、デフォルトの DebugLogger を作成
        self.logger = logger if logger is not None else DebugLogger()

    def _create_cache_key(self, params: Dict) -> str:
        """キャッシュキーを生成 (パラメータ辞書をソートして文字列化)
        Args:
            params (dict): 計算パラメータ
        Returns:
            str: キャッシュキー
        """
        # Numpy配列など、直接文字列化できない要素を考慮する必要がある場合は、
        # より洗練されたキー生成方法が必要になることがあります。
        # ここでは単純な辞書を想定しています。
        try:
            return str(sorted(params.items()))
        except TypeError:
            # params にソート不可能な型が含まれる場合の代替処理
            # (例: repr を使う、特定のキーだけ使うなど)
            # ここでは簡単な例として repr を使用
            return repr(params)

    def get_cache(self, params: Dict) -> Optional[np.ndarray]:
        """キャッシュからデータを取得
        Args:
            params (dict): 計算パラメータ
        Returns:
            np.ndarray or None: キャッシュされた画像データ（存在しない場合はNone）
        """
        key = self._create_cache_key(params)
        cached_item = self.cache.get(key)
        if cached_item:
            self.logger.log(LogLevel.INFO, f"Cache hit for key: {key[:50]}...") # キーが長い場合があるので一部表示
            return cached_item['image']
        else:
            self.logger.log(LogLevel.INFO, f"Cache miss for key: {key[:50]}...")
            return None

    def put_cache(self, params: Dict, data: np.ndarray) -> None:
        """データをキャッシュに保存
        Args:
            params (dict): 計算パラメータ
            data (np.ndarray): キャッシュするデータ (画像配列)
        """
        key = self._create_cache_key(params)
        if len(self.cache) >= self.max_size:
            try:
                # 最も古いキーを取得して削除 (Python 3.7+ では挿入順序が保証される)
                first_key = next(iter(self.cache))
                del self.cache[first_key]
                self.logger.log(LogLevel.DEBUG, f"Cache full. Removed oldest item with key: {first_key[:50]}...")
            except StopIteration:
                # キャッシュが空の場合は何もしない
                pass
        self.cache[key] = {'params': params, 'image': data}
        self.logger.log(LogLevel.DEBUG, f"Cached item with key: {key[:50]}...")


# --- メインの着色関数 ---
def apply_coloring_algorithm(results: Dict, params: Dict, logger: DebugLogger) -> np.ndarray:
    """フラクタルの着色アルゴリズムを適用 (ディスパッチャ)
    Args:
        results (dict): フラクタル計算結果 ('iterations', 'mask', 'z_vals')
        params (dict): 着色パラメータ ('diverge_algorithm', 'non_diverge_algorithm', etc.)
        logger (DebugLogger): デバッグログ用ロガー
    Returns:
        np.ndarray: 着色されたRGBA配列 (形状: (h, w, 4), dtype=float32, 値域: 0-255)
    Raises:
        ColorAlgorithmError: 対応するアルゴリズムが見つからない場合や、着色処理中にエラーが発生した場合
    """
    logger.log(LogLevel.INIT, "Coloring process started in manager.")

    # --- 1. キャッシュ確認 ---
    # 注意: paramsの内容によってはキャッシュキーの生成・比較が複雑になる可能性あり
    # 例えば、Colormapオブジェクト自体をparamsに入れると問題が起きやすい
    # paramsにはアルゴリズム名やカラーマップ名(文字列)など、比較可能なものを入れるのが安全
    cache = ColorCache(logger=logger) # キャッシュインスタンス生成
    cached_image = cache.get_cache(params)
    if cached_image is not None:
        logger.log(LogLevel.INFO, "Returning cached image.")
        return cached_image

    # --- 2. 必要なデータの準備 ---
    iterations = results.get('iterations')
    mask = results.get('mask') # 非発散（集合内部）のマスク (Trueが内部)
    z_vals = results.get('z_vals')

    # 入力データの基本的な検証
    if iterations is None or mask is None or z_vals is None:
        logger.log(LogLevel.ERROR, "Missing required keys in 'results' dictionary (iterations, mask, z_vals).")
        raise ColorAlgorithmError("Invalid fractal results data.")
    if not (iterations.shape == mask.shape == z_vals.shape):
         logger.log(LogLevel.ERROR, f"Shape mismatch: iterations={iterations.shape}, mask={mask.shape}, z_vals={z_vals.shape}")
         raise ColorAlgorithmError("Input data shapes do not match.")

    # 発散した点のマスク (Trueが発散)
    # 元のコードでは iterations > 0 で判定していたが、
    # 0回の反復で発散と判定される場合もあるため、maskを反転させる方が確実
    divergent_mask = ~mask
    image_shape = iterations.shape
    # 出力用のRGBA配列を初期化 (float32で計算し、最後にuint8に変換するのが一般的だが、元のコードに合わせてfloat32のまま返す)
    # 初期値は透明な黒 (R=0, G=0, B=0, A=0) とする
    colored = np.zeros((*image_shape, 4), dtype=np.float32)

    # カラーマップを取得 (文字列名からmatplotlibのColormapオブジェクトへ)
    try:
        diverge_cmap_name = params.get("diverge_colormap", "viridis") # デフォルトを設定
        non_diverge_cmap_name = params.get("non_diverge_colormap", "gray") # デフォルトを設定
        cmap_func = plt.cm.get_cmap(diverge_cmap_name)
        non_cmap_func = plt.cm.get_cmap(non_diverge_cmap_name)
    except ValueError as e:
        logger.log(LogLevel.ERROR, f"Invalid colormap name specified: {e}")
        raise ColorAlgorithmError(f"Invalid colormap name: {e}") from e

    # --- 3. 着色処理の実行 ---
    try:
        start_time = time.time()

        # --- 3.1 発散部分の着色 ---
        if np.any(divergent_mask):
            algo_name = params.get("diverge_algorithm", "反復回数線形マッピング") # デフォルト指定
            logger.log(LogLevel.DEBUG, f"Processing divergent points using: {algo_name}")

            if algo_name == '反復回数線形マッピング':
                # linear.py の関数を呼び出す
                div_linear.apply_linear_mapping(colored, divergent_mask, iterations, cmap_func, params, logger)
            # elif algo_name == '反復回数対数マッピング':
            #     div_logarithmic.apply_logarithmic_mapping(colored, divergent_mask, iterations, z_vals, cmap_func, params, logger)
            elif algo_name in ['スムージングカラーリング', '高速スムージング', '指数スムージング']:
                smooth_method_map = {
                    'スムージングカラーリング': 'standard',
                    '高速スムージング': 'fast',
                    '指数スムージング': 'exponential'
                }
                smooth_method = smooth_method_map.get(algo_name, 'standard')
                div_smoothing.apply_smoothing(
                    colored,
                    divergent_mask,
                    iterations,
                    z_vals,
                    cmap_func,
                    params,
                    smooth_method,
                    logger
                )
            # --- 他の発散アルゴリズムの呼び出しをここに追加 ---
            # elif algo_name == "ヒストグラム平坦化法":
            #     div_histogram.apply_histogram(...)
            # ...

            else:
                logger.log(LogLevel.WARNING, f"Unknown divergent coloring algorithm: {algo_name}. Skipping.")
                # 必要であれば、ここでエラーにするか、デフォルト処理を行う
                # raise ColorAlgorithmError(f"Unknown divergent algorithm: {algo_name}")

        else:
            logger.log(LogLevel.DEBUG, "No divergent points to process.")

        # --- 3.2 非発散部分の着色 ---
        non_divergent_mask = mask # mask が True の部分が非発散
        if np.any(non_divergent_mask):
            non_algo_name = params.get("non_diverge_algorithm", "単色") # デフォルト指定
            logger.log(LogLevel.DEBUG, f"Processing non-divergent points using: {non_algo_name}")

            if non_algo_name == "単色":
                # solid_color.py の関数を呼び出す
                ndiv_solid.apply_solid_color(colored, non_divergent_mask, params, logger)
            # elif non_algo_name == "グラデーション":
                 # gradient_based.py の関数を呼び出す
            #    gradient_values = gradient.compute_gradient(image_shape, logger)
            #    ndiv_gradient.apply_gradient(colored, non_divergent_mask, gradient_values, non_cmap_func, params, logger)
            # --- 他の非発散アルゴリズムの呼び出しをここに追加 ---
            # elif non_algo_name == "内部距離（Escape Time Distance）":
            #     ndiv_internal_distance.apply_internal_distance(...)
            # ...

            else:
                logger.log(LogLevel.WARNING, f"Unknown non-divergent coloring algorithm: {non_algo_name}. Skipping.")
                # raise ColorAlgorithmError(f"Unknown non-divergent algorithm: {non_algo_name}")
        else:
             logger.log(LogLevel.DEBUG, "No non-divergent points to process.")


        end_time = time.time()
        logger.log(LogLevel.INFO, f"Coloring process finished in {end_time - start_time:.4f} seconds.")

        # --- 4. 結果のキャッシュと返却 ---
        # colored 配列は float32 の 0-255 の範囲になっているはず
        # 必要に応じて uint8 に変換: colored.astype(np.uint8)
        # ここでは float32 のままキャッシュ・返却
        cache.put_cache(params, colored)

        logger.log(LogLevel.DEBUG,
            f"Final colored array stats: dtype={colored.dtype}, "
            f"shape={colored.shape}, min={np.min(colored)}, max={np.max(colored)}"
        )
        return colored

    except Exception as e:
#        # スタックトレースを取得
#        import traceback
#        stack_trace = traceback.format_exc()

#        # ログ出力時にスタックトレースをコンテキストとして渡す
#        logger.log(LogLevel.CRITICAL, f"An unexpected error occurred during coloring: {e}",
#                context={"stack_trace": stack_trace})
        logger.log(LogLevel.CRITICAL, f"An unexpected error occurred during coloring: {e}")
        # より詳細なエラー情報と共に再raiseするか、デフォルト画像(例: 真っ黒)を返すか
        raise ColorAlgorithmError(f"Coloring failed due to an internal error: {e}") from e
