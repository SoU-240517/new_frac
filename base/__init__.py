# パッケージ初期化ファイル
# このファイルが存在することで、
# Python は このディレクトリをパッケージとして認識します。

"""
アプリの基本機能を提供するパッケージです。
"""

# サブモジュールの一括インポート
# ここでは、base モジュールのクラスをインポートしています。
# これにより、他のモジュールからこのパッケージをインポートする際に、クラスを直接使用できるようになります。
# 具体的には、以下のようにインポートできます。
# from canvas import FractalCanvas
# ただし、他のモジュールからこのパッケージをインポートする際には、
# canvas.FractalCanvas という形でインポートすることになります。
# これは、パッケージの構造を明確にし、名前の衝突を避けるためです。
from .canvas import FractalCanvas
from .main_window import MainWindow
from .parameter_panel import ParameterPanel
from .render import render_fractal # クラスは無いが、関数をインポートできるようにする
from .status_bar import StatusBarManager

# 外部からインポート可能な名前
# __all__ にリストされている名前だけが外部からインポート可能です。
# これにより、パッケージの使用者は必要なクラスや関数だけをインポートできます。
__all__ = [
    'FractalCanvas',
    'MainWindow',
    'ParameterPanel',
    'render_fractal',
    'StatusBarManager'
]

# パッケージのバージョン情報
# これは、パッケージのバージョンを管理するために使用されます。
__version__ = '0.0.0'
