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

__version__ = "0.0.0"
