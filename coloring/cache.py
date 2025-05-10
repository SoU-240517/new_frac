import numpy as np
from typing import Dict, Optional, Any
from debug import DebugLogger, LogLevel

class ColorCache:
    """フラクタル画像のキャッシュ管理クラス
    - 既に計算されたフラクタル画像の再利用を可能にする
    - キャッシュの保存、取得、管理を行う
    Attributes:
        cache (dict): キャッシュデータを保持する辞書
        max_size (int): キャッシュの最大サイズ (設定ファイルから読み込む)
        logger (DebugLogger): デバッグログを記録するためのロガー
    """

    def __init__(self, config: Dict[str, Any], logger: Optional[DebugLogger] = None):
        """ColorCache クラスのコンストラクタ
        - クラスの初期化を行う
        - キャッシュの最大サイズを設定ファイルから読み込む
        - ロガーを設定する
        Args:
            config (Dict[str, Any]): config.json から読み込んだ設定データ
            logger (DebugLogger, optional): デバッグ用ロガー。指定されない場合は新しい DebugLogger が生成される
        """
        self.cache = {}
        self.logger = logger

        # 設定ファイルからキャッシュ最大サイズを取得
        coloring_settings = config.get("coloring_settings", {})
        # フォールバック用のデフォルト値を設定
        default_cache_max_size = 100
        self.cache_max_size = coloring_settings.get("cache_max_size", default_cache_max_size)

        # max_size が非正数の場合の処理
        if self.cache_max_size <= 0:
            self.logger.log(LogLevel.WARNING, f"設定ファイルの cache_max_size ({self.cache_max_size}) が無効なのでデフォルト値 ({default_cache_max_size}) を使用")
            self.cache_max_size = default_cache_max_size
        else:
             self.logger.log(LogLevel.LOAD, "設定読込", {"cache_max_size": self.cache_max_size})

    def _create_cache_key(self, params: Dict) -> str:
        """キャッシュキーを生成 (パラメータ辞書をソートして文字列化)
        - 計算パラメータの辞書をソートして文字列に変換する
        - キャッシュへの保存や取得に使用するキーを作成する
        Args:
            params (dict): 計算パラメータを含む辞書
        Returns:
            str: 生成されたキャッシュキー
        """
        # パラメータに numpy 配列などが含まれると TypeError が発生する可能性
        # より堅牢な方法として、json.dumps を使う方法もある
        import json
        try:
            # numpy 配列などを扱えるように default ハンドラを指定する例
            # def default_serializer(obj):
            #     if isinstance(obj, np.ndarray):
            #         # 配列はハッシュ値や形状、dtypeなどで代表させるなど
            #         return f"ndarray_shape_{obj.shape}_dtype_{obj.dtype}"
            #     raise TypeError(f"Object of type {obj.__class__.__name__} is not JSON serializable")
            # return json.dumps(params, sort_keys=True, default=default_serializer)

            # シンプルな辞書のみを想定 (現在の実装)
             return str(sorted(params.items()))
        except TypeError as e:
            # params にソート不可能な型が含まれる場合の代替処理
            self.logger.log(LogLevel.WARNING, f"キャッシュキー生成中に TypeError ({e})。reprを使用する。パラメータ内容の確認が必要: {params}")
            # repr を使う (オブジェクト固有の表現になるが、一意性は保証されにくい)
            return repr(params)
        except Exception as e:
            self.logger.log(LogLevel.ERROR, "キャッシュキー生成中に予期せぬエラー", {"message": e})
            # エラー発生時の代替キー (キャッシュ効率は落ちる)
            return f"error_key_{hash(frozenset(params.items()))}" if isinstance(params, dict) else f"error_key_{hash(params)}"

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
        key_short = key[:80] + "..." if len(key) > 80 else key # ログ用短縮キー
        if cached_item:
            self.logger.log(LogLevel.INFO, "キャッシュヒット", {"key_short": key_short})
            # キャッシュアイテムの構造が変わる可能性を考慮
            return cached_item.get('image') if isinstance(cached_item, dict) else None
        else:
            self.logger.log(LogLevel.INFO, "キャッシュミス", {"key_short": key_short})
            return None

    def put_cache(self, params: Dict, data: np.ndarray) -> None:
        """画像データをキャッシュに保存 (変更なし)
        - 計算パラメータとそれに対応する画像データをキャッシュに保存する
        - キャッシュが最大サイズに達している場合は、最も古いアイテムを削除 (LRU 風)
        Args:
            params (dict): 画像に関連付けられた計算パラメータ
            data (np.ndarray): キャッシュする画像データ
        """
        if self.cache_max_size <= 0: # キャッシュ無効の場合
             self.logger.log(LogLevel.DEBUG, "キャッシュ最大サイズが0以下なので保存をスキップします。")
             return

        key = self._create_cache_key(params)
        key_short = key[:80] + "..." if len(key) > 80 else key # ログ用短縮キー

        # 既にキーが存在する場合は更新 (古いものを削除する必要はない)
        if key in self.cache:
             self.logger.log(LogLevel.DEBUG, f"既存キャッシュキーを更新: {key_short}")
        # 新しいキーで、かつキャッシュが満杯の場合
        elif len(self.cache) >= self.cache_max_size:
            try:
                # 最も古いキーを取得して削除 (Python 3.7+ 前提)
                first_key = next(iter(self.cache))
                first_key_short = first_key[:80] + "..." if len(first_key) > 80 else first_key
                del self.cache[first_key]
                self.logger.log(LogLevel.DEBUG, f"キャッシュ超過。最も古いキーアイテムを削除: {first_key_short}")
            except StopIteration:
                # キャッシュが空の場合はここに来ないはずだが念のため
                self.logger.log(LogLevel.WARNING, "キャッシュ削除試行中に StopIteration (キャッシュが空？)")
                pass
            except Exception as e:
                 self.logger.log(LogLevel.ERROR, f"キャッシュ削除中にエラー: {e}")

        # キャッシュにデータを保存 (params も含めておくとデバッグに役立つ場合がある)
        self.cache[key] = {'params': params, 'image': data}
        self.logger.log(LogLevel.DEBUG, f"キャッシュに保存成功: {key_short}")
