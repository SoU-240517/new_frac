import importlib
import json
import os
import sys
from typing import Dict, Any, Optional, Callable, List

# ★ここは一時的★
# 現在のファイルの絶対パスを取得し、プロジェクトルートへのパスを計算
#current_dir = os.path.dirname(os.path.abspath(__file__))
#project_root = os.path.abspath(os.path.join(current_dir, "../.."))
# プロジェクトルートをPythonのパスに追加
#sys.path.insert(0, project_root)
# ★ここまで一時的★

from debug import DebugLogger, LogLevel

# プラグイン情報を格納するデータクラス (必要であれば)
# from dataclasses import dataclass
# @dataclass
# class FractalPlugin:
#     name: str
#     description: str
#     module_name: str
#     function_name: str
#     compute_function: Callable
#     parameters: List[Dict[str, Any]]
#     recommended_coloring: Dict[str, Any]

class FractalTypeLoader:
    """フラクタルタイププラグインをロードし、管理するクラス"""

    def __init__(self, plugin_dir: str = "plugins/fractal_types", logger: Optional[DebugLogger] = None):
        """
        Args:
            plugin_dir (str): プラグインが格納されているディレクトリのパス
            logger (Optional[DebugLogger]): ロギング用インスタンス
        """
        self.logger = logger

        self.plugin_dir = plugin_dir
        self.loaded_plugins: Dict[str, Dict[str, Any]] = {} # プラグイン名 -> プラグイン情報の辞書

    def scan_and_load_plugins(self) -> None:
        """プラグインディレクトリをスキャンし、有効なプラグインをロードする"""
        self.loaded_plugins = {} # ロード前にクリア

        if not os.path.isdir(self.plugin_dir):
            self.logger.log(LogLevel.ERROR, f"プラグインディレクトリが見つかりません: {self.plugin_dir}")
            return

        for item in os.scandir(self.plugin_dir):
            if item.is_dir():
                plugin_name = item.name
                self.logger.log(LogLevel.INFO, f"検出されたプラグイン候補ディレクトリ: {plugin_name}")
                self._load_single_plugin(plugin_name, item.path)

        self.logger.log(LogLevel.INFO, f"{len(self.loaded_plugins)} 個のプラグインをロード完了")

    def _load_single_plugin(self, plugin_name: str, plugin_path: str) -> None:
        """個別のプラグインをロードする試み"""
        json_path = os.path.join(plugin_path, f"{plugin_name}.json")
        py_path = os.path.join(plugin_path, f"{plugin_name}.py")
        init_path = os.path.join(plugin_path, "__init__.py") # __init__.py も確認

        if not os.path.exists(init_path):
             self.logger.log(LogLevel.WARNING, f"プラグイン '{plugin_name}' に __init__.py 未検出によりスキップ")
             return

        if not os.path.exists(json_path):
            self.logger.log(LogLevel.WARNING, f"プラグイン '{plugin_name}' に {plugin_name}.json 未検出によりスキップ")
            return

        if not os.path.exists(py_path):
            self.logger.log(LogLevel.WARNING, f"プラグイン '{plugin_name}' に {plugin_name}.py 未検出によりスキップ")
            return

        # 1. JSON設定ファイルの読み込み
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            self.logger.log(LogLevel.DEBUG, f"プラグイン '{plugin_name}' の JSON 設定読み込み完了")
            # --- JSON設定の必須キーを検証 ---
            required_keys = ["name", "description", "module_name", "function_name", "parameters"]
            if not all(key in config for key in required_keys):
                missing_keys = [key for key in required_keys if key not in config]
                self.logger.log(LogLevel.ERROR, f"プラグイン '{plugin_name}' の JSON 設定に必須キーが不足しています: {missing_keys}。スキップします。")
                return
            if config["module_name"] != plugin_name:
                 self.logger.log(LogLevel.WARNING, f"プラグイン '{plugin_name}' の JSON 内 module_name ('{config['module_name']}') がディレクトリ名と一致しません。")
            # ----------------------------------
        except json.JSONDecodeError as e:
            self.logger.log(LogLevel.ERROR, f"プラグイン '{plugin_name}' の JSON 設定ファイル解析エラー: {e}。スキップします。")
            return
        except Exception as e:
            self.logger.log(LogLevel.ERROR, f"プラグイン '{plugin_name}' の JSON 設定読み込み中に予期せぬエラー: {e}。スキップします。")
            return

        # 2. Pythonモジュールのインポートと関数の取得
        try:
            # モジュールパスを生成 (例: plugins.fractal_types.julia)
            # ここはプロジェクトのルートからの相対パスになるように調整が必要な場合があります
            module_spec_path = f"{self.plugin_dir.replace('/', '.')}.{plugin_name}.{plugin_name}"
            # importlib を使ってモジュールを動的にインポート
            module = importlib.import_module(module_spec_path)
            self.logger.log(LogLevel.DEBUG, f"プラグイン '{plugin_name}' のモジュールインポート成功: {module_spec_path}")

            # JSON で指定された関数を取得
            function_name = config["function_name"]
            compute_function = getattr(module, function_name, None)

            if compute_function is None or not callable(compute_function):
                self.logger.log(LogLevel.ERROR, f"プラグイン '{plugin_name}' のモジュールに関数 '{function_name}' が見つからないか、呼び出し可能ではありません。スキップします。")
                return

            self.logger.log(LogLevel.DEBUG, f"プラグイン '{plugin_name}' の関数 '{function_name}' 取得成功")

        except ImportError as e:
            self.logger.log(LogLevel.ERROR, f"プラグイン '{plugin_name}' のモジュールインポートエラー: {e}。パスを確認してください: {module_spec_path}。スキップします。")
            return
        except AttributeError as e:
             self.logger.log(LogLevel.ERROR, f"プラグイン '{plugin_name}' のモジュール属性エラー: {e}。関数名 '{config.get('function_name', 'N/A')}' を確認してください。スキップします。")
             return
        except Exception as e:
            self.logger.log(LogLevel.ERROR, f"プラグイン '{plugin_name}' のモジュール処理中に予期せぬエラー: {e}。スキップします。")
            return

        # 3. プラグイン情報を格納
        plugin_display_name = config["name"] # JSON内の "name" を表示名とする
        self.loaded_plugins[plugin_display_name] = {
            "config": config,
            "compute_function": compute_function,
            "plugin_dir_name": plugin_name # 必要であればディレクトリ名も保持
        }
        self.logger.log(LogLevel.DEBUG, f"プラグイン '{plugin_display_name}' (from '{plugin_name}') のロード成功")

    def get_available_types(self) -> List[str]:
        """ロードされたフラクタルタイプの表示名のリストを返す"""
        return list(self.loaded_plugins.keys())

    def get_plugin(self, name: str) -> Optional[Dict[str, Any]]:
        """指定された表示名に対応するプラグイン情報を返す"""
        return self.loaded_plugins.get(name)

    def get_compute_function(self, name: str) -> Optional[Callable]:
        """指定された表示名に対応するフラクタル計算関数を返す"""
        plugin = self.get_plugin(name)
        return plugin.get("compute_function") if plugin else None

    def get_parameters_config(self, name: str) -> Optional[List[Dict[str, Any]]]:
        """指定された表示名に対応するパラメータ設定リストを返す"""
        plugin = self.get_plugin(name)
        return plugin.get("config", {}).get("parameters") if plugin else None

    def get_description(self, name: str) -> Optional[str]:
        """指定された表示名に対応する説明文を返す"""
        plugin = self.get_plugin(name)
        return plugin.get("config", {}).get("description") if plugin else None

    def get_recommended_coloring(self, name: str) -> Optional[Dict[str, str]]:
         """指定された表示名に対応する推奨カラーリング設定を返す"""
         plugin = self.get_plugin(name)
         return plugin.get("config", {}).get("recommended_coloring") if plugin else None


# --- 使用例 ---
#if __name__ == '__main__':
    # **************************************************************
    # このファイル単体で実行した場合のテスト用コード
    # **************************************************************
    # pluginディレクトリのパスを適切に設定してください
    # この例では、loader.py の一つ上の階層を基準としています
#    logger = DebugLogger()

#    loader = FractalTypeLoader(plugin_dir="./plugins/fractal_types", logger=logger)
#    loader.scan_and_load_plugins()

#    print("\nロードされたフラクタルタイプ:")
#    types = loader.get_available_types()
#    print(types)

#    if types:
#        selected_type = types[0] # 最初のタイプを選択
#        print(f"\n--- {selected_type} の情報 ---")
#        plugin_info = loader.get_plugin(selected_type)
#        if plugin_info:
#            print("設定:", json.dumps(plugin_info.get("config"), indent=2, ensure_ascii=False))
#            print("計算関数:", plugin_info.get("compute_function"))
#            print("パラメータ設定:", loader.get_parameters_config(selected_type))
#            print("説明:", loader.get_description(selected_type))
#            print("推奨カラーリング:", loader.get_recommended_coloring(selected_type))

        # 計算関数の取得例
#        compute_func = loader.get_compute_function(selected_type)
#        print(f"\n取得した計算関数 ({selected_type}):", compute_func)
