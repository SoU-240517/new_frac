import matplotlib.pyplot as plt
import numpy as np
import time
from typing import Dict, Callable, Any
from debug import DebugLogger,LogLevel
from .utils import ColorAlgorithmError
from .gradient import compute_gradient
from .cache import ColorCache # キャッシュ管理クラス
from plugins.coloring.divergent import angle as div_angle
from plugins.coloring.divergent import distance as div_distance
from plugins.coloring.divergent import histogram as div_histogram
from plugins.coloring.divergent import linear as div_linear
from plugins.coloring.divergent import logarithmic as div_logarithmic
from plugins.coloring.divergent import orbit_trap as div_orbit_trap
from plugins.coloring.divergent import potential as div_potential
from plugins.coloring.divergent import smoothing as div_smoothing
from plugins.coloring.non_divergent import chaotic_orbit as ndiv_chaotic_orbit
from plugins.coloring.non_divergent import complex_potential as ndiv_complex_potential
from plugins.coloring.non_divergent import convergence_speed as ndiv_convergence_speed
from plugins.coloring.non_divergent import derivative as ndiv_derivative
from plugins.coloring.non_divergent import fourier_pattern as ndiv_fourier_pattern
from plugins.coloring.non_divergent import fractal_texture as ndiv_fractal_texture
from plugins.coloring.non_divergent import gradient_based as ndiv_gradient
from plugins.coloring.non_divergent import histogram_equalization as ndiv_histogram_equalization
from plugins.coloring.non_divergent import internal_distance as ndiv_internal_distance
from plugins.coloring.non_divergent import orbit_trap_circle as ndiv_orbit_trap_circle
from plugins.coloring.non_divergent import palam_c_z as ndiv_palam_c_z
from plugins.coloring.non_divergent import phase_symmetry as ndiv_phase_symmetry
from plugins.coloring.non_divergent import quantum_entanglement as ndiv_quantum_entanglement
from plugins.coloring.non_divergent import solid_color as ndiv_solid

def _load_algorithms_from_config(config: Dict) -> tuple[Dict[str, Callable], Dict[str, Callable]]:
    """
    設定ファイルからアルゴリズム定義を読み込み、関数オブジェクトに変換する
    """
    divergent_algos = {}
    non_divergent_algos = {}

    # fractal_settings の下に coloring_algorithms があることを確認
    fractal_settings = config.get('fractal_settings', {})
    if 'coloring_algorithms_settings' not in fractal_settings:
        raise ColorAlgorithmError("'coloring_algorithms_settings' section not found in fractal_settings")

    algorithms = fractal_settings['coloring_algorithms_settings']

    for algo_name, func_path in algorithms['divergent_list'].items():
        module_name, func_name = func_path.rsplit('.', 1)
        module = globals()[module_name]
        divergent_algos[algo_name] = getattr(module, func_name)

    for algo_name, func_path in algorithms['non_divergent_list'].items():
        module_name, func_name = func_path.rsplit('.', 1)
        module = globals()[module_name]
        non_divergent_algos[algo_name] = getattr(module, func_name)

    return divergent_algos, non_divergent_algos


def apply_coloring_algorithm(results: Dict, params: Dict, logger: DebugLogger, config: Dict[str, Any]) -> np.ndarray:
    """フラクタルの着色アルゴリズムを適用するディスパッチャ関数
    - 設定ファイルからアルゴリズム定義を動的に読み込み、適用する
    - 結果をキャッシュし、パフォーマンスを向上させる
    Args:
        results (dict): フラクタル計算結果。'iterations' (反復回数), 'mask' (発散マスク), 'z_vals' (複素数値) を含む
        params (dict): 着色パラメータ。使用するアルゴリズム名やカラーマップなどを含む
        logger (DebugLogger): デバッグログ用ロガー
        config (Dict[str, Any]): config.json から読み込んだ設定データ
    Returns:
        np.ndarray: 着色されたRGBA配列 (形状: (h, w, 4), dtype=float32, 値域: 0-255)
    Raises:
        ColorAlgorithmError: 対応するアルゴリズムが見つからない場合や、着色処理中にエラーが発生した場合
    """
    default_divergent_algo_name = config.get('coloring_algorithms_settings', {}).get('default_divergent_algo_name')
    default_non_divergent_algo_name = config.get('coloring_algorithms_settings', {}).get('default_non_divergent_algo_name')

    # --- 1. キャッシュ管理クラスの初期化とキャッシュ確認 ---
    cache = ColorCache(config=config, logger=logger)
    cache_params = params.copy()
    cached_image = cache.get_cache(cache_params)
    if cached_image is not None:
        logger.log(LogLevel.INFO, "キャッシュされた画像を返す")
        return cached_image

    # --- 2. アルゴリズムの動的読み込み ---
    try:
        divergent_algos, non_divergent_algos = _load_algorithms_from_config(config)

        # 使用するアルゴリズムの取得
        divergent_algo_name = params.get('diverge_algorithm', default_divergent_algo_name)
        non_divergent_algo_name = params.get('non_diverge_algorithm', default_non_divergent_algo_name)

        divergent_algo = divergent_algos.get(divergent_algo_name)
        non_divergent_algo = non_divergent_algos.get(non_divergent_algo_name)

        if divergent_algo is None:
            raise ColorAlgorithmError(f"Invalid divergent algorithm: {divergent_algo_name}")
        if non_divergent_algo is None:
            raise ColorAlgorithmError(f"Invalid non-divergent algorithm: {non_divergent_algo_name}")

    except Exception as e:
        logger.log(LogLevel.ERROR, f"Failed to load algorithms: {str(e)}")
        raise ColorAlgorithmError(f"Failed to load algorithms: {str(e)}")

    # --- 3. 必要なデータの準備 ---
    iterations = results.get('iterations')
    mask = results.get('mask')
    z_vals = results.get('z_vals')

    # 必須データの存在チェック
    if iterations is None or mask is None or z_vals is None:
        logger.log(LogLevel.CRITICAL, "着色に必要なデータ (iterations, mask, z_vals) が results 辞書にない")
        raise ColorAlgorithmError("Invalid fractal results data for coloring.")
    # 形状チェック
    if not (iterations.shape == mask.shape == z_vals.shape):
         logger.log(LogLevel.CRITICAL, "着色データの形状不一致", {"iterations": iterations.shape, "mask": mask.shape, "z_vals": z_vals.shape})
         raise ColorAlgorithmError("Input data shapes for coloring do not match.")

    # マスクの準備
    divergent_mask = ~mask if mask.dtype == bool else mask == 0
    non_divergent_mask = mask if mask.dtype == bool else mask != 0

    image_shape = iterations.shape
    # 出力画像の初期化 (float32 で計算し、最後に uint8 に変換する方が精度が良い)
    colored = np.zeros((*image_shape, 4), dtype=np.float32) # float32 に変更

    # カラーマップの取得 (エラー処理強化)
    try:
        diverge_cmap_name = params.get("diverge_colormap", "viridis") # デフォルト値
        non_diverge_cmap_name = params.get("non_diverge_colormap", "plasma") # デフォルト値
        cmap_func = plt.get_cmap(diverge_cmap_name)
        non_cmap_func = plt.get_cmap(non_diverge_cmap_name)
        logger.log(LogLevel.DEBUG, "カラーマップ取得", {"diverge_cmap_name": diverge_cmap_name, "non_diverge_cmap_name": non_diverge_cmap_name})
    except ValueError as e:
        logger.log(LogLevel.CRITICAL, "無効なカラーマップ名", {"message": e})
        # 無効な場合、デフォルトに戻すかエラーにするか。ここではエラーにする。
        raise ColorAlgorithmError(f"Invalid colormap name specified: {e}") from e
    except Exception as e:
        logger.log(LogLevel.CRITICAL, "カラーマップ取得中に予期せぬエラー", {"message": e})
        raise ColorAlgorithmError("Unexpected error while getting colormap.") from e

    # --- 3. 着色処理の実行 ---
    try:
        start_perf_counter = time.perf_counter()

        # --- 3.1 発散部分の着色 ---
        if np.any(divergent_mask): # 処理対象が存在するかチェック
            try:
                # アルゴリズムに応じて必要な引数を渡す
                if divergent_algo_name in ['スムージング', '軌道トラップ法']:
                    divergent_algo(colored, divergent_mask, iterations, z_vals, cmap_func, params, logger)
                elif divergent_algo_name in ['距離カラーリング', '角度カラーリング', 'ポテンシャル関数法']:
                    divergent_algo(colored, divergent_mask, z_vals, cmap_func, params, logger)
                else: # Linear, Logarithmic, Histogram など
                    divergent_algo(colored, divergent_mask, iterations, cmap_func, params, logger)
                logger.log(LogLevel.SUCCESS, "着色完了 発散部", {"divergent_algo_name": divergent_algo_name})
            except Exception as algo_e:
                logger.log(LogLevel.ERROR, f"発散アルゴリズム '{divergent_algo_name}' 実行中にエラー: {algo_e}")
                # エラーが発生した場合、この領域の着色はスキップされるか、
                # デフォルトの安全なアルゴリズムで再試行するなどの対策が必要
                # ここではエラーを上に投げる
                raise ColorAlgorithmError(f"Error during divergent algorithm '{divergent_algo_name}'.") from algo_e
        else:
            logger.log(LogLevel.INFO, "発散領域が存在しないため、発散部分の着色をスキップ")

        # --- 3.2 非発散部分の着色 ---
        if np.any(non_divergent_mask): # 処理対象が存在するかチェック

            try:
                # アルゴリズムに応じて必要な引数を渡す
                if non_divergent_algo_name == 'グラデーション':
                    # グラデーション用の値は事前に計算しておく必要がある
                    logger.log(LogLevel.DEBUG, "グラデーション値を計算します...")
                    gradient_values = compute_gradient(image_shape, logger)
                    logger.log(LogLevel.DEBUG, "グラデーション値 計算完了", {"shape": gradient_values.shape})
                    non_divergent_algo(colored, non_divergent_mask, iterations, gradient_values, non_cmap_func, params, logger)
                elif non_divergent_algo_name == '統計分布（Histogram Equalization）':
                    non_divergent_algo(colored, non_divergent_mask, iterations, non_cmap_func, params, logger)
                elif non_divergent_algo_name == '単色':
                    non_divergent_algo(colored, non_divergent_mask, params, logger)
                elif non_divergent_algo_name in ['パラメータ(C)', 'パラメータ(Z)']:
                    # パラメータカラーリングは mask, z_vals, cmap, params, logger を受け取る想定
                    # 関数内部で C か Z かを params['fractal_type'] などで判断する
                    non_divergent_algo(colored, non_divergent_mask, z_vals, non_cmap_func, params, logger)
                else:
                    # 他の多くの非発散アルゴリズムは z_vals が必要と想定
                    non_divergent_algo(colored, non_divergent_mask, z_vals, non_cmap_func, params, logger)
                logger.log(LogLevel.SUCCESS, "着色完了 非発散部", {"non_divergent_algo_name": non_divergent_algo_name})
            except Exception as algo_e:
                logger.log(LogLevel.ERROR, f"非発散アルゴリズム '{non_divergent_algo_name}' 実行中にエラー: {algo_e}")
                raise ColorAlgorithmError(f"Error during non-divergent algorithm '{non_divergent_algo_name}'.") from algo_e
        else:
            logger.log(LogLevel.INFO, "非発散領域が存在しないため、着色をスキップ")

        end_perf_counter = time.perf_counter()
        logger.log(LogLevel.INFO, f"全着色処理完了 ({end_perf_counter - start_perf_counter:.4f} 秒)")

        # --- 4. 結果のキャッシュと返却 ---
        # キャッシュに保存
        # 注意: `colored` は float32 (0-255) の状態。キャッシュもこの形式で保存。
        # uint8 への変換はキャッシュから取得した後か、render_fractal の最後で行う。
        cache.put_cache(cache_params, colored.copy()) # copy() して渡す方が安全
        logger.log(LogLevel.DEBUG,
            f"最終的な色付き float 配列の統計: dtype={colored.dtype}, "
            f"shape={colored.shape}, min={np.min(colored):.1f}, max={np.max(colored):.1f}"
        )
        # 関数としては float32 の配列を返す (render_fractal 側で uint8 に変換)
        return colored

    except ColorAlgorithmError:
        # 既にログ出力されているはずなので、そのまま再raise
        raise
    except Exception as e:
        # 予期せぬエラー (アルゴリズム実行前など)
        logger.log(LogLevel.CRITICAL, f"色付け処理の準備または後処理中に予期しないエラーが発生: {e}", exc_info=True) # スタックトレースも記録
        # エラーが発生した場合、安全な値 (例: 真っ黒な画像) を返すか、エラーを投げるか
        # ここではエラーを投げる
        raise ColorAlgorithmError("Coloring failed due to an unexpected internal error.") from e
