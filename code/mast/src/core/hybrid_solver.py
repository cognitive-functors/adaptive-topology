"""
Hybrid Solver: Preskip v4.0/v5.0 — Meta-Solver for TSP.

v5.0: Ultra-Scale (N>3000) — coordinate-first, hierarchical decomposition.
v4.0: Island Swarm (3 острова) + SOC-Perturb + Evolution + Segment Decomp.
v3.3: Numba JIT ускорение + 3-opt + адаптивный pipeline (legacy).

Dispatch:
  solve(D=...) → v4 (D-matrix)
  solve(coords=...) → v5 if N>3000, else v4
"""

from __future__ import annotations

import time
import numpy as np
from numpy.typing import NDArray
from typing import Optional

from .preskip_solver import solve_preskip
from .local_search import two_opt, or_opt
from .numba_accel import (
    HAS_NUMBA, warmup,
    nn_tour_jit, tour_length_jit,
    two_opt_jit, two_opt_nn_jit,
    or_opt_jit, build_neighbor_lists_jit,
    three_opt_pass_jit, three_opt_full_pass_jit,
    double_bridge_jit,
)

# JIT warmup при импорте (1-2 сек один раз)
_WARMED_UP = False


def _ensure_warmup():
    global _WARMED_UP
    if not _WARMED_UP and HAS_NUMBA:
        warmup()
        _WARMED_UP = True


def solve_hybrid(
    distance_matrix: NDArray[np.float64],
    max_depth: int = 4,
    min_cluster_size: int = 5,
    two_opt_iters: int = 50,
    or_opt_iters: int = 20,
    time_budget: Optional[float] = None,
) -> dict:
    """
    Гибридный солвер v2: Preskip + 2-opt + Or-opt.
    Backwards-compatible.
    """
    _ensure_warmup()
    n = distance_matrix.shape[0]
    t_start = time.perf_counter()
    phases = {}

    # Phase 1: Preskip construction
    t1 = time.perf_counter()
    tour_preskip, length_preskip = solve_preskip(
        distance_matrix, max_depth=max_depth, min_cluster_size=min_cluster_size,
    )
    phases['preskip'] = {
        'tour': tour_preskip[:], 'length': length_preskip, 'time': time.perf_counter() - t1,
    }
    current_tour, current_length = tour_preskip, length_preskip

    # Phase 2: 2-opt
    if time_budget and time.perf_counter() - t_start > time_budget:
        return _build_result(current_tour, current_length, phases, t_start)

    adaptive_2opt = min(two_opt_iters, max(10, n // 2))
    t2 = time.perf_counter()
    tour_2opt, length_2opt, iters_2opt = two_opt(
        current_tour, distance_matrix,
        max_iterations=adaptive_2opt, max_no_improve=max(3, adaptive_2opt // 10),
    )
    phases['two_opt'] = {
        'length': length_2opt, 'iterations': iters_2opt,
        'improvement': (current_length - length_2opt) / current_length * 100,
        'time': time.perf_counter() - t2,
    }
    current_tour, current_length = tour_2opt, length_2opt

    # Phase 3: Or-opt
    if time_budget and time.perf_counter() - t_start > time_budget - 0.1:
        return _build_result(current_tour, current_length, phases, t_start)

    t3 = time.perf_counter()
    tour_or, length_or, iters_or = or_opt(current_tour, distance_matrix, max_iterations=or_opt_iters)
    phases['or_opt'] = {
        'length': length_or, 'iterations': iters_or,
        'improvement': (current_length - length_or) / current_length * 100,
        'time': time.perf_counter() - t3,
    }

    return _build_result(tour_or, length_or, phases, t_start)


def solve_v3(
    distance_matrix: NDArray[np.float64],
    max_depth: int = 4,
    min_cluster_size: int = 5,
    population_size: int = 10,
    lk_depth: int = 5,
    lk_candidates: int = 7,
    eax_generations: int = 50,
    ils_iterations: int = 30,
    time_budget: Optional[float] = None,
) -> dict:
    """
    Preskip v3.3 — Full pipeline с Numba JIT ускорением.

    Адаптация по N (с Numba всё стало быстрее!):
      N<100:  aggressive LK + EAX + 3-opt
      N<500:  balanced 2-opt + 3-opt + EAX + MCTS
      N<1000: 2-opt NN JIT + EAX + MCTS (intensive)
      N>=1000: 2-opt NN JIT + MCTS (maximum budget)
    """
    _ensure_warmup()

    from .population import evolve_population

    n = distance_matrix.shape[0]
    t_start = time.perf_counter()
    phases = {}

    # ═══ ADAPTIVE PARAMETERS (v3.3 — Numba-aware) ═══
    # Numba 2-opt+3-opt быстрее Python LK → всегда используем JIT
    use_lk = False
    if n < 100:
        pop_size = min(population_size, 10)
        two_opt_iters = 200
        eax_gens = eax_generations * 2
        mcts_iters = 999999  # Numba быстр → полагаемся на time_budget
    elif n < 500:
        pop_size = min(population_size, 8)
        two_opt_iters = 150
        eax_gens = eax_generations
        mcts_iters = 999999
    elif n < 1000:
        pop_size = min(population_size, 6)
        two_opt_iters = 80
        eax_gens = 40
        mcts_iters = 999999
    else:
        pop_size = min(population_size, 6)
        two_opt_iters = 60
        eax_gens = 30
        mcts_iters = 999999

    def _time_left():
        if time_budget is None:
            return float('inf')
        return time_budget - (time.perf_counter() - t_start)

    # ═══ LEVEL 0: SPECTRAL ANALYSIS ═══
    t0 = time.perf_counter()
    from scipy.sparse.csgraph import laplacian

    spectral_vecs = None
    fiedler = np.zeros(n)
    spectral_gap = 0.0

    if n < 500:
        max_d = np.max(distance_matrix[distance_matrix < np.inf]) + 1e-10
        similarity = max_d - distance_matrix
        np.fill_diagonal(similarity, 0)
        L = laplacian(similarity, normed=False)
        eigenvalues, eigenvectors = np.linalg.eigh(L)
        fiedler = eigenvectors[:, 1] if n > 2 else np.zeros(n)
        spectral_gap = float(eigenvalues[1]) if len(eigenvalues) > 1 else 0
        spectral_vecs = eigenvectors[:, :min(6, eigenvectors.shape[1])]
    else:
        from scipy.sparse import csr_matrix
        from scipy.sparse.linalg import eigsh
        similarity = 1.0 / (1.0 + distance_matrix)
        np.fill_diagonal(similarity, 0)
        L = laplacian(csr_matrix(similarity), normed=False)
        try:
            k_eig = min(6, n - 1)
            eigenvalues, eigenvectors = eigsh(L, k=k_eig, which='SM')
            idx = np.argsort(eigenvalues)
            eigenvalues = eigenvalues[idx]
            eigenvectors = eigenvectors[:, idx]
            fiedler = eigenvectors[:, 1] if eigenvectors.shape[1] > 1 else np.zeros(n)
            spectral_gap = float(eigenvalues[1]) if len(eigenvalues) > 1 else 0
            spectral_vecs = eigenvectors
        except Exception:
            fiedler = np.random.randn(n)

    phases['spectral_analysis'] = {
        'spectral_gap': spectral_gap,
        'time': time.perf_counter() - t0,
    }

    # ═══ LEVEL 1: MULTI-START CONSTRUCTION ═══
    t1 = time.perf_counter()
    initial_tours = []

    # Tour 1: основной Preskip
    tour_main, _ = solve_preskip(
        distance_matrix, max_depth=max_depth, min_cluster_size=min_cluster_size,
    )
    initial_tours.append(tour_main)

    # Tour 2-3: с разной глубиной бисекции
    for depth in [2, 6]:
        if _time_left() < 1:
            break
        t, _ = solve_preskip(
            distance_matrix, max_depth=depth,
            min_cluster_size=max(3, min_cluster_size - 2),
        )
        initial_tours.append(t)

    # Tour 4+: Numba-ускоренный NN с разными стартами
    while len(initial_tours) < pop_size and _time_left() > 0.5:
        start = np.random.randint(n)
        if HAS_NUMBA:
            tour_nn = nn_tour_jit(distance_matrix, start).tolist()
        else:
            tour_nn = _nearest_neighbor(distance_matrix, start)
        initial_tours.append(tour_nn)

    phases['construction'] = {
        'num_tours': len(initial_tours),
        'best_length': min(_tour_length(t, distance_matrix) for t in initial_tours),
        'time': time.perf_counter() - t1,
    }

    # ═══ LEVEL 2: LOCAL SEARCH на каждом туре ═══
    t2 = time.perf_counter()
    improved_tours = []

    # 2-opt JIT (Numba) — работает на ВСЕХ турах, даже для N=3000+
    for tour in initial_tours:
        if _time_left() < 0.5:
            improved_tours.append(tour)
            continue
        tour_2, _, _ = two_opt(
            tour, distance_matrix,
            max_iterations=two_opt_iters, max_no_improve=8,
        )
        improved_tours.append(tour_2)

    # 3-opt JIT pass на каждом туре (быстро с Numba)
    if HAS_NUMBA and _time_left() > 1.0:
        nn_lists = build_neighbor_lists_jit(distance_matrix, min(15, n // 5 + 1))
        for i, tour in enumerate(improved_tours):
            if _time_left() < 0.3:
                break
            tour_arr = np.array(tour, dtype=np.int64)
            # Несколько проходов 3-opt
            for _ in range(3):
                if not three_opt_pass_jit(tour_arr, distance_matrix, nn_lists):
                    break
            improved_tours[i] = tour_arr.tolist()

    # Or-opt на лучшем
    best_idx = int(np.argmin([_tour_length(t, distance_matrix) for t in improved_tours]))
    best_local = improved_tours[best_idx]
    best_local_len = _tour_length(best_local, distance_matrix)

    if _time_left() > 0.5:
        best_local, best_local_len, _ = or_opt(
            best_local, distance_matrix, max_iterations=20,
        )
        improved_tours[best_idx] = best_local

    phases['local_search'] = {
        'method': '2opt+3opt JIT',
        'best_length': best_local_len,
        'num_tours': len(improved_tours),
        'time': time.perf_counter() - t2,
    }

    # ═══ LEVEL 3: EAX POPULATION EVOLUTION ═══
    t3 = time.perf_counter()
    if _time_left() > 2.0 and len(improved_tours) >= 2:
        eax_budget = min(_time_left() * 0.3, 60.0)
        best_eax, len_eax, eax_stats = evolve_population(
            distance_matrix, improved_tours,
            max_generations=eax_gens,
            population_size=min(pop_size, len(improved_tours)),
            max_no_improve=12,
            time_budget=eax_budget,
            eigenvectors=spectral_vecs,
        )
        phases['eax'] = {
            'length': len_eax,
            'generations': eax_stats.get('generations', 0),
            'crossovers': eax_stats.get('crossovers', 0),
            'improvements': eax_stats.get('improvements', 0),
            'time': time.perf_counter() - t3,
        }

        if len_eax < best_local_len and len(best_eax) == n and len(set(best_eax)) == n:
            best_local = best_eax
            best_local_len = len_eax
    else:
        phases['eax'] = {'length': best_local_len, 'skipped': True, 'time': 0}

    # ═══ LEVEL 4: MCTS-GUIDED ILS ═══
    t4 = time.perf_counter()
    best_tour = best_local[:]
    best_length = best_local_len

    if _time_left() > 2.0:
        from .mcts_perturb import mcts_local_search
        mcts_budget = min(_time_left() * 0.85, 300.0)  # До 5 минут для гига
        mcts_tour, mcts_len, mcts_stats = mcts_local_search(
            best_local, distance_matrix,
            max_iterations=mcts_iters,
            num_rollouts=5,
            time_budget=mcts_budget,
            fiedler=fiedler,
        )
        if mcts_len < best_length and len(mcts_tour) == n and len(set(mcts_tour)) == n:
            best_tour = mcts_tour
            best_length = mcts_len

        phases['mcts_ils'] = {
            'length': best_length,
            'iterations': mcts_stats.get('iterations', 0),
            'improvements': mcts_stats.get('improvements', 0),
            'rollouts': mcts_stats.get('rollouts', 0),
            'time': time.perf_counter() - t4,
        }
    else:
        phases['mcts_ils'] = {'length': best_length, 'skipped': True, 'time': 0}

    # ═══ FINAL: 2-opt + 3-opt polish ═══
    if _time_left() > 0.3:
        t5 = time.perf_counter()
        final_tour, final_length, _ = two_opt(
            best_tour, distance_matrix, max_iterations=50, max_no_improve=10,
        )
        # 3-opt polish
        if HAS_NUMBA and _time_left() > 0.2:
            if not hasattr(solve_v3, '_nn_cache') or solve_v3._nn_cache[0] != id(distance_matrix):
                nn_lists = build_neighbor_lists_jit(distance_matrix, min(15, n // 5 + 1))
            else:
                nn_lists = solve_v3._nn_cache[1]
            final_arr = np.array(final_tour, dtype=np.int64)
            for _ in range(5):
                if not three_opt_pass_jit(final_arr, distance_matrix, nn_lists):
                    break
            final_tour = final_arr.tolist()
            final_length = _tour_length(final_tour, distance_matrix)

        if final_length < best_length and len(final_tour) == n and len(set(final_tour)) == n:
            best_tour = final_tour
            best_length = final_length
        phases['final_polish'] = {
            'length': best_length,
            'time': time.perf_counter() - t5,
        }

    # ═══ SAFETY NET: v2 fallback ═══
    v2_result = solve_hybrid(
        distance_matrix, max_depth=max_depth, min_cluster_size=min_cluster_size,
        two_opt_iters=50, or_opt_iters=20,
    )
    if v2_result['length'] < best_length:
        best_tour = v2_result['tour']
        best_length = v2_result['length']
        phases['v2_fallback'] = {'used': True, 'length': best_length}

    return _build_result(best_tour, best_length, phases, t_start)


def solve_v4(
    distance_matrix: NDArray[np.float64],
    max_depth: int = 4,
    min_cluster_size: int = 5,
    time_budget: Optional[float] = None,
) -> dict:
    """
    Preskip v4.0 — Island Swarm Evolutionary Meta-Solver.

    Архитектура:
      Phase 0: Spectral analysis + SOC precompute
      Phase 1: Multi-strategy construction (8-16 tours)
      Phase 2: Local search (2-opt + 3-opt full JIT + or-opt)
      Phase 3: Island Swarm Evolution (3 острова + миграция)
      Phase 4: SOC-MCTS Final Refinement
      Phase 5: Segment decomposition (N>500)
      Safety: compare with v3.3

    Args:
        distance_matrix: NxN матрица расстояний
        time_budget: общий лимит времени (None = автоматический)
    """
    _ensure_warmup()

    from .swarm_engine import IslandSwarm
    from .segment_solver import segment_optimize
    from .soc_perturb import SOCEngine
    from .mcts_perturb import mcts_local_search

    n = distance_matrix.shape[0]
    t_start = time.perf_counter()
    phases = {}

    # Auto time budget
    if time_budget is None:
        if n < 100:
            time_budget = 30.0
        elif n < 500:
            time_budget = 60.0
        elif n < 1000:
            time_budget = 120.0
        else:
            time_budget = max(180.0, n * 0.1)

    def _elapsed():
        return time.perf_counter() - t_start

    def _time_left():
        return time_budget - _elapsed()

    # ═══ ADAPTIVE TIME ALLOCATION ═══
    if n < 100:
        pct = {'analysis': 0.02, 'construction': 0.10, 'local': 0.20,
               'swarm': 0.50, 'refine': 0.18, 'segment': 0.0}
    elif n < 500:
        pct = {'analysis': 0.02, 'construction': 0.08, 'local': 0.15,
               'swarm': 0.50, 'refine': 0.20, 'segment': 0.05}
    elif n < 1000:
        pct = {'analysis': 0.02, 'construction': 0.05, 'local': 0.10,
               'swarm': 0.50, 'refine': 0.25, 'segment': 0.08}
    else:
        pct = {'analysis': 0.02, 'construction': 0.05, 'local': 0.08,
               'swarm': 0.40, 'refine': 0.30, 'segment': 0.15}

    # ═══ PHASE 0: SPECTRAL ANALYSIS + SOC ═══
    t0 = time.perf_counter()
    from scipy.sparse.csgraph import laplacian

    spectral_vecs = None
    fiedler = np.zeros(n)
    spectral_gap = 0.0

    if n < 500:
        max_d = np.max(distance_matrix[distance_matrix < np.inf]) + 1e-10
        similarity = max_d - distance_matrix
        np.fill_diagonal(similarity, 0)
        L = laplacian(similarity, normed=False)
        eigenvalues, eigenvectors = np.linalg.eigh(L)
        fiedler = eigenvectors[:, 1] if n > 2 else np.zeros(n)
        spectral_gap = float(eigenvalues[1]) if len(eigenvalues) > 1 else 0
        spectral_vecs = eigenvectors[:, :min(6, eigenvectors.shape[1])]
    else:
        from scipy.sparse import csr_matrix
        from scipy.sparse.linalg import eigsh
        similarity = 1.0 / (1.0 + distance_matrix)
        np.fill_diagonal(similarity, 0)
        L = laplacian(csr_matrix(similarity), normed=False)
        try:
            k_eig = min(6, n - 1)
            eigenvalues, eigenvectors = eigsh(L, k=k_eig, which='SM')
            idx = np.argsort(eigenvalues)
            eigenvalues = eigenvalues[idx]
            eigenvectors = eigenvectors[:, idx]
            fiedler = eigenvectors[:, 1] if eigenvectors.shape[1] > 1 else np.zeros(n)
            spectral_gap = float(eigenvalues[1]) if len(eigenvalues) > 1 else 0
            spectral_vecs = eigenvectors
        except Exception:
            fiedler = np.random.randn(n)

    # SOC engine precompute
    soc_engine = SOCEngine(distance_matrix)

    phases['spectral_analysis'] = {
        'spectral_gap': spectral_gap,
        'time': time.perf_counter() - t0,
    }

    # ═══ PHASE 1: MULTI-STRATEGY CONSTRUCTION ═══
    budget_construction = time_budget * pct['construction']
    t1 = time.perf_counter()
    initial_tours = []

    # Preskip (3 variants)
    for depth in [max_depth, 2, 6]:
        if time.perf_counter() - t1 > budget_construction:
            break
        try:
            t, _ = solve_preskip(
                distance_matrix, max_depth=depth,
                min_cluster_size=max(3, min_cluster_size - 2),
            )
            initial_tours.append(t)
        except Exception:
            pass

    # NN JIT (разные старты)
    target_pop = 12 if n < 500 else 10 if n < 1000 else 8
    while len(initial_tours) < target_pop and time.perf_counter() - t1 < budget_construction:
        start = np.random.randint(n)
        if HAS_NUMBA:
            tour_nn = nn_tour_jit(distance_matrix, start).tolist()
        else:
            tour_nn = _nearest_neighbor(distance_matrix, start)
        initial_tours.append(tour_nn)

    # Spectral projections
    if spectral_vecs is not None and spectral_vecs.shape[1] > 1:
        for _ in range(2):
            if len(initial_tours) >= target_pop:
                break
            k = min(4, spectral_vecs.shape[1])
            emb = spectral_vecs[:, 1:k]
            direction = np.random.randn(k - 1)
            projection = emb @ direction
            initial_tours.append(list(np.argsort(projection)))

    phases['construction'] = {
        'num_tours': len(initial_tours),
        'best_length': min(_tour_length(t, distance_matrix) for t in initial_tours),
        'time': time.perf_counter() - t1,
    }

    # ═══ PHASE 2: LOCAL SEARCH ═══
    budget_local = time_budget * pct['local']
    t2 = time.perf_counter()
    improved_tours = []

    for tour in initial_tours:
        if time.perf_counter() - t2 > budget_local:
            improved_tours.append(tour)
            continue

        # 2-opt NN JIT
        tour_2, _, _ = two_opt(
            tour, distance_matrix,
            max_iterations=30, max_no_improve=5,
        )
        improved_tours.append(tour_2)

    # 3-opt full JIT на каждом
    if HAS_NUMBA and _time_left() > 1.0:
        nn_lists = build_neighbor_lists_jit(distance_matrix, min(15, n // 5 + 1))
        for i, tour in enumerate(improved_tours):
            if time.perf_counter() - t2 > budget_local:
                break
            tour_arr = np.array(tour, dtype=np.int64)
            for _ in range(3):
                if not three_opt_pass_jit(tour_arr, distance_matrix, nn_lists):
                    break
            # Полный 3-opt pass
            for _ in range(2):
                from .numba_accel import three_opt_full_pass_jit
                if not three_opt_full_pass_jit(tour_arr, distance_matrix, nn_lists):
                    break
            improved_tours[i] = tour_arr.tolist()

    # Or-opt на top-3
    lengths = [_tour_length(t, distance_matrix) for t in improved_tours]
    top3 = np.argsort(lengths)[:3]
    for idx in top3:
        if time.perf_counter() - t2 > budget_local:
            break
        t_or, _, _ = or_opt(improved_tours[idx], distance_matrix, max_iterations=15)
        improved_tours[idx] = t_or

    best_local_idx = int(np.argmin([_tour_length(t, distance_matrix) for t in improved_tours]))
    best_local = improved_tours[best_local_idx]
    best_local_len = _tour_length(best_local, distance_matrix)

    phases['local_search'] = {
        'method': '2opt+3opt_full+or_opt JIT',
        'best_length': best_local_len,
        'num_tours': len(improved_tours),
        'time': time.perf_counter() - t2,
    }

    # ═══ PHASE 3: ISLAND SWARM EVOLUTION ═══
    budget_swarm = time_budget * pct['swarm']
    t3 = time.perf_counter()

    if _time_left() > 3.0 and len(improved_tours) >= 4:
        swarm = IslandSwarm(
            distance_matrix, improved_tours,
            time_budget=min(budget_swarm, _time_left() * 0.6),
            spectral_vecs=spectral_vecs,
            fiedler=fiedler,
            soc_engine=soc_engine,
        )
        swarm_best, swarm_len, swarm_stats = swarm.run()

        phases['swarm_evolution'] = {
            'length': swarm_len,
            'generations': swarm_stats.get('total_generations', 0),
            'migrations': swarm_stats.get('migrations', 0),
            'island1_imp': swarm_stats.get('island1_improvements', 0),
            'island2_imp': swarm_stats.get('island2_improvements', 0),
            'island3_imp': swarm_stats.get('island3_improvements', 0),
            'time': time.perf_counter() - t3,
        }

        if swarm_len < best_local_len and len(swarm_best) == n and len(set(swarm_best)) == n:
            best_local = swarm_best
            best_local_len = swarm_len
    else:
        phases['swarm_evolution'] = {'skipped': True, 'length': best_local_len, 'time': 0}

    # ═══ PHASE 4: SOC-MCTS FINAL REFINEMENT ═══
    budget_refine = time_budget * pct['refine']
    t4 = time.perf_counter()
    best_tour = best_local[:]
    best_length = best_local_len

    if _time_left() > 2.0:
        mcts_budget = min(budget_refine, _time_left() * 0.7)
        mcts_tour, mcts_len, mcts_stats = mcts_local_search(
            best_local, distance_matrix,
            max_iterations=999999,
            num_rollouts=5,
            time_budget=mcts_budget,
            fiedler=fiedler,
            soc_engine=soc_engine,
        )
        if mcts_len < best_length and len(mcts_tour) == n and len(set(mcts_tour)) == n:
            best_tour = mcts_tour
            best_length = mcts_len

        phases['mcts_refine'] = {
            'length': best_length,
            'iterations': mcts_stats.get('iterations', 0),
            'improvements': mcts_stats.get('improvements', 0),
            'time': time.perf_counter() - t4,
        }
    else:
        phases['mcts_refine'] = {'skipped': True, 'length': best_length, 'time': 0}

    # ═══ PHASE 5: SEGMENT DECOMPOSITION ═══
    if n > 500 and pct['segment'] > 0 and _time_left() > 2.0:
        t5 = time.perf_counter()
        seg_budget = min(time_budget * pct['segment'], _time_left() * 0.8)
        seg_size = min(300, max(150, n // 4))
        seg_overlap = seg_size // 5

        seg_tour, seg_len = segment_optimize(
            best_tour, distance_matrix,
            segment_size=seg_size, overlap=seg_overlap,
            time_budget=seg_budget,
        )
        if seg_len < best_length and len(seg_tour) == n and len(set(seg_tour)) == n:
            best_tour = seg_tour
            best_length = seg_len

        phases['segment_decomp'] = {
            'length': best_length,
            'time': time.perf_counter() - t5,
        }

    # ═══ FINAL POLISH ═══
    if _time_left() > 0.5:
        t6 = time.perf_counter()
        # 2-opt
        final_tour, final_length, _ = two_opt(
            best_tour, distance_matrix, max_iterations=50, max_no_improve=10,
        )
        # 3-opt full
        if HAS_NUMBA and _time_left() > 0.3:
            nn_lists = build_neighbor_lists_jit(distance_matrix, min(15, n // 5 + 1))
            final_arr = np.array(final_tour, dtype=np.int64)
            from .numba_accel import three_opt_full_pass_jit
            for _ in range(5):
                if not three_opt_full_pass_jit(final_arr, distance_matrix, nn_lists):
                    break
            final_tour = final_arr.tolist()
            final_length = _tour_length(final_tour, distance_matrix)

        # Or-opt
        if _time_left() > 0.2:
            final_tour, final_length, _ = or_opt(final_tour, distance_matrix, max_iterations=10)

        if final_length < best_length and len(final_tour) == n and len(set(final_tour)) == n:
            best_tour = final_tour
            best_length = final_length

        phases['final_polish'] = {
            'length': best_length,
            'time': time.perf_counter() - t6,
        }

    # ═══ SAFETY NET: v3.3 fallback (только для N<500, иначе слишком дорого) ═══
    if n < 500 and _time_left() > 5.0:
        v3_result = solve_v3(
            distance_matrix,
            max_depth=max_depth,
            min_cluster_size=min_cluster_size,
            time_budget=min(_time_left() * 0.9, 20.0),
        )
        if v3_result['length'] < best_length:
            best_tour = v3_result['tour']
            best_length = v3_result['length']
            phases['v3_fallback'] = {'used': True, 'length': best_length}

    return _build_result(best_tour, best_length, phases, t_start)


def _nearest_neighbor(D: NDArray[np.float64], start: int = 0) -> list[int]:
    """Nearest Neighbor (vectorized numpy). Fallback если нет numba."""
    n = D.shape[0]
    visited = np.zeros(n, dtype=bool)
    tour = [start]
    visited[start] = True

    for _ in range(n - 1):
        current = tour[-1]
        dists = D[current].copy()
        dists[visited] = np.inf
        best_next = int(np.argmin(dists))
        if dists[best_next] == np.inf:
            break
        tour.append(best_next)
        visited[best_next] = True

    return tour


def _build_result(tour: list[int], length: float, phases: dict, t_start: float) -> dict:
    return {
        'tour': tour,
        'length': length,
        'phases': phases,
        'time_total': time.perf_counter() - t_start,
        'n': len(tour),
    }


def _tour_length(tour: list[int], D: NDArray[np.float64]) -> float:
    """Длина замкнутого тура (vectorized)."""
    t = np.asarray(tour)
    return float(D[t, np.roll(t, -1)].sum())


# ═══════════════════════════════════════════════════════════
#  UNIVERSAL DISPATCHER
# ═══════════════════════════════════════════════════════════

def solve(
    D: Optional[NDArray[np.float64]] = None,
    coords: Optional[NDArray[np.float64]] = None,
    time_budget: Optional[float] = None,
    **kwargs,
) -> dict:
    """
    Universal TSP solver dispatcher.

    - D provided → solve_v4 (D-matrix based)
    - coords provided, N>3000 → solve_v5 (coordinate-first ultra)
    - coords provided, N≤3000 → compute D, solve_v4
    """
    if coords is not None:
        n = len(coords)
        if n > 3000:
            from src.core.ultra_solver import solve_v5
            budget = time_budget if time_budget else max(60.0, n * 0.03)
            return solve_v5(coords, time_budget=budget, **kwargs)
        else:
            D = np.sqrt(((coords[:, None] - coords[None, :]) ** 2).sum(axis=2))

    if D is None:
        raise ValueError("Either D or coords must be provided")

    budget = time_budget if time_budget else None
    return solve_v4(D, time_budget=budget)
