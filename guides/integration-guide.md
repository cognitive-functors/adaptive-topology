# C4 Integration Guide

How to integrate the Complete Cognitive Coordinate System into AI agent architectures, analytical pipelines, and decision-support systems.

---

## 1. Introduction

C4 provides a structured coordinate system for cognitive states: each state is a triple (T, D, A) in {0, 1, 2}^3, yielding 27 basis states. This guide covers practical integration patterns for software systems that benefit from explicit modeling of temporal orientation, abstraction level, and agentive perspective.

**Use cases:**
- AI agents with metacognitive monitoring
- Conversational systems that track discourse dynamics
- Analytical dashboards for text corpora
- Decision-support systems requiring multi-perspective analysis

---

## 2. Core API

### 2.1 State Representation

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

### 2.2 Operators

```python
def shift_t(state: C4State) -> C4State:
 """Cycle time axis: Past -> Present -> Future -> Past."""
 return C4State(Time((state.t + 1) % 3), state.d, state.i)

def shift_d(state: C4State) -> C4State:
 """Cycle scale axis: Concrete -> Abstract -> Meta -> Concrete."""
 return C4State(state.t, Scale((state.d + 1) % 3), state.i)

def shift_i(state: C4State) -> C4State:
 """Cycle agency axis: Self -> Other -> System -> Self."""
 return C4State(state.t, state.d, Agency((state.i + 1) % 3))
```

### 2.3 Shortest Path (Theorem 9 Implementation)

```python
def belief_path(source: C4State, target: C4State) -> list[str]:
 """Compute shortest operator sequence from source to target.

 Returns list of operator names. Maximum length: 3.
 Based on Theorem 9 (constructive, formally verified).
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

## 3. Classification Pipeline

### 3.1 Using the Pretrained Model

```python
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch

class C4Classifier:
 """Classify text into C4 coordinates using DeBERTa with LoRA adapters."""

 def __init__(self, model_path: str = "c4-cognitive-adapters"):
 self.tokenizer = AutoTokenizer.from_pretrained(model_path)
 self.model = AutoModelForSequenceClassification.from_pretrained(model_path)
 self.model.eval()

 def predict(self, text: str) -> C4State:
 inputs = self.tokenizer(text, return_tensors="pt", truncation=True)
 with torch.no_grad():
 outputs = self.model(**inputs)
 # outputs.logits shape: (1, 9) -- 3 classes x 3 axes
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

### 3.2 LLM-Based Classification (No Fine-Tuned Model)

For rapid prototyping without a fine-tuned model:

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

This approach is suitable for bootstrapping training data or low-volume applications. Accuracy is lower than the fine-tuned model but sufficient for exploratory analysis.

---

## 4. Coverage Dashboard

### 4.1 Concept

A Coverage Dashboard tracks which of the 27 C4 states have been visited during a conversation, analysis, or reasoning process. This enables metacognitive monitoring: detecting blind spots in perspective.

### 4.2 Implementation

```python
class CoverageDashboard:
 """Track C4 state coverage over a sequence of observations."""

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
 """Identify which axis values are underrepresented."""
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

### 4.3 Usage in AI Agents

```python
# Inside an agent loop
dashboard = CoverageDashboard()
classifier = C4Classifier()

for turn in conversation:
 state = classifier.predict(turn.text)
 dashboard.observe(state)

 if dashboard.coverage < 0.5 and len(dashboard.history) > 10:
 # Agent is stuck in a narrow cognitive region
 gaps = dashboard.missing_by_axis()
 if 2 not in {s[0] for s in dashboard.visited}:
 prompt_agent("Consider future implications.")
 if 2 not in {s[2] for s in dashboard.visited}:
 prompt_agent("Consider the systemic perspective.")
```

---

## 5. Integration Patterns

### 5.1 Agent Metacognition

Attach a CoverageDashboard to each AI agent. After every N reasoning steps, check coverage. If the agent has not visited certain quadrants (e.g., never considered the future, or never took the other's perspective), inject a prompt to explore that region.

### 5.2 Multi-Agent Systems

In multi-agent architectures, assign agents to different C4 regions:

| Agent Role | Primary C4 Region | Function |
|------------|-------------------|----------|
| Analyst | (Present, Abstract, System) | Pattern recognition, systemic analysis |
| Empath | (Present, Concrete, Other) | Perspective-taking, user modeling |
| Strategist | (Future, Abstract, System) | Long-term planning |
| Historian | (Past, Concrete, System) | Precedent retrieval, case matching |
| Critic | (Present, Meta, Self) | Self-reflection, quality checking |

Coordinate agents by ensuring collective coverage of all 27 states.

### 5.3 RAG Pipeline Enhancement

When building Retrieval-Augmented Generation systems, tag retrieved documents with C4 coordinates. At query time, ensure the retrieved set covers multiple C4 states:

```python
def diversify_retrieval(
 candidates: list[Document],
 classifier: C4Classifier,
 top_k: int = 5,
) -> list[Document]:
 """Select documents that maximize C4 coverage."""
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

### 5.4 Discourse Monitoring

For conversational AI, track C4 state transitions to detect:
- **Loops:** Repeated visits to the same state (stuck in rumination)
- **Jumps:** Hamming distance > 2 between consecutive states (incoherent shift)
- **Drift:** Gradual movement away from the topic's target region

---

## 6. Connection to MASTm (Adaptive Routing)

The MASTm (Multi-scale Adaptive Spectral TSP meta-solver) framework applies C4's navigational principles to combinatorial optimization. The core insight: shortest-path computation in C4 (Theorem 9) generalizes to adaptive routing in arbitrary metric spaces.

For integration with optimization pipelines, see `papers/algorithmic-topology/`.

---

## 7. API Reference Summary

| Function | Input | Output | Description |
|----------|-------|--------|-------------|
| `C4State(t, d, i)` | Three enum values | State object | Create a cognitive state |
| `hamming_distance(s1, s2)` | Two states | int (0-3) | Distance between states |
| `belief_path(s1, s2)` | Two states | list[str] | Shortest operator sequence |
| `C4Classifier.predict(text)` | String | C4State | Classify text to coordinates |
| `CoverageDashboard.observe(s)` | State | None | Record a state visit |
| `CoverageDashboard.summary()` | None | String | Coverage report |

---

## 8. Deployment Considerations

- **Latency:** DeBERTa inference is ~15ms/sentence on GPU, ~100ms on CPU. For real-time applications, consider batching or using a smaller distilled model.
- **Confidence thresholds:** Set minimum confidence (e.g., 0.7 per axis) before acting on classifications.
- **Fallback:** When the classifier is uncertain, log the state as "unclassified" rather than forcing a low-confidence assignment.

---

## 9. Contact

- Research inquiries: psy.seliger@yandex.ru
- Technical / code: comonoid@yandex.ru
- GitHub: https://github.com/cognitive-functors/adaptive-topology

---

## References

- Selyutin, I. & Kovalev, N. (2025). "C4: Complete Cognitive Coordinate System." Preprint.
- He, P. et al. (2021). "DeBERTa: Decoding-enhanced BERT with Disentangled Attention." ICLR 2021.
