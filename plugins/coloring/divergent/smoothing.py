import numpy as np
from matplotlib.colors import Colormap
import matplotlib.pyplot as plt # カラーマップ取得のため
from typing import Dict, Callable
from debug import DebugLogger, LogLevel

# coloring.utils にある関数を使う場合は、パスの解決が必要になることがあります。
# 簡単なのは、必要な関数をこのファイルに持ってくるか、
# もしくは coloring.utils が適切にPythonパス上に見えるようにすることです。
# ここでは、coloring.utils の関数が直接呼び出せる前提で進めますが、
# 実際には from ...coloring import utils のように調整が必要かもしれません。
# もし `sou-240517-new_frac` が PYTHONPATH に含まれていれば、
# from coloring.utils import _normalize_and_color, _smooth_iterations のように書けるはずです。
# プロジェクトルートからの相対インポートを使う場合は、
# from ...coloring.utils import _normalize_and_color, _smooth_iterations のようになります。
# しかし、plugins フォルダ直下からの相対パスは複雑になりがちなので、
# PYTHONPATHの設定や、呼び出し側(manager.py)でパス解決を工夫する方が良いかもしれません。

# この例では、簡単のため、ユーティリティ関数が直接利用可能であるか、
# あるいはこのファイル内に同等の機能が実装されていると仮定します。
# coloring.utils._smooth_iterations と coloring.utils._normalize_and_color を使う想定

# 仮に、coloring.utils の関数をインポートする記述 (プロジェクト構造に依存)
# import sys
# import os
# # このファイルのディレクトリの2つ上 (plugins) の1つ上 (sou-240517-new_frac) をパスに追加
# current_dir = os.path.dirname(os.path.abspath(__file__))
# project_root = os.path.abspath(os.path.join(current_dir, "..", ".."))
# if project_root not in sys.path:
#    sys.path.append(project_root)
# from coloring.utils import _normalize_and_color, _smooth_iterations
# sys.path.remove(project_root) # 後始末 (推奨)

# --- 実際のプロジェクトでは、utilsのインポート方法をしっかり確立してください ---
# --- ここでは、仮に utils の関数が使えるものとして記述します ---
def _temp_smooth_iterations(z: np.ndarray, iters: np.ndarray, method: str = 'standard') -> np.ndarray:
    """ (coloring.utils._smooth_iterations の仮実装またはインポートされたもの) """
    # coloring.utils._smooth_iterations のロジックをここに書くか、正しくインポートする
    if method == 'standard':
        abs_z = np.abs(z)
        diverged_mask = abs_z > 2 # 仮の閾値
        log2 = np.log(2)
        smooth_values = np.full(iters.shape, np.nan, dtype=np.float32)
        if np.any(diverged_mask):
            z_diverged = z[diverged_mask]
            iters_diverged = iters[diverged_mask]
            abs_z_diverged = np.abs(z_diverged)
            with np.errstate(divide='ignore', invalid='ignore'):
                log_abs_z = np.log(abs_z_diverged)
                log_log_abs_z = np.log(log_abs_z)
            valid_calculation_mask = np.isfinite(log_log_abs_z)
            if np.any(valid_calculation_mask):
                calculated_smooth = (
                    iters_diverged[valid_calculation_mask] -
                    log_log_abs_z[valid_calculation_mask] / log2
                )
                # マスキングのインデックスを正しく扱う必要がある
                # 簡単のため、一度 diverged_mask が True の部分だけ取り出して処理する
                temp_smooth_for_diverged = np.full(diverged_mask.sum(), np.nan, dtype=np.float32)
                temp_smooth_for_diverged[valid_calculation_mask] = calculated_smooth.astype(np.float32)
                smooth_values[diverged_mask] = temp_smooth_for_diverged
        return smooth_values
    return iters.astype(np.float32) # 不明なメソッドならそのまま返す (エラー処理推奨)


def _temp_normalize_and_color(values: np.ndarray, cmap_func: Callable, vmin=None, vmax=None) -> np.ndarray:
    """ (coloring.utils._normalize_and_color の仮実装またはインポートされたもの) """
    # coloring.utils._normalize_and_color のロジックをここに書くか、正しくインポートする
    finite_values = values[np.isfinite(values)]
    if finite_values.size == 0:
        return np.zeros(values.shape + (4,), dtype=np.float32)

    if vmin is None: vmin = np.min(finite_values)
    if vmax is None: vmax = np.max(finite_values)
    if np.isclose(vmin, vmax): vmax = vmin + 1e-9

    # Normalize (matplotlib.colors.Normalize を使うのが望ましい)
    if vmax == vmin: # ゼロ除算回避
        normalized_values = np.zeros_like(values, dtype=float)
    else:
        normalized_values = (values - vmin) / (vmax - vmin)
    normalized_values = np.clip(normalized_values, 0, 1) # 0-1の範囲にクリップ

    colored_values = cmap_func(normalized_values) * 255.0 # cmap_func は plt.get_cmap() で得られたもの
    return colored_values.astype(np.float32)


def apply_color(
    colored_array: np.ndarray, # 変更対象の全体画像 (RGBA, float32, 0-255)
    mask_to_apply: np.ndarray, # このアルゴリズムが担当するマスク (Trueの部分)
    iterations: np.ndarray,    # 全体の反復回数
    z_values: np.ndarray,      # 全体のZ値
    cmap_func: Callable,       # カラーマップ関数 (plt.get_cmap() で得られたもの)
    params: dict,              # パネルからの全パラメータ
    logger: DebugLogger,
    config: dict,
    **kwargs # 将来的な追加引数用
) -> None:
    """
    スムージングアルゴリズムによる着色。
    colored_array の mask_to_apply が True の部分を更新する。
    """
    logger.log(LogLevel.CALL, f"Smoothing プラグイン ({__name__}) 実行開始")

    if not np.any(mask_to_apply):
        logger.log(LogLevel.INFO, "スムージング対象のピクセルがありません。処理をスキップします。")
        return

    # params からこのプラグインが必要とする情報を取得
    # 例: スムージングメソッド (なければデフォルト)
    smoothing_method = params.get("smoothing_method", "standard") # このキー名は manager.py と合わせる
    # smoothing_method = params.get(params.get('diverge_algorithm', {}).get("smoothing_method", "standard")) # より詳細な設定も可能

    # マスクされた部分のデータのみを取得
    iters_masked = iterations[mask_to_apply]
    z_masked = z_values[mask_to_apply]

    if iters_masked.size == 0: #念のため
        logger.log(LogLevel.WARNING, "マスク後のイテレーションデータが空です。")
        return

    # スムージング処理 (coloring.utils の関数を使うか、ここで実装)
    # smooth_iters = _smooth_iterations(z_masked, iters_masked, method=smoothing_method)
    smooth_iters = _temp_smooth_iterations(z_masked, iters_masked, method=smoothing_method) # 仮の関数を使用

    # NaNでない有限な値のみを対象に正規化と色付け
    finite_smooth_iters = smooth_iters[np.isfinite(smooth_iters)]
    if finite_smooth_iters.size > 0:
        # 正規化とカラーマップ適用 (coloring.utils の関数を使うか、ここで実装)
        # colored_segment_float = _normalize_and_color(smooth_iters, cmap_func)
        colored_segment_float = _temp_normalize_and_color(smooth_iters, cmap_func) # 仮の関数を使用

        # 元の colored_array の該当箇所を更新
        # colored_segment_float は (N, 4) の形状 (Nはマスクされたピクセル数)
        # colored_array[mask_to_apply] も (N, 4) の形状になる
        colored_array[mask_to_apply] = colored_segment_float
        logger.log(LogLevel.SUCCESS, f"Smoothing プラグイン ({__name__}) 完了。{finite_smooth_iters.size} ピクセルを着色。")
    else:
        logger.log(LogLevel.INFO, "スムージング後の有効な値がありませんでした。")
