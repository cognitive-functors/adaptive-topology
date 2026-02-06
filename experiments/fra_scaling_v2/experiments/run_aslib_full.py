#!/usr/bin/env python3
"""
Full FRA experiment on real ASlib scenarios.
"""

import os
import sys
import json
import time
import logging
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, asdict
from typing import List, Dict, Optional

import numpy as np
from sklearn.decomposition import PCA
from scipy import stats

os.environ['PYTHONUNBUFFERED'] = '1'
logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(message)s')
log = logging.getLogger(__name__)

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))
from fra.router import FRARouter, RouterConfig


@dataclass
class ASLibResult:
    """Result for one ASlib configuration."""
    scenario: str
    n_instances: int
    n_algorithms: int
    n_features: int
    d: int  # PCA dimension used
    K: int  # Number of algorithms used

    # Performance
    fra_par10: float
    sbs_par10: float
    vbs_par10: float

    # Metrics
    improvement_over_sbs: float
    gap_to_vbs: float
    routing_accuracy: float

    # Diversity
    diversity_score: float

    # Training
    training_time: float
    timestamp: str


def load_scenario(scenario_dir: Path) -> dict:
    """Load processed ASlib scenario."""
    data = np.load(scenario_dir / "processed.npz", allow_pickle=True)
    with open(scenario_dir / "metadata.json") as f:
        meta = json.load(f)

    return {
        "features": data["features"],
        "performance": data["performance"],
        "algorithms": meta["algorithms"],
        "diversity": meta["diversity"]
    }


def run_fra_experiment(
    features: np.ndarray,
    performance: np.ndarray,
    algorithms: List[str],
    K: int,
    d: Optional[int],
    seed: int = 42
) -> dict:
    """Run FRA experiment on ASlib data."""
    n_instances, n_features = features.shape
    n_algos = len(algorithms)

    # Limit K
    K = min(K, n_algos)
    perf_K = performance[:, :K]
    algos_K = algorithms[:K]

    # Handle NaN in features
    features = np.nan_to_num(features, nan=0.0, posinf=1e6, neginf=-1e6)

    # PCA if needed
    actual_d = d if d else n_features
    actual_d = min(actual_d, n_instances - 1, n_features)

    if n_features > actual_d:
        pca = PCA(n_components=actual_d)
        features_pca = pca.fit_transform(features)
    else:
        features_pca = features
        actual_d = n_features

    # Train/test split
    rng = np.random.default_rng(seed)
    indices = rng.permutation(n_instances)
    split_idx = int(n_instances * 0.7)
    train_idx = indices[:split_idx]
    test_idx = indices[split_idx:]

    X_train = features_pca[train_idx]
    X_test = features_pca[test_idx]
    perf_train = perf_K[train_idx]
    perf_test = perf_K[test_idx]

    # Convert to dict format
    strat_perf_train = {algos_K[k]: perf_train[:, k] for k in range(K)}
    strat_perf_test = {algos_K[k]: perf_test[:, k] for k in range(K)}

    # Train FRA router
    router_config = RouterConfig(
        input_dim=actual_d,
        n_strategies=K,
        hidden_layers=[128, 64],
        dropout=0.2,
        learning_rate=0.001,
        batch_size=min(64, len(train_idx)),
        epochs=100,
        early_stopping_patience=15
    )

    router = FRARouter(router_config)

    start_time = time.time()
    router.fit(X_train, strat_perf_train)
    training_time = time.time() - start_time

    # Evaluate
    eval_result = router.evaluate(X_test, strat_perf_test)

    # Compute PAR10 scores
    pred_test = router.model.predict(
        (X_test - router.feature_mean) / router.feature_std
    )
    fra_times = np.array([perf_test[i, pred_test[i]] for i in range(len(test_idx))])
    fra_par10 = np.mean(fra_times)

    # SBS (Single Best Solver)
    sbs_idx = np.argmin(np.mean(perf_train, axis=0))
    sbs_par10 = np.mean(perf_test[:, sbs_idx])

    # VBS (Virtual Best Solver / Oracle)
    vbs_par10 = np.mean(np.min(perf_test, axis=1))

    return {
        "fra_par10": fra_par10,
        "sbs_par10": sbs_par10,
        "vbs_par10": vbs_par10,
        "improvement_over_sbs": (sbs_par10 - fra_par10) / sbs_par10 * 100,
        "gap_to_vbs": (fra_par10 - vbs_par10) / vbs_par10 * 100 if vbs_par10 > 0 else 0,
        "routing_accuracy": eval_result["routing_accuracy"],
        "training_time": training_time,
        "actual_d": actual_d,
        "actual_K": K
    }


def main():
    """Run full ASlib experiment."""
    log.info("=" * 70)
    log.info("FRA SCALING EXPERIMENT — REAL ASLIB DATA")
    log.info("=" * 70)

    data_dir = Path("/Users/figuramax/LocalProjects/adaptive-topology/experiments/fra_scaling_v2/data/aslib")
    results_dir = Path("/Users/figuramax/LocalProjects/adaptive-topology/experiments/fra_scaling_v2/results/aslib_real")
    results_dir.mkdir(parents=True, exist_ok=True)

    all_results = []

    # Grid
    K_values = [2, 4, 8, 16, 32]
    d_values = [8, 16, 32, None]  # None = native

    scenarios = ["SAT11-RAND", "SAT12-ALL", "CSP-2010"]

    for scenario_name in scenarios:
        scenario_dir = data_dir / scenario_name
        if not scenario_dir.exists():
            log.warning(f"Scenario {scenario_name} not found, skipping")
            continue

        log.info(f"\n{'='*70}")
        log.info(f"SCENARIO: {scenario_name}")
        log.info(f"{'='*70}")

        try:
            data = load_scenario(scenario_dir)
            features = data["features"]
            performance = data["performance"]
            algorithms = data["algorithms"]
            diversity = data["diversity"]

            n_instances, n_features = features.shape
            n_algos = len(algorithms)

            log.info(f"Instances: {n_instances}, Features: {n_features}, Algorithms: {n_algos}")
            log.info(f"Diversity: {diversity['diversity_score']:.1%}")

            # Run grid
            for K in K_values:
                if K > n_algos:
                    continue

                for d in d_values:
                    if d and d > n_features:
                        continue

                    d_str = str(d) if d else "native"
                    log.info(f"\n--- K={K}, d={d_str} ---")

                    try:
                        result = run_fra_experiment(
                            features, performance, algorithms,
                            K=K, d=d, seed=42
                        )

                        log.info(f"  FRA PAR10: {result['fra_par10']:.2f}")
                        log.info(f"  SBS PAR10: {result['sbs_par10']:.2f}")
                        log.info(f"  VBS PAR10: {result['vbs_par10']:.2f}")
                        log.info(f"  Improvement over SBS: {result['improvement_over_sbs']:.1f}%")
                        log.info(f"  Routing accuracy: {result['routing_accuracy']:.1%}")

                        aslib_result = ASLibResult(
                            scenario=scenario_name,
                            n_instances=n_instances,
                            n_algorithms=n_algos,
                            n_features=n_features,
                            d=result["actual_d"],
                            K=result["actual_K"],
                            fra_par10=result["fra_par10"],
                            sbs_par10=result["sbs_par10"],
                            vbs_par10=result["vbs_par10"],
                            improvement_over_sbs=result["improvement_over_sbs"],
                            gap_to_vbs=result["gap_to_vbs"],
                            routing_accuracy=result["routing_accuracy"],
                            diversity_score=diversity["diversity_score"],
                            training_time=result["training_time"],
                            timestamp=datetime.now().isoformat()
                        )

                        all_results.append(aslib_result)

                        # Save incrementally
                        with open(results_dir / "experiment_results.json", 'w') as f:
                            json.dump([asdict(r) for r in all_results], f, indent=2)

                    except Exception as e:
                        log.error(f"  Failed: {e}")
                        import traceback
                        traceback.print_exc()

        except Exception as e:
            log.error(f"Failed to load scenario: {e}")
            import traceback
            traceback.print_exc()

    # Analysis
    log.info("\n" + "=" * 70)
    log.info("ANALYSIS")
    log.info("=" * 70)

    if all_results:
        improvements = [r.improvement_over_sbs for r in all_results]
        accuracies = [r.routing_accuracy for r in all_results]

        log.info(f"\nTotal configs: {len(all_results)}")
        log.info(f"Mean improvement over SBS: {np.mean(improvements):.1f}%")
        log.info(f"Mean routing accuracy: {np.mean(accuracies):.1%}")

        # Per scenario
        for scenario in scenarios:
            scenario_results = [r for r in all_results if r.scenario == scenario]
            if scenario_results:
                impr = np.mean([r.improvement_over_sbs for r in scenario_results])
                acc = np.mean([r.routing_accuracy for r in scenario_results])
                log.info(f"\n{scenario}:")
                log.info(f"  Mean improvement: {impr:.1f}%")
                log.info(f"  Mean accuracy: {acc:.1%}")

        # Hypothesis test: FRA vs SBS
        fra_times = [r.fra_par10 for r in all_results]
        sbs_times = [r.sbs_par10 for r in all_results]

        stat, p_value = stats.wilcoxon(fra_times, sbs_times, alternative='less')
        log.info(f"\nWilcoxon test (FRA < SBS):")
        log.info(f"  Statistic: {stat:.2f}")
        log.info(f"  P-value: {p_value:.4f}")

        if p_value < 0.05:
            log.info("  ✅ FRA significantly better than SBS (p < 0.05)")
        else:
            log.info("  ⚠️ No significant difference (p >= 0.05)")

        # Save analysis
        analysis = {
            "n_configs": len(all_results),
            "mean_improvement": float(np.mean(improvements)),
            "mean_accuracy": float(np.mean(accuracies)),
            "wilcoxon_statistic": float(stat),
            "wilcoxon_pvalue": float(p_value),
            "significant": p_value < 0.05
        }

        with open(results_dir / "analysis.json", 'w') as f:
            json.dump(analysis, f, indent=2)

    # Print summary table
    print("\n" + "=" * 100)
    print(f"{'Scenario':<15} {'d':>6} {'K':>4} {'FRA':>10} {'SBS':>10} {'VBS':>10} {'Impr%':>8} {'Acc%':>6}")
    print("-" * 100)

    for r in sorted(all_results, key=lambda x: (x.scenario, x.d, x.K)):
        print(f"{r.scenario:<15} {r.d:>6} {r.K:>4} {r.fra_par10:>10.1f} {r.sbs_par10:>10.1f} "
              f"{r.vbs_par10:>10.1f} {r.improvement_over_sbs:>8.1f} {r.routing_accuracy*100:>6.1f}")

    print("=" * 100)

    log.info(f"\nResults saved to {results_dir}")


if __name__ == "__main__":
    main()
