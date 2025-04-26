import matplotlib.pyplot as plt
import numpy as np
import time
from typing import Dict, Callable, Any # CallableとAnyを追加
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

# デフォルトのアルゴリズム関数
DEFAULT_DIVERGENT_ALGORITHM = div_linear.apply_linear_mapping
DEFAULT_NON_DIVERGENT_ALGORITHM = ndiv_solid.apply_solid_color

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
    # --- 1. キャッシュ確認 ---
    cache = ColorCache(logger=logger)
    cached_image = cache.get_cache(params)
    if cached_image is not None:
        logger.log(LogLevel.INFO, "Returning cached image.")
        return cached_image

    # --- 2. 必要なデータの準備 ---
    iterations = results.get('iterations')
    mask = results.get('mask')
    z_vals = results.get('z_vals')

    if iterations is None or mask is None or z_vals is None:
        logger.log(LogLevel.ERROR, "Missing required keys in 'results' dictionary (iterations, mask, z_vals).")
        raise ColorAlgorithmError("Invalid fractal results data.")
    if not (iterations.shape == mask.shape == z_vals.shape):
         logger.log(LogLevel.ERROR, f"Shape mismatch: iterations={iterations.shape}, mask={mask.shape}, z_vals={z_vals.shape}")
         raise ColorAlgorithmError("Input data shapes do not match.")

    divergent_mask = ~mask
    non_divergent_mask = mask # 元のコードに合わせて非発散マスクも用意
    image_shape = iterations.shape
    colored = np.zeros((*image_shape, 4), dtype=np.float32)

    try:
        diverge_cmap_name = params.get("diverge_colormap", "viridis")
        non_diverge_cmap_name = params.get("non_diverge_colormap", "plasma")
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
            algo_name = params.get("diverge_algorithm", "反復回数線形マッピング") # デフォルト名を指定
            logger.log(LogLevel.DEBUG, f"発散部分の着色: {algo_name}")

            # 辞書からアルゴリズム関数を取得、見つからなければデフォルトを使用
            algo_func = DIVERGENT_ALGORITHMS.get(algo_name)
            if algo_func:
                # スムージング系は辞書のラムダ式で smooth_method が設定される
                # 他のアルゴリズムは直接関数を呼び出す
                # 引数はアルゴリズム関数が必要とするものを渡す必要がある
                # ここでは代表的な引数を渡すが、アルゴリズムによっては調整が必要な場合がある
                if algo_name in ['スムージング', '高速スムージング', '指数スムージング']:
                    smooth_method_map = {
                        'スムージング': 'standard',
                        '高速スムージング': 'fast',
                        '指数スムージング': 'exponential'
                    }
                    smooth_method = smooth_method_map.get(algo_name, 'standard')
                    # スムージング系は z_vals が必要
                    algo_func(colored, divergent_mask, iterations, z_vals, cmap_func, params, smooth_method, logger)
                elif algo_name in ['距離カラーリング', '角度カラーリング', 'ポテンシャル関数法']:
                    # これらは z_vals が必要
                    algo_func(colored, divergent_mask, z_vals, cmap_func, params, logger)
                elif algo_name == '軌道トラップ法':
                   # 軌道トラップ法は iterations と z_vals が必要
                   algo_func(colored, divergent_mask, iterations, z_vals, cmap_func, params, logger)
                else:
                    # 線形、対数、ヒストグラムなどは iterations が必要
                    algo_func(colored, divergent_mask, iterations, cmap_func, params, logger)
            else:
                logger.log(LogLevel.WARNING, f"Unknown divergent coloring algorithm: {algo_name}. Using default (linear mapping).")
                DEFAULT_DIVERGENT_ALGORITHM(colored, divergent_mask, iterations, cmap_func, params, logger)

        # --- 3.2 非発散部分の着色 ---
        if np.any(non_divergent_mask):
            algo_name = params.get("non_diverge_algorithm", "単色") # デフォルト名を指定
            logger.log(LogLevel.DEBUG, f"非発散部分の着色: {algo_name}")

            # 辞書からアルゴリズム関数を取得、見つからなければデフォルトを使用
            algo_func = NON_DIVERGENT_ALGORITHMS.get(algo_name)
            if algo_func:
                # グラデーションは特別扱いが必要（gradient_valuesを計算）
                if algo_name == 'グラデーション':
                    gradient_values = gradient.compute_gradient(image_shape, logger)
                    algo_func(colored, non_divergent_mask, iterations, gradient_values, non_cmap_func, params, logger)
                elif algo_name == '統計分布（Histogram Equalization）':
                     # 統計分布は iterations が必要
                    algo_func(colored, non_divergent_mask, iterations, non_cmap_func, params, logger)
                elif algo_name == '単色':
                     # 単色は params のみ必要
                     algo_func(colored, non_divergent_mask, params, logger)
                else:
                    # 他の多くの非発散アルゴリズムは z_vals が必要
                    algo_func(colored, non_divergent_mask, z_vals, non_cmap_func, params, logger)
            else:
                logger.log(LogLevel.WARNING, f"Unknown non-divergent coloring algorithm: {algo_name}. Using default (solid color).")
                DEFAULT_NON_DIVERGENT_ALGORITHM(colored, non_divergent_mask, params, logger)

        end_time = time.time()
        logger.log(LogLevel.INFO, f"着色処理時間 {end_time - start_time:.4f} 秒")

        # --- 4. 結果のキャッシュと返却 ---
        cache.put_cache(params, colored)
        logger.log(LogLevel.DEBUG,
            f"最終的な色付き配列の統計: dtype={colored.dtype}, "
            f"shape={colored.shape}, min={np.min(colored)}, max={np.max(colored)}"
        )
        return colored

    except Exception as e:
        logger.log(LogLevel.CRITICAL, f"色付け中に予期しないエラーが発生しました: {e}")
        raise ColorAlgorithmError("Coloring failed due to an internal error: " + str(e)) from e
