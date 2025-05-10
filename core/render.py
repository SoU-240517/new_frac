"""
フラクタル画像生成エンジン

このモジュールはフラクタル画像の生成を担当し、以下の主要な機能を提供します：

主な機能：
- 動的解像度制御：ズームレベルに応じた最適な解像度の自動調整
- フラクタル計算：Mandelbrot集合とJulia集合の計算
- レンダリング最適化：スーパーサンプリングによる高品質な画像生成
- カラーリング：複数の着色アルゴリズムとカラーマップのサポート

特徴：
- 精度とパフォーマンスのバランスを考慮したデータ型選択
- 回転角度のサポートによる柔軟な視点制御
- エラーハンドリングとデバッグログの充実
"""

import numpy as np
import time
from coloring import manager
from typing import Dict, Any, Callable, Optional
from debug import DebugLogger, LogLevel

def _calculate_dynamic_resolution(width: float, config: Dict[str, Any], logger: DebugLogger) -> int:
    """
    ズームレベルに応じて描画解像度を動的に計算

    対数スケールで解像度を調整し、ズームインするほど解像度が上がる

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
        - log_factor は解像度調整の感度を制御（大きいほど解像度の変化が緩やか）
    """
    # 設定ファイルから動的解像度のパラメータを取得
    dr_config = config.get("fractal_settings", {}).get("dynamic_resolution_settings", {})
    base_res = dr_config.get("base", 600)
    min_res = dr_config.get("min", 400)
    max_res = dr_config.get("max", 1200)
    log_factor = dr_config.get("log_factor", 5.0) # 対数計算用係数
    logger.log(LogLevel.LOAD, "設定読込：動的解像度パラメータ",
                {"base_res": base_res, "min_res": min_res, "max_res": max_res, "log_factor": log_factor})

    # width が非常に小さい場合に log 引数が負にならないようにクリップ
    safe_width = max(width, 1e-9) # ゼロ割防止も兼ねる
    zoom_factor_log = np.log(log_factor / safe_width + 1.0)
    logger.log(LogLevel.DEBUG, f"対数ズームファクター計算結果: {zoom_factor_log:.3f} (width={width})")

    # zoom_factor に base_res を掛けて基本解像度を決定
    resolution = int(base_res * zoom_factor_log)
    logger.log(LogLevel.DEBUG, "基本解像度計算結果", {"resolution": resolution})

    # 最小解像度と最大解像度でクリップ
    final_resolution = np.clip(resolution, min_res, max_res)
    logger.log(LogLevel.DEBUG, f"最終動的解像度: {final_resolution} (min={min_res}, max={max_res} でクリップ)")

    return final_resolution

def _create_fractal_grid(
    params: dict,
    super_resolution_x: int,
    super_resolution_y: int,
    logger: DebugLogger
) -> np.ndarray:
    """
    フラクタル計算用の複素数グリッドを生成

    Args:
        params (dict): フラクタルのパラメータ
            - center_x: 中心X座標 (float)
            - center_y: 中心Y座標 (float)
            - width:  描画範囲の幅 (float)
            - height: 描画範囲の高さ (float)
            - rotation: 回転角度 (float, 度)
        super_resolution_x (int): 水平方向のスーパーサンプリング解像度
        super_resolution_y (int): 垂直方向のスーパーサンプリング解像度
        logger (DebugLogger): デバッグログ出力用

    Returns:
        np.ndarray: 複素数グリッド (dtype=np.complex64)

    Notes:
        - データ型選択ロジック：
          * width > 1.0 の場合: np.float16 を使用（メモリ効率重視）
          * width <= 1.0 の場合: np.float32 を使用（精度重視）
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

    return Z

def _compute_fractal(
    Z: np.ndarray,
    params: dict,
    compute_function: Callable[[np.ndarray, dict, DebugLogger], Dict[str, np.ndarray]],
    logger: DebugLogger
) -> Optional[Dict[str, np.ndarray]]:
    """
    フラクタルの計算

    Args:
        Z (np.ndarray): 複素数グリッド
        params (dict): フラクタルのパラメータ
            - fractal_type_name: フラクタルの種類 ("Julia" or "Mandelbrot")
            - c_real, c_imag: Julia用複素数 C の実部・虚部
            - z0_real, z0_imag: Mandelbrot用初期値 Z0 の実部・虚部
            - max_iterations: 最大反復回数
        compute_function (Callable): フラクタル計算関数
            - 第1引数: 複素数グリッド (np.ndarray)
            - 第2引数: フラクタルのパラメータ (dict)
            - 第3引数: デバッグログ (DebugLogger)
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
        - エラーハンドリング：
          * TypeError: 計算関数の引数型チェック
          * その他の例外: 計算中の予期せぬエラー
    """
    try:
        results = compute_function(Z, params, logger)
        if not isinstance(results, dict):
            logger.log(LogLevel.ERROR, f"計算関数が辞書を返さない: {type(results)}")
            return None
        return results
    except Exception as e:
        logger.log(LogLevel.CRITICAL, f"計算中にエラー: {e}")
        return None

def _downsample_image(
    high_res_image: np.ndarray,
    target_resolution_x: int,
    target_resolution_y: int,
    samples_per_pixel_x: int,
    samples_per_pixel_y: int,
    logger: DebugLogger
) -> np.ndarray:
    """
    高解像度画像をダウンサンプリングしてアンチエイリアシング

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
    params: dict,
    compute_function: Callable, # 計算関数を受け取る
    logger: DebugLogger,
    config: Dict[str, Any],
    coloring_plugin_loader: Any # ColoringPluginLoader インスタンスを追加
) -> np.ndarray:
    """
    フラクタル画像を生成

    Args:
        params (dict): フラクタルのパラメータ
            - fractal_type_name: フラクタルの種類 ("Julia" or "Mandelbrot")
            - c_real, c_imag: Julia用複素数 C の実部・虚部
            - z0_real, z0_imag: Mandelbrot用初期値 Z0 の実部・虚部
            - max_iterations: 最大反復回数
            - center_x, center_y: 画像の中心座標
            - width, height: 描画範囲のサイズ
            - rotation: 回転角度 (度)
            - diverge_algorithm: 発散領域の着色アルゴリズム
            - non_diverge_algorithm: 非発散領域の着色アルゴリズム
            - diverge_colormap: 発散領域のカラーマップ
            - non_diverge_colormap: 非発散領域のカラーマップ
            - render_mode: "quick" or "full"
        compute_function (Callable): フラクタル計算関数
        logger (DebugLogger): デバッグログ出力用
        config (Dict[str, Any]): config.json から読み込んだ設定データ
        coloring_plugin_loader (ColoringPluginLoader): カラーリングプラグインローダーのインスタンス

    Returns:
        np.ndarray: RGBA形式のフラクタル画像 (uint8 [0, 255])

    Notes:
        - 動的解像度制御により最適な解像度でレンダリング
        - スーパーサンプリングにより高品質な画像生成
        - カラーリングは coloring.manager モジュールを使用
    """
    render_mode = params.get("render_mode", "quick")  # デフォルトは簡易モード
    current_width = params.get("width", 4.0) # 現在の描画範囲の幅

    dpi = config.get("canvas_settings", {}).get("config_dpi", 100)
    logger.log(LogLevel.LOAD, "設定読込", {"dpi": dpi})

    # 動的解像度計算 (config を渡す)
    resolution = _calculate_dynamic_resolution(current_width, config, logger)

    # 簡易モードでは解像度をさらに下げる
    quick_mode_resolution_factor = config.get("canvas_settings", {}).get("quick_mode_resolution_factor", 0.5)
    logger.log(LogLevel.LOAD, "設定読込", {"quick_mode_resolution_factor": quick_mode_resolution_factor})

    if render_mode == "quick":
        resolution = int(resolution * quick_mode_resolution_factor)
        # 最小解像度を下回らないようにする
        resolution = max(resolution, dpi)

    # アンチエイリアシング設定 (設定ファイルから読み込む)
    ss_config = config.get("fractal_settings", {}).get("super_sampling_settings", {})
    zoom_threshold = ss_config.get("zoom_threshold", 0.8)
    low_samples = ss_config.get("low_samples", 2)
    high_samples = ss_config.get("high_samples", 4)
    logger.log(LogLevel.LOAD, "設定読込", {"zoom_threshold": zoom_threshold, "low_samples": low_samples, "high_samples": high_samples})

    zoom_level = 4.0 / current_width # 基準幅4.0に対する比率 (大きいほどズームイン)

    # 簡易モードではアンチエイリアシング無効 (サンプル数 = 1)
    if render_mode == "quick":
        samples_per_pixel = config.get("canvas_settings", {}).get("samples_per_pixel", 1)
        logger.log(LogLevel.LOAD, "設定読込", {"samples_per_pixel": samples_per_pixel})
    else:
        # ズームレベルに応じてサンプル数を決定
        samples_per_pixel = high_samples if zoom_level >= zoom_threshold else low_samples

    logger.log(LogLevel.DEBUG, f"描画モード: {render_mode}, 解像度: {resolution}x{resolution}, サンプル数: {samples_per_pixel} (ズームレベル={zoom_level:.2f}, 閾値={zoom_threshold})")

    # スーパーサンプリング
    super_resolution_x = resolution * samples_per_pixel
    super_resolution_y = resolution * samples_per_pixel

    # グリッド作成
    Z = _create_fractal_grid(params, super_resolution_x, super_resolution_y, logger)
    logger.log(LogLevel.DEBUG, "フラクタル計算用の複素数グリッドを作成完了", {"shape": Z.shape})

    # フラクタル計算 (計算関数を渡す)
    results = _compute_fractal(Z, params, compute_function, logger)

    # 計算失敗時の処理
    if results is None:
        logger.log(LogLevel.ERROR, "フラクタルの計算に失敗したのでエラー画像を表示")
        # エラー画像 (例: 赤色) を返す
        error_color = [255, 0, 0, 255] # 赤色
        # 最終的な解像度で作成
        final_image = np.full((resolution, resolution, 4), error_color, dtype=np.uint8)
        del Z # メモリ解放
        return final_image

    try:
        # 着色処理
        colored_high_res = manager.apply_coloring_algorithm(
            results,
            params,
            logger,
            config,
            coloring_plugin_loader=coloring_plugin_loader # ローダーを渡す
        )

        # 着色エラーハンドリング
        if not isinstance(colored_high_res, np.ndarray):
             raise TypeError(f"着色処理がndarrayを返さない: {type(colored_high_res)}")
        if colored_high_res.ndim != 3 or colored_high_res.shape[2] != 4:
             raise ValueError(f"着色処理が期待されるRGBA形状を返さない: {colored_high_res.shape}")
    except Exception as e:
        logger.log(LogLevel.CRITICAL, "着色処理中にエラー発生", {"message": e})
        # エラー画像 (例: 紫色) を返す
        error_color = [128, 0, 128, 255] # 紫色
        final_image = np.full((resolution, resolution, 4), error_color, dtype=np.uint8)
        del Z, results # メモリ解放
        return final_image

    # ダウンサンプリング (サンプル数が1より大きい場合のみ)
    if samples_per_pixel > 1:
        logger.log(LogLevel.DEBUG, "ダウンサンプリング実行...")
        # ダウンサンプリング関数呼び出し (解像度とサンプル数を渡す)
        # 正方形を仮定していても X/Y は同じ値
        colored = _downsample_image(
            colored_high_res,
            resolution, resolution, # 目標解像度 X, Y
            samples_per_pixel, samples_per_pixel, # サンプル数 X, Y
            logger
        )
    else:
        # サンプル数1の場合はダウンサンプリング不要
        logger.log(LogLevel.DEBUG, "ダウンサンプリングをスキップ（サンプル数 1 のため）")
        colored = colored_high_res # そのまま使う

    # 最終的な結果を uint8 [0, 255] に変換
    # データ型が float かどうかチェック
    if not np.issubdtype(colored.dtype, np.integer):
        # float の場合、0-255 の範囲にクリップしてから uint8 に変換
         colored = np.clip(colored, 0, 255).astype(np.uint8)
    elif colored.dtype != np.uint8:
        # 既に整数型だが uint8 でない場合 (uint16 など)、警告を出して変換
        logger.log(LogLevel.WARNING, f"最終画像のデータ型が uint8 でない ({colored.dtype}) ので変換実行。")
        colored = np.clip(colored, 0, 255).astype(np.uint8)

    logger.log(LogLevel.DEBUG, "最終的な render_fractal 出力", {"dtype": colored.dtype, "shape": colored.shape})

    # メモリ解放を促す (大きな配列を使った後)
    del Z, results, colored_high_res

    return colored
