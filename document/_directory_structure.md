# フォルダ構成

Directory structure:
└── sou-240517-new_frac/
    ├── readme.md
    ├── config.json
    ├── main.py
    ├── coloring/
    │   ├── __init__.py
    │   ├── cache.py
    │   ├── gradient.py
    │   ├── manager.py
    │   └── utils.py
    ├── core/
    │   ├── __init__.py
    │   ├── canvas.py
    │   ├── main_window.py
    │   ├── parameter_panel.py
    │   ├── render.py
    │   └── status_bar.py
    ├── debug/
    │   ├── __init__.py
    │   ├── debug_logger.py
    │   └── enum_debug.py
    ├── document/
    │   ├── _directory_structure.md
    │   └── _user_ profile.md
    ├── plugins/
    │   ├── coloring/
    │   │   ├── divergent/
    │   │   │   ├── __init__.py
    │   │   │   ├── angle.py
    │   │   │   ├── distance.py
    │   │   │   ├── histogram.py
    │   │   │   ├── linear.py
    │   │   │   ├── logarithmic.py
    │   │   │   ├── orbit_trap.py
    │   │   │   ├── potential.py
    │   │   │   └── smoothing.py
    │   │   └── non_divergent/
    │   │       ├── __init__.py
    │   │       ├── chaotic_orbit.py
    │   │       ├── complex_potential.py
    │   │       ├── convergence_speed.py
    │   │       ├── derivative.py
    │   │       ├── fourier_pattern.py
    │   │       ├── fractal_texture.py
    │   │       ├── gradient_based.py
    │   │       ├── histogram_equalization.py
    │   │       ├── internal_distance.py
    │   │       ├── orbit_trap_circle.py
    │   │       ├── palam_c_z.py
    │   │       ├── phase_symmetry.py
    │   │       ├── quantum_entanglement.py
    │   │       └── solid_color.py
    │   └── fractal_types/
    │       ├── __init__.py
    │       ├── loader.py
    │       ├── julia/
    │       │   ├── __init__.py
    │       │   ├── julia.json
    │       │   └── julia.py
    │       └── mandelbrot/
    │           ├── __init__.py
    │           ├── mandelbrot.json
    │           └── mandelbrot.py
    ├── ui/
    │   └── zoom_function/
    │       ├── __init__.py
    │       ├── cursor_manager.py
    │       ├── enum_rect.py
    │       ├── event_handler_core.py
    │       ├── event_handlers_private.py
    │       ├── event_handlers_utils.py
    │       ├── rect_manager.py
    │       ├── zoom_selector.py
    │       └── zoom_state_handler.py
    └── validator/
        ├── __init__.py
        └── event_validator.py
