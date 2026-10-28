"""Proposed input safeguard for the scalar-roughness FFT formulation.

Research prototype: callers must explicitly use this before creating WindShear.
It does not patch AeoLiS or implement heterogeneous-roughness physics.
"""

import numpy as np


def scalar_fft_roughness(z0, grid_shape):
    """Validate positive real roughness; collapse only an exactly uniform grid.

    Scalars and zero-dimensional arrays are accepted. Other arrays must match
    the terrain shape exactly. No tolerance or averaging hides spatial variation.
    This validates the input representation, not all transfer-function domains.
    """
    values = np.asarray(z0)
    if values.dtype.kind not in "iuf":
        raise ValueError("FFT roughness must contain real numeric values in metres.")
    if values.ndim != 0 and values.shape != tuple(grid_shape):
        raise ValueError("FFT roughness array must match the terrain grid shape.")
    if values.size == 0 or not np.all(np.isfinite(values)) or np.any(values <= 0):
        raise ValueError("FFT roughness must be finite and strictly positive.")
    first = values.flat[0]
    if not np.all(values == first):
        raise NotImplementedError(
            "Spatially varying roughness is unsupported by this scalar FFT "
            "safeguard. Choose a documented flow formulation; no averaging is applied."
        )
    return float(first)
