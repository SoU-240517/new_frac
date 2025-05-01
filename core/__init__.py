"""
Core モジュールパッケージ

アプリの基本機能を提供するパッケージです。

主な機能:
- FractalCanvas: フラクタル画像を表示するためのキャンバス
- MainWindow: アプリケーションの主ウィンドウ
- ParameterPanel: パラメータパネル
- render_fractal: フラクタル画像を生成するための関数
- StatusBarManager: ステータスバーの管理
"""

# サブモジュールから主要なクラスや関数をインポートし、
# パッケージレベルでアクセスできるようにします。
# 例: from base import MainWindow
from .canvas import FractalCanvas
from .main_window import MainWindow
from .parameter_panel import ParameterPanel
from .render import render_fractal # クラスは無いが、関数をインポートできるようにする
from .status_bar import StatusBarManager

# パッケージの公開インターフェースを定義します。
# 'from base import *' でインポートされる名前を制限します。
__all__ = [
    'FractalCanvas',
    'MainWindow',
    'ParameterPanel',
    'render_fractal',
    'StatusBarManager'
]

# パッケージのバージョン
# setup.py や pyproject.toml と連動させることも検討できます。
__version__ = '0.0.0'
