import numpy as np

def compute_julia(Z, C, max_iter):
    """ ジュリア集合を計算 """
    print("compute_julia:: FILE→ julia.py")
    shape = Z.shape
    iterations = np.zeros(shape, dtype=int)
    z = Z.copy()
    # 初期マスク：絶対値2以下の点
    mask = np.abs(z) <= 2.0
    z_vals = np.zeros(shape, dtype=complex)

    for i in range(max_iter):
        mask = np.abs(z) <= 2.0
        if not np.any(mask):
            break
        z[mask] = z[mask]**2 + C
        iterations[mask & (np.abs(z) > 2.0)] = i + 1
        z_vals = z.copy()
    iterations[mask] = 0
    return {
        'iterations': iterations,
        'mask': mask,
        'z_vals': z_vals
    }
