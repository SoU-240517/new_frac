import numpy as np
from typing import Dict, Optional
from ui.zoom_function.debug_logger import DebugLogger
from ui.zoom_function.enums import LogLevel

class ColorCache:
    """フラクタル画像のキャッシュ管理クラス
    - 既に計算されたフラクタル画像の再利用を可能にする
    - キャッシュの保存、取得、管理を行う
    Attributes:
        cache (dict): キャッシュデータを保持する辞書。キーは計算パラメータの文字列、値は画像データなど
        max_size (int): キャッシュの最大サイズ。保存できるアイテムの最大数
        logger (DebugLogger): デバッグログを記録するためのロガー。ログ出力機能
    """
    def __init__(self, max_size: int = 100, logger: Optional[DebugLogger] = None):
        """ColorCache クラスのコンストラクタ
        - クラスの初期化を行う
        - キャッシュの最大サイズとロガーを設定する
        Args:
            max_size (int): キャッシュの最大サイズ。デフォルトは100
            logger (DebugLogger): デバッグ用ロガー。指定されない場合は新しい DebugLogger が生成される
        """
        self.cache = {}
        self.max_size = max_size
        # logger が None の場合、デフォルトの DebugLogger を作成
        self.logger = logger if logger is not None else DebugLogger()

    def _create_cache_key(self, params: Dict) -> str:
        """キャッシュキーを生成 (パラメータ辞書をソートして文字列化)
        - 計算パラメータの辞書をソートして文字列に変換する
        - キャッシュへの保存や取得に使用するキーを作成する
        Args:
            params (dict): 計算パラメータを含む辞書
        Returns:
            str: 生成されたキャッシュキー
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
        """キャッシュから画像データを取得
        - 指定されたパラメータに対応する画像データをキャッシュから取得する
        Args:
            params (dict): 画像を識別するための計算パラメータ
        Returns:
            np.ndarray or None: キャッシュされた画像データ。存在しない場合は None
        """
        key = self._create_cache_key(params)
        cached_item = self.cache.get(key)
        if cached_item:
            # キーが長い場合があるのでログでは一部だけ表示する
            self.logger.log(LogLevel.INFO, "キーのキャッシュヒット: " + key[:50] + "...")
            return cached_item['image']
        else:
            self.logger.log(LogLevel.INFO, "キーのキャッシュミス: " + key[:50] + "...")
            return None

    def put_cache(self, params: Dict, data: np.ndarray) -> None:
        """画像データをキャッシュに保存
        - 計算パラメータとそれに対応する画像データをキャッシュに保存する
        - キャッシュが最大サイズに達している場合は、最も古いアイテムを削除する
        Args:
            params (dict): 画像に関連付けられた計算パラメータ
            data (np.ndarray): キャッシュする画像データ
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
