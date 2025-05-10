"""
 fractal_type_plugin  モジュールパッケージ

主な機能:
    - プラグインディレクトリから fractal_type_plugin をスキャンしてロードします。
"""

from .plugin_loader import FractalTypeLoader, ColoringPluginLoader

__all__ = ['FractalTypeLoader', 'ColoringPluginLoader']

__version__ = '0.0.0'
