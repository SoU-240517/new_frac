import matplotlib.pyplot as plt
import numpy as np
import time
from typing import Dict, Callable, Any
from ui.zoom_function.debug_logger import DebugLogger
from ui.zoom_function.enums import LogLevel
from .utils import ColorAlgorithmError
from . import gradient # gradient モジュール (グラデーション計算用)
from .cache import ColorCache # キャッシュ管理クラス

# 各アルゴリズムモジュールから着色関数をインポート
# (インポート部分は変更なし)
# 発散部
from .divergent import linear as div_linear
from .divergent import logarithmic as div_logarithmic
from .divergent import smoothing as div_smoothing
from .divergent import histogram as div_histogram
from .divergent import distance as div_distance
from .divergent import angle as div_angle
from .divergent import potential as div_potential
from .divergent import orbit_trap as div_orbit_trap
# 非発散部
from .non_divergent import solid_color as ndiv_solid
from .non_divergent import gradient_based as ndiv_gradient
from .non_divergent import internal_distance as ndiv_internal_distance
from .non_divergent import orbit_trap_circle as ndiv_orbit_trap_circle
from .non_divergent import phase_symmetry as ndiv_phase_symmetry
from .non_divergent import convergence_speed as ndiv_convergence_speed
from .non_divergent import derivative as ndiv_derivative
from .non_divergent import histogram_equalization as ndiv_histogram_equalization
from .non_divergent import complex_potential as ndiv_complex_potential
from .non_divergent import chaotic_orbit as ndiv_chaotic_orbit
from .non_divergent import fourier_pattern as ndiv_fourier_pattern
from .non_divergent import fractal_texture as ndiv_fractal_texture
from .non_divergent import quantum_entanglement as ndiv_quantum_entanglement
from .non_divergent import palam_c_z as ndiv_palam_c_z

# --- アルゴリズム関数をマッピングする辞書 ---
# Callable[[np.ndarray, np.ndarray, Any, Any, Dict, DebugLogger], None] のような型ヒントも可能だが、簡潔さのため省略
DIVERGENT_ALGORITHMS: Dict[str, Callable] = {
    '反復回数線形マッピング': div_linear.apply_linear_mapping,
    '反復回数対数マッピング': div_logarithmic.apply_logarithmic_mapping,
    'スムージング': div_smoothing.apply_smoothing,
    '高速スムージング': div_smoothing.apply_smoothing,
    '指数スムージング': div_smoothing.apply_smoothing,
    'ヒストグラム平坦化法': div_histogram.apply_histogram_flattening,
    '距離カラーリング': div_distance.apply_distance_coloring,
    '角度カラーリング': div_angle.apply_angle_coloring,
    'ポテンシャル関数法': div_potential.apply_potential,
    '軌道トラップ法': div_orbit_trap.apply_orbit_trap,
}

NON_DIVERGENT_ALGORITHMS: Dict[str, Callable] = {
    '単色': ndiv_solid.apply_solid_color,
    'グラデーション': ndiv_gradient.apply_gradient_based, # gradient_valuesは別途準備が必要
    '内部距離（Escape Time Distance）': ndiv_internal_distance.apply_internal_distance,
    '軌道トラップ(円)（Orbit Trap Coloring）': ndiv_orbit_trap_circle.apply_orbit_trap_circle,
    '位相对称（Phase Angle Symmetry）': ndiv_phase_symmetry.apply_phase_symmetry,
    '反復収束速度（Convergence Speed）': ndiv_convergence_speed.apply_convergence_speed,
    '微分係数（Derivative Coloring）': ndiv_derivative.apply_derivative_coloring,
    '統計分布（Histogram Equalization）': ndiv_histogram_equalization.apply_histogram_equalization,
    '複素ポテンシャル（Complex Potential Mapping）': ndiv_complex_potential.apply_complex_potential,
    'カオス軌道混合（Chaotic Orbit Mixing）': ndiv_chaotic_orbit.apply_chaotic_orbit,
    'フーリエ干渉（Fourier Pattern）': ndiv_fourier_pattern.apply_fourier_pattern,
    'フラクタルテクスチャ（Fractal Texture）': ndiv_fractal_texture.apply_fractal_texture,
    '量子もつれ（Quantum Entanglement）': ndiv_quantum_entanglement.apply_quantum_entanglement,
    'パラメータ(C)': ndiv_palam_c_z.apply_parameter_coloring, # 関数内でCかZかを判断する想定
    'パラメータ(Z)': ndiv_palam_c_z.apply_parameter_coloring, # 同上
}

# デフォルトアルゴリズム関数 (フォールバック用、これも関数自体ではなく名前で管理しても良い)
DEFAULT_DIVERGENT_ALGO_NAME = "スムージング" # フォールバック用のデフォルト名
DEFAULT_NON_DIVERGENT_ALGO_NAME = "単色" # フォールバック用のデフォルト名

# --- メインの着色関数 ---
def apply_coloring_algorithm(results: Dict, params: Dict, logger: DebugLogger, config: Dict[str, Any]) -> np.ndarray:
    """フラクタルの着色アルゴリズムを適用するディスパッチャ関数
    - 計算結果とパラメータに基づき、発散領域と非発散領域に対して適切な着色アルゴリズムを選択し、適用する
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
    # --- 1. キャッシュ管理クラスの初期化とキャッシュ確認 ---
    # ColorCache の初期化時に config を渡す
    cache = ColorCache(config=config, logger=logger)
    # キャッシュキー生成のために params を渡す (params に config を含めない想定)
    # キャッシュキーに影響するパラメータのみを抽出して渡す方がより良い場合もある
    cache_params = params.copy() # params をコピーして使う
    # 必要に応じてキャッシュキーに含めない項目を削除
    # cache_params.pop('render_mode', None)
    cached_image = cache.get_cache(cache_params)
    if cached_image is not None:
        logger.log(LogLevel.INFO, "キャッシュされた画像を返します。")
        return cached_image

    # --- 2. 必要なデータの準備 ---
    iterations = results.get('iterations')
    mask = results.get('mask') # True が非発散 (集合内部), False が発散 (集合外部)
    z_vals = results.get('z_vals')

    # 必須データの存在チェック
    if iterations is None or mask is None or z_vals is None:
        logger.log(LogLevel.CRITICAL, "着色に必要なデータ (iterations, mask, z_vals) が results 辞書にありません。")
        raise ColorAlgorithmError("Invalid fractal results data for coloring.")
    # 形状チェック
    if not (iterations.shape == mask.shape == z_vals.shape):
         logger.log(LogLevel.CRITICAL, f"着色データの形状不一致: iterations={iterations.shape}, mask={mask.shape}, z_vals={z_vals.shape}")
         raise ColorAlgorithmError("Input data shapes for coloring do not match.")

    # マスクの準備 (元のコードに合わせて bool 型を想定)
    # divergent_mask: 発散領域 (集合外部) -> True
    # non_divergent_mask: 非発散領域 (集合内部) -> True
    divergent_mask = ~mask if mask.dtype == bool else mask == 0 # bool でない場合も考慮
    non_divergent_mask = mask if mask.dtype == bool else mask != 0 # bool でない場合も考慮

    image_shape = iterations.shape
    # 出力画像の初期化 (float32 で計算し、最後に uint8 に変換する方が精度が良い)
    colored = np.zeros((*image_shape, 4), dtype=np.float32) # float32 に変更

    # カラーマップの取得 (エラー処理強化)
    try:
        diverge_cmap_name = params.get("diverge_colormap", "viridis") # デフォルト値
        non_diverge_cmap_name = params.get("non_diverge_colormap", "plasma") # デフォルト値
        cmap_func = plt.get_cmap(diverge_cmap_name)
        non_cmap_func = plt.get_cmap(non_diverge_cmap_name)
        logger.log(LogLevel.DEBUG, f"カラーマップ取得: 発散部={diverge_cmap_name}, 非発散部={non_diverge_cmap_name}")
    except ValueError as e:
        logger.log(LogLevel.CRITICAL, f"無効なカラーマップ名が指定されました: {e}")
        # 無効な場合、デフォルトに戻すかエラーにするか。ここではエラーにする。
        raise ColorAlgorithmError(f"Invalid colormap name specified: {e}") from e
    except Exception as e:
        logger.log(LogLevel.CRITICAL, f"カラーマップ取得中に予期せぬエラー: {e}")
        raise ColorAlgorithmError("Unexpected error while getting colormap.") from e

    # --- 3. 着色処理の実行 ---
    try:
        start_time = time.time() # perf_counter の方がより正確
        start_perf_counter = time.perf_counter()

        # --- 3.1 発散部分の着色 ---
        if np.any(divergent_mask): # 処理対象が存在するかチェック
            # params からアルゴリズム名を取得、なければデフォルト名を使用
            # ParameterPanel で設定された名前と辞書のキーを一致させる
            algo_name = params.get("diverge_algorithm", DEFAULT_DIVERGENT_ALGO_NAME)
            logger.log(LogLevel.INFO, f"発散部分の着色開始: アルゴリズム='{algo_name}'")

            # 辞書からアルゴリズム関数を取得
            algo_func = DIVERGENT_ALGORITHMS.get(algo_name)

            if algo_func:
                try:
                    # アルゴリズムに応じて必要な引数を渡す
                    if algo_name in ['スムージング', '高速スムージング', '指数スムージング']:
                        smooth_method_map = {
                            'スムージング': 'standard',
                            '高速スムージング': 'fast',
                            '指数スムージング': 'exponential'
                        }
                        smooth_type = smooth_method_map.get(algo_name, 'standard')
                        smooth_method = params.get('smoothing_method', smooth_type)
                        logger.log(LogLevel.DEBUG, f"Smoothing method: {smooth_method}")
                        # Smoothing 関数は mask, iterations, z_vals, cmap, params, method, logger を受け取る想定
                        algo_func(colored, divergent_mask, iterations, z_vals, cmap_func, params, smooth_method, logger)
                    elif algo_name in ['距離カラーリング', '角度カラーリング', 'ポテンシャル関数法']:
                        # これらは z_vals が必要
                        algo_func(colored, divergent_mask, z_vals, cmap_func, params, logger)
                    elif algo_name == '軌道トラップ法':
                       # 軌道トラップ法は iterations と z_vals が必要
                       algo_func(colored, divergent_mask, iterations, z_vals, cmap_func, params, logger)
                    else: # Linear, Logarithmic, Histogram など
                        # これらは iterations が必要
                        algo_func(colored, divergent_mask, iterations, cmap_func, params, logger)
                    logger.log(LogLevel.SUCCESS, f"発散部分の着色完了: '{algo_name}'")
                except Exception as algo_e:
                    logger.log(LogLevel.ERROR, f"発散アルゴリズム '{algo_name}' 実行中にエラー: {algo_e}")
                    # エラーが発生した場合、この領域の着色はスキップされるか、
                    # またはデフォルトの安全なアルゴリズムで再試行するなどの対策が必要
                    # ここではエラーを上に投げる
                    raise ColorAlgorithmError(f"Error during divergent algorithm '{algo_name}'.") from algo_e
            else:
                # アルゴリズム名が辞書にない場合
                logger.log(LogLevel.WARNING, f"未知の発散色付けアルゴリズム: '{algo_name}'。 フォールバック ({DEFAULT_DIVERGENT_ALGO_NAME}) を試みます。")
                fallback_func = DIVERGENT_ALGORITHMS.get(DEFAULT_DIVERGENT_ALGO_NAME)
                if fallback_func:
                     try:
                         # フォールバック関数を実行 (ここでは Linear を想定)
                         fallback_func(colored, divergent_mask, iterations, cmap_func, params, logger)
                     except Exception as fallback_e:
                         logger.log(LogLevel.ERROR, f"フォールバック発散アルゴリズム '{DEFAULT_DIVERGENT_ALGO_NAME}' 実行中にもエラー: {fallback_e}")
                         raise ColorAlgorithmError(f"Fallback divergent algorithm '{DEFAULT_DIVERGENT_ALGO_NAME}' failed.") from fallback_e
                else:
                    # フォールバック関数すら見つからない場合 (致命的)
                    logger.log(LogLevel.CRITICAL, f"デフォルトの発散アルゴリズム '{DEFAULT_DIVERGENT_ALGO_NAME}' が見つかりません。")
                    raise ColorAlgorithmError(f"Default divergent algorithm '{DEFAULT_DIVERGENT_ALGO_NAME}' not found.")

        else:
            logger.log(LogLevel.INFO, "発散領域が存在しないため、発散部分の着色をスキップします。")

        # --- 3.2 非発散部分の着色 ---
        if np.any(non_divergent_mask): # 処理対象が存在するかチェック
            # params からアルゴリズム名を取得、なければデフォルト名を使用
            algo_name = params.get("non_diverge_algorithm", DEFAULT_NON_DIVERGENT_ALGO_NAME)
            logger.log(LogLevel.INFO, f"非発散部分の着色開始: アルゴリズム='{algo_name}'")

            # 辞書からアルゴリズム関数を取得
            algo_func = NON_DIVERGENT_ALGORITHMS.get(algo_name)

            if algo_func:
                try:
                    # アルゴリズムに応じて必要な引数を渡す
                    if algo_name == 'グラデーション':
                        # グラデーション用の値は事前に計算しておく必要がある
                        logger.log(LogLevel.DEBUG, "グラデーション値を計算します...")
                        gradient_values = gradient.compute_gradient(image_shape, logger)
                        logger.log(LogLevel.DEBUG, f"グラデーション値 計算完了: shape={gradient_values.shape}")
                        # Gradient 関数は mask, iterations, gradient_values, cmap, params, logger を受け取る想定
                        algo_func(colored, non_divergent_mask, iterations, gradient_values, non_cmap_func, params, logger)
                    elif algo_name == '統計分布（Histogram Equalization）':
                         # 統計分布は iterations が必要
                        algo_func(colored, non_divergent_mask, iterations, non_cmap_func, params, logger)
                    elif algo_name == '単色':
                         # 単色は params のみ必要 (色情報が params に含まれる想定)
                         algo_func(colored, non_divergent_mask, params, logger)
                    elif algo_name in ['パラメータ(C)', 'パラメータ(Z)']:
                         # パラメータカラーリングは mask, z_vals, cmap, params, logger を受け取る想定
                         # 関数内部で C か Z かを params['fractal_type'] などで判断する
                         algo_func(colored, non_divergent_mask, z_vals, non_cmap_func, params, logger)
                    else:
                        # 他の多くの非発散アルゴリズムは z_vals が必要と想定
                        algo_func(colored, non_divergent_mask, z_vals, non_cmap_func, params, logger)
                    logger.log(LogLevel.SUCCESS, f"非発散部分の着色完了: '{algo_name}'")
                except Exception as algo_e:
                    logger.log(LogLevel.ERROR, f"非発散アルゴリズム '{algo_name}' 実行中にエラー: {algo_e}")
                    raise ColorAlgorithmError(f"Error during non-divergent algorithm '{algo_name}'.") from algo_e
            else:
                 # アルゴリズム名が辞書にない場合
                logger.log(LogLevel.WARNING, f"未知の非発散色付けアルゴリズム: '{algo_name}'。 フォールバック ({DEFAULT_NON_DIVERGENT_ALGO_NAME}) を試みます。")
                fallback_func = NON_DIVERGENT_ALGORITHMS.get(DEFAULT_NON_DIVERGENT_ALGO_NAME)
                if fallback_func:
                     try:
                         # フォールバック関数を実行 (ここでは Solid Color を想定)
                         fallback_func(colored, non_divergent_mask, params, logger)
                     except Exception as fallback_e:
                         logger.log(LogLevel.ERROR, f"フォールバック非発散アルゴリズム '{DEFAULT_NON_DIVERGENT_ALGO_NAME}' 実行中にもエラー: {fallback_e}")
                         raise ColorAlgorithmError(f"Fallback non-divergent algorithm '{DEFAULT_NON_DIVERGENT_ALGO_NAME}' failed.") from fallback_e
                else:
                    # フォールバック関数すら見つからない場合 (致命的)
                    logger.log(LogLevel.CRITICAL, f"デフォルトの非発散アルゴリズム '{DEFAULT_NON_DIVERGENT_ALGO_NAME}' が見つかりません。")
                    raise ColorAlgorithmError(f"Default non-divergent algorithm '{DEFAULT_NON_DIVERGENT_ALGO_NAME}' not found.")

        else:
            logger.log(LogLevel.INFO, "非発散領域が存在しないため、非発散部分の着色をスキップします。")

        end_perf_counter = time.perf_counter()
        logger.log(LogLevel.SUCCESS, f"全着色処理完了 ({end_perf_counter - start_perf_counter:.4f} 秒)")

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
        logger.log(LogLevel.CRITICAL, f"色付け処理の準備または後処理中に予期しないエラーが発生しました: {e}", exc_info=True) # スタックトレースも記録
        # エラーが発生した場合、安全な値 (例: 真っ黒な画像) を返すか、エラーを投げるか
        # ここではエラーを投げる
        raise ColorAlgorithmError("Coloring failed due to an unexpected internal error.") from e
