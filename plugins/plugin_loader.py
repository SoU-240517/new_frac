import importlib
import json
import os
import sys
import inspect # モジュール内の関数を見つけるため
from typing import Dict, Any, Optional, Callable, List

from debug import DebugLogger, LogLevel

# --- ユーティリティ関数 ---
def _filename_to_display_name(filename: str) -> str:
    """ファイル名から表示名を生成するヘルパー関数 (例: some_plugin.py -> Some Plugin)"""
    name_without_ext = os.path.splitext(filename)[0] # 拡張子を除去
    return name_without_ext.replace("_", " ").title()

# --- プラグインローダーの基底クラス ---
class PluginLoaderBase:
    """
    プラグインローダーの基本クラス

    モジュールの動的インポートや、モジュールからの関数取得といった共通機能を提供する。
    また、プラグインディレクトリのスキャン処理の共通基盤も提供する。
    """

    def __init__(self, logger: Optional[DebugLogger] = None):
        """
        Args:
            logger (Optional[DebugLogger]): ロギング用インスタンス
        """
        self.logger = logger
        self._ensure_project_root_in_sys_path()

    def _ensure_project_root_in_sys_path(self) -> None:
        """
        プロジェクトのルートディレクトリを Python のモジュール検索パス (sys.path) に追加する。
        これにより、プラグインモジュールのインポートが安定して行えるようになる。
        この plugin_loader.py が配置されているディレクトリの親ディレクトリをプロジェクトルートと仮定する。
        """
        try:
            # このファイル (plugin_loader.py) のあるディレクトリの親ディレクトリを取得
            # 例: new_frac/plugins/plugin_loader.py -> new_frac/plugins -> new_frac
            project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
            if project_root not in sys.path:
                sys.path.insert(0, project_root)
                if self.logger:
                    self.logger.log(LogLevel.DEBUG, f"sys.path にプロジェクトルートを追加: {project_root}")
        except Exception as e:
            if self.logger:
                self.logger.log(LogLevel.ERROR, f"sys.path の設定中にエラー: {e}")

    def _load_module(self, module_import_path: str, context_name_for_log: str) -> Optional[Any]:
        """
        指定されたPythonモジュールを動的にインポート（読み込み）する

        Args:
            module_import_path (str): インポートするモジュールのフルパス (例: "plugins.fractal_types.julia.julia")
            context_name_for_log (str): ログ出力時に使用する、文脈を示す名前 (例: プラグイン名 "julia")

        Returns:
            Optional[Any]: インポートされたモジュールオブジェクト。失敗した場合は None。
        """
        try:
            module = importlib.import_module(module_import_path)
            if self.logger:
                self.logger.log(LogLevel.DEBUG, f"モジュールインポート成功: {context_name_for_log}")
            return module
        except ImportError as e:
            if self.logger:
                # エラーメッセージにインポートしようとしたパスを含める
                self.logger.log(LogLevel.ERROR, f"'{context_name_for_log}' のモジュール '{module_import_path}' のインポートエラー: {e}")
            return None
        except Exception as e: # その他の予期せぬエラーもキャッチ
            if self.logger:
                self.logger.log(LogLevel.ERROR, f"'{context_name_for_log}' のモジュール '{module_import_path}' のロード中に予期せぬエラー: {e}")
            return None

    def _get_callable_from_module(self, module: Any, function_name: str, context_name_for_log: str) -> Optional[Callable]:
        """
        インポート済みのモジュールから、指定された名前の呼び出し可能なオブジェクト（通常は関数）を取得する

        Args:
            module (Any): インポートされたモジュールオブジェクト。
            function_name (str): 取得したい関数（または呼び出し可能なオブジェクト）の名前。
            context_name_for_log (str): ログ出力時に使用する、文脈を示す名前。

        Returns:
            Optional[Callable]: 取得された呼び出し可能なオブジェクト。見つからないか、呼び出し可能でなければ None。
        """
        try:
            func_candidate = getattr(module, function_name, None)

            if func_candidate is None:
                if self.logger:
                    self.logger.log(LogLevel.ERROR, f"'{context_name_for_log}' モジュールに属性 '{function_name}' が見つかりません。")
                return None
            if not callable(func_candidate):
                if self.logger:
                    self.logger.log(LogLevel.ERROR, f"'{context_name_for_log}' モジュールの属性 '{function_name}' は呼び出し可能ではありません。")
                return None
            if self.logger:
                self.logger.log(LogLevel.DEBUG, f"関数取得成功: {function_name}")
            return func_candidate
        except AttributeError:
            if self.logger:
                self.logger.log(LogLevel.ERROR, f"'{context_name_for_log}' モジュールに属性 '{function_name}' が見つかりません (AttributeError)。")
            return None
        except Exception as e:
            if self.logger:
                self.logger.log(LogLevel.ERROR, f"'{context_name_for_log}' モジュールから関数 '{function_name}' を取得中に予期せぬエラー: {e}")
            return None

    def _scan_and_process_directory(
        self,
        directory_path: str,
        item_processor_callback: Callable[[str, str, str], None]
    ) -> None:
        """
        指定されたディレクトリをスキャンし、各アイテムに対してコールバック関数を実行する。

        Args:
            directory_path (str): スキャンするディレクトリのパス。
            item_processor_callback (Callable[[str, str, str], None]):
                各アイテムに対して呼び出されるコールバック関数。
                引数は (item_name: str, item_path: str, scanned_directory_path: str)。
        """
        if not os.path.isdir(directory_path):
            if self.logger:
                self.logger.log(LogLevel.ERROR, f"スキャン対象ディレクトリ {directory_path} がない:")
            return

        if self.logger:
            self.logger.log(LogLevel.DEBUG, f"ディレクトリ {directory_path} をスキャン中...")

        for item_name in os.listdir(directory_path):
            item_path = os.path.join(directory_path, item_name)
            try:
                item_processor_callback(item_name, item_path, directory_path)
            except Exception as e:
                if self.logger:
                    self.logger.log(LogLevel.ERROR, f"アイテム '{item_name}' の処理中にエラー発生 ({directory_path}): {e}", exc_info=True)

# ---  fractal_type_plugin ローダー ---
class FractalTypeLoader(PluginLoaderBase):
    """
     fractal_type_plugin をロードし、管理するクラス
    """

    def __init__(self, plugin_dir: str, logger: Optional[DebugLogger] = None):
        super().__init__(logger)
        self.plugin_dir = plugin_dir # 例: "plugins/fractal_types"
        self.loaded_plugins: Dict[str, Dict[str, Any]] = {}

    def scan_and_load_plugins(self) -> None:
        """
        プラグインディレクトリをスキャンし、有効な fractal_type_plugin をロードする。
        """
        self.loaded_plugins = {} # ロード前にクリア

        if self.logger:
            self.logger.log(LogLevel.INFO, "fractal_type_plugin  のスキャンとロード開始")

        # _scan_and_process_directory を使用してディレクトリをスキャン
        self._scan_and_process_directory(self.plugin_dir, self._process_fractal_plugin_item)

        if self.logger:
            self.logger.log(LogLevel.SUCCESS, f"{len(self.loaded_plugins)} 個の fractal_type_plugin のロードに成功")

    def _process_fractal_plugin_item(self, item_name: str, item_path: str, scanned_directory_path: str) -> None:
        """
        _scan_and_process_directory から呼び出されるコールバック。
        アイテムがディレクトリであれば、フラクタルプラグインとしてロード試行。
        """
        if os.path.isdir(item_path): # フラクタルプラグインはディレクトリ形式
            if self.logger:
                self.logger.log(LogLevel.DEBUG, "plugin 検出", {"dir": item_name})
            # scanned_directory_path は self.plugin_dir と同じはず
            self._load_single_plugin(plugin_name=item_name, plugin_path=item_path)

    def _load_single_plugin(self, plugin_name: str, plugin_path: str) -> None:
        """
        個別の fractal_type_plugin をロードする
        """
        json_path = os.path.join(plugin_path, f"{plugin_name}.json")
        py_path = os.path.join(plugin_path, f"{plugin_name}.py") # JSON内の file_name と比較するならここで使用
        init_path = os.path.join(plugin_path, "__init__.py")

        if not os.path.exists(init_path):
            if self.logger: self.logger.log(LogLevel.WARNING, f"fractal_type_plugin '{plugin_name}' に __init__.py がないのでスキップ")
            return
        if not os.path.exists(json_path):
            if self.logger: self.logger.log(LogLevel.WARNING, f"fractal_type_plugin '{plugin_name}' の {plugin_name}.json 未検出でスキップ")
            return
        # py_path の存在チェックはJSONの file_name と照合後でも良いが、基本的な構造として先にチェック
        if not os.path.exists(py_path):
             if self.logger: self.logger.log(LogLevel.WARNING, f"fractal_type_plugin '{plugin_name}' の Pythonファイル {plugin_name}.py が見つからないためスキップ")
             return

        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                config = json.load(f) # フラクタルタイプのJSONは `config` という名前でロード
            if self.logger: self.logger.log(LogLevel.DEBUG, "JSON 読込完了", {"plugin_name": plugin_name})

            # フラクタルタイプ用JSONの必須キー
            required_keys = ["name", "description", "module_name", "function_name", "parameters"]
            if not all(key in config for key in required_keys):
                missing_keys = [key for key in required_keys if key not in config]
                if self.logger: self.logger.log(LogLevel.ERROR, f"fractal_type_plugin '{plugin_name}' : JSON の設定情報不足でスキップ: {missing_keys}")
                return
            if config["module_name"] != plugin_name: # 通常、モジュール名とプラグインディレクトリ名は一致させる
                 if self.logger: self.logger.log(LogLevel.WARNING, f"fractal_type_plugin '{plugin_name}' : JSON の module_name ('{config['module_name']}') がディレクトリ名と不一致")
        except json.JSONDecodeError as e:
            if self.logger: self.logger.log(LogLevel.ERROR, f"fractal_type_plugin '{plugin_name}' : JSON 解析エラーによりスキップ: {e}")
            return
        except Exception as e: # その他のJSON読み込みエラー
            if self.logger: self.logger.log(LogLevel.ERROR, f"fractal_type_plugin '{plugin_name}' : JSON 読込中に予期せぬエラーでスキップ: {e}")
            return

        try:
            base_module_path = self.plugin_dir.replace('/', '.').replace('\\', '.')
            module_import_path = f"{base_module_path}.{plugin_name}.{config['module_name']}"
            log_context = f"fractal type '{plugin_name}'"

            module = self._load_module(module_import_path, log_context)
            if module is None:
                return

            function_name_from_json = config["function_name"]
            compute_function = self._get_callable_from_module(module, function_name_from_json, log_context)
            if compute_function is None:
                return

        except Exception as e:
            if self.logger: self.logger.log(LogLevel.ERROR, f"fractal_type_plugin '{plugin_name}' モジュール処理中に予期せぬエラーでスキップ: {e}", exc_info=True)
            return

        plugin_display_name = config["name"]
        self.loaded_plugins[plugin_display_name] = {
            "config": config,
            "compute_function": compute_function,
            "plugin_dir_name": plugin_name
        }
        if self.logger: self.logger.log(LogLevel.SUCCESS, f"fractal_type_plugin '{plugin_name}' のロード成功: 表示名: {plugin_display_name}")

    def get_available_types(self) -> List[str]:
        return list(self.loaded_plugins.keys())

    def get_plugin(self, name: str) -> Optional[Dict[str, Any]]:
        return self.loaded_plugins.get(name)

    def get_compute_function(self, name: str) -> Optional[Callable]:
        plugin = self.get_plugin(name)
        return plugin.get("compute_function") if plugin else None

    def get_parameters_config(self, name: str) -> Optional[List[Dict[str, Any]]]:
        plugin = self.get_plugin(name)
        return plugin.get("config", {}).get("parameters") if plugin else None

    def get_description(self, name: str) -> Optional[str]:
        plugin = self.get_plugin(name)
        return plugin.get("config", {}).get("description") if plugin else None

    def get_recommended_coloring(self, name: str) -> Optional[Dict[str, str]]:
        plugin = self.get_plugin(name)
        return plugin.get("config", {}).get("recommended_coloring") if plugin else None


# --- カラーリングプラグインローダー ---
class ColoringPluginLoader(PluginLoaderBase):
    """
    カラーリングアルゴリズムのプラグインを読み込むクラス
    """
    def __init__(self, divergent_dir: str, non_divergent_dir: str, logger: DebugLogger):
        super().__init__(logger)
        self.divergent_dir = divergent_dir
        self.non_divergent_dir = non_divergent_dir
        self.divergent_algorithms: Dict[str, Dict[str, Any]] = {}
        self.non_divergent_algorithms: Dict[str, Dict[str, Any]] = {}

        self._current_loaded_algos_temp: Dict[str, Callable] = {}
        self._current_plugin_type_name_temp: str = ""


    def scan_and_load_plugins(self):
        """発散部と非発散部の両方のカラーリングプラグインをスキャンして読み込む"""
        if self.logger:
            self.logger.log(LogLevel.INFO, "coloring_plugin のスキャンとロード開始")

        self.divergent_algorithms = self._load_plugins_for_type(self.divergent_dir, "発散部")
        self.non_divergent_algorithms = self._load_plugins_for_type(self.non_divergent_dir, "非発散部")

        if self.logger:
            self.logger.log(LogLevel.SUCCESS,
                              f"coloring_plugin ロード完了 - 発散部: {len(self.divergent_algorithms)}個, 非発散部: {len(self.non_divergent_algorithms)}個")

    def _load_plugins_for_type(self, directory: str, plugin_type_name: str) -> Dict[str, Callable]:
        """指定されたディレクトリから特定のタイプのカラーリングプラグインを読み込む内部メソッド"""
        self._current_loaded_algos_temp = {}
        self._current_plugin_type_name_temp = plugin_type_name

        self._scan_and_process_directory(directory, self._process_coloring_plugin_item)

        processed_algos = self._current_loaded_algos_temp.copy()
        self._current_loaded_algos_temp = {}
        return processed_algos

    def _process_coloring_plugin_item(self, item_name: str, item_path: str, scanned_directory_path: str) -> None:
        """
        _scan_and_process_directory から呼び出されるコールバック。
        カラーリングプラグインのアイテムを処理する。
        """
        module_name_simple = ""
        full_module_path_to_import = ""
        py_file_path_to_check = "" # 実際にロードするPythonファイルのパス
        json_config_path = ""      # 対応するJSONファイルのパス

        module_base_path = scanned_directory_path.replace('/', '.').replace('\\', '.')

        # --- プラグイン構造の判定とJSON/PYパスの設定 ---
        is_dir_plugin = False
        if os.path.isdir(item_path): # ディレクトリベースのプラグインか？ (例: smoothing/)
            module_name_simple = item_name # ディレクトリ名がプラグイン名 (例: "smoothing")

            # このディレクトリ内に __init__.py と プラグイン名.py, プラグイン名.json があるか確認
            init_py_in_subdir = os.path.join(item_path, "__init__.py")
            potential_py_file = os.path.join(item_path, f"{module_name_simple}.py")
            potential_json_file = os.path.join(item_path, f"{module_name_simple}.json")

            if os.path.exists(init_py_in_subdir) and os.path.exists(potential_py_file) and os.path.exists(potential_json_file):
                is_dir_plugin = True
                py_file_path_to_check = potential_py_file
                json_config_path = potential_json_file
                # インポートパス例: "plugins.coloring.divergent.smoothing.smoothing"
                # .pyファイル名 (module_name_simple) がモジュールとしてインポートされる
                full_module_path_to_import = f"{module_base_path}.{module_name_simple}.{module_name_simple}"
                if self.logger:
                    self.logger.log(LogLevel.DEBUG, f"{self._current_plugin_type_name_temp} の plugin を検出: dir = {module_name_simple}")
            else:
                if self.logger:
                    self.logger.log(LogLevel.WARNING, f"coloring_plugin '{item_name}' は不適切な構造のためスキップ")
                return
        elif os.path.isfile(item_path) and item_name.endswith(".py") and item_name != "__init__.py": # ファイルベースのプラグインか？ (例: linear.py)
            module_name_simple = item_name[:-3] # ".py" を除去 (例: "linear")

            # 対応する .json ファイルが同じ階層にあるか確認 (linear.json)
            potential_json_file = os.path.join(scanned_directory_path, f"{module_name_simple}.json")
            if os.path.exists(potential_json_file):
                py_file_path_to_check = item_path # これがPythonファイル
                json_config_path = potential_json_file
                # インポートパス例: "plugins.coloring.divergent.linear"
                full_module_path_to_import = f"{module_base_path}.{module_name_simple}"
                if self.logger:
                    self.logger.log(LogLevel.DEBUG, f"coloring_plugin  (単一ファイル形式) を検出: {module_name_simple} ({self._current_plugin_type_name_temp})")
            else:
                if self.logger:
                    self.logger.log(LogLevel.DEBUG, f"単一ファイル形式プラグイン '{item_name}' に対応するJSONファイル '{module_name_simple}.json' が見つからないためスキップ。")
                return
        else: # プラグインとして認識できないもの
            if self.logger:
                self.logger.log(LogLevel.DEBUG, f"アイテム '{item_name}' はカラーリングプラグインとして認識されませんでした ({self._current_plugin_type_name_temp})。スキップします。")
            return

        # --- JSONファイルから設定を読み込む ---
        if not json_config_path or not os.path.exists(json_config_path): #念のため再チェック
            if self.logger:
                self.logger.log(LogLevel.ERROR, f"coloring_plugin  '{module_name_simple}': JSONファイルパスが見つからないか存在しません: {json_config_path}")
            return

        plugin_config = {}
        try:
            with open(json_config_path, 'r', encoding='utf-8') as f:
                json_data = json.load(f)
            plugin_config = json_data.get("basic_settings", {}) # "basic_settings" の中身を取得
            if not plugin_config:
                if self.logger:
                    self.logger.log(LogLevel.ERROR, f"coloring_plugin  '{module_name_simple}': JSONファイルに 'basic_settings' がないか空です ({json_config_path})。スキップします。")

                return

            display_name = plugin_config.get("display_name")
            target_function_name_from_json = plugin_config.get("coloring_func_name")
            # json_py_filename = plugin_config.get("file_name") # 必要ならpy_file_path_to_checkと比較

            if not display_name or not target_function_name_from_json:
                if self.logger:
                    self.logger.log(LogLevel.ERROR, f"coloring_plugin '{module_name_simple}': JSON内の 'display_name' または 'coloring_func_name' が不足しています。スキップします。")
                return

            # --- argument_list の読み込み ---
            argument_list = json_data.get("argument_list", [])
            if not argument_list:
                if self.logger:
                    self.logger.log(LogLevel.WARNING, f"coloring_plugin '{module_name_simple}' (表示名: {display_name}): JSONに 'argument_list' が見つからないか空です。引数なしとして扱います。")

            if self.logger: self.logger.log(LogLevel.DEBUG, f"JSON 読取完了: {module_name_simple}")

        except json.JSONDecodeError as e:
            if self.logger:
                self.logger.log(LogLevel.ERROR, f"coloring_plugin '{module_name_simple}': JSON解析エラー ({json_config_path}): {e}。スキップします。")
            return
        except Exception as e:
            if self.logger:
                self.logger.log(LogLevel.ERROR, f"coloring_plugin '{module_name_simple}': JSON読み込み中に予期せぬエラー ({json_config_path}): {e}。スキップします。")
            return

        # --- モジュールロードと関数取得 ---
        log_context = f"{module_name_simple} (表示名: {display_name})"

        module = self._load_module(full_module_path_to_import, log_context)
        if module is None:
            return

        # --- JSONから取得した関数名を使用 ---
        coloring_function = self._get_callable_from_module(module, target_function_name_from_json, log_context)

        # 最終チェックと格納
        if coloring_function and callable(coloring_function):
            if display_name in self._current_loaded_algos_temp:
                if self.logger: self.logger.log(LogLevel.WARNING,
                    f"{self._current_plugin_type_name_temp} プラグインで表示名 '{display_name}' が重複 ({module_name_simple}.py)。上書きします。")

            # --- 辞書に格納する情報を変更 ---
            self._current_loaded_algos_temp[display_name] = {
                "function": coloring_function,
                "argument_list": argument_list,
                "config": plugin_config # basic_settings 部分
            }
            if self.logger: self.logger.log(LogLevel.SUCCESS,
                    f"{self._current_plugin_type_name_temp} coloring_plugin '{display_name}' のロード成功 ({module_name_simple}.py, 関数名: {target_function_name_from_json}, 引数: {argument_list})")
        else:
            if self.logger: self.logger.log(LogLevel.WARNING,
                    f"{self._current_plugin_type_name_temp} coloring_plugin'{module_name_simple}.py' (表示名: {display_name}) の関数 '{target_function_name_from_json}' が見つからないか呼び出し可能ではありません。")

    def get_divergent_algorithm_info(self, name: str) -> Optional[Dict[str, Any]]:
        return self.divergent_algorithms.get(name)

    def get_non_divergent_algorithm_info(self, name: str) -> Optional[Dict[str, Any]]:
        return self.non_divergent_algorithms.get(name)

    def get_divergent_algorithm_names(self) -> List[str]:
        return sorted(list(self.divergent_algorithms.keys()))

    def get_non_divergent_algorithm_names(self) -> List[str]:
        return sorted(list(self.non_divergent_algorithms.keys()))

    def get_divergent_function(self, name: str) -> Optional[Callable]:
        # --- アルゴリズム情報から関数を返す ---
        info = self.get_divergent_algorithm_info(name)
        return info.get("function") if info else None

    def get_non_divergent_function(self, name: str) -> Optional[Callable]:
        # --- アルゴリズム情報から関数を返す ---
        info = self.get_non_divergent_algorithm_info(name)
        return info.get("function") if info else None
