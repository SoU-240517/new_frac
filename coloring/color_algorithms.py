import matplotlib.pyplot as plt
import numpy as np
import time
from matplotlib.colors import Normalize, Colormap
from typing import Dict, Tuple, Optional
from coloring import gradient
from ui.zoom_function.debug_logger import DebugLogger
from ui.zoom_function.enums import LogLevel

"""フラクタル画像の着色処理エンジン
このモジュールはフラクタル画像の着色処理を担当する
主な機能：
1. 複数の着色アルゴリズムの実装
   詳細は color_algorithms.md を参照
2. パフォーマンス最適化
   - 高速スムージングアルゴリズム
   - キャッシュ機能
   - ベクトル化された計算
3. 品質最適化
   - 正規化処理
   - カラーマップの適用
   - 発散/非発散部分の別々の着色
"""

class ColorAlgorithmError(Exception):
    """着色アルゴリズム関連のエラーを処理する例外クラス
    この例外は、着色処理中に発生するエラーをキャッチするために使用される
    主に以下のケースで発生：
    - 不正な着色アルゴリズムの指定
    - 計算値の範囲エラー
    - パラメータの不整合
    """
    pass

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
        self.logger = logger or DebugLogger()

    def _create_cache_key(self, params: Dict) -> str:
        """キャッシュキーを生成
        Args:
            params (dict): 計算パラメータ
        Returns:
            str: キャッシュキー
        """
        return str(sorted(params.items()))

    def get_cache(self, params: Dict) -> Optional[Dict]:
        """キャッシュからデータを取得
        Args:
            params (dict): 計算パラメータ
        Returns:
            dict: キャッシュデータ（存在しない場合はNone）
        """
        key = self._create_cache_key(params)
        return self.cache.get(key)

    def put_cache(self, params: Dict, data: np.ndarray) -> None:
        """データをキャッシュに保存
        Args:
            params (dict): 計算パラメータ
            data (np.ndarray): キャッシュするデータ
        """
        key = self._create_cache_key(params)
        if len(self.cache) >= self.max_size:
            # キャッシュが満杯の場合、最初の要素を削除
            first_key = next(iter(self.cache))
            del self.cache[first_key]
        self.cache[key] = {'params': params, 'image': data}

def _normalize_and_color(values: np.ndarray, cmap: Colormap, vmin: float = None, vmax: float = None) -> np.ndarray:
    """値を正規化して着色
    Args:
        values (np.ndarray): 着色対象の値
        cmap (Colormap): 色マップ
        vmin (float): 正規化の最小値（指定がない場合は自動計算）
        vmax (float): 正規化の最大値（指定がない場合は自動計算）
    Returns:
        np.ndarray: 着色されたRGBA配列
            - 形状: (height, width, 4)
            - 値の範囲: 0-255
            - RGBA形式（R, G, B, A）
    Notes:
        - 自動正規化の場合、最小値と最大値はデータから計算される
        - RGBA形式の配列は、最後の次元で4つの値（R, G, B, A）を持つ
        - 色マップはmatplotlibのColormapを使用
    """
    if vmin is None:
        vmin = np.min(values)
    if vmax is None:
        vmax = np.max(values)

    norm = Normalize(vmin=vmin, vmax=vmax)
    return cmap(norm(values)) * 255.0

def _smooth_iterations(z: np.ndarray, iters: np.ndarray, method: str = 'standard') -> np.ndarray:
    """反復回数のスムージング処理を実行
    Args:
        z (np.ndarray): 複素数配列
        iters (np.ndarray): 反復回数配列
        method (str): スムージング方法
            - 'standard': 標準的なスムージング
            - 'fast': 高速なスムージング
            - 'exponential': 指数的なスムージング
    Returns:
        np.ndarray: スムージングされた反復回数
            - 形状: (height, width)
            - 値の範囲: 0-無限大
    Raises:
        ColorAlgorithmError: 無効なスムージング方法が指定された場合
    Notes:
        - スムージングはフラクタルの境界線を滑らかにするために使用
        - 数値の不安定性を防ぐため、np.errstateを使用
        - 各スムージング方法は異なる視覚効果をもたらす
    """
    with np.errstate(invalid='ignore', divide='ignore'):
        if method == 'standard':
            log_zn = np.log(np.abs(z))
            nu = np.log(log_zn / np.log(2)) / np.log(2)
            return iters - nu
        elif method == 'fast':
            smooth_iter = np.zeros_like(iters, dtype=np.float32)
            fast_smoothing(z, iters, smooth_iter)
            return smooth_iter
        elif method == 'exponential':
            return iters + 1 - np.log(np.log(np.abs(z))) / np.log(2)
        else:
            raise ColorAlgorithmError(f"Unknown smoothing method: {method}")

def apply_coloring_algorithm(results: Dict, params: Dict, logger: DebugLogger) -> np.ndarray:
    """フラクタルの着色アルゴリズムを適用
    Args:
        results (dict): フラクタル計算結果
            - iterations: 反復回数配列
            - mask: フラクタル集合に属する点のマスク
            - z_vals: 複素数値配列
        params (dict): 着色パラメータ
            - diverge_algorithm: 発散部の着色アルゴリズム
            - diverge_colormap: 発散部のカラーマップ
            - non_diverge_colormap: 非発散部のカラーマップ
            - max_iterations: 最大反復回数
        logger (DebugLogger): デバッグログ用ロガー
    Returns:
        np.ndarray: 着色されたRGBA配列
            - 形状: (height, width, 4)
            - 値の範囲: 0-255
            - RGBA形式（R, G, B, A）
    Notes:
        - 発散部と非発散部で異なる着色を適用
        - キャッシュ機能により、同じパラメータでの再計算を避ける
        - 複数の着色アルゴリズムをサポート
    """
    logger.log(LogLevel.INIT, "ColorCache クラスのインスタンスを作成")
    cache = ColorCache()
    cached = cache.get_cache(params)
    if cached:
        logger.log(LogLevel.INFO, "キャッシュから画像を取得")
        return cached['image']

    iterations = results['iterations']
    mask = results['mask']
    z_vals = results['z_vals']
    divergent = iterations > 0
    colored = np.zeros((*iterations.shape, 4), dtype=np.float32)
    cmap_func = plt.cm.get_cmap(params["diverge_colormap"])
    non_cmap_func = plt.cm.get_cmap(params["non_diverge_colormap"])

    def process_divergent():
        """発散部の着色アルゴリズム"""
        algo = params["diverge_algorithm"]
        logger.log(LogLevel.DEBUG, f"着色アルゴリズム選択: {algo}")

        if algo == '反復回数線形マッピング':
            # 線形マッピング処理
            norm = Normalize(1, params["max_iterations"])
            colored[divergent] = cmap_func(norm(iterations[divergent])) * 255.0

        elif algo == '反復回数対数マッピング':
            # 対数マッピング処理
            log_iters = np.log(iterations[divergent]) # 対数スケールに変換
            # 対数スケールの正規化
            norm = Normalize(np.log(1), np.log(params["max_iterations"]))
            colored[divergent] = cmap_func(norm(log_iters)) * 255.0

        elif algo in ['スムージングカラーリング', '高速スムージング', '指数スムージング']:
            smooth_method = 'fast' if algo == '高速スムージング' else 'standard'
            smooth_iter = _smooth_iterations(z_vals, iterations, smooth_method)
            valid_vals = smooth_iter[divergent & np.isfinite(smooth_iter)]

            if len(valid_vals) == 0:
                raise ColorAlgorithmError("Valid values not found for smoothing")

            vmin = np.min(valid_vals)
            vmax = np.max(valid_vals)

            if vmin == vmax:
                vmax += 1e-9

            colored[divergent] = _normalize_and_color(
                smooth_iter[divergent],
                cmap_func,
                vmin,
                vmax
            )

        elif algo == "ヒストグラム平坦化法":
            hist, bins = np.histogram(iterations[divergent], bins=params["max_iterations"], density=True)
            cdf = hist.cumsum()
            cdf = cdf / cdf[-1]
            remapped = np.interp(iterations[divergent], bins[:-1], cdf)
            colored[divergent] = cmap_func(remapped) * 255.0

        elif algo == "距離カラーリング":
            dist = np.abs(z_vals)
            dist[mask] = 0
            colored[divergent] = _normalize_and_color(
                dist[divergent],
                cmap_func,
                0,
                10
            )

        elif algo == "角度カラーリング":
            angles = np.angle(z_vals) / (2 * np.pi) + 0.5
            colored[divergent] = cmap_func(angles[divergent]) * 255.0

        elif algo == "ポテンシャル関数法":
            with np.errstate(divide='ignore', invalid='ignore'):
                abs_z = np.abs(z_vals)
                log_abs_z = np.log(abs_z)
                potential = np.full_like(log_abs_z, 0.0)
                valid_potential = (log_abs_z != 0) & np.isfinite(log_abs_z) & divergent
                potential[valid_potential] = -np.log(log_abs_z[valid_potential]) / log_abs_z[valid_potential]
            potential[mask] = 0
            colored[divergent] = _normalize_and_color(
                potential[divergent],
                cmap_func,
                0
            )

        elif algo == "軌道トラップ法":
            trap_target = complex(1.0, 0.0)
            trap_dist = np.abs(z_vals - trap_target)
            trap_dist[mask] = float('inf')
            min_dist = np.min(trap_dist[divergent]) if np.any(divergent) else 0
            max_dist = np.max(trap_dist[divergent & np.isfinite(trap_dist)]) if np.any(divergent & np.isfinite(trap_dist)) else 1
            colored[divergent] = _normalize_and_color(
                trap_dist[divergent],
                cmap_func,
                min_dist,
                max_dist
            )

    def process_non_divergent():
        """非発散部の着色アルゴリズム"""
        non_divergent = ~divergent
        non_algo = params["non_diverge_algorithm"]

        if non_algo == "単色":
            colored[non_divergent] = [0.0, 0.0, 0.0, 255.0]

        elif non_algo == "グラデーション":
            grad = gradient.compute_gradient(iterations.shape, logger)
            colored[non_divergent] = non_cmap_func(grad[non_divergent]) * 255.0

        elif non_algo == "内部距離（Escape Time Distance）":
            # 内部距離の計算
            with np.errstate(invalid='ignore', divide='ignore'):
                # z_valsの絶対値を計算 (0にならないように微小値を加算)
                abs_z = np.abs(z_vals[non_divergent]) + 1e-10
                # 対数を取って正規化 (値が大きいほど境界に近い)
                distance = np.log(abs_z) / np.log(2.0)
                # 0-1の範囲に正規化
                distance = (distance - np.min(distance)) / (np.max(distance) - np.min(distance))
            # カラーマップを適用
            colored[non_divergent] = non_cmap_func(distance) * 255.0

        elif non_algo == "軌道トラップ(円)（Orbit Trap Coloring）":
            # 円形トラップ (中心0、半径Rの円に近いほど明るく)
            R = 1.4  # この値を0.5～2.0の範囲で変化させてみてください
            trap_dist = np.abs(np.abs(z_vals[non_divergent]) - R)
            normalized = 1 - (trap_dist / np.max(trap_dist))
            gamma = 1.0  # 1.0～2.0で調整
            normalized = normalized ** (1/gamma)
            colored[non_divergent] = non_cmap_func(normalized) * 255.0

        elif non_algo == "位相对称（Phase Angle Symmetry）":
            angles = np.angle(z_vals[non_divergent])
            # 対称性の次数 (4なら90度ごとに同じ色)
            symmetry_order = 5 # 3～8の整数で様々な対称性が試せます
            normalized = (angles * symmetry_order / (2*np.pi)) % 1.0
            gamma = 1.5  # 1.0～2.0で調整
            normalized = normalized ** (1/gamma)
            colored[non_divergent] = non_cmap_func(normalized) * 255.0

        elif non_algo == "反復収束速度（Convergence Speed）":
            # zの最終値が小さいほど速く収束したとみなす
            speed = 1 / (np.abs(z_vals[non_divergent]) + 1e-10)
            normalized = (speed - np.min(speed)) / (np.max(speed) - np.min(speed))
            gamma = 1.5  # 1.0～2.0で調整
            normalized = normalized ** (1/gamma)
            colored[non_divergent] = non_cmap_func(normalized) * 255.0

        elif non_algo == "微分係数（Derivative Coloring）":
            derivative = 2 * np.abs(z_vals[non_divergent]) * 0.5 # f(z)=z²+cならf'(z)=2z。最後の0.5が調整可能
            log_deriv = np.log(derivative + 1e-10)
            normalized = (log_deriv - np.min(log_deriv)) / (np.max(log_deriv) - np.min(log_deriv))
            gamma = 1.5  # 1.0～2.0で調整
            normalized = normalized ** (1/gamma)
            colored[non_divergent] = non_cmap_func(normalized) * 255.0

        elif non_algo == "統計分布（Histogram Equalization）":
            # 反復回数のヒストグラムを計算
            hist, bins = np.histogram(iterations[non_divergent], bins=256)
            cdf = hist.cumsum()
            cdf_normalized = cdf / cdf[-1]
            # ヒストグラム平坦化を適用
            gamma = 1.5  # 1.0～2.0で調整
            cdf_normalized = cdf_normalized ** (1/gamma)
            equalized = np.interp(iterations[non_divergent], bins[:-1], cdf_normalized)
            colored[non_divergent] = non_cmap_func(equalized) * 255.0

        elif non_algo == "複素ポテンシャル（Complex Potential Mapping）":
            with np.errstate(divide='ignore', invalid='ignore'):
                potential = np.log(np.abs(z_vals[non_divergent]) + 1e-10)
                potential = np.nan_to_num(potential, nan=0.0, posinf=0.0, neginf=0.0)
                normalized = (potential - np.min(potential)) / (np.max(potential) - np.min(potential))
                # 波模様を強調するために角度を加算
                angle_effect = np.angle(z_vals[non_divergent]) / (2*np.pi)
                combined = (normalized + 0.3 * angle_effect) % 1.0 # 0.3 * angle_effectの係数を変更して角度の影響度を調整
                colored[non_divergent] = non_cmap_func(combined) * 255.0

        elif non_algo == "カオス軌道混合（Chaotic Orbit Mixing）":
            # 簡易的な軌道情報のシミュレーション
            r = np.abs(z_vals[non_divergent])
            theta = np.angle(z_vals[non_divergent])
            # 各チャンネルに異なる数学関数を適用(red, green, blueの各チャンネルの数式を変更)
            red = np.sin(r * 5.0)**2
            green = (np.cos(theta * 3.0) + 1) / 2
            blue = (np.sin(r * 3.0 + theta * 2.0) + 1) / 2
            # RGB結合
            colored[non_divergent] = np.stack([red, green, blue, np.ones_like(red)], axis=-1) * 255.0

        elif non_algo == "フーリエ干渉（Fourier Pattern）":
            x = np.real(z_vals[non_divergent])
            y = np.imag(z_vals[non_divergent])

            # 複数の周波数成分を合成(10.0, 8.0などの周波数パラメータを変更)
            pattern = (np.sin(x * 10.0) * np.cos(y * 8.0) +
                    np.sin(x * 5.0 + y * 3.0)) / 2.0

            normalized = (pattern - np.min(pattern)) / (np.max(pattern) - np.min(pattern))
            colored[non_divergent] = non_cmap_func(normalized) * 255.0

        elif non_algo == "フラクタルテクスチャ（Fractal Texture）":
            def noise(x, y, scale=1.0): # noise関数内のscaleパラメータを調整
                return np.sin(scale * x) * np.cos(scale * y)

            x = np.real(z_vals[non_divergent])
            y = np.imag(z_vals[non_divergent])

            # マルチオクターブノイズ
            n1 = noise(x, y, 5.0)
            n2 = noise(x, y, 10.0) * 0.5
            n3 = noise(x, y, 20.0) * 0.25
            combined = n1 + n2 + n3

            normalized = (combined - np.min(combined)) / (np.max(combined) - np.min(combined))
            colored[non_divergent] = non_cmap_func(normalized) * 255.0

        elif non_algo == "量子もつれ（Quantum Entanglement）":
            real_part = np.real(z_vals[non_divergent])
            imag_part = np.imag(z_vals[non_divergent])

            # 値の標準化（ゼロ除算防止）
            with np.errstate(divide='ignore', invalid='ignore'):
                scale = 2.0  # この値を調整してみてください（0.1～50.0）
                real_part = (real_part - np.mean(real_part)) / (np.std(real_part) + 1e-10) * scale
                imag_part = (imag_part - np.mean(imag_part)) / (np.std(imag_part) + 1e-10) * scale

            # 負の値を避けるための処理
            real_pos = np.abs(real_part)  # 絶対値を取る
            imag_pos = np.abs(imag_part)

            # パターン計算の改善
            # より広い値の範囲を確保
            pattern = (
                np.sin(real_pos**1.5 + imag_pos**1.5) * 0.4 +
                np.cos(real_pos * imag_pos * 0.5) * 0.4 +
                np.arctan2(imag_part, real_part) / (2 * np.pi) * 0.2
            )
            
            # デバッグ用のログ
#            print(f"Pattern range: min={np.min(pattern)}, max={np.max(pattern)}")
            
            # NaN値の処理
            pattern = np.nan_to_num(pattern, nan=0.0)  # NaNを0に置き換え
            
            # 値の範囲を0-1にスケーリング
            pattern = (pattern - np.min(pattern)) / (np.max(pattern) - np.min(pattern) + 1e-10)
            pattern = np.clip(pattern, 0, 1)

            # ガンマ補正でコントラスト調整
            gamma = 1.8
            normalized = pattern ** (1/gamma)

            # カラーマップ適用
            colored[non_divergent] = non_cmap_func(normalized) * 255.0

        elif non_algo in ["パラメータ(C)", "パラメータ(Z)"]:
            if non_algo == "パラメータ(C)":
                # パラメータCを使う場合（Julia集合の定数C）
                if params["fractal_type"] == "Julia":
                    c_val = complex(params["c_real"], params["c_imag"])
                    angle = (np.angle(c_val) / (2 * np.pi)) + 0.5
                    color = non_cmap_func(angle)  # 色を取得
                    colored[non_divergent] = np.tile(color, (np.sum(non_divergent), 1)) * 255.0
                else:
                    # Mandelbrot集合の場合、Cは初期値z0（通常は0）なので意味がない
                    # 代わりに黒で塗るか、別のデフォルト色を使う
                    colored[non_divergent] = [0.0, 0.0, 0.0, 255.0]
            else:  # パラメータ(Z)の場合
                # zの値を使う（JuliaとMandelbrotの両方で有効）
                z_real, z_imag = np.real(z_vals[non_divergent]), np.imag(z_vals[non_divergent])
                angle = (np.arctan2(z_imag, z_real) / (2 * np.pi)) + 0.5
                colored[non_divergent] = non_cmap_func(angle) * 255.0

    try:
        if np.any(divergent):
            process_divergent()
            logger.log(LogLevel.DEBUG, f"発散する点の数: {np.sum(divergent)}")

        if np.any(~divergent):
            process_non_divergent()
            logger.log(LogLevel.DEBUG, f"発散しない点の数: {np.sum(~divergent)}")

        logger.log(LogLevel.DEBUG,
            f"最終的な colored 配列の dtype: {colored.dtype}, "
            f"min: {np.min(colored)}, max: {np.max(colored)}"
        )

        cache.put_cache(params, colored)
        return colored

    except Exception as e:
        logger.log(LogLevel.ERROR, f"着色処理中にエラーが発生しました: {str(e)}")
        raise ColorAlgorithmError(f"Coloring failed: {str(e)}") from e

def fast_smoothing(z, iters, out):
    """高速スムージングアルゴリズム"""
    with np.errstate(divide='ignore', invalid='ignore'):
        abs_z = np.abs(z)
        mask_smooth = abs_z > 2
        log2 = np.log(2)
        smooth_values = iters[mask_smooth] - np.log(np.log(abs_z[mask_smooth])) / log2
        out[...] = iters
        out[mask_smooth] = smooth_values
