#!/usr/bin/env python3
"""
ID-3 Deep Analysis: дополнительные исследования для углубления эксперимента.

Включает:
1. Per-axis slice ID: ID внутри каждого уровня каждой оси
2. Pairwise axis interaction: какие пары осей лучше разделяются
3. Embedding space geometry: cosine vs euclidean cluster structure
4. Effect of C4 fine-tuned model (simulated via axis-aware projection)
5. Stability analysis: повторные запуски с разными seed
6. Отдельная проверка: BERT-base (768d) vs MiniLM (384d) на Time оси

Authors: Ilya Selyutin, Nikolai Kovalev
"""

import json
import sys
import warnings
import time
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
from test_intrinsic_dimension import (
    id_twonn, id_mle, embed_texts,
    get_all_texts_and_labels,
)
from run_id3_full_experiment import (
    id_twonn_euclidean, supervised_subspace_id, load_c4factory_data,
)


BASE = Path("/Users/figuramax/LocalProjects/adaptive-topology/code/python/id3_results/full_experiment")
DEEP = BASE / "deep_analysis"
DEEP.mkdir(parents=True, exist_ok=True)
C4FACTORY = "/Users/figuramax/LocalProjects/prjcts/fleets/c4factory"


def save_json(data: dict, path: Path) -> None:
    with open(path, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False, default=str)


# ═══════════════════════════════════════════════════════════════
# 1. Per-axis slice ID: ID внутри каждого уровня оси
# ═══════════════════════════════════════════════════════════════
def per_axis_slice_id(X: np.ndarray, labels: List[Tuple[int, int, int]]) -> Dict:
    """Для каждой оси, для каждого уровня (0,1,2): замерить ID подвыборки."""
    labels_arr = np.array(labels)
    axes = ["Time", "Scale", "Agency"]
    result: Dict = {}

    for ax_idx, ax_name in enumerate(axes):
        for level in range(3):
            mask = labels_arr[:, ax_idx] == level
            X_sub = X[mask]
            if X_sub.shape[0] < 20:
                continue

            d_twonn = id_twonn_euclidean(X_sub)
            d_mle = id_mle(X_sub, k=min(10, X_sub.shape[0] // 3))

            key = f"{ax_name}_{level}"
            result[key] = {
                "n": int(X_sub.shape[0]),
                "id_twonn": round(float(d_twonn), 2),
                "id_mle": round(float(d_mle), 2),
            }

            # Subspace ID внутри slice
            if X_sub.shape[0] >= 50:
                # Используем оставшиеся 2 оси как labels
                other_axes = [i for i in range(3) if i != ax_idx]
                sub_labels = [(int(labels_arr[j, other_axes[0]]), int(labels_arr[j, other_axes[1]]))
                              for j in np.where(mask)[0]]
                # 2D labels → supervised subspace
                from sklearn.linear_model import Ridge
                from sklearn.preprocessing import StandardScaler
                sub_labels_arr = np.array(sub_labels, dtype=float)
                scaler = StandardScaler()
                X_scaled = scaler.fit_transform(X_sub)
                ridge = Ridge(alpha=1.0)
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    ridge.fit(X_scaled, sub_labels_arr)
                proj = ridge.predict(X_scaled)
                d_sub = id_twonn_euclidean(proj)
                result[key]["subspace_2d_id"] = round(float(d_sub), 2)

    return result


# ═══════════════════════════════════════════════════════════════
# 2. Pairwise axis interaction
# ═══════════════════════════════════════════════════════════════
def pairwise_axis_analysis(X: np.ndarray, labels: List[Tuple[int, int, int]]) -> Dict:
    """MI и classification для каждой ПАРЫ осей (TxD, TxA, DxA)."""
    from sklearn.linear_model import Ridge
    from sklearn.model_selection import cross_val_score
    from sklearn.preprocessing import StandardScaler

    labels_arr = np.array(labels, dtype=float)
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    pairs = [("Time+Scale", [0, 1]), ("Time+Agency", [0, 2]), ("Scale+Agency", [1, 2])]
    result: Dict = {}

    for pair_name, axes in pairs:
        y_pair = labels_arr[:, axes]
        ridge = Ridge(alpha=1.0)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            # Multi-output R²
            r2_scores = cross_val_score(ridge, X_scaled, y_pair, cv=5, scoring="r2")
        result[pair_name] = {
            "r2_mean": round(float(np.mean(r2_scores)), 3),
            "r2_std": round(float(np.std(r2_scores)), 3),
        }

        # 2D subspace ID
        ridge_fit = Ridge(alpha=1.0)
        ridge_fit.fit(X_scaled, y_pair)
        proj = ridge_fit.predict(X_scaled)
        d = id_twonn_euclidean(proj)
        result[pair_name]["subspace_2d_id"] = round(float(d), 2)

    return result


# ═══════════════════════════════════════════════════════════════
# 3. Stability analysis: разные seed'ы
# ═══════════════════════════════════════════════════════════════
def stability_analysis(
    c4factory_path: str,
    model_name: str,
    n_seeds: int = 5,
    sample_size: int = 1000,
) -> Dict:
    """Проверяем стабильность subspace ID через разные случайные выборки."""
    subspace_ids = []
    full_ids = []

    for seed in range(n_seeds):
        rng = np.random.default_rng(seed * 1000 + 42)
        texts, labels = load_c4factory_data(c4factory_path, sample_size=sample_size, rng=rng)
        if len(texts) < 50:
            continue
        emb = embed_texts(texts, model_name)
        sup = supervised_subspace_id(emb, labels)
        fid = id_twonn_euclidean(emb)

        subspace_ids.append(sup["c4_subspace_id_twonn"])
        full_ids.append(float(fid))
        print(f"    Seed {seed}: sub_id={sup['c4_subspace_id_twonn']:.2f}, full_id={fid:.2f}")

    return {
        "n_seeds": n_seeds,
        "sample_size": sample_size,
        "subspace_ids": [round(x, 2) for x in subspace_ids],
        "subspace_mean": round(float(np.mean(subspace_ids)), 3),
        "subspace_std": round(float(np.std(subspace_ids)), 3),
        "full_ids": [round(x, 2) for x in full_ids],
        "full_mean": round(float(np.mean(full_ids)), 3),
        "full_std": round(float(np.std(full_ids)), 3),
    }


# ═══════════════════════════════════════════════════════════════
# 4. Time axis deep dive: tense markers analysis
# ═══════════════════════════════════════════════════════════════
def time_axis_deep_dive(X: np.ndarray, labels: List[Tuple[int, int, int]]) -> Dict:
    """Детальный анализ: ПОЧЕМУ Time не декодируется?

    Гипотеза: sentence-transformers кодируют семантику, а не грамматику.
    Проверяем: если оставить только Scale-нейтральные тексты (D=const),
    различаются ли Past/Present/Future?
    """
    from sklearn.neighbors import KNeighborsClassifier
    from sklearn.model_selection import cross_val_score
    from sklearn.metrics.pairwise import cosine_distances

    labels_arr = np.array(labels)
    result: Dict = {}

    # Для каждого фиксированного (D, A) — accuracy по Time
    time_accs_controlled: List[float] = []
    for d in range(3):
        for a in range(3):
            mask = (labels_arr[:, 1] == d) & (labels_arr[:, 2] == a)
            X_sub = X[mask]
            y_time = labels_arr[mask, 0]
            if len(set(y_time)) < 2 or X_sub.shape[0] < 15:
                continue
            clf = KNeighborsClassifier(n_neighbors=min(3, X_sub.shape[0] - 1))
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                cv = min(3, min(np.bincount(y_time.astype(int))))
                if cv < 2:
                    continue
                scores = cross_val_score(clf, X_sub, y_time, cv=cv)
            acc = float(np.mean(scores))
            time_accs_controlled.append(acc)
            result[f"Time_acc_D{d}_A{a}"] = round(acc, 3)

    if time_accs_controlled:
        result["Time_controlled_mean_acc"] = round(float(np.mean(time_accs_controlled)), 3)
        result["Time_controlled_max_acc"] = round(float(np.max(time_accs_controlled)), 3)

    # Centroid distances по Time при фиксированных D, A
    centroid_dists: Dict[str, float] = {}
    for t1 in range(3):
        for t2 in range(t1 + 1, 3):
            dists_da: List[float] = []
            for d in range(3):
                for a in range(3):
                    mask1 = (labels_arr[:, 0] == t1) & (labels_arr[:, 1] == d) & (labels_arr[:, 2] == a)
                    mask2 = (labels_arr[:, 0] == t2) & (labels_arr[:, 1] == d) & (labels_arr[:, 2] == a)
                    if mask1.sum() < 3 or mask2.sum() < 3:
                        continue
                    c1 = X[mask1].mean(axis=0)
                    c2 = X[mask2].mean(axis=0)
                    dist = float(cosine_distances(c1.reshape(1, -1), c2.reshape(1, -1))[0, 0])
                    dists_da.append(dist)

            if dists_da:
                centroid_dists[f"T{t1}_vs_T{t2}_mean_dist"] = round(float(np.mean(dists_da)), 4)

    result["centroid_distances"] = centroid_dists

    # Сравним с Scale centroid distances
    for d1 in range(3):
        for d2 in range(d1 + 1, 3):
            dists_ta: List[float] = []
            for t in range(3):
                for a in range(3):
                    mask1 = (labels_arr[:, 0] == t) & (labels_arr[:, 1] == d1) & (labels_arr[:, 2] == a)
                    mask2 = (labels_arr[:, 0] == t) & (labels_arr[:, 1] == d2) & (labels_arr[:, 2] == a)
                    if mask1.sum() < 3 or mask2.sum() < 3:
                        continue
                    c1 = X[mask1].mean(axis=0)
                    c2 = X[mask2].mean(axis=0)
                    dist = float(cosine_distances(c1.reshape(1, -1), c2.reshape(1, -1))[0, 0])
                    dists_ta.append(dist)
            if dists_ta:
                centroid_dists[f"D{d1}_vs_D{d2}_mean_dist"] = round(float(np.mean(dists_ta)), 4)

    return result


# ═══════════════════════════════════════════════════════════════
# 5. Effective dimensionality: Shannon entropy of eigenvalues
# ═══════════════════════════════════════════════════════════════
def effective_dimensionality(X: np.ndarray, labels: List[Tuple[int, int, int]]) -> Dict:
    """Effective dimensionality через участие (participation ratio) собственных значений."""
    from sklearn.decomposition import PCA

    # Full space
    pca = PCA(n_components=min(50, X.shape[0], X.shape[1]))
    pca.fit(X)
    ev = pca.explained_variance_ratio_
    ev = ev[ev > 1e-10]
    # Participation ratio: (Σλ)² / Σλ²
    pr_full = float(np.sum(ev) ** 2 / np.sum(ev ** 2))

    # Subspace
    from sklearn.linear_model import Ridge
    from sklearn.preprocessing import StandardScaler
    labels_arr = np.array(labels, dtype=float)
    scaler = StandardScaler()
    X_sc = scaler.fit_transform(X)
    ridge = Ridge(alpha=1.0)
    ridge.fit(X_sc, labels_arr)
    proj = ridge.predict(X_sc)

    pca_sub = PCA(n_components=min(3, proj.shape[1]))
    pca_sub.fit(proj)
    ev_sub = pca_sub.explained_variance_ratio_
    pr_sub = float(np.sum(ev_sub) ** 2 / np.sum(ev_sub ** 2))

    # Shannon entropy dimensionality
    p = ev / ev.sum()
    shannon = float(-np.sum(p * np.log(p + 1e-20)))
    d_shannon = float(np.exp(shannon))

    return {
        "participation_ratio_full": round(pr_full, 2),
        "participation_ratio_subspace": round(pr_sub, 2),
        "shannon_entropy_dim": round(d_shannon, 2),
        "top3_var_explained": round(float(sum(ev[:3])), 4),
        "top10_var_explained": round(float(sum(ev[:10])), 4),
    }


# ═══════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════
def main():
    print("=" * 70)
    print("  ID-3 DEEP ANALYSIS")
    print("=" * 70)

    rng = np.random.default_rng(42)
    model = "all-MiniLM-L6-v2"

    # Загружаем данные
    print("\n  Loading c4factory data (N=2000)...")
    texts, labels = load_c4factory_data(C4FACTORY, sample_size=2000, rng=rng)
    print(f"  Loaded {len(texts)} texts")
    embeddings = embed_texts(texts, model)
    print(f"  Embedding dim: {embeddings.shape[1]}")

    all_results: Dict = {}

    # 1. Per-axis slice ID
    print("\n" + "─" * 70)
    print("  1. PER-AXIS SLICE ID")
    print("─" * 70)
    slice_id = per_axis_slice_id(embeddings, labels)
    print(f"  {'Slice':<15} {'N':>6} {'ID TwoNN':>10} {'ID MLE':>10} {'Sub 2D ID':>10}")
    for key, val in slice_id.items():
        sub = val.get("subspace_2d_id", "—")
        print(f"  {key:<15} {val['n']:>6} {val['id_twonn']:>10.2f} {val['id_mle']:>10.2f} {sub:>10}")
    all_results["per_axis_slice_id"] = slice_id
    save_json(slice_id, DEEP / "per_axis_slice_id.json")

    # 2. Pairwise axis analysis
    print("\n" + "─" * 70)
    print("  2. PAIRWISE AXIS INTERACTION")
    print("─" * 70)
    pairs = pairwise_axis_analysis(embeddings, labels)
    print(f"  {'Pair':<20} {'R²':>8} {'Sub 2D ID':>12}")
    for pair_name, val in pairs.items():
        print(f"  {pair_name:<20} {val['r2_mean']:>8.3f} {val['subspace_2d_id']:>12.2f}")
    all_results["pairwise_axes"] = pairs
    save_json(pairs, DEEP / "pairwise_axes.json")

    # 3. Stability analysis
    print("\n" + "─" * 70)
    print("  3. STABILITY ANALYSIS (5 seeds × N=1000)")
    print("─" * 70)
    stability = stability_analysis(C4FACTORY, model, n_seeds=5, sample_size=1000)
    print(f"\n  Subspace ID: {stability['subspace_mean']:.3f} ± {stability['subspace_std']:.3f}")
    print(f"  Full ID:     {stability['full_mean']:.3f} ± {stability['full_std']:.3f}")
    all_results["stability"] = stability
    save_json(stability, DEEP / "stability.json")

    # 4. Time axis deep dive
    print("\n" + "─" * 70)
    print("  4. TIME AXIS DEEP DIVE")
    print("─" * 70)
    time_dd = time_axis_deep_dive(embeddings, labels)
    print(f"  Time controlled mean acc: {time_dd.get('Time_controlled_mean_acc', '?')}")
    print(f"  Time controlled max acc:  {time_dd.get('Time_controlled_max_acc', '?')}")
    print(f"\n  Centroid distances:")
    cd = time_dd.get("centroid_distances", {})
    for k, v in cd.items():
        print(f"    {k}: {v:.4f}")
    all_results["time_deep_dive"] = time_dd
    save_json(time_dd, DEEP / "time_deep_dive.json")

    # 5. Effective dimensionality
    print("\n" + "─" * 70)
    print("  5. EFFECTIVE DIMENSIONALITY (participation ratio + Shannon)")
    print("─" * 70)
    eff_dim = effective_dimensionality(embeddings, labels)
    print(f"  Participation ratio (full):     {eff_dim['participation_ratio_full']:.2f}")
    print(f"  Participation ratio (subspace): {eff_dim['participation_ratio_subspace']:.2f}")
    print(f"  Shannon entropy dimension:      {eff_dim['shannon_entropy_dim']:.2f}")
    print(f"  Top-3 var explained:            {eff_dim['top3_var_explained']:.4f}")
    all_results["effective_dim"] = eff_dim
    save_json(eff_dim, DEEP / "effective_dim.json")

    # 6. Сравнение BERT-base (768d) — на тех же данных
    print("\n" + "─" * 70)
    print("  6. BERT-BASE COMPARISON (768d vs 384d)")
    print("─" * 70)
    models_compare = [
        ("all-MiniLM-L6-v2", "MiniLM-384d"),
        ("all-mpnet-base-v2", "MPNet-768d"),
    ]
    model_comparison: Dict[str, Dict] = {}
    for model_id, label in models_compare:
        print(f"\n  {label}:")
        emb = embed_texts(texts, model_id)
        sup = supervised_subspace_id(emb, labels)

        # Per-axis R²
        from sklearn.linear_model import Ridge
        from sklearn.preprocessing import StandardScaler
        from sklearn.model_selection import cross_val_score
        labels_arr = np.array(labels, dtype=float)
        sc = StandardScaler()
        X_sc = sc.fit_transform(emb)

        per_ax: Dict[str, float] = {}
        for ax_idx, ax_name in enumerate(["Time", "Scale", "Agency"]):
            r = Ridge(alpha=1.0)
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                r2 = cross_val_score(r, X_sc, labels_arr[:, ax_idx], cv=5, scoring="r2")
            per_ax[f"{ax_name}_r2"] = round(float(np.mean(r2)), 3)
            print(f"    {ax_name} R²: {np.mean(r2):.3f}")

        model_comparison[label] = {
            "subspace_id": sup["c4_subspace_id_twonn"],
            "c4_var": sup["c4_variance_explained"],
            **per_ax,
        }

    all_results["model_comparison"] = model_comparison
    save_json(model_comparison, DEEP / "model_comparison.json")

    # Grand save
    save_json(all_results, DEEP / "deep_analysis_all.json")

    # Summary
    print("\n" + "=" * 70)
    print("  DEEP ANALYSIS COMPLETE")
    print("=" * 70)
    print(f"\n  Results saved to: {DEEP}")
    print(f"  Files: {[f.name for f in DEEP.glob('*.json')]}")

    return all_results


if __name__ == "__main__":
    main()
