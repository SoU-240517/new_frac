import numpy as np
import time
from coloring.manager import apply_coloring_algorithm
from debug import DebugLogger, LogLevel
from typing import Dict, Any, Callable, Optional
from PIL import Image, ImageTk

"""フラクタル画像生成エンジン
このモジュールはフラクタル画像の生成を担当する
主な機能：
1. 動的解像度制御
   - ズームレベルに応じて最適な解像度を自動調整
   - パフォーマンスと品質のバランスを取る
2. フラクタル計算
   - Mandelbrot集合とJulia集合の生成
   - 高精度な複素数計算
3. レンダリング最適化
   - スーパーサンプリングによる高品質画像生成
   - パフォーマンス最適化された計算
"""

def _calculate_dynamic_resolution(width: float, config: Dict[str, Any], logger: DebugLogger) -> int:
    """ズームレベルに応じて描画解像度を動的に計算

    対数スケールで解像度を調整し、ズームインするほど高解像度になる

    Args:
        width (float): 描画範囲の幅 (ズームレベルの指標)
        config (Dict[str, Any]): config.json から読み込んだ設定データ
        logger (DebugLogger): デバッグログ用

    Returns:
        int: 計算された描画解像度（ピクセル数）

    Notes:
        - 基準幅（4.0）に対して対数スケールで解像度を調整
        - 最小解像度と最大解像度でクリップされる
        - ゼロ割防止のため width は 1e-9 でクリップされる
    """
    # 設定ファイルから動的解像度のパラメータを取得
    dr_config = config.get("fractal_settings", {}).get("dynamic_resolution", {})
    # 各パラメータにフォールバック用のデフォルト値を設定
    base_res = dr_config.get("base", 600)
    min_res = dr_config.get("min", 400)
    max_res = dr_config.get("max", 1200)
    log_factor = dr_config.get("log_factor", 5.0) # 対数計算用係数
    logger.log(LogLevel.DEBUG, f"動的解像度パラメータ: base={base_res}, min={min_res}, max={max_res}, factor={log_factor}")

    # 対数スケールでズームファクターを計算
    # width=4.0 を基準 (widthが大きいほどズームアウト)
    # width が小さい (ズームイン) ほど zoom_factor は大きくなる
    # +1 は log(1)=0 を避けるため & width=基準値 で zoom_factor=log(factor/基準値+1) となるように
    # 例: width=4.0, factor=5.0 -> log(5/4+1) = log(2.25) approx 0.81
    #     width=1.0, factor=5.0 -> log(5/1+1) = log(6)   approx 1.79 (ズームイン)
    #     width=0.1, factor=5.0 -> log(5/0.1+1)= log(51)  approx 3.93 (さらにズームイン)
    base_width_for_log = 4.0 # この値も設定ファイル化可能
    # widthが非常に小さい場合に log 引数が負にならないようにクリップ
    safe_width = max(width, 1e-9) # ゼロ割防止も兼ねる
    zoom_factor_log = np.log(log_factor / safe_width + 1.0)
    logger.log(LogLevel.DEBUG, f"計算された対数ズームファクター: {zoom_factor_log:.3f} (width={width})")

    # zoom_factorにbase_resを掛けて基本解像度を決定
    resolution = int(base_res * zoom_factor_log)
    logger.log(LogLevel.DEBUG, f"基本解像度計算結果: {resolution}")

    # 最小解像度と最大解像度でクリップ
    final_resolution = np.clip(resolution, min_res, max_res)
    logger.log(LogLevel.DEBUG, f"最終動的解像度: {final_resolution} (min={min_res}, max={max_res} でクリップ)")
    return final_resolution

def _create_fractal_grid(params: dict, super_resolution_x: int, super_resolution_y: int, logger: DebugLogger) -> np.ndarray:
    """フラクタル計算用の複素数グリッドを生成

    Args:
        params (dict): フラクタルのパラメータ
            - center_x: 中心X座標 (float)
            - center_y: 中心Y座標 (float)
            - width:  描画範囲の幅 (float)
            - height: 描画範囲の高さ (float)
            - rotation: 回転角度 (float, 度)
        super_resolution_x (int): 水平方向の解像度
        super_resolution_y (int): 垂直方向の解像度
        logger (DebugLogger): デバッグログ出力用

    Returns:
        np.ndarray: 複素数グリッド (dtype=np.complex64)

    Notes:
        - width > 1.0 の場合は np.float16 を使用
        - width <= 1.0 の場合は np.float32 を使用
        - 回転角度が指定された場合はグリッドを回転させる
    """
    center_x = params.get("center_x", 0.0)
    center_y = params.get("center_y", 0.0)
    width = params.get("width", 4.0)
    # 高さは params に含まれている想定 (MainWindow で width と height_ratio から計算済み)
    height = params.get("height", width * (9 / 16)) # フォールバック

    # データ型選択ロジック (これも設定ファイル化可能だが一旦維持)
    dtype = np.float16 if width > 1.0 else np.float32
    x = np.linspace(center_x - width/2, center_x + width/2, super_resolution_x, dtype=dtype)
    y = np.linspace(center_y - height/2, center_y + height/2, super_resolution_y, dtype=dtype)

    X, Y = np.meshgrid(x, y)
    Z = X + 1j * Y
    # complex64 で計算することが多いので型を変換
    Z = Z.astype(np.complex64)

    rotation_deg = params.get("rotation", 0.0)
    if rotation_deg != 0:
        logger.log(LogLevel.DEBUG, f"回転適用: {rotation_deg:.2f} 度")
        rotation_rad = np.radians(rotation_deg)
        # 回転中心はグリッドの中心
        center_complex = complex(center_x, center_y)
        # グリッド座標を回転中心からの相対座標に変換
        Z_relative = Z - center_complex
        # 回転演算子 (オイラーの公式 e^(i*theta))
        rotation_operator = np.exp(1j * rotation_rad)
        # 相対座標を回転
        Z_rotated_relative = Z_relative * rotation_operator
        # 回転後の座標を元の中心に戻す
        Z = Z_rotated_relative + center_complex
        logger.log(LogLevel.SUCCESS, "グリッド回転適用完了")

    return Z

def _compute_fractal(
    Z: np.ndarray,
    params: dict,
    compute_function: Callable, # 計算関数を引数で受け取る
    logger: DebugLogger
) -> Optional[Dict[str, np.ndarray]]: # 戻り値を Optional に変更

    """フラクタル計算を実行

    Args:
        Z (np.ndarray): 複素数グリッド
        params (dict): フラクタルのパラメータ
            - fractal_type_name: フラクタルの種類 ("Julia" or "Mandelbrot")
            - c_real, c_imag: Julia用複素数 C の実部・虚部
            - z0_real, z0_imag: Mandelbrot用初期値 Z0 の実部・虚部
            - max_iterations: 最大反復回数
        compute_function (Callable): フラクタル計算関数
        logger (DebugLogger): デバッグログ出力用

    Returns:
        Optional[Dict[str, np.ndarray]]: 計算結果
            - iterations: 反復回数配列
            - mask: 発散判定マスク
            - z_vals: 最終複素数値配列

    Raises:
        TypeError: 計算関数の呼び出し時に引数の型が不正な場合
        Exception: 計算中に予期せぬエラーが発生した場合

    Notes:
        - Julia集合の場合は C パラメータを使用
        - Mandelbrot集合の場合は Z0 パラメータを使用
        - 計算結果が None の場合はエラーが発生したことを示す
    """
    start_time = time.perf_counter()

    fractal_type_name = params.get("fractal_type_name", "Unknown") # ParameterPanel から渡される名前
    max_iter = params.get("max_iterations", 100)
    logger.log(LogLevel.INFO, f"フラクタル計算開始: タイプ={fractal_type_name}, 最大反復={max_iter}")

    # パラメータから計算関数に必要な引数を抽出する
    # ここは少し工夫が必要。現状の compute_julia と compute_mandelbrot の引数シグネチャが異なるため。
    # 案1: 各計算関数が必要な引数を params 辞書から **kwargs のように受け取るように修正する
    # 案2: タイプに応じて必要な引数をここで組み立てる (あまり良くない)
    # 案3: 計算関数に渡す引数を標準化する (例: compute(Z, max_iter, specific_params: dict, logger))

    # --- 案1 or 案3 を想定した実装例 (関数側が **params で受け取る or 標準化されている場合) ---
    try:
        # 計算関数が必要とするパラメータを params から抽出
        # inspect を使って関数の引数を調べることもできるが、複雑になる
        # ここでは params 全体を渡すか、必要なキーだけ渡すことを想定
        # 例: Julia なら C を、Mandelbrot なら Z0 を params から取り出して渡す必要がある

        # シンプルに、計算関数が必要なものを params から取り出すと仮定
        # (計算関数側で params.get("c_real", default) のようにアクセスする)
        # Mandelbrot の Z0 は params["z0_real"], params["z0_imag"] として渡ってくる想定
        # Julia の C は params["c_real"], params["c_imag"] として渡ってくる想定

        # compute_julia(Z, C, max_iter, logger)
        # compute_mandelbrot(Z, Z0, max_iter, logger)
        # に合わせるための引数準備

        func_args = [Z] # 最初の引数は Z グリッド

        # Julia の場合
        if fractal_type_name == "Julia": # プラグイン名で判定するのは良くないかも？ 関数オブジェクトで判定？
             c_real = params.get("c_real", -0.8) # ParameterPanel で取得した値
             c_imag = params.get("c_imag", 0.156)
             func_args.append(complex(c_real, c_imag)) # 第2引数 C
        # Mandelbrot の場合
        elif fractal_type_name == "Mandelbrot":
             z0_real = params.get("z0_real", 0.0) # ParameterPanel で取得した値
             z0_imag = params.get("z0_imag", 0.0)
             func_args.append(complex(z0_real, z0_imag)) # 第2引数 Z0
        # 他のプラグインの場合は、引数をどう渡すかルールを決める必要がある
        # else:
        #    logger.log(LogLevel.WARNING, f"未知のフラクタルタイプ '{fractal_type_name}' のための引数準備ロジックがありません。")
            # プラグイン固有パラメータを辞書で渡す？
            # specific_params = {k: v for k, v in params.items() if k not in [...共通パラメータ...]}
            # func_args.append(specific_params) # 第2引数として辞書を渡すルール？

        func_args.append(max_iter) # 第3引数 max_iter
        func_args.append(logger)   # 第4引数 logger

        # 計算関数を呼び出し
        results = compute_function(*func_args) # 引数を展開して渡す

        # results が辞書であることを確認 (より厳密なチェックが望ましい)
        if not isinstance(results, dict):
             logger.log(LogLevel.ERROR, f"フラクタル計算関数 '{compute_function.__name__}' が辞書を返しませんでした。")
             return None

        logger.log(LogLevel.SUCCESS, f"{fractal_type_name} 計算完了 ({time.perf_counter() - start_time:.3f}秒)")
        return results

    except TypeError as e:
         logger.log(LogLevel.CRITICAL, f"フラクタル計算関数の呼び出しで TypeError: {e}。引数を確認してください。")
         return None
    except Exception as e:
         logger.log(LogLevel.CRITICAL, f"フラクタル計算中に予期せぬエラー ({fractal_type_name}): {e}")
         return None
    # ---------------------------------------------------------------------------------------

def _downsample_image(
    high_res_image: np.ndarray,
    target_resolution_x: int,
    target_resolution_y: int,
    samples_per_pixel_x: int,
    samples_per_pixel_y: int,
    logger: DebugLogger
) -> np.ndarray:
    """高解像度画像をダウンサンプリングしてアンチエイリアシング

    Args:
        high_res_image (np.ndarray): 高解像度画像 (RGBA想定)
        target_resolution_x (int): 目標解像度 X
        target_resolution_y (int): 目標解像度 Y
        samples_per_pixel_x (int): X方向の1ピクセルあたりのサンプル数
        samples_per_pixel_y (int): Y方向の1ピクセルあたりのサンプル数
        logger (DebugLogger): デバッグログ出力用

    Returns:
        np.ndarray: ダウンサンプリングされた画像

    Notes:
        - サンプル数が1の場合はダウンサンプリングをスキップ
        - サンプル数が1より大きい場合はダウンサンプリングを実行
    """
    try:
        # 期待される高解像度画像の形状
        expected_height = target_resolution_y * samples_per_pixel_y
        expected_width = target_resolution_x * samples_per_pixel_x
        # チャンネル数を取得 (通常は4: RGBA)
        channels = high_res_image.shape[2] if high_res_image.ndim == 3 else 1

        expected_shape = (expected_height, expected_width, channels) if channels > 1 else (expected_height, expected_width)
        logger.log(LogLevel.DEBUG, f"ダウンサンプリング: 入力形状={high_res_image.shape}, 期待形状={expected_shape}, 目標形状=({target_resolution_y}, {target_resolution_x}, {channels})")

        if high_res_image.shape[:2] == expected_shape[:2]:
            # reshape して mean を取る
            # (target_y, samples_y, target_x, samples_x, channels) の形に変形
            reshaped = high_res_image.reshape(
                target_resolution_y, samples_per_pixel_y,
                target_resolution_x, samples_per_pixel_x,
                channels
            )
            # samples_y (axis 1) と samples_x (axis 3) で平均を取る
            downsampled = reshaped.mean(axis=(1, 3))
            logger.log(LogLevel.SUCCESS, f"ダウンサンプリング成功: 出力形状={downsampled.shape}")

        else:
            # 形状が不正な場合、エラーログを出力し、目標解像度で赤色の画像を返す
            logger.log(LogLevel.ERROR, f"ダウンサンプリングエラー: 形状が不正です。期待値: {expected_shape}, 実際: {high_res_image.shape}")
            # RGBA 画像を返す (エラーを示す赤色)
            error_color = [255, 0, 0, 255] if channels == 4 else [255]
            downsampled = np.full((target_resolution_y, target_resolution_x, channels), error_color, dtype=high_res_image.dtype) # データ型を合わせる

    except ValueError as e:
        # reshape などでエラーが発生した場合
        logger.log(LogLevel.ERROR, f"ダウンサンプリング中のValueError: {e}")
        channels = high_res_image.shape[2] if high_res_image.ndim == 3 else 1
        error_color = [255, 0, 0, 255] if channels == 4 else [255]
        downsampled = np.full((target_resolution_y, target_resolution_x, channels), error_color, dtype=high_res_image.dtype)
    except Exception as e:
        # その他の予期せぬエラー
        logger.log(LogLevel.CRITICAL, f"ダウンサンプリング中に予期せぬエラー: {e}")
        channels = high_res_image.shape[2] if high_res_image.ndim == 3 else 1
        error_color = [255, 0, 0, 255] if channels == 4 else [255]
        downsampled = np.full((target_resolution_y, target_resolution_x, channels), error_color, dtype=high_res_image.dtype)

    return downsampled

def render_fractal(
    params: Dict,
    compute_function: Callable, # フラクタル計算関数
    logger: DebugLogger,
    config: Dict[str, Any],
    coloring_loader # <<<--- 追加: MainWindowから渡される ColoringPluginLoader のインスタンス
) -> Optional[ImageTk.PhotoImage]:
    """
    指定されたパラメータと計算関数を使用してフラクタル画像を生成し、着色する。

    Args:
        params (Dict): フラクタル描画と着色に必要なパラメータ群。
                       (例: center_x, width, max_iterations, diverge_algorithm, diverge_colormap など)
        compute_function (Callable): フラクタル計算を行う関数。
                                     (例: plugins.fractal_types.mandelbrot.compute 等)
        logger (DebugLogger): ロガーインスタンス。
        config (Dict[str, Any]): アプリケーション全体の設定。
        coloring_loader (ColoringPluginLoader): ロードされた着色プラグインを管理するローダー。

    Returns:
        Optional[ImageTk.PhotoImage]: 生成されたフラクタル画像の PhotoImage オブジェクト。
                                      エラーが発生した場合は None。
    """
    logger.log(LogLevel.CALL, "render_fractal 関数の実行開始")
    start_time_render = time.perf_counter()

    # キャンバスサイズ (ピクセル単位)
    # params から 'canvas_width', 'canvas_height' を取得することを想定
    # これらは FractalCanvas から渡されるか、config のデフォルト値を使用する
    canvas_width = params.get("canvas_width", config.get("ui_settings", {}).get("initial_canvas_width", 800))
    canvas_height = params.get("canvas_height", config.get("ui_settings", {}).get("initial_canvas_height", 600))

    # フラクタル計算に必要な座標グリッドを生成
    # (この部分は既存のロジック、または compute_function 内部で行われるかもしれません)
    # ここでは compute_function が座標グリッドの面倒を見ると仮定します。
    # x_coords, y_coords = create_coordinate_grid(params, canvas_width, canvas_height, logger)

    # フラクタル計算の実行
    logger.log(LogLevel.CALL, "フラクタル計算処理の開始")
    start_time_compute = time.perf_counter()
    try:
        # compute_function は (params, canvas_width, canvas_height, logger) のような引数を期待
        # 戻り値は (iterations, mask, z_values, final_x_coords, final_y_coords) のようなタプルを想定
        # compute_function の仕様に合わせて調整してください。
        computation_results = compute_function(params, canvas_width, canvas_height, logger)
        # computation_results が None でないこと、および期待する要素を含んでいることを確認
        if computation_results is None:
            logger.log(LogLevel.ERROR, "フラクタル計算関数が None を返しました。")
            return None

        # 計算結果を分解 (compute_function の戻り値の構造に依存)
        # 例: iterations, mask, z_values, final_x_coords, final_y_coords = computation_results
        # 呼び出し元の _update_fractal_thread と整合性を取る必要があります。
        # ここでは、タプルで返ってくると仮定します。
        # もし辞書で返ってくるなら、 `iterations = computation_results.get('iterations')` のように取得します。
        # 今回は、compute_function が直接 iterations, mask, z_values などを返すのではなく、
        # それらを要素とする辞書またはオブジェクトを返すことを想定してみましょう。
        # (現在のコードでは compute_function が直接 iterations 等を返すわけではなさそうなので、
        #  compute_function の実装に依存します)

        # 仮に compute_function が辞書を返すとすると:
        # iterations = computation_results.get('iterations')
        # mask = computation_results.get('mask')
        # z_values = computation_results.get('z_vals')
        # final_x_coords = computation_results.get('final_x_coords') # 必要に応じて
        # final_y_coords = computation_results.get('final_y_coords') # 必要に応じて

        # 現状の FractalTypeLoader のプラグイン (mandelbrot.py, julia.py) は
        # iterations, mask, z_values をタプルで返しているようです。
        iterations, mask, z_values = computation_results[:3] # 最初の3要素を取得
        # final_x_coords, final_y_coords は compute_function が返すかどうかに依存
        final_x_coords = computation_results[3] if len(computation_results) > 3 else None
        final_y_coords = computation_results[4] if len(computation_results) > 4 else None


    except Exception as e:
        logger.log(LogLevel.ERROR, f"フラクタル計算中にエラーが発生: {e}", exc_info=True)
        return None
    end_time_compute = time.perf_counter()
    logger.log(LogLevel.SUCCESS, f"フラクタル計算処理の完了 (所要時間: {end_time_compute - start_time_compute:.4f} 秒)")

    # --- ここからが着色処理のセクションです ---
    # 「if iterations is not None and mask is not None and z_values is not None:」のブロックは
    # フラクタル計算が成功し、着色に必要なデータが得られた場合に実行されます。
    if iterations is not None and mask is not None and z_values is not None:
        # 着色に必要なデータを辞書にまとめる
        # manager.py の apply_coloring_algorithm がこの辞書を受け取る
        results_for_coloring = {
            'iterations': iterations,
            'mask': mask,
            'z_vals': z_values,
            # final_x_coords や final_y_coords も着色に使う場合はここに追加
            'final_x_coords': final_x_coords,
            'final_y_coords': final_y_coords
        }

        logger.log(LogLevel.CALL, "着色処理 (apply_coloring_algorithm) の呼び出し開始")
        start_time_coloring = time.perf_counter()
        try:
            # `apply_coloring_algorithm` を呼び出す際に `coloring_loader` を渡します。
            # これが今回の修正の主要なポイントです。
            colored_array_float = apply_coloring_algorithm(
                results_for_coloring, # 計算結果
                params,               # UIなどからのパラメータ
                logger,
                config,
                coloring_loader       # <<<--- ここで coloring_loader を渡す
            )
        except Exception as e:
            logger.log(LogLevel.ERROR, f"apply_coloring_algorithm でエラーが発生: {e}", exc_info=True)
            return None # エラー時は None を返す
        end_time_coloring = time.perf_counter()
        logger.log(LogLevel.SUCCESS, f"着色処理の完了 (所要時間: {end_time_coloring - start_time_coloring:.4f} 秒)")

        if colored_array_float is None:
            logger.log(LogLevel.ERROR, "着色処理の結果が None でした。")
            return None

        # float32 (0-255) の配列を uint8 (0-255) に変換
        try:
            # 値が確実に0-255の範囲内にあることを確認（クリッピング）
            colored_array_uint8 = np.clip(colored_array_float, 0, 255).astype(np.uint8)
            logger.log(LogLevel.DEBUG,
                       f"uint8変換後の配列統計: dtype={colored_array_uint8.dtype}, "
                       f"shape={colored_array_uint8.shape}, min={np.min(colored_array_uint8)}, max={np.max(colored_array_uint8)}")
        except Exception as e:
            logger.log(LogLevel.ERROR, f"着色結果の uint8 への変換中にエラー: {e}", exc_info=True)
            return None

        # NumPy 配列を PIL Image に変換
        try:
            # RGBAモードであることを確認
            if colored_array_uint8.shape[2] == 4:
                pil_image = Image.fromarray(colored_array_uint8, 'RGBA')
            elif colored_array_uint8.shape[2] == 3:
                pil_image = Image.fromarray(colored_array_uint8, 'RGB')
            else:
                logger.log(LogLevel.ERROR, f"予期しないチャネル数を持つ配列: {colored_array_uint8.shape}")
                return None
            logger.log(LogLevel.SUCCESS, "PIL Image への変換成功")
        except Exception as e:
            logger.log(LogLevel.ERROR, f"NumPy配列からPIL Imageへの変換中にエラー: {e}", exc_info=True)
            return None

        # PIL Image を Tkinter PhotoImage に変換
        try:
            photo_image = ImageTk.PhotoImage(pil_image)
            logger.log(LogLevel.SUCCESS, "Tkinter PhotoImage への変換成功")
            end_time_render = time.perf_counter()
            logger.log(LogLevel.SUCCESS, f"render_fractal 関数の実行完了 (総所要時間: {end_time_render - start_time_render:.4f} 秒)")
            return photo_image
        except Exception as e:
            logger.log(LogLevel.ERROR, f"PIL ImageからTkinter PhotoImageへの変換中にエラー: {e}", exc_info=True)
            return None
    else:
        # フラクタル計算の結果、着色に必要なデータが得られなかった場合
        logger.log(LogLevel.ERROR, "フラクタル計算結果が無効（iterations, mask, または z_values が None）なため、着色処理をスキップしました。")
        return None
