"""
Base classes for NP-hard problems in FRA scaling experiment.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Dict, Any, Optional, Tuple
import numpy as np


@dataclass
class Instance:
    """A problem instance."""
    id: str
    data: Any  # Problem-specific data
    optimal_value: Optional[float] = None  # Known optimum (if available)
    best_known: Optional[float] = None  # Best known solution
    metadata: Optional[Dict] = None


@dataclass
class Solution:
    """A solution to an instance."""
    instance_id: str
    strategy: str
    value: float  # Objective value
    time_seconds: float
    gap: Optional[float] = None  # Gap from optimum/best known
    solution_data: Any = None  # Strategy-specific solution details


class Problem(ABC):
    """Abstract base class for NP-hard problems."""

    name: str = "abstract"

    @abstractmethod
    def load_instances(self, source: str, count: int) -> List[Instance]:
        """Load benchmark instances."""
        pass

    @abstractmethod
    def extract_features(self, instance: Instance, feature_sets: List[str]) -> np.ndarray:
        """Extract fingerprint features from an instance."""
        pass

    @abstractmethod
    def get_strategy(self, name: str) -> callable:
        """Get a strategy/heuristic by name."""
        pass

    @abstractmethod
    def evaluate(self, instance: Instance, solution_data: Any) -> float:
        """Evaluate a solution, return objective value."""
        pass

    def solve(self, instance: Instance, strategy_name: str, timeout: float = 60.0) -> Solution:
        """Solve an instance with a given strategy."""
        import time

        strategy = self.get_strategy(strategy_name)

        start = time.time()
        solution_data = strategy(instance.data, timeout=timeout)
        elapsed = time.time() - start

        value = self.evaluate(instance, solution_data)

        # Calculate gap
        reference = instance.optimal_value or instance.best_known
        if reference:
            gap = (value - reference) / reference * 100  # Percent gap
        else:
            gap = None

        return Solution(
            instance_id=instance.id,
            strategy=strategy_name,
            value=value,
            time_seconds=elapsed,
            gap=gap,
            solution_data=solution_data
        )

    def solve_all_strategies(
        self,
        instance: Instance,
        strategies: List[str],
        timeout: float = 60.0
    ) -> Dict[str, Solution]:
        """Solve instance with all strategies, return dict."""
        results = {}
        for strat in strategies:
            try:
                results[strat] = self.solve(instance, strat, timeout)
            except Exception as e:
                print(f"  Warning: {strat} failed on {instance.id}: {e}")
                results[strat] = None
        return results


class FeatureExtractor:
    """Generic feature extraction utilities."""

    @staticmethod
    def stats(arr: np.ndarray) -> np.ndarray:
        """Basic statistics: mean, std, min, max, skew, kurtosis."""
        from scipy import stats as sp_stats
        return np.array([
            np.mean(arr),
            np.std(arr),
            np.min(arr),
            np.max(arr),
            sp_stats.skew(arr.flatten()),
            sp_stats.kurtosis(arr.flatten())
        ])

    @staticmethod
    def normalize(features: np.ndarray) -> np.ndarray:
        """Z-score normalization."""
        mean = np.mean(features)
        std = np.std(features) + 1e-8
        return (features - mean) / std
