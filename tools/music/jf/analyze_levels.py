import numpy as np
import pyloudnorm as pyln
from .dsp import SR


def active_lufs(y, sr=SR):
    """loudness of a stem only over the 400 ms blocks where it's actually playing (within 30 dB of its loudest)"""
    w = int(0.4 * sr); fr = np.sqrt(np.mean(y[:len(y) // w * w].mean(1).reshape(-1, w) ** 2, 1))
    act = np.flatnonzero(fr > fr.max() * 0.03)
    if len(act) < 3: return None
    seg = np.concatenate([y[i * w:(i + 1) * w] for i in act])
    return pyln.Meter(sr, block_size=0.4).integrated_loudness(seg)
