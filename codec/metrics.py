import math

import numpy as np

PEAK = 255.0


def to_uint8(image: np.ndarray) -> np.ndarray:
    return np.clip(np.rint(image), 0, 255).astype(np.uint8)


def mse(a: np.ndarray, b: np.ndarray) -> float:
    return float(np.mean((a.astype(float) - b.astype(float)) ** 2))


def psnr(a: np.ndarray, b: np.ndarray) -> float:
    error = mse(a, b)
    return math.inf if error == 0 else 10 * math.log10(PEAK ** 2 / error)
