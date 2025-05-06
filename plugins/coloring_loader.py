# sou-240517-new_frac/plugins/coloring_loader.py
import importlib.util
import os
from typing import Dict, Callable, List, Tuple, Any, Optional

from debug import DebugLogger, LogLevel # 既存のDebugLoggerを利用

# 着色プラグイン関数の期待される引数の型エイリアス (可読性向上のため)
# 実際のプラグイン関数はこの型シグネチャに従うことが期待されます。
# (例: iterations, z_values, mask, params, logger, config) -> np.ndarray
ColoringFunctionType = Callable[..., Any] # Any は np.ndarray を想定

class ColoringPluginLoader:
    """
    着色アルゴリズムのプラグインをロードし管理するクラス。
    指定されたディレクトリからプラグインをスキャンし、
    利用可能な着色関数を提供します。
    """

    def __init__(self, plugin_dirs: Dict[str, str], logger: DebugLogger):
        """
        ColoringPluginLoaderのコンストラクタ。

        Args:
            plugin_dirs (Dict[str, str]): 読み込むプラグインのカテゴリとディレクトリパスの辞書。
                                         例: {"divergent": "plugins/coloring/divergent",
                                               "non_divergent": "plugins/coloring/non_divergent"}
            logger (DebugLogger): ロガーインスタンス。
        """
        self.logger = logger
        self.plugin_dirs = plugin_dirs
        # ロードされたプラグインを保存する辞書
        # キー: プラグインカテゴリ (例: "divergent")
        # 値: {プラグイン名: プラグイン関数} の辞書
        self._coloring_functions: Dict[str, Dict[str, ColoringFunctionType]] = {}
        self.logger.log(LogLevel.INIT, "ColoringPluginLoaderのインスタンス作成開始")

    def scan_and_load_plugins(self) -> None:
        """
        設定されたプラグインディレクトリをスキャンし、有効な着色プラグインをロードする。
        """
        self.logger.log(LogLevel.CALL, "着色プラグインのスキャンとロードを開始します。")
        for category, plugin_dir_path in self.plugin_dirs.items():
            self._coloring_functions[category] = {} # カテゴリごとに初期化
            if not os.path.isdir(plugin_dir_path):
                self.logger.log(LogLevel.WARNING, f"プラグインディレクトリが見つかりません: {plugin_dir_path} (カテゴリ: {category})")
                continue

            self.logger.log(LogLevel.INFO, f"プラグインディレクトリをスキャン中 (カテゴリ: {category}): {plugin_dir_path}")
            for filename in os.listdir(plugin_dir_path):
                if filename.endswith(".py") and not filename.startswith("__init__"):
                    plugin_name = filename[:-3]  # .py 拡張子を除いた名前
                    module_path = os.path.join(plugin_dir_path, filename)
                    try:
                        # ファイルパスからモジュールを動的にインポート
                        # 'plugins.coloring.divergent.smoothing' のようなモジュール名を生成
                        module_import_name = f"{plugin_dir_path.replace('/', '.')}.{plugin_name}"

                        spec = importlib.util.spec_from_file_location(module_import_name, module_path)
                        if spec and spec.loader:
                            module = importlib.util.module_from_spec(spec)
                            spec.loader.exec_module(module)

                            # プラグインモジュール内で期待される関数 (例: apply_color) を取得
                            # この関数名は規約として定める (例: 各プラグインは apply_color を持つ)
                            if hasattr(module, "apply_color") and callable(getattr(module, "apply_color")):
                                self._coloring_functions[category][plugin_name] = getattr(module, "apply_color")
                                self.logger.log(LogLevel.SUCCESS, f"着色プラグイン '{plugin_name}' (カテゴリ: {category}) のロード成功")
                            else:
                                self.logger.log(LogLevel.WARNING, f"プラグイン '{plugin_name}' に 'apply_color' 関数が見つからないか、呼び出し可能ではありません。")
                        else:
                            self.logger.log(LogLevel.ERROR, f"プラグイン '{plugin_name}' のモジュール仕様の作成に失敗しました。")
                    except Exception as e:
                        self.logger.log(LogLevel.ERROR, f"プラグイン '{plugin_name}' のロード中にエラーが発生: {e}",
                                        context={"module_path": module_path})
        self.logger.log(LogLevel.SUCCESS, "全ての着色プラグインのスキャンとロードが完了しました。")
        self.logger.log(LogLevel.DEBUG, f"ロードされた着色関数: {self._coloring_functions}")


    def get_coloring_function(self, category: str, name: str) -> Optional[ColoringFunctionType]:
        """
        指定されたカテゴリと名前の着色関数を取得する。

        Args:
            category (str): プラグインのカテゴリ (例: "divergent", "non_divergent")。
            name (str): 取得したい着色関数の名前（ファイル名から .py を除いたもの）。

        Returns:
            Optional[ColoringFunctionType]: 見つかった場合は着色関数、見つからない場合は None。
        """
        category_functions = self._coloring_functions.get(category, {})
        func = category_functions.get(name)
        if func:
            self.logger.log(LogLevel.DEBUG, f"着色関数 '{name}' (カテゴリ: {category}) を取得しました。")
        else:
            self.logger.log(LogLevel.WARNING, f"着色関数 '{name}' (カテゴリ: {category}) が見つかりません。")
        return func

    def get_available_algorithms(self, category: str) -> List[str]:
        """
        指定されたカテゴリで利用可能な着色アルゴリズムの名前のリストを取得する。

        Args:
            category (str): プラグインのカテゴリ (例: "divergent", "non_divergent")。

        Returns:
            List[str]: 利用可能な着色アルゴリズム名のリスト。
        """
        if category in self._coloring_functions:
            return list(self._coloring_functions[category].keys())
        return []
