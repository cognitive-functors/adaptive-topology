"""
Hierarchical Decomposition для Ultra-Scale TSP (N=30K-200K).

Рекурсивная спектральная декомпозиция:
- LOCAL Laplacians per subgraph (не global eigenvector slicing)
- Adaptive branching: bisect vs quadrisect (spectral gap ratio)
- Stop criterion: leaf ≤ max_leaf_size (default 1000)
- Stitching: k-NN cross-edges → meta-TSP → boundary polish

| N      | Levels | Branching | Leaf size  |
|--------|--------|-----------|------------|
| 34K    | 3      | quad      | ~530       |
| 100K   | 3-4    | adaptive  | 800-1500   |
| 200K   | 4      | adaptive  | 780-1250   |
"""

from __future__ import annotations

import numpy as np
from numpy.typing import NDArray
from typing import Optional
from dataclasses import dataclass, field
from scipy.spatial import cKDTree
from scipy.sparse import csr_matrix, diags
from scipy.sparse.linalg import lobpcg, eigsh

import warnings
warnings.filterwarnings('ignore', message='.*Exited.*', category=UserWarning)

from src.core.distance_oracle import DistanceOracle
from src.core.numba_sparse import (
    tour_length_coords_jit, nn_tour_coords_jit,
    two_opt_nn_coords_jit, three_opt_full_pass_coords_jit,
    or_opt_pass_coords_jit, dist_jit,
    lk_opt_coords_jit, double_bridge_coords_jit,
    remap_knn_to_local_jit,
)

# V-cycle адаптивные константы
_STITCH_RATIO_LOW = 0.05    # хороший stitch, минимальный V-cycle
_STITCH_RATIO_HIGH = 0.15   # плохой stitch, агрессивный V-cycle
_STRESS_FACTOR_HIGH = 3.0   # ребро 3x медианы → увеличенное окно
_STRESS_FACTOR_MED = 2.0    # ребро 2x медианы → слегка увеличенное окно


# ═══════════════════════════════════════════════════════════
#  HIER NODE
# ═══════════════════════════════════════════════════════════

@dataclass
class HierNode:
    """Узел иерархического дерева декомпозиции."""
    cities: NDArray[np.int64]       # индексы городов в этом кластере
    children: list[HierNode] = field(default_factory=list)
    level: int = 0
    tour: Optional[NDArray[np.int64]] = None      # локальный тур (для листьев)
    tour_length: float = float('inf')
    boundary_cities: Optional[NDArray[np.int64]] = None  # города на границе

    @property
    def is_leaf(self) -> bool:
        return len(self.children) == 0

    @property
    def n(self) -> int:
        return len(self.cities)


# ═══════════════════════════════════════════════════════════
#  SPECTRAL BISECTION / QUADRISECTION
# ═══════════════════════════════════════════════════════════

def _build_local_laplacian(
    coords: NDArray[np.float64],
    cities: NDArray[np.int64],
    knn_k: int = 15,
    sigma: str = 'auto',
) -> csr_matrix:
    """Строим sparse Laplacian для подграфа cities."""
    local_coords = coords[cities]
    n = len(cities)

    if n <= knn_k + 1:
        # Слишком маленький подграф — полный граф
        D_local = np.sqrt(((local_coords[:, None] - local_coords[None, :]) ** 2).sum(axis=2))
        if sigma == 'auto':
            s = np.median(D_local[D_local > 0])
        else:
            s = float(sigma)
        W = np.exp(-D_local ** 2 / (2 * s * s))
        np.fill_diagonal(W, 0)
        D_diag = np.diag(W.sum(axis=1))
        return csr_matrix(D_diag - W)

    # KD-tree для локальных координат
    tree = cKDTree(local_coords)
    k_actual = min(knn_k, n - 1)
    dists, indices = tree.query(local_coords, k=k_actual + 1)

    # Sigma: медиана k-NN расстояний
    if sigma == 'auto':
        s = float(np.median(dists[:, 1:]))
    else:
        s = float(sigma)
    s = max(s, 1e-10)

    # Sparse weight matrix (symmetrized)
    rows, cols, vals = [], [], []
    for i in range(n):
        for j_idx in range(1, k_actual + 1):
            j = indices[i, j_idx]
            d = dists[i, j_idx]
            w = np.exp(-d * d / (2 * s * s))
            rows.append(i)
            cols.append(j)
            vals.append(w)

    W = csr_matrix((vals, (rows, cols)), shape=(n, n))
    W = (W + W.T) / 2  # симметризация

    # Laplacian: D - W
    deg = np.array(W.sum(axis=1)).flatten()
    D_sparse = diags(deg)
    L = D_sparse - W
    return L


def _spectral_partition(
    coords: NDArray[np.float64],
    cities: NDArray[np.int64],
    n_parts: int = 2,
    knn_k: int = 15,
) -> list[NDArray[np.int64]]:
    """
    Спектральная партиция подграфа на n_parts частей.
    Используем Fiedler vector (2-я собственная) для bisection,
    или первые k собственных для k-way partition.
    """
    n = len(cities)

    if n <= 4:
        return [cities]

    L = _build_local_laplacian(coords, cities, knn_k=knn_k)

    # Вычисляем собственные вектора
    n_eig = min(n_parts + 1, n - 2)
    if n_eig < 2:
        return [cities]

    try:
        if n < 200:
            # Маленький — dense eigensolver
            L_dense = L.toarray()
            eigenvalues, eigenvectors = np.linalg.eigh(L_dense)
        else:
            # LOBPCG для sparse
            rng = np.random.RandomState(42)
            X0 = rng.randn(n, n_eig)
            X0[:, 0] = 1.0 / np.sqrt(n)

            diag_L = np.array(L.diagonal()).flatten()
            diag_L[diag_L < 1e-10] = 1.0
            M_inv = diags(1.0 / diag_L)

            try:
                eigenvalues, eigenvectors = lobpcg(
                    L, X0, M=M_inv, tol=1e-6, maxiter=200,
                    largest=False, verbosityLevel=0,
                )
            except Exception:
                # Fallback: ARPACK
                eigenvalues, eigenvectors = eigsh(L, k=n_eig, which='SM')

        # Сортировка по eigenvalue
        order = np.argsort(eigenvalues)
        eigenvalues = eigenvalues[order]
        eigenvectors = eigenvectors[:, order]

    except Exception:
        # Fallback: случайная partition
        idx = np.arange(n)
        np.random.shuffle(idx)
        chunk = n // n_parts
        parts = []
        for p in range(n_parts):
            start = p * chunk
            end = n if p == n_parts - 1 else (p + 1) * chunk
            parts.append(cities[idx[start:end]])
        return parts

    if n_parts == 2:
        # Bisection по Fiedler vector
        fiedler = eigenvectors[:, 1]
        median = np.median(fiedler)
        mask = fiedler <= median
        part_a = cities[mask]
        part_b = cities[~mask]
        # Балансировка: разница не более 20%
        if len(part_a) == 0 or len(part_b) == 0:
            half = n // 2
            sorted_idx = np.argsort(fiedler)
            part_a = cities[sorted_idx[:half]]
            part_b = cities[sorted_idx[half:]]
        return [part_a, part_b]
    else:
        # k-way: k-means на спектральных координатах
        # Используем eigenvectors 1..n_parts-1 как features
        features = eigenvectors[:, 1:n_parts]
        return _kmeans_partition(cities, features, n_parts)


def _spatial_partition(
    coords: NDArray[np.float64],
    cities: NDArray[np.int64],
    n_parts: int = 2,
) -> list[NDArray[np.int64]]:
    """
    KD-tree-style spatial bisection/quadrisection.
    Разрезает по медиане самого длинного измерения bbox.
    Гарантирует balanced partition (50/50 ± 1) для любых данных.
    Для n_parts=4: рекурсивная bisection → quadrisection.
    """
    n = len(cities)
    if n <= 4:
        return [cities]

    local_coords = coords[cities]

    if n_parts == 2:
        return _spatial_bisect(local_coords, cities)
    else:
        # Quadrisection: bisect → bisect каждую половину
        parts_2 = _spatial_bisect(local_coords, cities)
        result = []
        for part in parts_2:
            if len(part) > 4:
                sub_coords = coords[part]
                sub_parts = _spatial_bisect(sub_coords, part)
                result.extend(sub_parts)
            else:
                result.append(part)
        return result


def _spatial_bisect(
    local_coords: NDArray[np.float64],
    cities: NDArray[np.int64],
) -> list[NDArray[np.int64]]:
    """Bisection по медиане самого длинного измерения."""
    # Определяем самое длинное измерение bbox
    bbox_range = local_coords.max(axis=0) - local_coords.min(axis=0)
    split_dim = int(np.argmax(bbox_range))

    # Сортируем по этому измерению и делим пополам по медиане
    values = local_coords[:, split_dim]
    sorted_idx = np.argsort(values)
    mid = len(sorted_idx) // 2

    part_a = cities[sorted_idx[:mid]]
    part_b = cities[sorted_idx[mid:]]

    return [part_a, part_b]


def _kmeans_partition(
    cities: NDArray[np.int64],
    features: NDArray[np.float64],
    k: int,
    max_iter: int = 30,
) -> list[NDArray[np.int64]]:
    """Simple k-means на спектральных координатах."""
    n = len(cities)
    rng = np.random.RandomState(42)

    # Инициализация: k-means++
    centers = np.empty((k, features.shape[1]))
    first = rng.randint(n)
    centers[0] = features[first]

    for c in range(1, k):
        dists = np.min([np.sum((features - centers[j]) ** 2, axis=1) for j in range(c)], axis=0)
        probs = dists / dists.sum()
        idx = rng.choice(n, p=probs)
        centers[c] = features[idx]

    # Итерации
    labels = np.zeros(n, dtype=np.int64)
    for _ in range(max_iter):
        # Assign
        dists_to_centers = np.array([
            np.sum((features - centers[c]) ** 2, axis=1) for c in range(k)
        ])
        new_labels = np.argmin(dists_to_centers, axis=0)

        if np.array_equal(new_labels, labels):
            break
        labels = new_labels

        # Update centers
        for c in range(k):
            mask = labels == c
            if mask.any():
                centers[c] = features[mask].mean(axis=0)

    # Формируем партиции
    parts = []
    for c in range(k):
        mask = labels == c
        if mask.any():
            parts.append(cities[mask])

    # Если какие-то кластеры пусты — merge
    if len(parts) < k:
        return parts if parts else [cities]

    return parts


# ═══════════════════════════════════════════════════════════
#  RECURSIVE DECOMPOSITION
# ═══════════════════════════════════════════════════════════

def decompose(
    coords: NDArray[np.float64],
    max_leaf_size: int = 1000,
    min_leaf_size: int = 50,
    knn_k: int = 15,
    spectral_gap_threshold: float = 1.5,
    use_spectral: bool = False,
) -> HierNode:
    """
    Рекурсивная декомпозиция (spectral или spatial).

    Алгоритм:
    1. Если N ≤ max_leaf_size → лист
    2. use_spectral=True → Laplacian spectral partition (для clustered instances)
    3. use_spectral=False → spatial KD-tree partition (для uniform/mixed)
    4. Рекурсия для каждой части

    Args:
        coords: координаты всех городов [N, 2]
        max_leaf_size: макс. размер листа
        min_leaf_size: мин. размер (не разбиваем дальше)
        knn_k: k для k-NN при построении Laplacian
        spectral_gap_threshold: порог для bisect vs quad
        use_spectral: True = spectral partition, False = spatial partition

    Returns:
        HierNode — корень дерева
    """
    all_cities = np.arange(len(coords), dtype=np.int64)
    root = _decompose_recursive(
        coords, all_cities, 0,
        max_leaf_size, min_leaf_size, knn_k, spectral_gap_threshold,
        use_spectral,
    )
    return root


def _decompose_recursive(
    coords: NDArray[np.float64],
    cities: NDArray[np.int64],
    level: int,
    max_leaf_size: int,
    min_leaf_size: int,
    knn_k: int,
    gap_threshold: float,
    use_spectral: bool = False,
) -> HierNode:
    """Рекурсивный шаг декомпозиции."""
    node = HierNode(cities=cities, level=level)
    n = len(cities)

    # База: лист
    if n <= max_leaf_size:
        return node

    # Стратегия разбиения определяется роутером через use_spectral параметр.
    # Spectral: улавливает кластерную структуру, но дорого и на uniform вырождается.
    # Spatial: быстро O(N log N), надёжно для uniform/mixed.
    # Fallback на spatial при n > 15000 (spectral слишком дорого).
    use_spatial = not use_spectral or (n > 15000)

    if use_spatial:
        # Quad для больших, bisect для средних
        n_parts = 4 if n > 4 * max_leaf_size else 2
        parts = _spatial_partition(coords, cities, n_parts=n_parts)
    else:
        # Определяем branching factor
        n_parts = _choose_branching(coords, cities, knn_k, gap_threshold)
        # Спектральная партиция
        parts = _spectral_partition(coords, cities, n_parts=n_parts, knn_k=knn_k)

        # Проверка на вырожденность: макс. часть > 80% → fallback на spatial
        max_part = max(len(p) for p in parts)
        if max_part > 0.8 * n:
            parts = _spatial_partition(coords, cities, n_parts=2)

    # Проверка: все части достаточного размера?
    valid_parts = []
    small_remainder = []
    for part in parts:
        if len(part) >= min_leaf_size:
            valid_parts.append(part)
        else:
            small_remainder.extend(part.tolist())

    # Перераспределяем маленькие кусочки
    if small_remainder and valid_parts:
        remainder = np.array(small_remainder, dtype=np.int64)
        # Ближайший к центроиду каждой valid part
        centroids = np.array([coords[p].mean(axis=0) for p in valid_parts])
        for city in remainder:
            dists = np.sum((centroids - coords[city]) ** 2, axis=1)
            best = np.argmin(dists)
            valid_parts[best] = np.append(valid_parts[best], city)

    if len(valid_parts) <= 1:
        # Не удалось разбить — лист
        return node

    # Рекурсия
    for part in valid_parts:
        child = _decompose_recursive(
            coords, part, level + 1,
            max_leaf_size, min_leaf_size, knn_k, gap_threshold,
            use_spectral,
        )
        node.children.append(child)

    return node


def _choose_branching(
    coords: NDArray[np.float64],
    cities: NDArray[np.int64],
    knn_k: int,
    gap_threshold: float,
) -> int:
    """
    Adaptive branching: bisect vs quadrisect.

    Анализируем spectral gap: λ₂/λ₃.
    - Большой gap (>threshold) → данные хорошо делятся на 2 → bisect
    - Маленький gap → лучше на 4
    """
    n = len(cities)

    # Для очень больших — всегда quad (быстрее сходимся к листьям)
    if n > 50000:
        return 4

    # Для средних — анализ spectral gap
    if n > 300:
        try:
            L = _build_local_laplacian(coords, cities, knn_k=knn_k)
            n_eig = min(5, n - 2)

            if n < 500:
                vals, _ = np.linalg.eigh(L.toarray())
                vals = np.sort(vals)
            else:
                rng = np.random.RandomState(42)
                X0 = rng.randn(n, n_eig)
                X0[:, 0] = 1.0 / np.sqrt(n)
                diag_L = np.array(L.diagonal()).flatten()
                diag_L[diag_L < 1e-10] = 1.0
                M_inv = diags(1.0 / diag_L)
                try:
                    vals, _ = lobpcg(
                        L, X0, M=M_inv, tol=1e-4, maxiter=100,
                        largest=False, verbosityLevel=0,
                    )
                    vals = np.sort(vals)
                except Exception:
                    vals, _ = eigsh(L, k=n_eig, which='SM')
                    vals = np.sort(vals)

            # Spectral gap ratio: λ₂/λ₃
            if len(vals) >= 3 and vals[2] > 1e-12:
                gap_ratio = vals[1] / vals[2] if vals[1] > 1e-12 else 0.0
                # Инвертируем: большой gap → λ₂ далеко от λ₃ → лучше bisect
                # Маленький gap → λ₂ ≈ λ₃ → данные НЕ естественно бинарны
                if gap_ratio > gap_threshold:
                    return 4  # данные не бинарные → quad
                else:
                    return 2  # хороший bisect
        except Exception:
            pass

    # Default: quad для N>5000, bisect для меньших
    return 4 if n > 5000 else 2


# ═══════════════════════════════════════════════════════════
#  BOUNDARY DETECTION
# ═══════════════════════════════════════════════════════════

def find_boundary_cities(
    coords: NDArray[np.float64],
    node: HierNode,
    n_boundary: int = 20,
) -> None:
    """
    Для каждого листа находит города-границы (ближайшие к другим кластерам).
    Нужно для stitching.
    """
    if node.is_leaf:
        return

    # Рекурсия для дочерних
    for child in node.children:
        find_boundary_cities(coords, child, n_boundary)

    # Для текущего уровня: найти boundary между дочерними
    leaves = get_leaves(node)
    if len(leaves) <= 1:
        return

    for i, leaf_i in enumerate(leaves):
        if leaf_i.n == 0:
            continue
        centroid_i = coords[leaf_i.cities].mean(axis=0)
        # Находим ближайшие города к соседним кластерам
        boundary = set()
        for j, leaf_j in enumerate(leaves):
            if i == j or leaf_j.n == 0:
                continue
            # k-NN между leaf_i и leaf_j
            tree_j = cKDTree(coords[leaf_j.cities])
            coords_i = coords[leaf_i.cities]
            k_query = min(3, leaf_j.n)
            dists, _ = tree_j.query(coords_i, k=k_query)
            if k_query == 1:
                dists = dists.reshape(-1, 1)
            # Ближайшие из leaf_i к leaf_j
            min_dists = dists[:, 0]
            n_bound = min(n_boundary, len(min_dists))
            closest = np.argsort(min_dists)[:n_bound]
            for idx in closest:
                boundary.add(int(leaf_i.cities[idx]))

        leaf_i.boundary_cities = np.array(sorted(boundary), dtype=np.int64)


def get_leaves(node: HierNode) -> list[HierNode]:
    """Собирает все листья дерева."""
    if node.is_leaf:
        return [node]
    leaves = []
    for child in node.children:
        leaves.extend(get_leaves(child))
    return leaves


def tree_stats(node: HierNode, depth: int = 0) -> dict:
    """Статистика дерева декомпозиции."""
    if node.is_leaf:
        return {
            'max_depth': depth,
            'n_leaves': 1,
            'leaf_sizes': [node.n],
            'total_cities': node.n,
        }
    stats = {
        'max_depth': depth,
        'n_leaves': 0,
        'leaf_sizes': [],
        'total_cities': 0,
    }
    for child in node.children:
        child_stats = tree_stats(child, depth + 1)
        stats['max_depth'] = max(stats['max_depth'], child_stats['max_depth'])
        stats['n_leaves'] += child_stats['n_leaves']
        stats['leaf_sizes'].extend(child_stats['leaf_sizes'])
        stats['total_cities'] += child_stats['total_cities']
    return stats


# ═══════════════════════════════════════════════════════════
#  STITCHING
# ═══════════════════════════════════════════════════════════

def stitch_leaf_tours(
    coords: NDArray[np.float64],
    node: HierNode,
    oracle: DistanceOracle,
) -> NDArray[np.int64]:
    """
    Сшивка локальных туров листьев в глобальный тур.

    3 уровня:
    1. Entry/exit: boundary candidates → k-NN cross-edges
    2. Meta-TSP: порядок обхода кластеров (NN-greedy на центроидах)
    3. Boundary polish: 2-opt + 3-opt в окне вокруг стыков
    """
    leaves = get_leaves(node)
    n_leaves = len(leaves)

    if n_leaves == 0:
        return np.array([], dtype=np.int64)

    if n_leaves == 1:
        return leaves[0].tour if leaves[0].tour is not None else leaves[0].cities

    # Проверяем что у всех листьев есть тур
    for leaf in leaves:
        if leaf.tour is None:
            # Fallback: просто порядок из cities
            leaf.tour = leaf.cities.copy()

    # Шаг 1: Находим порядок обхода кластеров (meta-TSP)
    centroids = np.array([coords[leaf.cities].mean(axis=0) for leaf in leaves])
    cluster_order = _greedy_cluster_order(centroids)

    # Шаг 2: Определяем entry/exit точки для каждого кластера
    # Для каждой пары соседних кластеров: ищем ближайшую пару городов
    global_tour_parts = []

    for ci in range(n_leaves):
        leaf_curr = leaves[cluster_order[ci]]
        leaf_next = leaves[cluster_order[(ci + 1) % n_leaves]]

        tour_curr = leaf_curr.tour
        cities_next = leaf_next.cities

        # Ближайший город из curr к next
        tree_next = cKDTree(coords[cities_next])
        coords_curr_boundary = coords[tour_curr]
        dists, _ = tree_next.query(coords_curr_boundary, k=1)
        exit_local_idx = int(np.argmin(dists))

        # Ротируем тур так, чтобы exit_point был последним
        # (или entry предыдущего — первым)
        rotated = np.roll(tour_curr, -(exit_local_idx + 1))
        global_tour_parts.append(rotated)

    # Собираем глобальный тур
    global_tour = np.concatenate(global_tour_parts)

    # Шаг 3: Boundary polish
    global_tour = _boundary_polish(
        global_tour, coords, oracle, leaves, cluster_order,
    )

    return global_tour


# ═══════════════════════════════════════════════════════════
#  STITCHING V2 — Meta-TSP на boundary nodes
# ═══════════════════════════════════════════════════════════

def stitch_leaf_tours_v2(
    coords: NDArray[np.float64],
    node: HierNode,
    oracle: DistanceOracle,
) -> NDArray[np.int64]:
    """
    Сшивка V2: meta-TSP на boundary nodes + multi-candidate entry/exit + iterative boundary refinement.

    Улучшения над V1:
    1. Meta-TSP на boundary cities (не центроидах) — точнее порядок кластеров
    2. Top-5 entry/exit кандидатов для каждого перехода
    3. Iterative 2-opt на boundary windows (size 300, 3 прохода)
    4. Or-opt segment moves на стыках
    """
    leaves = get_leaves(node)
    n_leaves = len(leaves)

    if n_leaves == 0:
        return np.array([], dtype=np.int64)

    if n_leaves == 1:
        return leaves[0].tour if leaves[0].tour is not None else leaves[0].cities

    # Fallback: у всех листьев должен быть тур
    for leaf in leaves:
        if leaf.tour is None:
            leaf.tour = leaf.cities.copy()

    # ─── Шаг 1: Строим meta-graph на boundary nodes ───
    # Для каждой пары листьев: находим top-K ближайших пар городов
    K_CROSS = 5  # кандидатов на cross-edge

    # Строим KD-деревья для каждого листа
    leaf_trees = []
    for leaf in leaves:
        leaf_trees.append(cKDTree(coords[leaf.cities]))

    # Матрица расстояний между кластерами (через ближайшие boundary пары)
    # + запоминаем лучшие пары для каждого соединения
    cluster_dist = np.full((n_leaves, n_leaves), np.inf)
    # best_pairs[i][j] = list of (city_i, city_j, dist) — top-K пар
    best_pairs: dict[tuple[int, int], list[tuple[int, int, float]]] = {}

    for i in range(n_leaves):
        for j in range(i + 1, n_leaves):
            cities_i = leaves[i].cities
            cities_j = leaves[j].cities

            # Запрашиваем K ближайших из j для каждого города i
            # Но это O(N_i * K) — оптимизируем: берём boundary candidates
            # Boundary = города ближайшие к другому кластеру
            tree_j = leaf_trees[j]
            dists_to_j, idx_to_j = tree_j.query(coords[cities_i], k=1)

            # Top-K_CROSS ближайших пар
            top_k = min(K_CROSS, len(cities_i))
            best_from_i = np.argsort(dists_to_j.ravel())[:top_k]

            pairs = []
            for rank in range(top_k):
                li = int(best_from_i[rank])
                ci = int(cities_i[li])
                lj = int(idx_to_j[li].ravel()[0]) if idx_to_j.ndim > 1 else int(idx_to_j[li])
                cj = int(cities_j[lj])
                d = float(dists_to_j.ravel()[li])
                pairs.append((ci, cj, d))

            # Также проверяем из j → i (может дать лучшие пары)
            tree_i = leaf_trees[i]
            dists_to_i, idx_to_i = tree_i.query(coords[cities_j], k=1)
            best_from_j = np.argsort(dists_to_i.ravel())[:top_k]

            for rank in range(min(top_k, len(best_from_j))):
                lj = int(best_from_j[rank])
                cj = int(cities_j[lj])
                li = int(idx_to_i[lj].ravel()[0]) if idx_to_i.ndim > 1 else int(idx_to_i[lj])
                ci = int(cities_i[li])
                d = float(dists_to_i.ravel()[lj])
                pairs.append((ci, cj, d))

            # Дедупликация и сортировка
            seen = set()
            unique_pairs = []
            for ci_p, cj_p, d_p in sorted(pairs, key=lambda x: x[2]):
                key = (ci_p, cj_p)
                if key not in seen:
                    seen.add(key)
                    unique_pairs.append((ci_p, cj_p, d_p))
            unique_pairs = unique_pairs[:K_CROSS]

            best_pairs[(i, j)] = unique_pairs
            best_pairs[(j, i)] = [(cj_p, ci_p, d_p) for ci_p, cj_p, d_p in unique_pairs]

            if unique_pairs:
                cluster_dist[i, j] = unique_pairs[0][2]
                cluster_dist[j, i] = unique_pairs[0][2]

    # ─── Шаг 2: Meta-TSP на кластерах (NN-greedy + 2-opt improve) ───
    cluster_order = _meta_tsp_solve(cluster_dist, n_leaves)

    # ─── Шаг 3: Для каждого перехода выбираем лучшую entry/exit пару ───
    # entry[i] = город в кластере cluster_order[i], через который входим
    # exit[i]  = город в кластере cluster_order[i], через который выходим (к i+1)
    chosen_exit = {}   # cluster_order[i] → exit city
    chosen_entry = {}  # cluster_order[i] → entry city

    for ci in range(n_leaves):
        idx_curr = cluster_order[ci]
        idx_next = cluster_order[(ci + 1) % n_leaves]

        key = (idx_curr, idx_next)
        if key in best_pairs and best_pairs[key]:
            # Лучшая пара: exit из curr, entry в next
            exit_city, entry_city, _ = best_pairs[key][0]
            chosen_exit[idx_curr] = exit_city
            chosen_entry[idx_next] = entry_city
        else:
            # Fallback: центроид-based
            c_curr = coords[leaves[idx_curr].cities].mean(axis=0)
            c_next = coords[leaves[idx_next].cities].mean(axis=0)
            # Ближайший к next из curr
            tree_curr = leaf_trees[idx_curr]
            _, idx_exit = tree_curr.query(c_next, k=1)
            chosen_exit[idx_curr] = int(leaves[idx_curr].cities[idx_exit])
            tree_next = leaf_trees[idx_next]
            _, idx_entry = tree_next.query(c_curr, k=1)
            chosen_entry[idx_next] = int(leaves[idx_next].cities[idx_entry])

    # ─── Шаг 3b: Оптимизация entry/exit — пробуем top-5 комбинаций ───
    # Для каждого перехода: выбираем пару минимизирующую
    #   dist(exit_prev → entry_curr) + tour_traverse(entry_curr → exit_curr) + dist(exit_curr → entry_next)
    # Это NP-hard в общем, но с 5 кандидатами — полный перебор feasible
    # Упрощение: оптимизируем только direct connection cost (exit → entry)
    for ci in range(n_leaves):
        idx_curr = cluster_order[ci]
        idx_prev = cluster_order[(ci - 1) % n_leaves]
        idx_next = cluster_order[(ci + 1) % n_leaves]

        key_in = (idx_prev, idx_curr)
        key_out = (idx_curr, idx_next)

        candidates_in = best_pairs.get(key_in, [])
        candidates_out = best_pairs.get(key_out, [])

        if not candidates_in or not candidates_out:
            continue

        # Пробуем все комбинации entry × exit для этого кластера
        best_cost = np.inf
        best_entry_c = chosen_entry.get(idx_curr, candidates_in[0][1])
        best_exit_c = chosen_exit.get(idx_curr, candidates_out[0][0])

        tour_curr = leaves[idx_curr].tour
        n_curr = len(tour_curr)

        # Для оценки внутрикластерной стоимости: позиция в туре
        city_pos = {int(tour_curr[p]): p for p in range(n_curr)}

        for _, entry_c, d_in in candidates_in[:K_CROSS]:
            for exit_c, _, d_out in candidates_out[:K_CROSS]:
                # Стоимость: вход + выход + внутренний traverse
                # Traverse ≈ порядок в существующем туре (не меняем внутренний тур)
                pos_entry = city_pos.get(entry_c, -1)
                pos_exit = city_pos.get(exit_c, -1)
                if pos_entry < 0 or pos_exit < 0:
                    continue
                # Внутренний тур уже оптимизирован — стоимость traverse зависит от направления
                # Считаем длину сегмента entry → exit (в обе стороны) и берём меньшую
                if pos_entry <= pos_exit:
                    seg_len_fwd = pos_exit - pos_entry
                else:
                    seg_len_fwd = n_curr - pos_entry + pos_exit
                seg_len_rev = n_curr - seg_len_fwd

                # Приближение: traverse cost ≈ пропорционально длине сегмента
                # Точнее: считаем реальную длину обоих путей
                cost_fwd = _segment_length(tour_curr, coords, pos_entry, pos_exit, n_curr)
                cost_rev = _segment_length(tour_curr, coords, pos_exit, pos_entry, n_curr)

                traverse = min(cost_fwd, cost_rev)
                total = d_in + d_out + traverse

                if total < best_cost:
                    best_cost = total
                    best_entry_c = entry_c
                    best_exit_c = exit_c

        chosen_entry[idx_curr] = best_entry_c
        chosen_exit[idx_curr] = best_exit_c

    # ─── Шаг 4: Собираем глобальный тур ───
    global_tour_parts = []

    for ci in range(n_leaves):
        idx = cluster_order[ci]
        tour_local = leaves[idx].tour
        n_local = len(tour_local)

        entry_city = chosen_entry.get(idx)
        exit_city = chosen_exit.get(idx)

        # Находим позиции entry и exit в локальном туре
        entry_pos = -1
        exit_pos = -1
        for p in range(n_local):
            if int(tour_local[p]) == entry_city:
                entry_pos = p
            if int(tour_local[p]) == exit_city:
                exit_pos = p

        if entry_pos < 0:
            entry_pos = 0
        if exit_pos < 0:
            exit_pos = n_local - 1

        # Извлекаем сегмент entry → exit (в правильном направлении)
        # Пробуем оба направления, выбираем короче
        seg_fwd = _extract_segment(tour_local, entry_pos, exit_pos)
        seg_rev = _extract_segment(tour_local, exit_pos, entry_pos)
        # Reverse rev чтобы тоже шёл от entry к exit
        seg_rev_flipped = seg_rev[::-1].copy()

        len_fwd = _array_tour_length_open(seg_fwd, coords)
        len_rev = _array_tour_length_open(seg_rev_flipped, coords)

        if len_fwd <= len_rev:
            global_tour_parts.append(seg_fwd)
        else:
            global_tour_parts.append(seg_rev_flipped)

    global_tour = np.concatenate(global_tour_parts)

    # Проверка: все города на месте?
    if len(np.unique(global_tour)) != len(global_tour):
        # Дедупликация с восстановлением пропущенных
        global_tour = _fix_tour_duplicates(global_tour, coords, node)

    # ─── Шаг 5: Iterative boundary refinement (2-opt + or-opt на стыках) ───
    global_tour = _boundary_polish_v2(
        global_tour, coords, oracle, leaves, cluster_order,
        window=300, n_passes=3,
    )

    return global_tour


def _segment_length(
    tour: NDArray[np.int64],
    coords: NDArray[np.float64],
    start_pos: int,
    end_pos: int,
    n: int,
) -> float:
    """Длина сегмента тура от start_pos до end_pos (по часовой)."""
    length = 0.0
    pos = start_pos
    while pos != end_pos:
        next_pos = (pos + 1) % n
        dx = coords[tour[pos], 0] - coords[tour[next_pos], 0]
        dy = coords[tour[pos], 1] - coords[tour[next_pos], 1]
        length += np.sqrt(dx * dx + dy * dy)
        pos = next_pos
    return length


def _extract_segment(
    tour: NDArray[np.int64],
    start_pos: int,
    end_pos: int,
) -> NDArray[np.int64]:
    """Извлекает сегмент тура от start_pos до end_pos включительно (циклически)."""
    n = len(tour)
    if start_pos <= end_pos:
        return tour[start_pos:end_pos + 1].copy()
    else:
        # Wrap-around
        return np.concatenate([tour[start_pos:], tour[:end_pos + 1]])


def _array_tour_length_open(
    segment: NDArray[np.int64],
    coords: NDArray[np.float64],
) -> float:
    """Длина открытого пути (не замкнутого) по координатам."""
    if len(segment) < 2:
        return 0.0
    total = 0.0
    for i in range(len(segment) - 1):
        dx = coords[segment[i], 0] - coords[segment[i + 1], 0]
        dy = coords[segment[i], 1] - coords[segment[i + 1], 1]
        total += np.sqrt(dx * dx + dy * dy)
    return total


def _fix_tour_duplicates(
    tour: NDArray[np.int64],
    coords: NDArray[np.float64],
    node: HierNode,
) -> NDArray[np.int64]:
    """
    Исправляет тур с дубликатами: убирает повторы, вставляет пропущенные.
    """
    all_cities = set(int(c) for c in node.cities)
    seen = set()
    clean = []
    for c in tour:
        ci = int(c)
        if ci not in seen and ci in all_cities:
            seen.add(ci)
            clean.append(ci)

    missing = list(all_cities - seen)
    if missing:
        # Вставляем пропущенные города в ближайшие позиции
        clean_arr = np.array(clean, dtype=np.int64)
        for mc in missing:
            # Ищем ближайшую позицию вставки (минимизируем detour)
            best_pos = len(clean_arr)
            best_cost = np.inf
            mc_coord = coords[mc]

            for pos in range(len(clean_arr)):
                c_prev = clean_arr[pos - 1] if pos > 0 else clean_arr[-1]
                c_next = clean_arr[pos]
                # Detour: d(prev, mc) + d(mc, next) - d(prev, next)
                d_prev_mc = np.sqrt((coords[c_prev, 0] - mc_coord[0])**2 +
                                    (coords[c_prev, 1] - mc_coord[1])**2)
                d_mc_next = np.sqrt((mc_coord[0] - coords[c_next, 0])**2 +
                                    (mc_coord[1] - coords[c_next, 1])**2)
                d_prev_next = np.sqrt((coords[c_prev, 0] - coords[c_next, 0])**2 +
                                      (coords[c_prev, 1] - coords[c_next, 1])**2)
                cost = d_prev_mc + d_mc_next - d_prev_next
                if cost < best_cost:
                    best_cost = cost
                    best_pos = pos

            clean_arr = np.insert(clean_arr, best_pos, mc)

        return clean_arr

    return np.array(clean, dtype=np.int64)


def _meta_tsp_solve(
    dist_matrix: NDArray[np.float64],
    n: int,
) -> list[int]:
    """
    Решает meta-TSP на кластерах: NN-greedy + 2-opt improve.
    dist_matrix[i,j] = расстояние между кластерами i и j.
    """
    if n <= 3:
        # Для 2-3 кластеров: полный перебор
        if n <= 1:
            return list(range(n))
        if n == 2:
            return [0, 1]
        # n == 3: пробуем все 3 варианта
        best_order = [0, 1, 2]
        best_len = np.inf
        from itertools import permutations
        for perm in permutations(range(n)):
            length = sum(
                dist_matrix[perm[i], perm[(i + 1) % n]]
                for i in range(n)
            )
            if length < best_len:
                best_len = length
                best_order = list(perm)
        return best_order

    # NN-greedy стартуя из лучшего начала
    best_order = None
    best_len = np.inf

    for start in range(min(n, 8)):  # пробуем до 8 стартов
        visited = [False] * n
        order = [start]
        visited[start] = True

        for _ in range(n - 1):
            last = order[-1]
            best_next = -1
            best_d = np.inf
            for j in range(n):
                if not visited[j] and dist_matrix[last, j] < best_d:
                    best_d = dist_matrix[last, j]
                    best_next = j
            if best_next < 0:
                # Все посещены (не должно случиться)
                break
            order.append(best_next)
            visited[best_next] = True

        # Длина тура
        tour_len = sum(
            dist_matrix[order[i], order[(i + 1) % n]]
            for i in range(n)
        )
        if tour_len < best_len:
            best_len = tour_len
            best_order = order[:]

    # 2-opt improve на meta-уровне
    if best_order is not None and n > 3:
        improved = True
        while improved:
            improved = False
            for i in range(n - 1):
                for j in range(i + 2, n):
                    if j == n - 1 and i == 0:
                        continue  # пропускаем wrap-around edge
                    # Текущие рёбра: (i, i+1) и (j, j+1 mod n)
                    ci = best_order[i]
                    ci1 = best_order[i + 1]
                    cj = best_order[j]
                    cj1 = best_order[(j + 1) % n]

                    d_old = dist_matrix[ci, ci1] + dist_matrix[cj, cj1]
                    d_new = dist_matrix[ci, cj] + dist_matrix[ci1, cj1]

                    if d_new < d_old - 1e-10:
                        # Reverse segment [i+1 .. j]
                        best_order[i + 1:j + 1] = best_order[i + 1:j + 1][::-1]
                        improved = True

    return best_order if best_order is not None else list(range(n))


def _boundary_polish_v2(
    tour: NDArray[np.int64],
    coords: NDArray[np.float64],
    oracle: DistanceOracle,
    leaves: list[HierNode],
    cluster_order: list[int],
    window: int = 300,
    n_passes: int = 3,
) -> NDArray[np.int64]:
    """
    Iterative boundary refinement V2:
    1. 2-opt на boundary windows (size=window)
    2. Or-opt segment moves на стыках
    3. Повторить n_passes раз
    """
    n = len(tour)
    if n < 20:
        return tour

    # Строим mapping: city → cluster_id
    city_to_cluster = {}
    for ci, leaf in enumerate(leaves):
        for c in leaf.cities:
            city_to_cluster[int(c)] = ci

    tour = tour.copy()
    half_w = window // 2

    for pass_idx in range(n_passes):
        # Находим текущие позиции стыков
        stitch_positions = []
        for i in range(n):
            c1 = city_to_cluster.get(int(tour[i]), -1)
            c2 = city_to_cluster.get(int(tour[(i + 1) % n]), -1)
            if c1 != c2 and c1 >= 0 and c2 >= 0:
                stitch_positions.append(i)

        if not stitch_positions:
            break

        # Обрабатываем каждый стык
        for pos in stitch_positions:
            start = max(0, pos - half_w)
            end = min(n, pos + half_w + 1)
            seg_len = end - start

            if seg_len < 20:
                continue

            sub_tour = tour[start:end].copy()
            sub_cities = np.unique(sub_tour)

            if len(sub_cities) < 10:
                continue

            # Локальный k-NN
            local_coords = coords[sub_cities]
            k_local = min(20, len(sub_cities) - 1)
            if k_local < 2:
                continue

            local_tree = cKDTree(local_coords)
            _, local_nn = local_tree.query(local_coords, k=k_local + 1)
            local_nn = local_nn[:, 1:].astype(np.int32)

            # Mapping global → local
            city_to_local = {int(c): i for i, c in enumerate(sub_cities)}
            local_tour = np.array(
                [city_to_local[int(c)] for c in sub_tour], dtype=np.int64
            )

            # 2-opt (thorough — больше итераций)
            two_opt_nn_coords_jit(local_tour, local_coords, local_nn, 20, 5)

            # Or-opt pass
            or_opt_pass_coords_jit(local_tour, local_coords, local_nn)

            # 3-opt pass (если окно не слишком большое)
            if seg_len <= 500:
                three_opt_full_pass_coords_jit(local_tour, local_coords, local_nn)

            # Ещё один 2-opt после or-opt/3-opt
            two_opt_nn_coords_jit(local_tour, local_coords, local_nn, 10, 3)

            # Mapping back
            improved_sub = np.array(
                [sub_cities[local_tour[i]] for i in range(len(local_tour))],
                dtype=np.int64,
            )
            tour[start:end] = improved_sub

    return tour


def _greedy_cluster_order(centroids: NDArray[np.float64]) -> list[int]:
    """NN-greedy порядок обхода кластеров."""
    n = len(centroids)
    if n <= 1:
        return list(range(n))

    visited = [False] * n
    order = [0]
    visited[0] = True

    for _ in range(n - 1):
        last = order[-1]
        best_dist = float('inf')
        best_next = -1
        for j in range(n):
            if not visited[j]:
                d = float(np.sum((centroids[last] - centroids[j]) ** 2))
                if d < best_dist:
                    best_dist = d
                    best_next = j
        order.append(best_next)
        visited[best_next] = True

    return order


def _boundary_polish(
    tour: NDArray[np.int64],
    coords: NDArray[np.float64],
    oracle: DistanceOracle,
    leaves: list[HierNode],
    cluster_order: list[int],
    window: int = 150,
) -> NDArray[np.int64]:
    """
    Polish стыков между кластерами: 2-opt + 3-opt в окне.

    Для каждого стыка берём window городов вокруг точки соединения
    и применяем локальный 2-opt/3-opt.
    """
    n = len(tour)
    if n < 20:
        return tour

    # Находим позиции стыков
    city_to_cluster = {}
    for ci, leaf in enumerate(leaves):
        for c in leaf.cities:
            city_to_cluster[int(c)] = ci

    stitch_positions = []
    for i in range(n):
        c1 = city_to_cluster.get(int(tour[i]), -1)
        c2 = city_to_cluster.get(int(tour[(i + 1) % n]), -1)
        if c1 != c2 and c1 >= 0 and c2 >= 0:
            stitch_positions.append(i)

    if not stitch_positions:
        return tour

    # Для каждого стыка: локальный polish
    tour = tour.copy()
    half_w = window // 2

    for pos in stitch_positions:
        # Извлекаем окно
        start = max(0, pos - half_w)
        end = min(n, pos + half_w + 1)
        seg_len = end - start

        if seg_len < 10:
            continue

        # Локальный sub-tour
        sub_tour = tour[start:end].copy()
        sub_cities = np.unique(sub_tour)

        if len(sub_cities) < 5:
            continue

        # k-NN для локального окна
        local_coords = coords[sub_cities]
        local_tree = cKDTree(local_coords)
        k_local = min(15, len(sub_cities) - 1)
        _, local_nn = local_tree.query(local_coords, k=k_local + 1)
        local_nn = local_nn[:, 1:].astype(np.int32)

        # Mapping: global city → local index
        city_to_local = {int(c): i for i, c in enumerate(sub_cities)}
        local_tour = np.array([city_to_local[int(c)] for c in sub_tour], dtype=np.int64)

        # 2-opt на локальном
        two_opt_nn_coords_jit(local_tour, local_coords, local_nn, 10, 3)

        # Mapping back
        improved_sub = np.array([sub_cities[local_tour[i]] for i in range(len(local_tour))], dtype=np.int64)
        tour[start:end] = improved_sub

    return tour


# ═══════════════════════════════════════════════════════════
#  STITCH METRICS
# ═══════════════════════════════════════════════════════════

def compute_stitch_ratio(
    tour: NDArray[np.int64],
    coords: NDArray[np.float64],
    leaves: list,
) -> dict:
    """Метрики качества stitching: ratio, count, stress."""
    n = len(tour)

    # city → cluster mapping
    city_to_cluster = np.full(coords.shape[0], -1, dtype=np.int32)
    for ci, leaf in enumerate(leaves):
        for c in leaf.cities:
            city_to_cluster[int(c)] = ci

    stitch_count = 0
    stitch_length_sum = 0.0
    total_length = 0.0
    edge_lengths = np.empty(n, dtype=np.float64)
    stitch_edge_lengths = []

    for i in range(n):
        d = dist_jit(coords, tour[i], tour[(i + 1) % n])
        total_length += d
        edge_lengths[i] = d
        c1 = city_to_cluster[tour[i]]
        c2 = city_to_cluster[tour[(i + 1) % n]]
        if c1 != c2 and c1 >= 0 and c2 >= 0:
            stitch_count += 1
            stitch_length_sum += d
            stitch_edge_lengths.append(d)

    median_edge = float(np.median(edge_lengths))
    stitch_ratio = stitch_length_sum / total_length if total_length > 0 else 0.0
    max_stitch_stress = (
        max(stitch_edge_lengths) / median_edge
        if stitch_edge_lengths and median_edge > 1e-10
        else 1.0
    )

    return {
        'stitch_ratio': stitch_ratio,
        'stitch_count': stitch_count,
        'stitch_length': stitch_length_sum,
        'median_edge': median_edge,
        'max_stitch_stress': max_stitch_stress,
    }


# ═══════════════════════════════════════════════════════════
#  V-CYCLE REFINEMENT
# ═══════════════════════════════════════════════════════════

def v_cycle_refine(
    tour: NDArray[np.int64],
    coords: NDArray[np.float64],
    oracle: DistanceOracle,
    n_cycles: int = 2,
    segment_size: int = 2000,
    overlap: int = 200,
    leaves: Optional[list] = None,
    time_budget: float = 60.0,
    stitch_metrics: Optional[dict] = None,
) -> NDArray[np.int64]:
    """
    Boundary-focused V-cycle: оптимизирует ТОЛЬКО зоны стыков между кластерами.

    Вместо равномерного скользящего окна по всему туру:
    1. Находим позиции стыков (соседние города из разных кластеров)
    2. Окна (~segment_size) центрированы на стыках
    3. Сливаем перекрывающиеся окна
    4. Интенсивная оптимизация: 2-opt + 3-opt + or-opt + LK-ILS на каждом окне
    5. Повторяем n_cycles раз

    Если leaves не переданы — fallback на uniform sliding window.
    """
    import time as time_mod
    t_start = time_mod.perf_counter()

    n = len(tour)
    tour = tour.copy()

    # Если нет информации о листьях — fallback на старую стратегию
    if leaves is None or len(leaves) <= 1:
        return _v_cycle_uniform(tour, coords, oracle, n_cycles, segment_size, overlap)

    # Строим mapping: city → cluster_id
    city_to_cluster = np.full(coords.shape[0], -1, dtype=np.int32)
    for ci, leaf in enumerate(leaves):
        for c in leaf.cities:
            city_to_cluster[int(c)] = ci

    for cycle in range(n_cycles):
        if time_mod.perf_counter() - t_start > time_budget:
            break

        # Находим позиции стыков (boundary) + stress-edges (длинные рёбра)
        stitch_positions = []
        for i in range(n):
            c1 = city_to_cluster[tour[i]]
            c2 = city_to_cluster[tour[(i + 1) % n]]
            if c1 != c2 and c1 >= 0 and c2 >= 0:
                stitch_positions.append(i)

        # Stress-edge detection: находим top-K самых длинных рёбер
        edge_lengths = np.empty(n, dtype=np.float64)
        for i in range(n):
            edge_lengths[i] = dist_jit(coords, tour[i], tour[(i + 1) % n])
        # Top 2% длиннейших рёбер (минимум 4, максимум 20)
        n_stress = min(20, max(4, n // 50))
        stress_idx = np.argsort(edge_lengths)[-n_stress:]
        stress_positions = [int(idx) for idx in stress_idx
                          if int(idx) not in set(stitch_positions)]

        all_positions = stitch_positions + stress_positions
        if not all_positions:
            break

        # Адаптивный half_w: увеличиваем окна при высоком stress
        base_half_w = segment_size // 2
        if stitch_metrics and stitch_metrics['max_stitch_stress'] > _STRESS_FACTOR_HIGH:
            half_w = min(int(base_half_w * 1.8), n // 4)
        elif stitch_metrics and stitch_metrics['max_stitch_stress'] > _STRESS_FACTOR_MED:
            half_w = min(int(base_half_w * 1.3), n // 4)
        else:
            half_w = base_half_w
        windows = _merge_boundary_windows(all_positions, half_w, n)

        # Оптимизируем каждое окно
        for win_start, win_end in windows:
            if time_mod.perf_counter() - t_start > time_budget:
                break

            # Извлекаем линейный segment (start < end гарантировано)
            seg = tour[win_start:win_end].copy()
            seg_len = len(seg)

            if seg_len < 20:
                continue

            # Локальный k-NN через oracle remap (без cKDTree rebuild)
            seg_unique = np.unique(seg)
            if len(seg_unique) < 10:
                continue

            local_coords = coords[seg_unique]
            k_local = min(oracle.knn_k, len(seg_unique) - 1)
            if k_local < 2:
                continue

            # Dense global→local mapping
            g2l = np.full(coords.shape[0], -1, dtype=np.int32)
            for i_loc in range(len(seg_unique)):
                g2l[seg_unique[i_loc]] = i_loc

            # Ремаппим oracle k-NN в локальные индексы
            local_nn = remap_knn_to_local_jit(
                seg_unique.astype(np.int64),
                oracle.knn_indices,
                g2l,
                k_local,
            )

            local_tour = np.array([g2l[int(c)] for c in seg], dtype=np.int64)

            # Интенсивная оптимизация границы
            best_local = local_tour.copy()
            best_len = tour_length_coords_jit(best_local, local_coords)

            # 2-opt (thorough)
            two_opt_nn_coords_jit(local_tour, local_coords, local_nn, 30, 5)

            # 3-opt + or-opt
            for _ in range(3):
                imp_or = or_opt_pass_coords_jit(local_tour, local_coords, local_nn)
                imp3 = three_opt_full_pass_coords_jit(local_tour, local_coords, local_nn)
                if not imp_or and not imp3:
                    break

            cur_len = tour_length_coords_jit(local_tour, local_coords)
            if cur_len < best_len:
                best_local = local_tour.copy()
                best_len = cur_len

            # LK-ILS на границе (до 8 попыток, время сэкономлено на oracle k-NN remap)
            for _ in range(8):
                if time_mod.perf_counter() - t_start > time_budget:
                    break
                perturbed = double_bridge_coords_jit(best_local)
                lk_opt_coords_jit(perturbed, local_coords, local_nn, 30, 2)
                p_len = tour_length_coords_jit(perturbed, local_coords)
                if p_len < best_len - 1e-10:
                    best_local = perturbed
                    best_len = p_len

            # Map back (линейный segment, start < end)
            improved = np.array(
                [seg_unique[best_local[i]] for i in range(seg_len)],
                dtype=np.int64,
            )
            tour[win_start:win_end] = improved

    return tour


def _merge_boundary_windows(
    positions: list[int],
    half_w: int,
    n: int,
) -> list[tuple[int, int]]:
    """
    Группирует близкие стыки и создаёт окна для каждой группы.
    Возвращает (start, end) — индексы в туре, start < end (линейные).
    Для wrap-around окон: два линейных сегмента (hi_start, n) + (0, lo_end).
    """
    if not positions:
        return []

    sorted_pos = sorted(positions)

    # Группируем: стыки ближе half_w друг к другу → одна группа
    groups = [[sorted_pos[0]]]
    for p in sorted_pos[1:]:
        if p - groups[-1][-1] <= half_w:
            groups[-1].append(p)
        else:
            groups.append([p])

    # Проверяем wrap-around: первая и последняя группа близко через границу тура
    is_wrap_merged = False
    if len(groups) > 1:
        gap = (sorted_pos[0] + n) - sorted_pos[-1]
        if gap <= half_w:
            is_wrap_merged = True
            wrap_group = groups[-1] + groups[0]
            groups[0] = wrap_group
            groups.pop()

    windows = []
    for gi, group in enumerate(groups):
        # Для wrap-around группы: вычисляем окно с учётом цикличности
        if gi == 0 and is_wrap_merged:
            # Группа содержит позиции вокруг точки n→0
            # Позиции из конца тура и из начала
            hi_positions = [p for p in group if p > n // 2]
            lo_positions = [p for p in group if p <= n // 2]

            hi_start = min(hi_positions) - half_w if hi_positions else n - half_w
            lo_end = max(lo_positions) + half_w + 1 if lo_positions else half_w

            hi_start = max(0, hi_start)
            lo_end = min(n, lo_end)

            # Проверяем не покрывает ли всё
            if hi_start <= lo_end:
                windows.append((0, n))
                return windows

            windows.append((hi_start, n))
            if lo_end > 0:
                windows.append((0, lo_end))
        else:
            lo = min(group) - half_w
            hi = max(group) + half_w + 1

            win_size = hi - lo
            if win_size >= n:
                return [(0, n)]

            lo = max(0, lo)
            hi = min(n, hi)
            windows.append((lo, hi))

    return windows


def _v_cycle_uniform(
    tour: NDArray[np.int64],
    coords: NDArray[np.float64],
    oracle: DistanceOracle,
    n_cycles: int,
    segment_size: int,
    overlap: int,
) -> NDArray[np.int64]:
    """Fallback: равномерное скользящее окно (старая версия)."""
    n = len(tour)

    for cycle in range(n_cycles):
        offset = (cycle * segment_size // 3) % n
        pos = offset
        while pos < n + offset:
            start = pos % n
            end = min(pos + segment_size, n + offset)
            seg_len = end - pos

            if seg_len < 20:
                pos += segment_size - overlap
                continue

            if start + seg_len <= n:
                seg = tour[start:start + seg_len].copy()
            else:
                part1 = tour[start:]
                part2 = tour[:seg_len - len(part1)]
                seg = np.concatenate([part1, part2])

            seg_unique = np.unique(seg)
            if len(seg_unique) < 10:
                pos += segment_size - overlap
                continue

            local_coords = coords[seg_unique]
            k_local = min(15, len(seg_unique) - 1)
            if k_local < 2:
                pos += segment_size - overlap
                continue

            local_tree = cKDTree(local_coords)
            _, local_nn = local_tree.query(local_coords, k=k_local + 1)
            local_nn = local_nn[:, 1:].astype(np.int32)

            city_to_local = {int(c): i for i, c in enumerate(seg_unique)}
            local_tour = np.array([city_to_local[int(c)] for c in seg], dtype=np.int64)

            two_opt_nn_coords_jit(local_tour, local_coords, local_nn, 15, 3)
            three_opt_full_pass_coords_jit(local_tour, local_coords, local_nn)
            or_opt_pass_coords_jit(local_tour, local_coords, local_nn)

            improved = np.array(
                [seg_unique[local_tour[i]] for i in range(len(local_tour))],
                dtype=np.int64,
            )

            if start + seg_len <= n:
                tour[start:start + seg_len] = improved
            else:
                split = n - start
                tour[start:] = improved[:split]
                tour[:seg_len - split] = improved[split:]

            pos += segment_size - overlap

    return tour
