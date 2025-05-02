"""
Non-divergent モジュールパッケージ
"""

from .chaotic_orbit import apply_chaotic_orbit
from .complex_potential import apply_complex_potential
from .convergence_speed import apply_convergence_speed
from .derivative import apply_derivative_coloring
from .fourier_pattern import apply_fourier_pattern
from .fractal_texture import apply_fractal_texture
from .gradient_based import apply_gradient_based
from .histogram_equalization import apply_histogram_equalization
from .internal_distance import apply_internal_distance
from .orbit_trap_circle import apply_orbit_trap_circle
from .palam_c_z import apply_parameter_coloring
from .phase_symmetry import apply_phase_symmetry
from .quantum_entanglement import apply_quantum_entanglement
from .solid_color import apply_solid_color

__all__ = [
    'apply_chaotic_orbit',
    'apply_complex_potential',
    'apply_convergence_speed',
    'apply_derivative_coloring',
    'apply_fourier_pattern',
    'apply_fractal_texture',
    'apply_gradient_based',
    'apply_histogram_equalization',
    'apply_internal_distance',
    'apply_orbit_trap_circle',
    'apply_parameter_coloring',
    'apply_phase_symmetry',
    'apply_quantum_entanglement',
    'apply_solid_color'
]

NON_DIVERGENT_ALGORITHMS = {
    'カオス軌道混合（Chaotic Orbit Mixing）': apply_chaotic_orbit,
    '複素ポテンシャル（Complex Potential Mapping）': apply_complex_potential,
    '反復収束速度（Convergence Speed）': apply_convergence_speed,
    '微分係数（Derivative Coloring）': apply_derivative_coloring,
    'フーリエ干渉（Fourier Pattern）': apply_fourier_pattern,
    'フラクタルテクスチャ（Fractal Texture）': apply_fractal_texture,
    'グラデーション': apply_gradient_based,
    '統計分布（Histogram Equalization）': apply_histogram_equalization,
    '内部距離（Escape Time Distance）': apply_internal_distance,
    '軌道トラップ(円)（Orbit Trap Coloring）': apply_orbit_trap_circle,
    'パラメータ(C)': apply_parameter_coloring,
    'パラメータ(Z)': apply_parameter_coloring,
    '位相对称（Phase Angle Symmetry）': apply_phase_symmetry,
    '量子もつれ（Quantum Entanglement）': apply_quantum_entanglement,
    '単色（Solid Color）': apply_solid_color
}

__version__ = "0.0.0"
