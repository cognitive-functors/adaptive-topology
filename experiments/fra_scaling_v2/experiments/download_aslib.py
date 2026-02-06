#!/usr/bin/env python3
"""
Download and parse real ASlib scenarios.
"""

import os
import json
import urllib.request
import zipfile
import tempfile
from pathlib import Path
import numpy as np
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(message)s')
log = logging.getLogger(__name__)

# ASlib scenarios URLs (from GitHub releases)
ASLIB_BASE = "https://github.com/coseal/aslib_data/raw/master"

# Priority scenarios with known diversity
SCENARIOS = {
    "SAT11-RAND": {
        "description": "Random 3-SAT instances, 12 SAT solvers",
        "expected_diversity": "high",
        "n_instances": 5355,
        "n_algorithms": 12
    },
    "SAT12-ALL": {
        "description": "Mixed SAT instances from SAT Competition 2012",
        "expected_diversity": "high",
        "n_instances": 1614,
        "n_algorithms": 31
    },
    "CSP-2010": {
        "description": "Constraint Satisfaction Problems",
        "expected_diversity": "medium",
        "n_instances": 2024,
        "n_algorithms": 2
    }
}


def download_scenario(name: str, output_dir: Path) -> bool:
    """Download ASlib scenario from GitHub."""
    scenario_dir = output_dir / name
    scenario_dir.mkdir(parents=True, exist_ok=True)

    files = [
        "description.txt",
        "feature_values.arff",
        "algorithm_runs.arff",
        "cv.arff"
    ]

    success = True
    for filename in files:
        url = f"{ASLIB_BASE}/{name}/{filename}"
        local_path = scenario_dir / filename

        if local_path.exists():
            log.info(f"  {filename} already exists")
            continue

        try:
            log.info(f"  Downloading {filename}...")
            urllib.request.urlretrieve(url, local_path)
        except Exception as e:
            log.warning(f"  Failed to download {filename}: {e}")
            success = False

    return success


def parse_arff_simple(filepath: Path) -> tuple:
    """Simple ARFF parser (no scipy dependency)."""
    attributes = []
    data = []
    in_data = False

    with open(filepath, 'r', errors='replace') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('%'):
                continue

            if line.lower().startswith('@attribute'):
                parts = line.split()
                if len(parts) >= 2:
                    attr_name = parts[1].strip("'\"")
                    attributes.append(attr_name)

            elif line.lower().startswith('@data'):
                in_data = True

            elif in_data:
                values = line.split(',')
                data.append(values)

    return attributes, data


def load_scenario(scenario_dir: Path) -> dict:
    """Load and parse ASlib scenario."""
    log.info(f"Loading scenario from {scenario_dir}")

    # Parse features
    feat_attrs, feat_data = parse_arff_simple(scenario_dir / "feature_values.arff")

    # Parse performance
    perf_attrs, perf_data = parse_arff_simple(scenario_dir / "algorithm_runs.arff")

    # Extract instance IDs and features
    instance_col = 0  # Usually first column
    feature_cols = [i for i, a in enumerate(feat_attrs) if a != 'instance_id']

    instances = []
    features = []

    for row in feat_data:
        if len(row) > max(feature_cols):
            inst_id = row[instance_col].strip("'\"")
            feat_vals = []
            for col in feature_cols:
                try:
                    val = float(row[col]) if row[col] != '?' else np.nan
                except:
                    val = np.nan
                feat_vals.append(val)
            instances.append(inst_id)
            features.append(feat_vals)

    features = np.array(features)

    # Extract algorithm names (excluding metadata columns)
    meta_cols = {'instance_id', 'repetition', 'runstatus', 'runtime'}
    algorithm_names = [a for a in perf_attrs if a.lower() not in meta_cols]

    # Build performance matrix
    # Performance data is typically: instance_id, algorithm, runtime, runstatus
    # OR: instance_id, algo1_runtime, algo2_runtime, ...

    # Try to detect format
    if 'algorithm' in [a.lower() for a in perf_attrs]:
        # Long format: one row per (instance, algorithm)
        perf_matrix = _parse_long_format(perf_data, perf_attrs, instances, algorithm_names)
    else:
        # Wide format: one row per instance, columns are algorithms
        perf_matrix = _parse_wide_format(perf_data, perf_attrs, instances)
        algorithm_names = [a for a in perf_attrs[1:] if a.lower() not in meta_cols]

    # Handle NaN/Inf
    features = np.nan_to_num(features, nan=0.0, posinf=1e6, neginf=-1e6)
    perf_matrix = np.nan_to_num(perf_matrix, nan=1e6, posinf=1e6, neginf=-1e6)

    log.info(f"  Instances: {len(instances)}")
    log.info(f"  Features: {features.shape[1]}")
    log.info(f"  Algorithms: {len(algorithm_names)}")

    return {
        "name": scenario_dir.name,
        "instances": instances,
        "features": features,
        "feature_names": [feat_attrs[i] for i in feature_cols],
        "performance": perf_matrix,
        "algorithm_names": algorithm_names
    }


def _parse_wide_format(data, attrs, instances):
    """Parse wide format: instance_id, algo1, algo2, ..."""
    n_instances = len(instances)
    n_algos = len(attrs) - 1  # Exclude instance_id

    perf = np.full((n_instances, n_algos), np.nan)
    inst_to_idx = {inst: i for i, inst in enumerate(instances)}

    for row in data:
        if len(row) < 2:
            continue
        inst_id = row[0].strip("'\"")
        if inst_id in inst_to_idx:
            idx = inst_to_idx[inst_id]
            for j in range(min(n_algos, len(row) - 1)):
                try:
                    perf[idx, j] = float(row[j + 1]) if row[j + 1] != '?' else np.nan
                except:
                    pass

    return perf


def _parse_long_format(data, attrs, instances, algorithms):
    """Parse long format: instance_id, algorithm, runtime, ..."""
    n_instances = len(instances)
    n_algos = len(algorithms)

    perf = np.full((n_instances, n_algos), np.nan)
    inst_to_idx = {inst: i for i, inst in enumerate(instances)}
    algo_to_idx = {algo: i for i, algo in enumerate(algorithms)}

    # Find column indices
    inst_col = next((i for i, a in enumerate(attrs) if a.lower() == 'instance_id'), 0)
    algo_col = next((i for i, a in enumerate(attrs) if a.lower() == 'algorithm'), 1)
    runtime_col = next((i for i, a in enumerate(attrs) if 'runtime' in a.lower()), 2)

    for row in data:
        if len(row) <= max(inst_col, algo_col, runtime_col):
            continue
        inst_id = row[inst_col].strip("'\"")
        algo_name = row[algo_col].strip("'\"")

        if inst_id in inst_to_idx and algo_name in algo_to_idx:
            i = inst_to_idx[inst_id]
            j = algo_to_idx[algo_name]
            try:
                perf[i, j] = float(row[runtime_col]) if row[runtime_col] != '?' else np.nan
            except:
                pass

    return perf


def compute_diversity(performance: np.ndarray) -> dict:
    """Compute diversity metrics for a scenario."""
    # Best algorithm per instance
    best_algo = np.argmin(performance, axis=1)

    # Entropy of best algorithm distribution
    counts = np.bincount(best_algo, minlength=performance.shape[1])
    probs = counts / counts.sum()
    entropy = -np.sum(probs * np.log(probs + 1e-10))
    max_entropy = np.log(len(probs))
    normalized_entropy = entropy / max_entropy if max_entropy > 0 else 0

    # Dominance: how often does best single algorithm win?
    sbs_idx = np.argmin(np.mean(performance, axis=0))
    sbs_wins = np.sum(best_algo == sbs_idx) / len(best_algo)

    return {
        "entropy": float(entropy),
        "normalized_entropy": float(normalized_entropy),
        "sbs_dominance": float(sbs_wins),
        "n_unique_best": int(len(np.unique(best_algo))),
        "diversity_score": float(1 - sbs_wins)  # Higher = more diverse
    }


def main():
    """Download and analyze ASlib scenarios."""
    output_dir = Path("/Users/figuramax/LocalProjects/adaptive-topology/experiments/fra_scaling_v2/data/aslib")
    output_dir.mkdir(parents=True, exist_ok=True)

    log.info("=" * 60)
    log.info("ASlib Scenario Downloader")
    log.info("=" * 60)

    results = {}

    for name, info in SCENARIOS.items():
        log.info(f"\n--- {name} ---")
        log.info(f"Description: {info['description']}")

        # Download
        success = download_scenario(name, output_dir)

        if success:
            try:
                # Load and analyze
                scenario = load_scenario(output_dir / name)
                diversity = compute_diversity(scenario["performance"])

                results[name] = {
                    "n_instances": len(scenario["instances"]),
                    "n_features": scenario["features"].shape[1],
                    "n_algorithms": len(scenario["algorithm_names"]),
                    "diversity": diversity
                }

                log.info(f"  Diversity score: {diversity['diversity_score']:.2%}")
                log.info(f"  SBS dominance: {diversity['sbs_dominance']:.2%}")

                # Save processed data
                np.savez(
                    output_dir / name / "processed.npz",
                    features=scenario["features"],
                    performance=scenario["performance"],
                    instances=scenario["instances"],
                    algorithms=scenario["algorithm_names"],
                    feature_names=scenario["feature_names"]
                )
                log.info(f"  Saved processed data")

            except Exception as e:
                log.error(f"  Failed to process: {e}")
                import traceback
                traceback.print_exc()
        else:
            log.warning(f"  Skipping (download failed)")

    # Save summary
    with open(output_dir / "scenarios_summary.json", 'w') as f:
        json.dump(results, f, indent=2)

    log.info("\n" + "=" * 60)
    log.info("Summary saved to scenarios_summary.json")

    return results


if __name__ == "__main__":
    main()
