import matplotlib.pyplot as plt
import numpy as np
import time
from typing import Dict, Callable, Any, Optional
from debug import DebugLogger,LogLevel
from .utils import ColorAlgorithmError
from .gradient import compute_gradient
from .cache import ColorCache # キャッシュ管理クラス

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


def apply_coloring_algorithm(
    results: Dict,
    params: Dict,
    logger: DebugLogger,
    config: Dict[str, Any],
    coloring_plugin_loader: Any # ColoringPluginLoader インスタンス
) -> np.ndarray:
    """フラクタルの着色アルゴリズムを適用するディスパッチャ関数
    - ColoringPluginLoader からアルゴリズム関数を取得し、適用する
    - 結果をキャッシュし、パフォーマンスを向上させる
    Args:
        results (dict): フラクタル計算結果。'iterations' (反復回数), 'mask' (発散マスク), 'z_vals' (複素数値) を含む
        params (dict): 着色パラメータ。使用するアルゴリズム名やカラーマップなどを含む
        logger (DebugLogger): デバッグログ用ロガー
        config (Dict[str, Any]): config.json から読み込んだ設定データ
        coloring_plugin_loader (ColoringPluginLoader): カラーリングプラグインローダーのインスタンス
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

    # --- 2. アルゴリズム関数の取得 (ColoringPluginLoader から) ---
    try:
        # 使用するアルゴリズムの取得
        divergent_algo_name = params.get('diverge_algorithm', default_divergent_algo_name)
        non_divergent_algo_name = params.get('non_diverge_algorithm', default_non_divergent_algo_name)

        # --- アルゴリズム情報（関数と引数リスト）を取得 ---
        divergent_algo_info = coloring_plugin_loader.get_divergent_algorithm_info(divergent_algo_name)
        non_divergent_algo_info = coloring_plugin_loader.get_non_divergent_algorithm_info(non_divergent_algo_name)

        if not divergent_algo_info:
            raise ColorAlgorithmError(f"発散部アルゴリズム '{divergent_algo_name}' の情報が見つかりません")
        if not non_divergent_algo_info:
            raise ColorAlgorithmError(f"非発散部アルゴリズム '{non_divergent_algo_name}' の情報が見つかりません")

        divergent_algo = divergent_algo_info.get('function')
        divergent_arg_list = divergent_algo_info.get('argument_list', [])

        non_divergent_algo = non_divergent_algo_info.get('function')
        non_divergent_arg_list = non_divergent_algo_info.get('argument_list', [])

        if divergent_algo is None:
            raise ColorAlgorithmError(f"発散部アルゴリズム '{divergent_algo_name}' がない")
        if non_divergent_algo is None:
            raise ColorAlgorithmError(f"非発散部アルゴリズム '{non_divergent_algo_name}' がない")
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

    # --- 全ての利用可能な引数をマップとして準備 ---
    gradient_values = None # グラデーションアルゴリズム用に事前に準備
    # 'グラデーション'アルゴリズムが選択され、かつその引数リストに'gradient_values'が含まれている場合に計算
    # (non_divergent_algo_name だけでなく、実際の引数リストも参照することがより堅牢)
    if non_divergent_algo_name == 'グラデーション' and 'gradient_values' in non_divergent_arg_list:
        logger.log(LogLevel.DEBUG, "グラデーション値を計算します...")
        gradient_values = compute_gradient(image_shape, logger)
        logger.log(LogLevel.DEBUG, "グラデーション値 計算完了", {"shape": gradient_values.shape if gradient_values is not None else "None"})

    all_available_args = {
        "colored": colored,
        "iterations": iterations,
        "z_vals": z_vals,
        "params": params,
        "logger": logger,
        "divergent_mask": divergent_mask,   # 発散アルゴリズム用
        "cmap_func": cmap_func,             # 発散アルゴリズム用
        "non_divergent_mask": non_divergent_mask, # 非発散アルゴリズム用
        "non_cmap_func": non_cmap_func,         # 非発散アルゴリズム用
        "gradient_values": gradient_values,
    }

    # --- 3. 着色処理の実行 ---
    try:
        start_perf_counter = time.perf_counter()
        # --- 3.1 発散部分の着色 ---
        if np.any(divergent_mask): # 処理対象が存在するかチェック
            try:
                args_to_pass = [all_available_args[arg_name] for arg_name in divergent_arg_list if arg_name in all_available_args]
                if len(args_to_pass) != len(divergent_arg_list):
                    missing_args = [arg for arg in divergent_arg_list if arg not in all_available_args]
                    raise ColorAlgorithmError(f"発散部アルゴリズム '{divergent_algo_name}' の引数不足: {missing_args}")
                divergent_algo(*args_to_pass)
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
                # --- 動的な引数渡し ---
                # JSON内の引数名とall_available_argsのキー名をマッピングする必要がある場合がある
                # 例えば、JSON側が 'mask' や 'cmap_func' という汎用的な名前を使い、
                # manager.py側で状況に応じて divergent_mask/non_divergent_mask を渡す場合など。
                # ここでは、JSONの引数名が all_available_args のキーと一致すると仮定。
                # ただし、'cmap_func' や 'mask' などの汎用名は、
                # non_divergent 用の 'non_cmap_func', 'non_divergent_mask' にマップする。
                current_context_args = all_available_args.copy()
                current_context_args['cmap_func'] = all_available_args['non_cmap_func'] # JSONが'cmap_func'を要求したらnon_cmap_funcを渡す
                current_context_args['divergent_mask'] = all_available_args['non_divergent_mask'] # JSONが'divergent_mask'を要求したらnon_divergent_maskを渡す
                args_to_pass = [current_context_args[arg_name] for arg_name in non_divergent_arg_list if arg_name in current_context_args]
                if len(args_to_pass) != len(non_divergent_arg_list):
                    missing_args = [arg for arg in non_divergent_arg_list if arg not in current_context_args]
                    raise ColorAlgorithmError(f"非発散部アルゴリズム '{non_divergent_algo_name}' の引数不足: {missing_args}")
                non_divergent_algo(*args_to_pass)
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
