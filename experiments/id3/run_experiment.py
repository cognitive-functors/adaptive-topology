#!/usr/bin/env python3
"""
ID-3 Full Experiment: 5-Phase validation of Hypothesis ID-3.

Phase 0: Fix estimator bugs (TwoNN Euclidean, bootstrap mean, supervised projection)
Phase 1: Multi-model robustness (5 embedding models)
Phase 2: Controlled template dataset (minimal pairs)
Phase 3: Large-scale c4factory data (1000+ real texts, EN+RU)
Phase 4: Supervised subspace ID (KEY: project to C4 3D → measure ID)
Phase 5: Cross-linguistic comparison (EN vs RU axis salience)

Usage:
    python3 run_id3_full_experiment.py --c4factory /path/to/c4factory
    python3 run_id3_full_experiment.py --phase 4        # только одна фаза
    python3 run_id3_full_experiment.py --sample-size 2000

Authors: Ilya Selyutin, Nikolai Kovalev
License: Apache-2.0-NC
"""

import argparse
import json
import sys
import warnings
import time
from pathlib import Path
from typing import List, Dict, Tuple, Optional

import numpy as np

# Импортируем базовые функции
from test_intrinsic_dimension import (
    id_pca, id_twonn, id_mle, id_correlation,
    bootstrap_id_estimates, permutation_test,
    per_axis_dimensionality, classification_accuracy,
    random_baseline_comparison, embed_texts,
    get_all_texts_and_labels, C4_EXAMPLES,
)


# ═══════════════════════════════════════════════════════════════
# PHASE 0: Исправленные оценщики
# ═══════════════════════════════════════════════════════════════

def id_twonn_euclidean(X: np.ndarray) -> float:
    """TwoNN с Euclidean distance — стабильнее на малых выборках."""
    from sklearn.neighbors import NearestNeighbors

    nn = NearestNeighbors(n_neighbors=3, metric="euclidean")
    nn.fit(X)
    distances, _ = nn.kneighbors(X)

    r1 = distances[:, 1]
    r2 = distances[:, 2]

    mask = (r1 > 1e-10) & (r2 > 1e-10)
    r1 = r1[mask]
    r2 = r2[mask]

    if len(r1) < 3:
        return float("nan")

    mu = r2 / r1
    n = len(mu)
    log_sum = np.sum(np.log(mu))

    if log_sum <= 0:
        return float("nan")

    return float(n / log_sum)


def bootstrap_mean_id(
    X: np.ndarray,
    n_bootstrap: int = 1000,
    confidence: float = 0.95,
    rng: Optional[np.random.Generator] = None,
) -> Dict[str, float]:
    """Bootstrap среднего ID по всем методам — правильный статистический тест."""
    if rng is None:
        rng = np.random.default_rng(42)

    n = X.shape[0]
    mean_ids: List[float] = []

    for _ in range(n_bootstrap):
        idx = rng.choice(n, size=n, replace=True)
        # Дедупликация для TwoNN
        unique_idx = np.unique(idx)
        X_b = X[unique_idx]
        if X_b.shape[0] < 10:
            continue

        estimates = []
        d = id_twonn_euclidean(X_b)
        if not np.isnan(d):
            estimates.append(d)
        for k in [10, 20]:
            d = id_mle(X_b, k=k)
            if not np.isnan(d):
                estimates.append(d)
        d = id_correlation(X_b)
        if not np.isnan(d):
            estimates.append(d)

        if estimates:
            mean_ids.append(float(np.mean(estimates)))

    if len(mean_ids) < 10:
        return {"mean": float("nan"), "ci_low": float("nan"), "ci_high": float("nan"),
                "std": float("nan"), "n_valid": 0}

    arr = np.array(mean_ids)
    alpha = (1 - confidence) / 2
    return {
        "mean": round(float(np.mean(arr)), 2),
        "ci_low": round(float(np.percentile(arr, alpha * 100)), 2),
        "ci_high": round(float(np.percentile(arr, (1 - alpha) * 100)), 2),
        "std": round(float(np.std(arr)), 2),
        "n_valid": len(mean_ids),
        "three_in_ci": bool(np.percentile(arr, alpha * 100) <= 3.0 <= np.percentile(arr, (1 - alpha) * 100)),
    }


def supervised_subspace_id(
    X: np.ndarray,
    labels: List[Tuple[int, int, int]],
) -> Dict[str, float]:
    """
    КЛЮЧЕВОЙ ТЕСТ: проецируем эмбеддинги на C4-релевантное подпространство,
    измеряем ID проекции (должен быть ≈ 3).

    Метод: обучаем 3 линейных регрессора (→T, →D, →A), используем их веса
    как оси C4-подпространства. Проецируем, измеряем ID.
    """
    from sklearn.linear_model import Ridge
    from sklearn.preprocessing import StandardScaler
    from sklearn.model_selection import cross_val_score

    labels_arr = np.array(labels, dtype=float)
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    # Обучаем 3 регрессора: один на каждую ось
    axis_names = ["Time", "Scale", "Agency"]
    projections = []
    r2_scores: Dict[str, float] = {}

    for ax_idx, ax_name in enumerate(axis_names):
        y = labels_arr[:, ax_idx]
        reg = Ridge(alpha=1.0)
        reg.fit(X_scaled, y)

        # R² через CV
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            cv_scores = cross_val_score(reg, X_scaled, y, cv=5, scoring="r2")
        r2_scores[f"{ax_name}_r2"] = round(float(np.mean(cv_scores)), 3)

        # Проекция на ось
        projection = X_scaled @ reg.coef_
        projections.append(projection)

    # Собираем 3D проекцию
    X_c4 = np.column_stack(projections)

    # ID этого 3D подпространства
    id_proj_twonn = id_twonn_euclidean(X_c4)
    id_proj_mle = id_mle(X_c4, k=10)

    # Для контроля: ID residual (всё что НЕ C4)
    # Ортогональный complement: X - X_c4 * pinv(X_c4) * X
    from numpy.linalg import lstsq
    coefs, _, _, _ = lstsq(X_c4, X_scaled, rcond=None)
    X_reconstructed = X_c4 @ coefs
    X_residual = X_scaled - X_reconstructed
    id_residual_twonn = id_twonn_euclidean(X_residual)

    # Доля дисперсии, объяснённая C4
    total_var = np.var(X_scaled, axis=0).sum()
    c4_var = np.var(X_reconstructed, axis=0).sum()
    residual_var = np.var(X_residual, axis=0).sum()
    variance_explained = c4_var / total_var if total_var > 0 else 0.0

    return {
        "c4_subspace_id_twonn": round(float(id_proj_twonn), 2),
        "c4_subspace_id_mle": round(float(id_proj_mle), 2),
        "residual_id_twonn": round(float(id_residual_twonn), 2),
        "c4_variance_explained": round(float(variance_explained), 4),
        **r2_scores,
    }


# ═══════════════════════════════════════════════════════════════
# PHASE 2: Контролируемый датасет (минимальные пары)
# ═══════════════════════════════════════════════════════════════

CONTROLLED_TEMPLATES: Dict[str, List[str]] = {
    # Формат: фиксируем тему, варьируем ТОЛЬКО C4-координаты
    # Тема 1: работа с кодом
    "(0,0,0)": ["I fixed the bug in the login module yesterday",
                "I wrote this function last week",
                "I deleted the old config file on Monday",
                "I ran the tests before the deadline",
                "I deployed the hotfix last night"],
    "(1,0,0)": ["I am fixing the bug in the login module right now",
                "I am writing this function at the moment",
                "I am deleting the old config file now",
                "I am running the tests right now",
                "I am deploying the hotfix at this moment"],
    "(2,0,0)": ["I will fix the bug in the login module tomorrow",
                "I will write this function next week",
                "I will delete the old config file on Friday",
                "I will run the tests after lunch",
                "I will deploy the hotfix tonight"],
    "(0,0,1)": ["She fixed the bug in the login module yesterday",
                "He wrote this function last week",
                "They deleted the old config file on Monday",
                "She ran the tests before the deadline",
                "He deployed the hotfix last night"],
    "(1,0,1)": ["She is fixing the bug in the login module right now",
                "He is writing this function at the moment",
                "They are deleting the old config file now",
                "She is running the tests right now",
                "He is deploying the hotfix at this moment"],
    "(2,0,1)": ["She will fix the bug in the login module tomorrow",
                "He will write this function next week",
                "They will delete the old config file on Friday",
                "She will run the tests after lunch",
                "He will deploy the hotfix tonight"],
    "(0,0,2)": ["The system fixed the bug in the login module yesterday",
                "The pipeline processed this function last week",
                "The cleanup script deleted the old config file on Monday",
                "The CI server ran the tests before the deadline",
                "The deployment system rolled out the hotfix last night"],
    "(1,0,2)": ["The system is fixing the bug in the login module right now",
                "The pipeline is processing this function at the moment",
                "The cleanup script is deleting the old config file now",
                "The CI server is running the tests right now",
                "The deployment system is rolling out the hotfix at this moment"],
    "(2,0,2)": ["The system will fix the bug in the login module tomorrow",
                "The pipeline will process this function next week",
                "The cleanup script will delete the old config file on Friday",
                "The CI server will run the tests after lunch",
                "The deployment system will roll out the hotfix tonight"],
    # Abstract level
    "(0,1,0)": ["I used to struggle with understanding complex architectures",
                "I had a pattern of avoiding refactoring tasks",
                "I tended to overcomplicate my solutions in the past",
                "I habitually skipped writing tests before",
                "I used to rely too much on intuition when debugging"],
    "(1,1,0)": ["I notice I struggle with understanding complex architectures",
                "I have a pattern of avoiding refactoring tasks",
                "I tend to overcomplicate my solutions",
                "I habitually skip writing tests",
                "I rely too much on intuition when debugging"],
    "(2,1,0)": ["I will learn to understand complex architectures better",
                "I plan to overcome my pattern of avoiding refactoring",
                "I will simplify my approach to solutions",
                "I intend to start writing tests consistently",
                "I will develop a more systematic debugging approach"],
    "(0,1,1)": ["He used to struggle with understanding complex architectures",
                "She had a pattern of avoiding refactoring tasks",
                "They tended to overcomplicate solutions in the past",
                "He habitually skipped writing tests before",
                "She used to rely too much on intuition when debugging"],
    "(1,1,1)": ["He struggles with understanding complex architectures",
                "She has a pattern of avoiding refactoring tasks",
                "They tend to overcomplicate their solutions",
                "He habitually skips writing tests",
                "She relies too much on intuition when debugging"],
    "(2,1,1)": ["He will learn to understand complex architectures better",
                "She plans to overcome her pattern of avoiding refactoring",
                "They will simplify their approach to solutions",
                "He intends to start writing tests consistently",
                "She will develop a more systematic debugging approach"],
    "(0,1,2)": ["The industry used to struggle with understanding distributed systems",
                "Organizations had a pattern of avoiding technical debt",
                "Companies tended to overcomplicate their infrastructure",
                "The field habitually ignored testing standards before",
                "Software development used to rely too much on manual processes"],
    "(1,1,2)": ["The industry struggles with understanding distributed systems",
                "Organizations have a pattern of avoiding technical debt",
                "Companies tend to overcomplicate their infrastructure",
                "The field habitually ignores testing standards",
                "Software development relies too much on manual processes"],
    "(2,1,2)": ["The industry will learn to handle distributed systems better",
                "Organizations will overcome their pattern of ignoring debt",
                "Companies will simplify their infrastructure",
                "The field will adopt better testing standards",
                "Software development will become more automated"],
    # Meta level
    "(0,2,0)": ["I used to think my approach to coding was the only right way",
                "I believed my debugging methodology was complete and sufficient",
                "I assumed my mental model of the system was accurate",
                "I thought my way of learning was the best possible method",
                "I believed my framework for evaluating code quality was sound"],
    "(1,2,0)": ["I am questioning whether my approach to coding is the right one",
                "I notice my debugging methodology might be incomplete",
                "I realize my mental model of the system might be inaccurate",
                "I am reconsidering my way of learning right now",
                "I am examining my framework for evaluating code quality"],
    "(2,2,0)": ["I wonder how my approach to coding will evolve over time",
                "I expect my debugging methodology will need revision",
                "I anticipate my mental model will change significantly",
                "I think my learning methods will transform in the future",
                "I predict my quality framework will require updating"],
    "(0,2,1)": ["He used to think his approach to coding was the only right way",
                "She believed her debugging methodology was complete",
                "They assumed their mental model was accurate",
                "He thought his learning method was the best possible",
                "She believed her quality framework was sound"],
    "(1,2,1)": ["He is questioning whether his approach to coding is right",
                "She notices her debugging methodology might be incomplete",
                "They realize their mental model might be inaccurate",
                "He is reconsidering his way of learning",
                "She is examining her quality evaluation framework"],
    "(2,2,1)": ["He wonders how his coding approach will evolve",
                "She expects her methodology will need revision",
                "They anticipate their mental model will change",
                "He thinks his learning methods will transform",
                "She predicts her quality framework will need updating"],
    "(0,2,2)": ["Science used to assume the waterfall model was the correct paradigm",
                "The field believed formal verification was sufficient for quality",
                "Academia assumed their theory of computation covered everything",
                "The industry thought object-oriented was the ultimate paradigm",
                "The community believed testing was secondary to design"],
    "(1,2,2)": ["Science is questioning whether agile is the correct paradigm",
                "The field is reconsidering whether AI testing methods are sufficient",
                "Academia notices their theory of computation has gaps",
                "The industry is debating whether functional programming is superior",
                "The community is examining whether testing methodologies are adequate"],
    "(2,2,2)": ["Science will develop new paradigms beyond agile and waterfall",
                "The field will create better frameworks for understanding quality",
                "Academia will revise their theories of computation fundamentally",
                "The industry will transcend the OOP vs FP debate entirely",
                "The community will rethink what testing means in the age of AI"],
}


def get_controlled_texts_and_labels() -> Tuple[List[str], List[Tuple[int, int, int]]]:
    """Извлечь контролируемые тексты и метки."""
    texts: List[str] = []
    labels: List[Tuple[int, int, int]] = []
    for state_key, examples in CONTROLLED_TEMPLATES.items():
        coords = tuple(int(x) for x in state_key.strip("()").split(","))
        for text in examples:
            texts.append(text)
            labels.append(coords)
    return texts, labels


# ═══════════════════════════════════════════════════════════════
# PHASE 3: Загрузка данных из c4factory
# ═══════════════════════════════════════════════════════════════

def load_c4factory_data(
    c4factory_path: str,
    sample_size: int = 2000,
    lang: Optional[str] = None,
    rng: Optional[np.random.Generator] = None,
) -> Tuple[List[str], List[Tuple[int, int, int]]]:
    """Загрузить и сэмплировать данные из c4factory/c4_classifier."""
    if rng is None:
        rng = np.random.default_rng(42)

    data_file = Path(c4factory_path) / "kaggle_data" / "c4_classifier" / "train.jsonl"
    if not data_file.exists():
        # Альтернативный путь
        data_file = Path(c4factory_path) / "kaggle_data" / "c4_classifier" / "val.jsonl"
    if not data_file.exists():
        print(f"  ERROR: не найден файл {data_file}")
        return [], []

    # Загружаем все данные (или достаточно много)
    all_items: List[Dict] = []
    with open(data_file) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            obj = json.loads(line)
            if lang and obj.get("lang") != lang:
                continue
            # Фильтруем слишком короткие тексты
            if len(obj.get("text", "")) < 15:
                continue
            all_items.append(obj)
            if len(all_items) >= sample_size * 5:
                break

    if not all_items:
        print(f"  ERROR: нет данных в {data_file}")
        return [], []

    # Стратифицированная выборка: равное число от каждого C4-состояния
    from collections import defaultdict
    by_state: Dict[int, List[Dict]] = defaultdict(list)
    for item in all_items:
        by_state[item["c4_index"]].append(item)

    per_state = max(1, sample_size // 27)
    sampled: List[Dict] = []
    for state_idx in range(27):
        items = by_state.get(state_idx, [])
        if items:
            n = min(per_state, len(items))
            chosen = rng.choice(len(items), size=n, replace=False)
            for idx in chosen:
                sampled.append(items[idx])

    texts = [item["text"] for item in sampled]
    labels = [(item["t"], item["d"], item["i"]) for item in sampled]

    return texts, labels


# ═══════════════════════════════════════════════════════════════
# PHASE 6: Time axis diagnosis
# ═══════════════════════════════════════════════════════════════

def diagnose_time_axis(
    X: np.ndarray,
    labels: List[Tuple[int, int, int]],
) -> Dict:
    """Глубокая диагностика оси Time: линейный vs нелинейный, per-tense анализ."""
    from sklearn.linear_model import Ridge
    from sklearn.neural_network import MLPRegressor
    from sklearn.preprocessing import StandardScaler
    from sklearn.model_selection import cross_val_score

    labels_arr = np.array(labels, dtype=float)
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    axis_names = ["Time", "Scale", "Agency"]
    result: Dict = {}

    for ax_idx, ax_name in enumerate(axis_names):
        y = labels_arr[:, ax_idx]

        # Linear probe (Ridge)
        ridge = Ridge(alpha=1.0)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            r2_linear = cross_val_score(ridge, X_scaled, y, cv=5, scoring="r2")

        # Non-linear probe (MLP)
        mlp = MLPRegressor(
            hidden_layer_sizes=(128, 64), max_iter=500,
            random_state=42, early_stopping=True, validation_fraction=0.15,
        )
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            r2_mlp = cross_val_score(mlp, X_scaled, y, cv=5, scoring="r2")

        result[f"{ax_name}_ridge_r2"] = round(float(np.mean(r2_linear)), 3)
        result[f"{ax_name}_mlp_r2"] = round(float(np.mean(r2_mlp)), 3)
        result[f"{ax_name}_nonlinear_gain"] = round(float(np.mean(r2_mlp) - np.mean(r2_linear)), 3)

    # Per-tense cluster analysis: внутриклассовое vs межклассовое расстояние
    from sklearn.metrics.pairwise import cosine_distances

    for ax_idx, ax_name in enumerate(axis_names):
        within_dists: List[float] = []
        between_dists: List[float] = []

        for level in range(3):
            mask_level = labels_arr[:, ax_idx] == level
            X_level = X[mask_level]
            if X_level.shape[0] < 2:
                continue

            # Внутриклассовые расстояния
            D_within = cosine_distances(X_level)
            np.fill_diagonal(D_within, np.nan)
            within_dists.extend(D_within[~np.isnan(D_within)].tolist())

            # Межклассовые расстояния
            mask_other = labels_arr[:, ax_idx] != level
            X_other = X[mask_other]
            if X_other.shape[0] > 0:
                # Подвыборка для скорости
                n_sub = min(200, X_other.shape[0])
                idx_sub = np.random.choice(X_other.shape[0], n_sub, replace=False)
                D_between = cosine_distances(X_level[:min(50, X_level.shape[0])], X_other[idx_sub])
                between_dists.extend(D_between.flatten().tolist())

        if within_dists and between_dists:
            # Fisher ratio: (mean_between - mean_within) / (std_within + std_between)
            mean_w = np.mean(within_dists)
            mean_b = np.mean(between_dists)
            std_w = np.std(within_dists)
            std_b = np.std(between_dists)
            fisher = (mean_b - mean_w) / (std_w + std_b + 1e-10)
            result[f"{ax_name}_fisher_ratio"] = round(float(fisher), 4)
            result[f"{ax_name}_within_dist"] = round(float(mean_w), 4)
            result[f"{ax_name}_between_dist"] = round(float(mean_b), 4)

    return result


# ═══════════════════════════════════════════════════════════════
# PHASE 7: Scaling analysis
# ═══════════════════════════════════════════════════════════════

def scaling_analysis(
    c4factory_path: str,
    model_name: str,
    sample_sizes: Optional[List[int]] = None,
) -> Dict[str, List]:
    """ID vs N: сходится ли subspace ID к 3 при увеличении данных?"""
    if sample_sizes is None:
        sample_sizes = [50, 100, 250, 500, 1000, 2000, 5000]

    result: Dict[str, List] = {"N": [], "subspace_id_twonn": [], "subspace_id_ci_low": [],
                                "subspace_id_ci_high": [], "full_id": [], "perm_p": []}

    for n in sample_sizes:
        rng = np.random.default_rng(42)
        texts, labels = load_c4factory_data(c4factory_path, sample_size=n, rng=rng)
        if len(texts) < 20:
            continue

        embeddings = embed_texts(texts, model_name)

        # Subspace ID
        sup = supervised_subspace_id(embeddings, labels)
        full_id = id_twonn_euclidean(embeddings)

        # Bootstrap CI для subspace ID
        from sklearn.linear_model import Ridge
        from sklearn.preprocessing import StandardScaler

        boot_ids: List[float] = []
        for _ in range(50):
            idx = rng.choice(len(labels), size=len(labels), replace=True)
            unique_idx = np.unique(idx)
            X_b = embeddings[unique_idx]
            labs_b = [labels[i] for i in unique_idx]
            if len(labs_b) < 20:
                continue
            try:
                s = supervised_subspace_id(X_b, labs_b)
                d = s["c4_subspace_id_twonn"]
                if not np.isnan(d):
                    boot_ids.append(d)
            except Exception:
                continue

        ci_low = float(np.percentile(boot_ids, 2.5)) if len(boot_ids) > 5 else float("nan")
        ci_high = float(np.percentile(boot_ids, 97.5)) if len(boot_ids) > 5 else float("nan")

        result["N"].append(len(texts))
        result["subspace_id_twonn"].append(sup["c4_subspace_id_twonn"])
        result["subspace_id_ci_low"].append(round(ci_low, 2))
        result["subspace_id_ci_high"].append(round(ci_high, 2))
        result["full_id"].append(round(float(full_id), 2))

        perm = permutation_test(embeddings, labels, n_permutations=100, rng=rng)
        result["perm_p"].append(perm["p_value"])

        print(f"  N={len(texts):>5}: subspace ID={sup['c4_subspace_id_twonn']:.2f} "
              f"[{ci_low:.2f}, {ci_high:.2f}], full ID={full_id:.2f}, p={perm['p_value']:.4f}")

    return result


# ═══════════════════════════════════════════════════════════════
# PHASE 8: Per-state confusion & topology
# ═══════════════════════════════════════════════════════════════

def per_state_topology(
    X: np.ndarray,
    labels: List[Tuple[int, int, int]],
) -> Dict:
    """Анализ попарных расстояний и confusion matrix для 27 состояний."""
    from sklearn.neighbors import KNeighborsClassifier
    from sklearn.model_selection import cross_val_predict
    from sklearn.metrics import confusion_matrix
    from collections import Counter

    labels_arr = np.array(labels)
    # Индекс состояния: T*9 + D*3 + A
    state_indices = labels_arr[:, 0] * 9 + labels_arr[:, 1] * 3 + labels_arr[:, 2]

    # 27-class KNN classification
    clf = KNeighborsClassifier(n_neighbors=min(5, len(labels) - 1))
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        y_pred = cross_val_predict(clf, X, state_indices, cv=5)

    cm = confusion_matrix(state_indices, y_pred, labels=list(range(27)))

    # Нормализуем (строки = true, столбцы = predicted)
    cm_norm = cm.astype(float) / (cm.sum(axis=1, keepdims=True) + 1e-10)

    # Для каждой пары состояний: confusion vs Hamming distance
    hamming_pairs: List[Tuple[int, float]] = []
    confusion_pairs: List[float] = []
    for i in range(27):
        for j in range(27):
            if i == j:
                continue
            # Hamming distance в Z₃³
            t_i, d_i, a_i = i // 9, (i // 3) % 3, i % 3
            t_j, d_j, a_j = j // 9, (j // 3) % 3, j % 3
            hamming = (t_i != t_j) + (d_i != d_j) + (a_i != a_j)
            confusion = cm_norm[i, j]
            hamming_pairs.append((hamming, confusion))

    # Средняя confusion по Hamming distance
    from collections import defaultdict
    by_hamming: Dict[int, List[float]] = defaultdict(list)
    for h, c in hamming_pairs:
        by_hamming[h].append(c)

    hamming_confusion: Dict[str, float] = {}
    for h in sorted(by_hamming.keys()):
        hamming_confusion[f"hamming_{h}"] = round(float(np.mean(by_hamming[h])), 4)

    # Корреляция Hamming vs confusion
    h_vals = [h for h, c in hamming_pairs]
    c_vals = [c for h, c in hamming_pairs]
    correlation = float(np.corrcoef(h_vals, c_vals)[0, 1])

    # Accuracy per state
    per_state_acc: Dict[str, float] = {}
    state_counts = Counter(state_indices)
    for s in range(27):
        if state_counts[s] > 0:
            correct = cm[s, s]
            total = cm[s].sum()
            acc = correct / total if total > 0 else 0
            t, d, a = s // 9, (s // 3) % 3, s % 3
            per_state_acc[f"({t},{d},{a})"] = round(float(acc), 3)

    # Топ-5 лучших и худших состояний
    sorted_states = sorted(per_state_acc.items(), key=lambda x: x[1], reverse=True)
    best_5 = dict(sorted_states[:5])
    worst_5 = dict(sorted_states[-5:])

    return {
        "overall_27class_accuracy": round(float(np.trace(cm) / cm.sum()), 3),
        "hamming_vs_confusion": hamming_confusion,
        "hamming_confusion_correlation": round(correlation, 3),
        "best_states": best_5,
        "worst_states": worst_5,
        "confusion_matrix_diagonal": [round(float(cm_norm[i, i]), 3) for i in range(27)],
    }


# ═══════════════════════════════════════════════════════════════
# PHASE 9: Non-linear subspace
# ═══════════════════════════════════════════════════════════════

def nonlinear_subspace_id(
    X: np.ndarray,
    labels: List[Tuple[int, int, int]],
) -> Dict:
    """MLP probe → извлечь нелинейное C4-подпространство → измерить ID."""
    from sklearn.neural_network import MLPRegressor
    from sklearn.preprocessing import StandardScaler
    from sklearn.model_selection import cross_val_score

    labels_arr = np.array(labels, dtype=float)
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    # Обучаем MLP: 384 → 128 → 64 → 3
    mlp = MLPRegressor(
        hidden_layer_sizes=(128, 64, 3), max_iter=1000,
        random_state=42, early_stopping=True, validation_fraction=0.15,
        activation="relu",
    )
    mlp.fit(X_scaled, labels_arr)

    # Извлечь активации последнего скрытого слоя (3 units = output)
    # В sklearn MLPRegressor доступ к скрытым слоям — через forward pass
    activations = X_scaled
    for i, (w, b) in enumerate(zip(mlp.coefs_, mlp.intercepts_)):
        activations = activations @ w + b
        if i < len(mlp.coefs_) - 1:  # ReLU кроме последнего слоя
            activations = np.maximum(activations, 0)

    # Последний слой (3 units) — нелинейная проекция на C4
    X_nonlinear_3d = activations  # shape: (N, 3)

    # Предпоследний (64 units)
    act_64 = X_scaled
    for i, (w, b) in enumerate(zip(mlp.coefs_[:-1], mlp.intercepts_[:-1])):
        act_64 = act_64 @ w + b
        act_64 = np.maximum(act_64, 0)

    # ID нелинейного 3D подпространства
    id_3d_twonn = id_twonn_euclidean(X_nonlinear_3d)
    id_3d_mle = id_mle(X_nonlinear_3d, k=10)

    # ID 64D скрытого слоя
    id_64d_twonn = id_twonn_euclidean(act_64)

    # R² MLP (на train, для оценки fit quality)
    y_pred = mlp.predict(X_scaled)
    from sklearn.metrics import r2_score
    r2_per_axis: Dict[str, float] = {}
    for ax_idx, ax_name in enumerate(["Time", "Scale", "Agency"]):
        r2 = r2_score(labels_arr[:, ax_idx], y_pred[:, ax_idx])
        r2_per_axis[f"{ax_name}_r2_train"] = round(float(r2), 3)

    return {
        "nonlinear_3d_id_twonn": round(float(id_3d_twonn), 2),
        "nonlinear_3d_id_mle": round(float(id_3d_mle), 2),
        "hidden_64d_id_twonn": round(float(id_64d_twonn), 2),
        **r2_per_axis,
    }


# ═══════════════════════════════════════════════════════════════
# PHASE 10: Multi-LLM annotation (генерация скрипта)
# ═══════════════════════════════════════════════════════════════

def prepare_multi_llm_annotation(
    c4factory_path: str,
    output_dir: Path,
    n_samples: int = 200,
) -> Dict:
    """Подготовить сэмпл текстов и промпт для мульти-LLM аннотации."""
    rng = np.random.default_rng(42)
    texts, labels = load_c4factory_data(c4factory_path, sample_size=n_samples, rng=rng)

    if not texts:
        return {"error": "no data"}

    # Сохранить тексты для аннотации
    output_dir.mkdir(parents=True, exist_ok=True)

    annotation_items = []
    for i, (text, label) in enumerate(zip(texts, labels)):
        annotation_items.append({
            "id": i,
            "text": text,
            "original_label": {"t": label[0], "d": label[1], "a": label[2]},
        })

    with open(output_dir / "texts_for_annotation.jsonl", "w") as f:
        for item in annotation_items:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")

    # Сгенерировать промпт для LLM-аннотаторов
    annotation_prompt = """You are a cognitive science expert annotating text by the C4 coordinate system.

For each text, assign THREE coordinates:
- T (Time): 0=Past, 1=Present, 2=Future — What temporal frame does the text primarily occupy?
- D (Scale): 0=Concrete (specific facts, actions, objects), 1=Abstract (patterns, generalizations), 2=Meta (thinking about thinking, paradigms, epistemology)
- A (Agency): 0=Self (I/my perspective), 1=Other (he/she/they), 2=System (organizations, nature, society as a whole)

Output ONLY valid JSON: {"t": 0-2, "d": 0-2, "a": 0-2}

Examples:
- "I fixed the bug yesterday" → {"t": 0, "d": 0, "a": 0}
- "The economy is entering a recession" → {"t": 1, "d": 1, "a": 2}
- "I am thinking about how I think" → {"t": 1, "d": 2, "a": 0}

Text to annotate:
"""

    with open(output_dir / "annotation_prompt.txt", "w") as f:
        f.write(annotation_prompt)

    # Скрипт для запуска аннотации
    annotation_script = '''#!/usr/bin/env python3
"""
Multi-LLM Annotation Script for ID-3 Experiment.
Annotates texts using multiple LLM providers for inter-rater reliability.

Usage:
    export OPENAI_API_KEY="..."
    export ANTHROPIC_API_KEY="..."
    export DEEPSEEK_API_KEY="..."
    python3 annotate_multi_llm.py
"""
import json, os, time, sys
from pathlib import Path

MODELS = {
    "gpt4o": {"provider": "openai", "model": "gpt-4o", "env": "OPENAI_API_KEY"},
    "claude": {"provider": "anthropic", "model": "claude-sonnet-4-20250514", "env": "ANTHROPIC_API_KEY"},
    "deepseek": {"provider": "openai_compat", "model": "deepseek-chat",
                 "env": "DEEPSEEK_API_KEY", "base_url": "https://api.deepseek.com"},
}

PROMPT = open("annotation_prompt.txt").read()

def annotate_openai(text: str, model: str, api_key: str, base_url: str = None) -> dict:
    from openai import OpenAI
    client = OpenAI(api_key=api_key, base_url=base_url)
    resp = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": PROMPT + text}],
        temperature=0, max_tokens=50,
    )
    return json.loads(resp.choices[0].message.content.strip())

def annotate_anthropic(text: str, model: str, api_key: str) -> dict:
    from anthropic import Anthropic
    client = Anthropic(api_key=api_key)
    resp = client.messages.create(
        model=model,
        max_tokens=50,
        messages=[{"role": "user", "content": PROMPT + text}],
    )
    return json.loads(resp.content[0].text.strip())

def main():
    texts = [json.loads(l) for l in open("texts_for_annotation.jsonl")]
    results = {m: [] for m in MODELS}

    for model_name, cfg in MODELS.items():
        api_key = os.environ.get(cfg["env"])
        if not api_key:
            print(f"SKIP {model_name}: {cfg['env']} not set")
            continue
        print(f"Annotating with {model_name} ({len(texts)} texts)...")
        for item in texts:
            try:
                if cfg["provider"] == "anthropic":
                    label = annotate_anthropic(item["text"], cfg["model"], api_key)
                else:
                    label = annotate_openai(item["text"], cfg["model"], api_key,
                                           cfg.get("base_url"))
                results[model_name].append({"id": item["id"], **label})
                time.sleep(0.5)  # rate limit
            except Exception as e:
                results[model_name].append({"id": item["id"], "error": str(e)})

        with open(f"annotations_{model_name}.jsonl", "w") as f:
            for r in results[model_name]:
                f.write(json.dumps(r, ensure_ascii=False) + "\\n")
        print(f"  Done: {model_name}")

    # Compute agreement
    print("\\nInter-rater agreement:")
    valid_models = [m for m in results if results[m] and "error" not in results[m][0]]
    if len(valid_models) >= 2:
        for axis in ["t", "d", "a"]:
            agreements = []
            for i in range(len(texts)):
                vals = []
                for m in valid_models:
                    if i < len(results[m]) and "error" not in results[m][i]:
                        vals.append(results[m][i].get(axis))
                if len(vals) >= 2:
                    agreements.append(len(set(vals)) == 1)
            pct = sum(agreements) / len(agreements) * 100 if agreements else 0
            print(f"  {axis.upper()}: {pct:.1f}% exact agreement")

if __name__ == "__main__":
    main()
'''

    with open(output_dir / "annotate_multi_llm.py", "w") as f:
        f.write(annotation_script)

    return {
        "n_texts": len(texts),
        "prompt_file": str(output_dir / "annotation_prompt.txt"),
        "data_file": str(output_dir / "texts_for_annotation.jsonl"),
        "script_file": str(output_dir / "annotate_multi_llm.py"),
    }


# ═══════════════════════════════════════════════════════════════
# Единый анализ (улучшенная версия)
# ═══════════════════════════════════════════════════════════════

def run_phase_analysis(
    embeddings: np.ndarray,
    labels: List[Tuple[int, int, int]],
    phase_name: str,
    output_dir: Path,
    n_bootstrap: int = 200,
    n_permutations: int = 300,
) -> Dict:
    """Запустить полный анализ для одной фазы."""
    from sklearn.decomposition import PCA

    rng = np.random.default_rng(42)
    results: Dict = {"phase": phase_name, "n_samples": embeddings.shape[0], "embedding_dim": embeddings.shape[1]}

    print(f"\n{'═' * 70}")
    print(f"  {phase_name}")
    print(f"{'═' * 70}")
    print(f"  Samples: {embeddings.shape[0]}, Embedding dim: {embeddings.shape[1]}")
    print(f"  Unique states: {len(set(labels))}")

    # 1. Point estimates
    print(f"\n  --- Point estimates ---")
    d_twonn_cos = id_twonn(embeddings)
    d_twonn_euc = id_twonn_euclidean(embeddings)
    d_mle5 = id_mle(embeddings, k=5)
    d_mle10 = id_mle(embeddings, k=10)
    d_mle20 = id_mle(embeddings, k=20)
    d_corr = id_correlation(embeddings)

    print(f"  TwoNN (cosine):    {d_twonn_cos:.2f}")
    print(f"  TwoNN (euclidean): {d_twonn_euc:.2f}")
    print(f"  MLE k=5:           {d_mle5:.2f}")
    print(f"  MLE k=10:          {d_mle10:.2f}")
    print(f"  MLE k=20:          {d_mle20:.2f}")
    print(f"  Correlation dim:   {d_corr:.2f}")

    results["twonn_cosine"] = round(d_twonn_cos, 2)
    results["twonn_euclidean"] = round(d_twonn_euc, 2)
    results["mle_k5"] = round(d_mle5, 2)
    results["mle_k10"] = round(d_mle10, 2)
    results["mle_k20"] = round(d_mle20, 2)
    results["correlation_dim"] = round(d_corr, 2)

    valid = [e for e in [d_twonn_euc, d_mle10, d_mle20, d_corr] if not np.isnan(e)]
    results["mean_id"] = round(float(np.mean(valid)), 2) if valid else float("nan")
    results["std_id"] = round(float(np.std(valid)), 2) if len(valid) > 1 else float("nan")

    # 2. Bootstrap mean (правильный тест)
    print(f"\n  --- Bootstrap mean ID (n={n_bootstrap}) ---")
    boot_mean = bootstrap_mean_id(embeddings, n_bootstrap=n_bootstrap, rng=rng)
    print(f"  Mean ID: {boot_mean['mean']:.2f} [{boot_mean['ci_low']:.2f}, {boot_mean['ci_high']:.2f}]")
    print(f"  3.0 in CI: {'YES' if boot_mean.get('three_in_ci') else 'NO'}")
    results["bootstrap_mean"] = boot_mean

    # 3. PCA + eigenvalue gaps
    print(f"\n  --- PCA & eigenvalue gaps ---")
    n_95, var_ratios = id_pca(embeddings, threshold=0.95)
    n_90, _ = id_pca(embeddings, threshold=0.90)
    print(f"  PC for 90% var: {n_90},  for 95%: {n_95}")
    print(f"  Top-3 explain: {sum(var_ratios[:3]):.1%}")

    n_eigen = min(10, embeddings.shape[0], embeddings.shape[1])
    pca_e = PCA(n_components=n_eigen)
    pca_e.fit(embeddings)
    ev = pca_e.explained_variance_
    gaps = {}
    for i in range(min(5, len(ev) - 1)):
        ratio = float(ev[i] / ev[i + 1]) if ev[i + 1] > 1e-10 else float("inf")
        gaps[f"lambda{i+1}_over_lambda{i+2}"] = round(ratio, 3)
    gap_3_4 = gaps.get("lambda3_over_lambda4", float("nan"))
    print(f"  λ₃/λ₄ = {gap_3_4:.3f}")
    results["pca_90"] = n_90
    results["pca_95"] = n_95
    results["pca_top3_var"] = round(float(sum(var_ratios[:3])), 4)
    results["eigenvalue_gaps"] = gaps

    # 4. MI matrix + permutation test
    print(f"\n  --- Axis alignment (MI) ---")
    n_comp = min(3, embeddings.shape[0], embeddings.shape[1])
    pca3 = PCA(n_components=n_comp)
    X3 = pca3.fit_transform(embeddings)
    labels_arr = np.array(labels)

    from sklearn.metrics import mutual_info_score

    mi_matrix: Dict[str, Dict[str, float]] = {}
    for ax_idx, ax_name in enumerate(["Time", "Scale", "Agency"]):
        mi_matrix[ax_name] = {}
        best_mi = 0.0
        best_pc = ""
        for pc_idx in range(n_comp):
            pc_binned = np.digitize(X3[:, pc_idx], bins=np.percentile(X3[:, pc_idx], [33, 67]))
            mi = mutual_info_score(labels_arr[:, ax_idx], pc_binned)
            mi_matrix[ax_name][f"PC{pc_idx+1}"] = round(mi, 3)
            if mi > best_mi:
                best_mi = mi
                best_pc = f"PC{pc_idx+1}"
        print(f"  {ax_name} best → {best_pc}: MI={best_mi:.3f}")
    results["mi_matrix"] = mi_matrix

    print(f"\n  --- Permutation test (n={n_permutations}) ---")
    perm = permutation_test(embeddings, labels, n_permutations=n_permutations, rng=rng)
    print(f"  p-value: {perm['p_value']:.4f} {'✓ significant' if perm['significant'] else '✗ not significant'}")
    results["permutation_test"] = perm

    # 5. Classification accuracy
    print(f"\n  --- Classification (KNN on PC1-3) ---")
    clf = classification_accuracy(embeddings, labels, n_components=3)
    for ax in ["Time", "Scale", "Agency"]:
        acc = clf.get(f"{ax}_accuracy", float("nan"))
        print(f"  {ax}: {acc:.1%} (chance: {clf['chance_level']:.1%})")
    results["classification"] = clf

    # 6. Supervised subspace (PHASE 4 KEY TEST)
    print(f"\n  --- Supervised subspace ID ---")
    sup = supervised_subspace_id(embeddings, labels)
    print(f"  C4 subspace ID (TwoNN): {sup['c4_subspace_id_twonn']:.2f}")
    print(f"  C4 subspace ID (MLE):   {sup['c4_subspace_id_mle']:.2f}")
    print(f"  Residual ID (TwoNN):    {sup['residual_id_twonn']:.2f}")
    print(f"  C4 variance explained:  {sup['c4_variance_explained']:.2%}")
    for ax in ["Time", "Scale", "Agency"]:
        r2 = sup.get(f"{ax}_r2", float("nan"))
        print(f"  {ax} R²: {r2:.3f}")
    results["supervised_subspace"] = sup

    # 7. Random baseline
    baseline = random_baseline_comparison(embeddings, rng=rng)
    print(f"\n  --- Random baseline ---")
    print(f"  Real ID: {baseline['real_id']:.2f}, Random: {baseline['random_mean_id']:.2f}")
    results["random_baseline"] = baseline

    # Сохранение
    output_dir.mkdir(parents=True, exist_ok=True)
    safe_name = phase_name.replace(" ", "_").replace(":", "").replace("/", "_").lower()
    with open(output_dir / f"{safe_name}.json", "w") as f:
        json.dump(results, f, indent=2, ensure_ascii=False, default=str)

    return results


# ═══════════════════════════════════════════════════════════════
# MAIN: Orchestrator всех фаз
# ═══════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(description="ID-3 Full 10-Phase Experiment")
    parser.add_argument("--c4factory", default="/Users/figuramax/LocalProjects/prjcts/fleets/c4factory",
                       help="Path to c4factory directory")
    parser.add_argument("--output", default="/Users/figuramax/LocalProjects/adaptive-topology/code/python/id3_results/full_experiment",
                       help="Output directory")
    parser.add_argument("--model", default="all-MiniLM-L6-v2", help="Default embedding model")
    parser.add_argument("--sample-size", type=int, default=2000, help="Sample size for c4factory data")
    parser.add_argument("--phase", type=int, default=None, help="Run only this phase (0-10)")
    parser.add_argument("--bootstrap", type=int, default=200, help="Bootstrap iterations")
    parser.add_argument("--permutations", type=int, default=300, help="Permutation test iterations")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    args = parser.parse_args()

    np.random.seed(args.seed)
    rng = np.random.default_rng(args.seed)
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    all_results: Dict[str, Dict] = {}
    phases_to_run = [args.phase] if args.phase is not None else list(range(11))

    start_time = time.time()

    # ─── PHASE 0: Baseline с фиксами ─────────────────────────
    if 0 in phases_to_run:
        print("\n" + "█" * 70)
        print("  PHASE 0: BASELINE (built-in 135 texts, fixed estimators)")
        print("█" * 70)

        texts, labels = get_all_texts_and_labels()
        embeddings = embed_texts(texts, args.model)
        results = run_phase_analysis(
            embeddings, labels, "Phase 0: Baseline (135 built-in)",
            output_dir / "phase0", n_bootstrap=args.bootstrap, n_permutations=args.permutations,
        )
        all_results["phase0"] = results

    # ─── PHASE 1: Multi-model ─────────────────────────────────
    if 1 in phases_to_run:
        print("\n" + "█" * 70)
        print("  PHASE 1: MULTI-MODEL ROBUSTNESS")
        print("█" * 70)

        texts, labels = get_all_texts_and_labels()
        models = [
            "all-MiniLM-L6-v2",
            "all-mpnet-base-v2",
            "paraphrase-multilingual-MiniLM-L12-v2",
        ]

        phase1_results: Dict[str, Dict] = {}
        for model_name in models:
            print(f"\n  Model: {model_name}")
            try:
                emb = embed_texts(texts, model_name)
                res = run_phase_analysis(
                    emb, labels, f"Phase 1: {model_name}",
                    output_dir / "phase1" / model_name.replace("/", "_"),
                    n_bootstrap=100, n_permutations=200,
                )
                phase1_results[model_name] = res
            except Exception as e:
                print(f"  ERROR: {e}")
                phase1_results[model_name] = {"error": str(e)}

        # Сводка
        print(f"\n  {'─' * 60}")
        print(f"  PHASE 1 SUMMARY: Multi-model comparison")
        print(f"  {'─' * 60}")
        print(f"  {'Model':<40} {'Mean ID':>8} {'Sub ID':>8} {'Perm p':>8}")
        for m, r in phase1_results.items():
            if "error" not in r:
                mid = r.get("mean_id", "?")
                sid = r.get("supervised_subspace", {}).get("c4_subspace_id_twonn", "?")
                pp = r.get("permutation_test", {}).get("p_value", "?")
                print(f"  {m:<40} {mid:>8} {sid:>8} {pp:>8}")

        all_results["phase1"] = phase1_results

    # ─── PHASE 2: Controlled dataset ──────────────────────────
    if 2 in phases_to_run:
        print("\n" + "█" * 70)
        print("  PHASE 2: CONTROLLED TEMPLATE DATASET")
        print("█" * 70)

        texts, labels = get_controlled_texts_and_labels()
        print(f"  Generated {len(texts)} controlled texts across {len(set(labels))} states")
        embeddings = embed_texts(texts, args.model)
        results = run_phase_analysis(
            embeddings, labels, "Phase 2: Controlled templates",
            output_dir / "phase2", n_bootstrap=args.bootstrap, n_permutations=args.permutations,
        )
        all_results["phase2"] = results

    # ─── PHASE 3: c4factory large-scale ───────────────────────
    if 3 in phases_to_run:
        print("\n" + "█" * 70)
        print(f"  PHASE 3: C4FACTORY LARGE-SCALE ({args.sample_size} samples)")
        print("█" * 70)

        texts, labels = load_c4factory_data(args.c4factory, sample_size=args.sample_size, rng=rng)
        if texts:
            print(f"  Loaded {len(texts)} texts from c4factory")
            embeddings = embed_texts(texts, args.model)
            results = run_phase_analysis(
                embeddings, labels, f"Phase 3: c4factory (n={len(texts)})",
                output_dir / "phase3", n_bootstrap=args.bootstrap, n_permutations=args.permutations,
            )
            all_results["phase3"] = results
        else:
            print("  SKIPPED: no data loaded")

    # ─── PHASE 4: Supervised subspace (уже встроен в run_phase_analysis) ──
    if 4 in phases_to_run and "phase3" not in all_results:
        print("\n" + "█" * 70)
        print("  PHASE 4: SUPERVISED SUBSPACE (on c4factory data)")
        print("█" * 70)

        texts, labels = load_c4factory_data(args.c4factory, sample_size=args.sample_size, rng=rng)
        if texts:
            embeddings = embed_texts(texts, args.model)
            results = run_phase_analysis(
                embeddings, labels, "Phase 4: Supervised subspace",
                output_dir / "phase4", n_bootstrap=args.bootstrap, n_permutations=args.permutations,
            )
            all_results["phase4"] = results

    # ─── PHASE 5: Cross-linguistic ────────────────────────────
    if 5 in phases_to_run:
        print("\n" + "█" * 70)
        print("  PHASE 5: CROSS-LINGUISTIC (EN vs RU)")
        print("█" * 70)

        multi_model = "paraphrase-multilingual-MiniLM-L12-v2"
        phase5_results: Dict[str, Dict] = {}

        for lang_code, lang_name in [("en", "English"), ("ru", "Russian")]:
            print(f"\n  Language: {lang_name}")
            texts, labels = load_c4factory_data(
                args.c4factory, sample_size=args.sample_size, lang=lang_code, rng=rng,
            )
            if texts:
                print(f"  Loaded {len(texts)} {lang_name} texts")
                embeddings = embed_texts(texts, multi_model)
                results = run_phase_analysis(
                    embeddings, labels, f"Phase 5: {lang_name}",
                    output_dir / "phase5" / lang_code,
                    n_bootstrap=args.bootstrap, n_permutations=args.permutations,
                )
                phase5_results[lang_code] = results
            else:
                print(f"  SKIPPED: no {lang_name} data")

        # Кросслингвистическое сравнение
        if "en" in phase5_results and "ru" in phase5_results:
            print(f"\n  {'─' * 60}")
            print(f"  PHASE 5 SUMMARY: Cross-linguistic axis salience")
            print(f"  {'─' * 60}")
            print(f"  {'Axis':<10} {'EN MI best':>12} {'RU MI best':>12} {'Prediction':>15}")
            for ax in ["Time", "Scale", "Agency"]:
                en_mi = max(phase5_results["en"].get("mi_matrix", {}).get(ax, {}).values(), default=0)
                ru_mi = max(phase5_results["ru"].get("mi_matrix", {}).get(ax, {}).values(), default=0)
                pred = "RU > EN" if ax == "Time" else "≈ equal"
                marker = "✓" if (ax == "Time" and ru_mi > en_mi) or ax != "Time" else "✗"
                print(f"  {ax:<10} {en_mi:>12.3f} {ru_mi:>12.3f} {pred:>15} {marker}")

        all_results["phase5"] = phase5_results

    # ─── PHASE 6: Time axis diagnosis ────────────────────────
    if 6 in phases_to_run:
        print("\n" + "█" * 70)
        print("  PHASE 6: TIME AXIS DIAGNOSIS (linear vs non-linear probes)")
        print("█" * 70)

        # Используем c4factory данные для достаточного объёма
        texts, labels = load_c4factory_data(args.c4factory, sample_size=args.sample_size, rng=rng)
        if texts:
            embeddings = embed_texts(texts, args.model)
            diag = diagnose_time_axis(embeddings, labels)
            print(f"\n  {'Axis':<10} {'Ridge R²':>10} {'MLP R²':>10} {'NL gain':>10} {'Fisher':>10}")
            for ax in ["Time", "Scale", "Agency"]:
                r2_l = diag.get(f"{ax}_ridge_r2", float("nan"))
                r2_m = diag.get(f"{ax}_mlp_r2", float("nan"))
                nlg = diag.get(f"{ax}_nonlinear_gain", float("nan"))
                fish = diag.get(f"{ax}_fisher_ratio", float("nan"))
                print(f"  {ax:<10} {r2_l:>10.3f} {r2_m:>10.3f} {nlg:>10.3f} {fish:>10.4f}")

            # Сохранение
            phase6_dir = output_dir / "phase6"
            phase6_dir.mkdir(parents=True, exist_ok=True)
            with open(phase6_dir / "time_diagnosis.json", "w") as f:
                json.dump(diag, f, indent=2, ensure_ascii=False, default=str)
            all_results["phase6"] = diag
        else:
            print("  SKIPPED: no data loaded")

    # ─── PHASE 7: Scaling analysis ───────────────────────────
    if 7 in phases_to_run:
        print("\n" + "█" * 70)
        print("  PHASE 7: SCALING ANALYSIS (ID vs N convergence)")
        print("█" * 70)

        scaling = scaling_analysis(args.c4factory, args.model)
        print(f"\n  Convergence table:")
        print(f"  {'N':>6} {'Sub ID':>8} {'CI low':>8} {'CI high':>8} {'Full ID':>8} {'Perm p':>8}")
        for i, n in enumerate(scaling["N"]):
            sid = scaling["subspace_id_twonn"][i]
            cil = scaling["subspace_id_ci_low"][i]
            cih = scaling["subspace_id_ci_high"][i]
            fid = scaling["full_id"][i]
            pp = scaling["perm_p"][i]
            print(f"  {n:>6} {sid:>8.2f} {cil:>8.2f} {cih:>8.2f} {fid:>8.2f} {pp:>8.4f}")

        # Сохранение
        phase7_dir = output_dir / "phase7"
        phase7_dir.mkdir(parents=True, exist_ok=True)
        with open(phase7_dir / "scaling_analysis.json", "w") as f:
            json.dump(scaling, f, indent=2, ensure_ascii=False, default=str)
        all_results["phase7"] = scaling

    # ─── PHASE 8: Per-state topology ─────────────────────────
    if 8 in phases_to_run:
        print("\n" + "█" * 70)
        print("  PHASE 8: PER-STATE TOPOLOGY (27-class confusion vs Hamming)")
        print("█" * 70)

        texts, labels = load_c4factory_data(args.c4factory, sample_size=args.sample_size, rng=rng)
        if texts:
            embeddings = embed_texts(texts, args.model)
            topo = per_state_topology(embeddings, labels)
            print(f"\n  27-class accuracy: {topo['overall_27class_accuracy']:.1%}")
            print(f"  Hamming ↔ confusion correlation: {topo['hamming_confusion_correlation']:.3f}")
            print(f"\n  Confusion by Hamming distance:")
            for k, v in topo["hamming_vs_confusion"].items():
                print(f"    {k}: {v:.4f}")
            print(f"\n  Best 5 states: {topo['best_states']}")
            print(f"  Worst 5 states: {topo['worst_states']}")

            phase8_dir = output_dir / "phase8"
            phase8_dir.mkdir(parents=True, exist_ok=True)
            with open(phase8_dir / "per_state_topology.json", "w") as f:
                json.dump(topo, f, indent=2, ensure_ascii=False, default=str)
            all_results["phase8"] = topo
        else:
            print("  SKIPPED: no data loaded")

    # ─── PHASE 9: Non-linear subspace ────────────────────────
    if 9 in phases_to_run:
        print("\n" + "█" * 70)
        print("  PHASE 9: NON-LINEAR SUBSPACE ID (MLP probe)")
        print("█" * 70)

        texts, labels = load_c4factory_data(args.c4factory, sample_size=args.sample_size, rng=rng)
        if texts:
            embeddings = embed_texts(texts, args.model)
            nl = nonlinear_subspace_id(embeddings, labels)
            print(f"\n  Non-linear 3D ID (TwoNN):  {nl['nonlinear_3d_id_twonn']:.2f}")
            print(f"  Non-linear 3D ID (MLE):    {nl['nonlinear_3d_id_mle']:.2f}")
            print(f"  Hidden 64D ID (TwoNN):     {nl['hidden_64d_id_twonn']:.2f}")
            for ax in ["Time", "Scale", "Agency"]:
                r2 = nl.get(f"{ax}_r2_train", float("nan"))
                print(f"  {ax} R² (train): {r2:.3f}")

            phase9_dir = output_dir / "phase9"
            phase9_dir.mkdir(parents=True, exist_ok=True)
            with open(phase9_dir / "nonlinear_subspace.json", "w") as f:
                json.dump(nl, f, indent=2, ensure_ascii=False, default=str)
            all_results["phase9"] = nl
        else:
            print("  SKIPPED: no data loaded")

    # ─── PHASE 10: Multi-LLM annotation prep ────────────────
    if 10 in phases_to_run:
        print("\n" + "█" * 70)
        print("  PHASE 10: MULTI-LLM ANNOTATION PREPARATION")
        print("█" * 70)

        phase10_dir = output_dir / "phase10"
        annot = prepare_multi_llm_annotation(args.c4factory, phase10_dir, n_samples=200)
        if "error" not in annot:
            print(f"  Prepared {annot['n_texts']} texts for annotation")
            print(f"  Prompt: {annot['prompt_file']}")
            print(f"  Data:   {annot['data_file']}")
            print(f"  Script: {annot['script_file']}")
        else:
            print(f"  ERROR: {annot['error']}")
        all_results["phase10"] = annot

    # ═══════════════════════════════════════════════════════════
    # GRAND SUMMARY
    # ═══════════════════════════════════════════════════════════
    elapsed = time.time() - start_time
    print("\n" + "═" * 70)
    print("  GRAND SUMMARY: ALL PHASES")
    print("═" * 70)

    summary_table: List[Dict] = []
    for phase_key, phase_data in all_results.items():
        if isinstance(phase_data, dict) and "mean_id" in phase_data:
            row = {
                "phase": phase_data.get("phase", phase_key),
                "n": phase_data.get("n_samples", "?"),
                "mean_id": phase_data.get("mean_id", "?"),
                "subspace_id": phase_data.get("supervised_subspace", {}).get("c4_subspace_id_twonn", "?"),
                "perm_p": phase_data.get("permutation_test", {}).get("p_value", "?"),
                "c4_var": phase_data.get("supervised_subspace", {}).get("c4_variance_explained", "?"),
            }
            summary_table.append(row)
            print(f"  {row['phase']}")
            print(f"    Mean ID: {row['mean_id']}, Subspace ID: {row['subspace_id']}, "
                  f"Perm p: {row['perm_p']}, C4 var: {row['c4_var']}")

    # Сохранение итогов
    with open(output_dir / "grand_summary.json", "w") as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False, default=str)

    print(f"\n  Total time: {elapsed:.0f}s")
    print(f"  Results saved to: {output_dir}")
    print("═" * 70)

    return all_results


if __name__ == "__main__":
    main()
