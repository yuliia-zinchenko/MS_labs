from dataclasses import dataclass

import numpy as np
from PIL import Image

from . import dct, haar
from .metrics import psnr, to_uint8


def load_grayscale(path: str) -> np.ndarray:
    with Image.open(path) as image:
        return np.asarray(image.convert("L"), dtype=np.uint8)


def pad_to_multiple(image: np.ndarray, multiple: int) -> np.ndarray:
    h, w = image.shape
    return np.pad(image, ((0, -h % multiple), (0, -w % multiple)), mode="edge")


def keep_largest(coeffs: np.ndarray, fraction: float) -> np.ndarray:
    count = int(round(coeffs.size * fraction))
    if count >= coeffs.size:
        return coeffs.copy()
    if count <= 0:
        return np.zeros_like(coeffs)
    magnitude = np.abs(coeffs)
    flat = magnitude.ravel()
    threshold = np.partition(flat, flat.size - count)[flat.size - count]
    return np.where(magnitude >= threshold, coeffs, 0.0)


@dataclass
class Result:
    name: str
    image: np.ndarray
    kept: int
    total: int
    psnr: float

    @property
    def fraction(self) -> float:
        return self.kept / self.total

    @property
    def ratio(self) -> float:
        return self.total / self.kept if self.kept else float("inf")


class Codec:

    def __init__(self, image: np.ndarray, levels: int = 3):
        self.original = image
        self.levels = levels
        padded = pad_to_multiple(image, max(dct.BLOCK, 2 ** levels)).astype(float)
        self.dct_coeffs = dct.forward(padded)
        self.dwt_coeffs = haar.forward(padded, levels)

    def _result(self, name: str, coeffs: np.ndarray, restored: np.ndarray) -> Result:
        h, w = self.original.shape
        image = to_uint8(restored[:h, :w])
        return Result(name, image, int(np.count_nonzero(coeffs)), coeffs.size,
                      psnr(self.original, image))

    def dct(self, fraction: float) -> Result:
        coeffs = keep_largest(self.dct_coeffs, fraction)
        return self._result("DCT", coeffs, dct.inverse(coeffs))

    def dwt(self, fraction: float) -> Result:
        coeffs = keep_largest(self.dwt_coeffs, fraction)
        return self._result("DWT", coeffs, haar.inverse(coeffs, self.levels))
