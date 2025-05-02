"""
Divergent モジュールパッケージ

発散する点に対する着色アルゴリズムを提供するパッケージです。
"""

from .angle import apply_angle_coloring
from .distance import apply_distance_coloring
from .histogram import apply_histogram_flattening
from .linear import apply_linear_mapping
from .logarithmic import apply_logarithmic_mapping
from .orbit_trap import apply_orbit_trap
from .potential import apply_potential
from .smoothing import apply_smoothing

__all__ = [
    'apply_angle_coloring',
    'apply_distance_coloring',
    'apply_histogram_flattening',
    'apply_linear_mapping',
    'apply_logarithmic_mapping',
    'apply_orbit_trap',
    'apply_potential',
    'apply_smoothing'
]

DIVERGENT_ALGORITHMS = {
    '角度カラーリング': apply_angle_coloring,
    '距離カラーリング': apply_distance_coloring,
    'ヒストグラム平坦化法': apply_histogram_flattening,
    '反復回数線形マッピング': apply_linear_mapping,
    '反復回数対数マッピング': apply_logarithmic_mapping,
    '軌道トラップ法': apply_orbit_trap,
    'ポテンシャル関数法': apply_potential,
    'スムージング': apply_smoothing,
    '高速スムージング': apply_smoothing,
    '指数スムージング': apply_smoothing
}

__version__ = "0.0.0"
