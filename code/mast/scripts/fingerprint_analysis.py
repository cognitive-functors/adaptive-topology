#!/usr/bin/env python3
"""
Fingerprint Analysis + Ablation Study для MASTm v6.

Запуск:
  cd code/mast
  PYTHONPATH=. python3 scripts/fingerprint_analysis.py [--mode fingerprint|ablation|both]
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from src.core.distance_oracle import DistanceOracle
from src.core.fingerprint import (
    InstanceFingerprint, SolverConfig, StrategyRouter, compute_fingerprint,
)

# TSPLIB оптимумы и пути
OPTIMAL = {
    'eil51': 426, 'berlin52': 7542, 'kroA100': 21282, 'ch150': 6528,
    'pcb442': 50778, 'rat783': 8806, 'dsj1000': 18659688,
    'pcb3038': 137694, 'fl3795': 28772, 'fnl4461': 182566,
    'rl5915': 565530, 'pla7397': 23260728, 'd15112': 1573084,
}

_ROOT = Path(__file__).resolve().parent.parent
TSP_DIR = _ROOT / 'benchmarks'
RESULTS_DIR = _ROOT / 'results'
PLOTS_DIR = _ROOT / 'results' / 'plots'


def load_instance(name: str) -> np.ndarray:
    """Загружает координаты из TSP файла."""
    import tsplib95
    path = TSP_DIR / f'{name}.tsp'
    if not path.exists():
        raise FileNotFoundError(f'{path} not found')
    prob = tsplib95.load(str(path))
    nodes = list(prob.get_nodes())
    return np.array([prob.node_coords[n] for n in nodes], dtype=np.float64)


def compute_all_fingerprints() -> dict[str, tuple[InstanceFingerprint, SolverConfig]]:
    """Вычисляет fingerprint для всех TSPLIB инстансов."""
    results = {}
    router = StrategyRouter()

    for name in sorted(OPTIMAL.keys()):
        try:
            coords = load_instance(name)
        except FileNotFoundError:
            continue

        oracle = DistanceOracle(coords, knn_k=20)
        oracle.build_knn()
        fp = compute_fingerprint(oracle)
        config = router.route(fp, time_budget=300.0)
        results[name] = (fp, config)

        pattern = "uniform" if fp.is_uniform else "clustered" if fp.is_clustered else "mixed"
        print(f'{name:<14} N={fp.n:>6}  cv_nn={fp.cv_nn_dist:.3f}  '
              f'Q={fp.modularity:.3f}  AR={fp.aspect_ratio:.2f}  '
              f'pattern={pattern:<10} → {config.strategy_name}')

    return results


def plot_fingerprint_scatter(fps: dict[str, tuple[InstanceFingerprint, SolverConfig]]):
    """Scatter plot: cv_nn_dist vs modularity с размером = N."""
    PLOTS_DIR.mkdir(parents=True, exist_ok=True)

    fig, ax = plt.subplots(1, 1, figsize=(10, 7))

    colors = {
        'uniform': '#2196F3',
        'clustered': '#F44336',
        'mixed': '#FF9800',
        'structured': '#4CAF50',
    }

    for name, (fp, config) in fps.items():
        if fp.is_structured:
            pattern = 'structured'
        elif fp.is_uniform:
            pattern = 'uniform'
        elif fp.is_clustered:
            pattern = 'clustered'
        else:
            pattern = 'mixed'

        size = max(30, min(200, fp.n / 50))
        ax.scatter(fp.cv_nn_dist, fp.modularity, s=size,
                   c=colors[pattern], alpha=0.8, edgecolors='black', linewidths=0.5)
        ax.annotate(name, (fp.cv_nn_dist, fp.modularity),
                    fontsize=7, ha='center', va='bottom', xytext=(0, 5),
                    textcoords='offset points')

    # Границы классификации
    ax.axvline(x=0.4, color='gray', linestyle='--', alpha=0.5, label='cv_nn=0.4 (uniform)')
    ax.axvline(x=0.8, color='gray', linestyle=':', alpha=0.5, label='cv_nn=0.8 (clustered)')
    ax.axhline(y=0.2, color='gray', linestyle='--', alpha=0.3, label='Q=0.2 (uniform)')
    ax.axhline(y=0.4, color='gray', linestyle=':', alpha=0.3, label='Q=0.4 (clustered)')

    ax.set_xlabel('cv_nn_dist (coefficient of variation of 1-NN distances)')
    ax.set_ylabel('modularity (Newman Q on k-NN graph)')
    ax.set_title('MASTm Instance Fingerprint Space')
    ax.legend(fontsize=8)
    ax.grid(True, alpha=0.2)

    # Легенда цветов
    for pattern, color in colors.items():
        ax.scatter([], [], c=color, s=50, label=pattern, edgecolors='black', linewidths=0.5)
    ax.legend(fontsize=8, loc='upper left')

    path = PLOTS_DIR / 'fingerprint_scatter.png'
    fig.savefig(path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f'\nSaved: {path}')


def plot_fingerprint_heatmap(fps: dict[str, tuple[InstanceFingerprint, SolverConfig]]):
    """Heatmap: все фичи fingerprint для всех инстансов."""
    PLOTS_DIR.mkdir(parents=True, exist_ok=True)

    names = sorted(fps.keys(), key=lambda x: fps[x][0].n)
    features = ['cv_nn_dist', 'modularity', 'aspect_ratio', 'density_cv', 'mean_nn_dist']

    data = np.zeros((len(names), len(features)))
    for i, name in enumerate(names):
        fp = fps[name][0]
        data[i] = [fp.cv_nn_dist, fp.modularity, fp.aspect_ratio, fp.density_cv, fp.mean_nn_dist]

    # Нормализуем каждую фичу [0, 1]
    for j in range(len(features)):
        col = data[:, j]
        mn, mx = col.min(), col.max()
        if mx > mn:
            data[:, j] = (col - mn) / (mx - mn)

    fig, ax = plt.subplots(1, 1, figsize=(8, max(6, len(names) * 0.4)))
    im = ax.imshow(data, cmap='YlOrRd', aspect='auto')
    ax.set_xticks(range(len(features)))
    ax.set_xticklabels(features, rotation=45, ha='right', fontsize=9)
    ax.set_yticks(range(len(names)))
    ax.set_yticklabels([f'{n} (N={fps[n][0].n})' for n in names], fontsize=8)
    ax.set_title('Instance Fingerprint Heatmap (normalized)')

    # Значения в ячейках
    for i in range(len(names)):
        fp = fps[names[i]][0]
        raw = [fp.cv_nn_dist, fp.modularity, fp.aspect_ratio, fp.density_cv, fp.mean_nn_dist]
        for j in range(len(features)):
            ax.text(j, i, f'{raw[j]:.2f}', ha='center', va='center', fontsize=7,
                    color='white' if data[i, j] > 0.5 else 'black')

    fig.colorbar(im, ax=ax, shrink=0.6)

    path = PLOTS_DIR / 'fingerprint_heatmap.png'
    fig.savefig(path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f'Saved: {path}')


def plot_routing_decisions(fps: dict[str, tuple[InstanceFingerprint, SolverConfig]]):
    """Bar chart: routing decisions для каждого инстанса."""
    PLOTS_DIR.mkdir(parents=True, exist_ok=True)

    names = sorted(fps.keys(), key=lambda x: fps[x][0].n)
    strategies = [fps[n][1].strategy_name for n in names]

    strategy_colors = {
        'no-decompose-small': '#81D4FA',
        'no-decompose-structured': '#A5D6A7',
        'no-decompose-med-clustered': '#FFAB91',
        'decompose-clustered': '#EF5350',
        'default-decompose': '#FFA726',
        'default-decompose+eax-dominant': '#AB47BC',
    }

    fig, axes = plt.subplots(1, 3, figsize=(14, max(5, len(names) * 0.35)))

    # Plot 1: Strategy assignment
    ax = axes[0]
    y = range(len(names))
    colors = [strategy_colors.get(s, '#999') for s in strategies]
    ax.barh(y, [1] * len(names), color=colors, edgecolor='white')
    ax.set_yticks(y)
    ax.set_yticklabels([f'{n}' for n in names], fontsize=8)
    ax.set_title('Strategy', fontsize=10)
    for i, s in enumerate(strategies):
        ax.text(0.5, i, s, ha='center', va='center', fontsize=6, fontweight='bold')

    # Plot 2: Budget allocation
    ax = axes[1]
    leaf_b = [fps[n][1].leaf_budget_fraction for n in names]
    vcycle_b = [fps[n][1].v_cycle_budget_fraction for n in names]
    polish_b = [fps[n][1].polish_budget_fraction for n in names]
    ax.barh(y, leaf_b, label='leaf', color='#42A5F5')
    ax.barh(y, vcycle_b, left=leaf_b, label='v-cycle', color='#66BB6A')
    ax.barh(y, polish_b, left=[l+v for l, v in zip(leaf_b, vcycle_b)], label='polish', color='#FFA726')
    ax.set_yticks(y)
    ax.set_yticklabels([])
    ax.set_title('Budget Split', fontsize=10)
    ax.legend(fontsize=7, loc='lower right')

    # Plot 3: Key features
    ax = axes[2]
    cv_vals = [fps[n][0].cv_nn_dist for n in names]
    ax.barh(y, cv_vals, color='#78909C', edgecolor='white')
    ax.axvline(x=0.4, color='blue', linestyle='--', alpha=0.5, label='uniform threshold')
    ax.axvline(x=0.8, color='red', linestyle='--', alpha=0.5, label='clustered threshold')
    ax.set_yticks(y)
    ax.set_yticklabels([])
    ax.set_title('cv_nn_dist', fontsize=10)
    ax.legend(fontsize=7)

    fig.suptitle('MASTm v6 Strategy Router Decisions', fontsize=12, fontweight='bold')
    fig.tight_layout()

    path = PLOTS_DIR / 'routing_decisions.png'
    fig.savefig(path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f'Saved: {path}')


def print_ablation_table():
    """Печатает ablation table из сохранённых результатов."""
    # Загружаем результаты разных версий
    result_files = {
        'v6.0 (baseline)': RESULTS_DIR / 'v6_benchmark_120s.json',
        'v6.5 (300s)': RESULTS_DIR / 'v6.5_benchmark_300s.json',
    }

    all_results = {}
    for label, path in result_files.items():
        if path.exists():
            with open(path) as f:
                all_results[label] = json.load(f)

    if not all_results:
        print('No result files found for ablation.')
        return

    # Ключевые инстансы
    key_instances = ['fl3795', 'fnl4461', 'rl5915', 'pla7397', 'd15112']

    print(f'\n{"="*70}')
    print(f'ABLATION TABLE')
    print(f'{"="*70}')
    print(f'{"Version":<20}', end='')
    for inst in key_instances:
        print(f' {inst:>10}', end='')
    print()
    print(f'{"-"*20}' + f' {"-"*10}' * len(key_instances))

    for label, results in all_results.items():
        print(f'{label:<20}', end='')
        for inst in key_instances:
            if inst in results:
                print(f' {results[inst]["min"]:>9.2f}%', end='')
            else:
                print(f' {"N/A":>10}', end='')
        print()

    # v5.3 baseline
    v53 = {'fl3795': 0.80, 'fnl4461': 2.24, 'rl5915': 1.71, 'pla7397': 1.40, 'd15112': 5.29}
    print(f'{"v5.3 baseline":<20}', end='')
    for inst in key_instances:
        if inst in v53:
            print(f' {v53[inst]:>9.2f}%', end='')
        else:
            print(f' {"N/A":>10}', end='')
    print()


def main():
    parser = argparse.ArgumentParser(description='MASTm Fingerprint Analysis')
    parser.add_argument('--mode', choices=['fingerprint', 'ablation', 'both'],
                        default='both')
    args = parser.parse_args()

    if args.mode in ('fingerprint', 'both'):
        print('Computing fingerprints...')
        fps = compute_all_fingerprints()

        print('\nGenerating plots...')
        plot_fingerprint_scatter(fps)
        plot_fingerprint_heatmap(fps)
        plot_routing_decisions(fps)

    if args.mode in ('ablation', 'both'):
        print_ablation_table()


if __name__ == '__main__':
    main()
