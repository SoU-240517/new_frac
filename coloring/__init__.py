"""
Coloring モジュールパッケージ

このモジュールはフラクタルのカラーリング機能を提供します。
主な機能として、発散型と非発散型のカラーリングをサポートしています。
"""

from .manager import apply_coloring_algorithm
from .gradient import compute_gradient
from .cache import ColorCache

__all__ = [
    'apply_coloring_algorithm',
    'compute_gradient',
    'ColorCache'
]

__version__ = "0.0.0"
