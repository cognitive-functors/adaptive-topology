#!/usr/bin/env python3
"""
FRA Scaling Hypothesis (1.4) Experiment
========================================

Tests: K = O(1/ε^d) scaling law for NP-hard problems.

Usage:
    # Full experiment (requires vast.ai)
    python run_experiment.py --full

    # Local test (small scale)
    python run_experiment.py --local --instances 20

    # Just analysis (after data collection)
    python run_experiment.py --analyze results/

Author: Ilya Selyutin
"""

import os
import sys
import json
import yaml
import argparse
import time
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
import numpy as np
from datetime import datetime
# Removed unused parallel imports

# Force unbuffered output
os.environ['PYTHONUNBUFFERED'] = '1'

def log(msg):
    """Print with flush for real-time logging."""
    print(msg, flush=True)

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent))

from problems.tsp import TSPProblem
from problems.sat import SATProblem
from problems.maxcut import MaxCutProblem
from fra.router import FRARouter, RouterConfig


@dataclass
class ExperimentResult:
    """Results from one experiment configuration."""
    problem: str
    d: int  # Fingerprint dimension
    K: int  # Number of strategies
    n_instances: int
    train_instances: int
    test_instances: int

    # FRA performance
    fra_gap_train: float
    fra_gap_test: float
    best_single_gap: float
    best_single_name: str
    oracle_gap: float
    routing_accuracy: float

    # Improvement metrics
    improvement_over_single: float  # Percent
    gap_to_oracle: float  # Percent

    # Training
    training_time: float
    final_val_loss: float
    final_val_acc: float

    timestamp: str = ""

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()


class FRAScalingExperiment:
    """Main experiment runner."""

    def __init__(self, config_path: str = "config.yaml"):
        with open(config_path) as f:
            self.config = yaml.safe_load(f)

        self.problems = {
            "tsp": TSPProblem(),
            "sat": SATProblem(),
            "maxcut": MaxCutProblem()
        }

        self.results: List[ExperimentResult] = []
        self.output_dir = Path(self.config["output"]["results_dir"])
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def run_single_config(
        self,
        problem_name: str,
        d: int,
        K: int,
        n_instances: int = None,
        timeout_per_instance: float = 30.0
    ) -> ExperimentResult:
        """
        Run experiment with single (d, K) configuration.

        Args:
            problem_name: "tsp", "sat", or "maxcut"
            d: Fingerprint dimensionality
            K: Number of strategies to use
            n_instances: Number of instances (None = use config)
            timeout_per_instance: Timeout per strategy execution
        """
        log(f"\n{'='*60}")
        log(f"Running: {problem_name.upper()} | d={d} | K={K}")
        log(f"{'='*60}")

        problem = self.problems[problem_name]
        problem_config = self.config["problems"][problem_name]

        # Load instances
        if n_instances is None:
            n_instances = problem_config["instances"]["count"]

        log(f"Loading {n_instances} instances...")
        instances = problem.load_instances(
            problem_config["instances"]["source"],
            n_instances
        )
        log(f"  Loaded {len(instances)} instances")

        if len(instances) < 10:
            log(f"  Warning: Too few instances ({len(instances)}), skipping")
            return None

        # Select K strategies
        all_strategies = problem_config["strategies"]
        strategies = all_strategies[:K]
        log(f"  Using {K} strategies: {strategies[:3]}...")

        # Select feature sets to get d dimensions
        all_features = problem_config["features"]
        # Approximate: use all features, then reduce
        feature_sets = all_features

        # Extract fingerprints
        log(f"Extracting fingerprints...")
        fingerprints = []
        for inst in instances:
            fp = problem.extract_features(inst, feature_sets)
            fingerprints.append(fp)

        fingerprints = np.array(fingerprints)
        # Handle NaN/inf values
        fingerprints = np.nan_to_num(fingerprints, nan=0.0, posinf=1e6, neginf=-1e6)
        log(f"  Raw fingerprint dim: {fingerprints.shape[1]}")

        # Reduce to target dimension d (but not more than n_samples)
        n_samples = len(fingerprints)
        n_features = fingerprints.shape[1]
        actual_d = min(d, n_samples - 1, n_features)  # PCA requires n_components < min(n_samples, n_features)
        log(f"  PCA: n_samples={n_samples}, n_features={n_features}, d={d}, actual_d={actual_d}")
        if n_features > actual_d:
            from sklearn.decomposition import PCA
            pca = PCA(n_components=actual_d)
            fingerprints = pca.fit_transform(fingerprints)
            log(f"  Reduced to dim: {actual_d}" + (f" (requested {d})" if actual_d != d else ""))
        elif n_features < actual_d:
            # Pad with noise
            padding = np.random.randn(len(fingerprints), actual_d - fingerprints.shape[1]) * 0.01
            fingerprints = np.hstack([fingerprints, padding])
            log(f"  Padded to dim: {actual_d}")

        # Run all strategies on all instances
        log(f"Running {K} strategies on {len(instances)} instances...")
        strategy_performance = {s: [] for s in strategies}
        start_eval = time.time()

        for i, inst in enumerate(instances):
            if i % 5 == 0:
                elapsed = time.time() - start_eval
                eta = (elapsed / (i + 1)) * (len(instances) - i - 1) if i > 0 else 0
                log(f"  Instance {i+1}/{len(instances)} (ETA: {eta:.0f}s)")

            for strat in strategies:
                try:
                    solution = problem.solve(inst, strat, timeout=timeout_per_instance)
                    perf = solution.gap if solution.gap is not None else solution.value
                    strategy_performance[strat].append(perf)
                except Exception as e:
                    strategy_performance[strat].append(1e6)

        # Convert to arrays
        for s in strategies:
            strategy_performance[s] = np.array(strategy_performance[s])

        # Train/test split
        n = len(instances)
        split_idx = int(n * 0.7)
        indices = np.random.permutation(n)
        train_idx, test_idx = indices[:split_idx], indices[split_idx:]

        train_fp = fingerprints[train_idx]
        test_fp = fingerprints[test_idx]

        train_perf = {s: strategy_performance[s][train_idx] for s in strategies}
        test_perf = {s: strategy_performance[s][test_idx] for s in strategies}

        # Train router
        log(f"Training FRA router...")
        # Use actual fingerprint dimension (may be less than d due to PCA constraints)
        final_dim = fingerprints.shape[1]
        router_config = RouterConfig(
            input_dim=final_dim,
            n_strategies=K,
            hidden_layers=self.config["router"]["hidden_layers"],
            dropout=self.config["router"]["dropout"],
            learning_rate=self.config["router"]["learning_rate"],
            epochs=self.config["router"]["epochs"],
            batch_size=self.config["router"]["batch_size"],
            early_stopping_patience=self.config["router"]["early_stopping_patience"]
        )

        router = FRARouter(router_config)
        start_time = time.time()
        history = router.fit(train_fp, train_perf)
        training_time = time.time() - start_time

        log(f"  Training time: {training_time:.1f}s")
        log(f"  Final val_acc: {history['val_acc'][-1]:.3f}")

        # Evaluate
        log(f"Evaluating...")
        train_eval = router.evaluate(train_fp, train_perf)
        test_eval = router.evaluate(test_fp, test_perf)

        log(f"  Train - FRA gap: {train_eval['fra_gap']:.4f}, Best single: {train_eval['best_single_gap']:.4f}")
        log(f"  Test  - FRA gap: {test_eval['fra_gap']:.4f}, Best single: {test_eval['best_single_gap']:.4f}")
        log(f"  Improvement: {test_eval['improvement_over_single']:.2f}%")
        log(f"  Routing accuracy: {test_eval['routing_accuracy']:.3f}")

        result = ExperimentResult(
            problem=problem_name,
            d=d,
            K=K,
            n_instances=len(instances),
            train_instances=len(train_idx),
            test_instances=len(test_idx),
            fra_gap_train=train_eval['fra_gap'],
            fra_gap_test=test_eval['fra_gap'],
            best_single_gap=test_eval['best_single_gap'],
            best_single_name=test_eval['best_single_name'],
            oracle_gap=test_eval['oracle_gap'],
            routing_accuracy=test_eval['routing_accuracy'],
            improvement_over_single=test_eval['improvement_over_single'],
            gap_to_oracle=test_eval['gap_to_oracle'],
            training_time=training_time,
            final_val_loss=history['val_loss'][-1],
            final_val_acc=history['val_acc'][-1]
        )

        self.results.append(result)
        # Incremental save after each config
        self.save_results()
        log(f"  ✓ Config saved ({len(self.results)} total)")
        return result

    def run_grid(self, problems: List[str] = None, local: bool = False, n_instances: int = None):
        """Run full experiment grid."""
        if problems is None:
            problems = [p for p, cfg in self.config["problems"].items() if cfg.get("enabled", True)]

        grid = self.config["grid"]

        for problem_name in problems:
            log(f"\n{'#'*60}")
            log(f"# PROBLEM: {problem_name.upper()}")
            log(f"{'#'*60}")

            # Vary K at fixed d
            d = grid["vary_K"]["d"]
            for K in grid["vary_K"]["K"]:
                self.run_single_config(
                    problem_name, d, K,
                    n_instances=n_instances if local else None,
                    timeout_per_instance=10.0 if local else 30.0
                )

            # Vary d at fixed K
            K = grid["vary_d"]["K"]
            for d in grid["vary_d"]["d"]:
                self.run_single_config(
                    problem_name, d, K,
                    n_instances=n_instances if local else None,
                    timeout_per_instance=10.0 if local else 30.0
                )

        # Save results
        self.save_results()
        return self.results

    def save_results(self):
        """Save all results to JSON."""
        results_file = self.output_dir / "experiment_results.json"
        with open(results_file, 'w') as f:
            json.dump([asdict(r) for r in self.results], f, indent=2)
        log(f"\nResults saved to {results_file}")

    def analyze_results(self, results_path: str = None):
        """Analyze results and test hypothesis."""
        if results_path:
            with open(results_path) as f:
                data = json.load(f)
                self.results = [ExperimentResult(**r) for r in data]

        if not self.results:
            print("No results to analyze")
            return

        log("\n" + "="*60)
        print("HYPOTHESIS 1.4 ANALYSIS")
        print("="*60)

        # Group by problem
        problems = set(r.problem for r in self.results)

        all_confirmed = True
        problem_results = {}

        for problem in problems:
            log(f"\n--- {problem.upper()} ---")
            problem_res = [r for r in self.results if r.problem == problem]

            # 1. FRA vs Best Single
            fra_beats = sum(1 for r in problem_res if r.improvement_over_single > 0)
            fra_total = len(problem_res)
            log(f"FRA beats best single: {fra_beats}/{fra_total} ({fra_beats/fra_total*100:.1f}%)")

            # 2. Scaling with K (at fixed d)
            vary_k = [r for r in problem_res if r.d == self.config["grid"]["vary_K"]["d"]]
            if len(vary_k) > 2:
                Ks = [r.K for r in vary_k]
                gaps = [r.fra_gap_test for r in vary_k]
                from scipy import stats
                corr_K, p_K = stats.spearmanr(Ks, gaps)
                log(f"Correlation (K vs gap): r={corr_K:.3f}, p={p_K:.4f}")
            else:
                corr_K = 0

            # 3. Scaling with d (at fixed K)
            vary_d = [r for r in problem_res if r.K == self.config["grid"]["vary_d"]["K"]]
            if len(vary_d) > 2:
                ds = [r.d for r in vary_d]
                gaps = [r.fra_gap_test for r in vary_d]
                corr_d, p_d = stats.spearmanr(ds, gaps)
                log(f"Correlation (d vs gap): r={corr_d:.3f}, p={p_d:.4f}")
            else:
                corr_d = 0

            # 4. Fit K = c/ε^d curve
            try:
                from scipy.optimize import curve_fit
                Ks = np.array([r.K for r in vary_k])
                gaps = np.array([r.fra_gap_test for r in vary_k])
                # gap ~ 1/K^alpha
                def power_law(K, c, alpha):
                    return c / (K ** alpha)
                popt, _ = curve_fit(power_law, Ks, gaps, p0=[1, 0.5], maxfev=1000)
                gaps_pred = power_law(Ks, *popt)
                ss_res = np.sum((gaps - gaps_pred) ** 2)
                ss_tot = np.sum((gaps - gaps.mean()) ** 2)
                r2 = 1 - ss_res / ss_tot if ss_tot > 0 else 0
                log(f"Power law fit: gap ~ {popt[0]:.3f} / K^{popt[1]:.3f}, R²={r2:.3f}")
            except Exception as e:
                r2 = 0
                log(f"Power law fit failed: {e}")

            # Check criteria
            criteria = self.config["criteria"]
            confirmed = (
                fra_beats / fra_total > 0.5 and  # FRA wins >50%
                corr_K < criteria["scaling"]["min_correlation_K_gap"] and  # Negative correlation
                r2 > criteria["scaling"]["min_fit_r2"]  # Good fit
            )

            problem_results[problem] = {
                "confirmed": confirmed,
                "fra_win_rate": fra_beats / fra_total,
                "corr_K": corr_K,
                "corr_d": corr_d,
                "r2": r2
            }

            if not confirmed:
                all_confirmed = False

            log(f"Hypothesis for {problem}: {'CONFIRMED' if confirmed else 'NOT CONFIRMED'}")

        # Overall verdict
        log("\n" + "="*60)
        n_confirmed = sum(1 for p in problem_results.values() if p["confirmed"])
        log(f"OVERALL: {n_confirmed}/{len(problems)} problems confirmed")

        if n_confirmed >= 2:
            log("\n>>> HYPOTHESIS 1.4: CONFIRMED <<<")
            print("FRA scaling law holds for majority of tested NP-hard problems.")
        elif n_confirmed == 1:
            log("\n>>> HYPOTHESIS 1.4: PARTIALLY CONFIRMED <<<")
            print("FRA scaling law holds for some NP-hard problems.")
        else:
            log("\n>>> HYPOTHESIS 1.4: NOT CONFIRMED <<<")
            print("FRA scaling law does not hold for tested problems.")

        # Save analysis
        analysis_file = self.output_dir / "hypothesis_analysis.json"
        with open(analysis_file, 'w') as f:
            json.dump({
                "problems": problem_results,
                "overall_confirmed": n_confirmed >= 2,
                "n_confirmed": n_confirmed,
                "n_total": len(problems)
            }, f, indent=2)
        log(f"\nAnalysis saved to {analysis_file}")

        return problem_results

    def generate_figures(self):
        """Generate publication-quality figures."""
        import matplotlib.pyplot as plt

        figures_dir = Path(self.config["output"]["figures_dir"])
        figures_dir.mkdir(parents=True, exist_ok=True)

        # Figure 1: K vs Gap (all problems)
        fig, axes = plt.subplots(1, 3, figsize=(15, 4))
        problems = set(r.problem for r in self.results)

        for idx, problem in enumerate(sorted(problems)):
            ax = axes[idx]
            vary_k = [r for r in self.results
                      if r.problem == problem and r.d == self.config["grid"]["vary_K"]["d"]]

            if vary_k:
                Ks = [r.K for r in vary_k]
                fra_gaps = [r.fra_gap_test for r in vary_k]
                single_gaps = [r.best_single_gap for r in vary_k]
                oracle_gaps = [r.oracle_gap for r in vary_k]

                ax.plot(Ks, fra_gaps, 'o-', label='FRA', linewidth=2, markersize=8)
                ax.plot(Ks, single_gaps, 's--', label='Best Single', linewidth=2, markersize=8)
                ax.plot(Ks, oracle_gaps, '^:', label='Oracle', linewidth=2, markersize=8)

                ax.set_xlabel('K (number of strategies)', fontsize=12)
                ax.set_ylabel('Gap (%)', fontsize=12)
                ax.set_title(f'{problem.upper()}', fontsize=14)
                ax.legend()
                ax.grid(True, alpha=0.3)

        plt.tight_layout()
        plt.savefig(figures_dir / 'scaling_K.png', dpi=150, bbox_inches='tight')
        plt.close()

        # Figure 2: d vs Gap
        fig, axes = plt.subplots(1, 3, figsize=(15, 4))

        for idx, problem in enumerate(sorted(problems)):
            ax = axes[idx]
            vary_d = [r for r in self.results
                      if r.problem == problem and r.K == self.config["grid"]["vary_d"]["K"]]

            if vary_d:
                ds = [r.d for r in vary_d]
                fra_gaps = [r.fra_gap_test for r in vary_d]

                ax.plot(ds, fra_gaps, 'o-', linewidth=2, markersize=8, color='blue')
                ax.set_xlabel('d (fingerprint dimension)', fontsize=12)
                ax.set_ylabel('FRA Gap (%)', fontsize=12)
                ax.set_title(f'{problem.upper()}', fontsize=14)
                ax.set_xscale('log', base=2)
                ax.grid(True, alpha=0.3)

        plt.tight_layout()
        plt.savefig(figures_dir / 'scaling_d.png', dpi=150, bbox_inches='tight')
        plt.close()

        log(f"Figures saved to {figures_dir}")


def main():
    parser = argparse.ArgumentParser(description="FRA Scaling Hypothesis Experiment")
    parser.add_argument("--full", action="store_true", help="Run full experiment")
    parser.add_argument("--local", action="store_true", help="Run local test (small scale)")
    parser.add_argument("--instances", type=int, default=50, help="Number of instances for local test")
    parser.add_argument("--analyze", type=str, help="Analyze existing results")
    parser.add_argument("--config", type=str, default="config.yaml", help="Config file path")
    parser.add_argument("--problem", type=str, help="Run only specific problem (tsp/sat/maxcut)")

    args = parser.parse_args()

    experiment = FRAScalingExperiment(args.config)

    if args.analyze:
        experiment.analyze_results(args.analyze)
        experiment.generate_figures()
    elif args.local:
        problems = [args.problem] if args.problem else None
        experiment.run_grid(problems=problems, local=True, n_instances=args.instances)
        experiment.analyze_results()
        experiment.generate_figures()
    elif args.full:
        problems = [args.problem] if args.problem else None
        experiment.run_grid(problems=problems, local=False)
        experiment.analyze_results()
        experiment.generate_figures()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
