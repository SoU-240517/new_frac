"""
Debug モジュールパッケージ

このパッケージは、フラクタルアプリケーションのデバッグ機能を提供します。

主な機能:
- DebugLogger: デバッグログを出力するためのクラス
- LogLevel: デバッグログのレベルを定義する列挙型
"""

from .debug_logger import DebugLogger
from .enum_debug import LogLevel

__all__ = ['DebugLogger', 'LogLevel']

__version__ = '0.0.0'