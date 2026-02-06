"""
ASlib Problem - загрузка и адаптация ASlib scenarios для FRA.

ASlib (Algorithm Selection Library) - стандартный benchmark для algorithm selection.
Содержит готовые features и performance data для разных NP-hard проблем.
"""

import os
import json
import logging
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
import numpy as np

try:
    from scipy.io import arff
    HAS_ARFF = True
except ImportError:
    HAS_ARFF = False

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)


@dataclass
class ASLibScenario:
    """ASlib scenario data."""
    name: str
    features: np.ndarray          # [n_instances, n_features]
    feature_names: List[str]
    performance: np.ndarray       # [n_instances, n_algorithms]
    algorithm_names: List[str]
    instance_ids: List[str]
    cv_splits: Optional[List[Tuple[List[int], List[int]]]] = None  # [(train_idx, test_idx), ...]


class ASLibProblem:
    """
    Загружает ASlib scenario и адаптирует к FRA формату.

    ASlib format:
    - feature_values.arff: instance features
    - algorithm_runs.arff: performance data (runtime or quality)
    - cv.arff: cross-validation splits

    Мы используем упрощённый формат CSV для быстрого старта.
    """

    # Встроенные mini-scenarios для демо (если ASlib недоступен)
    BUILTIN_SCENARIOS = {
        "sat-mini": {
            "description": "Mini SAT scenario (synthetic)",
            "n_instances": 100,
            "n_features": 10,
            "n_algorithms": 5,
            "algorithm_names": ["minisat", "glucose", "cadical", "walksat", "lingeling"],
            "diversity": 0.8  # 80% случаев разные алгоритмы лучше
        },
        "tsp-mini": {
            "description": "Mini TSP scenario (synthetic)",
            "n_instances": 100,
            "n_features": 8,
            "n_algorithms": 4,
            "algorithm_names": ["nearest_neighbor", "2opt", "christofides", "lkh"],
            "diversity": 0.7
        }
    }

    def __init__(self, scenario_path: Optional[str] = None, scenario_name: Optional[str] = None):
        """
        Args:
            scenario_path: Path to ASlib scenario directory
            scenario_name: Name of builtin scenario (if no path)
        """
        self.scenario: Optional[ASLibScenario] = None

        if scenario_path:
            self.scenario = self._load_from_path(scenario_path)
        elif scenario_name:
            if scenario_name in self.BUILTIN_SCENARIOS:
                self.scenario = self._generate_builtin(scenario_name)
            else:
                raise ValueError(f"Unknown builtin scenario: {scenario_name}")

    def _load_from_path(self, path: str) -> ASLibScenario:
        """Загружает scenario из директории."""
        path = Path(path)

        if not path.exists():
            raise FileNotFoundError(f"Scenario path not found: {path}")

        # Ищем файлы
        feature_file = path / "feature_values.arff"
        perf_file = path / "algorithm_runs.arff"

        if not feature_file.exists() or not perf_file.exists():
            # Пробуем CSV формат
            feature_file = path / "features.csv"
            perf_file = path / "performance.csv"

        if feature_file.suffix == ".arff":
            return self._load_arff(path)
        else:
            return self._load_csv(path)

    def _load_arff(self, path: Path) -> ASLibScenario:
        """Загружает ARFF формат (стандарт ASlib)."""
        if not HAS_ARFF:
            raise ImportError("scipy required for ARFF parsing: pip install scipy")

        # Загружаем features
        feature_data, feature_meta = arff.loadarff(path / "feature_values.arff")
        feature_names = [n for n in feature_meta.names() if n != "instance_id"]

        # Загружаем performance
        perf_data, perf_meta = arff.loadarff(path / "algorithm_runs.arff")
        algorithm_names = [n for n in perf_meta.names()
                         if n not in ("instance_id", "repetition", "runstatus")]

        # Конвертируем в numpy
        instance_ids = [str(row["instance_id"]) for row in feature_data]
        features = np.array([[row[n] for n in feature_names] for row in feature_data])
        performance = np.array([[row[n] for n in algorithm_names] for row in perf_data])

        log.info(f"Loaded ASlib scenario from {path}")
        log.info(f"  Instances: {len(instance_ids)}")
        log.info(f"  Features: {len(feature_names)}")
        log.info(f"  Algorithms: {len(algorithm_names)}")

        return ASLibScenario(
            name=path.name,
            features=features,
            feature_names=feature_names,
            performance=performance,
            algorithm_names=algorithm_names,
            instance_ids=instance_ids
        )

    def _load_csv(self, path: Path) -> ASLibScenario:
        """Загружает CSV формат (упрощённый)."""
        import csv

        # Features
        with open(path / "features.csv") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            feature_names = [k for k in rows[0].keys() if k != "instance_id"]
            instance_ids = [r["instance_id"] for r in rows]
            features = np.array([[float(r[k]) for k in feature_names] for r in rows])

        # Performance
        with open(path / "performance.csv") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            algorithm_names = [k for k in rows[0].keys() if k != "instance_id"]
            performance = np.array([[float(r[k]) for k in algorithm_names] for r in rows])

        return ASLibScenario(
            name=path.name,
            features=features,
            feature_names=feature_names,
            performance=performance,
            algorithm_names=algorithm_names,
            instance_ids=instance_ids
        )

    def _generate_builtin(self, name: str) -> ASLibScenario:
        """Генерирует встроенный scenario с контролируемой diversity."""
        config = self.BUILTIN_SCENARIOS[name]
        rng = np.random.default_rng(42)

        n = config["n_instances"]
        n_feat = config["n_features"]
        n_alg = config["n_algorithms"]
        diversity = config["diversity"]

        # Генерируем features (кластеры в feature space)
        n_clusters = n_alg
        features = np.zeros((n, n_feat))
        true_best = np.zeros(n, dtype=int)

        for i in range(n):
            cluster = i % n_clusters
            # Features зависят от кластера
            features[i] = rng.normal(cluster * 2, 1, n_feat)
            # С вероятностью diversity, лучший алгоритм = кластер
            if rng.random() < diversity:
                true_best[i] = cluster
            else:
                true_best[i] = rng.integers(0, n_alg)

        # Генерируем performance matrix
        performance = np.zeros((n, n_alg))
        for i in range(n):
            for a in range(n_alg):
                if a == true_best[i]:
                    # Лучший алгоритм: низкий runtime
                    performance[i, a] = rng.exponential(1.0)
                else:
                    # Другие: выше runtime
                    performance[i, a] = rng.exponential(2.0) + 1.0

        log.info(f"Generated builtin scenario '{name}'")
        log.info(f"  Instances: {n}, Features: {n_feat}, Algorithms: {n_alg}")
        log.info(f"  Diversity: {diversity*100:.0f}%")

        return ASLibScenario(
            name=name,
            features=features,
            feature_names=[f"f{i}" for i in range(n_feat)],
            performance=performance,
            algorithm_names=config["algorithm_names"],
            instance_ids=[f"inst_{i}" for i in range(n)]
        )

    def get_fingerprints(self) -> np.ndarray:
        """Возвращает feature matrix."""
        return self.scenario.features.copy()

    def get_performance_matrix(self) -> np.ndarray:
        """Возвращает performance matrix (runtime/cost, lower is better)."""
        return self.scenario.performance.copy()

    def get_algorithm_names(self) -> List[str]:
        """Возвращает имена алгоритмов."""
        return self.scenario.algorithm_names.copy()

    def get_strategy_performance_dict(self, K: Optional[int] = None) -> Dict[str, np.ndarray]:
        """
        Возвращает performance в формате для FRARouter.

        Args:
            K: Использовать только первые K алгоритмов (None = все)
        """
        perf = self.scenario.performance
        names = self.scenario.algorithm_names

        if K is not None:
            K = min(K, len(names))
            names = names[:K]
            perf = perf[:, :K]

        return {names[k]: perf[:, k] for k in range(len(names))}

    def compute_metrics(self, pred_indices: np.ndarray) -> Dict:
        """
        Вычисляет ASlib-стандартные метрики.

        Args:
            pred_indices: Предсказанные индексы алгоритмов для каждого инстанса

        Returns:
            - par10: Penalized Average Runtime (таймаут = 10x)
            - vbs_gap: Gap to Virtual Best Solver
            - sbs_gap: Gap to Single Best Solver
        """
        perf = self.scenario.performance
        n = len(perf)

        # Predicted performance
        pred_perf = np.array([perf[i, pred_indices[i]] for i in range(n)])

        # Virtual Best Solver (oracle)
        vbs_perf = np.min(perf, axis=1)

        # Single Best Solver
        mean_per_alg = np.mean(perf, axis=0)
        sbs_idx = np.argmin(mean_per_alg)
        sbs_perf = perf[:, sbs_idx]

        # Метрики
        pred_mean = np.mean(pred_perf)
        vbs_mean = np.mean(vbs_perf)
        sbs_mean = np.mean(sbs_perf)

        return {
            "predicted_mean": pred_mean,
            "vbs_mean": vbs_mean,
            "sbs_mean": sbs_mean,
            "vbs_gap": (pred_mean - vbs_mean) / vbs_mean * 100 if vbs_mean > 0 else 0,
            "sbs_gap": (pred_mean - sbs_mean) / sbs_mean * 100 if sbs_mean > 0 else 0,
            "improvement_over_sbs": (sbs_mean - pred_mean) / sbs_mean * 100 if sbs_mean > 0 else 0
        }


def test_aslib_problem():
    """Тест ASLibProblem."""
    print("=" * 60)
    print("Testing ASLibProblem")
    print("=" * 60)

    # Тест builtin scenario
    for name in ["sat-mini", "tsp-mini"]:
        print(f"\n--- {name} ---")
        problem = ASLibProblem(scenario_name=name)

        features = problem.get_fingerprints()
        perf = problem.get_performance_matrix()
        names = problem.get_algorithm_names()

        print(f"Features: {features.shape}")
        print(f"Performance: {perf.shape}")
        print(f"Algorithms: {names}")

        # Проверяем NaN
        assert not np.any(np.isnan(features)), "NaN in features"
        assert not np.any(np.isnan(perf)), "NaN in performance"

        # Тест метрик
        oracle_idx = np.argmin(perf, axis=1)
        metrics = problem.compute_metrics(oracle_idx)
        print(f"Oracle metrics: VBS gap = {metrics['vbs_gap']:.2f}%")

        # Тест strategy dict
        strat_dict = problem.get_strategy_performance_dict(K=3)
        print(f"Strategy dict (K=3): {list(strat_dict.keys())}")

    print("\n✅ All ASlib tests passed!")
    return True


if __name__ == "__main__":
    test_aslib_problem()
