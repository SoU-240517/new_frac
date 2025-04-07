import numpy as np

def compute_gradient(shape):
    """_summary_
    グラデーションを計算
    """
    print('\033[32m'+'compute_gradient:: gradient.py'+'\033[0m')
    x, y = np.indices(shape)
    normalized_distance = np.sqrt((x - shape[0]/2)**2 + (y - shape[1]/2)**2) / np.sqrt((shape[0]/2)**2 + (shape[1]/2)**2)
    return normalized_distance
