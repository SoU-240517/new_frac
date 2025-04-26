import numpy as np
from typing import Dict, Tuple
from matplotlib.colors import Colormap
from ui.zoom_function.debug_logger import DebugLogger
from ui.zoom_function.enums import LogLevel

def apply_complex_potential(
    colored: np.ndarray,
    non_divergent_mask: np.ndarray,
    z_vals: np.ndarray, # iterations の代わりに z_vals を受け取る
    non_cmap_func: Colormap, # 正しいカラーマップ関数を受け取る
    params: Dict,
    logger: DebugLogger
) -> None:
    """非発散部：複素ポテンシャルで着色する
        複素数の絶対値の対数と角度情報を組み合わせて、
        非発散部の特徴を視覚的に表現します。
    Args:
            colored (np.ndarray): 出力用のRGBA配列 (形状: (h, w, 4), dtype=float32)
            non_divergent_mask (np.ndarray): 非発散した点のマスク (形状: (h, w), dtype=bool)
            z_vals (np.ndarray): 複素数配列
            non_cmap_func (Colormap): 非発散部分用のカラーマップ関数
            params (Dict): 着色パラメータ
            logger (DebugLogger): ロガーインスタンス
    """
    # 複素数の絶対値の対数を計算（複素ポテンシャル）
    # 除算によるゼロ除算や無限大を防ぐためのエラーハンドリング
    with np.errstate(divide='ignore', invalid='ignore'):

        # 絶対値の対数を計算（1e-10の小さな値を加算してゼロ除算を防ぐ）
        potential = np.log(np.abs(z_vals[non_divergent_mask]) + 1e-10)

        # NaNや無限大を0に置き換え
        potential = np.nan_to_num(potential, nan=0.0, posinf=0.0, neginf=0.0)

        # 0-1の範囲に正規化
        normalized = (potential - np.min(potential)) / (np.max(potential) - np.min(potential))

        # 複素数の角度（位相）を計算して正規化
        # 2πで割ることで0-1の範囲に正規化
        angle_effect = np.angle(z_vals[non_divergent_mask]) / (2*np.pi)

        # 正規化された値と角度効果を組み合わせ
        # 0.3の係数で角度の影響度を調整
        # % 1.0で0-1の範囲に収める
        combined = (normalized + 0.3 * angle_effect) % 1.0

        # 正規化された位相値をカラーマップに適用
        # 結果を255倍して0-255の範囲に変換
        colored[non_divergent_mask] = non_cmap_func(combined) * 255.0
