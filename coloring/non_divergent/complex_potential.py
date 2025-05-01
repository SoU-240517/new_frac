import numpy as np
from typing import Dict
from matplotlib.colors import Colormap
from debug.debug_logger import DebugLogger
from debug.enum_debug import LogLevel

def apply_complex_potential(
    colored: np.ndarray,
    non_divergent_mask: np.ndarray,
    z_vals: np.ndarray, # iterations の代わりに z_vals を受け取る
    non_cmap_func: Colormap, # 正しいカラーマップ関数を受け取る
    params: Dict,
    logger: DebugLogger
) -> None:
    """非発散領域を複素ポテンシャルで着色する
    - 複素数の絶対値の対数と角度情報を組み合わせ、非発散領域の特徴を視覚的に表現する
    Args:
        colored (np.ndarray): 出力用のRGBA配列 (形状: (h, w, 4), dtype=float32)
        non_divergent_mask (np.ndarray): 非発散点のマスク配列 (形状: (h, w), dtype=bool)
        z_vals (np.ndarray): 複素数値の配列
        non_cmap_func (Colormap): 非発散領域の着色に使用するカラーマップ関数
        params (Dict): 使用しない
        logger (DebugLogger): デバッグ用ロガーインスタンス
    """
    # 複素数の絶対値の対数を計算（複素ポテンシャル）
    # 除算によるゼロ除算や無限大を防ぐためのエラーハンドリング
    with np.errstate(divide='ignore', invalid='ignore'):

        # 絶対値の対数を計算（ゼロ除算を防ぐために小さな値を加算）
        potential = np.log(np.abs(z_vals[non_divergent_mask]) + 1e-10)

        # NaNや無限大を0に置き換え
        potential = np.nan_to_num(potential, nan=0.0, posinf=0.0, neginf=0.0)

        # 0-1の範囲に正規化
        normalized = (potential - np.min(potential)) / (np.max(potential) - np.min(potential))

        # 複素数の角度（位相）を計算して正規化
        # 2πで割ることで0-1の範囲に正規化
        angle_effect = np.angle(z_vals[non_divergent_mask]) / (2 * np.pi)

        # 正規化された値と角度効果を組み合わせ
        # 角度の影響度を調整し、0-1の範囲に収める
        combined = (normalized + 0.3 * angle_effect) % 1.0

        # 正規化された値をカラーマップに適用し、0-255の範囲に変換
        colored[non_divergent_mask] = non_cmap_func(combined) * 255.0
