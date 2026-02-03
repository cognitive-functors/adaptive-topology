#!/usr/bin/env python3
"""
Полный бенчмарк v6 meta-router (Phase 6).

Запуск:
  cd code/mast
  PYTHONPATH=. python3 scripts/run_benchmark_v6.py [--instances X,Y] [--budget 120] [--runs 3] [--full]
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np
import tsplib95

from src.core.ultra_solver import solve_v5

# Оптимумы TSPLIB (из литературы)
OPTIMAL = {
    'eil51': 426,
    'berlin52': 7542,
    'st70': 675,
    'eil76': 538,
    'kroA100': 21282,
    'ch150': 6528,
    'tsp225': 3916,
    'a280': 2579,
    'pcb442': 50778,
    'att532': 27686,
    'rat783': 8806,
    'dsj1000': 18659688,
    'pr1002': 259045,
    'si1032': 92650,
    'u1060': 224094,
    'vm1084': 239297,
    'pcb1173': 56892,
    'd1291': 50801,
    'rl1304': 252948,
    'rl1323': 270199,
    'fl1400': 20127,
    'nrw1379': 56638,
    'u1432': 152970,
    'fl1577': 22249,
    'd1655': 62128,
    'vm1748': 336556,
    'u1817': 57201,
    'rl1889': 316536,
    'd2103': 80450,
    'u2152': 64253,
    'pr2392': 378032,
    'u2319': 234256,
    'pcb3038': 137694,
    'fl3795': 28772,
    'fnl4461': 182566,
    'rl5915': 565530,
    'rl5934': 556045,
    'pla7397': 23260728,
    'rl11849': 923288,
    'usa13509': 19982859,
    'brd14051': 469385,
    'd15112': 1573084,
    'd18512': 645238,
    'pla33810': 66048945,
    'pla85900': 142382641,
    'mona-lisa100K': 5757191,
}

TSP_DIR = Path(__file__).resolve().parent.parent / 'benchmarks'

# Наборы инстансов
SMALL = ['eil51', 'berlin52', 'kroA100', 'ch150', 'tsp225', 'pcb442', 'att532', 'rat783']
MEDIUM = ['dsj1000', 'pcb3038', 'fl3795', 'fnl4461', 'rl5915', 'pla7397']
LARGE = ['d15112', 'pla33810']
ULTRA = ['mona-lisa100K']

DEFAULT_INSTANCES = SMALL + MEDIUM + LARGE


def load_instance(name: str) -> np.ndarray:
    """Загружает координаты из TSP файла."""
    path = TSP_DIR / f'{name}.tsp'
    if not path.exists():
        raise FileNotFoundError(f'{path} not found')
    prob = tsplib95.load(str(path))
    nodes = list(prob.get_nodes())
    return np.array([prob.node_coords[n] for n in nodes], dtype=np.float64)


def run_benchmark(
    instances: list[str],
    budget: int,
    n_runs: int,
    verbose: bool = False,
    checkpoint_path: str | None = None,
) -> dict:
    """Запускает бенчмарк."""
    results = {}

    for name in instances:
        if name not in OPTIMAL:
            print(f'SKIP {name}: no optimal value known')
            continue

        try:
            coords = load_instance(name)
        except FileNotFoundError as e:
            print(f'SKIP {name}: {e}')
            continue

        optimal = OPTIMAL[name]
        n = len(coords)
        gaps = []
        times_list = []
        phase_info = []

        print(f'\n{"="*60}')
        print(f'{name} (N={n}, optimal={optimal}, budget={budget}s, {n_runs} runs)')
        print(f'{"="*60}')

        for run in range(n_runs):
            t0 = time.perf_counter()
            result = solve_v5(coords, time_budget=budget, verbose=verbose)
            elapsed = time.perf_counter() - t0

            length = result['length']
            gap = (length - optimal) / optimal * 100
            gaps.append(round(gap, 3))
            times_list.append(round(elapsed, 1))

            # Собираем phase info
            phases = result.get('phases', {})
            info = {}
            if 'stitching' in phases:
                info['stitch_ratio'] = phases['stitching'].get('stitch_ratio', None)
            if 'v_cycle' in phases:
                info['vcycle_time'] = phases['v_cycle'].get('time', None)
                info['vcycle_improvement'] = phases['v_cycle'].get('improvement', None)
            phase_info.append(info)

            print(f'  run {run+1}: length={length:.0f}, gap={gap:.2f}%, time={elapsed:.0f}s')

        results[name] = {
            'n': n,
            'optimal': optimal,
            'budget': budget,
            'runs': gaps,
            'mean': round(float(np.mean(gaps)), 3),
            'min': round(float(min(gaps)), 3),
            'std': round(float(np.std(gaps)), 3),
            'times': times_list,
            'phase_info': phase_info,
        }

        print(f'  → mean={results[name]["mean"]:.2f}%, min={results[name]["min"]:.2f}%, '
              f'std={results[name]["std"]:.2f}%')

        # Инкрементальное сохранение после каждого инстанса
        if checkpoint_path:
            with open(checkpoint_path, 'w') as f:
                json.dump(results, f, indent=2)

    return results


def print_summary(results: dict, v53_baseline: dict | None = None):
    """Печатает таблицу результатов."""
    print(f'\n{"="*80}')
    print(f'BENCHMARK SUMMARY')
    print(f'{"="*80}')
    print(f'{"Instance":<14} {"N":>7} {"Budget":>6} {"Mean%":>7} {"Min%":>7} {"Std%":>6} '
          f'{"v5.3%":>7} {"Delta":>7}')
    print(f'{"-"*14} {"-"*7} {"-"*6} {"-"*7} {"-"*7} {"-"*6} {"-"*7} {"-"*7}')

    for name, data in sorted(results.items(), key=lambda x: x[1]['n']):
        v53 = v53_baseline.get(name, None) if v53_baseline else None
        delta = f'{data["min"] - v53:.2f}' if v53 is not None else 'N/A'
        v53_str = f'{v53:.2f}' if v53 is not None else 'N/A'

        print(f'{name:<14} {data["n"]:>7} {data["budget"]:>5}s '
              f'{data["mean"]:>6.2f}% {data["min"]:>6.2f}% {data["std"]:>5.2f}% '
              f'{v53_str:>6} {delta:>7}')


def main():
    parser = argparse.ArgumentParser(description='MASTm v6 Benchmark')
    parser.add_argument('--instances', type=str, default=None,
                        help='Comma-separated instance names')
    parser.add_argument('--budget', type=int, default=120,
                        help='Time budget per run (seconds)')
    parser.add_argument('--runs', type=int, default=3,
                        help='Number of runs per instance')
    parser.add_argument('--full', action='store_true',
                        help='Run all instances including ultra-large')
    parser.add_argument('--verbose', action='store_true',
                        help='Verbose solver output')
    parser.add_argument('--output', type=str, default=None,
                        help='Output JSON file')
    args = parser.parse_args()

    if args.instances:
        instances = args.instances.split(',')
    elif args.full:
        instances = DEFAULT_INSTANCES + ULTRA
    else:
        instances = DEFAULT_INSTANCES

    print(f'MASTm v6 Benchmark')
    print(f'Instances: {len(instances)}, Budget: {args.budget}s, Runs: {args.runs}')
    print(f'Instances: {instances}')

    _root = str(Path(__file__).resolve().parent.parent / 'results')
    out_path = args.output or f'{_root}/v6_benchmark_{args.budget}s.json'
    checkpoint_path = out_path.replace('.json', '_checkpoint.json')

    results = run_benchmark(instances, args.budget, args.runs, args.verbose,
                            checkpoint_path=checkpoint_path)

    # v5.3 baseline (known best results)
    v53 = {
        'fl3795': 0.80, 'fnl4461': 2.24, 'rl5915': 1.71,
        'pla7397': 1.40, 'd15112': 5.29, 'pla33810': 7.40,
        'mona-lisa100K': 3.17,
    }
    print_summary(results, v53)

    # Сохраняем
    _root = str(Path(__file__).resolve().parent.parent / 'results')
    out_path = args.output or f'{_root}/v6_benchmark_{args.budget}s.json'
    with open(out_path, 'w') as f:
        json.dump(results, f, indent=2)
    print(f'\nResults saved to {out_path}')


if __name__ == '__main__':
    main()
