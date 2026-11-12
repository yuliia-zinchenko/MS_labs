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


class RankedCoefficients:

    def __init__(self, values: np.ndarray):
        self.values = values
        self.magnitude = np.abs(values)
        self.ranked = np.sort(self.magnitude, axis=None)[::-1]

    def keep_largest(self, fraction: float) -> np.ndarray:
        count = int(round(self.values.size * fraction))
        if count >= self.values.size:
            return self.values.copy()
        if count <= 0:
            return np.zeros_like(self.values)
        return np.where(self.magnitude >= self.ranked[count - 1], self.values, 0.0)


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
        self.dct_coeffs = RankedCoefficients(dct.forward(padded))
        self.dwt_coeffs = RankedCoefficients(haar.forward(padded, levels))

    def _result(self, name: str, coeffs: np.ndarray, restored: np.ndarray) -> Result:
        h, w = self.original.shape
        image = to_uint8(restored[:h, :w])
        return Result(name, image, int(np.count_nonzero(coeffs)), coeffs.size,
                      psnr(self.original, image))

    def dct(self, fraction: float) -> Result:
        coeffs = self.dct_coeffs.keep_largest(fraction)
        return self._result("DCT", coeffs, dct.inverse(coeffs))

    def dwt(self, fraction: float) -> Result:
        coeffs = self.dwt_coeffs.keep_largest(fraction)
        return self._result("DWT", coeffs, haar.inverse(coeffs, self.levels))
