#!/usr/bin/env python3
"""
FRA Scaling Hypothesis 1.4 — Experiment Runner v2

Проверяет гипотезу K = O(1/ε^d) на:
1. Синтетических данных (proof-of-concept)
2. ASlib scenarios (validation)

Defensive programming: все edge cases обработаны.
"""

import os
import sys
import json
import time
import logging
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from pathlib import Path

import numpy as np
from sklearn.decomposition import PCA
from scipy import stats

# Настройка логирования
os.environ['PYTHONUNBUFFERED'] = '1'
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s',
    datefmt='%H:%M:%S'
)
log = logging.getLogger(__name__)

# Добавляем путь к модулям
sys.path.insert(0, str(Path(__file__).parent))

from problems.synthetic import SyntheticProblem, SyntheticConfig
from problems.aslib import ASLibProblem
from fra.router import FRARouter, RouterConfig


@dataclass
class ExperimentResult:
    """Результат одной конфигурации эксперимента."""
    problem: str
    d: int
    K: int
    n_instances: int
    train_instances: int
    test_instances: int

    # Performance metrics
    fra_cost_train: float
    fra_cost_test: float
    best_single_cost: float
    best_single_name: str
    oracle_cost: float

    # Derived metrics
    fra_win_rate: float          # % случаев когда FRA лучше best single
    improvement_over_single: float  # (best_single - fra) / best_single
    gap_to_oracle: float         # (fra - oracle) / oracle

    # Router metrics
    routing_accuracy: float
    training_time: float
    final_val_loss: float
    final_val_acc: float

    timestamp: str


class FRAScalingExperiment:
    """Главный класс эксперимента."""

    def __init__(self, output_dir: str = "results/synthetic"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.results: List[ExperimentResult] = []

    def run_synthetic_experiment(
        self,
        n_instances: int = 200,
        n_types: int = 4,
        K_values: List[int] = [2, 4, 8, 16],
        d_values: List[int] = [4, 8, 16, 32],
        noise_level: float = 0.1,
        seed: int = 42
    ):
        """
        Запускает эксперимент на синтетических данных.

        Grid:
        - vary_K: фиксированный d=16, варьируем K
        - vary_d: фиксированный K=8, варьируем d
        """
        log.info("=" * 60)
        log.info("SYNTHETIC EXPERIMENT")
        log.info("=" * 60)

        # Grid 1: Vary K at fixed d
        fixed_d = 16
        log.info(f"\n--- Varying K at d={fixed_d} ---")
        for K in K_values:
            self._run_single_config(
                n_instances=n_instances,
                n_types=n_types,
                d=fixed_d,
                K=K,
                noise_level=noise_level,
                seed=seed
            )

        # Grid 2: Vary d at fixed K
        fixed_K = 8
        log.info(f"\n--- Varying d at K={fixed_K} ---")
        for d in d_values:
            if d == fixed_d:
                continue  # Уже запускали в первом grid
            self._run_single_config(
                n_instances=n_instances,
                n_types=n_types,
                d=d,
                K=fixed_K,
                noise_level=noise_level,
                seed=seed
            )

        # Анализ результатов
        self._analyze_results()

    def _run_single_config(
        self,
        n_instances: int,
        n_types: int,
        d: int,
        K: int,
        noise_level: float,
        seed: int
    ):
        """Запускает один конфиг эксперимента."""
        log.info(f"\n{'='*60}")
        log.info(f"Running: d={d}, K={K}")
        log.info(f"{'='*60}")

        try:
            # 1. Создаём синтетическую задачу
            config = SyntheticConfig(
                n_instances=n_instances,
                n_types=n_types,
                d=d,
                noise_level=noise_level,
                seed=seed
            )
            problem = SyntheticProblem(config)

            # 2. Получаем данные
            fingerprints = problem.get_fingerprints()
            true_labels = problem.get_true_labels()
            performance = problem.compute_performance_matrix(K)

            log.info(f"  Instances: {len(fingerprints)}")
            log.info(f"  Fingerprint dim: {fingerprints.shape[1]}")
            log.info(f"  Strategies: {K}")

            # 3. Defensive: проверяем на NaN/Inf
            fingerprints = np.nan_to_num(fingerprints, nan=0.0, posinf=1e6, neginf=-1e6)
            performance = np.nan_to_num(performance, nan=1e6, posinf=1e6, neginf=-1e6)

            # 4. PCA если нужно (d < native dimension)
            n_samples, n_features = fingerprints.shape
            actual_d = min(d, n_samples - 1, n_features)
            if n_features > actual_d:
                log.info(f"  PCA: {n_features} -> {actual_d}")
                pca = PCA(n_components=actual_d)
                fingerprints = pca.fit_transform(fingerprints)

            # 5. Train/test split
            n = len(fingerprints)
            indices = np.random.default_rng(seed).permutation(n)
            split_idx = int(n * 0.7)
            train_idx = indices[:split_idx]
            test_idx = indices[split_idx:]

            X_train = fingerprints[train_idx]
            X_test = fingerprints[test_idx]
            perf_train = performance[train_idx]
            perf_test = performance[test_idx]
            labels_test = true_labels[test_idx]

            log.info(f"  Train: {len(train_idx)}, Test: {len(test_idx)}")

            # 6. Определяем лучшую стратегию для каждого инстанса (ground truth)
            best_strategy_train = np.argmin(perf_train, axis=1)
            best_strategy_test = np.argmin(perf_test, axis=1)

            # 7. Конвертируем performance в формат для FRARouter (dict)
            strategy_names = problem.get_strategy_names(K)
            strategy_perf_train = {
                strategy_names[k]: perf_train[:, k]
                for k in range(K)
            }
            strategy_perf_test = {
                strategy_names[k]: perf_test[:, k]
                for k in range(K)
            }

            # 8. Обучаем FRA router
            final_dim = X_train.shape[1]
            router_config = RouterConfig(
                input_dim=final_dim,  # Используем реальную размерность!
                n_strategies=K,       # Исправлено: n_strategies вместо num_strategies
                hidden_layers=[64, 32],
                dropout=0.1,
                learning_rate=0.003,
                batch_size=min(64, len(train_idx)),
                epochs=50,
                early_stopping_patience=10
            )

            router = FRARouter(router_config)

            start_time = time.time()
            history = router.fit(X_train, strategy_perf_train)
            training_time = time.time() - start_time

            log.info(f"  Training time: {training_time:.1f}s")

            # 9. Оцениваем на тесте
            eval_result = router.evaluate(X_test, strategy_perf_test)

            # Также получаем предсказания для детального анализа
            pred_test = router.model.predict(
                (X_test - router.feature_mean) / router.feature_std
            )

            # 10. Извлекаем метрики из eval_result
            fra_cost_test = eval_result["fra_gap"]
            best_single_cost = eval_result["best_single_gap"]
            best_single_name = eval_result["best_single_name"]
            oracle_cost = eval_result["oracle_gap"]
            routing_accuracy = eval_result["routing_accuracy"]
            improvement = eval_result["improvement_over_single"]
            gap_to_oracle = eval_result["gap_to_oracle"]

            # FRA win rate = % инстансов где FRA лучше best single
            fra_costs = np.array([perf_test[i, pred_test[i]] for i in range(len(test_idx))])
            best_single_k = list(strategy_names).index(best_single_name)
            single_costs = perf_test[:, best_single_k]
            fra_win_rate = np.mean(fra_costs < single_costs)

            # FRA cost на train (для полноты)
            pred_train_idx = router.model.predict(
                (X_train - router.feature_mean) / router.feature_std
            )
            fra_cost_train = np.mean([perf_train[i, pred_train_idx[i]] for i in range(len(train_idx))])

            log.info(f"  FRA cost (test): {fra_cost_test:.4f}")
            log.info(f"  Best single ({best_single_name}): {best_single_cost:.4f}")
            log.info(f"  Oracle: {oracle_cost:.4f}")
            log.info(f"  FRA win rate: {fra_win_rate*100:.1f}%")
            log.info(f"  Improvement: {improvement:.2f}%")
            log.info(f"  Routing accuracy: {routing_accuracy*100:.1f}%")

            # 10. Сохраняем результат
            result = ExperimentResult(
                problem="synthetic",
                d=d,
                K=K,
                n_instances=n_instances,
                train_instances=len(train_idx),
                test_instances=len(test_idx),
                fra_cost_train=float(fra_cost_train),
                fra_cost_test=float(fra_cost_test),
                best_single_cost=float(best_single_cost),
                best_single_name=best_single_name,
                oracle_cost=float(oracle_cost),
                fra_win_rate=float(fra_win_rate),
                improvement_over_single=float(improvement),
                gap_to_oracle=float(gap_to_oracle),
                routing_accuracy=float(routing_accuracy),
                training_time=float(training_time),
                final_val_loss=float(history.get('val_loss', [0])[-1]) if history else 0.0,
                final_val_acc=float(history.get('val_acc', [0])[-1]) if history else 0.0,
                timestamp=datetime.now().isoformat()
            )

            self.results.append(result)
            self._save_results()
            log.info(f"  ✓ Config saved ({len(self.results)} total)")

        except Exception as e:
            log.error(f"  ✗ Error: {e}")
            import traceback
            traceback.print_exc()

    def _save_results(self):
        """Сохраняет результаты в JSON."""
        output_file = self.output_dir / "experiment_results.json"
        with open(output_file, 'w') as f:
            json.dump([asdict(r) for r in self.results], f, indent=2)

    def _analyze_results(self):
        """Анализирует результаты и проверяет гипотезу."""
        log.info("\n" + "=" * 60)
        log.info("ANALYSIS")
        log.info("=" * 60)

        if len(self.results) < 2:
            log.warning("Not enough results for analysis")
            return

        # Извлекаем данные
        K_values = [r.K for r in self.results]
        d_values = [r.d for r in self.results]
        gaps = [r.gap_to_oracle for r in self.results]
        improvements = [r.improvement_over_single for r in self.results]
        win_rates = [r.fra_win_rate for r in self.results]

        # Корреляция K vs gap (при фиксированном d)
        fixed_d_results = [r for r in self.results if r.d == 16]
        if len(fixed_d_results) >= 3:
            K_vals = [r.K for r in fixed_d_results]
            gap_vals = [r.gap_to_oracle for r in fixed_d_results]
            corr_K, p_K = stats.spearmanr(K_vals, gap_vals)
            log.info(f"\nCorrelation (K vs gap @ d=16): r={corr_K:.3f}, p={p_K:.4f}")
        else:
            corr_K, p_K = 0, 1

        # Корреляция d vs gap (при фиксированном K)
        fixed_K_results = [r for r in self.results if r.K == 8]
        if len(fixed_K_results) >= 3:
            d_vals = [r.d for r in fixed_K_results]
            gap_vals = [r.gap_to_oracle for r in fixed_K_results]
            corr_d, p_d = stats.spearmanr(d_vals, gap_vals)
            log.info(f"Correlation (d vs gap @ K=8): r={corr_d:.3f}, p={p_d:.4f}")
        else:
            corr_d, p_d = 0, 1

        # Средние метрики
        avg_win_rate = np.mean(win_rates)
        avg_improvement = np.mean(improvements)

        log.info(f"\nAverage FRA win rate: {avg_win_rate*100:.1f}%")
        log.info(f"Average improvement: {avg_improvement:.2f}%")

        # Проверка гипотезы (proof-of-concept)
        # Критерии:
        # 1. FRA побеждает best single чаще чем проигрывает (win rate > 50%)
        # 2. Среднее улучшение > 10%
        # 3. При K >= n_types (4), FRA достигает near-oracle (gap < 5%)

        high_K_results = [r for r in self.results if r.K >= 4]
        avg_gap_high_K = np.mean([r.gap_to_oracle for r in high_K_results]) if high_K_results else 100

        hypothesis_confirmed = (
            avg_win_rate > 0.5 and        # FRA побеждает чаще
            avg_improvement > 10 and       # Значимое улучшение
            avg_gap_high_K < 5             # Near-oracle при достаточном K
        )

        log.info(f"\n{'='*60}")
        if hypothesis_confirmed:
            log.info(">>> PROOF-OF-CONCEPT: SUCCESSFUL <<<")
            log.info("FRA routing works on synthetic data with controlled diversity!")
            log.info(f"  - Win rate: {avg_win_rate*100:.1f}% (>50%)")
            log.info(f"  - Improvement: {avg_improvement:.1f}% (>10%)")
            log.info(f"  - Gap to oracle (K>=4): {avg_gap_high_K:.2f}% (<5%)")
        else:
            log.info(">>> PROOF-OF-CONCEPT: FAILED <<<")
            log.info("FRA routing does not meet success criteria.")
            log.info(f"  - Win rate: {avg_win_rate*100:.1f}% (need >50%)")
            log.info(f"  - Improvement: {avg_improvement:.1f}% (need >10%)")
            log.info(f"  - Gap to oracle (K>=4): {avg_gap_high_K:.2f}% (need <5%)")
        log.info(f"{'='*60}")

        # Сохраняем анализ
        analysis = {
            "correlation_K_gap": {"r": float(corr_K), "p": float(p_K)},
            "correlation_d_gap": {"r": float(corr_d), "p": float(p_d)},
            "avg_win_rate": float(avg_win_rate),
            "avg_improvement": float(avg_improvement),
            "hypothesis_confirmed": bool(hypothesis_confirmed),
            "n_configs": len(self.results)
        }

        analysis_file = self.output_dir / "hypothesis_analysis.json"
        with open(analysis_file, 'w') as f:
            json.dump(analysis, f, indent=2)

        log.info(f"\nResults saved to: {self.output_dir}")

    def run_aslib_experiment(
        self,
        scenarios: List[str] = ["sat-mini", "tsp-mini"],
        K_values: List[int] = [2, 4, 8],
        d_values: List[int] = [4, 8, 16],
        seed: int = 42
    ):
        """
        Запускает эксперимент на ASlib scenarios.

        Args:
            scenarios: Список scenario names (builtin или paths)
            K_values: Варьируем K (число стратегий)
            d_values: Варьируем d (PCA dimension)
        """
        log.info("=" * 60)
        log.info("ASLIB EXPERIMENT")
        log.info("=" * 60)

        for scenario_name in scenarios:
            log.info(f"\n{'='*60}")
            log.info(f"SCENARIO: {scenario_name}")
            log.info(f"{'='*60}")

            try:
                problem = ASLibProblem(scenario_name=scenario_name)
            except Exception as e:
                log.error(f"Failed to load scenario {scenario_name}: {e}")
                continue

            # Grid 1: Vary K at native d
            for K in K_values:
                self._run_aslib_config(problem, scenario_name, K=K, d=None, seed=seed)

            # Grid 2: Vary d at fixed K
            fixed_K = 4
            for d in d_values:
                self._run_aslib_config(problem, scenario_name, K=fixed_K, d=d, seed=seed)

        # Анализ
        self._analyze_results()

    def _run_aslib_config(
        self,
        problem: ASLibProblem,
        scenario_name: str,
        K: int,
        d: Optional[int],
        seed: int
    ):
        """Запускает один конфиг ASlib эксперимента."""
        log.info(f"\n--- {scenario_name} | K={K} | d={'native' if d is None else d} ---")

        try:
            # 1. Получаем данные
            fingerprints = problem.get_fingerprints()
            perf_matrix = problem.get_performance_matrix()
            algorithm_names = problem.get_algorithm_names()

            # Ограничиваем K
            K = min(K, len(algorithm_names))
            perf_matrix = perf_matrix[:, :K]
            algorithm_names = algorithm_names[:K]

            n_instances = len(fingerprints)
            native_d = fingerprints.shape[1]

            log.info(f"  Instances: {n_instances}, Native features: {native_d}, K: {K}")

            # 2. Defensive: NaN handling
            fingerprints = np.nan_to_num(fingerprints, nan=0.0, posinf=1e6, neginf=-1e6)
            perf_matrix = np.nan_to_num(perf_matrix, nan=1e6, posinf=1e6, neginf=-1e6)

            # 3. PCA если нужно
            actual_d = d if d is not None else native_d
            actual_d = min(actual_d, n_instances - 1, native_d)

            if native_d > actual_d:
                log.info(f"  PCA: {native_d} -> {actual_d}")
                pca = PCA(n_components=actual_d)
                fingerprints = pca.fit_transform(fingerprints)

            # 4. Train/test split
            rng = np.random.default_rng(seed)
            indices = rng.permutation(n_instances)
            split_idx = int(n_instances * 0.7)
            train_idx = indices[:split_idx]
            test_idx = indices[split_idx:]

            X_train = fingerprints[train_idx]
            X_test = fingerprints[test_idx]
            perf_train = perf_matrix[train_idx]
            perf_test = perf_matrix[test_idx]

            log.info(f"  Train: {len(train_idx)}, Test: {len(test_idx)}")

            # 5. Конвертируем в dict формат
            strategy_perf_train = {algorithm_names[k]: perf_train[:, k] for k in range(K)}
            strategy_perf_test = {algorithm_names[k]: perf_test[:, k] for k in range(K)}

            # 6. Обучаем FRA router
            final_dim = X_train.shape[1]
            router_config = RouterConfig(
                input_dim=final_dim,
                n_strategies=K,
                hidden_layers=[64, 32],
                dropout=0.1,
                learning_rate=0.003,
                batch_size=min(64, len(train_idx)),
                epochs=50,
                early_stopping_patience=10
            )

            router = FRARouter(router_config)

            start_time = time.time()
            history = router.fit(X_train, strategy_perf_train)
            training_time = time.time() - start_time

            log.info(f"  Training time: {training_time:.1f}s")

            # 7. Оцениваем
            eval_result = router.evaluate(X_test, strategy_perf_test)

            # 8. Дополнительные метрики
            pred_test = router.model.predict(
                (X_test - router.feature_mean) / router.feature_std
            )
            fra_costs = np.array([perf_test[i, pred_test[i]] for i in range(len(test_idx))])
            best_single_k = list(algorithm_names).index(eval_result["best_single_name"])
            single_costs = perf_test[:, best_single_k]
            fra_win_rate = np.mean(fra_costs < single_costs)

            # FRA on train
            pred_train = router.model.predict(
                (X_train - router.feature_mean) / router.feature_std
            )
            fra_cost_train = np.mean([perf_train[i, pred_train[i]] for i in range(len(train_idx))])

            log.info(f"  FRA: {eval_result['fra_gap']:.4f}, Single: {eval_result['best_single_gap']:.4f}")
            log.info(f"  Improvement: {eval_result['improvement_over_single']:.2f}%")
            log.info(f"  Routing accuracy: {eval_result['routing_accuracy']*100:.1f}%")

            # 9. Сохраняем результат
            result = ExperimentResult(
                problem=f"aslib_{scenario_name}",
                d=actual_d,
                K=K,
                n_instances=n_instances,
                train_instances=len(train_idx),
                test_instances=len(test_idx),
                fra_cost_train=float(fra_cost_train),
                fra_cost_test=float(eval_result["fra_gap"]),
                best_single_cost=float(eval_result["best_single_gap"]),
                best_single_name=eval_result["best_single_name"],
                oracle_cost=float(eval_result["oracle_gap"]),
                fra_win_rate=float(fra_win_rate),
                improvement_over_single=float(eval_result["improvement_over_single"]),
                gap_to_oracle=float(eval_result["gap_to_oracle"]),
                routing_accuracy=float(eval_result["routing_accuracy"]),
                training_time=float(training_time),
                final_val_loss=float(history.get('val_loss', [0])[-1]) if history else 0.0,
                final_val_acc=float(history.get('val_acc', [0])[-1]) if history else 0.0,
                timestamp=datetime.now().isoformat()
            )

            self.results.append(result)
            self._save_results()
            log.info(f"  ✓ Config saved ({len(self.results)} total)")

        except Exception as e:
            log.error(f"  ✗ Error: {e}")
            import traceback
            traceback.print_exc()

    def print_summary_table(self):
        """Выводит таблицу результатов."""
        if not self.results:
            return

        print("\n" + "=" * 90)
        print(f"{'Problem':<20} {'d':>4} {'K':>4} {'FRA':>8} {'Single':>8} {'Oracle':>8} {'Win%':>6} {'Impr%':>7} {'Acc%':>6}")
        print("-" * 90)

        for r in sorted(self.results, key=lambda x: (x.problem, x.d, x.K)):
            print(f"{r.problem:<20} {r.d:>4} {r.K:>4} {r.fra_cost_test:>8.4f} {r.best_single_cost:>8.4f} "
                  f"{r.oracle_cost:>8.4f} {r.fra_win_rate*100:>6.1f} {r.improvement_over_single:>7.2f} "
                  f"{r.routing_accuracy*100:>6.1f}")
        print("=" * 90)


def main():
    """Главная функция."""
    log.info("FRA Scaling Hypothesis 1.4 — Experiment v2")
    log.info(f"Started at: {datetime.now().isoformat()}")

    # ========================================
    # ФАЗА 1: Синтетический proof-of-concept
    # ========================================
    log.info("\n" + "#" * 60)
    log.info("# PHASE 1: SYNTHETIC PROOF-OF-CONCEPT")
    log.info("#" * 60)

    synthetic_exp = FRAScalingExperiment(
        output_dir="/Users/figuramax/LocalProjects/adaptive-topology/experiments/fra_scaling_v2/results/synthetic"
    )

    synthetic_exp.run_synthetic_experiment(
        n_instances=200,
        n_types=4,
        K_values=[2, 4, 8, 16],
        d_values=[4, 8, 16, 32],
        noise_level=0.1,
        seed=42
    )

    synthetic_exp.print_summary_table()

    # ========================================
    # ФАЗА 2: ASlib validation
    # ========================================
    log.info("\n" + "#" * 60)
    log.info("# PHASE 2: ASLIB VALIDATION")
    log.info("#" * 60)

    aslib_exp = FRAScalingExperiment(
        output_dir="/Users/figuramax/LocalProjects/adaptive-topology/experiments/fra_scaling_v2/results/aslib"
    )

    aslib_exp.run_aslib_experiment(
        scenarios=["sat-mini", "tsp-mini"],
        K_values=[2, 4],
        d_values=[4, 8],
        seed=42
    )

    aslib_exp.print_summary_table()

    # ========================================
    # ФИНАЛЬНЫЙ ОТЧЁТ
    # ========================================
    log.info("\n" + "#" * 60)
    log.info("# FINAL REPORT")
    log.info("#" * 60)

    # Объединяем результаты
    all_results = synthetic_exp.results + aslib_exp.results
    synthetic_win_rates = [r.fra_win_rate for r in synthetic_exp.results]
    aslib_win_rates = [r.fra_win_rate for r in aslib_exp.results]

    log.info(f"\nSynthetic experiments: {len(synthetic_exp.results)} configs")
    log.info(f"  Average win rate: {np.mean(synthetic_win_rates)*100:.1f}%")
    log.info(f"  Average improvement: {np.mean([r.improvement_over_single for r in synthetic_exp.results]):.1f}%")

    log.info(f"\nASlib experiments: {len(aslib_exp.results)} configs")
    log.info(f"  Average win rate: {np.mean(aslib_win_rates)*100:.1f}%")
    log.info(f"  Average improvement: {np.mean([r.improvement_over_single for r in aslib_exp.results]):.1f}%")

    # Вердикт
    overall_win_rate = np.mean(synthetic_win_rates + aslib_win_rates)
    overall_improvement = np.mean([r.improvement_over_single for r in all_results])

    log.info(f"\n{'='*60}")
    log.info("OVERALL VERDICT")
    log.info(f"{'='*60}")

    if overall_win_rate > 0.5 and overall_improvement > 10:
        log.info("✅ FRA ROUTING VALIDATED")
        log.info(f"   Win rate: {overall_win_rate*100:.1f}% (>50%)")
        log.info(f"   Improvement: {overall_improvement:.1f}% (>10%)")
        log.info("\n   FRA-роутинг работает когда есть diversity в данных.")
        log.info("   Гипотеза 1.4 требует проверки на реальных ASlib scenarios.")
    else:
        log.info("❌ FRA ROUTING NOT VALIDATED")
        log.info(f"   Win rate: {overall_win_rate*100:.1f}%")
        log.info(f"   Improvement: {overall_improvement:.1f}%")

    log.info(f"\nCompleted at: {datetime.now().isoformat()}")


if __name__ == "__main__":
    main()
