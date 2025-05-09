import importlib
import json
import os
import sys
from typing import Dict, Any, Optional, Callable, List
from debug import DebugLogger, LogLevel
import importlib # 動的インポートのため
import inspect # モジュール内の関数を見つけるため
from typing import Dict, Callable, Optional, List, Any # 型ヒントのため

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
    このクラスを継承することで、具体的なプラグインローダー (FractalTypeLoader や ColoringPluginLoader) は
    これらの共通処理を利用可能。
    """

    def __init__(self, logger: Optional[DebugLogger] = None):
        """
        Args:
            logger (Optional[DebugLogger]): ロギング用インスタンス
        """
        self.logger = logger
        # loaded_plugins のような具体的なプラグイン格納場所は、
        # サブクラス (このクラスを継承するクラス) ごとに異なるため、ここでは定義しません。

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
                self.logger.log(LogLevel.DEBUG, f"'{context_name_for_log}' のモジュール '{module_import_path}' のインポート成功")
            return module
        except ImportError as e:
            if self.logger:
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
            # モジュールから指定された名前の属性（変数や関数など）を取得します。
            # 見つからなかった場合は None を返します (getattr の第3引数)。
            func_candidate = getattr(module, function_name, None)

            if func_candidate is None:
                if self.logger:
                    self.logger.log(LogLevel.ERROR, f"'{context_name_for_log}' モジュールに属性 '{function_name}' が見つかりません。")
                return None
            # 取得したものが関数のように呼び出せるか (callable) を確認します。
            if not callable(func_candidate):
                if self.logger:
                    self.logger.log(LogLevel.ERROR, f"'{context_name_for_log}' モジュールの属性 '{function_name}' は呼び出し可能ではありません。")
                return None
            if self.logger:
                self.logger.log(LogLevel.DEBUG, f"'{context_name_for_log}' モジュールから関数 '{function_name}' の取得成功")
            return func_candidate
        except AttributeError: # 通常 getattr のデフォルト値でカバーされるが、念のため
            if self.logger:
                self.logger.log(LogLevel.ERROR, f"'{context_name_for_log}' モジュールに属性 '{function_name}' が見つかりません (AttributeError)。")
            return None
        except Exception as e: # その他の予期せぬエラー
            if self.logger:
                self.logger.log(LogLevel.ERROR, f"'{context_name_for_log}' モジュールから関数 '{function_name}' を取得中に予期せぬエラー: {e}")
            return None

# --- フラクタルタイププラグインローダー ---
class FractalTypeLoader(PluginLoaderBase): # PluginLoaderBase を継承
    """
    フラクタルタイププラグインをロードし、管理するクラス

    プラグインは JSON 設定ファイルと Python モジュールから構成され、
    フラクタルの計算関数とそのパラメータ設定を提供する。

    Attributes:
        plugin_dir (str): プラグインが格納されているディレクトリのパス
        loaded_plugins (Dict[str, Dict[str, Any]]): ロードされたプラグインの情報
        logger (Optional[DebugLogger]): ロギング用インスタンス (基底クラスで初期化)
    """

    def __init__(self, plugin_dir, logger: Optional[DebugLogger] = None):
        """
        Args:
            plugin_dir (str): プラグインが格納されているディレクトリのパス
            logger (Optional[DebugLogger]): ロギング用インスタンス
        """
        super().__init__(logger) # 基底クラス (PluginLoaderBase) の __init__ を呼び出す
        self.plugin_dir = plugin_dir
        self.loaded_plugins: Dict[str, Dict[str, Any]] = {} # プラグイン名 -> プラグイン情報の辞書

    def scan_and_load_plugins(self) -> None:
        """
        プラグインディレクトリをスキャンし、有効なプラグインをロードする

        各プラグインディレクトリからJSON設定ファイルとPythonモジュールを読み込み、
        フラクタル計算関数を初期化する。
        """
        self.loaded_plugins = {} # ロード前にクリア

        if not os.path.isdir(self.plugin_dir):
            if self.logger: self.logger.log(LogLevel.ERROR, "プラグインディレクトリなし", {"plugin_dir": self.plugin_dir})
            return

        if self.logger: self.logger.log(LogLevel.INFO, "フラクタルタイププラグインのスキャンとロード開始")
        for item in os.scandir(self.plugin_dir):
            if item.is_dir():
                plugin_name = item.name
                if self.logger: self.logger.log(LogLevel.DEBUG, "フラクタルタイププラグイン検出", {"plugin_name": plugin_name})
                self._load_single_plugin(plugin_name, item.path)
        if self.logger: self.logger.log(LogLevel.SUCCESS, f"{len(self.loaded_plugins)} 個のフラクタルタイププラグインのロードに成功")

    def _load_single_plugin(self, plugin_name: str, plugin_path: str) -> None:
        """
        個別のフラクタルタイププラグインをロードする

        JSON設定ファイルとPythonモジュールの存在を確認し、
        必要な要件を満たしている場合にのみロードを実行する。
        """
        json_path = os.path.join(plugin_path, f"{plugin_name}.json")
        py_path = os.path.join(plugin_path, f"{plugin_name}.py")
        init_path = os.path.join(plugin_path, "__init__.py")

        # --- プラグインの構造チェック (ここは変更なし) ---
        if not os.path.exists(init_path):
            if self.logger: self.logger.log(LogLevel.WARNING, f"フラクタルタイププラグイン '{plugin_name}' に __init__.py がないのでスキップ")
            return
        if not os.path.exists(json_path):
            if self.logger: self.logger.log(LogLevel.WARNING, f"フラクタルタイププラグイン '{plugin_name}' の {plugin_name}.json 未検出でスキップ")
            return
        if not os.path.exists(py_path):
            if self.logger: self.logger.log(LogLevel.WARNING, f"フラクタルタイププラグイン '{plugin_name}' の {plugin_name}.py 未検出でスキップ")
            return

        # --- JSON設定ファイルの読み込み (ここは変更なし) ---
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            if self.logger: self.logger.log(LogLevel.DEBUG, f"フラクタルタイププラグイン '{plugin_name}' の JSON 読込完了")

            required_keys = ["name", "description", "module_name", "function_name", "parameters"]
            if not all(key in config for key in required_keys):
                missing_keys = [key for key in required_keys if key not in config]
                if self.logger: self.logger.log(LogLevel.ERROR, f"フラクタルタイププラグイン '{plugin_name}' : JSON の設定情報不足でスキップ: {missing_keys}")
                return
            if config["module_name"] != plugin_name:
                 if self.logger: self.logger.log(LogLevel.WARNING, f"フラクタルタイププラグイン '{plugin_name}' : JSON の module_name がディレクトリ名と不一致: {config['module_name']}")
        except json.JSONDecodeError as e:
            if self.logger: self.logger.log(LogLevel.ERROR, f"フラクタルタイププラグイン '{plugin_name}' : JSON 解析エラーによりスキップ: {e}")
            return
        except Exception as e:
            if self.logger: self.logger.log(LogLevel.ERROR, f"フラクタルタイププラグイン '{plugin_name}' : JSON 読込中に予期せぬエラーでスキップ: {e}")
            return

        # --- Pythonモジュールのインポートと関数の取得 (基底クラスのメソッドを使用) ---
        try:
            # モジュールパスを生成 (例: plugins.fractal_types.julia.julia)
            # plugin_dir は "plugins/fractal_types" のような形式なので、"." に置換
            module_spec_path = f"{self.plugin_dir.replace('/', '.')}.{plugin_name}.{plugin_name}"

            # 基底クラスの _load_module メソッドを使用してモジュールをインポート
            module = self._load_module(module_spec_path, f"フラクタルタイプ '{plugin_name}'")
            if module is None:
                # _load_module 内でエラーログは出力済みなので、ここではリターンするだけ
                return

            function_name_from_json = config["function_name"]
            # 基底クラスの _get_callable_from_module メソッドを使用して関数を取得
            compute_function = self._get_callable_from_module(module, function_name_from_json, f"フラクタルタイプ '{plugin_name}'")
            if compute_function is None:
                # _get_callable_from_module 内でエラーログは出力済み
                return

        except Exception as e: # 上記以外の予期せぬエラー (モジュールパス生成など)
            if self.logger: self.logger.log(LogLevel.ERROR, f"フラクタルタイププラグイン '{plugin_name}' モジュール処理中に予期せぬエラーでスキップ: {e}")
            return

        # --- プラグイン情報を格納 (ここは変更なし) ---
        plugin_display_name = config["name"]
        self.loaded_plugins[plugin_display_name] = {
            "config": config,
            "compute_function": compute_function,
            "plugin_dir_name": plugin_name
        }
        if self.logger: self.logger.log(LogLevel.SUCCESS, f"フラクタルタイププラグイン '{plugin_name}' のロード成功: リスト表示名: {plugin_display_name}")

    # --- ゲッターメソッド群 (変更なし) ---
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
class ColoringPluginLoader(PluginLoaderBase): # PluginLoaderBase を継承
    """
    指定されたディレクトリからカラーリングアルゴリズムのプラグインを読み込むクラス

    各プラグインは、特定のカラーリング関数を定義するPythonファイル。
    """
    def __init__(self, divergent_dir: str, non_divergent_dir: str, logger: DebugLogger):
        super().__init__(logger) # 基底クラス (PluginLoaderBase) の __init__ を呼び出す
        self.divergent_dir = divergent_dir
        self.non_divergent_dir = non_divergent_dir
        # キー: 表示名 (例: "Smoothing"), 値: カラーリング関数オブジェクト
        self.divergent_algorithms: Dict[str, Callable] = {}
        self.non_divergent_algorithms: Dict[str, Callable] = {}

    def _load_plugins_from_dir(self, directory: str, plugin_type_name: str) -> Dict[str, Callable]:
        """指定されたディレクトリからカラーリングプラグインをスキャンして読み込む内部関数"""
        loaded_algos: Dict[str, Callable] = {}
        if not os.path.isdir(directory):
            if self.logger: self.logger.log(LogLevel.ERROR, f"{plugin_type_name} のプラグインディレクトリが見つかりません: {directory}")
            return loaded_algos

        if self.logger: self.logger.log(LogLevel.DEBUG, f"{plugin_type_name} のプラグインをスキャン中: {directory}")

        module_base_path = directory.replace('/', '.') # OSのパス区切り文字をドットに置換 (例: "plugins.coloring.divergent")

        for item_name in os.listdir(directory):
            item_path = os.path.join(directory, item_name)
            module_name_simple = "" # プラグインの単純名 (例: "smoothing")
            full_module_path = ""   # Python のインポートパス (例: "plugins.coloring.divergent.smoothing")

            if os.path.isdir(item_path):
                # サブディレクトリ形式のプラグイン (例: smoothing/smoothing.py)
                plugin_filename_in_subdir = f"{item_name}.py" # 例: "smoothing.py"
                plugin_filepath_in_subdir = os.path.join(item_path, plugin_filename_in_subdir)
                # __init__.py がサブディレクトリ内にないとパッケージとして認識されない場合がある
                init_py_in_subdir = os.path.join(item_path, "__init__.py")

                if os.path.exists(plugin_filepath_in_subdir) and os.path.exists(init_py_in_subdir):
                    module_name_simple = item_name # 例: "smoothing"
                    # インポートパス: plugins.coloring.divergent.smoothing.smoothing
                    full_module_path = f"{module_base_path}.{module_name_simple}.{module_name_simple}"
                    if self.logger: self.logger.log(LogLevel.DEBUG, f"カラーリングプラグイン (ディレクトリ形式) を検出: {module_name_simple}")
                else:
                    if self.logger: self.logger.log(LogLevel.DEBUG, f"ディレクトリ '{item_name}' は適切なカラーリングプラグイン構造ではないためスキップ。")
                    continue
            elif os.path.isfile(item_path) and item_name.endswith(".py") and item_name != "__init__.py":
                # 単一ファイル形式のプラグイン (例: linear.py)
                module_name_simple = item_name[:-3] # .py を除去 (例: "linear")
                # インポートパス: plugins.coloring.divergent.linear
                full_module_path = f"{module_base_path}.{module_name_simple}"
                if self.logger: self.logger.log(LogLevel.DEBUG, f"カラーリングプラグイン (単一ファイル形式) を検出: {module_name_simple}")
            else:
                continue # .pyファイルまたは関連ディレクトリでなければスキップ

            try:
                # --- モジュールのインポート (基底クラスのメソッドを使用) ---
                # context_name_for_log には、どのプラグインかを特定しやすい情報を渡す
                log_context = f"{plugin_type_name} カラーリングプラグイン '{module_name_simple}'"
                module = self._load_module(full_module_path, log_context)
                if module is None:
                    continue # エラーは _load_module 内でログ記録済み

                # --- 表示名の取得 (変更なし) ---
                display_name = getattr(module, "DISPLAY_NAME", None)
                if not display_name:
                    display_name = _filename_to_display_name(module_name_simple + ".py") # smoothing.py から "Smoothing"

                # --- カラーリング関数の取得 ---
                coloring_function: Optional[Callable] = None
                # 規約1: モジュール内の COLORING_FUNCTION_NAME 変数で指定された関数名
                target_function_name_from_var = getattr(module, "COLORING_FUNCTION_NAME", None)

                if target_function_name_from_var:
                    # 基底クラスの _get_callable_from_module を使用
                    coloring_function = self._get_callable_from_module(module, target_function_name_from_var, f"{log_context} (表示名: {display_name})")
                else:
                    # 規約2: "apply_" で始まる最初の公開関数を探す
                    for func_name_candidate, func_obj_candidate in inspect.getmembers(module, inspect.isfunction):
                        if func_name_candidate.startswith("apply_") and not func_name_candidate.startswith("_"):
                            coloring_function = func_obj_candidate # この場合は既に関数オブジェクト
                            if self.logger: self.logger.log(LogLevel.DEBUG, f"'{module_name_simple}' で規約 'apply_' により関数 '{func_name_candidate}' を発見")
                            break
                    # 規約3: "apply_{モジュール名}" という名前の関数 (フォールバック)
                    if not coloring_function:
                        fallback_func_name = f"apply_{module_name_simple}"
                        # hasattr で確認してから _get_callable_from_module を使う方が安全
                        if hasattr(module, fallback_func_name):
                            coloring_function = self._get_callable_from_module(module, fallback_func_name, f"{log_context} (表示名: {display_name}, フォールバック)")


                if coloring_function and callable(coloring_function): # callable の再確認 (inspect の場合は不要だが統一のため)
                    if display_name in loaded_algos:
                        if self.logger: self.logger.log(LogLevel.WARNING, f"{plugin_type_name} プラグインで表示名 '{display_name}' が重複 ({module_name_simple}.py)。上書きします。")
                    loaded_algos[display_name] = coloring_function
                    if self.logger: self.logger.log(LogLevel.SUCCESS, f"{plugin_type_name} '{display_name}' のロード成功 ({module_name_simple}.py, 関数名: {coloring_function.__name__})")
                else:
                    if self.logger: self.logger.log(LogLevel.WARNING, f"{plugin_type_name} プラグイン '{module_name_simple}.py' (表示名: {display_name}) に適切なカラーリング関数が見つかりません。")

            except Exception as e: # _load_module や _get_callable_from_module 以外の部分でのエラー
                if self.logger: self.logger.log(LogLevel.ERROR, f"{plugin_type_name} プラグイン '{module_name_simple}.py' の読み込み処理中に予期せぬエラー: {e}", exc_info=True)
        return loaded_algos

    def scan_and_load_plugins(self):
        """発散部と非発散部の両方のカラーリングプラグインをスキャンして読み込む"""
        if self.logger: self.logger.log(LogLevel.INFO, "カラーリングプラグインのスキャンとロード開始")

        # --- sys.path の設定 (これは ColoringPluginLoader 特有なのでここに残す) ---
        # この plugin_loader.py は sou-240517-new_frac/plugins/ にある想定
        # プロジェクトルート (sou-240517-new_frac) を sys.path に追加する
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        if project_root not in sys.path:
            sys.path.insert(0, project_root)
            if self.logger: self.logger.log(LogLevel.DEBUG, f"sys.path にプロジェクトルートを追加: {project_root}")
        # --- ここまで sys.path 設定 ---

        self.divergent_algorithms = self._load_plugins_from_dir(self.divergent_dir, "発散部")
        self.non_divergent_algorithms = self._load_plugins_from_dir(self.non_divergent_dir, "非発散部")
        if self.logger: self.logger.log(LogLevel.SUCCESS, f"カラーリングプラグインロード完了 - 発散部: {len(self.divergent_algorithms)}個, 非発散部: {len(self.non_divergent_algorithms)}個")

    # --- ゲッターメソッド群 (変更なし) ---
    def get_divergent_algorithm_names(self) -> List[str]:
        return sorted(list(self.divergent_algorithms.keys()))

    def get_non_divergent_algorithm_names(self) -> List[str]:
        return sorted(list(self.non_divergent_algorithms.keys()))

    def get_divergent_function(self, name: str) -> Optional[Callable]:
        return self.divergent_algorithms.get(name)

    def get_non_divergent_function(self, name: str) -> Optional[Callable]:
        return self.non_divergent_algorithms.get(name)
