"""
Синтетическая задача с контролируемой diversity.

Ключевая идея: создаём "задачу" где мы ЗНАЕМ какая стратегия лучше для какого типа инстанса.
Это позволяет проверить работает ли FRA-роутер в идеальных условиях.
"""

import numpy as np
from dataclasses import dataclass
from typing import List, Dict, Tuple, Optional
import logging

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)


@dataclass
class SyntheticInstance:
    """Синтетический инстанс."""
    id: str
    features: np.ndarray  # d-мерный fingerprint
    true_type: int        # Истинный тип (какая стратегия оптимальна)


@dataclass
class SyntheticConfig:
    """Конфигурация синтетической задачи."""
    n_instances: int = 200      # Общее число инстансов
    n_types: int = 4            # Число типов (кластеров)
    d: int = 16                 # Размерность fingerprint
    noise_level: float = 0.1   # Шум в performance (0-1)
    cluster_std: float = 1.0   # Разброс внутри кластера
    cluster_separation: float = 5.0  # Расстояние между центроидами
    seed: int = 42


class SyntheticProblem:
    """
    Синтетическая задача для proof-of-concept FRA.

    Структура:
    - n_types кластеров в d-мерном пространстве
    - Стратегия k оптимальна для инстансов типа k
    - Performance зависит от расстояния до "своего" центроида
    """

    def __init__(self, config: SyntheticConfig):
        self.config = config
        self.rng = np.random.default_rng(config.seed)

        # Генерируем центроиды кластеров
        self.centroids = self._generate_centroids()

        # Генерируем инстансы
        self.instances = self._generate_instances()

        log.info(f"SyntheticProblem: {config.n_instances} instances, "
                f"{config.n_types} types, d={config.d}")

    def _generate_centroids(self) -> np.ndarray:
        """Генерирует центроиды кластеров, равномерно распределённые."""
        n_types = self.config.n_types
        d = self.config.d
        sep = self.config.cluster_separation

        # Размещаем центроиды на гиперкубе
        # Простая схема: используем углы гиперкуба
        centroids = np.zeros((n_types, d))
        for i in range(n_types):
            # Бинарное представление i задаёт позицию
            for j in range(min(d, 10)):  # Используем до 10 бит
                if (i >> j) & 1:
                    centroids[i, j] = sep

        # Добавляем случайный сдвиг для разнообразия
        centroids += self.rng.normal(0, sep/4, centroids.shape)

        return centroids

    def _generate_instances(self) -> List[SyntheticInstance]:
        """Генерирует инстансы вокруг центроидов."""
        instances = []
        n_per_type = self.config.n_instances // self.config.n_types

        for t in range(self.config.n_types):
            for i in range(n_per_type):
                # Генерируем точку вокруг центроида
                features = self.centroids[t] + self.rng.normal(
                    0, self.config.cluster_std, self.config.d
                )

                instance = SyntheticInstance(
                    id=f"type{t}_inst{i}",
                    features=features,
                    true_type=t
                )
                instances.append(instance)

        # Перемешиваем
        self.rng.shuffle(instances)
        return instances

    def get_fingerprints(self) -> np.ndarray:
        """Возвращает матрицу fingerprints [n_instances, d]."""
        return np.array([inst.features for inst in self.instances])

    def get_true_labels(self) -> np.ndarray:
        """Возвращает истинные типы инстансов."""
        return np.array([inst.true_type for inst in self.instances])

    def compute_performance_matrix(self, K: int) -> np.ndarray:
        """
        Вычисляет матрицу performance [n_instances, K].

        Логика:
        - Стратегия k оптимальна для типа k (если k < n_types)
        - Performance = base_cost + penalty * distance_to_optimal
        - Добавляем шум

        Returns:
            performance[i, k] = "cost" стратегии k на инстансе i (меньше = лучше)
        """
        n = len(self.instances)
        n_types = self.config.n_types
        noise = self.config.noise_level

        performance = np.zeros((n, K))

        for i, inst in enumerate(self.instances):
            true_type = inst.true_type

            for k in range(K):
                # Базовая стоимость
                base_cost = 1.0

                if k < n_types:
                    # Стратегия k оптимальна для типа k
                    if k == true_type:
                        # Оптимальная стратегия — низкая стоимость
                        cost = base_cost
                    else:
                        # Не-оптимальная — штраф пропорционален "расстоянию" типов
                        type_distance = min(abs(k - true_type), n_types - abs(k - true_type))
                        cost = base_cost + 0.5 * type_distance
                else:
                    # Дополнительные стратегии (K > n_types) — средняя производительность
                    cost = base_cost + 0.25 * n_types

                # Добавляем шум
                cost += self.rng.normal(0, noise * base_cost)

                # Гарантируем положительность
                performance[i, k] = max(0.01, cost)

        return performance

    def get_strategy_names(self, K: int) -> List[str]:
        """Возвращает имена стратегий."""
        return [f"strategy_{k}" for k in range(K)]

    def get_oracle_performance(self, performance: np.ndarray) -> np.ndarray:
        """Oracle выбирает лучшую стратегию для каждого инстанса."""
        return np.min(performance, axis=1)

    def get_best_single_performance(self, performance: np.ndarray) -> Tuple[np.ndarray, int, str]:
        """Лучшая одиночная стратегия (по среднему)."""
        mean_perf = np.mean(performance, axis=0)
        best_k = np.argmin(mean_perf)
        return performance[:, best_k], best_k, f"strategy_{best_k}"


def test_synthetic_problem():
    """Тест синтетической задачи."""
    print("=" * 60)
    print("Testing SyntheticProblem")
    print("=" * 60)

    config = SyntheticConfig(
        n_instances=100,
        n_types=4,
        d=8,
        noise_level=0.05,
        seed=42
    )

    problem = SyntheticProblem(config)

    # Проверяем fingerprints
    fingerprints = problem.get_fingerprints()
    print(f"Fingerprints shape: {fingerprints.shape}")
    assert fingerprints.shape == (100, 8), "Wrong fingerprint shape"
    assert not np.any(np.isnan(fingerprints)), "NaN in fingerprints"

    # Проверяем labels
    labels = problem.get_true_labels()
    print(f"Labels: {np.bincount(labels)}")
    assert len(labels) == 100, "Wrong labels count"

    # Проверяем performance matrix
    for K in [2, 4, 8]:
        perf = problem.compute_performance_matrix(K)
        print(f"\nK={K}:")
        print(f"  Performance shape: {perf.shape}")
        print(f"  Mean per strategy: {np.mean(perf, axis=0).round(3)}")

        oracle = problem.get_oracle_performance(perf)
        best_single, best_k, best_name = problem.get_best_single_performance(perf)

        print(f"  Oracle mean: {np.mean(oracle):.3f}")
        print(f"  Best single ({best_name}): {np.mean(best_single):.3f}")

        # При K >= n_types, оракул должен быть значительно лучше
        if K >= config.n_types:
            assert np.mean(oracle) < np.mean(best_single), \
                f"Oracle should beat best single when K >= n_types"

    print("\n✅ All tests passed!")
    return True


if __name__ == "__main__":
    test_synthetic_problem()
