# MASTm: Multi-scale Adaptive Spectral TSP meta-solver

## A coordinate-first TSP meta-solver

MASTm is a Travelling Salesman Problem solver that uses instance fingerprinting
to adaptively select optimization strategy. It scales to N=200K+ cities using
only ~230 MB RAM by never materializing the N x N distance matrix (which would
require 80 GB at N=100K).

**Authors:** Ilya Selyutin, Nikolai Kovalev

---

### Quick Start (3 commands)

```bash
pip install -r requirements.txt

# Set PYTHONPATH to the package root so `src.core.*` imports resolve
PYTHONPATH=$(pwd) python3 scripts/run_benchmark_v6.py \
    --instances fl3795 --budget 120 --runs 1

# Expected output (120s budget, single run):
#   fl3795 (N=3795, optimal=28772, budget=120s, 1 runs)
#   run 1: length=28885, gap=0.39%, time=120s
```

**Important.** The benchmark script loads `.tsp` files by instance name from a
directory defined in `TSP_DIR` (line 74 of `run_benchmark_v6.py`). Before
running, update that path to point to your local `benchmarks/` directory:

```python
# In scripts/run_benchmark_v6.py, change:
TSP_DIR = Path('/path/to/your/benchmarks')
# To:
TSP_DIR = Path(__file__).resolve().parent.parent / 'benchmarks'
```

**Note on the fingerprint module.** The solver imports
`src.core.fingerprint` (instance fingerprinting and strategy routing).
This module is included in the distribution at `src/core/fingerprint.py`.

---

### What is MASTm?

MASTm treats TSP not as a single optimization problem but as a family of
structurally distinct problems. Before solving, it computes a topological
fingerprint of the instance -- measuring density uniformity (cv_nn_dist),
spectral gap (decomposability), Newman modularity (clusterability), and
aspect ratio. A strategy router then selects:

- Whether to use hierarchical decomposition or solve directly
- Spectral vs. spatial decomposition mode
- Leaf budget allocation, V-cycle intensity, LK search depth
- Whether to engage EAX crossover in the polish phase

This instance-adaptive routing yields 15-30% gap improvement over any
single fixed strategy.

**Key properties:**

| Property          | Value                                    |
|-------------------|------------------------------------------|
| Memory at N=100K  | ~230 MB (coords + k-NN graph + tour)     |
| Memory naive      | ~80 GB (full distance matrix)            |
| Parallelism       | multiprocessing (fork), up to 12 workers |
| Local search      | Numba JIT: 2-opt, 3-opt, or-opt, LK-DLB |
| Crossover         | EAX (Edge Assembly Crossover) for N>5K   |
| Decomposition     | Recursive spectral / spatial (adaptive)  |

---

### Key Results

Best gaps on TSPLIB instances (120s budget, best of 3 runs, M3 Max):

| Instance | N      | Optimal   | Best Gap % | Mean Gap % |
|----------|--------|-----------|------------|------------|
| berlin52 |     52 |     7,542 |      0.031 |      0.031 |
| kroA100  |    100 |    21,282 |      0.016 |      0.016 |
| ch150    |    150 |     6,528 |      0.044 |      0.044 |
| pcb442   |    442 |    50,778 |      0.27  |      0.49  |
| dsj1000  |  1,000 | 18,659,688|     0.16  |      0.38  |
| pcb3038  |  3,038 |   137,694 |      1.18  |      1.27  |
| fl3795   |  3,795 |    28,772 |      0.39  |      1.22  |
| fnl4461  |  4,461 |   182,566 |      1.78  |      2.05  |
| rl5915   |  5,915 |   565,530 |      1.20  |      1.56  |
| pla7397  |  7,397 | 23,260,728|     2.21  |      2.52  |
| d15112   | 15,112 | 1,573,084 |      3.54  |      3.64  |

Extended runs with 300s budget and parameter tuning achieve fl3795 0.22%
and rl5915 1.20%.

---

### Architecture (6-phase pipeline)

```
Input: coords[N, 2]
         |
         v
  Phase 0: DistanceOracle          ~2% time
  KDTree k-NN (k=20), sparse Laplacian
         |
         v
  Phase 0a: Fingerprint + Route    ~1% time
  cv_nn_dist, spectral_gap, modularity -> SolverConfig
         |
         v
  Phase 1: Recursive Decompose     ~3% time
  Spectral bisection / quadrisection -> leaf nodes (N<=1500)
         |
         v
  Phase 2: Parallel Leaf Optimize  ~50% time
  Per-leaf: multi-start NN -> 2-opt -> or-opt/3-opt -> ILS (DB+LK)
  12 workers via multiprocessing (fork)
         |
         v
  Phase 3: Bottom-up Stitch        ~10% time
  k-NN cross-edges -> meta-TSP -> boundary polish
  Stitch quality metric guides V-cycle budget
         |
         v
  Phase 4: V-cycle Refinement      ~25% time
  Sliding window (segment_size adaptive), or-opt + 3-opt + LK
  Boundary-focused: stress edges from stitch points
         |
         v
  Phase 5: Global Polish           ~10% time
  Phase A: ILS (double_bridge + LK-DLB), collects diverse tours
  Phase B: EAX population optimize (for N>5K)
         |
         v
Output: {tour, length, phases, time_total}
```

For small instances (N<3000, uniform distribution), the router may skip
decomposition entirely, running direct NN + LK + ILS + EAX.

---

### Running Benchmarks

**Single instance:**

```bash
PYTHONPATH=$(pwd) python3 scripts/run_benchmark_v6.py \
    --instances fl3795 --budget 120 --runs 3
```

**Multiple instances:**

```bash
PYTHONPATH=$(pwd) python3 scripts/run_benchmark_v6.py \
    --instances eil51,kroA100,pcb442,fl3795,rl5915 --budget 120 --runs 3
```

**Full benchmark suite (small + medium + large):**

```bash
PYTHONPATH=$(pwd) python3 scripts/run_benchmark_v6.py --budget 120 --runs 3
```

**Full suite including ultra-large (100K+):**

```bash
PYTHONPATH=$(pwd) python3 scripts/run_benchmark_v6.py --full --budget 300 --runs 1
```

**Fingerprint analysis:**

```bash
PYTHONPATH=$(pwd) python3 scripts/fingerprint_analysis.py --mode fingerprint
```

**Output format.** Results are saved as JSON to the `results/` directory.
Each entry contains per-instance stats: N, optimal value, budget, per-run
gaps, mean/min/std gap, wall-clock times, and phase metadata (stitch_ratio,
V-cycle improvement).

**Verbose mode.** Add `--verbose` to see per-phase progress:

```
[v5] Phase 0: Building DistanceOracle (k=20, adaptive=True)...
[v5] Phase 0a: CLUSTERED strategy (cv_nn=0.891, Q=0.52) -> decompose+spectral
[v5] Phase 1: Spectral decomposition (max_leaf=1200)...
  decomposed: 6 leaves, depth=2, leaf_size=412-832
[v5] Phase 2: Optimizing 6 leaves (12 workers, budget=42s)...
[v5] Phase 3: Stitching 6 leaf tours...
  stitch quality: ratio=0.047, count=12, stress=3.2x
[v5] Phase 4: V-cycle refinement (budget=55s, fraction=75%)...
[v5] Phase 5: Global polish (budget=18s)...
[v5] DONE: length=28885, time=120.0s
```

---

### Included Benchmark Instances

All instances are from TSPLIB. Files are in `benchmarks/` in standard
TSPLIB format (.tsp).

| Instance | N      | Optimal Value | Category |
|----------|--------|---------------|----------|
| eil51    |     51 |           426 | small    |
| berlin52 |     52 |         7,542 | small    |
| kroA100  |    100 |        21,282 | small    |
| ch150    |    150 |         6,528 | small    |
| pcb442   |    442 |        50,778 | small    |
| att532   |    532 |        27,686 | small    |
| fl1400   |  1,400 |        20,127 | medium   |
| fl3795   |  3,795 |        28,772 | medium   |
| fnl4461  |  4,461 |       182,566 | medium   |
| rl5915   |  5,915 |       565,530 | medium   |
| pla7397  |  7,397 |    23,260,728 | large    |
| d15112   | 15,112 |     1,573,084 | large    |

Additional TSPLIB instances (up to pla85900, mona-lisa100K) are supported
if placed in the benchmarks directory. Optimal values are built into the
benchmark script.

---

### Hardware Requirements

**Software:**

- Python 3.10+ (tested on 3.14; 3.10-3.12 also work with Numba)
- NumPy >= 1.24
- SciPy >= 1.10
- Numba >= 0.59
- tsplib95 >= 0.7
- matplotlib >= 3.7 (for fingerprint analysis plots)

**macOS note:** The solver uses `multiprocessing.get_context('fork')` for
parallel leaf optimization. This is the correct context for macOS with
Python 3.8+, where the default changed to `spawn`. No configuration
needed -- it is handled internally.

**Hardware recommendations:**

| Scale        | N         | Cores | RAM   | Time (120s budget) |
|--------------|-----------|-------|-------|--------------------|
| Small        | < 1,000   | 4+    | 4 GB  | < 120s             |
| Medium       | 1K - 10K  | 8+    | 8 GB  | 120s               |
| Large        | 10K - 50K | 8+    | 16 GB | 120-300s           |
| Ultra        | 50K+      | 12+   | 32 GB | 300-600s           |

The solver was developed and benchmarked on MacBook Pro M3 Max (12 P-cores,
48 GB RAM).

---

### Project Structure

```
mast/
|-- README.md                       This file
|-- requirements.txt                Python dependencies
|-- src/
|   |-- __init__.py
|   |-- core/
|       |-- __init__.py
|       |-- distance_oracle.py      KDTree k-NN, sparse Laplacian, on-demand sub-D
|       |-- numba_sparse.py         Numba JIT: dist, NN, 2-opt, 3-opt, or-opt,
|       |                           LK-DLB, double_bridge (~1400 lines)
|       |-- hierarchy.py            Recursive spectral decomposition, stitch,
|       |                           V-cycle refinement (~1600 lines)
|       |-- eax_sparse.py           EAX crossover: AB-cycle + population optimize
|       |                           (~1300 lines)
|       |-- ultra_solver.py         solve_v5() entry point, 6-phase pipeline
|       |-- hybrid_solver.py        Legacy dispatcher (v4/v5 routing)
|-- scripts/
|   |-- run_benchmark_v6.py         Main benchmark runner
|   |-- fingerprint_analysis.py     Instance fingerprint visualization + ablation
|-- benchmarks/
|   |-- eil51.tsp ... d15112.tsp    12 TSPLIB instances
|-- results/
|   |-- v6_benchmark_120s.json      Full benchmark results (120s, 3 runs)
|   |-- v6.6_large_300s.json        Extended run results
|   |-- exp2_spectral_dna.json      Spectral fingerprint data
|   |-- ...                         Historical version results (v3-v6)
```

**Total codebase:** ~6,000 lines of Python (core solver), all Numba JIT
hot paths.

---

### Related Papers

The theoretical foundations of MASTm are described in the companion paper
series located in `../papers/`:

- `algorithmic-topology/` -- Formal topology of TSP solution spaces
  - `00-mast-instance-adaptive-tsp.md` -- MASTm: Instance-Adaptive TSP
  - `01-universal-fingerprint-protocol.md` -- Universal Fingerprint Protocol
  - `02-from-cognitive-coordinates-to-combinatorial-optimization.md`
  - `03-adaptive-routing-theorem.md` -- Formal routing guarantees
  - `04-cross-domain-evidence.md` -- Cross-domain applications

- `formal-mathematics/` -- Formal proofs and category-theoretic framework
- `fractal-c4/` -- Connection to the C4 coordinate system (Z3^3)

---

### License

Research code. Contact the authors for licensing terms.
