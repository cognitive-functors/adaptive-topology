# C4: Complete Cognitive Coordinate System

[![License: Triple](https://img.shields.io/badge/License-Apache--2.0--NC%20%7C%20AGPL--3.0%20%7C%20Commercial-orange)](./LICENSE)
[![Agda Verified](https://img.shields.io/badge/Agda_Verified-10%2F11_theorems-green)](./formal-proofs/)
[![Papers](https://img.shields.io/badge/Papers-17_papers-blue)](./papers/)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue)](./code/python/)
[![HuggingFace](https://img.shields.io/badge/%F0%9F%A4%97_HuggingFace-Models_on_HF_Hub-yellow)](https://huggingface.co/HangJang/c4-cognitive-adapters)
[![Demo](https://img.shields.io/badge/Demo-Live_Demo-brightgreen)](https://c4cognitive.com)

**Adaptive routing as a model of intelligence in structured state space.**

---

## What is C4

C4 is a formal framework that models cognition as navigation through a 27-element
state space Z3^3, structured by three orthogonal axes: **Time** (Past / Present / Future),
**Scale** (Concrete / Abstract / Meta), and **Agency** (Self / Other / System).
The framework provides an algebraic foundation for cognitive modeling,
with 11 core theorems -- 10 of which have been formally verified in Agda.

> **Why "C4"?** The name encodes four layers of meaning: a letter-based abbreviation (CCCS → C4),
> an allusion to detonating the combinatorial explosion problem, a completeness claim
> validated by a phenomenological proof ([The Koan of Awakening](preprint/en/C4-AWAKENING-KOAN-v3.6.md)),
> and a hint at the hidden fourth dimension. See **[WHY-C4.md](WHY-C4.md)** for the full explanation.

Most content is available in both English and Russian.

---

## Central Thesis: The Adaptive Routing Theorem

Any system that (1) fingerprints its input into a structured state space,
(2) routes execution to a strategy matched to that fingerprint, and
(3) adapts its execution based on feedback will outperform any fixed strategy
over a sufficiently diverse set of inputs.

This theorem connects results across combinatorial optimization, machine learning,
cognitive science, and decision theory under a shared formal framework.

---

## Repository Structure

| Directory | Contents | Description |
|-----------|----------|-------------|
| `papers/fractal-c4/` | 6 RU + 6 EN papers + README | Core C4 theory: Z3^3 group, Hamming metric, routing |
| `papers/formal-mathematics/` | 6 RU + 6 EN papers + README | Agda proofs, functors, categorical semantics |
| `papers/algorithmic-topology/` | 5 EN papers + README | MASTm TSP solver, fingerprint protocol |
| `preprint/` | 7 EN + 5 RU files | Full preprint (English and Russian editions) |
| `guides/` | 7 EN + 7 RU guides + README + SUMMARY-FOR-AI | Entry points for different audiences |
| `applications/functor-agents/` | 2 RU + 2 EN files | Functor-based AI agents |
| `code/mast/` | solver + 12 benchmarks + results | Run-ready MASTm (Multi-scale Adaptive Spectral TSP meta-solver) |
| `code/agda/` | 1 file | Agda formal proofs |
| `code/python/` | demo + ID-3 experiment + examples | C4 classifier, ID-3 validation (10-phase experiment), examples |
| `formal-proofs/` | 3 files | Agda proofs + verification guide |
| `start-here/` | EN + RU | Popular introductions |
| `visualizations/` | EN + RU | Interactive 3D hypercube (HTML/JavaScript) |
| `WHY-C4.md` | bilingual | Why the framework is called "C4" — four layers of meaning |

**Total:** 19 unique research papers (14 bilingual EN+RU, 5 EN-only), 14 bilingual guides,
4 bilingual application docs, run-ready code with benchmark data and experimental results.

---

## Quick Start

1. Start with **`guides/`** -- choose the entry point that matches your background
   (mathematician, cognitive scientist, engineer, philosopher, or general reader).
2. Read the **`preprint/`** for the complete formal treatment.
3. Explore **`papers/`** for individual results and proofs.

---

## Key Results

- **Z3^3 group structure** -- 27 cognitive states forming a finite Abelian group
  with well-defined composition and Hamming distance metric.
- **11 theorems** -- 10 formally verified in Agda, covering reachability,
  completeness, and optimality of adaptive routing.
- **Reachability** -- any cognitive state is reachable from any other in at most 6 steps.
- **Hypothesis ID-3 confirmed** -- the intrinsic dimensionality of the C4-supervised
  cognitive subspace is 3.07 [95% CI: 2.91--3.15] at N=5000, consistent with Z3^3.
  Robust across 3 embedding models, 2 languages (EN/RU), and multiple datasets.
  Hamming distance in Z3^3 predicts inter-state confusion (r = -0.489).
  See `papers/ID3-INTRINSIC-DIMENSIONALITY-en.md` for the full study.
- **MASTm solver** -- MASTm (Multi-scale Adaptive Spectral TSP meta-solver):
  algorithmic topology approach to TSP achieving 0.22% optimality gap on fl3795 benchmark.
- **Cross-domain applicability** -- the same fingerprint-route-adapt pattern yields
  improvements across optimization, NLP, decision-making, and cognitive modeling.

---

## Limitations

- C4 is a **mathematical model**, not a claim about how the brain works at the neural level.
- Empirical validation of ID-3 uses AI-generated labels (c4factory); human annotation studies are needed.
- The Time axis is not decodable from current sentence-transformers (Scale >> Agency >> Time).
- Minimality of the 3-dimensional structure (Conjecture 2) remains unproven in Agda.
- Cross-domain results are promising but do not establish that cognition *is* routing -- only that routing is a useful modeling lens.

---

## Live Demo & Pretrained Models

- **Interactive Demo:** [c4cognitive.com](https://c4cognitive.com) -- real-time C4 classification, 27-state space exploration, LLM-powered cognitive analysis
- **Pretrained Adapters:** [HuggingFace Hub](https://huggingface.co/HangJang/c4-cognitive-adapters) -- 12 LoRA adapters (65 classification heads) for mDeBERTa-v3-base, PyTorch + ONNX formats

---

## For AI Agents

Machine-readable project description is available at [llms.txt](./llms.txt).

---

## License

This work is available under a **triple license**:

- **Apache-2.0-NC** -- free for research, education, and personal use
- **AGPL-3.0** -- free for open-source projects with copyleft obligation
- **Commercial** -- paid license for proprietary and SaaS use

See [LICENSE](./LICENSE) for details.

---

## Authors

- **Ilya Selyutin** -- psy.seliger@yandex.ru
- **Nikolai Kovalev** -- comonoid@yandex.ru

---

## Citation

If you use this work in academic research, please cite using the metadata
in [CITATION.cff](./CITATION.cff).

---

Copyright 2024-2026 Ilya Selyutin, Nikolai Kovalev and contributors.
