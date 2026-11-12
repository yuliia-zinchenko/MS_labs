import numpy as np

BLOCK = 8
LEVEL_SHIFT = 128.0


def dct_matrix(n: int = BLOCK) -> np.ndarray:
    k = np.arange(n)[:, None]
    i = np.arange(n)[None, :]
    matrix = np.sqrt(2 / n) * np.cos((2 * i + 1) * k * np.pi / (2 * n))
    matrix[0] /= np.sqrt(2)
    return matrix


C = dct_matrix()


def split_blocks(image: np.ndarray) -> np.ndarray:
    h, w = image.shape
    return image.reshape(h // BLOCK, BLOCK, w // BLOCK, BLOCK).swapaxes(1, 2)


def merge_blocks(blocks: np.ndarray) -> np.ndarray:
    rows, cols = blocks.shape[:2]
    return blocks.swapaxes(1, 2).reshape(rows * BLOCK, cols * BLOCK)


def forward(image: np.ndarray) -> np.ndarray:
    return merge_blocks(C @ split_blocks(image - LEVEL_SHIFT) @ C.T)


def inverse(coeffs: np.ndarray) -> np.ndarray:
    return merge_blocks(C.T @ split_blocks(coeffs) @ C) + LEVEL_SHIFT
