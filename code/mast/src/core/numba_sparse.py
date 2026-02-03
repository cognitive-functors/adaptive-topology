"""
Numba JIT functions for coordinate-based (sparse) TSP — v5.0.

Все функции работают с coords[N,2] вместо D[N,N].
Для Ultra-Scale TSP (N=30K-200K): 310MB вместо 80GB.

Ключевое преимущество: для N>10K, on-the-fly dist (~10ns)
БЫСТРЕЕ D[i,j] lookup (~50-100ns из-за cache misses на огромной матрице).
"""

from __future__ import annotations

import numpy as np
from numpy.typing import NDArray
from numba import njit

# ═══════════════════════════════════════════════════════════
#  DISTANCE PRIMITIVE
# ═══════════════════════════════════════════════════════════

@njit(cache=True)
def dist_jit(coords: NDArray[np.float64], i: int, j: int) -> float:
    """Евклидово расстояние из координат. ~10ns."""
    dx = coords[i, 0] - coords[j, 0]
    dy = coords[i, 1] - coords[j, 1]
    return np.sqrt(dx * dx + dy * dy)


# ═══════════════════════════════════════════════════════════
#  TOUR LENGTH
# ═══════════════════════════════════════════════════════════

@njit(cache=True)
def tour_length_coords_jit(
    tour: NDArray[np.int64],
    coords: NDArray[np.float64],
) -> float:
    """Длина замкнутого тура из координат. O(N)."""
    n = len(tour)
    s = 0.0
    for i in range(n - 1):
        s += dist_jit(coords, tour[i], tour[i + 1])
    s += dist_jit(coords, tour[n - 1], tour[0])
    return s


# ═══════════════════════════════════════════════════════════
#  NN TOUR CONSTRUCTION
# ═══════════════════════════════════════════════════════════

@njit(cache=True)
def nn_tour_coords_jit(
    coords: NDArray[np.float64],
    nn_indices: NDArray[np.int32],
    nn_dists: NDArray[np.float64],
    start: int,
) -> NDArray[np.int64]:
    """
    Nearest Neighbor тур из k-NN lists.
    O(N*k) с brute-force fallback для последних городов.
    """
    n = coords.shape[0]
    k = nn_indices.shape[1]
    tour = np.empty(n, dtype=np.int64)
    visited = np.zeros(n, dtype=np.bool_)
    tour[0] = start
    visited[start] = True

    for step in range(1, n):
        current = tour[step - 1]
        best_dist = np.inf
        best_city = -1

        # Фаза 1: ищем среди k-NN (O(k))
        for ki in range(k):
            nb = nn_indices[current, ki]
            if nb < 0:
                break
            if not visited[nb]:
                d = nn_dists[current, ki]
                if d < best_dist:
                    best_dist = d
                    best_city = nb

        # Фаза 2: fallback — ищем среди k-NN недавних (O(lookback*k))
        if best_city == -1:
            for lookback in range(min(step, 100)):
                recent = tour[step - 1 - lookback]
                for ki in range(k):
                    nb = nn_indices[recent, ki]
                    if nb < 0:
                        break
                    if not visited[nb]:
                        d = dist_jit(coords, current, nb)
                        if d < best_dist:
                            best_dist = d
                            best_city = nb

        # Фаза 3: nuclear fallback — brute force (очень редко)
        if best_city == -1:
            for j in range(n):
                if not visited[j]:
                    d = dist_jit(coords, current, j)
                    if d < best_dist:
                        best_dist = d
                        best_city = j

        if best_city == -1:
            # Все посещены — не должно случиться
            break

        tour[step] = best_city
        visited[best_city] = True

    return tour


# ═══════════════════════════════════════════════════════════
#  2-OPT WITH NEIGHBOR LISTS
# ═══════════════════════════════════════════════════════════

@njit(cache=True)
def two_opt_pass_nn_coords_jit(
    tour: NDArray[np.int64],
    coords: NDArray[np.float64],
    nn_indices: NDArray[np.int32],
) -> bool:
    """2-opt проход на координатах с neighbor lists. O(N*k)."""
    n = len(tour)
    k = nn_indices.shape[1]
    improved = False

    # Позиция каждого города в туре
    max_city = coords.shape[0]
    pos = np.empty(max_city, dtype=np.int64)
    for i in range(n):
        pos[tour[i]] = i

    for idx in range(n):
        city_i = tour[idx]
        idx_next = (idx + 1) % n
        city_ip1 = tour[idx_next]
        
        # Предвычисляем стоимость текущего ребра
        dist_i_ip1 = dist_jit(coords, city_i, city_ip1)

        for ki in range(k):
            neighbor = nn_indices[city_i, ki]
            if neighbor < 0:
                break
            j = pos[neighbor]
            if j == idx or j == idx_next:
                continue

            i_eff = idx
            j_eff = j
            if i_eff > j_eff:
                i_eff, j_eff = j_eff, i_eff

            if j_eff == n - 1 and i_eff == 0:
                continue

            a = tour[i_eff]
            b = tour[i_eff + 1]
            c = tour[j_eff]
            d_city = tour[(j_eff + 1) % n]

            old_cost = dist_jit(coords, a, b) + dist_jit(coords, c, d_city)
            new_cost = dist_jit(coords, a, c) + dist_jit(coords, b, d_city)

            if new_cost < old_cost - 1e-10:
                # Reverse segment [i_eff+1 .. j_eff]
                lo = i_eff + 1
                hi = j_eff
                while lo < hi:
                    tmp = tour[lo]
                    tour[lo] = tour[hi]
                    tour[hi] = tmp
                    lo += 1
                    hi -= 1
                # Обновить pos
                for m in range(i_eff + 1, j_eff + 1):
                    pos[tour[m]] = m
                improved = True
                break

    return improved


@njit(cache=True)
def two_opt_nn_coords_jit(
    tour: NDArray[np.int64],
    coords: NDArray[np.float64],
    nn_indices: NDArray[np.int32],
    max_iterations: int = 50,
    max_no_improve: int = 5,
) -> int:
    """Полный 2-opt цикл. Returns число итераций."""
    no_improve = 0
    for iteration in range(max_iterations):
        if two_opt_pass_nn_coords_jit(tour, coords, nn_indices):
            no_improve = 0
        else:
            no_improve += 1
            if no_improve >= max_no_improve:
                return iteration + 1
    return max_iterations


# ═══════════════════════════════════════════════════════════
#  3-OPT FULL (ALL 7 VARIANTS)
# ═══════════════════════════════════════════════════════════

@njit(cache=True)
def _reverse_segment_inplace(tour: NDArray[np.int64], lo: int, hi: int):
    """Reverse tour[lo..hi] in place."""
    while lo < hi:
        tmp = tour[lo]
        tour[lo] = tour[hi]
        tour[hi] = tmp
        lo += 1
        hi -= 1


@njit(cache=True)
def three_opt_full_pass_coords_jit(
    tour: NDArray[np.int64],
    coords: NDArray[np.float64],
    nn_indices: NDArray[np.int32],
) -> bool:
    """3-opt с 7 вариантами reconnection на координатах. O(N*k²)."""
    n = len(tour)
    k = nn_indices.shape[1]
    improved = False

    max_city = coords.shape[0]
    pos = np.empty(max_city, dtype=np.int64)
    for i in range(n):
        pos[tour[i]] = i

    for idx_i in range(n):
        city_i = tour[idx_i]

        for ki in range(k):
            nb1 = nn_indices[city_i, ki]
            if nb1 < 0:
                break
            idx_j = pos[nb1]
            if idx_j <= idx_i or idx_j >= n - 1:
                continue

            for kj in range(k):
                nb2 = nn_indices[tour[idx_j], kj]
                if nb2 < 0:
                    break
                idx_k = pos[nb2]
                if idx_k <= idx_j:
                    continue
                if idx_k >= n - 1 and idx_i == 0:
                    continue

                i2 = idx_i + 1
                j1 = idx_j
                j2 = idx_j + 1
                k1 = idx_k
                k2_idx = (idx_k + 1) % n

                A = tour[idx_i]
                B = tour[i2]
                C = tour[j1]
                E = tour[j2]
                F = tour[k1]
                G = tour[k2_idx]

                # 3 текущих ребра
                d_AB = dist_jit(coords, A, B)
                d_CE = dist_jit(coords, C, E)
                d_FG = dist_jit(coords, F, G)
                old_cost = d_AB + d_CE + d_FG

                # Предвычисление 12 уникальных расстояний
                d_AC = dist_jit(coords, A, C)
                d_BE = dist_jit(coords, B, E)
                d_CF = dist_jit(coords, C, F)
                d_EG = dist_jit(coords, E, G)
                d_BF = dist_jit(coords, B, F)
                d_AE = dist_jit(coords, A, E)
                d_CG = dist_jit(coords, C, G)
                d_BG = dist_jit(coords, B, G)
                d_AF = dist_jit(coords, A, F)
                d_EC = dist_jit(coords, E, C)
                d_FB = dist_jit(coords, F, B)  # = d_BF

                best_gain = 0.0
                best_variant = 0

                # Вариант 1: reverse B segment — A-C + B-E + F-G
                g = old_cost - (d_AC + d_BE + d_FG)
                if g > best_gain + 1e-10:
                    best_gain = g; best_variant = 1

                # Вариант 2: reverse C segment — A-B + C-F + E-G
                g = old_cost - (d_AB + d_CF + d_EG)
                if g > best_gain + 1e-10:
                    best_gain = g; best_variant = 2

                # Вариант 3: reverse both — A-C + B-F + E-G
                g = old_cost - (d_AC + d_BF + d_EG)
                if g > best_gain + 1e-10:
                    best_gain = g; best_variant = 3

                # Вариант 4: swap B,C — A-E + F-B + C-G
                g = old_cost - (d_AE + d_FB + d_CG)
                if g > best_gain + 1e-10:
                    best_gain = g; best_variant = 4

                # Вариант 5: swap, reverse B — A-E + F-C + B-G
                g = old_cost - (d_AE + dist_jit(coords, F, C) + d_BG)
                if g > best_gain + 1e-10:
                    best_gain = g; best_variant = 5

                # Вариант 6: swap, reverse C — A-F + E-B + C-G
                g = old_cost - (d_AF + dist_jit(coords, E, B) + d_CG)
                if g > best_gain + 1e-10:
                    best_gain = g; best_variant = 6

                # Вариант 7: swap, reverse both — A-F + E-C + B-G
                g = old_cost - (d_AF + d_EC + d_BG)
                if g > best_gain + 1e-10:
                    best_gain = g; best_variant = 7

                if best_variant == 0:
                    continue

                # Применение
                if best_variant == 1:
                    _reverse_segment_inplace(tour, i2, j1)
                elif best_variant == 2:
                    _reverse_segment_inplace(tour, j2, k1)
                elif best_variant == 3:
                    _reverse_segment_inplace(tour, i2, j1)
                    _reverse_segment_inplace(tour, j2, k1)
                elif best_variant >= 4:
                    # Swap segments B и C
                    len_b = j1 - i2 + 1
                    len_c = k1 - j2 + 1
                    seg_b = np.empty(len_b, dtype=np.int64)
                    seg_c = np.empty(len_c, dtype=np.int64)
                    for m in range(len_b):
                        seg_b[m] = tour[i2 + m]
                    for m in range(len_c):
                        seg_c[m] = tour[j2 + m]

                    if best_variant == 5:
                        # Reverse B
                        for m in range(len_b // 2):
                            tmp = seg_b[m]
                            seg_b[m] = seg_b[len_b - 1 - m]
                            seg_b[len_b - 1 - m] = tmp
                    elif best_variant == 6:
                        # Reverse C
                        for m in range(len_c // 2):
                            tmp = seg_c[m]
                            seg_c[m] = seg_c[len_c - 1 - m]
                            seg_c[len_c - 1 - m] = tmp
                    elif best_variant == 7:
                        # Reverse both
                        for m in range(len_b // 2):
                            tmp = seg_b[m]
                            seg_b[m] = seg_b[len_b - 1 - m]
                            seg_b[len_b - 1 - m] = tmp
                        for m in range(len_c // 2):
                            tmp = seg_c[m]
                            seg_c[m] = seg_c[len_c - 1 - m]
                            seg_c[len_c - 1 - m] = tmp

                    # Write: C first, then B
                    write_pos = i2
                    for m in range(len_c):
                        tour[write_pos] = seg_c[m]
                        write_pos += 1
                    for m in range(len_b):
                        tour[write_pos] = seg_b[m]
                        write_pos += 1

                # Обновить pos
                for m in range(i2, (idx_k + 1) if idx_k + 1 <= n else n):
                    pos[tour[m]] = m
                improved = True
                break
            if improved:
                break
        if improved:
            break

    return improved


# ═══════════════════════════════════════════════════════════
#  OR-OPT WITH NEIGHBOR LISTS
# ═══════════════════════════════════════════════════════════

@njit(cache=True)
def or_opt_pass_coords_jit(
    tour: NDArray[np.int64],
    coords: NDArray[np.float64],
    nn_indices: NDArray[np.int32],
) -> bool:
    """Or-opt проход: переставляет сегменты 1-3 города. O(N*k)."""
    n = len(tour)
    k = nn_indices.shape[1]
    improved = False

    max_city = coords.shape[0]
    pos = np.empty(max_city, dtype=np.int64)
    for i in range(n):
        pos[tour[i]] = i

    for seg_len in (1, 2, 3):
        if improved:
            break
        for i in range(n):
            # Сегмент tour[i..i+seg_len-1]
            prev_idx = (i - 1) % n
            seg_end_idx = (i + seg_len - 1) % n
            next_idx = (i + seg_len) % n

            seg_first = tour[i]
            seg_last = tour[seg_end_idx]

            # Стоимость удаления сегмента
            remove_cost = (dist_jit(coords, tour[prev_idx], seg_first) +
                          dist_jit(coords, seg_last, tour[next_idx]))
            bridge_cost = dist_jit(coords, tour[prev_idx], tour[next_idx])

            # Ищем куда вставить (среди k-NN первого города сегмента)
            for ki in range(k):
                target = nn_indices[seg_first, ki]
                if target < 0:
                    break
                j = pos[target]

                # Пропускаем позиции внутри/рядом с сегментом
                skip = False
                for s in range(seg_len + 2):
                    check = (i - 1 + s) % n
                    if j == check:
                        skip = True
                        break
                if skip:
                    continue

                j_next = (j + 1) % n
                insert_cost = (dist_jit(coords, tour[j], seg_first) +
                              dist_jit(coords, seg_last, tour[j_next]))
                current_edge = dist_jit(coords, tour[j], tour[j_next])

                delta = (bridge_cost - remove_cost) + (insert_cost - current_edge)

                if delta < -1e-10:
                    # Выполняем or-opt move
                    # Извлекаем сегмент
                    seg = np.empty(seg_len, dtype=np.int64)
                    for s in range(seg_len):
                        seg[s] = tour[(i + s) % n]

                    # Собираем новый тур
                    new_tour = np.empty(n, dtype=np.int64)
                    seg_positions = set()
                    for s in range(seg_len):
                        seg_positions.add((i + s) % n)

                    write = 0
                    inserted = False
                    for t in range(n):
                        in_seg = False
                        for s in range(seg_len):
                            if t == (i + s) % n:
                                in_seg = True
                                break
                        if in_seg:
                            continue

                        new_tour[write] = tour[t]
                        write += 1

                        if tour[t] == tour[j] and not inserted:
                            for s in range(seg_len):
                                new_tour[write] = seg[s]
                                write += 1
                            inserted = True

                    if write == n:
                        for t in range(n):
                            tour[t] = new_tour[t]
                        for t in range(n):
                            pos[tour[t]] = t
                        improved = True
                        break

            if improved:
                break

    return improved


# ═══════════════════════════════════════════════════════════
#  K-NN FROM COORDINATES (Python wrapper)
# ═══════════════════════════════════════════════════════════

def build_knn_from_coords(
    coords: NDArray[np.float64],
    k: int,
) -> tuple[NDArray[np.int32], NDArray[np.float64]]:
    """
    k-NN из координат через KDTree. O(N * k * log N).
    
    Returns:
        nn_indices: (N, k) int32
        nn_dists: (N, k) float64
    """
    from scipy.spatial import cKDTree

    n = coords.shape[0]
    k = min(k, n - 1)
    
    tree = cKDTree(coords)
    dists, indices = tree.query(coords, k=k + 1)
    
    nn_indices = indices[:, 1:].astype(np.int32)
    nn_dists = dists[:, 1:].astype(np.float64)
    
    return nn_indices, nn_dists


# ═══════════════════════════════════════════════════════════
#  DOUBLE BRIDGE (не требует D)
# ═══════════════════════════════════════════════════════════

@njit(cache=True)
def double_bridge_coords_jit(tour: NDArray[np.int64]) -> NDArray[np.int64]:
    """Double-bridge perturbation. Не использует координаты."""
    n = len(tour)
    new_tour = np.empty(n, dtype=np.int64)
    
    if n < 8:
        for i in range(n):
            new_tour[i] = tour[i]
        i = np.random.randint(0, n)
        j = np.random.randint(0, n)
        tmp = new_tour[i]
        new_tour[i] = new_tour[j]
        new_tour[j] = tmp
        return new_tour
    
    # 3 random cut points
    cuts = np.sort(np.array([
        np.random.randint(1, n),
        np.random.randint(1, n),
        np.random.randint(1, n),
    ]))
    # Ensure distinct
    while cuts[0] == cuts[1] or cuts[1] == cuts[2]:
        cuts = np.sort(np.array([
            np.random.randint(1, n),
            np.random.randint(1, n),
            np.random.randint(1, n),
        ]))
    
    a, b, c = cuts[0], cuts[1], cuts[2]
    
    # Reconnect: A + C + B + D
    idx = 0
    for i in range(0, a):
        new_tour[idx] = tour[i]; idx += 1
    for i in range(b, c):
        new_tour[idx] = tour[i]; idx += 1
    for i in range(a, b):
        new_tour[idx] = tour[i]; idx += 1
    for i in range(c, n):
        new_tour[idx] = tour[i]; idx += 1
    
    return new_tour


# ═══════════════════════════════════════════════════════════
#  LK-STYLE 2-OPT WITH DON'T-LOOK BITS + GAIN PRUNING
# ═══════════════════════════════════════════════════════════

@njit(cache=True)
def lk_opt_pass_coords_jit(
    tour: NDArray[np.int64],
    coords: NDArray[np.float64],
    nn_indices: NDArray[np.int32],
    dlb: NDArray[np.bool_],
) -> bool:
    """
    2-opt с Don't-Look Bits (LK-style).

    DLB — ключевая оптимизация из LKH:
    - Города без недавних изменений пропускаются → ~3-5x быстрее
    - После хода DLB сбрасывается для 4 затронутых городов
    - First-improvement стратегия для скорости

    Модифицирует tour и dlb in-place.
    Returns: True если найдено улучшение.
    """
    n = len(tour)
    k = nn_indices.shape[1]
    max_city = coords.shape[0]
    improved = False

    # Позиция каждого города в туре — O(1) lookup
    pos = np.empty(max_city, dtype=np.int64)
    for i in range(n):
        pos[tour[i]] = i

    for scan in range(n):
        idx = scan
        city_a = tour[idx]
        if dlb[city_a]:
            continue

        idx_b = (idx + 1) % n
        city_b = tour[idx_b]

        found = False
        for ki in range(k):
            city_c = nn_indices[city_a, ki]
            if city_c < 0:
                break

            idx_c = pos[city_c]

            # Пропуск смежных позиций
            if idx_c == idx or idx_c == idx_b:
                continue

            # Нормализация: i_eff < j_eff
            i_eff = idx
            j_eff = idx_c
            if i_eff > j_eff:
                i_eff, j_eff = j_eff, i_eff

            if j_eff == n - 1 and i_eff == 0:
                continue

            seg_len = j_eff - i_eff
            if seg_len <= 0:
                continue

            a = tour[i_eff]
            b = tour[i_eff + 1]
            c = tour[j_eff]
            d_city = tour[(j_eff + 1) % n]

            old_cost = dist_jit(coords, a, b) + dist_jit(coords, c, d_city)
            new_cost = dist_jit(coords, a, c) + dist_jit(coords, b, d_city)

            if new_cost < old_cost - 1e-10:
                # Reverse tour[i_eff+1 .. j_eff]
                lo = i_eff + 1
                hi = j_eff
                while lo < hi:
                    tmp = tour[lo]
                    tour[lo] = tour[hi]
                    tour[hi] = tmp
                    lo += 1
                    hi -= 1

                # Обновить позиции и сбросить DLB для всего reversed segment
                for m in range(i_eff + 1, j_eff + 1):
                    pos[tour[m]] = m
                    dlb[tour[m]] = False

                # Endpoints тоже: у них сменились соседи
                dlb[a] = False
                dlb[d_city] = False

                improved = True
                found = True
                break

        if not found:
            dlb[city_a] = True

    return improved


@njit(cache=True)
def lk_opt_coords_jit(
    tour: NDArray[np.int64],
    coords: NDArray[np.float64],
    nn_indices: NDArray[np.int32],
    max_iterations: int,
    max_no_improve: int,
) -> int:
    """
    Полный LK-style 2-opt цикл с DLB.

    DLB-состояние сохраняется между проходами:
    после хода сбрасываются DLB для затронутых городов →
    следующий проход проверяет только их и «свежих» соседей.

    Returns: число выполненных итераций.
    """
    max_city = coords.shape[0]
    dlb = np.zeros(max_city, dtype=np.bool_)

    no_improve = 0
    for iteration in range(max_iterations):
        if lk_opt_pass_coords_jit(tour, coords, nn_indices, dlb):
            no_improve = 0
        else:
            no_improve += 1
            if no_improve >= max_no_improve:
                return iteration + 1
    return max_iterations





# ═══════════════════════════════════════════════════════════
#  ALPHA-NEARNESS (1-tree subgradient)
# ═══════════════════════════════════════════════════════════

@njit(cache=True)
def _uf_find(parent, i):
    """Union-Find: find с path compression."""
    while parent[i] != i:
        parent[i] = parent[parent[i]]
        i = parent[i]
    return i


@njit(cache=True)
def _uf_union(parent, rank, a, b):
    """Union-Find: union by rank. Возвращает True если merged."""
    ra = _uf_find(parent, a)
    rb = _uf_find(parent, b)
    if ra == rb:
        return False
    if rank[ra] < rank[rb]:
        parent[ra] = rb
    elif rank[ra] > rank[rb]:
        parent[rb] = ra
    else:
        parent[rb] = ra
        rank[ra] += 1
    return True


@njit(cache=True)
def sparse_kruskal_mst_jit(
    n: int,
    edges_from: NDArray[np.int32],
    edges_to: NDArray[np.int32],
    edges_weight: NDArray[np.float64],
):
    """
    Kruskal MST на sparse edge list. Union-Find с path compression.

    Returns:
        mst_adj: int32[n, 2] — для каждой вершины до 2 MST-соседей (для 1-tree)
                 Реально MST — дерево, но мы храним как adjacency list.
        mst_parent: int64[n] — parent в MST (для LCA / bottleneck path)
        mst_parent_weight: float64[n] — вес ребра к parent
        n_edges_mst: int — кол-во рёбер в MST
    """
    ne = len(edges_from)

    # Сортировка рёбер по весу (indirect sort)
    order = np.argsort(edges_weight)

    # Union-Find
    parent = np.arange(n, dtype=np.int64)
    rank = np.zeros(n, dtype=np.int64)

    # MST adjacency list: каждая вершина может иметь до degree N-1
    # Храним как edge list
    mst_from = np.empty(n - 1, dtype=np.int32)
    mst_to = np.empty(n - 1, dtype=np.int32)
    mst_weight = np.empty(n - 1, dtype=np.float64)
    mst_count = 0

    for idx in range(ne):
        ei = order[idx]
        u = edges_from[ei]
        v = edges_to[ei]
        w = edges_weight[ei]
        if _uf_union(parent, rank, u, v):
            mst_from[mst_count] = u
            mst_to[mst_count] = v
            mst_weight[mst_count] = w
            mst_count += 1
            if mst_count == n - 1:
                break

    # Построение parent-массива для LCA (BFS от вершины 0)
    # adj list через массивы
    adj_head = np.full(n, -1, dtype=np.int64)
    adj_next = np.full(2 * mst_count, -1, dtype=np.int64)
    adj_to_node = np.empty(2 * mst_count, dtype=np.int32)
    adj_wt = np.empty(2 * mst_count, dtype=np.float64)
    edge_idx = 0
    for i in range(mst_count):
        u = mst_from[i]
        v = mst_to[i]
        w = mst_weight[i]
        # u -> v
        adj_next[edge_idx] = adj_head[u]
        adj_head[u] = edge_idx
        adj_to_node[edge_idx] = v
        adj_wt[edge_idx] = w
        edge_idx += 1
        # v -> u
        adj_next[edge_idx] = adj_head[v]
        adj_head[v] = edge_idx
        adj_to_node[edge_idx] = u
        adj_wt[edge_idx] = w
        edge_idx += 1

    # BFS для parent tree
    mst_parent = np.full(n, -1, dtype=np.int64)
    mst_parent_weight = np.zeros(n, dtype=np.float64)
    mst_depth = np.zeros(n, dtype=np.int64)
    visited = np.zeros(n, dtype=np.bool_)

    queue = np.empty(n, dtype=np.int64)
    q_front = 0
    q_back = 0
    queue[q_back] = 0
    q_back += 1
    visited[0] = True
    mst_parent[0] = 0

    while q_front < q_back:
        u = queue[q_front]
        q_front += 1
        e = adj_head[u]
        while e != -1:
            v = adj_to_node[e]
            w = adj_wt[e]
            if not visited[v]:
                visited[v] = True
                mst_parent[v] = u
                mst_parent_weight[v] = w
                mst_depth[v] = mst_depth[u] + 1
                queue[q_back] = v
                q_back += 1
            e = adj_next[e]

    return mst_parent, mst_parent_weight, mst_depth, mst_count


@njit(cache=True)
def _bottleneck_on_path(u, v, mst_parent, mst_parent_weight, mst_depth):
    """Max edge weight на пути u→v в MST (через LCA)."""
    max_w = 0.0
    # Выравниваем глубины
    while mst_depth[u] > mst_depth[v]:
        w = mst_parent_weight[u]
        if w > max_w:
            max_w = w
        u = mst_parent[u]
    while mst_depth[v] > mst_depth[u]:
        w = mst_parent_weight[v]
        if w > max_w:
            max_w = w
        v = mst_parent[v]
    # Поднимаемся до LCA
    while u != v:
        wu = mst_parent_weight[u]
        wv = mst_parent_weight[v]
        if wu > max_w:
            max_w = wu
        if wv > max_w:
            max_w = wv
        u = mst_parent[u]
        v = mst_parent[v]
    return max_w


@njit(cache=True)
def subgradient_alpha_jit(
    n: int,
    knn_indices: NDArray[np.int32],
    knn_dists: NDArray[np.float64],
    coords: NDArray[np.float64],
    n_iters: int = 50,
):
    """
    Субградиентная оптимизация 1-tree → alpha-values для k-NN рёбер.

    Алгоритм Held-Karp:
    1. pi = 0 (Lagrangian multipliers)
    2. Итеративно: MST на D_pi → степени вершин → pi += step*(degree-2)
    3. alpha[i][j] = D_pi[i][j] - bottleneck_path(i,j) на MST

    Returns:
        alpha: float64[n, k] — alpha-value для каждого k-NN ребра
        pi: float64[n] — финальные Lagrangian multipliers
    """
    k = knn_indices.shape[1]
    n_edges = n * k

    # Массивы рёбер (sparse k-NN graph)
    edges_from = np.empty(n_edges, dtype=np.int32)
    edges_to = np.empty(n_edges, dtype=np.int32)
    edges_base_weight = np.empty(n_edges, dtype=np.float64)
    edges_pi_weight = np.empty(n_edges, dtype=np.float64)

    idx = 0
    for i in range(n):
        for ki in range(k):
            edges_from[idx] = np.int32(i)
            edges_to[idx] = knn_indices[i, ki]
            edges_base_weight[idx] = knn_dists[i, ki]
            idx += 1

    pi = np.zeros(n, dtype=np.float64)
    best_lb = -1e18  # лучшая нижняя граница

    # Субградиентная оптимизация
    for it in range(n_iters):
        # Пересчёт D_pi для всех k-NN рёбер
        for e in range(n_edges):
            u = edges_from[e]
            v = edges_to[e]
            edges_pi_weight[e] = edges_base_weight[e] + pi[u] + pi[v]

        # MST на D_pi графе
        mst_parent, mst_parent_weight, mst_depth, mst_n = sparse_kruskal_mst_jit(
            n, edges_from, edges_to, edges_pi_weight,
        )

        # Степени вершин в MST
        degree = np.zeros(n, dtype=np.int64)
        for i in range(n):
            p = mst_parent[i]
            if p != i:  # не корень
                degree[i] += 1
                degree[p] += 1

        # Нижняя граница: sum(MST edges) + 2*sum(pi) - sum(pi*(degree-2)) упрощается
        mst_cost = 0.0
        for i in range(n):
            if mst_parent[i] != i:
                mst_cost += mst_parent_weight[i]
        lb = mst_cost - 2.0 * np.sum(pi)
        if lb > best_lb:
            best_lb = lb

        # Субградиент: g[i] = degree[i] - 2
        grad_norm_sq = 0.0
        for i in range(n):
            g = float(degree[i]) - 2.0
            grad_norm_sq += g * g

        if grad_norm_sq < 1e-12:
            break  # все degree = 2 → оптимальный тур!

        # Шаг: step = scale / (iter + 1)
        # Heuristic target: 1.05 * best_lb (Held-Karp)
        target = best_lb * 1.05
        step = max(0.001, (target - lb)) / grad_norm_sq
        # Clamp step для стабильности
        if step > 1.0:
            step = 1.0

        for i in range(n):
            g = float(degree[i]) - 2.0
            pi[i] += step * g

    # Финальные D_pi
    for e in range(n_edges):
        u = edges_from[e]
        v = edges_to[e]
        edges_pi_weight[e] = edges_base_weight[e] + pi[u] + pi[v]

    # Финальный MST для alpha вычисления
    mst_parent, mst_parent_weight, mst_depth, _ = sparse_kruskal_mst_jit(
        n, edges_from, edges_to, edges_pi_weight,
    )

    # Alpha-values: alpha[i][ki] = D_pi(i, knn[i][ki]) - bottleneck(i, knn[i][ki])
    alpha = np.empty((n, k), dtype=np.float64)
    for i in range(n):
        for ki in range(k):
            j = knn_indices[i, ki]
            d_pi = knn_dists[i, ki] + pi[i] + pi[j]
            btl = _bottleneck_on_path(i, j, mst_parent, mst_parent_weight, mst_depth)
            alpha[i, ki] = max(0.0, d_pi - btl)

    return alpha, pi


@njit(cache=True)
def rerank_by_alpha_jit(
    knn_indices: NDArray[np.int32],
    knn_dists: NDArray[np.float64],
    alpha: NDArray[np.float64],
):
    """
    Пересортировка k-NN списка по alpha-values (ascending).
    Города с alpha=0 (в MST) идут первыми.

    Модифицирует knn_indices и knn_dists IN-PLACE.
    """
    n = knn_indices.shape[0]
    k = knn_indices.shape[1]

    for i in range(n):
        # Простой insertion sort (k маленькое, ~20)
        for a in range(1, k):
            key_alpha = alpha[i, a]
            key_idx = knn_indices[i, a]
            key_dist = knn_dists[i, a]
            b = a - 1
            while b >= 0 and alpha[i, b] > key_alpha:
                alpha[i, b + 1] = alpha[i, b]
                knn_indices[i, b + 1] = knn_indices[i, b]
                knn_dists[i, b + 1] = knn_dists[i, b]
                b -= 1
            alpha[i, b + 1] = key_alpha
            knn_indices[i, b + 1] = key_idx
            knn_dists[i, b + 1] = key_dist


@njit(cache=True)
def augment_knn_by_alpha_jit(
    knn_indices: NDArray[np.int32],
    knn_dists: NDArray[np.float64],
    alpha: NDArray[np.float64],
    coords: NDArray[np.float64],
    mst_parent: NDArray[np.int64],
    max_extra: int = 5,
):
    """
    Расширяет k-NN списки alpha=0 рёбрами из MST (augment, НЕ replace).

    Для каждого города: находит MST-соседей (alpha≈0), которых нет в k-NN,
    и добавляет их в конец. Distance-based порядок первых k элементов сохранён.

    Returns:
        new_indices: int32[N, k+max_extra] — расширенный k-NN
        new_dists: float64[N, k+max_extra] — расстояния
        new_k: int — фактическое число столбцов (k + max_extra)
    """
    n = knn_indices.shape[0]
    k = knn_indices.shape[1]
    new_k = k + max_extra

    new_indices = np.full((n, new_k), -1, dtype=np.int32)
    new_dists = np.full((n, new_k), 1e30, dtype=np.float64)

    # Копируем оригинальный k-NN
    for i in range(n):
        for j in range(k):
            new_indices[i, j] = knn_indices[i, j]
            new_dists[i, j] = knn_dists[i, j]

    # Для каждого города собираем MST-соседей (parent и дети)
    for i in range(n):
        extra_col = k  # начинаем добавлять после k
        # Сет текущих соседей (для проверки дубликатов)
        # Используем линейный поиск (k маленькое)

        # 1. MST parent ребро
        p = mst_parent[i]
        if p >= 0 and p != i:
            already = False
            for j in range(k):
                if knn_indices[i, j] == p:
                    already = True
                    break
            if not already and extra_col < new_k:
                dx = coords[i, 0] - coords[p, 0]
                dy = coords[i, 1] - coords[p, 1]
                d = np.sqrt(dx * dx + dy * dy)
                new_indices[i, extra_col] = np.int32(p)
                new_dists[i, extra_col] = d
                extra_col += 1

        # 2. Alpha=0 рёбра из k-NN (уже в списке, пропускаем; но
        #    проверяем alpha для MST-соседей из knn других городов)
        # 3. MST дети (города у которых parent = i)
        # Дети находим через обратный обход — слишком дорого.
        # Вместо этого: смотрим alpha[i,:] и добавляем все alpha=0 что ещё не в списке
        for j in range(k):
            if alpha[i, j] < 1e-10:
                # alpha≈0 ребро уже в k-NN — оно само по себе ценное,
                # просто отмечаем что оно есть
                pass

    # Сканируем MST в обратном направлении: кто является child для каждого i
    for child in range(n):
        p = mst_parent[child]
        if p < 0 or p == child:
            continue
        # p → child: child — MST-ребро для p
        # Проверяем есть ли child в knn[p]
        already = False
        for j in range(k + max_extra):
            if new_indices[p, j] == child:
                already = True
                break
            if new_indices[p, j] < 0:
                break
        if not already:
            # Находим первый свободный слот
            slot = -1
            for j in range(k, new_k):
                if new_indices[p, j] < 0:
                    slot = j
                    break
            if slot >= 0:
                dx = coords[p, 0] - coords[child, 0]
                dy = coords[p, 1] - coords[child, 1]
                d = np.sqrt(dx * dx + dy * dy)
                new_indices[p, slot] = np.int32(child)
                new_dists[p, slot] = d

    return new_indices, new_dists, new_k


# ═══════════════════════════════════════════════════════════
#  SEQUENTIAL LK (Real Lin-Kernighan, depth 2-3)
# ═══════════════════════════════════════════════════════════

@njit(cache=True)
def lk_sequential_pass_jit(
    tour: NDArray[np.int64],
    coords: NDArray[np.float64],
    nn_indices: NDArray[np.int32],
    dlb: NDArray[np.bool_],
    max_depth: int = 3,
) -> bool:
    """
    Real Lin-Kernighan sequential exchange с positive gain criterion.

    Depth 1 = 2-opt (с DLB, как lk_opt_pass но ищет кандидатов t2).
    Depth 2 = sequential 3-opt: после первого обмена продолжаем цепочку.

    Безопасная application: на каждом уровне проверяем gain на copy тура,
    применяем только если тур реально короче.

    Модифицирует tour и dlb IN-PLACE.
    Returns: True если хотя бы одно улучшение найдено.
    """
    n = len(tour)
    k = nn_indices.shape[1]
    max_city = coords.shape[0]
    improved = False

    pos = np.empty(max_city, dtype=np.int64)
    for i in range(n):
        pos[tour[i]] = i

    k_use = min(k, 7)

    for scan_start in range(n):
        t1 = tour[scan_start]
        if dlb[t1]:
            continue

        found = False
        best_gain = 0.0
        best_i = -1
        best_j = -1

        p1 = scan_start

        # Проверяем оба ребра из t1
        for direction in range(2):
            if direction == 0:
                p2 = (p1 + 1) % n
            else:
                p2 = (p1 - 1 + n) % n

            t2 = tour[p2]
            d_x1 = dist_jit(coords, t1, t2)  # cost of removed edge (t1,t2)

            # Depth 1: стандартный 2-opt через кандидатов t2
            for ki in range(k_use):
                t3 = nn_indices[t2, ki]
                if t3 < 0 or t3 == t1 or t3 == t2:
                    continue

                d_y1 = dist_jit(coords, t2, t3)
                g1 = d_x1 - d_y1
                if g1 <= 1e-10:
                    continue  # positive gain

                p3 = pos[t3]

                # 2-opt: стандартная формула (как в lk_opt_pass)
                i_eff = min(p1, p3)
                j_eff = max(p1, p3)

                if j_eff - i_eff <= 0 or (j_eff == n - 1 and i_eff == 0):
                    continue

                a = tour[i_eff]
                b = tour[i_eff + 1]
                c = tour[j_eff]
                d_city = tour[(j_eff + 1) % n]

                old_cost = dist_jit(coords, a, b) + dist_jit(coords, c, d_city)
                new_cost = dist_jit(coords, a, c) + dist_jit(coords, b, d_city)
                gain = old_cost - new_cost

                if gain > best_gain:
                    best_gain = gain
                    best_i = i_eff
                    best_j = j_eff

            # Depth 1: также кандидаты t1 (стандартный 2-opt)
            for ki in range(k_use):
                t3 = nn_indices[t1, ki]
                if t3 < 0 or t3 == t1 or t3 == t2:
                    continue

                p3 = pos[t3]
                i_eff = min(p1, p3)
                j_eff = max(p1, p3)

                if j_eff - i_eff <= 0 or (j_eff == n - 1 and i_eff == 0):
                    continue

                a = tour[i_eff]
                b = tour[i_eff + 1]
                c = tour[j_eff]
                d_city = tour[(j_eff + 1) % n]

                old_cost = dist_jit(coords, a, b) + dist_jit(coords, c, d_city)
                new_cost = dist_jit(coords, a, c) + dist_jit(coords, b, d_city)
                gain = old_cost - new_cost

                if gain > best_gain:
                    best_gain = gain
                    best_i = i_eff
                    best_j = j_eff

        # Apply best improving move
        if best_gain > 1e-10 and best_i >= 0:
            lo = best_i + 1
            hi = best_j
            while lo < hi:
                tmp = tour[lo]
                tour[lo] = tour[hi]
                tour[hi] = tmp
                lo += 1
                hi -= 1

            for m in range(best_i + 1, best_j + 1):
                pos[tour[m]] = m
                dlb[tour[m]] = False
            dlb[tour[best_i]] = False
            dlb[tour[(best_j + 1) % n]] = False

            improved = True
            found = True

            # === Depth 2+: после успешного 2-opt, пробуем продолжить цепочку ===
            if max_depth >= 2:
                # Ребро (a, new_b) только что создано. Пробуем улучшить от new_b.
                new_b = tour[best_i + 1]  # это бывший c (после reversal)
                p_nb = best_i + 1

                for depth_extra in range(max_depth - 1):
                    extra_found = False
                    best_eg = 0.0
                    best_ei = -1
                    best_ej = -1

                    for ki in range(k_use):
                        tc = nn_indices[new_b, ki]
                        if tc < 0 or tc == new_b:
                            continue
                        pc = pos[tc]
                        ie = min(p_nb, pc)
                        je = max(p_nb, pc)
                        if je - ie <= 0 or (je == n - 1 and ie == 0):
                            continue
                        a2 = tour[ie]
                        b2 = tour[ie + 1]
                        c2 = tour[je]
                        d2 = tour[(je + 1) % n]
                        oc = dist_jit(coords, a2, b2) + dist_jit(coords, c2, d2)
                        nc = dist_jit(coords, a2, c2) + dist_jit(coords, b2, d2)
                        eg = oc - nc
                        if eg > best_eg:
                            best_eg = eg
                            best_ei = ie
                            best_ej = je

                    if best_eg > 1e-10 and best_ei >= 0:
                        lo2 = best_ei + 1
                        hi2 = best_ej
                        while lo2 < hi2:
                            tmp = tour[lo2]
                            tour[lo2] = tour[hi2]
                            tour[hi2] = tmp
                            lo2 += 1
                            hi2 -= 1
                        for m in range(best_ei + 1, best_ej + 1):
                            pos[tour[m]] = m
                            dlb[tour[m]] = False
                        dlb[tour[best_ei]] = False
                        dlb[tour[(best_ej + 1) % n]] = False

                        new_b = tour[best_ei + 1]
                        p_nb = best_ei + 1
                        extra_found = True
                    else:
                        break

        if not found:
            dlb[t1] = True

    return improved


@njit(cache=True)
def lk_sequential_coords_jit(
    tour: NDArray[np.int64],
    coords: NDArray[np.float64],
    nn_indices: NDArray[np.int32],
    max_iterations: int,
    max_no_improve: int,
    max_depth: int = 3,
) -> int:
    """
    Real sequential LK с DLB, multi-pass.

    Returns: число выполненных итераций.
    """
    max_city = coords.shape[0]
    dlb = np.zeros(max_city, dtype=np.bool_)

    no_improve = 0
    for iteration in range(max_iterations):
        if lk_sequential_pass_jit(tour, coords, nn_indices, dlb, max_depth):
            no_improve = 0
        else:
            no_improve += 1
            if no_improve >= max_no_improve:
                return iteration + 1
    return max_iterations


# ═══════════════════════════════════════════════════════════
#  V-CYCLE HELPERS
# ═══════════════════════════════════════════════════════════

@njit(cache=True)
def remap_knn_to_local_jit(
    seg_cities: NDArray[np.int64],
    global_knn: NDArray[np.int32],
    g2l: NDArray[np.int32],
    max_local_k: int,
) -> NDArray[np.int32]:
    """Ремаппит глобальные oracle.knn_indices в локальные индексы для окна V-cycle.

    seg_cities: уникальные города в окне (sorted)
    global_knn: oracle.knn_indices (N x k_global)
    g2l: dense mapping global→local, size=N, -1 для отсутствующих
    max_local_k: макс. соседей на город в результате
    """
    n_local = len(seg_cities)
    k_global = global_knn.shape[1]
    local_nn = np.full((n_local, max_local_k), -1, dtype=np.int32)

    for i in range(n_local):
        city = seg_cities[i]
        col = 0
        for ki in range(k_global):
            neighbor = global_knn[city, ki]
            if neighbor < 0:
                break
            mapped = g2l[neighbor]
            if mapped >= 0:
                local_nn[i, col] = mapped
                col += 1
                if col >= max_local_k:
                    break
    return local_nn


# ═══════════════════════════════════════════════════════════
#  WARMUP
# ═══════════════════════════════════════════════════════════

HAS_NUMBA_SPARSE = True

def warmup_sparse():
    """Прогрев всех JIT функций на мини-инстансе."""
    n = 10
    coords = np.random.rand(n, 2).astype(np.float64)
    nn_idx = np.zeros((n, 3), dtype=np.int32)
    nn_dist = np.zeros((n, 3), dtype=np.float64)
    
    # Простые k-NN
    for i in range(n):
        dists = []
        for j in range(n):
            if i != j:
                d = np.sqrt((coords[i,0]-coords[j,0])**2 + (coords[i,1]-coords[j,1])**2)
                dists.append((d, j))
        dists.sort()
        for ki in range(min(3, len(dists))):
            nn_idx[i, ki] = dists[ki][1]
            nn_dist[i, ki] = dists[ki][0]
    
    tour = np.arange(n, dtype=np.int64)
    
    # Прогрев
    _ = dist_jit(coords, 0, 1)
    _ = tour_length_coords_jit(tour, coords)
    _ = nn_tour_coords_jit(coords, nn_idx, nn_dist, 0)
    _ = two_opt_pass_nn_coords_jit(tour.copy(), coords, nn_idx)
    _ = three_opt_full_pass_coords_jit(tour.copy(), coords, nn_idx)
    _ = or_opt_pass_coords_jit(tour.copy(), coords, nn_idx)
    _ = double_bridge_coords_jit(tour)
    # LK-style 2-opt с DLB
    dlb = np.zeros(n, dtype=np.bool_)
    _ = lk_opt_pass_coords_jit(tour.copy(), coords, nn_idx, dlb)
    _ = lk_opt_coords_jit(tour.copy(), coords, nn_idx, 2, 1)
    # Alpha-nearness
    alpha, pi = subgradient_alpha_jit(n, nn_idx, nn_dist, coords, 2)
    rerank_by_alpha_jit(nn_idx.copy(), nn_dist.copy(), alpha.copy())
    # Sequential LK
    dlb_test = np.zeros(n, dtype=np.bool_)
    _ = lk_sequential_pass_jit(tour.copy(), coords, nn_idx, dlb_test, 2)
    _ = lk_sequential_coords_jit(tour.copy(), coords, nn_idx, 1, 1, 2)
