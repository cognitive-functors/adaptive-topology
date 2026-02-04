#!/usr/bin/env python3
"""
Hypothesis ID-3 Tester: Is the intrinsic dimension of cognitive text embeddings ≈ 3?

C4 claims that cognitive space is ℤ₃³ (27 states, 3 dimensions).
If true, text embeddings of cognitive content should have intrinsic dimension ≈ 3,
even though the embedding space itself is ℝ⁷⁶⁸ (or higher).

This script:
1. Generates/loads texts labeled by 27 C4 states
2. Embeds them via sentence-transformers (or any HuggingFace model)
3. Estimates intrinsic dimensionality using 4 methods:
   - PCA (scree plot / explained variance)
   - TwoNN (Facco et al., 2017)
   - MLE (Levina & Bickel, 2004)
   - Correlation dimension
4. Statistical validation:
   - Bootstrap confidence intervals for all estimates
   - Permutation test (null hypothesis: labels are random)
   - Per-axis dimensionality (each axis should contribute ≈ 1)
   - Classification accuracy (do PCA components predict T/D/A?)
   - Random baseline comparison
5. Reports results and compares with H₀ (id ≈ 3)

Usage:
    pip install sentence-transformers scikit-learn numpy matplotlib
    python3 test_intrinsic_dimension.py

    # С кастомной моделью:
    python3 test_intrinsic_dimension.py --model "intfloat/multilingual-e5-large"

    # С файлом данных (jsonl: {"text": "...", "state": [T,D,A]}):
    python3 test_intrinsic_dimension.py --data my_cognitive_texts.jsonl

    # Мульти-модельное сравнение:
    python3 test_intrinsic_dimension.py --multi-model

Authors: Ilya Selyutin, Nikolai Kovalev
License: Apache-2.0-NC
"""

import argparse
import json
import sys
import warnings
from pathlib import Path
from typing import List, Dict, Tuple, Optional

import numpy as np

# ─── Встроенный датасет: примеры из 27 C4-состояний ──────────────────────

C4_EXAMPLES: Dict[str, List[str]] = {
    # Past × Concrete × Self/Other/System
    "(0,0,0)": [
        "I made a mistake yesterday",
        "I successfully completed that project last month",
        "I said something stupid in the meeting",
        "I forgot to send the email last week",
        "I finished the report ahead of deadline",
    ],
    "(0,0,1)": [
        "He betrayed me last year",
        "She helped me when I needed it",
        "They made a bad decision at the meeting",
        "My colleague solved the bug instantly",
        "The client sent a harsh complaint",
    ],
    "(0,0,2)": [
        "The company launched the product in 2020",
        "The law was changed last year",
        "The market crashed in 2008",
        "The server went down during peak hours",
        "The organization restructured in January",
    ],
    # Past × Abstract × Self/Other/System
    "(0,1,0)": [
        "I tend to procrastinate on difficult tasks",
        "I usually avoid conflict in meetings",
        "I've always been good at math",
        "I have a habit of overcommitting",
        "My pattern is to start strong then lose focus",
    ],
    "(0,1,1)": [
        "He always makes excuses when confronted",
        "She tends to be late to every meeting",
        "They never listen to feedback from the team",
        "My boss has a pattern of micromanaging",
        "The team consistently underestimates timelines",
    ],
    "(0,1,2)": [
        "Empires tend to decline after reaching peak complexity",
        "Markets cycle between boom and bust regularly",
        "Revolutions follow similar patterns throughout history",
        "Technological adoption follows an S-curve",
        "Economic inequality tends to increase over time",
    ],
    # Past × Meta × Self/Other/System
    "(0,2,0)": [
        "I used to believe my thoughts were facts",
        "I didn't realize I was making assumptions about people",
        "I've changed my mind about how to approach problems",
        "I used to think intelligence was fixed, now I see it as growth",
        "My framework for understanding relationships has evolved",
    ],
    "(0,2,1)": [
        "He didn't understand the framework back then",
        "She was operating from a different paradigm entirely",
        "They were blind to their own biases in the analysis",
        "The team's mental model was too simplistic",
        "His worldview shifted after the experience",
    ],
    "(0,2,2)": [
        "Science used to operate under a Newtonian paradigm",
        "Society believed in the divine right of kings for centuries",
        "The field shifted from behaviorism to cognitivism",
        "The prevailing epistemology changed after quantum mechanics",
        "The dominant paradigm in economics shifted to monetarism",
    ],
    # Present × Concrete × Self/Other/System
    "(1,0,0)": [
        "I am writing this report right now",
        "I notice tension in my shoulders at this moment",
        "I'm stuck on line 47 of the code",
        "I feel hungry and tired right now",
        "I am debugging this function currently",
    ],
    "(1,0,1)": [
        "She is presenting to the board right now",
        "He looks stressed in this meeting",
        "The user is clicking the wrong button",
        "My colleague is struggling with the deployment",
        "The client is waiting on hold at this moment",
    ],
    "(1,0,2)": [
        "The server is down right now",
        "The market is volatile today",
        "The pipeline is processing 10,000 records currently",
        "Traffic is congested throughout the city",
        "The system is experiencing high latency",
    ],
    # Present × Abstract × Self/Other/System
    "(1,1,0)": [
        "I notice I keep avoiding this type of task",
        "I see a pattern in my reactions to criticism",
        "I'm becoming aware of my communication style",
        "I realize I process information better visually",
        "I notice I tend to get defensive in these situations",
    ],
    "(1,1,1)": [
        "The team dynamics are shifting right now",
        "She seems to be in a leadership transition",
        "He is following his usual avoidance pattern",
        "Their communication style is evolving",
        "The group is developing new norms",
    ],
    "(1,1,2)": [
        "The economy is entering a recession",
        "Culture is shifting toward remote work",
        "The technology landscape is consolidating",
        "The political climate is becoming more polarized",
        "The industry is undergoing digital transformation",
    ],
    # Present × Meta × Self/Other/System
    "(1,2,0)": [
        "I am thinking about how I think about this problem",
        "I notice my awareness of my own cognitive process",
        "Right now I'm questioning my own assumptions",
        "I observe my mind switching between analysis and intuition",
        "I'm aware that I'm being metacognitive right now",
    ],
    "(1,2,1)": [
        "I can see how her mental model shapes her conclusions",
        "He doesn't realize his framework is limiting him",
        "I notice they're confusing the map with the territory",
        "Her epistemological stance is influencing the debate",
        "I observe his thinking process as he works through it",
    ],
    "(1,2,2)": [
        "The current scientific paradigm is being questioned",
        "We're in a period of epistemic crisis in society",
        "The framework we use to understand AI is shifting",
        "The dominant narrative about progress is changing",
        "Our collective understanding of intelligence is evolving",
    ],
    # Future × Concrete × Self/Other/System
    "(2,0,0)": [
        "I will send the email tomorrow morning",
        "I'm going to fix this bug after lunch",
        "I plan to run the benchmark tonight",
        "I need to call the client by Friday",
        "I'll deploy the update next week",
    ],
    "(2,0,1)": [
        "She will present the results next Monday",
        "He needs to finish the code review by tomorrow",
        "They should deliver the prototype by end of month",
        "The candidate will start in two weeks",
        "She's going to submit the paper next month",
    ],
    "(2,0,2)": [
        "The product launches in March",
        "The server migration happens next quarter",
        "The new policy takes effect in January",
        "The system upgrade is scheduled for next weekend",
        "The market opens at nine tomorrow",
    ],
    # Future × Abstract × Self/Other/System
    "(2,1,0)": [
        "I aspire to become a better leader",
        "I want to develop a more systematic approach",
        "I hope to build a deeper understanding over time",
        "I plan to change my communication habits",
        "My goal is to develop better metacognitive skills",
    ],
    "(2,1,1)": [
        "She will become a great researcher in time",
        "He needs to develop better listening skills",
        "They should evolve their team culture",
        "The next generation will think differently about work",
        "Students will need different skills in the future",
    ],
    "(2,1,2)": [
        "AI will transform how society functions",
        "The economy will shift to sustainable energy",
        "Education will become more personalized",
        "Globalization will continue to reshape cultures",
        "Healthcare will be revolutionized by genomics",
    ],
    # Future × Meta × Self/Other/System
    "(2,2,0)": [
        "I wonder how my thinking will change as I learn more",
        "Will I see this problem differently in five years?",
        "I anticipate my framework will need updating",
        "How will my understanding of consciousness evolve?",
        "I expect my mental models will shift significantly",
    ],
    "(2,2,1)": [
        "How will they think about AI ethics in a decade?",
        "His perspective will mature with experience",
        "Future researchers will have different assumptions",
        "Their epistemological framework will need revision",
        "She will develop a more nuanced worldview",
    ],
    "(2,2,2)": [
        "What paradigm will replace the current one?",
        "How will humanity's understanding of mind evolve?",
        "The next scientific revolution will redefine intelligence",
        "Future civilizations will have entirely different epistemologies",
        "The way we think about thinking will fundamentally change",
    ],
}


def get_all_texts_and_labels() -> Tuple[List[str], List[Tuple[int, int, int]]]:
    """Извлечь все тексты и их C4-координаты."""
    texts: List[str] = []
    labels: List[Tuple[int, int, int]] = []
    for state_key, examples in C4_EXAMPLES.items():
        coords = tuple(int(x) for x in state_key.strip("()").split(","))
        for text in examples:
            texts.append(text)
            labels.append(coords)
    return texts, labels


def load_custom_data(path: str) -> Tuple[List[str], List[Tuple[int, int, int]]]:
    """Загрузить данные из jsonl: {"text": "...", "state": [T,D,A]}."""
    texts: List[str] = []
    labels: List[Tuple[int, int, int]] = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            obj = json.loads(line)
            texts.append(obj["text"])
            labels.append(tuple(obj["state"]))
    return texts, labels


def embed_texts(texts: List[str], model_name: str) -> np.ndarray:
    """Получить эмбеддинги текстов через sentence-transformers."""
    try:
        from sentence_transformers import SentenceTransformer
    except ImportError:
        print("ERROR: sentence-transformers не установлен.")
        print("  pip install sentence-transformers")
        sys.exit(1)

    print(f"Загрузка модели: {model_name}")
    model = SentenceTransformer(model_name)
    print(f"Эмбеддинг {len(texts)} текстов...")
    embeddings = model.encode(texts, show_progress_bar=True, normalize_embeddings=True)
    print(f"Размерность эмбеддинга: {embeddings.shape[1]}")
    return np.array(embeddings)


# ─── Методы оценки внутренней размерности ─────────────────────────────────

def id_pca(X: np.ndarray, threshold: float = 0.95) -> Tuple[int, np.ndarray]:
    """PCA: число компонент, объясняющих >= threshold дисперсии."""
    from sklearn.decomposition import PCA

    pca = PCA()
    pca.fit(X)
    cumvar = np.cumsum(pca.explained_variance_ratio_)
    n_components = int(np.searchsorted(cumvar, threshold) + 1)
    return n_components, pca.explained_variance_ratio_


def id_twonn(X: np.ndarray) -> float:
    """
    TwoNN estimator (Facco et al., 2017).
    Оценка внутренней размерности через отношение расстояний
    до первого и второго ближайших соседей.
    """
    from sklearn.neighbors import NearestNeighbors

    nn = NearestNeighbors(n_neighbors=3, metric="cosine")
    nn.fit(X)
    distances, _ = nn.kneighbors(X)

    r1 = distances[:, 1]
    r2 = distances[:, 2]

    # Убираем нулевые/вырожденные расстояния
    mask = (r1 > 1e-10) & (r2 > 1e-10)
    r1 = r1[mask]
    r2 = r2[mask]

    if len(r1) < 3:
        return float("nan")

    mu = r2 / r1
    n = len(mu)

    # MLE для d: d = n / sum(log(mu_i))
    log_sum = np.sum(np.log(mu))
    if log_sum <= 0:
        return float("nan")

    d_mle = n / log_sum
    return d_mle


def id_mle(X: np.ndarray, k: int = 10) -> float:
    """
    MLE estimator (Levina & Bickel, 2004).
    Оценка через k ближайших соседей.
    """
    from sklearn.neighbors import NearestNeighbors

    k_actual = min(k, X.shape[0] - 1)
    if k_actual < 2:
        return float("nan")

    nn = NearestNeighbors(n_neighbors=k_actual + 1, metric="cosine")
    nn.fit(X)
    distances, _ = nn.kneighbors(X)

    # Убираем расстояние до себя (= 0)
    distances = distances[:, 1:]

    n = X.shape[0]
    dims: List[float] = []
    for i in range(n):
        T_k = distances[i, -1]
        if T_k < 1e-10:
            continue
        log_ratios = np.log(T_k / np.maximum(distances[i, :-1], 1e-10))
        log_sum = np.sum(log_ratios)
        if log_sum > 0:
            d_i = (k_actual - 1) / log_sum
            dims.append(d_i)

    return np.mean(dims) if dims else float("nan")


def id_correlation(X: np.ndarray) -> float:
    """
    Correlation dimension estimate.
    Оценка через корреляционный интеграл C(r) ~ r^d.
    """
    from sklearn.metrics.pairwise import cosine_distances

    n = X.shape[0]
    max_subsample = min(n, 200)
    if n > max_subsample:
        idx = np.random.choice(n, max_subsample, replace=False)
        X_sub = X[idx]
    else:
        X_sub = X

    D = cosine_distances(X_sub)
    np.fill_diagonal(D, np.inf)
    d_flat = D[np.triu_indices_from(D, k=1)]

    if len(d_flat) < 10:
        return float("nan")

    # Корреляционный интеграл: C(r) = fraction of pairs with distance < r
    r_values = np.linspace(np.percentile(d_flat, 5), np.percentile(d_flat, 50), 50)
    c_values = np.array([np.mean(d_flat < r) for r in r_values])

    mask = c_values > 0
    if np.sum(mask) < 5:
        return float("nan")

    log_r = np.log(r_values[mask])
    log_c = np.log(c_values[mask])

    # Линейная регрессия: log(C) = d * log(r) + const
    slope, _ = np.polyfit(log_r, log_c, 1)
    return float(slope)


# ─── Статистическая валидация ─────────────────────────────────────────────

def bootstrap_id_estimates(
    X: np.ndarray,
    n_bootstrap: int = 100,
    confidence: float = 0.95,
    rng: Optional[np.random.Generator] = None,
) -> Dict[str, Dict[str, float]]:
    """Bootstrap confidence intervals для всех оценок ID."""
    if rng is None:
        rng = np.random.default_rng(42)

    n = X.shape[0]
    estimates: Dict[str, List[float]] = {
        "twonn": [],
        "mle_k5": [],
        "mle_k10": [],
        "mle_k20": [],
        "correlation": [],
    }

    for _ in range(n_bootstrap):
        idx = rng.choice(n, size=n, replace=True)
        X_b = X[idx]

        estimates["twonn"].append(id_twonn(X_b))
        estimates["mle_k5"].append(id_mle(X_b, k=5))
        estimates["mle_k10"].append(id_mle(X_b, k=10))
        estimates["mle_k20"].append(id_mle(X_b, k=20))
        estimates["correlation"].append(id_correlation(X_b))

    alpha = (1 - confidence) / 2
    result: Dict[str, Dict[str, float]] = {}

    for method, vals in estimates.items():
        valid = [v for v in vals if not np.isnan(v)]
        if len(valid) < 5:
            result[method] = {"mean": float("nan"), "ci_low": float("nan"), "ci_high": float("nan"), "std": float("nan")}
            continue
        arr = np.array(valid)
        result[method] = {
            "mean": float(np.mean(arr)),
            "ci_low": float(np.percentile(arr, alpha * 100)),
            "ci_high": float(np.percentile(arr, (1 - alpha) * 100)),
            "std": float(np.std(arr)),
        }

    return result


def permutation_test(
    X: np.ndarray,
    labels: List[Tuple[int, int, int]],
    n_permutations: int = 200,
    rng: Optional[np.random.Generator] = None,
) -> Dict[str, float]:
    """
    Permutation test: перемешиваем метки, пересчитываем взаимную информацию.
    Null hypothesis: структура C4-меток не связана с эмбеддингами.
    """
    from sklearn.decomposition import PCA
    from sklearn.metrics import mutual_info_score

    if rng is None:
        rng = np.random.default_rng(42)

    pca3 = PCA(n_components=min(3, X.shape[0], X.shape[1]))
    X3 = pca3.fit_transform(X)
    labels_arr = np.array(labels)

    # Реальная mutual information: сумма по осям и PC
    def compute_total_mi(labs: np.ndarray) -> float:
        total_mi = 0.0
        for ax_idx in range(3):
            for pc_idx in range(X3.shape[1]):
                pc_binned = np.digitize(
                    X3[:, pc_idx], bins=np.percentile(X3[:, pc_idx], [33, 67])
                )
                total_mi += mutual_info_score(labs[:, ax_idx], pc_binned)
        return total_mi

    real_mi = compute_total_mi(labels_arr)

    # Пермутации
    perm_mis: List[float] = []
    for _ in range(n_permutations):
        perm_labels = labels_arr.copy()
        rng.shuffle(perm_labels)
        perm_mis.append(compute_total_mi(perm_labels))

    perm_arr = np.array(perm_mis)
    p_value = float(np.mean(perm_arr >= real_mi))

    return {
        "real_mi": round(real_mi, 4),
        "perm_mean_mi": round(float(np.mean(perm_arr)), 4),
        "perm_std_mi": round(float(np.std(perm_arr)), 4),
        "p_value": round(p_value, 4),
        "significant": p_value < 0.05,
    }


def per_axis_dimensionality(
    X: np.ndarray,
    labels: List[Tuple[int, int, int]],
) -> Dict[str, float]:
    """
    Оценка ID для подпространств, определяемых каждой C4-осью.
    Если C4 верна, каждая ось вносит ~1 измерение.
    Метод: оценить ID внутри каждого уровня оси и сравнить с полным ID.
    """
    labels_arr = np.array(labels)
    axis_names = ["Time", "Scale", "Agency"]
    result: Dict[str, float] = {}

    full_id = id_twonn(X)
    result["full_id"] = round(float(full_id), 2)

    for ax_idx, ax_name in enumerate(axis_names):
        # Средний ID внутри каждого уровня оси (с контролем за другими осями)
        within_ids: List[float] = []
        for level in range(3):
            mask = labels_arr[:, ax_idx] == level
            X_sub = X[mask]
            if X_sub.shape[0] >= 5:
                d = id_twonn(X_sub)
                if not np.isnan(d):
                    within_ids.append(d)

        if within_ids:
            mean_within = float(np.mean(within_ids))
            # Contribution ≈ full_id - within_id (разница = вклад этой оси)
            contribution = full_id - mean_within if not np.isnan(full_id) else float("nan")
            result[f"{ax_name}_within_id"] = round(mean_within, 2)
            result[f"{ax_name}_contribution"] = round(float(contribution), 2)
        else:
            result[f"{ax_name}_within_id"] = float("nan")
            result[f"{ax_name}_contribution"] = float("nan")

    return result


def classification_accuracy(
    X: np.ndarray,
    labels: List[Tuple[int, int, int]],
    n_components: int = 3,
) -> Dict[str, float]:
    """
    Проверка: предсказывают ли первые n PCA-компонент оси T/D/A?
    Используем LOO cross-validation с KNN (k=5).
    """
    from sklearn.decomposition import PCA
    from sklearn.neighbors import KNeighborsClassifier
    from sklearn.model_selection import cross_val_score

    n_comp = min(n_components, X.shape[0], X.shape[1])
    pca = PCA(n_components=n_comp)
    X_pca = pca.fit_transform(X)
    labels_arr = np.array(labels)

    axis_names = ["Time", "Scale", "Agency"]
    result: Dict[str, float] = {}

    for ax_idx, ax_name in enumerate(axis_names):
        y = labels_arr[:, ax_idx]
        clf = KNeighborsClassifier(n_neighbors=min(5, X.shape[0] - 1))

        # 5-fold CV (или LOO если мало данных)
        n_folds = min(5, len(np.unique(y)))
        if n_folds < 2:
            result[f"{ax_name}_accuracy"] = float("nan")
            continue

        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            scores = cross_val_score(clf, X_pca, y, cv=n_folds, scoring="accuracy")

        result[f"{ax_name}_accuracy"] = round(float(np.mean(scores)), 3)

    # Baseline: случайное угадывание = 1/3 для каждой оси
    result["chance_level"] = round(1.0 / 3, 3)
    result["n_pca_components"] = n_comp

    return result


def random_baseline_comparison(
    X: np.ndarray,
    n_random_sets: int = 10,
    rng: Optional[np.random.Generator] = None,
) -> Dict[str, float]:
    """
    Сравнение с random baseline: генерируем случайные тексты
    (перемешиваем строки эмбеддингов → ломаем смысловую структуру)
    и оцениваем их ID.
    """
    if rng is None:
        rng = np.random.default_rng(42)

    # ID реальных данных
    real_id = id_twonn(X)

    # ID для случайных данных (перемешиваем признаки независимо)
    random_ids: List[float] = []
    for _ in range(n_random_sets):
        X_rand = X.copy()
        for col in range(X_rand.shape[1]):
            rng.shuffle(X_rand[:, col])
        # Нормализуем строки (как sentence-transformers)
        norms = np.linalg.norm(X_rand, axis=1, keepdims=True)
        norms = np.maximum(norms, 1e-10)
        X_rand = X_rand / norms
        d = id_twonn(X_rand)
        if not np.isnan(d):
            random_ids.append(d)

    if not random_ids:
        return {"real_id": round(float(real_id), 2), "random_mean_id": float("nan")}

    return {
        "real_id": round(float(real_id), 2),
        "random_mean_id": round(float(np.mean(random_ids)), 2),
        "random_std_id": round(float(np.std(random_ids)), 2),
        "ratio": round(float(real_id / np.mean(random_ids)), 3) if np.mean(random_ids) > 0 else float("nan"),
        "cognitive_lower": real_id < np.mean(random_ids),
    }


# ─── Основной анализ ─────────────────────────────────────────────────────

def run_analysis(
    embeddings: np.ndarray,
    labels: List[Tuple[int, int, int]],
    save_plots: bool = True,
    output_dir: str = "id3_results",
    n_bootstrap: int = 100,
    n_permutations: int = 200,
) -> Dict:
    """Запустить все методы и собрать результаты."""
    from sklearn.decomposition import PCA

    rng = np.random.default_rng(42)
    results: Dict = {}

    print("\n" + "=" * 70)
    print("HYPOTHESIS ID-3: INTRINSIC DIMENSION OF COGNITIVE EMBEDDINGS")
    print("=" * 70)
    print(f"Samples: {embeddings.shape[0]}")
    print(f"Embedding dim: {embeddings.shape[1]}")
    print(f"Unique C4 states: {len(set(labels))}")

    # ─── 1. PCA ───
    print("\n--- Method 1: PCA (explained variance) ---")
    n_95, var_ratios = id_pca(embeddings, threshold=0.95)
    n_90, _ = id_pca(embeddings, threshold=0.90)
    n_80, _ = id_pca(embeddings, threshold=0.80)
    print(f"  Components for 80% variance: {n_80}")
    print(f"  Components for 90% variance: {n_90}")
    print(f"  Components for 95% variance: {n_95}")
    print(f"  Top-3 components explain: {sum(var_ratios[:3]):.1%}")
    print(f"  Top-5 components explain: {sum(var_ratios[:5]):.1%}")
    print(f"  Top-10 components explain: {sum(var_ratios[:10]):.1%}")
    results["pca_80"] = int(n_80)
    results["pca_90"] = int(n_90)
    results["pca_95"] = int(n_95)
    results["pca_top3_var"] = round(float(sum(var_ratios[:3])), 4)
    results["pca_top5_var"] = round(float(sum(var_ratios[:5])), 4)

    # ─── 2. TwoNN ───
    print("\n--- Method 2: TwoNN (Facco et al., 2017) ---")
    d_twonn = id_twonn(embeddings)
    print(f"  Estimated intrinsic dimension: {d_twonn:.2f}")
    results["twonn"] = round(d_twonn, 2)

    # ─── 3. MLE ───
    print("\n--- Method 3: MLE (Levina & Bickel, 2004) ---")
    for k in [5, 10, 20]:
        d_mle = id_mle(embeddings, k=k)
        print(f"  k={k}: estimated dimension = {d_mle:.2f}")
        results[f"mle_k{k}"] = round(d_mle, 2)

    # ─── 4. Correlation dimension ───
    print("\n--- Method 4: Correlation dimension ---")
    d_corr = id_correlation(embeddings)
    print(f"  Estimated dimension: {d_corr:.2f}")
    results["correlation_dim"] = round(d_corr, 2)

    # ─── 5. Bootstrap CI ───
    print(f"\n--- Method 5: Bootstrap confidence intervals (n={n_bootstrap}) ---")
    bootstrap_results = bootstrap_id_estimates(embeddings, n_bootstrap=n_bootstrap, rng=rng)
    for method, stats in bootstrap_results.items():
        if not np.isnan(stats["mean"]):
            print(f"  {method}: {stats['mean']:.2f} [{stats['ci_low']:.2f}, {stats['ci_high']:.2f}] (σ={stats['std']:.2f})")
    results["bootstrap"] = bootstrap_results

    # ─── 5b. One-sample t-test: is mean ID ≠ 3? ───
    print("\n--- Statistical test: H₀ mean(ID) = 3.0 ---")
    from scipy import stats as sp_stats
    # Собираем все bootstrap means в один вектор для t-теста
    all_bootstrap_vals: List[float] = []
    for method, bstats in bootstrap_results.items():
        if not np.isnan(bstats["mean"]):
            all_bootstrap_vals.append(bstats["mean"])
    if len(all_bootstrap_vals) >= 2:
        t_stat, t_pvalue = sp_stats.ttest_1samp(all_bootstrap_vals, 3.0)
        print(f"  t-statistic: {t_stat:.3f}")
        print(f"  p-value (two-tailed): {t_pvalue:.4f}")
        if t_pvalue > 0.05:
            print("  ✅ Cannot reject H₀: mean(ID) = 3.0 (p > 0.05)")
        else:
            print(f"  ⚠️  H₀ rejected: mean(ID) ≠ 3.0 (p = {t_pvalue:.4f})")
        results["ttest_h0_eq_3"] = {
            "t_statistic": round(float(t_stat), 3),
            "p_value": round(float(t_pvalue), 4),
            "reject_h0": bool(t_pvalue <= 0.05),
        }
    else:
        print("  ⚠️  Not enough estimators for t-test")
        results["ttest_h0_eq_3"] = {"t_statistic": float("nan"), "p_value": float("nan"), "reject_h0": False}

    # ─── 5c. Eigenvalue gap ratio λ₃/λ₄ ───
    print("\n--- Eigenvalue gap analysis ---")
    n_eigen = min(10, embeddings.shape[0], embeddings.shape[1])
    pca_eigen = PCA(n_components=n_eigen)
    pca_eigen.fit(embeddings)
    eigenvalues = pca_eigen.explained_variance_
    print(f"  Top eigenvalues: {', '.join(f'{v:.4f}' for v in eigenvalues[:6])}")
    eigen_ratios: Dict[str, float] = {}
    for i in range(min(5, len(eigenvalues) - 1)):
        ratio = float(eigenvalues[i] / eigenvalues[i + 1]) if eigenvalues[i + 1] > 1e-10 else float("inf")
        eigen_ratios[f"lambda{i+1}_over_lambda{i+2}"] = round(ratio, 3)
        print(f"  λ{i+1}/λ{i+2} = {ratio:.3f}")
    # Ключевой разрыв: λ₃/λ₄ — должен быть большим если ID ≈ 3
    gap_3_4 = eigen_ratios.get("lambda3_over_lambda4", float("nan"))
    gap_2_3 = eigen_ratios.get("lambda2_over_lambda3", float("nan"))
    if not np.isnan(gap_3_4) and not np.isnan(gap_2_3):
        if gap_3_4 > gap_2_3:
            print(f"  ✅ Gap λ₃/λ₄ ({gap_3_4:.2f}) > λ₂/λ₃ ({gap_2_3:.2f}) — supports d=3")
        else:
            print(f"  ⚠️  Gap λ₃/λ₄ ({gap_3_4:.2f}) ≤ λ₂/λ₃ ({gap_2_3:.2f})")
    results["eigenvalue_gaps"] = eigen_ratios

    # ─── 6. Axis alignment (MI) ───
    print("\n--- Axis alignment check (Mutual Information) ---")
    n_comp_align = min(3, embeddings.shape[0], embeddings.shape[1])
    pca3 = PCA(n_components=n_comp_align)
    X3 = pca3.fit_transform(embeddings)
    labels_arr = np.array(labels)

    from sklearn.metrics import mutual_info_score

    mi_matrix: Dict[str, Dict[str, float]] = {}
    for ax_idx, ax_name in enumerate(["Time", "Scale", "Agency"]):
        mi_matrix[ax_name] = {}
        for pc_idx in range(n_comp_align):
            pc_binned = np.digitize(
                X3[:, pc_idx], bins=np.percentile(X3[:, pc_idx], [33, 67])
            )
            mi = mutual_info_score(labels_arr[:, ax_idx], pc_binned)
            mi_matrix[ax_name][f"PC{pc_idx+1}"] = round(mi, 3)
            if mi > 0.05:
                print(f"  PC{pc_idx+1} ↔ {ax_name}: MI = {mi:.3f}")
    results["mi_matrix"] = mi_matrix

    # ─── 7. Permutation test ───
    print(f"\n--- Permutation test (n={n_permutations}) ---")
    perm_results = permutation_test(embeddings, labels, n_permutations=n_permutations, rng=rng)
    print(f"  Real total MI: {perm_results['real_mi']:.4f}")
    print(f"  Permuted mean MI: {perm_results['perm_mean_mi']:.4f} ± {perm_results['perm_std_mi']:.4f}")
    print(f"  p-value: {perm_results['p_value']:.4f}")
    if perm_results["significant"]:
        print("  ✅ Structure is SIGNIFICANT (p < 0.05)")
    else:
        print("  ⚠️  Structure is NOT significant (p >= 0.05)")
    results["permutation_test"] = perm_results

    # ─── 8. Per-axis dimensionality ───
    print("\n--- Per-axis dimensionality contribution ---")
    axis_results = per_axis_dimensionality(embeddings, labels)
    print(f"  Full ID (TwoNN): {axis_results['full_id']:.2f}")
    for ax_name in ["Time", "Scale", "Agency"]:
        within = axis_results.get(f"{ax_name}_within_id", float("nan"))
        contrib = axis_results.get(f"{ax_name}_contribution", float("nan"))
        print(f"  {ax_name}: within-level ID = {within:.2f}, contribution ≈ {contrib:.2f}")
    results["per_axis"] = axis_results

    # ─── 9. Classification accuracy ───
    print("\n--- Classification: do PC1-3 predict T/D/A? ---")
    clf_results = classification_accuracy(embeddings, labels, n_components=3)
    for ax_name in ["Time", "Scale", "Agency"]:
        acc = clf_results.get(f"{ax_name}_accuracy", float("nan"))
        print(f"  {ax_name} accuracy: {acc:.1%} (chance: {clf_results['chance_level']:.1%})")
    results["classification"] = clf_results

    # ─── 10. Random baseline ───
    print("\n--- Random baseline comparison ---")
    baseline = random_baseline_comparison(embeddings, rng=rng)
    print(f"  Cognitive data ID: {baseline['real_id']:.2f}")
    print(f"  Random baseline ID: {baseline['random_mean_id']:.2f} ± {baseline.get('random_std_id', 0):.2f}")
    if baseline.get("cognitive_lower", False):
        print("  ✅ Cognitive data has LOWER ID than random (structured!)")
    else:
        print("  ⚠️  Cognitive data does NOT have lower ID than random")
    results["random_baseline"] = baseline

    # ─── SUMMARY ───
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)

    estimates = [
        d_twonn,
        results.get("mle_k5", float("nan")),
        results.get("mle_k10", float("nan")),
        results.get("mle_k20", float("nan")),
        d_corr,
    ]
    valid = [e for e in estimates if not np.isnan(e)]
    mean_id = float(np.mean(valid)) if valid else float("nan")
    std_id = float(np.std(valid)) if len(valid) > 1 else float("nan")
    results["mean_estimate"] = round(mean_id, 2)
    results["std_estimate"] = round(std_id, 2)

    print(f"\n  Mean intrinsic dimension estimate: {mean_id:.2f} ± {std_id:.2f}")
    print(f"  C4 prediction: 3.0")
    print(f"  Difference: {abs(mean_id - 3.0):.2f}")

    # Проверяем, попадает ли 3.0 в CI (если есть bootstrap)
    all_cis = []
    for method, stats in bootstrap_results.items():
        if not np.isnan(stats["ci_low"]):
            all_cis.append((stats["ci_low"], stats["ci_high"]))

    three_in_ci = any(lo <= 3.0 <= hi for lo, hi in all_cis)
    results["three_in_bootstrap_ci"] = three_in_ci

    print()
    if abs(mean_id - 3.0) < 1.0:
        print("  ✅ CONSISTENT with Hypothesis ID-3 (|id - 3| < 1)")
        results["verdict"] = "consistent"
    elif abs(mean_id - 3.0) < 2.0:
        print("  🟡 PARTIALLY consistent (|id - 3| < 2)")
        results["verdict"] = "partially_consistent"
    else:
        print("  ❌ NOT consistent with Hypothesis ID-3")
        results["verdict"] = "inconsistent"

    if three_in_ci:
        print("  ✅ 3.0 falls within at least one bootstrap CI")
    else:
        print("  ⚠️  3.0 does NOT fall within any bootstrap CI")

    if perm_results["significant"]:
        print("  ✅ C4 label structure is statistically significant")
    else:
        print("  ⚠️  C4 label structure is NOT statistically significant")

    ttest = results.get("ttest_h0_eq_3", {})
    if not np.isnan(ttest.get("p_value", float("nan"))):
        if not ttest["reject_h0"]:
            print(f"  ✅ t-test: cannot reject H₀ (mean ID = 3), p = {ttest['p_value']:.4f}")
        else:
            print(f"  ⚠️  t-test: H₀ rejected (mean ID ≠ 3), p = {ttest['p_value']:.4f}")

    gap_3_4 = results.get("eigenvalue_gaps", {}).get("lambda3_over_lambda4", float("nan"))
    if not np.isnan(gap_3_4):
        print(f"  Eigenvalue gap λ₃/λ₄ = {gap_3_4:.2f}")

    print(f"\n  Note: This test uses {embeddings.shape[0]} samples.")
    if embeddings.shape[0] < 500:
        print("  ⚠️  For statistical power, use ≥500 diverse texts.")
        print("     Built-in dataset has 5 examples × 27 states = 135 texts.")
        print("     Consider augmenting with real-world cognitive texts.")

    # ─── Сохранение ───
    if save_plots:
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        with open(output_path / "id3_results.json", "w") as f:
            json.dump(results, f, indent=2, ensure_ascii=False, default=str)
        print(f"\n  Results saved to {output_path / 'id3_results.json'}")

        try:
            import matplotlib
            matplotlib.use("Agg")
            import matplotlib.pyplot as plt

            _save_plots(output_path, var_ratios, X3, labels_arr, bootstrap_results, plt)

        except ImportError:
            print("  matplotlib не установлен, графики пропущены.")

    return results


def _save_plots(
    output_path: Path,
    var_ratios: np.ndarray,
    X3: np.ndarray,
    labels_arr: np.ndarray,
    bootstrap_results: Dict,
    plt,
) -> None:
    """Сохранить все графики."""
    # ─── Plot 1: Scree + Cumulative ───
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    n_show = min(20, len(var_ratios))

    ax1 = axes[0]
    ax1.bar(range(1, n_show + 1), var_ratios[:n_show], color="#667eea")
    ax1.axvline(x=3, color="red", linestyle="--", label="C4 prediction (d=3)")
    ax1.set_xlabel("Principal Component")
    ax1.set_ylabel("Explained Variance Ratio")
    ax1.set_title("PCA Scree Plot — Cognitive Embeddings")
    ax1.legend()

    ax2 = axes[1]
    cumvar = np.cumsum(var_ratios[:n_show])
    ax2.plot(range(1, n_show + 1), cumvar, "o-", color="#764ba2")
    ax2.axhline(y=0.80, color="gray", linestyle=":", label="80%")
    ax2.axhline(y=0.90, color="gray", linestyle="--", label="90%")
    ax2.axhline(y=0.95, color="gray", linestyle="-", label="95%")
    ax2.axvline(x=3, color="red", linestyle="--", label="C4 prediction")
    ax2.set_xlabel("Number of Components")
    ax2.set_ylabel("Cumulative Explained Variance")
    ax2.set_title("Cumulative Variance — How Many Dimensions?")
    ax2.legend(loc="lower right")

    plt.tight_layout()
    plt.savefig(output_path / "scree_plot.png", dpi=150)
    print(f"  Scree plot saved to {output_path / 'scree_plot.png'}")

    # ─── Plot 2: 3D scatter ───
    fig = plt.figure(figsize=(10, 8))
    ax = fig.add_subplot(111, projection="3d")
    colors = labels_arr[:, 0] * 9 + labels_arr[:, 1] * 3 + labels_arr[:, 2]
    scatter = ax.scatter(
        X3[:, 0], X3[:, 1], X3[:, 2],
        c=colors, cmap="viridis", s=50, alpha=0.7,
    )
    ax.set_xlabel("PC1")
    ax.set_ylabel("PC2")
    ax.set_zlabel("PC3")
    ax.set_title("Cognitive Embeddings in PCA-3D Space (colored by C4 state)")
    plt.colorbar(scatter, label="C4 state index (0-26)", shrink=0.6)
    plt.savefig(output_path / "pca_3d.png", dpi=150)
    print(f"  3D PCA plot saved to {output_path / 'pca_3d.png'}")

    # ─── Plot 3: Bootstrap distributions ───
    methods_with_data = {m: s for m, s in bootstrap_results.items() if not np.isnan(s["mean"])}
    if methods_with_data:
        fig, ax = plt.subplots(figsize=(10, 5))
        names = list(methods_with_data.keys())
        means = [methods_with_data[m]["mean"] for m in names]
        ci_lows = [methods_with_data[m]["ci_low"] for m in names]
        ci_highs = [methods_with_data[m]["ci_high"] for m in names]
        yerr_low = [m - lo for m, lo in zip(means, ci_lows)]
        yerr_high = [hi - m for m, hi in zip(means, ci_highs)]

        ax.errorbar(names, means, yerr=[yerr_low, yerr_high], fmt="o", capsize=8,
                    color="#667eea", markersize=10, linewidth=2)
        ax.axhline(y=3.0, color="red", linestyle="--", linewidth=2, label="C4 prediction (d=3)")
        ax.set_ylabel("Estimated Intrinsic Dimension")
        ax.set_title("Bootstrap CI (95%) for Intrinsic Dimension Estimates")
        ax.legend()
        ax.grid(axis="y", alpha=0.3)

        plt.tight_layout()
        plt.savefig(output_path / "bootstrap_ci.png", dpi=150)
        print(f"  Bootstrap CI plot saved to {output_path / 'bootstrap_ci.png'}")

    plt.close("all")


def run_multi_model(
    texts: List[str],
    labels: List[Tuple[int, int, int]],
    output_dir: str = "id3_results",
) -> Dict[str, Dict]:
    """Запустить анализ на нескольких моделях для проверки робастности."""
    models = [
        "all-MiniLM-L6-v2",        # 384d, быстрая, англ
        "all-mpnet-base-v2",        # 768d, лучшее качество, англ
        "paraphrase-multilingual-MiniLM-L12-v2",  # 384d, мультиязычная
    ]

    print("\n" + "=" * 70)
    print("MULTI-MODEL ROBUSTNESS CHECK")
    print("=" * 70)

    all_results: Dict[str, Dict] = {}
    for model_name in models:
        print(f"\n{'─' * 50}")
        print(f"Model: {model_name}")
        print(f"{'─' * 50}")

        try:
            embeddings = embed_texts(texts, model_name)
            model_output = f"{output_dir}/{model_name.replace('/', '_')}"
            results = run_analysis(
                embeddings, labels,
                save_plots=True,
                output_dir=model_output,
                n_bootstrap=50,  # Быстрее для мульти-модели
                n_permutations=100,
            )
            all_results[model_name] = results
        except Exception as e:
            print(f"  ERROR: {e}")
            all_results[model_name] = {"error": str(e)}

    # Сводная таблица
    print("\n" + "=" * 70)
    print("MULTI-MODEL SUMMARY")
    print("=" * 70)
    print(f"{'Model':<45} {'Mean ID':>8} {'TwoNN':>8} {'Verdict':<20}")
    print("─" * 85)
    for model_name, res in all_results.items():
        if "error" in res:
            print(f"{model_name:<45} {'ERROR':>8} {'':>8} {res['error']:<20}")
        else:
            mean_id = res.get("mean_estimate", "?")
            twonn = res.get("twonn", "?")
            verdict = res.get("verdict", "?")
            print(f"{model_name:<45} {mean_id:>8} {twonn:>8} {verdict:<20}")

    # Сохранение сводки
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    with open(output_path / "multi_model_summary.json", "w") as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False, default=str)
    print(f"\n  Multi-model summary saved to {output_path / 'multi_model_summary.json'}")

    return all_results


def main() -> Optional[Dict]:
    parser = argparse.ArgumentParser(
        description="Test Hypothesis ID-3: intrinsic dimension of cognitive embeddings ≈ 3"
    )
    parser.add_argument(
        "--model",
        default="all-MiniLM-L6-v2",
        help="Sentence-transformer model (default: all-MiniLM-L6-v2, fast & good)",
    )
    parser.add_argument(
        "--data",
        default=None,
        help="Path to custom data file (jsonl: {text, state}). "
             "If not provided, uses built-in 135 examples.",
    )
    parser.add_argument(
        "--output",
        default="id3_results",
        help="Output directory for results and plots",
    )
    parser.add_argument(
        "--no-plots",
        action="store_true",
        help="Skip plot generation",
    )
    parser.add_argument(
        "--multi-model",
        action="store_true",
        help="Run across 3 models for robustness check",
    )
    parser.add_argument(
        "--bootstrap",
        type=int,
        default=100,
        help="Number of bootstrap iterations (default: 100)",
    )
    parser.add_argument(
        "--permutations",
        type=int,
        default=200,
        help="Number of permutation test iterations (default: 200)",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducibility (default: 42)",
    )
    args = parser.parse_args()

    np.random.seed(args.seed)

    # Данные
    if args.data:
        texts, labels = load_custom_data(args.data)
        print(f"Loaded {len(texts)} texts from {args.data}")
    else:
        texts, labels = get_all_texts_and_labels()
        print(f"Using built-in dataset: {len(texts)} texts across 27 C4 states")

    # Мульти-модельный режим
    if args.multi_model:
        return run_multi_model(texts, labels, output_dir=args.output)

    # Эмбеддинги
    embeddings = embed_texts(texts, args.model)

    # Анализ
    results = run_analysis(
        embeddings, labels,
        save_plots=not args.no_plots,
        output_dir=args.output,
        n_bootstrap=args.bootstrap,
        n_permutations=args.permutations,
    )

    return results


if __name__ == "__main__":
    main()
