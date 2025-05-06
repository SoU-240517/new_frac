import matplotlib.pyplot as plt
import numpy as np
import time
from typing import Dict, Callable, Any
from debug import DebugLogger,LogLevel
from .utils import ColorAlgorithmError
from .gradient import compute_gradient
from .cache import ColorCache # キャッシュ管理クラス

import matplotlib.pyplot as plt
import numpy as np
import time
from typing import Dict, Callable, Any, Optional
from debug import DebugLogger,LogLevel
from .utils import ColorAlgorithmError
from .gradient import compute_gradient # 既存 (これはプラグイン化しないなら残す)
from .cache import ColorCache
from plugins.coloring_loader import ColoringPluginLoader

def apply_coloring_algorithm(
    results: Dict,
    params: Dict,
    logger: DebugLogger,
    config: Dict[str, Any],
    coloring_loader: ColoringPluginLoader # ColoringPluginLoader を引数で受け取る
) -> np.ndarray:
    """
    フラクタルの着色アルゴリズムを適用するディスパッチャ関数
    - ColoringPluginLoader から着色関数を取得し、適用する
    - 結果をキャッシュし、パフォーマンスを向上させる (キャッシュ部分は変更なし)
    Args:
        results (dict): フラクタル計算結果。
        params (dict): 着色パラメータ。使用するアルゴリズム名(ファイル名)やカラーマップなどを含む
        logger (DebugLogger): デバッグログ用ロガー
        config (Dict[str, Any]): config.json から読み込んだ設定データ
        coloring_loader (ColoringPluginLoader): ロードされた着色プラグインを管理するローダー
    Returns:
        np.ndarray: 着色されたRGBA配列 (形状: (h, w, 4), dtype=float32, 値域: 0-255)
    Raises:
        ColorAlgorithmError: 対応するアルゴリズムが見つからない場合や、着色処理中にエラーが発生した場合
    """
    # --- 1. キャッシュ管理クラスの初期化とキャッシュ確認 ---
    cache = ColorCache(config=config, logger=logger)
    cache_params = params.copy()
    cached_image = cache.get_cache(cache_params)
    if cached_image is not None:
        logger.log(LogLevel.INFO, "キャッシュされた画像を返します。")
        return cached_image

    # --- 2. アルゴリズムの取得 (ローダー経由に変更) ---
    # ParameterPanelから渡されるアルゴリズム名は、プラグインのファイル名（拡張子なし）を想定
    divergent_algo_name = params.get('diverge_algorithm') # 例: "smoothing"
    non_divergent_algo_name = params.get('non_diverge_algorithm') # 例: "solid_color"

    # config.json からデフォルトのアルゴリズム名を取得 (フォールバック用)
    default_divergent_plugin = config.get("fractal_settings", {}).get("coloring_algorithms", {}).get("default_divergent", "smoothing")
    default_non_divergent_plugin = config.get("fractal_settings", {}).get("coloring_algorithms", {}).get("default_non_divergent", "solid_color")

    if not divergent_algo_name:
        logger.log(LogLevel.WARNING, f"発散部アルゴリズム名が指定されていません。デフォルト '{default_divergent_plugin}' を使用します。")
        divergent_algo_name = default_divergent_plugin
    if not non_divergent_algo_name:
        logger.log(LogLevel.WARNING, f"非発散部アルゴリズム名が指定されていません。デフォルト '{default_non_divergent_plugin}' を使用します。")
        non_divergent_algo_name = default_non_divergent_plugin

    # ローダーから着色関数を取得
    divergent_algo_func = coloring_loader.get_coloring_function("divergent", divergent_algo_name)
    non_divergent_algo_func = coloring_loader.get_coloring_function("non_divergent", non_divergent_algo_name)

    if divergent_algo_func is None:
        logger.log(LogLevel.ERROR, f"発散部アルゴリズム '{divergent_algo_name}' の関数が見つかりません。")
        # フォールバックとして、設定ファイルで指定されたデフォルトのプラグインを試みる
        divergent_algo_func = coloring_loader.get_coloring_function("divergent", default_divergent_plugin)
        if divergent_algo_func is None:
            raise ColorAlgorithmError(f"発散部アルゴリズム '{divergent_algo_name}' もデフォルト '{default_divergent_plugin}' も見つかりません。")
        else:
            logger.log(LogLevel.WARNING, f"フォールバックして発散部アルゴリズム '{default_divergent_plugin}' を使用します。")
            divergent_algo_name = default_divergent_plugin # 名前も更新

    if non_divergent_algo_func is None:
        logger.log(LogLevel.ERROR, f"非発散部アルゴリズム '{non_divergent_algo_name}' の関数が見つかりません。")
        non_divergent_algo_func = coloring_loader.get_coloring_function("non_divergent", default_non_divergent_plugin)
        if non_divergent_algo_func is None:
            raise ColorAlgorithmError(f"非発散部アルゴリズム '{non_divergent_algo_name}' もデフォルト '{default_non_divergent_plugin}' も見つかりません。")
        else:
            logger.log(LogLevel.WARNING, f"フォールバックして非発散部アルゴリズム '{default_non_divergent_plugin}' を使用します。")
            non_divergent_algo_name = default_non_divergent_plugin # 名前も更新
    # ---------------------------------------------

    # --- 3. 必要なデータの準備 ---
    iterations = results.get('iterations')
    mask = results.get('mask')
    z_vals = results.get('z_vals')

    # 必須データの存在チェック
    if iterations is None or mask is None or z_vals is None:
        logger.log(LogLevel.CRITICAL, "着色に必要なデータ (iterations, mask, z_vals) が results 辞書にありません。")
        raise ColorAlgorithmError("Invalid fractal results data for coloring.")
    # 形状チェック
    if not (iterations.shape == mask.shape == z_vals.shape):
         logger.log(LogLevel.CRITICAL, f"着色データの形状不一致: iterations={iterations.shape}, mask={mask.shape}, z_vals={z_vals.shape}")
         raise ColorAlgorithmError("Input data shapes for coloring do not match.")

    divergent_mask = ~mask if mask.dtype == bool else mask == 0
    non_divergent_mask = mask if mask.dtype == bool else mask != 0
    image_shape = iterations.shape
    colored = np.zeros((*image_shape, 4), dtype=np.float32)

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

    # --- 3. 着色処理の実行 (呼び出す関数を変更) ---
    try:
        start_time = time.time()
        start_perf_counter = time.perf_counter()

        # --- 3.1 発散部分の着色 ---
        if np.any(divergent_mask):
            logger.log(LogLevel.INFO, f"発散部分の着色開始: アルゴリズム='{divergent_algo_name}' (プラグイン)")
            try:
                # プラグイン関数を直接呼び出し
                # プラグイン関数は (colored_array, mask_to_apply, iterations, z_values, cmap_func, params_from_panel, logger, config)
                # のような引数を取るように統一する必要がある。
                # ここでは、プラグインが必要な情報を params から取得し、
                # colored 配列の該当箇所 (divergent_mask) を直接変更することを想定する。
                # 戻り値は部分的な画像ではなく、colored 配列を変更する副作用を持つ。

                # プラグインに必要な引数を渡す
                # プラグイン側で params から "smoothing_method" などを取得する
                divergent_algo_func(
                    colored,            # 変更対象の全体画像配列
                    divergent_mask,     # このアルゴリズムが担当するマスク
                    iterations,         # 全体の反復回数
                    z_vals,             # 全体のZ値
                    cmap_func,          # カラーマップ関数
                    params,             # パネルからの全パラメータ (プラグインが必要なものを選択)
                    logger,
                    config
                )
                logger.log(LogLevel.SUCCESS, f"発散部分の着色完了: '{divergent_algo_name}'")
            except Exception as algo_e:
                logger.log(LogLevel.ERROR, f"発散アルゴリズム '{divergent_algo_name}' 実行中にエラー: {algo_e}", exc_info=True)
                raise ColorAlgorithmError(f"Error during divergent algorithm '{divergent_algo_name}'.") from algo_e
        else:
            logger.log(LogLevel.INFO, "発散領域が存在しないため、発散部分の着色をスキップします。")

        # --- 3.2 非発散部分の着色 ---
        if np.any(non_divergent_mask):
            logger.log(LogLevel.INFO, f"非発散部分の着色開始: アルゴリズム='{non_divergent_algo_name}' (プラグイン)")
            try:
                # 発散部と同様にプラグイン関数を呼び出す
                # gradient_values のような特殊な引数が必要な場合は、
                # プラグイン側で計算するか、この manager で計算して渡すか、設計による。
                # ここでは、もし 'gradient' プラグインなら manager で計算して渡す例を示す。
                additional_args = {}
                if non_divergent_algo_name == "gradient_based": # プラグイン名に合わせて変更
                    logger.log(LogLevel.DEBUG, "グラデーション値を計算します...")
                    gradient_values = compute_gradient(image_shape, logger) # compute_gradient は既存
                    additional_args['gradient_values'] = gradient_values
                    logger.log(LogLevel.DEBUG, f"グラデーション値 計算完了: shape={gradient_values.shape}")


                non_divergent_algo_func(
                    colored,
                    non_divergent_mask,
                    iterations, # 非発散部でも iteration を使うアルゴリズムがあるかもしれない
                    z_vals,
                    non_cmap_func,
                    params,
                    logger,
                    config,
                    **additional_args # 追加の引数をキーワード引数として渡す
                )
                logger.log(LogLevel.SUCCESS, f"非発散部分の着色完了: '{non_divergent_algo_name}'")
            except Exception as algo_e:
                logger.log(LogLevel.ERROR, f"非発散アルゴリズム '{non_divergent_algo_name}' 実行中にエラー: {algo_e}", exc_info=True)
                raise ColorAlgorithmError(f"Error during non-divergent algorithm '{non_divergent_algo_name}'.") from algo_e
        else:
            logger.log(LogLevel.INFO, "非発散領域が存在しないため、非発散部分の着色をスキップします。")

        end_perf_counter = time.perf_counter()
        logger.log(LogLevel.SUCCESS, f"全着色処理完了 ({end_perf_counter - start_perf_counter:.4f} 秒)")

        # --- 4. 結果のキャッシュと返却 (変更なし) ---
        cache.put_cache(cache_params, colored.copy())
        logger.log(LogLevel.DEBUG,
            f"最終的な色付き float 配列の統計: dtype={colored.dtype}, "
            f"shape={colored.shape}, min={np.min(colored):.1f}, max={np.max(colored):.1f}"
        )
        return colored

    except ColorAlgorithmError:
        raise
    except Exception as e:
        logger.log(LogLevel.CRITICAL, f"色付け処理の準備または後処理中に予期しないエラーが発生しました: {e}", exc_info=True)
        raise ColorAlgorithmError("Coloring failed due to an unexpected internal error.") from e
