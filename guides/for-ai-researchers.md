# C4 for AI Researchers

How the Complete Cognitive Coordinate System enables structured multi-label classification of cognitive states, with a production-ready DeBERTa architecture and benchmark results.

---

## Problem Statement

Given a text segment (sentence, paragraph, or discourse unit), predict its cognitive coordinates:

```
f(text) -> (T, D, A) in {0, 1, 2}^3
```

Where:
- **T (Time):** Past (0) / Present (1) / Future (2)
- **D (Scale):** Concrete (0) / Abstract (1) / Meta (2)
- **A (Agency):** Self (0) / Other (1) / System (2)

This is a **structured multi-label classification** task: three correlated ordinal outputs, each with 3 classes. The label space has 27 possible combinations.

---

## Why This Matters for AI

1. **Interpretable dimensionality reduction:** Text embeddings live in R^768+. C4 maps them to Z3^3 (27 discrete states) while preserving cognitively meaningful structure. This is analogous to PCA but with semantically grounded axes.

2. **Testable hypothesis:** If C4's claim is correct, the *intrinsic dimension* of cognitive text embeddings should be approximately 3. This is an independently verifiable prediction (see Section on Falsification).

3. **AI agent architecture:** C4 coordinates can serve as a structured state representation for cognitive agents, enabling explicit reasoning about time horizon, abstraction level, and perspective.

4. **Alignment:** C4 provides a formal vocabulary for describing what an AI system is "thinking about" -- which temporal horizon, which abstraction level, whose perspective.

---

## Architecture: Published HuggingFace Model

### Overview

The published model uses DeBERTa-v3-base as the backbone with a multi-head classification architecture:

```
Input text
 |
[DeBERTa-v3-base encoder]
 |
[CLS token representation] (768-dim)
 |
 +---> [T-head] -> softmax(3) -- Time prediction
 +---> [D-head] -> softmax(3) -- Scale prediction
 +---> [A-head] -> softmax(3) -- Agency prediction
```

### Model Specifics

- **65 classification heads** across 12 LoRA adapters
- **12 LoRA adapter modules:** specialized for different text domains and classification tasks
- **Ensemble:** Final prediction is majority vote across heads, with confidence = agreement ratio
- **Training:** Multi-task loss = L_T + L_D + L_I with class weights to handle label imbalance

### Why 65 Heads?

Single-head classifiers achieve ~75% per-axis accuracy. The 65-head ensemble with adapter specialization reaches ~85-88% per-axis accuracy by:
- Reducing variance through averaging
- Capturing domain-specific patterns via adapters
- Providing calibrated confidence estimates (high agreement = high confidence)

---

## Training Data

### Data Sources

| Source | Size | Description |
|--------|------|-------------|
| Expert-annotated | ~5K samples | Gold standard, triple-annotated with adjudication |
| LLM-assisted | ~50K samples | GPT-4 / Claude annotations, filtered by consistency |
| Semi-supervised | ~200K samples | High-confidence predictions from V5/V6, human-verified subset |

### Annotation Protocol

1. Annotator reads text segment
2. Assigns T in {Past, Present, Future}
3. Assigns D in {Concrete, Abstract, Meta}
4. Assigns I in {Self, Other, System}
5. Confidence flag: {certain, uncertain}
6. Inter-annotator agreement: Cohen's kappa > 0.7 required

### Label Distribution

The label space is not uniform. Common states:
- (1, 1, 2) = Present/Abstract/System -- academic/analytical text (most frequent)
- (0, 0, 0) = Past/Concrete/Self -- personal narrative
- (1, 0, 0) = Present/Concrete/Self -- experiential report

Rare states:
- (2, 2, 1) = Future/Meta/Other -- anticipating another's meta-cognition
- (0, 2, 2) = Past/Meta/System -- historical meta-analysis of systemic processes

Class weighting is applied to compensate for this imbalance.

---

## Benchmarks

### Per-Axis Accuracy (test set)

| Axis | Accuracy | Macro-F1 | Notes |
|------|----------|----------|-------|
| T (Time) | 87.2% | 0.85 | Future is hardest (fewer samples) |
| D (Scale) | 83.5% | 0.81 | Meta vs. Abstract boundary is fuzzy |
| A (Agency) | 85.8% | 0.84 | System vs. Other requires context |

### Joint Accuracy

- **Exact match (all 3 correct):** 68.4%
- **Hamming accuracy (per-axis average):** 85.5%
- **Within Hamming distance 1:** 91.2%

### Comparison

| Model | Exact Match | Hamming Acc |
|-------|-------------|-------------|
| Majority baseline | 12.3% | 48.1% |
| BERT-base (single head) | 54.7% | 78.3% |
| DeBERTa V5 (12 heads) | 61.2% | 82.1% |
| DeBERTa (65 heads, 12 LoRA adapters) | 68.4% | 85.5% |

---

## Falsification Protocol

C4 makes a testable prediction: the intrinsic dimension of cognitive text embeddings is approximately 3.

**Method:**
1. Embed a large corpus (>100K sentences) using a pretrained language model
2. Apply intrinsic dimension estimation (e.g., MLE, TwoNN)
3. If intrinsic dimension >> 3, C4's claim of 3-axis sufficiency is challenged
4. If intrinsic dimension is approximately 3, this is independent evidence for C4

**Current status:** Preliminary results on 10K samples suggest intrinsic dimension in range 2.8-4.2, consistent with the hypothesis but not yet conclusive. Larger-scale studies are planned.

---

## Integration with AI Systems

### As a State Representation

```python
# Pseudo-code for C4-aware agent
state = c4_classifier(observation_text) # -> (T, D, A)

if state.T == FUTURE and state.D == META:
 # Agent is in strategic planning mode
 route_to_planner()
elif state.T == PRESENT and state.D == CONCRETE:
 # Agent is in execution mode
 route_to_executor()
```

### Coverage Dashboard

For AI agents processing multi-turn conversations, track which C4 states have been visited:

```
Coverage: 14/27 states visited (51.9%)
Missing: Future-Meta quadrant, Past-System column
Recommendation: Prompt agent to consider long-term systemic perspective
```

This enables metacognitive monitoring: the agent can detect its own cognitive blind spots.

---

## Reproducing Results

Code, trained models, and evaluation scripts are available at:
`https://github.com/cognitive-functors/adaptive-topology`

### Quick Start

```bash
pip install torch transformers datasets
python evaluate.py --model c4-cognitive-adapters --data test_set.jsonl
```

---

## Open Problems

1. **Cross-lingual transfer:** Does a model trained on English generalize to other languages? (Hypothesis: yes, because C4 is language-independent.)
2. **Fine-grained recursion:** Can each of the 27 states be subdivided into 27 sub-states, as the fractal conjecture predicts?
3. **Temporal dynamics:** Modeling C4 state transitions over discourse time (sequence labeling rather than per-sentence classification).
4. **Neural correlates:** Mapping C4 states to fMRI activation patterns.

---

## References

- He, P. et al. (2021). "DeBERTa: Decoding-enhanced BERT with Disentangled Attention." ICLR 2021.
- Selyutin, I. & Kovalev, N. (2025). "C4: Complete Cognitive Coordinate System." Preprint.

---

*Contact: psy.seliger@yandex.ru / comonoid@yandex.ru*
