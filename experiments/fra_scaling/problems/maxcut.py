"""
MaxCut implementation for FRA scaling experiment.
"""

import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
import time
from .base import Problem, Instance, FeatureExtractor


class MaxCutProblem(Problem):
    """Maximum Cut Problem."""

    name = "maxcut"

    # Gset best known solutions
    GSET_BEST_KNOWN = {
        "G1": 11624, "G2": 11620, "G3": 11622, "G4": 11646, "G5": 11631,
        "G6": 2178, "G7": 2006, "G8": 2005, "G9": 2054, "G10": 2000,
        "G11": 564, "G12": 556, "G13": 582, "G14": 3064, "G15": 3050,
        "G16": 3052, "G17": 3047, "G18": 992, "G19": 906, "G20": 941,
        "G21": 931, "G22": 13359, "G23": 13344, "G24": 13337, "G25": 13340,
        "G26": 13328, "G27": 3341, "G28": 3298, "G29": 3405, "G30": 3413,
        "G31": 3310, "G32": 1410, "G33": 1382, "G34": 1384, "G35": 7687,
        "G36": 7680, "G37": 7691, "G38": 7688, "G39": 2408, "G40": 2400,
        "G41": 2405, "G42": 2481, "G43": 6660, "G44": 6650, "G45": 6654,
        "G46": 6649, "G47": 6657, "G48": 6000, "G49": 6000, "G50": 5880,
        "G51": 3848, "G52": 3851, "G53": 3850, "G54": 3852, "G55": 10299,
        "G56": 4017, "G57": 3494, "G58": 19293, "G59": 6086, "G60": 14188,
        "G61": 5796, "G62": 4870, "G63": 27045, "G64": 8751, "G65": 5560,
        "G66": 6364, "G67": 6940,
    }

    def load_instances(self, source: str, count: int) -> List[Instance]:
        """Load MaxCut benchmark instances."""
        instances = []
        cache_dir = Path(__file__).parent.parent / "data" / "maxcut"
        cache_dir.mkdir(parents=True, exist_ok=True)

        if source == "gset":
            # Generate random graphs similar to Gset
            for i in range(count):
                n_nodes = np.random.choice([100, 200, 500, 800])
                density = np.random.uniform(0.01, 0.1)
                n_edges = int(n_nodes * (n_nodes - 1) / 2 * density)

                adj, weights = self._generate_random_graph(n_nodes, n_edges)

                instances.append(Instance(
                    id=f"random_maxcut_{n_nodes}n_{n_edges}e_{i}",
                    data={"n_nodes": n_nodes, "adj": adj, "weights": weights},
                    best_known=None,  # Unknown for random
                    metadata={"source": "random", "n_nodes": n_nodes, "n_edges": n_edges}
                ))

        return instances

    def _generate_random_graph(self, n_nodes: int, n_edges: int) -> Tuple[np.ndarray, np.ndarray]:
        """Generate random weighted graph."""
        adj = np.zeros((n_nodes, n_nodes))
        weights = np.zeros((n_nodes, n_nodes))

        edges_added = 0
        while edges_added < n_edges:
            i = np.random.randint(n_nodes)
            j = np.random.randint(n_nodes)
            if i != j and adj[i, j] == 0:
                w = np.random.randint(1, 10)
                adj[i, j] = adj[j, i] = 1
                weights[i, j] = weights[j, i] = w
                edges_added += 1

        return adj, weights

    def extract_features(self, instance: Instance, feature_sets: List[str]) -> np.ndarray:
        """Extract fingerprint features from MaxCut instance."""
        data = instance.data
        n_nodes = data["n_nodes"]
        adj = data["adj"]
        weights = data["weights"]

        features = []

        if "graph_stats" in feature_sets:
            n_edges = int(adj.sum() / 2)
            density = n_edges / (n_nodes * (n_nodes - 1) / 2) if n_nodes > 1 else 0
            features.extend([n_nodes / 1000, n_edges / 10000, density])

        if "degree_dist" in feature_sets:
            degrees = adj.sum(axis=1)
            features.extend(FeatureExtractor.stats(degrees))

        if "spectral" in feature_sets:
            # Laplacian eigenvalues
            D = np.diag(adj.sum(axis=1))
            L = D - adj
            try:
                eigvals = np.linalg.eigvalsh(L)
                eigvals = np.sort(eigvals)[:5]  # Smallest 5
                features.extend(eigvals)
            except:
                features.extend([0] * 5)

        if "clustering" in feature_sets:
            # Local clustering coefficient
            cc = self._clustering_coefficients(adj)
            features.extend(FeatureExtractor.stats(cc))

        if "modularity" in feature_sets:
            # Estimate modularity
            mod = self._estimate_modularity(adj)
            features.append(mod)

        return np.array(features, dtype=np.float32)

    def _clustering_coefficients(self, adj: np.ndarray) -> np.ndarray:
        """Compute local clustering coefficients."""
        n = len(adj)
        cc = np.zeros(n)
        for i in range(n):
            neighbors = np.where(adj[i] > 0)[0]
            k = len(neighbors)
            if k < 2:
                cc[i] = 0
                continue
            # Count triangles
            triangles = 0
            for j, n1 in enumerate(neighbors):
                for n2 in neighbors[j+1:]:
                    if adj[n1, n2] > 0:
                        triangles += 1
            cc[i] = 2 * triangles / (k * (k - 1))
        return cc

    def _estimate_modularity(self, adj: np.ndarray) -> float:
        """Estimate graph modularity."""
        n = len(adj)
        if n < 3:
            return 0.0

        # Simple spectral clustering
        D = np.diag(adj.sum(axis=1))
        L = D - adj
        try:
            eigvals, eigvecs = np.linalg.eigh(L)
            # Use Fiedler vector
            idx = np.argsort(eigvals)[1]  # Second smallest
            fiedler = eigvecs[:, idx]
            partition = fiedler > 0

            # Compute modularity
            m = adj.sum() / 2
            if m == 0:
                return 0.0

            degrees = adj.sum(axis=1)
            Q = 0
            for i in range(n):
                for j in range(n):
                    if partition[i] == partition[j]:
                        Q += adj[i, j] - degrees[i] * degrees[j] / (2 * m)
            return Q / (2 * m)
        except:
            return 0.0

    def get_strategy(self, name: str) -> callable:
        """Get MaxCut strategy by name."""
        strategies = {
            "greedy": self._strat_greedy,
            "random_multistart": self._strat_random_multistart,
            "simulated_annealing": self._strat_sa,
            "genetic_algorithm": self._strat_ga,
            "sdp_relaxation": self._strat_sdp_approx,
            "goemans_williamson": self._strat_gw,
            "local_search_steepest": lambda d, t: self._strat_local_search(d, t, "steepest"),
            "local_search_first": lambda d, t: self._strat_local_search(d, t, "first"),
            "grasp": self._strat_grasp,
            "tabu_search": self._strat_tabu,
        }
        return strategies.get(name, self._strat_greedy)

    def evaluate(self, instance: Instance, solution_data: Any) -> float:
        """Evaluate cut value (higher is better, but we minimize negative)."""
        partition = solution_data
        if partition is None:
            return 0.0

        adj = instance.data["adj"]
        weights = instance.data["weights"]
        n = len(partition)

        cut_value = 0
        for i in range(n):
            for j in range(i + 1, n):
                if partition[i] != partition[j] and adj[i, j] > 0:
                    cut_value += weights[i, j]

        return cut_value

    def solve(self, instance: Instance, strategy_name: str, timeout: float = 60.0):
        """Override solve for MaxCut (maximize instead of minimize)."""
        from .base import Solution
        strategy = self.get_strategy(strategy_name)

        start = time.time()
        partition = strategy(instance.data, timeout=timeout)
        elapsed = time.time() - start

        value = self.evaluate(instance, partition)

        # Gap from best known (if available)
        reference = instance.best_known or instance.optimal_value
        if reference:
            gap = (reference - value) / reference * 100  # Percent below best
        else:
            gap = None

        return Solution(
            instance_id=instance.id,
            strategy=strategy_name,
            value=value,
            time_seconds=elapsed,
            gap=gap,
            solution_data=partition
        )

    # ==================== STRATEGIES ====================

    def _strat_greedy(self, data: Dict, timeout: float = 60) -> np.ndarray:
        """Greedy MaxCut."""
        n = data["n_nodes"]
        adj = data["adj"]
        weights = data["weights"]

        partition = np.zeros(n, dtype=bool)

        for i in range(n):
            # Compute gain of putting i in set 1
            gain_1 = sum(weights[i, j] for j in range(n) if adj[i, j] > 0 and not partition[j])
            gain_0 = sum(weights[i, j] for j in range(n) if adj[i, j] > 0 and partition[j])
            partition[i] = gain_1 > gain_0

        return partition

    def _strat_random_multistart(self, data: Dict, timeout: float = 60) -> np.ndarray:
        """Random multistart with local search."""
        n = data["n_nodes"]
        best_partition = np.random.choice([True, False], n)
        best_value = self._cut_value(data, best_partition)

        start = time.time()
        while time.time() - start < timeout:
            partition = np.random.choice([True, False], n)
            partition = self._local_search(data, partition, (timeout - (time.time() - start)) / 10)
            value = self._cut_value(data, partition)

            if value > best_value:
                best_value = value
                best_partition = partition.copy()

        return best_partition

    def _strat_sa(self, data: Dict, timeout: float = 60) -> np.ndarray:
        """Simulated Annealing for MaxCut."""
        n = data["n_nodes"]
        partition = np.random.choice([True, False], n)
        current_value = self._cut_value(data, partition)

        best_partition = partition.copy()
        best_value = current_value

        T = 1000
        cooling = 0.9995

        start = time.time()
        while time.time() - start < timeout and T > 0.1:
            # Random flip
            i = np.random.randint(n)
            partition[i] = not partition[i]
            new_value = self._cut_value(data, partition)

            delta = new_value - current_value

            if delta > 0 or np.random.random() < np.exp(delta / T):
                current_value = new_value
                if current_value > best_value:
                    best_value = current_value
                    best_partition = partition.copy()
            else:
                partition[i] = not partition[i]  # Revert

            T *= cooling

        return best_partition

    def _strat_ga(self, data: Dict, timeout: float = 60) -> np.ndarray:
        """Genetic Algorithm for MaxCut."""
        n = data["n_nodes"]
        pop_size = 50

        # Initialize
        population = [np.random.choice([True, False], n) for _ in range(pop_size)]
        fitness = [self._cut_value(data, p) for p in population]

        best_idx = np.argmax(fitness)
        best_partition = population[best_idx].copy()
        best_value = fitness[best_idx]

        start = time.time()
        while time.time() - start < timeout:
            # Selection (tournament)
            new_pop = []
            for _ in range(pop_size):
                candidates = np.random.choice(pop_size, 5, replace=False)
                winner = max(candidates, key=lambda x: fitness[x])
                new_pop.append(population[winner].copy())

            # Crossover
            for i in range(0, pop_size - 1, 2):
                if np.random.random() < 0.8:
                    point = np.random.randint(1, n)
                    child1 = np.concatenate([new_pop[i][:point], new_pop[i+1][point:]])
                    child2 = np.concatenate([new_pop[i+1][:point], new_pop[i][point:]])
                    new_pop[i] = child1
                    new_pop[i+1] = child2

            # Mutation
            for p in new_pop:
                if np.random.random() < 0.1:
                    idx = np.random.randint(n)
                    p[idx] = not p[idx]

            population = new_pop
            fitness = [self._cut_value(data, p) for p in population]

            current_best_idx = np.argmax(fitness)
            if fitness[current_best_idx] > best_value:
                best_value = fitness[current_best_idx]
                best_partition = population[current_best_idx].copy()

        return best_partition

    def _strat_sdp_approx(self, data: Dict, timeout: float = 60) -> np.ndarray:
        """SDP relaxation approximation (simplified)."""
        # Use spectral method as approximation
        return self._strat_gw(data, timeout)

    def _strat_gw(self, data: Dict, timeout: float = 60) -> np.ndarray:
        """Goemans-Williamson style (spectral rounding)."""
        n = data["n_nodes"]
        adj = data["adj"]

        # Laplacian
        D = np.diag(adj.sum(axis=1))
        L = D - adj

        try:
            eigvals, eigvecs = np.linalg.eigh(L)
            # Use random hyperplane rounding on Fiedler-like vectors
            best_partition = None
            best_value = 0

            for _ in range(10):
                # Random projection
                r = np.random.randn(n)
                proj = eigvecs @ (eigvecs.T @ r)
                partition = proj > 0
                value = self._cut_value(data, partition)

                if value > best_value:
                    best_value = value
                    best_partition = partition

            return best_partition if best_partition is not None else np.random.choice([True, False], n)
        except:
            return np.random.choice([True, False], n)

    def _strat_local_search(self, data: Dict, timeout: float, mode: str = "steepest") -> np.ndarray:
        """Local search with steepest/first improvement."""
        n = data["n_nodes"]
        partition = np.random.choice([True, False], n)
        partition = self._local_search(data, partition, timeout, mode)
        return partition

    def _strat_grasp(self, data: Dict, timeout: float = 60) -> np.ndarray:
        """GRASP for MaxCut."""
        n = data["n_nodes"]
        best_partition = None
        best_value = 0

        start = time.time()
        while time.time() - start < timeout:
            # Randomized greedy construction
            partition = np.zeros(n, dtype=bool)
            remaining = list(range(n))
            np.random.shuffle(remaining)

            for i in remaining:
                gain_1 = self._gain_if_set(data, partition, i, True)
                gain_0 = self._gain_if_set(data, partition, i, False)

                # Randomized selection with RCL
                if np.random.random() < 0.3:
                    partition[i] = np.random.choice([True, False])
                else:
                    partition[i] = gain_1 > gain_0

            # Local search
            partition = self._local_search(data, partition, (timeout - (time.time() - start)) / 10)
            value = self._cut_value(data, partition)

            if value > best_value:
                best_value = value
                best_partition = partition.copy()

        return best_partition if best_partition is not None else np.random.choice([True, False], n)

    def _strat_tabu(self, data: Dict, timeout: float = 60) -> np.ndarray:
        """Tabu search for MaxCut."""
        n = data["n_nodes"]
        partition = np.random.choice([True, False], n)
        current_value = self._cut_value(data, partition)

        best_partition = partition.copy()
        best_value = current_value

        tabu_list = {}
        tabu_tenure = max(7, n // 10)

        start = time.time()
        iteration = 0

        while time.time() - start < timeout:
            # Find best non-tabu move
            best_move = None
            best_delta = -float('inf')

            for i in range(n):
                if tabu_list.get(i, 0) <= iteration or self._cut_value(data, partition) + self._flip_delta(data, partition, i) > best_value:
                    delta = self._flip_delta(data, partition, i)
                    if delta > best_delta:
                        best_delta = delta
                        best_move = i

            if best_move is not None:
                partition[best_move] = not partition[best_move]
                current_value += best_delta
                tabu_list[best_move] = iteration + tabu_tenure

                if current_value > best_value:
                    best_value = current_value
                    best_partition = partition.copy()

            iteration += 1

        return best_partition

    def _cut_value(self, data: Dict, partition: np.ndarray) -> float:
        """Compute cut value."""
        adj = data["adj"]
        weights = data["weights"]
        n = len(partition)

        value = 0
        for i in range(n):
            for j in range(i + 1, n):
                if partition[i] != partition[j] and adj[i, j] > 0:
                    value += weights[i, j]
        return value

    def _flip_delta(self, data: Dict, partition: np.ndarray, i: int) -> float:
        """Compute change in cut value if we flip node i."""
        adj = data["adj"]
        weights = data["weights"]

        delta = 0
        for j in range(len(partition)):
            if adj[i, j] > 0:
                if partition[i] == partition[j]:
                    delta += weights[i, j]  # Would add to cut
                else:
                    delta -= weights[i, j]  # Would remove from cut
        return delta

    def _gain_if_set(self, data: Dict, partition: np.ndarray, i: int, value: bool) -> float:
        """Compute contribution if we set node i to value."""
        adj = data["adj"]
        weights = data["weights"]

        gain = 0
        for j in range(len(partition)):
            if j != i and adj[i, j] > 0:
                if partition[j] != value:
                    gain += weights[i, j]
        return gain

    def _local_search(self, data: Dict, partition: np.ndarray, timeout: float, mode: str = "steepest") -> np.ndarray:
        """Local search improvement."""
        n = len(partition)
        improved = True
        start = time.time()

        while improved and time.time() - start < timeout:
            improved = False

            if mode == "first":
                # First improvement
                for i in range(n):
                    delta = self._flip_delta(data, partition, i)
                    if delta > 0:
                        partition[i] = not partition[i]
                        improved = True
                        break
            else:
                # Steepest descent
                best_i = None
                best_delta = 0
                for i in range(n):
                    delta = self._flip_delta(data, partition, i)
                    if delta > best_delta:
                        best_delta = delta
                        best_i = i

                if best_i is not None:
                    partition[best_i] = not partition[best_i]
                    improved = True

        return partition
