import numpy as np

S = 1 / np.sqrt(2)


def analyze_rows(x: np.ndarray) -> np.ndarray:
    even, odd = x[:, 0::2], x[:, 1::2]
    return np.hstack(((even + odd) * S, (even - odd) * S))


def synthesize_rows(x: np.ndarray) -> np.ndarray:
    half = x.shape[1] // 2
    low, high = x[:, :half], x[:, half:]
    out = np.empty_like(x)
    out[:, 0::2] = (low + high) * S
    out[:, 1::2] = (low - high) * S
    return out


def forward_2d(x: np.ndarray) -> np.ndarray:
    return analyze_rows(analyze_rows(x).T).T


def inverse_2d(x: np.ndarray) -> np.ndarray:
    return synthesize_rows(synthesize_rows(x.T).T)


def max_levels(shape: tuple[int, int]) -> int:
    levels = 0
    h, w = shape
    while h % 2 == 0 and w % 2 == 0 and min(h, w) > 1:
        h, w = h // 2, w // 2
        levels += 1
    return levels


def forward(image: np.ndarray, levels: int) -> np.ndarray:
    out = image.astype(float)
    h, w = out.shape
    for _ in range(levels):
        out[:h, :w] = forward_2d(out[:h, :w])
        h, w = h // 2, w // 2
    return out


def inverse(coeffs: np.ndarray, levels: int) -> np.ndarray:
    out = coeffs.astype(float)
    h, w = (size >> (levels - 1) for size in out.shape)
    for _ in range(levels):
        out[:h, :w] = inverse_2d(out[:h, :w])
        h, w = h * 2, w * 2
    return out
