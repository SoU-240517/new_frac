# パッケージ初期化ファイル
# このファイルが存在することで、
# Python は このディレクトリをパッケージとして認識します。
# 詳細は base/__init__.py を参照してください。

"""
バリデーション機能を提供するパッケージです。
"""

# サブモジュールの一括インポート
from .event_validator import EventValidator

# 外部からインポート可能な名前
__all__ = ['EventValidator']

# パッケージのバージョン情報
__version__ = '0.0.0'
