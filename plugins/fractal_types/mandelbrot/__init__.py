"""
Mandelbrot モジュールパッケージ

主な機能:
    - Mandelbrot集合の計算
    - パラメータの管理
    - カラーマッピング
    - レンダリング
"""

from .mandelbrot import compute_mandelbrot

__all__ = ['compute_mandelbrot']

__version__ = '0.0.0'
