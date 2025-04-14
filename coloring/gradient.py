import numpy as np
from ui.zoom_function.debug_logger import DebugLogger
from ui.zoom_function.enums import LogLevel

def compute_gradient(shape, logger: DebugLogger):
    """ グラデーションを計算 """
    logger.log(LogLevel.DEBUG, "グラデーション計算開始")
    x, y = np.indices(shape)
    normalized_distance = np.sqrt((x - shape[0]/2)**2 + (y - shape[1]/2)**2) / np.sqrt((shape[0]/2)**2 + (shape[1]/2)**2)
    return normalized_distance
