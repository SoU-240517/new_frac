# フォルダ構成

Directory structure:
└── sou-240517-new_frac/
    ├── config.json
    ├── main.py
    ├── coloring/
    │   ├── __init__.py
    │   ├── cache.py
    │   ├── gradient.py
    │   ├── manager.py
    │   ├── utils.py
    │   ├── divergent/
    │   │   ├── __init__.py
    │   │   ├── angle.py
    │   │   ├── distance.py
    │   │   ├── histogram.py
    │   │   ├── linear.py
    │   │   ├── logarithmic.py
    │   │   ├── orbit_trap.py
    │   │   ├── potential.py
    │   │   └── smoothing.py
    │   └── non_divergent/
    │       ├── __init__.py
    │       ├── chaotic_orbit.py
    │       ├── complex_potential.py
    │       ├── convergence_speed.py
    │       ├── derivative.py
    │       ├── fourier_pattern.py
    │       ├── fractal_texture.py
    │       ├── gradient_based.py
    │       ├── histogram_equalization.py
    │       ├── internal_distance.py
    │       ├── orbit_trap_circle.py
    │       ├── palam_c_z.py
    │       ├── phase_symmetry.py
    │       ├── quantum_entanglement.py
    │       └── solid_color.py
    ├── document/
    ├── fractal/
    │   ├── render.py
    │   └── fractal_types/
    │       ├── julia.py
    │       └── mandelbrot.py
    └── ui/
        ├── canvas.py
        ├── main_window.py
        ├── parameter_panel.py
        ├── status_bar.py
        └── zoom_function/
            ├── cursor_manager.py
            ├── debug_logger.py
            ├── enums.py
            ├── event_handler_core.py
            ├── event_handlers_private.py
            ├── event_handlers_utils.py
            ├── event_validator.py
            ├── rect_manager.py
            ├── zoom_selector.py
            └── zoom_state_handler.py
