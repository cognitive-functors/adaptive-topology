# Руководство по интеграции C4

Как интегрировать Полную когнитивную координатную систему в архитектуры ИИ-агентов, аналитические пайплайны и системы поддержки принятия решений.

---

## 1. Введение

C4 предоставляет структурированную координатную систему для когнитивных состояний: каждое состояние -- тройка (T, D, A) из {0, 1, 2}^3, что даёт 27 базисных состояний. Данное руководство охватывает практические паттерны интеграции для программных систем, которым полезно явное моделирование временной ориентации, уровня абстракции и агентной перспективы.

**Сценарии использования:**
- ИИ-агенты с метакогнитивным мониторингом
- Диалоговые системы, отслеживающие динамику дискурса
- Аналитические дашборды для текстовых корпусов
- Системы поддержки принятия решений, требующие мультиперспективного анализа

---

## 2. Основной API

### 2.1 Представление состояния

```python
from dataclasses import dataclass
from enum import IntEnum

class Time(IntEnum):
 PAST = 0
 PRESENT = 1
 FUTURE = 2

class Scale(IntEnum):
 CONCRETE = 0
 ABSTRACT = 1
 META = 2

class Agency(IntEnum):
 SELF = 0
 OTHER = 1
 SYSTEM = 2

@dataclass(frozen=True)
class C4State:
 t: Time
 d: Scale
 i: Agency

 def as_tuple(self) -> tuple[int, int, int]:
 return (self.t.value, self.d.value, self.i.value)

 def hamming_distance(self, other: "C4State") -> int:
 return sum(
 a != b for a, b in zip(self.as_tuple(), other.as_tuple())
 )
```

### 2.2 Операторы

```python
def shift_t(state: C4State) -> C4State:
 """Циклический сдвиг оси времени: Past -> Present -> Future -> Past."""
 return C4State(Time((state.t + 1) % 3), state.d, state.i)

def shift_d(state: C4State) -> C4State:
 """Циклический сдвиг оси масштаба: Concrete -> Abstract -> Meta -> Concrete."""
 return C4State(state.t, Scale((state.d + 1) % 3), state.i)

def shift_i(state: C4State) -> C4State:
 """Циклический сдвиг оси агентности: Self -> Other -> System -> Self."""
 return C4State(state.t, state.d, Agency((state.i + 1) % 3))
```

### 2.3 Кратчайший путь (реализация Теоремы 9)

```python
def belief_path(source: C4State, target: C4State) -> list[str]:
 """Вычисление кратчайшей последовательности операторов от source к target.

 Возвращает список имён операторов. Максимальная длина: 3.
 Основано на Теореме 9 (конструктивная, формально верифицированная).
 """
 path = []
 dt = (target.t - source.t) % 3
 dd = (target.d - source.d) % 3
 di = (target.i - source.i) % 3

 for _ in range(dt):
 path.append("shift_t")
 for _ in range(dd):
 path.append("shift_d")
 for _ in range(di):
 path.append("shift_i")
 return path
```

---

## 3. Пайплайн классификации

### 3.1 Использование предобученной модели

```python
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch

class C4Classifier:
 """Классификация текста в координаты C4 с использованием DeBERTa и LoRA-адаптеров."""

 def __init__(self, model_path: str = "c4-cognitive-adapters"):
 self.tokenizer = AutoTokenizer.from_pretrained(model_path)
 self.model = AutoModelForSequenceClassification.from_pretrained(model_path)
 self.model.eval()

 def predict(self, text: str) -> C4State:
 inputs = self.tokenizer(text, return_tensors="pt", truncation=True)
 with torch.no_grad():
 outputs = self.model(**inputs)
 # outputs.logits shape: (1, 9) -- 3 класса x 3 оси
 logits = outputs.logits.view(3, 3)
 t_pred = logits[0].argmax().item()
 d_pred = logits[1].argmax().item()
 i_pred = logits[2].argmax().item()
 return C4State(Time(t_pred), Scale(d_pred), Agency(i_pred))

 def predict_with_confidence(self, text: str) -> tuple[C4State, dict]:
 inputs = self.tokenizer(text, return_tensors="pt", truncation=True)
 with torch.no_grad():
 outputs = self.model(**inputs)
 logits = outputs.logits.view(3, 3)
 probs = torch.softmax(logits, dim=1)
 state = C4State(
 Time(logits[0].argmax().item()),
 Scale(logits[1].argmax().item()),
 Agency(logits[2].argmax().item()),
 )
 confidence = {
 "t": probs[0].max().item(),
 "d": probs[1].max().item(),
 "i": probs[2].max().item(),
 }
 return state, confidence
```

### 3.2 Классификация на основе LLM (без дообученной модели)

Для быстрого прототипирования без дообученной модели:

```python
CLASSIFICATION_PROMPT = """Classify the following text on three axes.
Each axis has values 0, 1, 2.

T (Time): 0=Past, 1=Present, 2=Future
D (Scale): 0=Concrete, 1=Abstract, 2=Meta
A (Agency): 0=Self, 1=Other, 2=System

Text: "{text}"

Respond with JSON only: {{"t": N, "d": N, "i": N}}
"""
```

Этот подход пригоден для начальной разметки обучающих данных или приложений с небольшим объёмом запросов. Точность ниже, чем у дообученной модели, но достаточна для исследовательского анализа.

---

## 4. Дашборд покрытия

### 4.1 Концепция

Дашборд покрытия отслеживает, какие из 27 состояний C4 были посещены в ходе разговора, анализа или процесса рассуждения. Это обеспечивает метакогнитивный мониторинг: обнаружение слепых пятен в перспективе.

### 4.2 Реализация

```python
class CoverageDashboard:
 """Отслеживание покрытия состояний C4 по последовательности наблюдений."""

 def __init__(self):
 self.visited: set[tuple[int, int, int]] = set()
 self.history: list[C4State] = []

 def observe(self, state: C4State) -> None:
 self.visited.add(state.as_tuple())
 self.history.append(state)

 @property
 def coverage(self) -> float:
 return len(self.visited) / 27.0

 @property
 def missing_states(self) -> list[tuple[int, int, int]]:
 all_states = {
 (t, d, i)
 for t in range(3) for d in range(3) for i in range(3)
 }
 return sorted(all_states - self.visited)

 def missing_by_axis(self) -> dict[str, set[int]]:
 """Определение недопредставленных значений по осям."""
 visited_t = {s[0] for s in self.visited}
 visited_d = {s[1] for s in self.visited}
 visited_i = {s[2] for s in self.visited}
 return {
 "T": {0, 1, 2} - visited_t,
 "D": {0, 1, 2} - visited_d,
 "I": {0, 1, 2} - visited_i,
 }

 def summary(self) -> str:
 pct = self.coverage * 100
 missing = self.missing_states
 lines = [f"Coverage: {len(self.visited)}/27 ({pct:.1f}%)"]
 if missing:
 lines.append(f"Missing states: {len(missing)}")
 by_axis = self.missing_by_axis()
 for axis, vals in by_axis.items():
 if vals:
 lines.append(f" {axis}-axis gaps: {sorted(vals)}")
 else:
 lines.append("Full coverage achieved.")
 return "\n".join(lines)
```

### 4.3 Использование в ИИ-агентах

```python
# Внутри цикла агента
dashboard = CoverageDashboard()
classifier = C4Classifier()

for turn in conversation:
 state = classifier.predict(turn.text)
 dashboard.observe(state)

 if dashboard.coverage < 0.5 and len(dashboard.history) > 10:
 # Агент застрял в узком когнитивном регионе
 gaps = dashboard.missing_by_axis()
 if 2 not in {s[0] for s in dashboard.visited}:
 prompt_agent("Consider future implications.")
 if 2 not in {s[2] for s in dashboard.visited}:
 prompt_agent("Consider the systemic perspective.")
```

---

## 5. Паттерны интеграции

### 5.1 Метакогниция агента

Подключите CoverageDashboard к каждому ИИ-агенту. После каждых N шагов рассуждения проверяйте покрытие. Если агент не посещал определённые квадранты (например, никогда не рассматривал будущее или не принимал перспективу другого), инъектируйте запрос на исследование этого региона.

### 5.2 Мультиагентные системы

В мультиагентных архитектурах назначайте агентам различные регионы C4:

| Роль агента | Основной регион C4 | Функция |
|-------------|-------------------|---------|
| Аналитик | (Настоящее, Абстрактное, Система) | Распознавание паттернов, системный анализ |
| Эмпат | (Настоящее, Конкретное, Другой) | Принятие перспективы, моделирование пользователя |
| Стратег | (Будущее, Абстрактное, Система) | Долгосрочное планирование |
| Историк | (Прошлое, Конкретное, Система) | Поиск прецедентов, подбор кейсов |
| Критик | (Настоящее, Мета, Я) | Саморефлексия, контроль качества |

Координируйте агентов, обеспечивая коллективное покрытие всех 27 состояний.

### 5.3 Улучшение RAG-пайплайна

При построении систем генерации с дополнением поиском (RAG) размечайте извлечённые документы координатами C4. При запросе убедитесь, что извлечённый набор покрывает несколько состояний C4:

```python
def diversify_retrieval(
 candidates: list[Document],
 classifier: C4Classifier,
 top_k: int = 5,
) -> list[Document]:
 """Выбор документов, максимизирующих покрытие C4."""
 selected = []
 covered = set()
 for doc in sorted(candidates, key=lambda d: d.relevance, reverse=True):
 state = classifier.predict(doc.text)
 coords = state.as_tuple()
 if coords not in covered or len(selected) < 2:
 selected.append(doc)
 covered.add(coords)
 if len(selected) >= top_k:
 break
 return selected
```

### 5.4 Мониторинг дискурса

Для диалогового ИИ отслеживайте переходы состояний C4 для обнаружения:
- **Циклов:** повторные посещения одного и того же состояния (застревание в руминации)
- **Скачков:** расстояние Хэмминга > 2 между последовательными состояниями (некогерентный сдвиг)
- **Дрейфа:** постепенное смещение от целевого региона темы

---

## 6. Связь с MASTm (адаптивная маршрутизация)

Фреймворк MASTm (Multi-scale Adaptive Spectral TSP meta-solver) применяет навигационные принципы C4 к комбинаторной оптимизации. Ключевой вывод: вычисление кратчайшего пути в C4 (Теорема 9) обобщается на адаптивную маршрутизацию в произвольных метрических пространствах.

Для интеграции с оптимизационными пайплайнами см. `papers/algorithmic-topology/`.

---

## 7. Сводка по API

| Функция | Вход | Выход | Описание |
|---------|------|-------|----------|
| `C4State(t, d, i)` | Три значения enum | Объект состояния | Создание когнитивного состояния |
| `hamming_distance(s1, s2)` | Два состояния | int (0-3) | Расстояние между состояниями |
| `belief_path(s1, s2)` | Два состояния | list[str] | Кратчайшая последовательность операторов |
| `C4Classifier.predict(text)` | Строка | C4State | Классификация текста в координаты |
| `CoverageDashboard.observe(s)` | Состояние | None | Регистрация посещения состояния |
| `CoverageDashboard.summary()` | None | Строка | Отчёт о покрытии |

---

## 8. Соображения по развёртыванию

- **Латентность:** Инференс DeBERTa занимает ~15 мс/предложение на GPU, ~100 мс на CPU. Для приложений реального времени рассмотрите батчинг или дистиллированную модель меньшего размера.
- **Пороги уверенности:** Установите минимальную уверенность (например, 0.7 по каждой оси) перед принятием решений на основе классификации.
- **Запасной вариант (fallback):** Когда классификатор неуверен, логируйте состояние как "неклассифицированное" вместо принудительного присвоения с низкой уверенностью.

---

## 9. Контакты

- Исследовательские запросы: psy.seliger@yandex.ru
- Технические вопросы / код: comonoid@yandex.ru
- GitHub: https://github.com/cognitive-functors/adaptive-topology

---

## Литература

- Selyutin, I. & Kovalev, N. (2025). "C4: Complete Cognitive Coordinate System." Preprint.
- He, P. et al. (2021). "DeBERTa: Decoding-enhanced BERT with Disentangled Attention." ICLR 2021.
