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
    │   ├── __init__.py
    │   ├── coloring.md
    │   ├── plugin_loader.py
    │   ├── coloring/
    │   │   ├── divergent/
    │   │   │   ├── angle/
    │   │   │   │   ├── __init__.py
    │   │   │   │   └── angle.py
    │   │   │   ├── distance/
    │   │   │   │   ├── __init__.py
    │   │   │   │   └── distance.py
    │   │   │   ├── histogram/
    │   │   │   │   ├── __init__.py
    │   │   │   │   └── histogram.py
    │   │   │   ├── linear/
    │   │   │   │   ├── __init__.py
    │   │   │   │   └── linear.py
    │   │   │   ├── logarithmic/
    │   │   │   │   ├── __init__.py
    │   │   │   │   └── logarithmic.py
    │   │   │   ├── orbit_trap/
    │   │   │   │   ├── __init__.py
    │   │   │   │   └── orbit_trap.py
    │   │   │   ├── potential/
    │   │   │   │   ├── __init__.py
    │   │   │   │   └── potential.py
    │   │   │   └── smoothing/
    │   │   │       ├── __init__.py
    │   │   │       └── smoothing.py
    │   │   └── non_divergent/
    │   │       ├── chaotic_orbit/
    │   │       │   ├── __init__.py
    │   │       │   └── chaotic_orbit.py
    │   │       ├── complex_potential/
    │   │       │   ├── __init__.py
    │   │       │   └── complex_potential.py
    │   │       ├── convergence_speed/
    │   │       │   ├── __init__.py
    │   │       │   └── convergence_speed.py
    │   │       ├── derivative/
    │   │       │   ├── __init__.py
    │   │       │   └── derivative.py
    │   │       ├── fourier_pattern/
    │   │       │   ├── __init__.py
    │   │       │   └── fourier_pattern.py
    │   │       ├── fractal_texture/
    │   │       │   ├── __init__.py
    │   │       │   └── fractal_texture.py
    │   │       ├── gradient_based/
    │   │       │   ├── __init__.py
    │   │       │   └── gradient_based.py
    │   │       ├── histogram_equalization/
    │   │       │   ├── __init__.py
    │   │       │   └── histogram_equalization.py
    │   │       ├── internal_distance/
    │   │       │   ├── __init__.py
    │   │       │   └── internal_distance.py
    │   │       ├── orbit_trap_circle/
    │   │       │   ├── __init__.py
    │   │       │   └── orbit_trap_circle.py
    │   │       ├── palam_c_z/
    │   │       │   ├── __init__.py
    │   │       │   └── palam_c_z.py
    │   │       ├── phase_symmetry/
    │   │       │   ├── __init__.py
    │   │       │   └── phase_symmetry.py
    │   │       ├── quantum_entanglement/
    │   │       │   ├── __init__.py
    │   │       │   └── quantum_entanglement.py
    │   │       └── solid_color/
    │   │           ├── __init__.py
    │   │           └── solid_color.py
    │   └── fractal_types/
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
