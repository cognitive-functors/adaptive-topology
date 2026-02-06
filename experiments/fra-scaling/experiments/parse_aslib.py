#!/usr/bin/env python3
"""
Correct ASlib parser for long-format algorithm_runs.arff
"""

import numpy as np
from pathlib import Path
import json
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(message)s')
log = logging.getLogger(__name__)


def parse_aslib_scenario(scenario_dir: Path) -> dict:
    """Parse ASlib scenario with correct long-format handling."""
    log.info(f"Parsing {scenario_dir.name}")

    # 1. Parse features
    features_file = scenario_dir / "feature_values.arff"
    feat_instances, features, feature_names = parse_features(features_file)
    log.info(f"  Features: {len(feat_instances)} instances, {len(feature_names)} features")

    # 2. Parse performance (long format)
    perf_file = scenario_dir / "algorithm_runs.arff"
    perf_instances, algorithms, performance = parse_performance_long(perf_file)
    log.info(f"  Performance: {len(perf_instances)} instances, {len(algorithms)} algorithms")

    # 3. Align instances (keep only those in both files)
    common_instances = sorted(set(feat_instances) & set(perf_instances))
    log.info(f"  Common instances: {len(common_instances)}")

    # Build aligned matrices
    feat_idx = {inst: i for i, inst in enumerate(feat_instances)}
    perf_idx = {inst: i for i, inst in enumerate(perf_instances)}

    aligned_features = np.array([features[feat_idx[inst]] for inst in common_instances])
    aligned_perf = np.array([performance[perf_idx[inst]] for inst in common_instances])

    # Handle NaN/timeout (PAR10: timeout = 10x cutoff)
    cutoff = 5000  # Common ASlib timeout
    aligned_perf = np.where(aligned_perf >= cutoff, cutoff * 10, aligned_perf)
    aligned_perf = np.nan_to_num(aligned_perf, nan=cutoff * 10)

    # Compute diversity
    diversity = compute_diversity(aligned_perf, algorithms)

    return {
        "name": scenario_dir.name,
        "instances": common_instances,
        "features": aligned_features,
        "feature_names": feature_names,
        "performance": aligned_perf,
        "algorithms": algorithms,
        "diversity": diversity
    }


def parse_features(filepath: Path) -> tuple:
    """Parse feature_values.arff"""
    instances = []
    features = []
    feature_names = []
    in_data = False

    with open(filepath, 'r', errors='replace') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('%'):
                continue

            if line.lower().startswith('@attribute'):
                parts = line.split(None, 2)
                if len(parts) >= 2:
                    name = parts[1].strip("'\"")
                    if name.lower() != 'instance_id':
                        feature_names.append(name)

            elif line.lower().startswith('@data'):
                in_data = True

            elif in_data:
                parts = line.split(',')
                if len(parts) >= 2:
                    inst_id = parts[0].strip("'\"")
                    feat_vals = []
                    for v in parts[1:]:
                        try:
                            feat_vals.append(float(v) if v.strip() != '?' else np.nan)
                        except:
                            feat_vals.append(np.nan)
                    instances.append(inst_id)
                    features.append(feat_vals)

    return instances, np.array(features), feature_names


def parse_performance_long(filepath: Path) -> tuple:
    """Parse algorithm_runs.arff in long format."""
    # First pass: collect unique instances and algorithms
    instances_set = set()
    algorithms_set = set()
    data_rows = []

    in_data = False
    with open(filepath, 'r', errors='replace') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('%'):
                continue

            if line.lower().startswith('@data'):
                in_data = True
                continue

            if in_data:
                parts = line.split(',')
                if len(parts) >= 4:
                    inst_id = parts[0].strip("'\"")
                    algo = parts[2].strip("'\"")
                    try:
                        runtime = float(parts[3])
                    except:
                        runtime = np.nan

                    instances_set.add(inst_id)
                    algorithms_set.add(algo)
                    data_rows.append((inst_id, algo, runtime))

    instances = sorted(instances_set)
    algorithms = sorted(algorithms_set)

    # Build performance matrix
    inst_to_idx = {inst: i for i, inst in enumerate(instances)}
    algo_to_idx = {algo: i for i, algo in enumerate(algorithms)}

    performance = np.full((len(instances), len(algorithms)), np.nan)

    for inst_id, algo, runtime in data_rows:
        i = inst_to_idx[inst_id]
        j = algo_to_idx[algo]
        performance[i, j] = runtime

    return instances, algorithms, performance


def compute_diversity(performance: np.ndarray, algorithms: list) -> dict:
    """Compute diversity metrics."""
    # Best algorithm per instance (lowest runtime)
    best_algo_idx = np.nanargmin(performance, axis=1)

    # Count per algorithm
    n_algos = len(algorithms)
    counts = np.bincount(best_algo_idx, minlength=n_algos)

    # Entropy
    probs = counts / counts.sum()
    entropy = -np.sum(probs * np.log(probs + 1e-10))
    max_entropy = np.log(n_algos)
    normalized_entropy = entropy / max_entropy if max_entropy > 0 else 0

    # SBS dominance
    mean_per_algo = np.nanmean(performance, axis=0)
    sbs_idx = np.argmin(mean_per_algo)
    sbs_wins = counts[sbs_idx] / counts.sum()

    # Best algorithms with their win rates
    best_algos = [(algorithms[i], int(counts[i]), float(counts[i]/counts.sum()))
                  for i in np.argsort(-counts)[:5]]

    return {
        "entropy": float(entropy),
        "normalized_entropy": float(normalized_entropy),
        "sbs_idx": int(sbs_idx),
        "sbs_name": algorithms[sbs_idx],
        "sbs_dominance": float(sbs_wins),
        "n_unique_best": int(np.sum(counts > 0)),
        "diversity_score": float(1 - sbs_wins),
        "top_algorithms": best_algos
    }


def main():
    """Parse all downloaded scenarios."""
    data_dir = Path("/Users/figuramax/LocalProjects/adaptive-topology/experiments/fra_scaling_v2/data/aslib")

    log.info("=" * 60)
    log.info("ASlib Parser (Correct Version)")
    log.info("=" * 60)

    results = {}

    for scenario_dir in sorted(data_dir.iterdir()):
        if not scenario_dir.is_dir():
            continue
        if not (scenario_dir / "algorithm_runs.arff").exists():
            continue

        try:
            data = parse_aslib_scenario(scenario_dir)

            # Save processed data
            np.savez(
                scenario_dir / "processed.npz",
                features=data["features"],
                performance=data["performance"],
                allow_pickle=True
            )

            # Save metadata
            meta = {
                "name": data["name"],
                "n_instances": len(data["instances"]),
                "n_features": len(data["feature_names"]),
                "n_algorithms": len(data["algorithms"]),
                "algorithms": data["algorithms"],
                "feature_names": data["feature_names"][:10],  # First 10
                "diversity": data["diversity"]
            }

            with open(scenario_dir / "metadata.json", 'w') as f:
                json.dump(meta, f, indent=2)

            results[data["name"]] = meta

            log.info(f"  ✓ Saved. Diversity: {data['diversity']['diversity_score']:.1%}")
            log.info(f"    Top algos: {data['diversity']['top_algorithms'][:3]}")

        except Exception as e:
            log.error(f"  ✗ Failed: {e}")
            import traceback
            traceback.print_exc()

    # Save summary
    with open(data_dir / "scenarios_summary.json", 'w') as f:
        json.dump(results, f, indent=2)

    log.info("\n" + "=" * 60)
    log.info("SUMMARY")
    log.info("=" * 60)

    for name, meta in results.items():
        div = meta["diversity"]
        log.info(f"{name}:")
        log.info(f"  Instances: {meta['n_instances']}, Algorithms: {meta['n_algorithms']}")
        log.info(f"  Diversity: {div['diversity_score']:.1%}, SBS: {div['sbs_name']} ({div['sbs_dominance']:.1%})")

    return results


if __name__ == "__main__":
    main()
