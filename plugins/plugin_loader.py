import importlib
import json
import os
import sys
from typing import Dict, Any, Optional, Callable, List
from debug import DebugLogger, LogLevel
import importlib # 動的インポートのため
import inspect # モジュール内の関数を見つけるため
from typing import Dict, Callable, Optional, List # 型ヒントのため

def _filename_to_display_name(filename: str) -> str:
    """ファイル名から表示名を生成するヘルパー関数 (例: some_plugin.py -> Some Plugin)"""
    name_without_ext = os.path.splitext(filename)[0] # 拡張子を除去
    return name_without_ext.replace("_", " ").title()

class FractalTypeLoader:
    """
    フラクタルタイププラグインをロードし、管理するクラス。
    プラグインはJSON設定ファイルとPythonモジュールから構成され、
    フラクタルの計算関数とそのパラメータ設定を提供します。

    Attributes:
        plugin_dir (str): プラグインが格納されているディレクトリのパス
        loaded_plugins (Dict[str, Dict[str, Any]]): ロードされたプラグインの情報
        logger (Optional[DebugLogger]): ロギング用インスタンス
    """

    def __init__(self, plugin_dir, logger: Optional[DebugLogger] = None):
        """
        Args:
            plugin_dir (str): プラグインが格納されているディレクトリのパス
            logger (Optional[DebugLogger]): ロギング用インスタンス
        """
        self.logger = logger
        self.plugin_dir = plugin_dir
        self.loaded_plugins: Dict[str, Dict[str, Any]] = {} # プラグイン名 -> プラグイン情報の辞書

    def scan_and_load_plugins(self) -> None:
        """
        プラグインディレクトリをスキャンし、有効なプラグインをロードします。
        各プラグインディレクトリからJSON設定ファイルとPythonモジュールを読み込み、
        フラクタル計算関数を初期化します。

        Raises:
            なし（エラーはログとして記録され、該当プラグインのロードがスキップされます）
        """
        self.loaded_plugins = {} # ロード前にクリア

        if not os.path.isdir(self.plugin_dir):
            self.logger.log(LogLevel.ERROR, "プラグインディレクトリなし", {"plugin_dir": self.plugin_dir})
            return

        self.logger.log(LogLevel.INFO, "プラグインのスキャンとロード開始")
        for item in os.scandir(self.plugin_dir):
            if item.is_dir():
                plugin_name = item.name
                self.logger.log(LogLevel.DEBUG, "プラグイン検出", {"plugin_name": plugin_name})
                self._load_single_plugin(plugin_name, item.path)
        self.logger.log(LogLevel.SUCCESS, f"{len(self.loaded_plugins)} 個のロードに成功")

    def _load_single_plugin(self, plugin_name: str, plugin_path: str) -> None:
        """
        個別のプラグインをロードします。
        JSON設定ファイルとPythonモジュールの存在を確認し、
        必要な要件を満たしている場合にのみロードを実行します。

        Args:
            plugin_name (str): プラグインのディレクトリ名
            plugin_path (str): プラグインディレクトリの絶対パス

        Raises:
            なし（エラーはログとして記録され、該当プラグインのロードがスキップされます）
        """
        json_path = os.path.join(plugin_path, f"{plugin_name}.json")
        py_path = os.path.join(plugin_path, f"{plugin_name}.py")
        init_path = os.path.join(plugin_path, "__init__.py")

        if not os.path.exists(init_path):
            self.logger.log(LogLevel.WARNING, f"不適切な情報なのでスキップ: {plugin_name}")
            return

        if not os.path.exists(json_path):
            self.logger.log(LogLevel.WARNING, f"{plugin_name} の {plugin_name}.json 未検出でスキップ")
            return

        if not os.path.exists(py_path):
            self.logger.log(LogLevel.WARNING, f"{plugin_name} の {plugin_name}.py 未検出でスキップ")
            return

        # 1. JSON設定ファイルの読み込み
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            self.logger.log(LogLevel.DEBUG, f"{plugin_name} の JSON 読込完了")

            # --- JSON設定の必須キーを検証 ---
            required_keys = ["name", "description", "module_name", "function_name", "parameters"]
            if not all(key in config for key in required_keys):
                missing_keys = [key for key in required_keys if key not in config]
                self.logger.log(LogLevel.ERROR, f"{plugin_name} : JSON の設定情報不足でスキップ: {missing_keys}")
                return
            if config["module_name"] != plugin_name:
                 self.logger.log(LogLevel.WARNING, f"{plugin_name} : JSON の module_name がディレクトリ名と不一致: {config['module_name']}")
        except json.JSONDecodeError as e:
            self.logger.log(LogLevel.ERROR, f"{plugin_name} : JSON 解析エラーによりスキップ: {e}")
            return
        except Exception as e:
            self.logger.log(LogLevel.ERROR, f"{plugin_name} : JSON 読込中に予期せぬエラーでスキップ: {e}")
            return

        # 2. Pythonモジュールのインポートと関数の取得
        try:
            # モジュールパスを生成 (例: plugins.fractal_types.julia)
            module_spec_path = f"{self.plugin_dir.replace('/', '.')}.{plugin_name}.{plugin_name}"

            # importlib を使ってモジュールを動的にインポート
            module = importlib.import_module(module_spec_path)
            self.logger.log(LogLevel.DEBUG, f"{plugin_name} のモジュールインポート完了")

            # JSON で指定された関数を取得
            function_name = config["function_name"]
            compute_function = getattr(module, function_name, None)

            if compute_function is None or not callable(compute_function):
                self.logger.log(LogLevel.ERROR, f"{plugin_name} モジュールに関数 {function_name} が見つからないか、呼び出し不可能でスキップ")
                return

            self.logger.log(LogLevel.DEBUG, f"{plugin_name} の関数 '{function_name}' を取得完了")

        except ImportError as e:
            self.logger.log(LogLevel.ERROR, f"{plugin_name} モジュールインポートエラーでスキップ: {e}")
            self.logger.log(LogLevel.ERROR, f"パスの確認が必要: {module_spec_path}")
            return
        except AttributeError as e:
             self.logger.log(LogLevel.ERROR, f"{plugin_name} モジュール属性エラーでスキップ: {e}")
             self.logger.log(LogLevel.ERROR, f"関数名の確認が必要: {config.get('function_name', 'N/A')}")
             return
        except Exception as e:
            self.logger.log(LogLevel.ERROR, f"{plugin_name} モジュール処理中に予期せぬエラーでスキップ: {e}")
            return

        # 3. プラグイン情報を格納
        plugin_display_name = config["name"] # JSON内の "name" を表示名とする
        self.loaded_plugins[plugin_display_name] = {
            "config": config,
            "compute_function": compute_function,
            "plugin_dir_name": plugin_name # 必要であればディレクトリ名も保持
        }

        self.logger.log(LogLevel.SUCCESS, f"{plugin_name} のロード成功: リスト表示名: {plugin_display_name}")

    def get_available_types(self) -> List[str]:
        """
        ロードされたフラクタルタイプの表示名のリストを返します。

        Returns:
            List[str]: ロードされたフラクタルタイプの表示名のリスト
        """
        return list(self.loaded_plugins.keys())

    def get_plugin(self, name: str) -> Optional[Dict[str, Any]]:
        """
        指定された表示名に対応するプラグイン情報を返します。

        Args:
            name (str): フラクタルタイプの表示名

        Returns:
            Optional[Dict[str, Any]]: プラグイン情報の辞書（存在しない場合はNone）
        """
        return self.loaded_plugins.get(name)

    def get_compute_function(self, name: str) -> Optional[Callable]:
        """
        指定された表示名に対応するフラクタル計算関数を返します。

        Args:
            name (str): フラクタルタイプの表示名

        Returns:
            Optional[Callable]: フラクタル計算関数（存在しない場合はNone）
        """
        plugin = self.get_plugin(name)
        return plugin.get("compute_function") if plugin else None

    def get_parameters_config(self, name: str) -> Optional[List[Dict[str, Any]]]:
        """
        指定された表示名に対応するパラメータ設定リストを返します。

        Args:
            name (str): フラクタルタイプの表示名

        Returns:
            Optional[List[Dict[str, Any]]]: パラメータ設定リスト（存在しない場合はNone）
        """
        plugin = self.get_plugin(name)
        return plugin.get("config", {}).get("parameters") if plugin else None

    def get_description(self, name: str) -> Optional[str]:
        """
        指定された表示名に対応する説明文を返します。

        Args:
            name (str): フラクタルタイプの表示名

        Returns:
            Optional[str]: プラグインの説明文（存在しない場合はNone）
        """
        plugin = self.get_plugin(name)
        return plugin.get("config", {}).get("description") if plugin else None

    def get_recommended_coloring(self, name: str) -> Optional[Dict[str, str]]:
        """
        指定された表示名に対応する推奨カラーリング設定を返します。

        Args:
            name (str): フラクタルタイプの表示名

        Returns:
            Optional[Dict[str, str]]: 推奨カラーリング設定（存在しない場合はNone）
        """
        plugin = self.get_plugin(name)
        return plugin.get("config", {}).get("recommended_coloring") if plugin else None

class ColoringPluginLoader:
    """
    指定されたディレクトリからカラーリングアルゴリズムのプラグインを読み込むクラス。
    各プラグインは、特定のカラーリング関数を定義するPythonファイルです。
    """
    def __init__(self, divergent_dir: str, non_divergent_dir: str, logger: DebugLogger):
        self.divergent_dir = divergent_dir
        self.non_divergent_dir = non_divergent_dir
        self.logger = logger
        # キー: 表示名 (例: "Smoothing"), 値: カラーリング関数オブジェクト
        self.divergent_algorithms: Dict[str, Callable] = {}
        self.non_divergent_algorithms: Dict[str, Callable] = {}

    def _load_plugins_from_dir(self, directory: str, plugin_type_name: str) -> Dict[str, Callable]:
        """指定されたディレクトリからプラグインをスキャンして読み込む内部関数"""
        loaded_algos: Dict[str, Callable] = {}
        if not os.path.isdir(directory):
            self.logger.log(LogLevel.ERROR, f"{plugin_type_name} のプラグインディレクトリが見つかりません: {directory}")
            return loaded_algos

        self.logger.log(LogLevel.DEBUG, f"{plugin_type_name} のプラグインをスキャン中: {directory}")

        # importlib.import_module で正しくモジュールをインポートするためには、
        # プラグインディレクトリの親ディレクトリ (この場合は 'plugins') がPythonの検索パスに含まれているか、
        # もしくはプラグインのパスをPythonのモジュールパス形式 (例: 'plugins.coloring.divergent') に変換する必要があります。
        # ここでは、ディレクトリ構造 ('plugins/coloring/divergent/') をモジュールパス ('plugins.coloring.divergent') に変換します。
        module_base_path = directory.replace('/', '.') # OSのパス区切り文字をドットに置換
        # プロジェクトルートをsys.pathに追加する必要がある場合がある
        # 例: project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")) # main_window.pyの場所に応じて調整
        # if project_root not in sys.path:
        #     sys.path.insert(0, project_root)

        for item_name in os.listdir(directory):
            item_path = os.path.join(directory, item_name)
            # 各アルゴリズムがサブディレクトリに格納されている場合 (例: smoothing/smoothing.py)
            if os.path.isdir(item_path):
                # サブディレクトリ名と同じ名前の .py ファイルを探す (例: smoothing/smoothing.py)
                plugin_filename = f"{item_name}.py"
                plugin_filepath = os.path.join(item_path, plugin_filename)
                module_name_simple = item_name # smoothing
                # モジュールフルパス (例: plugins.coloring.divergent.smoothing.smoothing)
                full_module_path = f"{module_base_path}.{module_name_simple}.{module_name_simple}"
                is_package = True # サブディレクトリはパッケージとして扱う
            # .py ファイルが直接置かれている場合 (例: smoothing.py)
            elif os.path.isfile(item_path) and item_name.endswith(".py") and item_name != "__init__.py":
                plugin_filename = item_name
                plugin_filepath = item_path # 使用しないが念のため
                module_name_simple = item_name[:-3] # .pyを除去 (例: smoothing)
                # モジュールフルパス (例: plugins.coloring.divergent.smoothing)
                full_module_path = f"{module_base_path}.{module_name_simple}"
                is_package = False
            else:
                continue # .pyファイルまたは関連ディレクトリでなければスキップ

            try:
                self.logger.log(LogLevel.DEBUG, f"モジュール '{plugin_filename}' のインポート試行")
                module = importlib.import_module(full_module_path)
                self.logger.log(LogLevel.DEBUG, f"モジュールインポート成功: {plugin_filename}")

                # プラグインファイル内の規約に基づいて情報を取得
                # 1. 表示名: モジュール内の DISPLAY_NAME 変数、なければファイル名から生成
                display_name = getattr(module, "DISPLAY_NAME", None)
                if not display_name:
                    display_name = _filename_to_display_name(module_name_simple + ".py") # smoothing.py から "Smoothing"

                # 2. カラーリング関数: モジュール内の COLORING_FUNCTION_NAME 変数で指定された関数名
                #    または、apply_ で始まる関数を探す (例: apply_smoothing)
                target_function_name = getattr(module, "COLORING_FUNCTION_NAME", None)
                coloring_function = None

                if target_function_name:
                    coloring_function = getattr(module, target_function_name, None)
                else:
                    # apply_ で始まる最初の公開関数を探す
                    for func_name, func_obj in inspect.getmembers(module, inspect.isfunction):
                        if func_name.startswith("apply_") and not func_name.startswith("_"):
                            coloring_function = func_obj
                            self.logger.log(LogLevel.DEBUG, f"'{module_name_simple}' で関数 '{func_name}' を発見")
                            break
                    if not coloring_function and hasattr(module, f"apply_{module_name_simple}"): # 例: smoothing モジュール内の apply_smoothing 関数
                         coloring_function = getattr(module, f"apply_{module_name_simple}", None)
                         if coloring_function:
                             self.logger.log(LogLevel.DEBUG, f"'{module_name_simple}' で関数 'apply_{module_name_simple}' を発見")

                if coloring_function and callable(coloring_function):
                    if display_name in loaded_algos:
                        self.logger.log(LogLevel.WARNING, f"{plugin_type_name} プラグインで表示名 '{display_name}' が重複 ({plugin_filename})。上書きします。")
                    loaded_algos[display_name] = coloring_function
                    self.logger.log(LogLevel.SUCCESS, f"{plugin_type_name} {display_name} のロード成功 ({plugin_filename}, {coloring_function.__name__})")
                else:
                    self.logger.log(LogLevel.WARNING, f"{plugin_type_name} プラグイン '{plugin_filename}' に適切なカラーリング関数が見つかりません。")

            except ImportError as e:
                self.logger.log(LogLevel.WARNING, "プラグイン未検出でスキップ")

            except Exception as e:
                self.logger.log(LogLevel.ERROR, f"{plugin_type_name} プラグイン '{plugin_filename}' の読み込み中にエラー: {e}", exc_info=True)
        return loaded_algos

    def scan_and_load_plugins(self):
        """発散部と非発散部の両方のカラーリングプラグインをスキャンして読み込む"""
        self.logger.log(LogLevel.INFO, "カラーリングプラグインのスキャンとロード開始")
        # プロジェクトのルートディレクトリを sys.path に追加する必要があるかもしれません。
        # これにより、`plugins.coloring.divergent`のようなインポートが可能になります。
        # main_window.py が core ディレクトリにあるため、
        # プロジェクトルート (sou-240517-new_frac) を指すようにパスを調整します。
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..")) # main_window.py の場所に応じて調整
        if project_root not in sys.path:
            sys.path.insert(0, project_root)
            self.logger.log(LogLevel.DEBUG, f"sys.path にプロジェクトルートを追加: {project_root}")

        self.divergent_algorithms = self._load_plugins_from_dir(self.divergent_dir, "発散部")
        self.non_divergent_algorithms = self._load_plugins_from_dir(self.non_divergent_dir, "非発散部")
        self.logger.log(LogLevel.SUCCESS, f"発散部: {len(self.divergent_algorithms)}個, 非発散部: {len(self.non_divergent_algorithms)}個 のロード成功")

    def get_divergent_algorithm_names(self) -> List[str]:
        """読み込まれた発散部アルゴリズムの表示名リストを返す"""
        return sorted(list(self.divergent_algorithms.keys()))

    def get_non_divergent_algorithm_names(self) -> List[str]:
        """読み込まれた非発散部アルゴリズムの表示名リストを返す"""
        return sorted(list(self.non_divergent_algorithms.keys()))

    def get_divergent_function(self, name: str) -> Optional[Callable]:
        """指定された表示名に対応する発散部カラーリング関数を返す"""
        return self.divergent_algorithms.get(name)

    def get_non_divergent_function(self, name: str) -> Optional[Callable]:
        """指定された表示名に対応する非発散部カラーリング関数を返す"""
        return self.non_divergent_algorithms.get(name)
