"""
Ultra Solver v5.0 — Ultra-Scale TSP (N=5K-200K+).

Coordinate-first архитектура: НИКОГДА не строим D[N,N].
Memory: ~310 MB для N=100K (vs 80 GB с полной матрицей).

Pipeline:
  Phase 0: DistanceOracle (KDTree k-NN)       — 2% time
  Phase 1: Recursive spectral decompose        — 3% time
  Phase 2: Parallel leaf optimize (12 cores)    — 50% time
  Phase 3: Bottom-up stitch + boundary          — 10% time
  Phase 4: V-cycle refinement (2 passes)        — 25% time
  Phase 5: Global polish (2-opt NN on kNN)      — 10% time
"""

from __future__ import annotations

import numpy as np
from numpy.typing import NDArray
from typing import Optional
import time
import multiprocessing
import sys

from src.core.distance_oracle import DistanceOracle
from src.core.numba_sparse import (
    warmup_sparse,
    tour_length_coords_jit,
    nn_tour_coords_jit,
    two_opt_nn_coords_jit,
    two_opt_pass_nn_coords_jit,
    three_opt_full_pass_coords_jit,
    or_opt_pass_coords_jit,
    double_bridge_coords_jit,
    lk_opt_coords_jit,
    lk_sequential_coords_jit,
)
from src.core.eax_sparse import eax_population_optimize
from src.core.hierarchy import (
    compute_stitch_ratio,
    decompose,
    get_leaves,
    find_boundary_cities,
    stitch_leaf_tours,
    stitch_leaf_tours_v2,
    v_cycle_refine,
    tree_stats,
)
from src.core.fingerprint import compute_fingerprint, StrategyRouter, SolverConfig


# ═══════════════════════════════════════════════════════════
#  MAIN ENTRY POINT
# ═══════════════════════════════════════════════════════════

def solve_v5(
    coords: NDArray[np.float64],
    time_budget: float = 300.0,
    n_workers: int = 0,
    knn_k: int = 20,
    max_leaf_size: int = 1500,
    verbose: bool = True,
    adaptive_knn: bool = True,
) -> dict:
    """
    Ultra-Scale TSP solver v5.0 with adaptive k-NN.

    Args:
        coords: координаты городов [N, 2]
        time_budget: бюджет времени в секундах
        n_workers: число параллельных процессов (0 = auto)
        knn_k: базовое k для k-NN (используется для leaf opt + v-cycle)
        max_leaf_size: макс. размер листа декомпозиции
        verbose: вывод прогресса
        adaptive_knn: если True, использовать k=10 для decompose, k=30 для global polish

    Returns:
        dict с ключами: tour, length, phases, time_total, n
    """
    t_start = time.perf_counter()
    n = len(coords)
    phases = {}

    if verbose:
        _log(f'[v5] Starting: N={n}, budget={time_budget:.0f}s, knn_k={knn_k}')

    # Auto workers
    if n_workers <= 0:
        n_workers = min(multiprocessing.cpu_count(), 12)

    # ═══════════ Phase 0: DistanceOracle ═══════════
    t0 = time.perf_counter()
    if verbose:
        _log(f'[v5] Phase 0: Building DistanceOracle (k={knn_k}, adaptive={adaptive_knn})...')

    # Phase 0: Oracle построен с базовым k (для листьев и V-cycle)
    oracle = DistanceOracle(coords, knn_k=knn_k)
    oracle.build_knn()
    oracle_knn_k_initial = knn_k  # Сохраняем начальное k

    # Instance Fingerprint + Strategy Router
    fp = compute_fingerprint(oracle)
    router = StrategyRouter()
    config = router.route(fp, time_budget=time_budget)
    cv_nn_dist = fp.cv_nn_dist

    if verbose:
        _log(f'[v5] Phase 0a: {router.explain(fp, config)}')

    # Alpha-nearness augment (управляется роутером)
    use_alpha = config.use_alpha
    if use_alpha:
        t_alpha = time.perf_counter()
        oracle.build_alpha_augmented(n_iters=config.alpha_iters, max_extra=5)
        if verbose:
            _log(f'  alpha augment done: k={oracle.knn_k}, {time.perf_counter() - t_alpha:.1f}s')

    # Adaptive leaf_size: роутер + N-scale overrides
    if config.use_decompose:
        if max_leaf_size == 1500:  # дефолтное значение → адаптируем
            max_leaf_size = config.max_leaf_size
            if n > 20000:
                target_leaves = max(24, min(100, n // 1500))
                max_leaf_size = max(2000, n // target_leaves)
                if cv_nn_dist > 0.8:
                    max_leaf_size = int(max_leaf_size * 0.85)
        max_leaf_size = min(max_leaf_size, 3000)
        max_leaf_size = min(max_leaf_size, n // 3)

    phases['oracle'] = {
        'time': time.perf_counter() - t0,
        'knn_k': knn_k,
        'memory_mb': _estimate_memory(n, knn_k),
        'cv_nn_dist': cv_nn_dist,
        'adaptive_leaf_size': max_leaf_size,
    }
    if verbose:
        _log(f'  oracle built: {phases["oracle"]["time"]:.1f}s, ~{phases["oracle"]["memory_mb"]:.0f} MB, '
             f'cv_nn={cv_nn_dist:.3f}, leaf_size={max_leaf_size}')

    # ═══════════ Phase 0.5: Warmup Numba ═══════════
    t0 = time.perf_counter()
    warmup_sparse()
    phases['warmup'] = {'time': time.perf_counter() - t0}

    leaves = None  # для fallback
    if config.use_decompose:
        # ═══════════ Phase 1: Hierarchical decomposition ═══════════
        t0 = time.perf_counter()
        if verbose:
            _log(f'[v5] Phase 1: Spectral decomposition (max_leaf={max_leaf_size})...')

        decompose_k = min(knn_k, 15)
        root = decompose(
            coords,
            max_leaf_size=max_leaf_size,
            min_leaf_size=50,
            knn_k=decompose_k,
            use_spectral=config.use_spectral_decompose,
        )
        stats = tree_stats(root)
        phases['decomposition'] = {
            'time': time.perf_counter() - t0,
            'n_leaves': stats['n_leaves'],
            'max_depth': stats['max_depth'],
            'leaf_min': min(stats['leaf_sizes']),
            'leaf_max': max(stats['leaf_sizes']),
            'leaf_mean': float(np.mean(stats['leaf_sizes'])),
        }
        if verbose:
            _log(f'  decomposed: {stats["n_leaves"]} leaves, depth={stats["max_depth"]}, '
                 f'leaf_size={min(stats["leaf_sizes"])}-{max(stats["leaf_sizes"])}')

        # ═══════════ Phase 2: Parallel leaf optimization ═══════════
        time_remaining = time_budget - (time.perf_counter() - t_start)
        leaf_fraction = config.leaf_budget_fraction if n <= 20000 else 0.35
        leaf_budget = time_remaining * leaf_fraction

        t0 = time.perf_counter()
        if verbose:
            _log(f'[v5] Phase 2: Optimizing {stats["n_leaves"]} leaves '
                 f'({n_workers} workers, budget={leaf_budget:.0f}s)...')

        leaves = get_leaves(root)
        _optimize_leaves_parallel(
            coords, oracle, leaves,
            n_workers=n_workers,
            time_budget=leaf_budget,
            verbose=verbose,
        )

        leaf_lengths = [l.tour_length for l in leaves if l.tour is not None]
        phases['leaf_optimization'] = {
            'time': time.perf_counter() - t0,
            'n_leaves': len(leaves),
            'sum_length': sum(leaf_lengths),
        }
        if verbose:
            _log(f'  leaves optimized: {time.perf_counter()-t0:.1f}s')

        # ═══════════ Phase 3: Stitching ═══════════
        t0 = time.perf_counter()
        if verbose:
            _log(f'[v5] Phase 3: Stitching {stats["n_leaves"]} leaf tours...')

        find_boundary_cities(coords, root, n_boundary=20)
        global_tour = stitch_leaf_tours(coords, root, oracle)

        if len(global_tour) != n or len(set(global_tour.tolist())) != n:
            if verbose:
                _log(f'  WARNING: stitch invalid tour. Rebuilding...')
            global_tour = _rebuild_tour_fallback(coords, oracle, leaves)

        stitch_length = tour_length_coords_jit(global_tour, coords)
        phases['stitching'] = {
            'time': time.perf_counter() - t0,
            'length': float(stitch_length),
        }
        if verbose:
            _log(f'  stitched: length={stitch_length:.0f}, t={time.perf_counter()-t0:.1f}s')

        best_tour = global_tour.copy()
        best_length = float(stitch_length)

        # Stitch quality metrics (для адаптивного V-cycle)
        stitch_metrics = compute_stitch_ratio(global_tour, coords, leaves)
        phases['stitching']['stitch_ratio'] = stitch_metrics['stitch_ratio']
        phases['stitching']['stitch_count'] = stitch_metrics['stitch_count']
        phases['stitching']['max_stitch_stress'] = stitch_metrics['max_stitch_stress']
        if verbose:
            _log(f'  stitch quality: ratio={stitch_metrics["stitch_ratio"]:.3f}, '
                 f'count={stitch_metrics["stitch_count"]}, '
                 f'stress={stitch_metrics["max_stitch_stress"]:.1f}x')

        # ═══════════ Phase 4: V-cycle refinement ═══════════
        time_remaining = time_budget - (time.perf_counter() - t_start)

        # Адаптивный бюджет V-cycle на основе stitch quality
        base_fraction = config.v_cycle_budget_fraction if n <= 20000 else 0.75
        sr = stitch_metrics['stitch_ratio']
        if sr > 0.15:
            vcycle_fraction = min(0.85, base_fraction * 1.3)
        elif sr < 0.05:
            vcycle_fraction = max(0.30, base_fraction * 0.6)
        else:
            vcycle_fraction = base_fraction
        vcycle_budget = time_remaining * vcycle_fraction

        t0 = time.perf_counter()
        if verbose:
            _log(f'[v5] Phase 4: V-cycle refinement (budget={vcycle_budget:.0f}s, '
                 f'fraction={vcycle_fraction:.0%})...')

        # Адаптивный segment size
        base_seg_size = min(4000, max(1000, n // 10))
        if sr > 0.15:
            seg_size = min(6000, int(base_seg_size * 1.5))
        elif sr < 0.05:
            seg_size = max(800, int(base_seg_size * 0.7))
        else:
            seg_size = base_seg_size
        n_cycles = max(1, min(3, int(vcycle_budget / max(n / 3000, 1))))

        refined = v_cycle_refine(
            best_tour, coords, oracle,
            n_cycles=n_cycles,
            segment_size=seg_size,
            overlap=seg_size // 5,
            leaves=leaves,
            time_budget=vcycle_budget,
            stitch_metrics=stitch_metrics,
        )
        refined_length = tour_length_coords_jit(refined, coords)

        if refined_length < best_length:
            best_tour = refined
            best_length = float(refined_length)

        phases['v_cycle'] = {
            'time': time.perf_counter() - t0,
            'length': best_length,
            'n_cycles': n_cycles,
            'segment_size': seg_size,
            'improvement': float(stitch_length - best_length),
        }
        if verbose:
            _log(f'  v-cycle: {stitch_length:.0f} -> {best_length:.0f} '
                 f'(-{(stitch_length-best_length)/stitch_length*100:.1f}%)')

    else:
        # ═══════════ NO DECOMPOSE: direct NN + LK ═══════════
        t0 = time.perf_counter()
        if verbose:
            _log(f'[v5] Skip decompose (strategy={config.strategy_name})')
            _log(f'[v5] Building initial tour via NN + LK...')

        tour = nn_tour_coords_jit(coords, oracle.knn_indices, oracle.knn_dists, 0)
        two_opt_nn_coords_jit(tour, coords, oracle.knn_indices, 30, 3)
        three_opt_full_pass_coords_jit(tour, coords, oracle.knn_indices)
        or_opt_pass_coords_jit(tour, coords, oracle.knn_indices)
        lk_opt_coords_jit(tour, coords, oracle.knn_indices, 30, 3)

        best_tour = tour.copy()
        best_length = float(tour_length_coords_jit(tour, coords))

        phases['no_decompose'] = {
            'time': time.perf_counter() - t0,
            'initial_length': best_length,
        }
        if verbose:
            _log(f'  initial tour: {best_length:.0f} ({time.perf_counter()-t0:.1f}s)')

    # ═══════════ Phase 5: Global polish ═══════════
    time_remaining = time_budget - (time.perf_counter() - t_start)

    t0 = time.perf_counter()
    if verbose:
        _log(f'[v5] Phase 5: Global polish (budget={time_remaining:.0f}s)...')

    # Adaptive k-NN: rebuild для более thorough поиска в polish фазе
    oracle_knn_k_polish = oracle_knn_k_initial  # дефолт: не меняем
    knn_rebuild_time = 0.0

    if adaptive_knn and time_remaining > 3.0:
        # Переход к k=30 для более thorough global search
        knn_k_polish = min(30, n - 1)  # cap at n-1
        if knn_k_polish > oracle_knn_k_initial:
            t_knn_rebuild = time.perf_counter()
            oracle.knn_k = knn_k_polish
            oracle.build_knn()
            # Re-apply alpha augment на расширенном k-NN
            if use_alpha:
                oracle.build_alpha_augmented(n_iters=30, max_extra=5)
            knn_rebuild_time = time.perf_counter() - t_knn_rebuild
            oracle_knn_k_polish = knn_k_polish

            time_remaining -= knn_rebuild_time
            if verbose:
                _log(f'  rebuilding oracle k-NN: {oracle_knn_k_initial} → {knn_k_polish} '
                     f'({knn_rebuild_time:.2f}s)')

    polished = _global_polish(
        best_tour, coords, oracle,
        time_budget=time_remaining,
        verbose=verbose,
        use_sequential_lk=config.use_sequential_lk,
        lk_max_depth=config.lk_max_depth,
    )
    polish_length = tour_length_coords_jit(polished, coords)

    if polish_length < best_length:
        best_tour = polished
        best_length = float(polish_length)

    phases['global_polish'] = {
        'time': time.perf_counter() - t0,
        'length': best_length,
        'knn_k': oracle_knn_k_polish,
        'knn_rebuild_time': knn_rebuild_time,
    }
    if verbose:
        _log(f'  polish: -> {best_length:.0f}')

    # ═══════════ Result ═══════════
    total_time = time.perf_counter() - t_start
    if verbose:
        _log(f'[v5] DONE: length={best_length:.0f}, time={total_time:.1f}s')

    return {
        'tour': best_tour.tolist(),
        'length': best_length,
        'phases': phases,
        'time_total': total_time,
        'n': n,
    }



# ═══════════════════════════════════════════════════════════
#  LEAF OPTIMIZATION
# ═══════════════════════════════════════════════════════════

def _optimize_single_leaf(args: tuple) -> tuple:
    """Worker: оптимизирует один лист. Для multiprocessing."""
    cities, coords_all, knn_k, leaf_budget = args

    n_local = len(cities)
    local_coords = coords_all[cities]

    # Строим локальную D-матрицу (помещается в RAM для N≤1000)
    from scipy.spatial import cKDTree
    k_local = min(knn_k, n_local - 1)

    if n_local <= 5:
        # Тривиальный случай
        tour = np.arange(n_local, dtype=np.int64)
        length = tour_length_coords_jit(tour, local_coords)
        return cities[tour].tolist(), float(length)

    tree = cKDTree(local_coords)
    _, nn_idx = tree.query(local_coords, k=k_local + 1)
    nn_idx = nn_idx[:, 1:].astype(np.int32)
    nn_dists = np.zeros_like(nn_idx, dtype=np.float64)
    for i in range(n_local):
        for j in range(nn_idx.shape[1]):
            nn_dists[i, j] = np.sqrt(((local_coords[i] - local_coords[nn_idx[i, j]]) ** 2).sum())

    # NN greedy tour
    best_tour = nn_tour_coords_jit(local_coords, nn_idx, nn_dists, 0)
    best_length = tour_length_coords_jit(best_tour, local_coords)

    # Мульти-старт NN (3 старта)
    for start in [n_local // 3, 2 * n_local // 3]:
        cand = nn_tour_coords_jit(local_coords, nn_idx, nn_dists, start)
        cand_len = tour_length_coords_jit(cand, local_coords)
        if cand_len < best_length:
            best_tour = cand
            best_length = cand_len

    # Phase 1: детерминированный 2-opt для быстрого начального улучшения
    two_opt_nn_coords_jit(best_tour, local_coords, nn_idx, 50, 5)
    best_length = tour_length_coords_jit(best_tour, local_coords)

    # Phase 2: детерминированный ILS (or-opt + 3-opt → double_bridge + LK)
    t_end = time.perf_counter() + leaf_budget * 0.5

    # Начальная полировка: or-opt + 3-opt
    or_opt_pass_coords_jit(best_tour, local_coords, nn_idx)
    three_opt_full_pass_coords_jit(best_tour, local_coords, nn_idx)
    best_length = tour_length_coords_jit(best_tour, local_coords)

    # ILS loop: double_bridge perturbation + LK recovery
    while time.perf_counter() < t_end:
        perturbed = double_bridge_coords_jit(best_tour)
        lk_opt_coords_jit(perturbed, local_coords, nn_idx, 30, 2)
        p_len = tour_length_coords_jit(perturbed, local_coords)
        if p_len < best_length - 1e-10:
            best_tour = perturbed
            best_length = p_len

    # Map back to global indices
    global_tour = cities[best_tour].tolist()
    return global_tour, float(best_length)


def _optimize_leaves_parallel(
    coords: NDArray[np.float64],
    oracle: DistanceOracle,
    leaves: list,
    n_workers: int = 8,
    time_budget: float = 120.0,
    verbose: bool = True,
):
    """Параллельная оптимизация всех листьев."""
    n_leaves = len(leaves)
    per_leaf_budget = time_budget / max(n_leaves / n_workers, 1)

    # Подготовка аргументов
    args_list = [
        (leaf.cities, coords, oracle.knn_k, per_leaf_budget)
        for leaf in leaves
    ]

    if n_workers <= 1 or n_leaves <= 2:
        # Последовательно
        for i, args in enumerate(args_list):
            tour_global, length = _optimize_single_leaf(args)
            leaves[i].tour = np.array(tour_global, dtype=np.int64)
            leaves[i].tour_length = length
            if verbose and (i + 1) % 5 == 0:
                _log(f'    leaf {i+1}/{n_leaves}: N={leaves[i].n}, len={length:.0f}')
    else:
        # Параллельно через multiprocessing (fork на macOS)
        try:
            ctx = multiprocessing.get_context('fork')
            with ctx.Pool(n_workers) as pool:
                results = pool.map(_optimize_single_leaf, args_list)
            for i, (tour_global, length) in enumerate(results):
                leaves[i].tour = np.array(tour_global, dtype=np.int64)
                leaves[i].tour_length = length
        except Exception as e:
            if verbose:
                _log(f'  WARNING: parallel failed ({e}), falling back to sequential')
            for i, args in enumerate(args_list):
                tour_global, length = _optimize_single_leaf(args)
                leaves[i].tour = np.array(tour_global, dtype=np.int64)
                leaves[i].tour_length = length


# ═══════════════════════════════════════════════════════════
#  GLOBAL POLISH
# ═══════════════════════════════════════════════════════════

def _global_polish(
    tour: NDArray[np.int64],
    coords: NDArray[np.float64],
    oracle: DistanceOracle,
    time_budget: float = 60.0,
    verbose: bool = False,
    use_sequential_lk: bool = False,
    lk_max_depth: int = 3,
) -> NDArray[np.int64]:
    """
    Глобальный polish: гибрид ILS + EAX.

    Phase A (60% времени): ILS (double_bridge + LK-DLB/seqLK) — генерирует
    разнообразные хорошие туры для популяции.
    Phase B (40% времени): EAX population — рекомбинирует лучшие рёбра
    из ILS-туров.
    """
    tour = tour.copy()
    n = len(tour)
    t_end = time.perf_counter() + time_budget

    if time_budget < 1.0:
        return tour

    # Phase A-0: deterministic local search
    best_length = tour_length_coords_jit(tour, coords)
    max_2opt = min(20, max(3, int(time_budget / 5)))
    two_opt_nn_coords_jit(tour, coords, oracle.knn_indices, max_2opt, 3)

    remaining = t_end - time.perf_counter()
    if remaining > 5.0:
        for _ in range(3):
            if time.perf_counter() > t_end:
                break
            imp_or = or_opt_pass_coords_jit(tour, coords, oracle.knn_indices)
            imp3 = three_opt_full_pass_coords_jit(tour, coords, oracle.knn_indices)
            if not imp_or and not imp3:
                break

    best_length = tour_length_coords_jit(tour, coords)
    best_tour = tour.copy()

    # Для N > 5K: hybrid ILS (60%) + EAX (40%)
    # Для N ≤ 5K: чистый ILS (EAX Python overhead слишком велик для малых N)
    use_eax = n > 5000

    # Phase A-1: ILS — double_bridge + LK-DLB
    remaining = t_end - time.perf_counter()
    ils_fraction = 0.60 if use_eax else 1.0
    ils_end = time.perf_counter() + remaining * ils_fraction
    good_tours: list[tuple[float, NDArray[np.int64]]] = [(best_length, best_tour.copy())]

    while time.perf_counter() < ils_end:
        perturbed = double_bridge_coords_jit(tour)
        if use_sequential_lk:
            # seqLK: deeper search, slower but better quality per iteration
            lk_sequential_coords_jit(perturbed, coords, oracle.knn_indices, 30, 2, lk_max_depth)
        else:
            lk_opt_coords_jit(perturbed, coords, oracle.knn_indices, 30, 2)
        p_len = tour_length_coords_jit(perturbed, coords)

        if p_len < best_length - 1e-10:
            best_tour = perturbed.copy()
            best_length = float(p_len)
            tour = perturbed

        # Сохраняем хорошие туры для EAX
        if use_eax:
            good_tours.append((float(p_len), perturbed.copy()))
            if len(good_tours) > 20:
                good_tours.sort(key=lambda x: x[0])
                good_tours = good_tours[:15]

    if verbose:
        _log(f'  ILS phase: {best_length:.0f}' +
             (f', collected {len(good_tours)} tours' if use_eax else ''))

    # Phase B: EAX population (только для N > 10K)
    if use_eax:
        remaining = t_end - time.perf_counter()
        if remaining > 3.0 and len(good_tours) >= 3:
            good_tours.sort(key=lambda x: x[0])
            pop_size = min(15, len(good_tours))
            init_tours = [t for _, t in good_tours[:pop_size]]

            eax_best, eax_len = eax_population_optimize(
                coords, oracle.knn_indices, init_tours,
                pop_size=pop_size,
                max_generations=300,
                time_budget=remaining - 0.5,
                lk_iters=25,
                lk_no_improve=2,
                verbose=verbose,
            )

            if eax_len < best_length:
                best_tour = eax_best
                best_length = eax_len
                if verbose:
                    _log(f'  EAX improved: {best_length:.0f}')

    return best_tour


# ═══════════════════════════════════════════════════════════
#  FALLBACK & UTILITIES
# ═══════════════════════════════════════════════════════════


def _rebuild_tour_fallback(
    coords: NDArray[np.float64],
    oracle: DistanceOracle,
    leaves: list,
) -> NDArray[np.int64]:
    """Fallback: строим тур из всех городов если stitching не удался."""
    n = len(coords)
    # NN greedy на полном наборе
    tour = nn_tour_coords_jit(coords, oracle.knn_indices, oracle.knn_dists, 0)
    two_opt_nn_coords_jit(tour, coords, oracle.knn_indices, 20, 5)
    return tour


def _estimate_memory(n: int, knn_k: int) -> float:
    """Оценка памяти в MB."""
    coords_mb = n * 2 * 8 / 1024 / 1024
    knn_mb = n * knn_k * (4 + 8) / 1024 / 1024  # indices + dists
    tour_mb = n * 8 / 1024 / 1024
    return coords_mb + knn_mb + tour_mb + 20  # overhead


def _log(msg: str):
    """Печать с flush."""
    print(msg)
    sys.stdout.flush()
