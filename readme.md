# 生成AIさんへ:
- 以下の明確化について、現在のコード中では不適切な部分もあるが、順次、以下の状態に修正する。
- キャンセルの明確化:
    - ズーム確定キャンセル:
        - ズーム確定で再描画されたフラクタルを元に戻す
        - パラメータパネルの情報も元に戻す
        - ズーム処理用の内部状態は全て消す
    - ズーム領域編集キャンセル:
        - ズーム領域の編集操作（移動、リサイズ、回転）を、一つ前の編集状態に戻す
        - 一つ前の編集状態が無い場合は、ズーム領域を削除する
        - ズーム領域を削除した場合は、ズーム処理用の内部状態も消す
- 確定の明確化:
    - ズーム確定:
        - ズーム操作全般を確定し、パラメータパネルの情報を更新した上で、フラクタルを再描画する
        - ズーム処理用の内部状態は全て消す
    - ズーム領域編集確定:
        - 移動、リサイズ、回転の編集操作をし終わった EDIT 状態
        - まだ編集は続けられる状態

# 主なデータフロー
MainWindow
├→ FractalCanvas → ZoomSelector → EventHandler → RectManager
└→ render_fractal → (julia/mandelbrot) → color_algorithms

# クラスの依存関係
new_frac/
├── main.py
│   └─→ ui.main_window.MainWindow
├── coloring/
│   ├── color_algorithms.py
│   │   ├─ ColorCache
│   │   ├─→ coloring.gradient
│   │   └─→ ui.zoom_function.debug_logger
│   └── gradient.py
├── fractal/
│   ├── render.py
│   │   ├─ FractalCache
│   │   ├─→ fractal.fractal_types.julia
│   │   ├─→ fractal.fractal_types.mandelbrot
│   │   ├─→ coloring.color_algorithms
│   │   └─→ ui.zoom_function.debug_logger
│   └── fractal_types/
│       ├── julia.py
│       └── mandelbrot.py
└── ui/
    ├── canvas.py
    │   └─ FractalCanvas
    │      └─→ ui.zoom_function.zoom_selector
    ├── main_window.py
    │   └─ MainWindow
    │      ├─→ ui.canvas.FractalCanvas
    │      ├─→ ui.parameter_panel.ParameterPanel
    │      └─→ fractal.render.render_fractal
    ├── parameter_panel.py
    │   └─ ParameterPanel
    └── zoom_function/
        ├── cursor_manager.py
        │   └─ CursorManager
        ├── debug_logger.py
        │   └─ DebugLogger (全クラスから参照)
        ├── event_handler.py
        │   └─ EventHandler
        │      ├─→ zoom_selector.ZoomSelector
        │      ├─→ rect_manager.RectManager
        │      └─→ cursor_manager.CursorManager
        ├── rect_manager.py
        │   └─ RectManager
        └── zoom_selector.py
            └─ ZoomSelector
               ├─→ event_handler.EventHandler
               ├─→ rect_manager.RectManager
               └─→ cursor_manager.CursorManager
