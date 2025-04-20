import numpy as np
import time
from coloring import color_algorithms
from fractal.fractal_types import julia, mandelbrot
from ui.zoom_function.debug_logger import DebugLogger
from ui.zoom_function.enums import LogLevel

"""フラクタル画像を生成する主要ロジック部分
- 役割:
    - 設定されたパラメータでフラクタルを描画
"""
# FractalCache クラスは省略（修正なし）

def render_fractal(params, logger: DebugLogger, cache=None) -> np.ndarray:
    """設定されたパラメータでフラクタルを描画（動的解像度版）

    Args:
        params (dict): パラメータ辞書。center_x, center_y, width, rotationなどが含まれる。
        logger (DebugLogger): ログ出力クラス
        cache (FractalCache): キャッシュクラス（現在は使用されていませんが引数として残します）

    Returns:
        np.ndarray: フラクタル画像 (uint8 [0, 255] RGBA 配列)
    """
    # 動的解像度計算 - これは描画する画像のピクセル解像度を決定します
    # params["width"] はデータ座標系での幅です
    resolution = calculate_dynamic_resolution(params.get("width", 4.0))
    logger.log(LogLevel.SUCCESS, f"動的解像度計算完了: {resolution}x{resolution} (width={params.get('width', 4.0):.2f})")

    # アンチエイリアシング設定
    # ズームレベルに応じてサンプル数を調整（widthが小さいほどズームイン）
    zoom_level = 4.0 / params.get("width", 4.0) # 基準となる幅4.0からの相対的なズームレベル
    samples_per_pixel = 2 if zoom_level < 1.0 else 4 # ズームアウト時はサンプル数減らす
    # 必要に応じてサンプル数を増やすことも検討 (例: zoom_levelに応じて動的に計算)
    # samples_per_pixel = max(1, min(4, int(zoom_level**0.5))) # 一例

    logger.log(LogLevel.DEBUG, f"アンチエイリアシング設定：samples_per_pixel={samples_per_pixel}")

    # 実際にフラクタル計算を行うための高解像度グリッドサイズ
    super_resolution_x = resolution * samples_per_pixel
    super_resolution_y = resolution * samples_per_pixel # アンチエイリアシングのため、縦横同じ倍率をかけます

    # 表示領域の中心座標とデータ座標系での幅を取得
    center_x = params.get("center_x", 0.0)
    center_y = params.get("center_y", 0.0)
    width = params.get("width", 4.0)

    # フラクタルを計算する複素平面上の高さ（height）を、
    # 表示領域の縦横比（16:9）に合わせて計算します。
    # 表示幅(width) / 表示高さ(height) = 16 / 9
    height = width * (9 / 16)

    # 修正されたログ出力: self.logger を logger に変更
    logger.log(LogLevel.DEBUG, f"フラクタル計算範囲の高さ設定: {height:.4f} (幅 {width:.4f}, 縦横比 16:9)")

    # 回転角度を取得 (度単位)
    rotation_deg = params.get("rotation", 0.0)

    # 回転前のグリッド座標を、計算する範囲 (width, height) と高解像度 (super_resolution) で生成
    # データ型の最適化: ズームアウト時はfloat16、ズームイン時はfloat32を使用
    dtype = np.float16 if width > 1.0 else np.float32 # 幅が大きい（ズームアウト）ほど精度を落とす
    x = np.linspace(center_x - width/2, center_x + width/2, super_resolution_x, dtype=dtype)
    y = np.linspace(center_y - height/2, center_y + height/2, super_resolution_y, dtype=dtype)

    # 複素数グリッドを作成
    X, Y = np.meshgrid(x, y)

    Z = X + 1j * Y # 各ピクセルに対応する複素数 (初期Z0またはC)
    Z = Z.astype(np.complex64) # 複素数型に変換

    # 回転を適用
    if rotation_deg != 0:
        logger.log(LogLevel.DEBUG, f"回転適用: {rotation_deg} 度")
        # 回転中心を(center_x, center_y)として回転
        rotation_rad = np.radians(rotation_deg)
        # グリッドを回転中心からの相対座標に変換 -> 回転 -> 元の座標系に戻す
        Z -= complex(center_x, center_y)
        rotation_operator = np.exp(1j * rotation_rad)
        Z *= rotation_operator
        Z += complex(center_x, center_y)
        logger.log(LogLevel.SUCCESS, "グリッド回転適用完了")

    logger.log(LogLevel.SUCCESS, "グリッドの作成と変換完了",
               context={"中心_x": center_x, "中心_y": center_y, "w": width, "h": height, "角度": rotation_deg})

    # フラクタルの種類に応じた計算
    # Z0やCはparamsから取得し、必要に応じて complex 型に変換
    if params["fractal_type"] == "Julia":
        # Julia集合の計算には Z と 定数C が必要
        c_val = complex(params.get("c_real", -0.7), params.get("c_imag", 0.27015))
        start_time = time.perf_counter()
        # compute_julia は iterations, mask, z_vals を含む辞書を返すことを期待
        results = julia.compute_julia(Z, c_val, params.get("max_iterations", 100), logger)
        # イテレーション数は通常整数ですが、uint16で十分な範囲をカバーできます
        results['iterations'] = results['iterations'].astype(np.uint16)
        elapsed = time.perf_counter() - start_time
        logger.log(LogLevel.INFO, f"ジュリア集合計算時間：{elapsed:.3f}秒")

    else: # Mandelbrot
        # Mandelbrot集合の計算では、グリッドZがCとなり、初期値Z0が必要
        z0_val = complex(params.get("z_real", 0.0), params.get("z_imag", 0.0))
        start_time = time.perf_counter()
        # compute_mandelbrot は iterations, mask, z_vals を含む辞書を返すことを期待
        results = mandelbrot.compute_mandelbrot(Z, z0_val, params.get("max_iterations", 100), logger)
        # イテレーション数は通常整数ですが、uint16で十分な範囲をカバーできます
        results['iterations'] = results['iterations'].astype(np.uint16)
        elapsed = time.perf_counter() - start_time
        logger.log(LogLevel.INFO, f"マンデルブロ集合計算時間：{elapsed:.3f}秒")

    # 着色処理
    # apply_coloring_algorithm は計算結果とパラメータを受け取り、float32 [0, 255] RGBA 配列を返すことを期待
    colored_high_res = color_algorithms.apply_coloring_algorithm(results, params, logger)

    # ダウンサンプリング（アンチエイリアシング効果）
    # 高解像度で計算した画像を、目的の解像度(resolution)に縮小します。
    if samples_per_pixel > 1:
        logger.log(LogLevel.DEBUG, "ダウンサンプリング実行")
        # 高解像度画像 colored_high_res を resolution x resolution に平均化して縮小
        # colored_high_res の形状は (super_resolution_y, super_resolution_x, 4) です
        # reshapeを使ってサンプルピクセルをまとめ、axis=(1, 3)で平均を取ります
        # 元形状: (res*spp, res*spp, 4)
        # reshape後: (res, spp, res, spp, 4)
        # mean(axis=(1, 3))で spp x spp のブロックごとに平均
        try:
            # colored_high_res の形状が期待通りであることを確認してからreshape
            expected_shape = (super_resolution_y, super_resolution_x, 4)
            if colored_high_res.shape == expected_shape:
                colored = colored_high_res.reshape((resolution, samples_per_pixel, resolution, samples_per_pixel, 4)).mean(axis=(1, 3))
            else:
                 # 形状が異なる場合はエラーログを出力し、ダウンサンプリングをスキップするか、エラー処理を行う
                 logger.log(LogLevel.ERROR, f"ダウンサンプリングエラー: colored_high_resの形状が不正です。期待値: {expected_shape}, 実際: {colored_high_res.shape}")
                 # エラーを示す画像で置き換えるか、ダウンサンプリングしない処理に進む
                 # ここではエラーを示す単色画像を例として返します
                 colored = np.full((resolution, resolution, 4), [255, 0, 0, 255], dtype=np.float32) # 赤色のエラー画像

        except ValueError as e:
            logger.log(LogLevel.ERROR, f"ダウンサンプリング中のValueError: {e}. 解像度={resolution}, samples_per_pixel={samples_per_pixel}, colored_high_res.shape={colored_high_res.shape}")
            # ValueError発生時もエラーを示す画像で置き換えるなど
            colored = np.full((resolution, resolution, 4), [255, 0, 0, 255], dtype=np.float32) # 赤色のエラー画像

    else:
        # ダウンサンプリングしない場合
        # この場合、計算された colored_high_res はすでに resolution x resolution になっているはずですが
        # 念のため最終的なサイズに調整する必要があるかもしれません。
        # 現在のロジックでは samples_per_pixel=1 のとき super_resolution == resolution なので問題ありません。
        colored = colored_high_res

    # 最終的な結果を uint8 [0, 255] に変換
    # np.clip で範囲外の値が発生しないように念のためクリップ
    colored = np.clip(colored, 0, 255).astype(np.uint8)
    logger.log(LogLevel.DEBUG, f"最終的な render_fractal 出力 dtype: {colored.dtype}, shape: {colored.shape}")

    return colored

def calculate_dynamic_resolution(width, base_res=600, min_res=300, max_res=1200):
    """ズームレベルに応じて描画解像度を動的に計算

    Args:
        width (float): ウィンドウの幅（データ座標系）。ズームレベルの指標として使用。
                       widthが小さいほどズームインしており、高解像度が必要。
        base_res (int, optional): 基準となる解像度. Defaults to 600.
        min_res (int, optional): 最小解像度. Defaults to 300.
        max_res (int, optional): 最大解像度. Defaults to 1200.

    Returns:
        int: 計算された描画解像度（一辺のピクセル数）。実際にはこれにsamples_per_pixelをかけた高解像度で計算し、後で縮小します。
    """
    # 対数スケールでズームファクターを計算。width=4.0を基準（ズームなし）とするとlog(5)あたり。
    # widthが小さくなる（ズームイン）ほどzoom_factorは大きくなります。
    # +1.0 は width が非常に小さい場合に log(ほぼ0) にならないようにするため。
    zoom_factor = np.log(5.0 / width + 1.0) # 調整可能なマジックナンバー (5.0)

    # zoom_factorにbase_resを掛けて基本解像度を決定
    resolution = int(base_res * zoom_factor)

    # 最小解像度と最大解像度でクリップ
    return np.clip(resolution, min_res, max_res)
