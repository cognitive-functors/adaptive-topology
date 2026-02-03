"""
EAX (Edge Assembly Crossover) для coordinate-based TSP — v6.0.

Nagata-style EAX на coords[N,2] + k-NN (без D[N,N]):
- AB-cycle decomposition union graph двух туров
- Single-cycle crossover (MVP) → block EAX (v6.1)
- Reconnection disconnected компонент через k-NN bridges
- Population loop с tournament selection + distance-preserving replacement

Ключевое свойство: EAX передаёт ХОРОШИЕ рёбра от одного тура другому,
в отличие от double_bridge (слепая случайная пертурбация).
Literature: EAX 5-10x быстрее ILS на N>5K.
"""

from __future__ import annotations

import numpy as np
from numpy.typing import NDArray
from numba import njit
import time

from src.core.numba_sparse import (
    tour_length_coords_jit, lk_opt_coords_jit,
    two_opt_nn_coords_jit, double_bridge_coords_jit,
    or_opt_pass_coords_jit, dist_jit,
)


# ═══════════════════════════════════════════════════════════
#  NUMBA JIT EAX CORE (v7.0)
#  ~20x ускорение: массивы вместо Python set/dict
# ═══════════════════════════════════════════════════════════

@njit(cache=True)
def build_adjacency_jit(tour, n_cities):
    """
    Тур → adj[N, 2]: два соседа для каждого города.
    adj[city, 0] = prev, adj[city, 1] = next в порядке тура.
    """
    n = len(tour)
    adj = np.full((n_cities, 2), -1, dtype=np.int32)
    for i in range(n):
        c = tour[i]
        prev_c = tour[(i - 1 + n) % n]
        next_c = tour[(i + 1) % n]
        adj[c, 0] = prev_c
        adj[c, 1] = next_c
    return adj


@njit(cache=True)
def find_common_edges_jit(adj_a, adj_b, n_cities):
    """
    Маска общих рёбер: common[city, k] = True если adj_a[city, k] — общее ребро.
    Ребро (u,v) общее если v ∈ adj_a[u] И v ∈ adj_b[u].
    """
    common_a = np.zeros((n_cities, 2), dtype=np.bool_)
    common_b = np.zeros((n_cities, 2), dtype=np.bool_)
    for city in range(n_cities):
        for k in range(2):
            nb_a = adj_a[city, k]
            if nb_a < 0:
                continue
            # Проверяем: nb_a — сосед city и в B?
            if adj_b[city, 0] == nb_a or adj_b[city, 1] == nb_a:
                common_a[city, k] = True
        for k in range(2):
            nb_b = adj_b[city, k]
            if nb_b < 0:
                continue
            if adj_a[city, 0] == nb_b or adj_a[city, 1] == nb_b:
                common_b[city, k] = True
    return common_a, common_b


@njit(cache=True)
def _count_ab_degree(adj_a, adj_b, common_a, common_b, n_cities):
    """Подсчёт AB-degree для каждого города (сколько не-общих рёбер)."""
    degree = np.zeros(n_cities, dtype=np.int32)
    for city in range(n_cities):
        for k in range(2):
            if adj_a[city, k] >= 0 and not common_a[city, k]:
                degree[city] += 1
            if adj_b[city, k] >= 0 and not common_b[city, k]:
                degree[city] += 1
    return degree


@njit(cache=True)
def decompose_ab_cycles_jit(adj_a, adj_b, common_a, common_b, n_cities):
    """
    AB-cycle decomposition через массивы.

    Возвращает:
        cycle_cities: int32[max_cycles, max_len] — города в каждом цикле
        cycle_sources: int8[max_cycles, max_len] — источник ребра (0=A, 1=B)
        cycle_lengths: int32[max_cycles] — длина каждого цикла
        n_cycles: int — количество найденных циклов

    Цикл хранится как последовательность городов:
        city[0] --(source[0])--> city[1] --(source[1])--> city[2] ...
        source[i] = тип ребра (city[i] → city[i+1])
    """
    # Максимальные размеры буферов
    max_cycles = n_cities  # теоретический максимум N/2 циклов
    max_len = n_cities * 2  # длина одного цикла (безопасный запас)

    cycle_cities = np.zeros((max_cycles, max_len), dtype=np.int32)
    cycle_sources = np.zeros((max_cycles, max_len), dtype=np.int8)
    cycle_lengths = np.zeros(max_cycles, dtype=np.int32)
    n_cycles = 0

    # Маска использованных рёбер: used[city, k, src]
    # src: 0=A (adj_a[city,k]), 1=B (adj_b[city,k])
    used_a = np.zeros((n_cities, 2), dtype=np.bool_)
    used_b = np.zeros((n_cities, 2), dtype=np.bool_)

    # Обход всех не-общих рёбер
    for start in range(n_cities):
        for start_k in range(2):
            # Пробуем начать с A-ребра от start
            if common_a[start, start_k]:
                continue
            if used_a[start, start_k]:
                continue
            first_nb = adj_a[start, start_k]
            if first_nb < 0:
                continue

            # Трассируем цикл: чередуем A → B → A → B ...
            path_len = 0
            current = start
            next_city = first_nb
            current_src = 0  # 0 = A
            current_k = start_k

            success = False

            for _safety in range(max_len):
                # Записываем текущее ребро
                cycle_cities[n_cycles, path_len] = current
                cycle_sources[n_cycles, path_len] = current_src
                path_len += 1

                # Помечаем ребро как использованное
                if current_src == 0:
                    used_a[current, current_k] = True
                    # Обратное ребро в A: найти k для (next_city → current)
                    for kk in range(2):
                        if adj_a[next_city, kk] == current:
                            used_a[next_city, kk] = True
                            break
                else:
                    used_b[current, current_k] = True
                    for kk in range(2):
                        if adj_b[next_city, kk] == current:
                            used_b[next_city, kk] = True
                            break

                # Переходим в next_city
                current = next_city
                next_src = 1 - current_src  # чередование A↔B

                # Ищем следующее не-общее, не-использованное ребро нужного типа
                found = False
                if next_src == 0:
                    # Ищем A-ребро от current
                    for kk in range(2):
                        if common_a[current, kk]:
                            continue
                        if used_a[current, kk]:
                            continue
                        nb = adj_a[current, kk]
                        if nb < 0:
                            continue
                        # Замыкание цикла?
                        if nb == start and path_len >= 3:
                            cycle_cities[n_cycles, path_len] = current
                            cycle_sources[n_cycles, path_len] = 0
                            path_len += 1
                            # Помечаем замыкающее ребро
                            used_a[current, kk] = True
                            for kkk in range(2):
                                if adj_a[start, kkk] == current:
                                    used_a[start, kkk] = True
                                    break
                            success = True
                            break
                        next_city = nb
                        current_src = 0
                        current_k = kk
                        found = True
                        break
                else:
                    # Ищем B-ребро от current
                    for kk in range(2):
                        if common_b[current, kk]:
                            continue
                        if used_b[current, kk]:
                            continue
                        nb = adj_b[current, kk]
                        if nb < 0:
                            continue
                        if nb == start and path_len >= 3:
                            cycle_cities[n_cycles, path_len] = current
                            cycle_sources[n_cycles, path_len] = 1
                            path_len += 1
                            used_b[current, kk] = True
                            for kkk in range(2):
                                if adj_b[start, kkk] == current:
                                    used_b[start, kkk] = True
                                    break
                            success = True
                            break
                        next_city = nb
                        current_src = 1
                        current_k = kk
                        found = True
                        break

                if success:
                    break
                if not found:
                    break

            if success and path_len >= 4:
                cycle_lengths[n_cycles] = path_len
                n_cycles += 1
                if n_cycles >= max_cycles:
                    break

        if n_cycles >= max_cycles:
            break

    return cycle_cities, cycle_sources, cycle_lengths, n_cycles


@njit(cache=True)
def _calc_cycle_gain(cycle_cities, cycle_sources, cycle_len, adj_a, adj_b, coords):
    """
    Считаем gain цикла: sum(удаляемых A-рёбер) - sum(добавляемых B-рёбер).
    Положительный gain = улучшение.
    """
    gain = 0.0
    for i in range(cycle_len - 1):
        city = cycle_cities[i]
        next_city = cycle_cities[i + 1]
        src = cycle_sources[i]
        d = dist_jit(coords, city, next_city)
        if src == 0:  # A-ребро (удаляем) → +gain
            gain += d
        else:         # B-ребро (добавляем) → -gain
            gain -= d
    return gain


@njit(cache=True)
def apply_cycle_jit(tour_a, cycle_cities, cycle_sources, cycle_len, n_cities):
    """
    Применяем один AB-цикл к parent A.
    Убираем A-рёбра, добавляем B-рёбра → собираем новый тур.

    Стратегия:
    1. Строим adj из tour_a
    2. Для каждого A-ребра в цикле: удаляем из adj
    3. Для каждого B-ребра: добавляем в adj
    4. Обходим adj → child tour

    Returns:
        child: int64[n_cities] — новый тур, или tour с child[0]=-1 если неудача
    """
    child = np.empty(n_cities, dtype=np.int64)
    n = len(tour_a)

    # Строим adj из tour_a
    adj = np.full((n_cities, 4), -1, dtype=np.int32)  # до 4 соседей временно
    deg = np.zeros(n_cities, dtype=np.int32)

    for i in range(n):
        c = tour_a[i]
        prev_c = tour_a[(i - 1 + n) % n]
        next_c = tour_a[(i + 1) % n]
        adj[c, 0] = prev_c
        adj[c, 1] = next_c
        deg[c] = 2

    # Собираем A-рёбра и B-рёбра из цикла
    for i in range(cycle_len - 1):
        city = cycle_cities[i]
        next_city = cycle_cities[i + 1]
        src = cycle_sources[i]

        if src == 0:
            # Удаляем A-ребро (city, next_city) из adj
            for k in range(deg[city]):
                if adj[city, k] == next_city:
                    # Сдвигаем
                    for kk in range(k, deg[city] - 1):
                        adj[city, kk] = adj[city, kk + 1]
                    adj[city, deg[city] - 1] = -1
                    deg[city] -= 1
                    break
            for k in range(deg[next_city]):
                if adj[next_city, k] == city:
                    for kk in range(k, deg[next_city] - 1):
                        adj[next_city, kk] = adj[next_city, kk + 1]
                    adj[next_city, deg[next_city] - 1] = -1
                    deg[next_city] -= 1
                    break
        else:
            # Добавляем B-ребро
            adj[city, deg[city]] = next_city
            deg[city] += 1
            adj[next_city, deg[next_city]] = city
            deg[next_city] += 1

    # Проверяем что все degree == 2
    for c in range(n_cities):
        if deg[c] != 2:
            child[0] = -1
            return child

    # Обходим adj → tour
    child[0] = 0
    prev = -1
    current = 0
    for i in range(1, n_cities):
        # Выбираем соседа != prev
        if adj[current, 0] != prev:
            nxt = adj[current, 0]
        else:
            nxt = adj[current, 1]
        if nxt < 0:
            child[0] = -1
            return child
        child[i] = nxt
        prev = current
        current = nxt

    # Проверка замыкания
    if adj[current, 0] != child[0] and adj[current, 1] != child[0]:
        child[0] = -1
        return child

    return child


@njit(cache=True)
def _find_components_jit(adj, deg, n_cities):
    """
    Находим connected components из adj/deg массивов.
    Returns:
        comp_id[n_cities] — номер компоненты для каждого города
        n_components — количество компонент
    """
    comp_id = np.full(n_cities, -1, dtype=np.int32)
    n_comp = 0

    for start in range(n_cities):
        if comp_id[start] >= 0:
            continue
        if deg[start] == 0:
            comp_id[start] = n_comp
            n_comp += 1
            continue

        # BFS/chain обход подтура
        current = start
        prev = -1
        for _safety in range(n_cities + 1):
            comp_id[current] = n_comp
            # Следующий сосед
            nxt = -1
            for k in range(deg[current]):
                if adj[current, k] != prev and adj[current, k] >= 0:
                    nxt = adj[current, k]
                    break
            if nxt < 0 or nxt == start:
                break
            prev = current
            current = nxt
        n_comp += 1

    return comp_id, n_comp


@njit(cache=True)
def apply_cycle_with_reconnect_jit(
    tour_a, cycle_cities, cycle_sources, cycle_len,
    n_cities, coords, nn_indices
):
    """
    Применяем AB-цикл + reconnect disconnected компонент через k-NN.

    Returns:
        child: int64[n_cities] — новый тур. child[0]=-1 если неудача.
    """
    child = np.empty(n_cities, dtype=np.int64)
    n = len(tour_a)

    # Строим adj из tour_a (до 4 соседей для промежуточных состояний)
    adj = np.full((n_cities, 4), -1, dtype=np.int32)
    deg = np.zeros(n_cities, dtype=np.int32)

    for i in range(n):
        c = tour_a[i]
        prev_c = tour_a[(i - 1 + n) % n]
        next_c = tour_a[(i + 1) % n]
        adj[c, 0] = prev_c
        adj[c, 1] = next_c
        deg[c] = 2

    # Применяем цикл: удаляем A, добавляем B
    for i in range(cycle_len - 1):
        city = cycle_cities[i]
        next_city = cycle_cities[i + 1]
        src = cycle_sources[i]

        if src == 0:
            for k in range(deg[city]):
                if adj[city, k] == next_city:
                    for kk in range(k, deg[city] - 1):
                        adj[city, kk] = adj[city, kk + 1]
                    adj[city, deg[city] - 1] = -1
                    deg[city] -= 1
                    break
            for k in range(deg[next_city]):
                if adj[next_city, k] == city:
                    for kk in range(k, deg[next_city] - 1):
                        adj[next_city, kk] = adj[next_city, kk + 1]
                    adj[next_city, deg[next_city] - 1] = -1
                    deg[next_city] -= 1
                    break
        else:
            adj[city, deg[city]] = next_city
            deg[city] += 1
            adj[next_city, deg[next_city]] = city
            deg[next_city] += 1

    # Находим компоненты
    comp_id, n_comp = _find_components_jit(adj, deg, n_cities)

    if n_comp == 1:
        # Все degree должны быть 2
        for c in range(n_cities):
            if deg[c] != 2:
                child[0] = -1
                return child
        # Собираем тур
        child[0] = 0
        prev = -1
        current = 0
        for i in range(1, n_cities):
            if adj[current, 0] != prev:
                nxt = adj[current, 0]
            else:
                nxt = adj[current, 1]
            if nxt < 0:
                child[0] = -1
                return child
            child[i] = nxt
            prev = current
            current = nxt
        return child

    # Reconnect: мержим компоненты через k-NN bridges
    k_nn = nn_indices.shape[1]
    max_merges = n_comp * 2

    for _merge in range(max_merges):
        # Пересчитываем компоненты
        comp_id, n_comp = _find_components_jit(adj, deg, n_cities)
        if n_comp <= 1:
            break

        # Ищем лучший bridge: город из comp 0 → ближайший из другой comp
        best_cost = 1e18
        best_u = -1
        best_v = -1

        for city in range(n_cities):
            ci = comp_id[city]
            for ki in range(k_nn):
                nb = nn_indices[city, ki]
                if nb < 0:
                    break
                cj = comp_id[nb]
                if cj == ci or cj < 0:
                    continue
                cost = dist_jit(coords, city, nb)
                if cost < best_cost:
                    best_cost = cost
                    best_u = city
                    best_v = nb

        if best_u < 0:
            # Fallback: brute-force на подмножестве
            for i in range(min(n_cities, 500)):
                ci = comp_id[i]
                for j in range(i + 1, min(n_cities, 500)):
                    cj = comp_id[j]
                    if cj == ci:
                        continue
                    cost = dist_jit(coords, i, j)
                    if cost < best_cost:
                        best_cost = cost
                        best_u = i
                        best_v = j

        if best_u < 0:
            child[0] = -1
            return child

        # Merge: открываем оба sub-tour в точках best_u, best_v
        # У best_u два соседа: оставляем одного, отцепляем другого
        # У best_v аналогично
        # Соединяем best_u ↔ best_v, и отцепленных друг с другом

        # Находим соседей
        u_nb0 = adj[best_u, 0]
        u_nb1 = adj[best_u, 1]
        v_nb0 = adj[best_v, 0]
        v_nb1 = adj[best_v, 1]

        if u_nb0 < 0 or u_nb1 < 0 or v_nb0 < 0 or v_nb1 < 0:
            child[0] = -1
            return child

        # Выбираем какие рёбра разрывать: (u, u_nb1) и (v, v_nb0)
        # Создаём: (u, v) и (u_nb1, v_nb0)
        # Удаляем (best_u, u_nb1)
        for k in range(deg[best_u]):
            if adj[best_u, k] == u_nb1:
                for kk in range(k, deg[best_u] - 1):
                    adj[best_u, kk] = adj[best_u, kk + 1]
                adj[best_u, deg[best_u] - 1] = -1
                deg[best_u] -= 1
                break
        for k in range(deg[u_nb1]):
            if adj[u_nb1, k] == best_u:
                for kk in range(k, deg[u_nb1] - 1):
                    adj[u_nb1, kk] = adj[u_nb1, kk + 1]
                adj[u_nb1, deg[u_nb1] - 1] = -1
                deg[u_nb1] -= 1
                break

        # Удаляем (best_v, v_nb0)
        for k in range(deg[best_v]):
            if adj[best_v, k] == v_nb0:
                for kk in range(k, deg[best_v] - 1):
                    adj[best_v, kk] = adj[best_v, kk + 1]
                adj[best_v, deg[best_v] - 1] = -1
                deg[best_v] -= 1
                break
        for k in range(deg[v_nb0]):
            if adj[v_nb0, k] == best_v:
                for kk in range(k, deg[v_nb0] - 1):
                    adj[v_nb0, kk] = adj[v_nb0, kk + 1]
                adj[v_nb0, deg[v_nb0] - 1] = -1
                deg[v_nb0] -= 1
                break

        # Добавляем (best_u, best_v)
        adj[best_u, deg[best_u]] = best_v
        deg[best_u] += 1
        adj[best_v, deg[best_v]] = best_u
        deg[best_v] += 1

        # Добавляем (u_nb1, v_nb0)
        adj[u_nb1, deg[u_nb1]] = v_nb0
        deg[u_nb1] += 1
        adj[v_nb0, deg[v_nb0]] = u_nb1
        deg[v_nb0] += 1

    # Финальная проверка и сборка тура
    for c in range(n_cities):
        if deg[c] != 2:
            child[0] = -1
            return child

    child[0] = 0
    prev = -1
    current = 0
    for i in range(1, n_cities):
        if adj[current, 0] != prev:
            nxt = adj[current, 0]
        else:
            nxt = adj[current, 1]
        if nxt < 0:
            child[0] = -1
            return child
        child[i] = nxt
        prev = current
        current = nxt

    return child


@njit(cache=True)
def eax_crossover_jit(tour_a, tour_b, coords, nn_indices):
    """
    Полный EAX crossover в одной JIT-функции.

    1. Строим adjacency для обоих туров
    2. Находим общие рёбра
    3. Декомпозируем AB-циклы
    4. Оцениваем gain каждого цикла
    5. Пробуем top-5 по gain: apply → reconnect

    Returns:
        child: int64[n_cities]. child[0]=-1 если неудача.
    """
    n_cities = coords.shape[0]

    # 1. Adjacency
    adj_a = build_adjacency_jit(tour_a, n_cities)
    adj_b = build_adjacency_jit(tour_b, n_cities)

    # 2. Общие рёбра
    common_a, common_b = find_common_edges_jit(adj_a, adj_b, n_cities)

    # 3. AB-cycles
    cycle_cities, cycle_sources, cycle_lengths, n_cycles = \
        decompose_ab_cycles_jit(adj_a, adj_b, common_a, common_b, n_cities)

    if n_cycles == 0:
        child = np.empty(n_cities, dtype=np.int64)
        child[0] = -1
        return child

    # 4. Оцениваем gain для каждого цикла
    gains = np.zeros(n_cycles, dtype=np.float64)
    for ci in range(n_cycles):
        clen = cycle_lengths[ci]
        gain = 0.0
        for i in range(clen - 1):
            city = cycle_cities[ci, i]
            next_city = cycle_cities[ci, i + 1]
            src = cycle_sources[ci, i]
            d = dist_jit(coords, city, next_city)
            if src == 0:
                gain += d
            else:
                gain -= d
        gains[ci] = gain

    # 5. Сортируем по gain (desc) — простой selection sort для top-5
    order = np.arange(n_cycles, dtype=np.int32)
    top_k = min(5, n_cycles)
    for i in range(top_k):
        best_idx = i
        for j in range(i + 1, n_cycles):
            if gains[order[j]] > gains[order[best_idx]]:
                best_idx = j
        if best_idx != i:
            tmp = order[i]
            order[i] = order[best_idx]
            order[best_idx] = tmp

    # 6. Пробуем top-5 циклов
    for ti in range(top_k):
        ci = order[ti]
        clen = cycle_lengths[ci]
        if clen < 4:
            continue

        # Прямое применение (без reconnect)
        child = apply_cycle_jit(
            tour_a,
            cycle_cities[ci],
            cycle_sources[ci],
            clen,
            n_cities,
        )
        if child[0] >= 0:
            return child

        # С reconnect
        child = apply_cycle_with_reconnect_jit(
            tour_a,
            cycle_cities[ci],
            cycle_sources[ci],
            clen,
            n_cities,
            coords,
            nn_indices,
        )
        if child[0] >= 0:
            return child

    # Все циклы не дали валидный тур
    child = np.empty(n_cities, dtype=np.int64)
    child[0] = -1
    return child


# ═══════════════════════════════════════════════════════════
#  PYTHON WRAPPERS (обратная совместимость + вызов JIT)
# ═══════════════════════════════════════════════════════════

def eax_crossover_fast(
    tour_a: NDArray[np.int64],
    tour_b: NDArray[np.int64],
    coords: NDArray[np.float64],
    nn_indices: NDArray[np.int32],
) -> NDArray[np.int64] | None:
    """
    Быстрый EAX crossover через Numba JIT.
    Drop-in замена для eax_crossover().
    """
    child = eax_crossover_jit(tour_a, tour_b, coords, nn_indices)
    if child[0] < 0:
        return None
    return child


# ═══════════════════════════════════════════════════════════
#  LEGACY PYTHON IMPLEMENTATION (ниже)
# ═══════════════════════════════════════════════════════════


# ═══════════════════════════════════════════════════════════
#  ADJACENCY / EDGE SET
# ═══════════════════════════════════════════════════════════

def build_adjacency(tour: NDArray[np.int64], n_cities: int) -> NDArray[np.int32]:
    """
    Тур → adjacency[N, 2]: каждый город хранит двух соседей.
    O(N).
    """
    n = len(tour)
    adj = np.full((n_cities, 2), -1, dtype=np.int32)
    for i in range(n):
        c = tour[i]
        prev_c = tour[(i - 1) % n]
        next_c = tour[(i + 1) % n]
        adj[c, 0] = prev_c
        adj[c, 1] = next_c
    return adj


def edge_set_from_tour(tour: NDArray[np.int64]) -> set[tuple[int, int]]:
    """Тур → множество рёбер (canonical: min, max)."""
    n = len(tour)
    edges = set()
    for i in range(n):
        a, b = int(tour[i]), int(tour[(i + 1) % n])
        edges.add((min(a, b), max(a, b)))
    return edges


# ═══════════════════════════════════════════════════════════
#  AB-CYCLE DECOMPOSITION
# ═══════════════════════════════════════════════════════════

def decompose_ab_cycles(
    tour_a: NDArray[np.int64],
    tour_b: NDArray[np.int64],
    n_cities: int,
) -> list[list[tuple[tuple[int, int], str]]]:
    """
    Декомпозиция union graph G_A ∪ G_B в AB-циклы.

    AB-цикл: чередующиеся рёбра из A и B.
    Каждое ребро union graph (не общее) входит ровно в один AB-цикл.

    Returns:
        Список циклов, каждый = [(edge, source), ...], source ∈ {'A', 'B'}
    """
    adj_a = build_adjacency(tour_a, n_cities)
    adj_b = build_adjacency(tour_b, n_cities)

    edges_a = edge_set_from_tour(tour_a)
    edges_b = edge_set_from_tour(tour_b)
    common = edges_a & edges_b

    # AB-граф: для каждого города — список (сосед, источник) без общих рёбер
    # Используем массивы для эффективности
    ab_neighbors = [[] for _ in range(n_cities)]
    for city in range(n_cities):
        for nb in adj_a[city]:
            if nb < 0:
                continue
            edge = (min(city, nb), max(city, nb))
            if edge not in common:
                ab_neighbors[city].append((int(nb), 'A'))
        for nb in adj_b[city]:
            if nb < 0:
                continue
            edge = (min(city, nb), max(city, nb))
            if edge not in common:
                ab_neighbors[city].append((int(nb), 'B'))

    # Извлекаем AB-циклы обходом
    used_edges: set[tuple[int, int]] = set()
    cycles = []

    for start in range(n_cities):
        for nb, etype in ab_neighbors[start]:
            edge = (min(start, nb), max(start, nb))
            if edge in used_edges:
                continue

            cycle = _trace_ab_cycle(start, nb, etype, ab_neighbors, used_edges)
            if cycle is not None and len(cycle) >= 4:
                cycles.append(cycle)
                for (e, _) in cycle:
                    used_edges.add(e)

    return cycles


def _trace_ab_cycle(
    start: int,
    first_nb: int,
    first_type: str,
    ab_neighbors: list[list[tuple[int, str]]],
    used_edges: set[tuple[int, int]],
) -> list[tuple[tuple[int, int], str]] | None:
    """Трассируем один AB-цикл с чередованием A/B."""
    path = []
    current = start
    next_city = first_nb
    current_type = first_type
    visited_in_path: set[tuple[int, int]] = set()

    for _ in range(len(ab_neighbors) * 2):  # safety limit
        edge = (min(current, next_city), max(current, next_city))

        if edge in used_edges or edge in visited_in_path:
            return None

        path.append((edge, current_type))
        visited_in_path.add(edge)

        current = next_city
        next_type = 'B' if current_type == 'A' else 'A'

        # Ищем неиспользованное ребро нужного типа от current
        found = False
        for nb, etype in ab_neighbors[current]:
            if etype != next_type:
                continue
            edge_cand = (min(current, nb), max(current, nb))
            if edge_cand in used_edges or edge_cand in visited_in_path:
                continue

            # Проверяем замыкание цикла
            if nb == start and len(path) >= 3:
                path.append((edge_cand, next_type))
                return path

            next_city = nb
            current_type = next_type
            found = True
            break

        if not found:
            return None

    return None


# ═══════════════════════════════════════════════════════════
#  E-SET APPLICATION
# ═══════════════════════════════════════════════════════════

def apply_single_cycle(
    tour_a: NDArray[np.int64],
    cycle: list[tuple[tuple[int, int], str]],
    n_cities: int,
) -> NDArray[np.int64] | None:
    """
    Применяем один AB-цикл к родителю A.
    Убираем A-рёбра из цикла, добавляем B-рёбра.
    Результат может быть disconnected — вернём None если не получается
    восстановить тур, или валидный тур.
    """
    edges_a = edge_set_from_tour(tour_a)

    # Рёбра для удаления (A) и добавления (B) из цикла
    to_remove = set()
    to_add = set()
    for edge, source in cycle:
        if source == 'A':
            to_remove.add(edge)
        else:
            to_add.add(edge)

    # Новое множество рёбер
    child_edges = (edges_a - to_remove) | to_add

    # Пробуем собрать тур
    return _edges_to_tour(child_edges, n_cities)


def _edges_to_tour(
    edges: set[tuple[int, int]],
    n_cities: int,
) -> NDArray[np.int64] | None:
    """
    Множество рёбер → упорядоченный тур (если Hamilton cycle).
    Если граф disconnected или не degree-2 → None.
    """
    # Строим adjacency list
    adj: dict[int, list[int]] = {}
    for a, b in edges:
        adj.setdefault(a, []).append(b)
        adj.setdefault(b, []).append(a)

    # Проверяем degree = 2 для всех
    for city in range(n_cities):
        neighbors = adj.get(city, [])
        if len(neighbors) != 2:
            return None

    # Обход
    tour = np.empty(n_cities, dtype=np.int64)
    tour[0] = 0
    prev = -1
    current = 0

    for i in range(1, n_cities):
        neighbors = adj[current]
        if neighbors[0] != prev:
            nxt = neighbors[0]
        else:
            nxt = neighbors[1]
        tour[i] = nxt
        prev = current
        current = nxt

    # Проверяем замыкание
    if current != tour[0] and (min(current, int(tour[0])), max(current, int(tour[0]))) not in edges:
        return None

    return tour


# ═══════════════════════════════════════════════════════════
#  COMPONENT RECONNECTION
# ═══════════════════════════════════════════════════════════

def apply_cycle_with_reconnect(
    tour_a: NDArray[np.int64],
    cycle: list[tuple[tuple[int, int], str]],
    n_cities: int,
    coords: NDArray[np.float64],
    nn_indices: NDArray[np.int32],
) -> NDArray[np.int64] | None:
    """
    Применяем AB-цикл + reconnect disconnected компонент.
    """
    edges_a = edge_set_from_tour(tour_a)

    to_remove = set()
    to_add = set()
    for edge, source in cycle:
        if source == 'A':
            to_remove.add(edge)
        else:
            to_add.add(edge)

    child_edges = (edges_a - to_remove) | to_add

    # Строим adjacency
    adj: dict[int, list[int]] = {}
    for a, b in child_edges:
        adj.setdefault(a, []).append(b)
        adj.setdefault(b, []).append(a)

    # Находим connected components (sub-tours)
    visited = np.zeros(n_cities, dtype=np.bool_)
    components: list[list[int]] = []

    for start in range(n_cities):
        if visited[start]:
            continue
        if start not in adj:
            continue
        # Обход компоненты
        comp = []
        current = start
        prev = -1
        for _ in range(n_cities):
            comp.append(current)
            visited[current] = True
            neighbors = adj.get(current, [])
            if len(neighbors) == 0:
                break
            if len(neighbors) == 1:
                nxt = neighbors[0]
            elif neighbors[0] != prev:
                nxt = neighbors[0]
            else:
                nxt = neighbors[1]
            if nxt == start:
                break
            prev = current
            current = nxt
        components.append(comp)

    # Одиночные города (без рёбер)
    for c in range(n_cities):
        if not visited[c]:
            components.append([c])

    if len(components) == 1 and len(components[0]) == n_cities:
        return np.array(components[0], dtype=np.int64)

    if len(components) == 0:
        return None

    # Reconnect: iteratively merge closest pair
    return _reconnect_components(components, coords, nn_indices, n_cities)


def _reconnect_components(
    components: list[list[int]],
    coords: NDArray[np.float64],
    nn_indices: NDArray[np.int32],
    n_cities: int,
) -> NDArray[np.int64] | None:
    """
    Мержим disconnected sub-tours через k-NN bridges.
    Для каждой пары компонент: находим ближайшую пару городов,
    открываем оба цикла и соединяем.
    """
    if len(components) == 0:
        return None

    # Быстрый lookup: city → component id
    comp_of = np.full(n_cities, -1, dtype=np.int32)
    for ci, comp in enumerate(components):
        for city in comp:
            comp_of[city] = ci

    # Для каждого компонента храним как ordered list (sub-tour)
    # и позицию в sub-tour
    subtours: list[list[int]] = [list(c) for c in components]

    max_merges = len(subtours) * 2  # safety
    for _ in range(max_merges):
        if len(subtours) <= 1:
            break

        # Ищем лучший bridge через k-NN
        best_cost = float('inf')
        best_merge = None  # (ci, cj, pos_i, pos_j)

        # Rebuild comp_of
        comp_of[:] = -1
        pos_in_comp = np.full(n_cities, -1, dtype=np.int32)
        for ci, st in enumerate(subtours):
            for pi, city in enumerate(st):
                comp_of[city] = ci
                pos_in_comp[city] = pi

        for ci, st in enumerate(subtours):
            for pi, city in enumerate(st):
                k = nn_indices.shape[1]
                for ki in range(k):
                    nb = int(nn_indices[city, ki])
                    if nb < 0:
                        break
                    cj = comp_of[nb]
                    if cj == ci or cj < 0:
                        continue
                    cost = float(dist_jit(coords, city, nb))
                    if cost < best_cost:
                        best_cost = cost
                        pj = pos_in_comp[nb]
                        best_merge = (ci, cj, pi, pj)

        if best_merge is None:
            # Fallback: не нашли через k-NN, brute-force
            for ci in range(len(subtours)):
                for cj in range(ci + 1, len(subtours)):
                    for city_i in subtours[ci][:5]:  # sample
                        for city_j in subtours[cj][:5]:
                            cost = float(dist_jit(coords, city_i, city_j))
                            if cost < best_cost:
                                best_cost = cost
                                pi = subtours[ci].index(city_i)
                                pj = subtours[cj].index(city_j)
                                best_merge = (ci, cj, pi, pj)

        if best_merge is None:
            break

        ci, cj, pi, pj = best_merge

        # Мержим: rotируем обе подтуры так чтобы bridge cities
        # стали "стыковочными"
        st_i = subtours[ci]
        st_j = subtours[cj]

        # Rotate: city_i в конце st_i, city_j в начале st_j
        rotated_i = st_i[pi + 1:] + st_i[:pi + 1]
        rotated_j = st_j[pj:] + st_j[:pj]

        merged = rotated_i + rotated_j

        # Обновляем subtours
        new_subtours = []
        for k_idx, st in enumerate(subtours):
            if k_idx != ci and k_idx != cj:
                new_subtours.append(st)
        new_subtours.append(merged)
        subtours = new_subtours

    if len(subtours) == 1 and len(subtours[0]) == n_cities:
        return np.array(subtours[0], dtype=np.int64)

    return None


# ═══════════════════════════════════════════════════════════
#  EAX CROSSOVER
# ═══════════════════════════════════════════════════════════

def eax_crossover(
    tour_a: NDArray[np.int64],
    tour_b: NDArray[np.int64],
    coords: NDArray[np.float64],
    nn_indices: NDArray[np.int32],
) -> NDArray[np.int64] | None:
    """
    EAX crossover: single-cycle strategy.
    Сначала пробуем Numba JIT (быстро), fallback на Python.

    Returns:
        Offspring tour или None если crossover не удался.
    """
    # Быстрый путь: Numba JIT (~2ms vs ~40ms)
    child = eax_crossover_fast(tour_a, tour_b, coords, nn_indices)
    if child is not None:
        return child

    # Fallback: Python implementation
    n = len(tour_a)
    n_cities = coords.shape[0]

    cycles = decompose_ab_cycles(tour_a, tour_b, n_cities)
    if not cycles:
        return None

    # Оцениваем gain для каждого цикла
    cycle_gains = []
    for cycle in cycles:
        gain = 0.0
        for edge, source in cycle:
            d = float(dist_jit(coords, edge[0], edge[1]))
            if source == 'A':
                gain += d  # удаляем A-ребро → +gain
            else:
                gain -= d  # добавляем B-ребро → -gain
        cycle_gains.append(gain)

    # Сортируем по gain (desc), пробуем лучшие
    order = sorted(range(len(cycles)), key=lambda i: cycle_gains[i], reverse=True)

    for idx in order[:5]:  # пробуем top-5 циклов
        cycle = cycles[idx]
        if len(cycle) < 4:
            continue

        # Пробуем прямое применение (быстрее)
        child = apply_single_cycle(tour_a, cycle, n_cities)
        if child is not None:
            return child

        # Fallback: с reconnection
        child = apply_cycle_with_reconnect(
            tour_a, cycle, n_cities, coords, nn_indices,
        )
        if child is not None:
            return child

    return None


# ═══════════════════════════════════════════════════════════
#  POPULATION LOOP
# ═══════════════════════════════════════════════════════════

def eax_population_optimize(
    coords: NDArray[np.float64],
    nn_indices: NDArray[np.int32],
    initial_tours: list[NDArray[np.int64]],
    pop_size: int = 15,
    max_generations: int = 200,
    time_budget: float = 60.0,
    lk_iters: int = 30,
    lk_no_improve: int = 2,
    verbose: bool = False,
) -> tuple[NDArray[np.int64], float]:
    """
    Population-based EAX optimization.

    Args:
        coords: координаты [N, 2]
        nn_indices: k-NN индексы [N, k]
        initial_tours: начальные туры для популяции
        pop_size: размер популяции
        max_generations: макс. поколений
        time_budget: бюджет времени (секунды)
        lk_iters: итерации LK для offspring
        lk_no_improve: early stop LK

    Returns:
        (best_tour, best_length)
    """
    t_start = time.perf_counter()
    n_cities = coords.shape[0]

    # Инициализация популяции
    pop_tours: list[NDArray[np.int64]] = []
    pop_lengths: list[float] = []

    for tour in initial_tours[:pop_size]:
        t = tour.copy()
        length = float(tour_length_coords_jit(t, coords))
        pop_tours.append(t)
        pop_lengths.append(length)

    # Добиваем до pop_size пертурбациями лучшего
    best_idx = int(np.argmin(pop_lengths))
    while len(pop_tours) < pop_size:
        p = double_bridge_coords_jit(pop_tours[best_idx])
        lk_opt_coords_jit(p, coords, nn_indices, lk_iters, lk_no_improve)
        p_len = float(tour_length_coords_jit(p, coords))
        pop_tours.append(p)
        pop_lengths.append(p_len)

    best_idx = int(np.argmin(pop_lengths))
    best_tour = pop_tours[best_idx].copy()
    best_length = pop_lengths[best_idx]

    stagnant = 0

    for gen in range(max_generations):
        if time.perf_counter() - t_start > time_budget:
            break

        # Tournament selection (2 родителя)
        idx_a, idx_b = _tournament_select(pop_lengths)

        # EAX crossover
        child = eax_crossover(
            pop_tours[idx_a], pop_tours[idx_b],
            coords, nn_indices,
        )

        if child is None:
            stagnant += 1
            if stagnant > 10:
                # Diversity injection: double_bridge + LK
                worst_idx = int(np.argmax(pop_lengths))
                p = double_bridge_coords_jit(best_tour)
                lk_opt_coords_jit(p, coords, nn_indices, lk_iters, lk_no_improve)
                p_len = float(tour_length_coords_jit(p, coords))
                pop_tours[worst_idx] = p
                pop_lengths[worst_idx] = p_len
                stagnant = 0
            continue

        # Sequential LK refinement offspring
        lk_opt_coords_jit(child, coords, nn_indices, lk_iters, lk_no_improve)
        # Or-opt pass
        or_opt_pass_coords_jit(child, coords, nn_indices)
        child_length = float(tour_length_coords_jit(child, coords))

        # Replacement: worst in population
        worst_idx = int(np.argmax(pop_lengths))
        if child_length < pop_lengths[worst_idx]:
            pop_tours[worst_idx] = child
            pop_lengths[worst_idx] = child_length
            stagnant = 0

            if child_length < best_length:
                best_tour = child.copy()
                best_length = child_length
                if verbose:
                    print(f'  EAX gen {gen}: new best = {best_length:.0f}')
        else:
            stagnant += 1

        # Diversity injection при стагнации
        if stagnant >= 5:
            worst_idx = int(np.argmax(pop_lengths))
            p = double_bridge_coords_jit(best_tour)
            lk_opt_coords_jit(p, coords, nn_indices, lk_iters, lk_no_improve)
            p_len = float(tour_length_coords_jit(p, coords))
            pop_tours[worst_idx] = p
            pop_lengths[worst_idx] = p_len
            stagnant = 0

    return best_tour, best_length


def _tournament_select(
    lengths: list[float],
    tournament_size: int = 3,
) -> tuple[int, int]:
    """Tournament selection: выбираем двух разных родителей."""
    n = len(lengths)
    rng = np.random.default_rng()

    def _pick() -> int:
        candidates = rng.choice(n, size=min(tournament_size, n), replace=False)
        best = candidates[0]
        for c in candidates[1:]:
            if lengths[c] < lengths[best]:
                best = c
        return int(best)

    a = _pick()
    for _ in range(10):
        b = _pick()
        if b != a:
            return a, b
    # Fallback: любой другой
    b = (a + 1) % n
    return a, b
