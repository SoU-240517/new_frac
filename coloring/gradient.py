import numpy as np

def compute_gradient(shape):
    print("====== グラデーション計算開始:（def compute_gradient）")  # ← debug print★
    x, y = np.indices(shape)
    normalized_distance = np.sqrt((x - shape[0]/2)**2 + (y - shape[1]/2)**2) / np.sqrt((shape[0]/2)**2 + (shape[1]/2)**2)
    return normalized_distance
