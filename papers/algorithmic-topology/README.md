# Algorithmic Topology Papers

Papers connecting C4's navigational algebra to combinatorial optimization through the MASTm (Multi-scale Adaptive Spectral TSP meta-solver) framework.

---

## Papers

| # | File | Title | Focus |
|---|------|-------|-------|
| 0 | [00-mast-instance-adaptive-tsp.md](00-mast-instance-adaptive-tsp.md) | MASTm Instance-Adaptive TSP | Core MASTm formulation as an instance-adaptive TSP solver |
| 1 | [01-universal-fingerprint-protocol.md](01-universal-fingerprint-protocol.md) | Universal Fingerprint Protocol | Instance fingerprinting for adaptive algorithm selection |
| 2 | [02-from-cognitive-coordinates-to-combinatorial-optimization.md](02-from-cognitive-coordinates-to-combinatorial-optimization.md) | From Cognitive Coordinates to Combinatorial Optimization | Bridge paper: how C4's Z3^3 structure informs routing heuristics |
| 3 | [03-adaptive-routing-theorem.md](03-adaptive-routing-theorem.md) | Adaptive Routing Theorem | Formal statement and proof of the adaptive routing principle |
| 4 | [04-cross-domain-evidence.md](04-cross-domain-evidence.md) | Cross-Domain Evidence | Empirical validation across logistics, circuit design, and scheduling |

## Recommended Reading Order

1. **Paper 0** -- Start here. Introduces MASTm and the core TSP formulation.
2. **Paper 2** -- Explains the connection between C4 and combinatorial optimization.
3. **Paper 3** -- The formal adaptive routing theorem.
4. **Paper 1** -- Fingerprinting protocol (technical detail).
5. **Paper 4** -- Empirical evidence and benchmarks.

## Code

A run-ready Python implementation of the MASTm solver is available at [`../../code/mast/`](../../code/mast/) (6K lines, 12 TSPLIB instances, benchmark results).
