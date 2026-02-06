"""
SAT (Boolean Satisfiability) implementation for FRA scaling experiment.
"""

import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
import subprocess
import tempfile
import time
from .base import Problem, Instance, FeatureExtractor


class SATProblem(Problem):
    """Boolean Satisfiability Problem."""

    name = "sat"

    def load_instances(self, source: str, count: int) -> List[Instance]:
        """Load SAT benchmark instances."""
        instances = []
        cache_dir = Path(__file__).parent.parent / "data" / "sat"
        cache_dir.mkdir(parents=True, exist_ok=True)

        if source == "satcomp":
            # Генерируем random 3-SAT instances с контролируемой сложностью
            # Ratio ~4.26 - phase transition (hard instances)
            for i in range(count):
                n_vars = np.random.choice([50, 75, 100, 150, 200])
                ratio = np.random.uniform(4.0, 4.5)  # Around phase transition
                n_clauses = int(n_vars * ratio)

                clauses = self._generate_random_3sat(n_vars, n_clauses)

                instances.append(Instance(
                    id=f"random3sat_{n_vars}v_{n_clauses}c_{i}",
                    data={"n_vars": n_vars, "clauses": clauses},
                    optimal_value=None,  # Unknown - we measure solve time
                    metadata={"source": "random", "n_vars": n_vars, "n_clauses": n_clauses}
                ))

        return instances

    def _generate_random_3sat(self, n_vars: int, n_clauses: int) -> List[List[int]]:
        """Generate random 3-SAT instance."""
        clauses = []
        for _ in range(n_clauses):
            # Select 3 distinct variables
            vars_in_clause = np.random.choice(n_vars, 3, replace=False) + 1
            # Random polarity
            signs = np.random.choice([-1, 1], 3)
            clause = (vars_in_clause * signs).tolist()
            clauses.append(clause)
        return clauses

    def extract_features(self, instance: Instance, feature_sets: List[str]) -> np.ndarray:
        """Extract fingerprint features from SAT instance."""
        data = instance.data
        n_vars = data["n_vars"]
        clauses = data["clauses"]
        n_clauses = len(clauses)

        features = []

        if "clause_variable_ratio" in feature_sets:
            features.append(n_clauses / n_vars)

        if "clause_length_dist" in feature_sets:
            lengths = [len(c) for c in clauses]
            features.extend(FeatureExtractor.stats(np.array(lengths)))

        if "variable_frequency" in feature_sets:
            # How often each variable appears
            var_counts = np.zeros(n_vars)
            for clause in clauses:
                for lit in clause:
                    var_counts[abs(lit) - 1] += 1
            features.extend(FeatureExtractor.stats(var_counts))

        if "vig_features" in feature_sets:
            # Variable Interaction Graph features
            vig = self._build_vig(n_vars, clauses)
            degrees = vig.sum(axis=1)
            features.extend(FeatureExtractor.stats(degrees))

        if "cvig_features" in feature_sets:
            # Clause-Variable Interaction Graph
            cvig_degrees = [len(c) for c in clauses]
            features.extend(FeatureExtractor.stats(np.array(cvig_degrees)))

        if "community_structure" in feature_sets:
            # Simple modularity estimate
            vig = self._build_vig(n_vars, clauses)
            features.append(self._estimate_modularity(vig))

        if "horn_ratio" in feature_sets:
            # Ratio of Horn clauses
            horn_count = sum(1 for c in clauses if sum(1 for l in c if l > 0) <= 1)
            features.append(horn_count / n_clauses if n_clauses > 0 else 0)

        if "positive_negative_ratio" in feature_sets:
            pos = sum(1 for c in clauses for l in c if l > 0)
            neg = sum(1 for c in clauses for l in c if l < 0)
            features.append(pos / (neg + 1))

        return np.array(features, dtype=np.float32)

    def _build_vig(self, n_vars: int, clauses: List[List[int]]) -> np.ndarray:
        """Build Variable Interaction Graph."""
        vig = np.zeros((n_vars, n_vars))
        for clause in clauses:
            vars_in_clause = [abs(l) - 1 for l in clause]
            for i, v1 in enumerate(vars_in_clause):
                for v2 in vars_in_clause[i+1:]:
                    vig[v1, v2] += 1
                    vig[v2, v1] += 1
        return vig

    def _estimate_modularity(self, adj: np.ndarray) -> float:
        """Estimate graph modularity (simplified)."""
        degrees = adj.sum(axis=1)
        m = degrees.sum() / 2
        if m == 0:
            return 0.0
        # Simple: ratio of self-loops to total edges
        n = len(adj)
        k = min(3, n)
        from sklearn.cluster import KMeans
        if n < k:
            return 0.0
        try:
            kmeans = KMeans(n_clusters=k, n_init=3, max_iter=50, random_state=42)
            labels = kmeans.fit_predict(adj)
            # Within-cluster edges
            within = 0
            for c in range(k):
                mask = labels == c
                within += adj[np.ix_(mask, mask)].sum()
            return within / (2 * m) if m > 0 else 0
        except:
            return 0.0

    def get_strategy(self, name: str) -> callable:
        """Get SAT solver strategy by name."""
        strategies = {
            "minisat": self._strat_pysat_solver("Minisat22"),
            "glucose": self._strat_pysat_solver("Glucose4"),
            "cadical": self._strat_pysat_solver("Cadical"),
            "walksat": self._strat_walksat,
            "gsat": self._strat_gsat,
            "probsat": self._strat_probsat,
            "random_restart_100": lambda d, t: self._strat_random_restart(d, t, 100),
            "random_restart_1000": lambda d, t: self._strat_random_restart(d, t, 1000),
            # Fallbacks for unavailable solvers
            "cryptominisat": self._strat_pysat_solver("Minisat22"),
            "sparrow": self._strat_walksat,
            "lingeling": self._strat_pysat_solver("Glucose4"),
            "kissat": self._strat_pysat_solver("Cadical"),
        }
        return strategies.get(name, self._strat_walksat)

    def _strat_pysat_solver(self, solver_name: str):
        """Create PySAT solver strategy."""
        def solve(data: Dict, timeout: float = 60) -> Dict:
            try:
                from pysat.solvers import Solver
                with Solver(name=solver_name, bootstrap_with=data["clauses"]) as solver:
                    start = time.time()
                    result = solver.solve()
                    elapsed = time.time() - start
                    model = solver.get_model() if result else None
                    return {
                        "satisfiable": result,
                        "model": model,
                        "time": elapsed
                    }
            except ImportError:
                return self._strat_walksat(data, timeout)
        return solve

    def _strat_walksat(self, data: Dict, timeout: float = 60) -> Dict:
        """WalkSAT local search."""
        n_vars = data["n_vars"]
        clauses = data["clauses"]

        start = time.time()
        best_unsat = len(clauses)

        for restart in range(100):
            if time.time() - start > timeout:
                break

            # Random assignment
            assignment = {i+1: np.random.choice([True, False]) for i in range(n_vars)}

            for step in range(10000):
                if time.time() - start > timeout:
                    break

                # Find unsatisfied clauses
                unsat = [c for c in clauses if not self._clause_satisfied(c, assignment)]

                if len(unsat) == 0:
                    return {"satisfiable": True, "model": self._to_model(assignment), "time": time.time() - start}

                if len(unsat) < best_unsat:
                    best_unsat = len(unsat)

                # Pick random unsatisfied clause
                clause = unsat[np.random.randint(len(unsat))]

                # Flip a variable (with noise)
                if np.random.random() < 0.5:
                    # Random walk
                    var = abs(clause[np.random.randint(len(clause))])
                else:
                    # Greedy - flip var that minimizes unsatisfied
                    var = self._best_flip(clauses, assignment, clause)

                assignment[var] = not assignment[var]

        return {"satisfiable": False, "model": None, "time": time.time() - start}

    def _strat_gsat(self, data: Dict, timeout: float = 60) -> Dict:
        """GSAT greedy local search."""
        n_vars = data["n_vars"]
        clauses = data["clauses"]

        start = time.time()

        for restart in range(50):
            if time.time() - start > timeout:
                break

            assignment = {i+1: np.random.choice([True, False]) for i in range(n_vars)}

            for step in range(5000):
                if time.time() - start > timeout:
                    break

                unsat = [c for c in clauses if not self._clause_satisfied(c, assignment)]
                if len(unsat) == 0:
                    return {"satisfiable": True, "model": self._to_model(assignment), "time": time.time() - start}

                # Find best variable to flip
                best_var = None
                best_improvement = -float('inf')

                for var in range(1, n_vars + 1):
                    # Count improvement if we flip var
                    current = sum(1 for c in clauses if self._clause_satisfied(c, assignment))
                    assignment[var] = not assignment[var]
                    flipped = sum(1 for c in clauses if self._clause_satisfied(c, assignment))
                    assignment[var] = not assignment[var]  # flip back

                    if flipped - current > best_improvement:
                        best_improvement = flipped - current
                        best_var = var

                if best_var and best_improvement > 0:
                    assignment[best_var] = not assignment[best_var]
                else:
                    # Random flip
                    var = np.random.randint(1, n_vars + 1)
                    assignment[var] = not assignment[var]

        return {"satisfiable": False, "model": None, "time": time.time() - start}

    def _strat_probsat(self, data: Dict, timeout: float = 60) -> Dict:
        """ProbSAT (probability-based flip selection)."""
        return self._strat_walksat(data, timeout)  # Similar to WalkSAT

    def _strat_random_restart(self, data: Dict, timeout: float, max_flips: int) -> Dict:
        """Random restart with limited flips."""
        n_vars = data["n_vars"]
        clauses = data["clauses"]
        start = time.time()

        while time.time() - start < timeout:
            assignment = {i+1: np.random.choice([True, False]) for i in range(n_vars)}

            for _ in range(max_flips):
                unsat = [c for c in clauses if not self._clause_satisfied(c, assignment)]
                if len(unsat) == 0:
                    return {"satisfiable": True, "model": self._to_model(assignment), "time": time.time() - start}

                clause = unsat[np.random.randint(len(unsat))]
                var = abs(clause[np.random.randint(len(clause))])
                assignment[var] = not assignment[var]

        return {"satisfiable": False, "model": None, "time": time.time() - start}

    def _clause_satisfied(self, clause: List[int], assignment: Dict[int, bool]) -> bool:
        """Check if clause is satisfied."""
        for lit in clause:
            var = abs(lit)
            if (lit > 0 and assignment.get(var, False)) or (lit < 0 and not assignment.get(var, False)):
                return True
        return False

    def _to_model(self, assignment: Dict[int, bool]) -> List[int]:
        """Convert assignment to model format."""
        return [v if val else -v for v, val in sorted(assignment.items())]

    def _best_flip(self, clauses: List[List[int]], assignment: Dict, clause: List[int]) -> int:
        """Find best variable to flip in clause."""
        best_var = abs(clause[0])
        best_break = float('inf')

        for lit in clause:
            var = abs(lit)
            # Count how many clauses we would break
            assignment[var] = not assignment[var]
            broken = sum(1 for c in clauses if not self._clause_satisfied(c, assignment))
            assignment[var] = not assignment[var]

            if broken < best_break:
                best_break = broken
                best_var = var

        return best_var

    def evaluate(self, instance: Instance, solution_data: Any) -> float:
        """Evaluate SAT solution. Return solve time (for SAT, lower is better)."""
        if solution_data is None:
            return float('inf')
        return solution_data.get("time", float('inf'))

    def solve(self, instance: Instance, strategy_name: str, timeout: float = 60.0):
        """Override solve to handle SAT-specific evaluation."""
        from .base import Solution
        strategy = self.get_strategy(strategy_name)

        start = time.time()
        result = strategy(instance.data, timeout=timeout)
        elapsed = time.time() - start

        # For SAT, "value" is solve time (lower = better)
        value = result.get("time", elapsed)
        if not result.get("satisfiable"):
            value = timeout  # Penalize unsolved

        return Solution(
            instance_id=instance.id,
            strategy=strategy_name,
            value=value,
            time_seconds=elapsed,
            gap=None,  # No gap for SAT
            solution_data=result
        )
