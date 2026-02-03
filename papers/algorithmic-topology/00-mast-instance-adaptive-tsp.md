# MASTm: Instance-Adaptive Spectral Decomposition for Large-Scale TSP

**Authors:** Ilya Selyutin, Nikolai Kovalev
**Affiliation:** Independent Research (Fractal27 Project)
**Version:** v6.6 (Jan 2026)
**Repository:** github.com/fractal27/mast

---

## Abstract

We present MASTm (Multi-scale Adaptive Spectral TSP meta-solver), a meta-solver for the Travelling Salesman Problem that replaces fixed algorithmic strategies with instance-adaptive routing. MASTm operates through a six-stage pipeline: (1) a 7D topological fingerprint classifies each instance, (2) a lightweight router selects a decomposition strategy, (3) spectral decomposition partitions the instance into tractable subproblems, (4) parallel Iterated Local Search with deterministic restarts solves each partition, (5) a stitching phase reconnects subproblem solutions via boundary optimization, and (6) a V-cycle multigrid refinement followed by EAX crossover polishes the global tour. Key innovations include oracle k-NN remapping for sub-quadratic memory, deterministic ILS with adaptive perturbation, and budget-adaptive V-cycle scheduling. On TSPLIB benchmarks, MASTm achieves a median gap of 0.39% across 13 instances ranging from N=52 to N=15112, with memory consumption of O(N*k) instead of O(N^2), enabling runs at N=100K within 230MB.

**Keywords:** Travelling Salesman Problem, spectral decomposition, instance-adaptive algorithm, metaheuristic, fingerprint-based routing

---

## 1. Introduction

The Travelling Salesman Problem remains the canonical NP-hard combinatorial optimization benchmark. Despite decades of progress in exact solvers (Concorde), local search heuristics (LKH, LK-DLB), and evolutionary methods (EAX), a persistent gap exists between algorithmic capability and practical deployment: no single strategy dominates across all instance topologies.

Clustered instances with well-separated groups of cities respond well to decomposition followed by inter-cluster stitching. Uniform random instances resist decomposition but yield to global perturbation methods. Structured instances with elongated or grid-like geometry require geometry-aware partitioning. A fixed pipeline necessarily underperforms on at least one of these classes.

**Our contributions:**
1. A 7-dimensional topological fingerprint that characterizes instance structure in O(N log N) time
2. A trained router that maps fingerprints to decomposition strategies (Clustered, Uniform, Structured)
3. An oracle k-NN remapping scheme that reduces memory from O(N^2) to O(N*k)
4. A V-cycle multigrid refinement with adaptive budget allocation across resolution levels

**Central thesis:** Instance-adaptive solvers that invest polynomial overhead in fingerprinting consistently outperform fixed-strategy solvers across diverse instance distributions.

---

## 2. Background

### 2.1 Spectral Decomposition for TSP
Spectral methods partition a graph by computing the Fiedler vector (second-smallest eigenvector of the graph Laplacian) and recursively bisecting. Applied to TSP, this produces geographically coherent subproblems amenable to independent optimization.

### 2.2 Lin-Kernighan with Don't-Look Bits (LK-DLB)
The LK heuristic performs variable-depth edge exchanges guided by improvement criteria. Don't-Look Bits suppress unpromising neighborhoods, yielding near-linear average-case behavior per improvement step.

### 2.3 Edge Assembly Crossover (EAX)
EAX constructs offspring by identifying AB-cycles between two parent tours and selectively recombining edges. It is the strongest known crossover operator for TSP, achieving near-optimal results on instances up to N=100K.

### 2.4 Iterated Local Search (ILS)
ILS alternates between local optimization (e.g., LK-DLB) and perturbation (double-bridge moves). Deterministic restart schedules prevent cycling and ensure coverage of the solution landscape.

---

## 3. Method

### 3.1 Architecture Overview

```
Input instance (N cities)
 |
 v
[1] Fingerprint (7D feature vector)
 |
 v
[2] Router (classify: Clustered / Uniform / Structured)
 |
 v
[3] Spectral Decomposition (adaptive partition tree)
 |
 v
[4] Parallel ILS (deterministic LK-DLB per partition)
 |
 v
[5] Stitch (boundary re-optimization)
 |
 v
[6] V-cycle Refinement + EAX Polish
 |
 v
Output tour
```

### 3.2 7D Topological Fingerprint

The fingerprint vector f(I) for instance I is computed as:

| Dimension | Feature | Computation | Complexity |
|-----------|---------|-------------|------------|
| f1 | cv_nn_dist | Coefficient of variation of nearest-neighbor distances | O(N log N) |
| f2 | spectral_gap | Gap between 2nd and 3rd eigenvalues of k-NN graph Laplacian | O(N*k) |
| f3 | modularity | Newman-Girvan modularity of k-NN graph | O(N*k) |
| f4 | aspect_ratio | Ratio of PCA eigenvalues (lambda_1 / lambda_2) | O(N) |
| f5 | density_cv | Coefficient of variation of local density estimates | O(N log N) |
| f6 | mean_nn_dist | Mean nearest-neighbor distance (normalized) | O(N log N) |
| f7 | alpha_edge_ratio | Ratio of alpha-shape perimeter edges to total edges | O(N log N) |

Total fingerprinting cost: O(N*k) where k << N (typically k=10-20).

### 3.3 Router Classification

The router applies trained decision boundaries on the fingerprint:

| Class | Condition | Strategy |
|-------|-----------|----------|
| **Clustered** | cv_nn_dist > 0.8 | Deep spectral decomposition, small partitions |
| **Uniform** | cv_nn_dist < 0.4 | Shallow decomposition, large partitions, strong ILS |
| **Structured** | cv_nn_dist < 0.3 AND aspect_ratio > 1.5 | Geometry-aware strip partitioning |

Misclassification penalty is bounded: all strategies produce valid tours, and V-cycle refinement compensates for suboptimal decomposition.

### 3.4 Spectral Decomposition

For Clustered instances, recursive spectral bisection continues until partition size falls below threshold T_min (typically 200-500 cities). For Uniform instances, a single level of k-way partitioning is used. For Structured instances, axis-aligned strip decomposition replaces spectral methods.

### 3.5 Oracle k-NN Remapping

Standard TSP solvers require O(N^2) distance storage. MASTm constructs a k-NN graph (k=10) using a KD-tree in O(N log N) time. During LK-DLB moves, if an edge candidate is not in the k-NN set, an oracle lookup computes the distance on demand. This reduces memory from O(N^2) to O(N*k), enabling N=100K within 230MB.

### 3.6 V-Cycle Multigrid Refinement

After stitching, MASTm applies a V-cycle inspired by multigrid methods:
1. **Restriction:** coarsen the tour by merging nearby cities
2. **Solve:** optimize the coarsened tour
3. **Prolongation:** project improvements back to the fine level
4. **Smooth:** apply LK-DLB at the fine level

Budget allocation across V-cycle levels is adaptive: levels with higher improvement rates receive proportionally more ILS iterations.

### 3.7 EAX Polish

The final stage applies EAX crossover between the V-cycle output and independently generated tours. This captures non-local improvements that sequential local search cannot find. EAX runs for a fixed number of generations (typically 50-100) or until stagnation.

---

## 4. Results

### 4.1 TSPLIB Benchmark Results (v6.6, single-thread, 60s budget)

| Instance | N | Optimal | MASTm Tour | Gap (%) | Class |
|----------|---|---------|-----------|---------|-------|
| berlin52 | 52 | 7,542 | 7,544 | 0.03 | Clustered |
| kroA100 | 100 | 21,282 | 21,294 | 0.06 | Clustered |
| ch150 | 150 | 6,528 | 6,541 | 0.20 | Uniform |
| kroA200 | 200 | 29,368 | 29,412 | 0.15 | Clustered |
| a280 | 280 | 2,579 | 2,589 | 0.39 | Structured |
| lin318 | 318 | 42,029 | 42,113 | 0.20 | Structured |
| pcb442 | 442 | 50,778 | 50,982 | 0.40 | Uniform |
| rat783 | 783 | 8,806 | 8,862 | 0.64 | Uniform |
| fl3795 | 3,795 | 28,772 | 28,835 | 0.22 | Clustered |
| fnl4461 | 4,461 | 182,566 | 185,815 | 1.78 | Uniform |
| rl5934 | 5,934 | 556,045 | 561,210 | 0.93 | Structured |
| usa13509 | 13,509 | 19,982,859 | 20,290,586 | 1.54 | Clustered |
| d15112 | 15,112 | 1,573,084 | 1,628,802 | 3.54 | Uniform |

*All results on a single core. Time budget: 60 seconds (small instances), 300 seconds (N > 5000).*

**Summary:**
- Sub-1% gap on 8/13 instances (including all N < 1000)
- **Median gap: 0.39%** (over all 13 instances)
- **Mean gap: 0.78%** across small-to-medium instances (N < 5000)
- **3.54%** on d15112 represents the current ceiling for single-thread + time-bounded execution

**Note on LKH-3:** LKH-3 (Helsgaun, 2017) is widely regarded as the current state-of-the-art inexact TSP solver, routinely achieving near-optimal results on TSPLIB instances with longer time budgets. A direct time-controlled comparison between MASTm and LKH-3 under identical hardware and budget constraints is pending and constitutes important future work. The results above should not be interpreted as claiming competitive parity with LKH-3; rather, they demonstrate the effectiveness of instance-adaptive routing within the MASTm pipeline.

### 4.2 Memory Profile

| N | Full distance matrix | MASTm (k=10) | Ratio |
|---|---------------------|-------------|-------|
| 1,000 | 8 MB | 0.08 MB | 100x |
| 10,000 | 800 MB | 0.8 MB | 1000x |
| 100,000 | 80 GB | 8 MB (~230 MB total) | 10000x |

---

## 5. Ablation Study

### 5.1 Impact of Router

| Configuration | Median Gap (%) | Notes |
|---------------|---------------|-------|
| Full MASTm (adaptive routing) | 0.39 | Baseline |
| Fixed Clustered strategy | 0.72 | Degrades on Uniform instances |
| Fixed Uniform strategy | 0.95 | Degrades on Clustered instances |
| Random strategy selection | 0.81 | High variance |

Router contributes approximately 40-50% of MASTm's advantage over fixed strategies.

### 5.2 Impact of V-Cycle

| Configuration | Median Gap (%) |
|---------------|---------------|
| With V-cycle | 0.39 |
| Without V-cycle (ILS + stitch only) | 0.88 |

V-cycle contributes the largest single improvement, reducing gap by approximately 50%.

### 5.3 Impact of EAX Polish

| Configuration | Median Gap (%) |
|---------------|---------------|
| With EAX polish | 0.39 |
| Without EAX (V-cycle only) | 0.62 |

EAX polish contributes approximately 0.2 percentage points of median gap reduction.

---

## 6. Discussion

### 6.1 Strengths and Limitations

MASTm demonstrates that a polynomial-overhead fingerprinting step enables consistent performance across diverse instance topologies. The approach is practical: fingerprinting takes less than 1% of total runtime, yet determines the decomposition strategy that accounts for most of the performance variation.

Current limitations include:
1. **Large uniform instances** (d15112, 3.54% gap) remain challenging because spectral decomposition provides limited benefit when no natural clusters exist
2. **Time budget sensitivity:** at very short budgets (< 10s), the overhead of fingerprinting and V-cycle setup is non-negligible
3. **Router granularity:** three classes may be insufficient; finer-grained routing (e.g., 7-10 strategies) could improve results
4. **Benchmark scope:** All results are on TSPLIB instances only; performance on random, adversarial, or real-world logistics instances has not been evaluated
5. **No direct comparison with LKH-3 at equal time budgets:** While we note LKH-3 as state-of-the-art (Section 4.1), a controlled head-to-head comparison under identical hardware and time constraints is pending
6. **Fingerprint features are hand-selected:** The 7D feature vector was designed by domain expertise, not learned from data; automated feature selection or learned representations may yield better routing accuracy

### 6.2 Relation to Algorithm Selection

MASTm can be viewed as an instance of the Algorithm Selection Problem (Rice, 1976), where the feature space is the 7D fingerprint and the algorithm portfolio is {Clustered, Uniform, Structured}. The algorithm selection literature has produced increasingly sophisticated portfolio methods: SATzilla (Leyton-Brown et al., 2003; Xu et al., 2008) pioneered instance-feature-based solver selection for SAT; AutoFolio (Lindauer et al., 2015) introduced automated configuration of the selector itself; and Kerschke et al. (2019) provide a comprehensive survey of feature-based algorithm selection across combinatorial domains.

MASTm differs from these portfolio approaches in a key respect: it does not merely select among independent solvers. Instead, the router parameterizes a shared pipeline — the same decomposition-ILS-stitch-refine architecture is used for all classes, but with class-dependent parameters (partition depth, ILS budget allocation, stitching strategy). This integration of selection with hierarchical decomposition and V-cycle optimization means that even a misclassified instance receives a reasonable solution, since all strategies share the same refinement stages.

### 6.3 Scalability

The O(N*k) memory profile makes MASTm viable for instances up to N=500K on commodity hardware (16GB RAM). Beyond this, distributed decomposition with message-passing stitching would be required.

---

## References

- Appleby, D., Bixby, R., Chvatal, V., & Cook, W. (2006). The Traveling Salesman Problem: A Computational Study. Princeton University Press.
- Nagata, Y., & Kobayashi, S. (2013). A powerful genetic algorithm using edge assembly crossover for the TSP. INFORMS J. Computing.
- Helsgaun, K. (2009). General k-opt submoves for the Lin-Kernighan TSP heuristic. Mathematical Programming Computation.
- Rice, J. R. (1976). The algorithm selection problem. Advances in Computers, 15, 65-118.
- Leyton-Brown, K., Nudelman, E., Andrew, G., McFadden, J., & Shoham, Y. (2003). A portfolio approach to algorithm selection. IJCAI.
- Xu, L., Hutter, F., Hoos, H. H., & Leyton-Brown, K. (2008). SATzilla: Portfolio-based algorithm selection for SAT. J. Artificial Intelligence Research, 32, 565-606.
- Lindauer, M., Hoos, H. H., Hutter, F., & Schaub, T. (2015). AutoFolio: An automatically configured algorithm selector. J. Artificial Intelligence Research, 53, 745-778.
- Kerschke, P., Hoos, H. H., Neumann, F., & Trautmann, H. (2019). Automated algorithm selection: Survey and perspectives. Evolutionary Computation, 27(1), 3-45.
- Helsgaun, K. (2017). An extension of the Lin-Kernighan-Helsgaun TSP solver for constrained traveling salesman and vehicle routing problems. Technical report, Roskilde University.
- Newman, M. E. J. (2006). Modularity and community structure in networks. PNAS.
- Fiedler, M. (1973). Algebraic connectivity of graphs. Czech. Math. J.

---

## Appendix

- Code: github.com/fractal27/mast (v6.6)
- Benchmarks: TSPLIB (http://comopt.ifi.uni-heidelberg.de/software/TSPLIB95/)
- Fingerprint data: available at github.com/fractal27/mast/data/fingerprints/
- Full ablation data: github.com/fractal27/mast/experiments/
