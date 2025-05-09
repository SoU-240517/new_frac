"""
フラクタルタイププラグイン モジュールパッケージ

主な機能:
    - プラグインディレクトリからフラクタルタイププラグインをスキャンしてロードします。
"""

from .plugin_loader import FractalTypeLoader, ColoringPluginLoader

__all__ = ['FractalTypeLoader', 'ColoringPluginLoader']

__version__ = '0.0.0'
