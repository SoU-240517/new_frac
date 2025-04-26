import numpy as np
from typing import Dict, Optional
from ui.zoom_function.debug_logger import DebugLogger
from ui.zoom_function.enums import LogLevel

class ColorCache:
    """フラクタル画像のキャッシュ管理クラス
    このクラスはフラクタル画像のキャッシュを管理し、既に計算された画像の再利用を可能にする
    Attributes:
        cache (dict): キャッシュデータを保持する辞書
        max_size (int): キャッシュの最大サイズ
        logger (DebugLogger): デバッグログを記録するためのロガー
    """
    def __init__(self, max_size: int = 100, logger: Optional[DebugLogger] = None):
        """ColorCache クラスのコンストラクタ
        Args:
            max_size (int): キャッシュの最大サイズ
            logger (DebugLogger): デバッグ用ロガー
        """
        self.cache = {}
        self.max_size = max_size
        # logger が None の場合、デフォルトの DebugLogger を作成
        self.logger = logger if logger is not None else DebugLogger()

    def _create_cache_key(self, params: Dict) -> str:
        """キャッシュキーを生成 (パラメータ辞書をソートして文字列化)
        Args:
            params (dict): 計算パラメータ
        Returns:
            str: キャッシュキー
        """
        # Numpy配列など、直接文字列化できない要素を考慮する必要がある場合は、
        # より洗練されたキー生成方法が必要になることがあります。
        # ここでは単純な辞書を想定しています。
        try:
            return str(sorted(params.items()))
        except TypeError:
            # params にソート不可能な型が含まれる場合の代替処理
            # (例: repr を使う、特定のキーだけ使うなど)
            # ここでは簡単な例として repr を使用
            return repr(params)

    def get_cache(self, params: Dict) -> Optional[np.ndarray]:
        """キャッシュからデータを取得
        Args:
            params (dict): 計算パラメータ
        Returns:
            np.ndarray or None: キャッシュされた画像データ（存在しない場合はNone）
        """
        key = self._create_cache_key(params)
        cached_item = self.cache.get(key)
        if cached_item:
            # キーが長い場合があるのでログでは一部だけ表示する
            self.logger.log(LogLevel.INFO, "Cache hit for key: " + key[:50] + "...")
            return cached_item['image']
        else:
            self.logger.log(LogLevel.INFO, "Cache miss for key: " + key[:50] + "...")
            return None

    def put_cache(self, params: Dict, data: np.ndarray) -> None:
        """データをキャッシュに保存
        Args:
            params (dict): 計算パラメータ
            data (np.ndarray): キャッシュするデータ (画像配列)
        """
        key = self._create_cache_key(params)
        if len(self.cache) >= self.max_size:
            try:
                # 最も古いキーを取得して削除 (Python 3.7+ では挿入順序が保証される)
                first_key = next(iter(self.cache))
                del self.cache[first_key]
                self.logger.log(LogLevel.DEBUG, "キャッシュフル。最も古いキーアイテムを削除: " + first_key[:50] + "...")
            except StopIteration:
                # キャッシュが空の場合は何もしない
                pass
        self.cache[key] = {'params': params, 'image': data}
        self.logger.log(LogLevel.DEBUG, "キャッシュキー: " + key[:50] + "...")
