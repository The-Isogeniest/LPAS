"""
Public-key encryption scheme of Figure 9 (Appendix C): an MLWE-based,
IND-CPA-secure scheme, a simplified variant of CRYSTALS-Kyber.

Simplification: reuses the same ring R_q and module rank as the signature
scheme (params.py) with ternary secrets/errors, instead of standing up a
separate lattice with its own parameters. Encrypts a vector of small
coefficients; in the LPAS protocol this carries a LAMBDA-bit one-time-pad
mask, one bit per coefficient, zero-padded if there's room to spare.
"""
from __future__ import annotations
import numpy as np

import params as P
from ring import Poly, vec_add, vec_sub, matvec, matmat, sample_uniform_vec

TAU = 1             # l_infty bound on all "short" PKE elements (S1, S2, s, e1, e2)
PLAINTEXT_MOD = 2   # message space is {0, 1}, one bit per ring coefficient
DELTA = P.Q // PLAINTEXT_MOD  # LWE scaling factor the message is shifted by


def _sample_short_vec(rng, length):
    # ternary coefficients, used for secrets and error terms
    return [Poly(rng.integers(-TAU, TAU + 1, size=P.N)) for _ in range(length)]


def _sample_short_matrix(rng, rows, cols):
    # a matrix of ternary vectors
    return [_sample_short_vec(rng, cols) for _ in range(rows)]


def keygen(rng: np.random.Generator):
    # build a fresh (public key, secret key) pair
    A1 = [sample_uniform_vec(rng, P.M) for _ in range(P.M)]   # public
    S1 = _sample_short_matrix(rng, P.M, P.M)                  # secret key
    S2 = _sample_short_matrix(rng, P.M, P.M)
    A2 = matmat(S1, A1)
    A2 = [vec_add(row, s2_row) for row, s2_row in zip(A2, S2)]
    pk = (A1, A2)
    sk = S1
    return pk, sk


def encrypt(rng: np.random.Generator, pk, m):
    # encrypt a vector of small (here: 0/1) coefficients under pk
    A1, A2 = pk
    s = _sample_short_vec(rng, P.M)
    e1 = _sample_short_vec(rng, P.M)
    e2 = _sample_short_vec(rng, P.M)
    c1 = [p.modq() for p in vec_add(matvec(A1, s), e1)]
    delta_m = [Poly(DELTA * p.c) for p in m]
    c2 = [p.modq() for p in vec_add(vec_add(matvec(A2, s), e2), delta_m)]
    return (c1, c2)


def decrypt(sk, ct):
    # recover the plaintext vector from a ciphertext
    S1 = sk
    c1, c2 = ct
    t = [p.modq() for p in vec_sub(c2, matvec(S1, c1))]
    out = []
    for p in t:
        bits = np.round(p.c.astype(np.float64) / DELTA).astype(np.int64) % PLAINTEXT_MOD
        out.append(Poly(bits))
    return out


# --------------------------------------------------------------------------
# Bit-string <-> plaintext-vector encoding (one bit per ring coefficient).
# --------------------------------------------------------------------------

def bytes_to_plaintext_vec(data: bytes):
    # turn a byte string into a plaintext vector, zero-padding any unused slots
    total_slots = P.N * P.M
    nbits = len(data) * 8
    assert nbits <= total_slots, "message does not fit in one plaintext vector"
    bits = np.unpackbits(np.frombuffer(data, dtype=np.uint8))
    if nbits < total_slots:
        bits = np.concatenate([bits, np.zeros(total_slots - nbits, dtype=np.uint8)])
    return [Poly(bits[i * P.N:(i + 1) * P.N].astype(np.int64)) for i in range(P.M)]


def plaintext_vec_to_bytes(vec, nbytes: int) -> bytes:
    # inverse of bytes_to_plaintext_vec, reading back only the first nbytes
    bits = np.concatenate([p.c for p in vec]).astype(np.uint8)
    return np.packbits(bits[:nbytes * 8]).tobytes()
