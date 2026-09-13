# LPAS proof of concept

 **single-proxy LPAS**
construction (Figure 3) from the paper "LPAS: Lattice-based Proxy
Adaptor Signatures". 


This repository represents a proof-of-concept and it is an optimized code. There are also some simplified
parts implemented as we mentionlater

## Requirements

- Python 3.10+
- `numpy`
- `cryptography`

```bash
pip install numpy cryptography
```

- `numpy`: array/math library, used here for random number generation (`SeedSequence`) and vector arithmetic.
- `cryptography`: general-purpose crypto library, used here only for AES-256-GCM (the SKE part of the scheme).

## Usage

```bash
python3 demo.py
```
runs one full exchange on the toy profile, with fresh randomness and full
step-by-step output. `demo.py` also takes four optional flags, which can
be combined freely:

| Flag | Default | Meaning |
|---|---|---|
| `--profile toy\|paper` | `toy` | Which parameter set to run with (see the table below). |
| `--seed N` | random (OS entropy) | Fixes the RNG so the run (or whole batch) is reproducible. |
| `--trials N` | `1` | Run the exchange N times instead of once. |
| `--verbose True\|False` | `True` | Full step-by-step detail per trial, or just a one-line pass/fail summary per trial. |

A few examples:

```bash
python3 demo.py --profile paper
```
Same single run, but on the paper's actual Table 2 / Appendix E parameters
(real modulus-rounding compression included), instead of the fast toy set.

```bash
python3 demo.py --seed 42
```
Reproducible run: the witness, challenge, blindness, etc. come out
identical every time you run this exact command.

```bash
python3 demo.py --trials 50
```
Stress test: runs the exchange 50 times. Trial 1 prints full detail, the
rest print a one-line pass/fail summary, and a batch summary ("X/N
succeeded", timing min/avg/max) is printed at the end.

```bash
python3 demo.py --profile paper --trials 30
```
Same stress test, on the real parameters.

```bash
python3 demo.py --trials 5 --verbose True
```
Forces every trial to print full detail, not just the first one.

```bash
python3 demo.py --verbose False
```
Forces a concise one-line summary even for a single run, no step-by-step
output at all.

```bash
python3 demo.py --profile paper --trials 100 --verbose False --seed 7
```
A quiet, reproducible 100-trial batch on the real parameters, just the
pass/fail summary for each one plus the final aggregate.

```bash
python3 demo.py --help
```
Lists every flag and its default directly from the CLI.

A couple of details worth knowing about how the flags interact: `--seed`
controls reproducibility for the whole batch, not just one trial, each
trial still gets its own independently-spawned RNG stream (via numpy's
`SeedSequence`), but a given seed always produces the same sequence of
per-trial streams. And `--trials`/`--verbose` are independent of each
other: `--trials 1` (the default) combined with `--verbose False` gives a
single concise pass/fail line instead of the usual walkthrough, handy for
a quick sanity check without the full output.

## Parameter profiles

Two parameter profiles are available (`params.py`, selected via `--profile` /
the `LPAS_PROFILE` env var):

| | `toy` (default) | `paper` |
|---|---|---|
| `n`, `q` | 64, 3329 | 256, 8365057 |
| `k`, `l` | 2, 2 | 4, 4 |
| `ω` (challenge weight) | 20 | 60 |
| compression `ν_b`, `ν_w` | 0, 0 (disabled) | 9, 15 (real) |
| runtime (full exchange) | ~10 ms | ~100 ms |



## Files

| File | Contents |
|---|---|
| `params.py` | Two parameter profiles, `toy` and `paper` (see above). Both are for reading/running this demo, not production use. |
| `ring.py` | `R = Z[x]/(x^n+1)` arithmetic, module vectors/matrices, sampling, modulus rounding. |
| `signature.py` | The underlying signature scheme `Pi` = (KeyGen, Sign, Verify), Figure 2 (Fiat–Shamir with aborts), plus `Rej`, Figure 4. |
| `pke.py` | The MLWE-based PKE of Figure 9 (Appendix C), a simplified Kyber-like scheme. |
| `ske.py` | AES-256-GCM, the paper's stated SKE instantiation. |
| `nizk.py` | **Stub**, not a real proof system |
| `lpas.py` | Figure 3 itself: `Setup, ReqGen, ReqVerify, AdGen, AdVerify, ProxySign, ProxyPreVerify, Adapt, ProxyExt, ReqExt`, and the hard relation `R_A`. |
| `demo.py` | End-to-end run: Buyer/Seller/Proxy simulation with printed steps and assertions. |


## Suggested next steps

- Replace `nizk.py` with a real Fiat-Shamir-compiled Sigma-protocol for statement (7)-(8) (a linear-relation proof over `R_A` combined with an encryption-correctness proof for the PKE/SKE ciphertexts).
- For now, the `nizk.py` file does not implement the full NIZK proofs.
