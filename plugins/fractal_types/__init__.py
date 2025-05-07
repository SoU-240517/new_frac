"""
フラクタルタイププラグイン モジュールパッケージ

主な機能:
    - プラグインディレクトリからフラクタルタイププラグインをスキャンしてロードします。
"""

from .loader import FractalTypeLoader

__all__ = ['FractalTypeLoader']

__version__ = '0.0.0'
