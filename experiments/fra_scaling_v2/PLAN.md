# FRA Scaling Hypothesis 1.4 — План v2

## Цель
Проверить гипотезу K = O(1/ε^d) на данных с **реальной diversity** (разные стратегии побеждают на разных инстансах).

## Стратегия: Синтетика (proof-of-concept) + ASlib (validation)

---

## ФАЗА 1: Синтетический Proof-of-Concept (локально)

### 1.1 Создание синтетического датасета

**Идея:** Создать "задачу" где мы **контролируем** какая стратегия лучше для какого типа инстанса.

```
Instance types:     A, B, C, D (4 кластера в feature space)
Strategies:         s1, s2, s3, s4
Ground truth:       type A → s1 wins
                    type B → s2 wins
                    type C → s3 wins
                    type D → s4 wins
```

**Параметры:**
- n_instances: 200 (50 per type)
- n_features (d): варьируем [4, 8, 16, 32]
- n_strategies (K): варьируем [2, 4, 8, 16]
- noise_level: 0.1 (10% случаев не-оптимальная стратегия побеждает)

### 1.2 Реализация SyntheticProblem

```python
class SyntheticProblem(Problem):
    """
    Синтетическая задача с контролируемой diversity.
    Fingerprint = координаты в d-мерном пространстве.
    Strategy performance = зависит от расстояния до центроида кластера.
    """

    def generate_instances(self, n, d, n_types):
        # Создаём n_types центроидов в d-мерном пространстве
        # Генерируем инстансы вокруг центроидов
        # Возвращаем (fingerprints, true_labels)

    def compute_performance(self, fingerprints, labels, K, noise):
        # Strategy k оптимальна для type k
        # Performance[i, k] = base + bonus if label[i] == k else penalty
        # Добавляем noise
```

### 1.3 Эксперимент на синтетике

**Grid:**
```yaml
vary_K:
  d: 16
  K: [2, 4, 8, 16]

vary_d:
  K: 8
  d: [4, 8, 16, 32]
```

**Метрики:**
- FRA win rate (% случаев когда FRA лучше best single)
- Gap to oracle
- Routing accuracy
- Correlation: K vs gap, d vs gap

**Ожидаемый результат:**
- При K = n_types, FRA должен достичь oracle performance
- При K < n_types, FRA хуже oracle пропорционально

### 1.4 Валидация proof-of-concept

**Критерии успеха:**
1. FRA win rate > 50% при K ≥ n_types
2. Routing accuracy > 80% при достаточном K
3. Gap ↓ при K ↑ (отрицательная корреляция)

---

## ФАЗА 2: ASlib Validation (реальные данные)

### 2.1 Что такое ASlib

**Algorithm Selection Library** — стандартный benchmark для algorithm selection.
- 30+ scenarios (SAT, TSP, QBF, etc.)
- Готовые features для каждого инстанса
- Готовые performance data (время/качество каждого алгоритма)

**Формат:**
```
scenario/
├── description.txt      # Метаданные
├── feature_values.arff  # Fingerprints
├── algorithm_runs.arff  # Performance matrix
└── cv.arff              # Cross-validation splits
```

### 2.2 Скачивание и парсинг

```python
# ASlib scenarios доступны на GitHub
ASLIB_URL = "https://github.com/coseal/aslib_data"

# Приоритетные scenarios:
SCENARIOS = [
    "SAT11-RAND",      # Random SAT (diverse solvers)
    "SAT11-INDU",      # Industrial SAT
    "TSP-LION2015",    # TSP instances
    "MAXSAT12-PMS",    # MaxSAT
]
```

### 2.3 Адаптация FRA для ASlib

```python
class ASLibProblem(Problem):
    """Загружает ASlib scenario и адаптирует к FRA формату."""

    def load_scenario(self, scenario_path):
        # Парсим .arff файлы
        # Извлекаем features, performance, cv_splits

    def get_strategies(self):
        # Возвращаем список алгоритмов из scenario

    def extract_features(self, instance):
        # Возвращаем готовые features из feature_values.arff
```

### 2.4 Эксперимент на ASlib

**Для каждого scenario:**
```yaml
vary_K:
  d: native  # Используем все features
  K: [2, 4, 8, 16, 32, all]

vary_d:
  K: 8
  d: [4, 8, 16, 32, native]
```

**Cross-validation:** Используем официальные CV splits из ASlib.

### 2.5 Анализ гипотезы

**Метрики:**
- PAR10 score (Penalized Average Runtime, стандарт ASlib)
- VBS gap (Virtual Best Solver gap)
- SBS gap (Single Best Solver gap)

**Проверка гипотезы:**
```
H0: K scaling не зависит от d
H1: K = O(1/ε^d) — количество стратегий растёт экспоненциально с d
```

---

## ФАЗА 3: Анализ и визуализация

### 3.1 Графики

1. **K vs Gap** (log-log scale) — проверка power law
2. **d vs Gap** — влияние размерности
3. **Routing accuracy heatmap** — K × d
4. **Comparison: Synthetic vs ASlib** — validation

### 3.2 Статистические тесты

- Spearman correlation (K vs gap)
- Power law fit: gap ~ α/K^β
- Bootstrap confidence intervals

### 3.3 Отчёт

Markdown отчёт с:
- Методология
- Результаты (таблицы + графики)
- Выводы по гипотезе
- Limitations

---

## IMPLEMENTATION CHECKLIST

### Defensive Programming (уроки из v1)

- [ ] Все numpy arrays проверять на NaN/Inf перед использованием
- [ ] PCA: `n_components = min(d, n_samples-1, n_features)`
- [ ] Router input_dim = actual fingerprint dimension, не config
- [ ] Try/except вокруг каждого шага с понятными сообщениями
- [ ] Incremental saving после каждого config
- [ ] Тестировать локально перед vast.ai

### Файловая структура

```
fra_scaling_v2/
├── PLAN.md                 # Этот файл
├── config.yaml             # Конфигурация
├── run_experiment.py       # Главный скрипт
├── problems/
│   ├── base.py             # Копия из v1
│   ├── synthetic.py        # Новый: SyntheticProblem
│   └── aslib.py            # Новый: ASLibProblem
├── fra/
│   └── router.py           # Копия из v1
├── data/
│   └── aslib/              # Скачанные scenarios
├── results/
│   ├── synthetic/          # Результаты фазы 1
│   └── aslib/              # Результаты фазы 2
└── analysis/
    └── report.md           # Финальный отчёт
```

### Порядок выполнения

1. **Setup** (5 min)
   - Создать структуру папок
   - Скопировать base.py, router.py из v1

2. **Synthetic Problem** (15 min)
   - Реализовать SyntheticProblem
   - Unit test локально

3. **Synthetic Experiment** (10 min)
   - Запустить grid локально
   - Сохранить результаты

4. **ASlib Setup** (10 min)
   - Скачать scenarios
   - Реализовать ASLibProblem

5. **ASlib Experiment** (20 min)
   - Запустить на 4 scenarios
   - Сохранить результаты

6. **Analysis** (10 min)
   - Графики
   - Статистика
   - Отчёт

**Total estimated: ~70 min**

---

## КРИТЕРИИ УСПЕХА

### Минимальный успех (proof-of-concept works)
- [ ] Synthetic: FRA beats best single when K ≥ n_types
- [ ] Synthetic: Negative correlation K vs gap

### Полный успех (hypothesis confirmed)
- [ ] ASlib: FRA beats SBS on ≥2 scenarios
- [ ] ASlib: Power law fit R² > 0.7
- [ ] ASlib: Consistent pattern across scenarios

### Negative result (hypothesis rejected)
- [ ] Document why it doesn't work
- [ ] Identify conditions where FRA helps vs doesn't
- [ ] Propose refined hypothesis

---

## НАЧАЛО ВЫПОЛНЕНИЯ

После утверждения плана — автоматическое выполнение всех фаз.
