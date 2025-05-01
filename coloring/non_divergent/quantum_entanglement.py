import numpy as np
from typing import Dict
from matplotlib.colors import Colormap
from debug.debug_logger import DebugLogger
from debug.enum_debug import LogLevel

def apply_quantum_entanglement(
    colored: np.ndarray,
    non_divergent_mask: np.ndarray,
    z_vals: np.ndarray, # iterations の代わりに z_vals を受け取る
    non_cmap_func: Colormap, # 正しいカラーマップ関数を受け取る
    params: Dict,
    logger: DebugLogger
) -> None:
    """非発散領域を量子もつれ風のパターンで着色する
        複素数の実部と虚部を用いて量子的なパターンを生成し、非発散領域を着色する。
        このパターンは、量子もつれの性質を模倣することを意図している。
    Args:
        colored (np.ndarray): 出力用のRGBA配列 (形状: (h, w, 4), dtype=float32)
        non_divergent_mask (np.ndarray): 非発散領域を示すマスク配列 (形状: (h, w), dtype=bool)
        z_vals (np.ndarray): 各点における複素数Zの配列 (形状: (h, w), dtype=complex128)
        non_cmap_func (Colormap): 非発散領域の着色に使用するカラーマップ関数
        params (Dict): 着色に関するパラメータを含む辞書
        logger (DebugLogger): デバッグログ出力用ロガーインスタンス
    """
    # 複素数の実部と虚部を抽出
    real_part = np.real(z_vals[non_divergent_mask])
    imag_part = np.imag(z_vals[non_divergent_mask])

    # 値の標準化（ゼロ除算防止）
    # 量子的な性質を表現するために、実部と虚部の分布を標準化
    with np.errstate(divide='ignore', invalid='ignore'):
        scale = 2.0  # 量子パターンの強度を調整（0.1～50.0）
        real_part = (real_part - np.mean(real_part)) / (np.std(real_part) + 1e-10) * scale
        imag_part = (imag_part - np.mean(imag_part)) / (np.std(imag_part) + 1e-10) * scale

    # 負の値を避けるための処理
    # 量子的な振る舞いを表現するために、絶対値を取る
    real_pos = np.abs(real_part)
    imag_pos = np.abs(imag_part)

    # 量子パターンの生成
    # 以下の各項は量子的な性質を表現するために組み合わせています：
    # - sin: 量子的な振動を表現
    # - cos: 量子的な干渉を表現
    # - arctan2: 量子的な位相関係を表現
    pattern = (
        np.sin(real_pos**1.5 + imag_pos**1.5) * 0.4 +
        np.cos(real_pos * imag_pos * 0.5) * 0.4 +
        np.arctan2(imag_part, real_part) / (2 * np.pi) * 0.2
    )

    # NaN値の処理とスケーリング
    # 量子パターンを0-1の範囲に正規化
    pattern = np.nan_to_num(pattern, nan=0.0)  # NaNを0に置き換え

    # 値の範囲を0-1にスケーリング
    pattern = (pattern - np.min(pattern)) / (np.max(pattern) - np.min(pattern) + 1e-10)
    pattern = np.clip(pattern, 0, 1)

    # ガンマ補正でコントラスト調整
    gamma = 1.8
    normalized = pattern ** (1/gamma)

    # カラーマップ適用
    colored[non_divergent_mask] = non_cmap_func(normalized) * 255.0
