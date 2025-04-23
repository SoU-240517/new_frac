import matplotlib.pyplot as plt
import numpy as np
import time
from matplotlib.colors import Normalize, Colormap
from typing import Dict, Tuple, Optional
from coloring import gradient
from ui.zoom_function.debug_logger import DebugLogger
from ui.zoom_function.enums import LogLevel

class ColorAlgorithmError(Exception):
    """着色アルゴリズム関連のエラー"""
    pass

class ColorCache:
    """フラクタル画像をキャッシュするクラス
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
        self.logger.log(LogLevel.INIT, "ColorCache 初期化完了")

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

def _normalize_and_color(
    values: np.ndarray,
    cmap: Colormap,
    vmin: float = None,
    vmax: float = None
) -> np.ndarray:
    """値を正規化して着色する
    Args:
        values (np.ndarray): 着色対象の値
        cmap (Colormap): 色マップ
        vmin (float): 正規化の最小値
        vmax (float): 正規化の最大値
    Returns:
        np.ndarray: 着色されたRGBA配列
    """
    if vmin is None:
        vmin = np.min(values)
    if vmax is None:
        vmax = np.max(values)

    norm = Normalize(vmin=vmin, vmax=vmax)
    return cmap(norm(values)) * 255.0

def _smooth_iterations(
    z: np.ndarray,
    iters: np.ndarray,
    method: str = 'standard'
) -> np.ndarray:
    """スムージング処理を実行
    Args:
        z (np.ndarray): 複素数配列
        iters (np.ndarray): 反復回数配列
        method (str): スムージング方法 ('standard', 'fast', 'exponential')
    Returns:
        np.ndarray: スムージングされた反復回数
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

def apply_coloring_algorithm(
    results: Dict,
    params: Dict,
    logger: DebugLogger
) -> np.ndarray:
    """フラクタルの着色アルゴリズムを適用
    Args:
        results (dict): フラクタル計算結果
        params (dict): 着色パラメータ
        logger (DebugLogger): デバッグログ用ロガー
    Returns:
        np.ndarray: 着色されたRGBA配列
    """
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

    def process_divergent():
        """発散部の着色アルゴリズム"""
        algo = params["diverge_algorithm"]
        logger.log(LogLevel.DEBUG, f"着色アルゴリズム選択: {algo}")

        if algo in ['反復回数線形マッピング', '反復回数対数マッピング']:
            norm = Normalize(1, params["max_iterations"])
            colored[divergent] = cmap_func(norm(iterations[divergent])) * 255.0

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
            colored[non_divergent] = cmap_func(grad[non_divergent]) * 255.0

        elif non_algo in ["パラメータ(C)", "パラメータ(Z)"]:
            if params["fractal_type"] == "Julia" and non_algo == "パラメータ(C)":
                c_val = complex(params["c_real"], params["c_imag"])
                angle = (np.angle(c_val) / (2 * np.pi)) + 0.5
                color = np.array(cmap_func(angle)) * 255.0  # cmapの戻り値をnumpy配列に変換
                colored[non_divergent] = np.broadcast_to(color, colored[non_divergent].shape)
            else:
                z_real, z_imag = np.real(z_vals[non_divergent]), np.imag(z_vals[non_divergent])
                angle = (np.arctan2(z_imag, z_real) / (2 * np.pi)) + 0.5
                colored[non_divergent] = cmap_func(angle) * 255.0

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
