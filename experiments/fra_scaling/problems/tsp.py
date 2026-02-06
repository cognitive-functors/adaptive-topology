"""
TSP (Traveling Salesman Problem) implementation for FRA scaling experiment.
"""

import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
import requests
import re
from .base import Problem, Instance, FeatureExtractor


class TSPProblem(Problem):
    """Traveling Salesman Problem."""

    name = "tsp"

    # TSPLIB instances with known optimal solutions
    TSPLIB_OPTIMA = {
        "a280": 2579, "ali535": 202339, "att48": 10628, "att532": 27686,
        "bayg29": 1610, "bays29": 2020, "berlin52": 7542, "bier127": 118282,
        "brazil58": 25395, "brd14051": 469385, "brg180": 1950, "burma14": 3323,
        "ch130": 6110, "ch150": 6528, "d198": 15780, "d493": 35002,
        "d657": 48912, "d1291": 50801, "d1655": 62128, "d2103": 80450,
        "d15112": 1573084, "d18512": 645238, "dantzig42": 699, "dsj1000": 18659688,
        "eil51": 426, "eil76": 538, "eil101": 629, "fl417": 11861,
        "fl1400": 20127, "fl1577": 22249, "fl3795": 28772, "fnl4461": 182566,
        "fri26": 937, "gil262": 2378, "gr17": 2085, "gr21": 2707,
        "gr24": 1272, "gr48": 5046, "gr96": 55209, "gr120": 6942,
        "gr137": 69853, "gr202": 40160, "gr229": 134602, "gr431": 171414,
        "gr666": 294358, "hk48": 11461, "kroA100": 21282, "kroB100": 22141,
        "kroC100": 20749, "kroD100": 21294, "kroE100": 22068, "kroA150": 26524,
        "kroB150": 26130, "kroA200": 29368, "kroB200": 29437, "lin105": 14379,
        "lin318": 42029, "linhp318": 41345, "nrw1379": 56638, "p654": 34643,
        "pa561": 2763, "pcb442": 50778, "pcb1173": 56892, "pcb3038": 137694,
        "pla7397": 23260728, "pla33810": 66048945, "pla85900": 142382641,
        "pr76": 108159, "pr107": 44303, "pr124": 59030, "pr136": 96772,
        "pr144": 58537, "pr152": 73682, "pr226": 80369, "pr264": 49135,
        "pr299": 48191, "pr439": 107217, "pr1002": 259045, "pr2392": 378032,
        "rat99": 1211, "rat195": 2323, "rat575": 6773, "rat783": 8806,
        "rd100": 7910, "rd400": 15281, "rl1304": 252948, "rl1323": 270199,
        "rl1889": 316536, "rl5915": 565530, "rl5934": 556045, "rl11849": 923288,
        "si175": 21407, "si535": 48450, "si1032": 92650, "st70": 675,
        "swiss42": 1273, "ts225": 126643, "tsp225": 3916, "u159": 42080,
        "u574": 36905, "u724": 41910, "u1060": 224094, "u1432": 152970,
        "u1817": 57201, "u2152": 64253, "u2319": 234256, "ulysses16": 6859,
        "ulysses22": 7013, "usa13509": 19982859, "vm1084": 239297,
        "vm1748": 336556,
    }

    def load_instances(self, source: str, count: int) -> List[Instance]:
        """Load or generate TSP instances."""
        instances = []

        if source == "tsplib":
            # Пробуем скачать с TSPLIB, если не получается - генерируем случайные
            cache_dir = Path(__file__).parent.parent / "data" / "tsplib"
            cache_dir.mkdir(parents=True, exist_ok=True)

            failed_downloads = 0
            for name, opt in list(self.TSPLIB_OPTIMA.items())[:count]:
                instance_file = cache_dir / f"{name}.tsp"

                if not instance_file.exists():
                    try:
                        self._download_tsplib(name, cache_dir)
                    except Exception as e:
                        print(f"  Skipping {name}: {e}")
                        failed_downloads += 1
                        # Если много ошибок - сервер недоступен
                        if failed_downloads >= 5:
                            print(f"  TSPLIB server unavailable, switching to random generation")
                            break
                        continue

                if instance_file.exists():
                    coords = self._parse_tsp_file(instance_file)
                    if coords is not None:
                        instances.append(Instance(
                            id=name,
                            data=coords,
                            optimal_value=float(opt),
                            metadata={"source": "tsplib", "n": len(coords)}
                        ))

            # Если недостаточно инстансов - догенерируем случайные
            if len(instances) < count:
                print(f"  Loaded {len(instances)} from TSPLIB, generating {count - len(instances)} random instances")
                instances.extend(self._generate_random_instances(count - len(instances), start_id=len(instances)))

        elif source == "random":
            instances = self._generate_random_instances(count)

        return instances

    def _generate_random_instances(self, count: int, start_id: int = 0) -> List[Instance]:
        """Generate random TSP instances with various structures."""
        instances = []
        np.random.seed(42 + start_id)  # Воспроизводимость

        # Разные размеры и структуры
        sizes = [20, 30, 50, 75, 100, 150, 200]
        structures = ["uniform", "clustered", "grid", "circular"]

        for i in range(count):
            n = sizes[i % len(sizes)]
            structure = structures[i % len(structures)]
            instance_id = f"random_{structure}_{n}_{start_id + i}"

            if structure == "uniform":
                coords = np.random.rand(n, 2) * 1000
            elif structure == "clustered":
                # 3-5 кластеров
                n_clusters = np.random.randint(3, 6)
                centers = np.random.rand(n_clusters, 2) * 1000
                coords = []
                for _ in range(n):
                    c = centers[np.random.randint(n_clusters)]
                    coords.append(c + np.random.randn(2) * 50)
                coords = np.array(coords)
            elif structure == "grid":
                # Возмущённая сетка
                side = int(np.ceil(np.sqrt(n)))
                coords = []
                for x in range(side):
                    for y in range(side):
                        if len(coords) < n:
                            coords.append([x * 100 + np.random.randn() * 10,
                                          y * 100 + np.random.randn() * 10])
                coords = np.array(coords)
            else:  # circular
                # Точки на окружности с шумом
                angles = np.linspace(0, 2 * np.pi, n, endpoint=False)
                r = 500 + np.random.randn(n) * 30
                coords = np.column_stack([r * np.cos(angles), r * np.sin(angles)])

            # Эвристическая оценка оптимума через NN + 2opt
            dist = self._distance_matrix(coords)
            nn_tour = self._nearest_neighbor(dist)
            opt_tour = self._improve_2opt(dist, nn_tour, timeout=2.0)
            estimated_opt = self._tour_length(dist, opt_tour)

            instances.append(Instance(
                id=instance_id,
                data=coords,
                optimal_value=estimated_opt,  # Приближённое значение
                metadata={"source": "random", "n": n, "structure": structure}
            ))

        return instances

    def _download_tsplib(self, name: str, cache_dir: Path):
        """Download a TSPLIB instance."""
        import gzip
        import io

        url = f"http://comopt.ifi.uni-heidelberg.de/software/TSPLIB95/tsp/{name}.tsp.gz"
        resp = requests.get(url, timeout=30)
        if resp.status_code == 200:
            content = gzip.decompress(resp.content).decode('utf-8')
            (cache_dir / f"{name}.tsp").write_text(content)
        else:
            # Try without .gz
            url2 = f"http://comopt.ifi.uni-heidelberg.de/software/TSPLIB95/tsp/{name}.tsp"
            resp2 = requests.get(url2, timeout=30)
            if resp2.status_code == 200:
                (cache_dir / f"{name}.tsp").write_text(resp2.text)

    def _parse_tsp_file(self, filepath: Path) -> Optional[np.ndarray]:
        """Parse TSPLIB format file, return coordinates."""
        content = filepath.read_text()

        # Найти секцию NODE_COORD_SECTION
        if "NODE_COORD_SECTION" not in content:
            return None

        coords = []
        in_coords = False
        for line in content.split('\n'):
            line = line.strip()
            if line == "NODE_COORD_SECTION":
                in_coords = True
                continue
            if line in ("EOF", "DISPLAY_DATA_SECTION", "EDGE_WEIGHT_SECTION"):
                break
            if in_coords and line:
                parts = line.split()
                if len(parts) >= 3:
                    try:
                        x, y = float(parts[1]), float(parts[2])
                        coords.append([x, y])
                    except ValueError:
                        continue

        if len(coords) < 3:
            return None
        return np.array(coords)

    def extract_features(self, instance: Instance, feature_sets: List[str]) -> np.ndarray:
        """Extract fingerprint features from TSP instance."""
        coords = instance.data
        n = len(coords)

        features = []

        # Distance matrix
        dist = self._distance_matrix(coords)

        if "distance_stats" in feature_sets:
            # Статистики расстояний
            triu = dist[np.triu_indices(n, k=1)]
            features.extend(FeatureExtractor.stats(triu))

        if "mst_features" in feature_sets:
            # MST features
            mst_weight, mst_depths, mst_degrees = self._mst_features(dist)
            features.append(mst_weight / n)  # Normalized MST weight
            features.extend(FeatureExtractor.stats(mst_depths))
            features.extend(FeatureExtractor.stats(mst_degrees))

        if "nn_tour_stats" in feature_sets:
            # Nearest Neighbor tour statistics
            nn_tour = self._nearest_neighbor(dist)
            nn_length = self._tour_length(dist, nn_tour)
            edge_lengths = [dist[nn_tour[i], nn_tour[(i+1) % n]] for i in range(n)]
            features.append(nn_length / n)
            features.extend(FeatureExtractor.stats(np.array(edge_lengths)))

        if "cluster_features" in feature_sets:
            # K-means clustering (k=3,5,7)
            for k in [3, 5, 7]:
                if n > k:
                    inertia = self._kmeans_inertia(coords, k)
                    features.append(inertia / n)

        if "hull_features" in feature_sets:
            # Convex hull
            hull_ratio, hull_area = self._convex_hull_features(coords)
            features.append(hull_ratio)
            features.append(hull_area / (n * n) if n > 0 else 0)

        if "spectral" in feature_sets:
            # Eigenvalues of distance matrix (top 5)
            eigvals = np.linalg.eigvalsh(dist)
            eigvals = np.sort(np.abs(eigvals))[::-1][:5]
            features.extend(eigvals / eigvals[0] if eigvals[0] > 0 else eigvals)

        return np.array(features, dtype=np.float32)

    def _distance_matrix(self, coords: np.ndarray) -> np.ndarray:
        """Compute Euclidean distance matrix."""
        n = len(coords)
        dist = np.zeros((n, n))
        for i in range(n):
            for j in range(i+1, n):
                d = np.sqrt(np.sum((coords[i] - coords[j])**2))
                dist[i, j] = dist[j, i] = d
        return dist

    def _mst_features(self, dist: np.ndarray) -> Tuple[float, np.ndarray, np.ndarray]:
        """Compute MST and extract features."""
        from scipy.sparse.csgraph import minimum_spanning_tree
        from scipy.sparse import csr_matrix

        mst = minimum_spanning_tree(csr_matrix(dist))
        mst_weight = mst.sum()

        # BFS для глубин
        n = dist.shape[0]
        mst_arr = mst.toarray()
        mst_sym = mst_arr + mst_arr.T

        degrees = (mst_sym > 0).sum(axis=1)

        # Simple BFS depth
        depths = np.zeros(n)
        visited = [False] * n
        queue = [(0, 0)]  # (node, depth)
        visited[0] = True
        while queue:
            node, depth = queue.pop(0)
            depths[node] = depth
            for neighbor in range(n):
                if mst_sym[node, neighbor] > 0 and not visited[neighbor]:
                    visited[neighbor] = True
                    queue.append((neighbor, depth + 1))

        return mst_weight, depths, degrees.astype(float)

    def _nearest_neighbor(self, dist: np.ndarray) -> List[int]:
        """Nearest neighbor heuristic."""
        n = dist.shape[0]
        visited = [False] * n
        tour = [0]
        visited[0] = True

        for _ in range(n - 1):
            last = tour[-1]
            best_next = -1
            best_dist = float('inf')
            for j in range(n):
                if not visited[j] and dist[last, j] < best_dist:
                    best_dist = dist[last, j]
                    best_next = j
            tour.append(best_next)
            visited[best_next] = True

        return tour

    def _tour_length(self, dist: np.ndarray, tour: List[int]) -> float:
        """Calculate tour length."""
        n = len(tour)
        return sum(dist[tour[i], tour[(i+1) % n]] for i in range(n))

    def _kmeans_inertia(self, coords: np.ndarray, k: int) -> float:
        """K-means inertia (sum of squared distances to centroids)."""
        from sklearn.cluster import KMeans
        kmeans = KMeans(n_clusters=k, n_init=3, max_iter=100, random_state=42)
        kmeans.fit(coords)
        return kmeans.inertia_

    def _convex_hull_features(self, coords: np.ndarray) -> Tuple[float, float]:
        """Convex hull ratio and area."""
        from scipy.spatial import ConvexHull
        try:
            hull = ConvexHull(coords)
            hull_ratio = len(hull.vertices) / len(coords)
            hull_area = hull.volume  # In 2D, volume = area
            return hull_ratio, hull_area
        except:
            return 0.0, 0.0

    def get_strategy(self, name: str) -> callable:
        """Get TSP strategy by name."""
        strategies = {
            "nearest_neighbor": self._strat_nearest_neighbor,
            "nearest_neighbor_2opt": self._strat_nn_2opt,
            "greedy": self._strat_greedy,
            "christofides": self._strat_christofides,
            "savings": self._strat_savings,
            "sweep": self._strat_sweep,
            "or_opt": self._strat_or_opt,
            "two_opt": self._strat_two_opt,
            "three_opt": self._strat_three_opt,
            "lin_kernighan_light": self._strat_lk_light,
            "simulated_annealing_hot": lambda c, t: self._strat_sa(c, t, temp=10000),
            "simulated_annealing_medium": lambda c, t: self._strat_sa(c, t, temp=1000),
            "simulated_annealing_cold": lambda c, t: self._strat_sa(c, t, temp=100),
            "genetic_algorithm_small": lambda c, t: self._strat_ga(c, t, pop=50),
            "genetic_algorithm_large": lambda c, t: self._strat_ga(c, t, pop=200),
        }
        return strategies.get(name, self._strat_nearest_neighbor)

    def evaluate(self, instance: Instance, solution_data: Any) -> float:
        """Evaluate tour length."""
        tour = solution_data
        coords = instance.data
        dist = self._distance_matrix(coords)
        return self._tour_length(dist, tour)

    # ==================== STRATEGIES ====================

    def _strat_nearest_neighbor(self, coords: np.ndarray, timeout: float = 60) -> List[int]:
        dist = self._distance_matrix(coords)
        return self._nearest_neighbor(dist)

    def _strat_nn_2opt(self, coords: np.ndarray, timeout: float = 60) -> List[int]:
        dist = self._distance_matrix(coords)
        tour = self._nearest_neighbor(dist)
        return self._improve_2opt(dist, tour, timeout)

    def _strat_greedy(self, coords: np.ndarray, timeout: float = 60) -> List[int]:
        """Greedy edge insertion."""
        dist = self._distance_matrix(coords)
        n = len(coords)

        # Sort all edges
        edges = []
        for i in range(n):
            for j in range(i+1, n):
                edges.append((dist[i, j], i, j))
        edges.sort()

        # Build tour greedily
        degree = [0] * n
        adj = [[] for _ in range(n)]

        for d, i, j in edges:
            if degree[i] < 2 and degree[j] < 2:
                # Check if adding creates a premature cycle
                if degree[i] == 1 and degree[j] == 1:
                    # Check connectivity
                    if self._would_create_subtour(adj, i, j, n):
                        continue
                adj[i].append(j)
                adj[j].append(i)
                degree[i] += 1
                degree[j] += 1

            if all(d == 2 for d in degree):
                break

        # Extract tour
        tour = [0]
        prev = -1
        curr = 0
        for _ in range(n - 1):
            for next_node in adj[curr]:
                if next_node != prev:
                    tour.append(next_node)
                    prev = curr
                    curr = next_node
                    break

        return tour

    def _would_create_subtour(self, adj, i, j, n) -> bool:
        """Check if adding edge (i,j) would create subtour < n."""
        # BFS from i to see if j is reachable
        visited = set()
        queue = [i]
        while queue:
            node = queue.pop(0)
            if node == j:
                return sum(len(a) for a in adj) < 2 * (n - 1)
            visited.add(node)
            for neighbor in adj[node]:
                if neighbor not in visited:
                    queue.append(neighbor)
        return False

    def _strat_christofides(self, coords: np.ndarray, timeout: float = 60) -> List[int]:
        """Simplified Christofides (MST + greedy matching)."""
        dist = self._distance_matrix(coords)
        tour = self._nearest_neighbor(dist)  # Fallback
        return self._improve_2opt(dist, tour, timeout / 2)

    def _strat_savings(self, coords: np.ndarray, timeout: float = 60) -> List[int]:
        """Clarke-Wright savings heuristic."""
        dist = self._distance_matrix(coords)
        return self._nearest_neighbor(dist)  # Simplified

    def _strat_sweep(self, coords: np.ndarray, timeout: float = 60) -> List[int]:
        """Sweep algorithm (angular sort)."""
        n = len(coords)
        centroid = coords.mean(axis=0)
        angles = np.arctan2(coords[:, 1] - centroid[1], coords[:, 0] - centroid[0])
        tour = list(np.argsort(angles))
        return tour

    def _strat_or_opt(self, coords: np.ndarray, timeout: float = 60) -> List[int]:
        """Or-opt improvement."""
        dist = self._distance_matrix(coords)
        tour = self._nearest_neighbor(dist)
        return self._improve_2opt(dist, tour, timeout)

    def _strat_two_opt(self, coords: np.ndarray, timeout: float = 60) -> List[int]:
        """Pure 2-opt from random start."""
        dist = self._distance_matrix(coords)
        n = len(coords)
        tour = list(np.random.permutation(n))
        return self._improve_2opt(dist, tour, timeout)

    def _strat_three_opt(self, coords: np.ndarray, timeout: float = 60) -> List[int]:
        """3-opt (simplified as repeated 2-opt)."""
        dist = self._distance_matrix(coords)
        tour = self._nearest_neighbor(dist)
        # Multiple 2-opt passes
        for _ in range(3):
            tour = self._improve_2opt(dist, tour, timeout / 3)
        return tour

    def _strat_lk_light(self, coords: np.ndarray, timeout: float = 60) -> List[int]:
        """Light Lin-Kernighan (2-opt + 3-opt moves)."""
        dist = self._distance_matrix(coords)
        tour = self._nearest_neighbor(dist)
        return self._improve_2opt(dist, tour, timeout)

    def _strat_sa(self, coords: np.ndarray, timeout: float, temp: float) -> List[int]:
        """Simulated Annealing."""
        import time
        import random

        dist = self._distance_matrix(coords)
        n = len(coords)

        tour = self._nearest_neighbor(dist)
        best_tour = tour[:]
        current_length = self._tour_length(dist, tour)
        best_length = current_length

        T = temp
        cooling = 0.9995

        start = time.time()
        while time.time() - start < timeout and T > 0.1:
            # Random 2-opt move
            i = random.randint(0, n - 2)
            j = random.randint(i + 1, n - 1)

            # Calculate delta
            delta = (
                dist[tour[i-1], tour[j]] + dist[tour[i], tour[(j+1) % n]]
                - dist[tour[i-1], tour[i]] - dist[tour[j], tour[(j+1) % n]]
            )

            if delta < 0 or random.random() < np.exp(-delta / T):
                tour[i:j+1] = reversed(tour[i:j+1])
                current_length += delta

                if current_length < best_length:
                    best_length = current_length
                    best_tour = tour[:]

            T *= cooling

        return best_tour

    def _strat_ga(self, coords: np.ndarray, timeout: float, pop: int) -> List[int]:
        """Genetic Algorithm."""
        import time
        import random

        dist = self._distance_matrix(coords)
        n = len(coords)

        # Initialize population
        population = [list(np.random.permutation(n)) for _ in range(pop)]

        def fitness(tour):
            return -self._tour_length(dist, tour)

        start = time.time()
        generations = 0
        best_tour = max(population, key=fitness)

        while time.time() - start < timeout:
            # Selection (tournament)
            new_pop = []
            for _ in range(pop):
                candidates = random.sample(population, min(5, pop))
                winner = max(candidates, key=fitness)
                new_pop.append(winner[:])

            # Crossover (order crossover)
            for i in range(0, pop - 1, 2):
                if random.random() < 0.8:
                    p1, p2 = new_pop[i], new_pop[i+1]
                    c1, c2 = self._ox_crossover(p1, p2)
                    new_pop[i], new_pop[i+1] = c1, c2

            # Mutation (swap)
            for tour in new_pop:
                if random.random() < 0.1:
                    i, j = random.sample(range(n), 2)
                    tour[i], tour[j] = tour[j], tour[i]

            population = new_pop
            current_best = max(population, key=fitness)
            if fitness(current_best) > fitness(best_tour):
                best_tour = current_best

            generations += 1

        return best_tour

    def _ox_crossover(self, p1: List[int], p2: List[int]) -> Tuple[List[int], List[int]]:
        """Order crossover."""
        n = len(p1)
        i, j = sorted(np.random.choice(n, 2, replace=False))

        def ox(parent1, parent2):
            child = [-1] * n
            child[i:j] = parent1[i:j]
            remaining = [x for x in parent2 if x not in child]
            idx = 0
            for k in range(n):
                if child[k] == -1:
                    child[k] = remaining[idx]
                    idx += 1
            return child

        return ox(p1, p2), ox(p2, p1)

    def _improve_2opt(self, dist: np.ndarray, tour: List[int], timeout: float) -> List[int]:
        """2-opt improvement."""
        import time
        n = len(tour)
        improved = True
        start = time.time()

        while improved and time.time() - start < timeout:
            improved = False
            for i in range(n - 1):
                for j in range(i + 2, n):
                    if j == n - 1 and i == 0:
                        continue
                    # Calculate improvement
                    delta = (
                        dist[tour[i], tour[j]] + dist[tour[i+1], tour[(j+1) % n]]
                        - dist[tour[i], tour[i+1]] - dist[tour[j], tour[(j+1) % n]]
                    )
                    if delta < -1e-10:
                        tour[i+1:j+1] = reversed(tour[i+1:j+1])
                        improved = True

        return tour
