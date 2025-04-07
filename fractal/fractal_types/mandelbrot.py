import numpy as np

def compute_mandelbrot(Z, Z0, max_iter):
    """ マンデルブロ集合を計算 """
    print('\033[32m'+'compute_mandelbrot:: mandelbrot.py'+'\033[0m')
    shape = Z.shape
    iterations = np.zeros(shape, dtype=int)
    z = np.full(shape, Z0, dtype=complex)
    c = Z.copy()
    mask = np.abs(z) <= 2.0
    z_vals = np.zeros(shape, dtype=complex)

    for i in range(max_iter):
        mask = np.abs(z) <= 2.0
        if not np.any(mask):
            break
        z[mask] = z[mask]**2 + c[mask]
        iterations[mask & (np.abs(z) > 2.0)] = i + 1
        z_vals = z.copy()
    iterations[mask] = 0
    return {
        'iterations': iterations,
        'mask': mask,
        'z_vals': z_vals
    }
