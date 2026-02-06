# C4: Complete Cognitive Coordinate System

[![License: Triple](https://img.shields.io/badge/License-Apache--2.0--NC%20%7C%20AGPL--3.0%20%7C%20Commercial-orange)](./LICENSE)
[![Agda Verified](https://img.shields.io/badge/Agda_Verified-10%2F11_theorems-green)](./formal-proofs/)
[![Papers](https://img.shields.io/badge/Papers-17_papers-blue)](./papers/)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue)](./code/)
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
> validated by a phenomenological proof ([The Koan of Awakening](papers/c4-awakening-koan-en.md)),
> and a hint at the hidden fourth dimension. See **[about/WHY-C4.md](about/WHY-C4.md)** for the full explanation.

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
| `papers/` | 20+ papers (EN+RU) | All research papers including fractal-c4, formal-mathematics, algorithmic-topology |
| `experiments/` | FRA, ID3 | Hypothesis validation experiments with reproducibility packages |
| `guides/` | 7 EN + 7 RU guides | Entry points for different audiences (AI researchers, linguists, philosophers) |
| `code/` | mast, c4-classifier, agda | Run-ready implementations and formal proofs |
| `start-here/` | EN + RU | Plain-language introductions (FOR-EVERYONE + popular intros) |
| `applications/` | functor-agents | Practical applications of C4 theory |
| `formal-proofs/` | Agda proofs | Verification guides and verified theorems |
| `visualizations/` | EN + RU | Interactive 3D hypercube (HTML/JavaScript) |
| `about/` | WHY-C4, TOPICS, llms.txt | Meta-documentation and AI-readable descriptions |

**Total:** 20+ research papers (bilingual EN+RU), 14 bilingual guides, run-ready code with benchmark data and experimental results.

---

## Quick Start

**New here?** Start with **[FOR-EVERYONE](start-here/FOR-EVERYONE-en.md)** — a plain-language explanation of what C4 is, what we proved, and why it matters for you (no math required).

Then:
1. Explore **`guides/`** for entry points matching your background (mathematician, cognitive scientist, engineer, philosopher).
2. Dive into **`papers/`** for formal treatments and proofs.
3. Check **`experiments/`** for reproducible hypothesis validation.

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
- **FRA Scaling validated** -- FRA (Fingerprint-Route-Adapt) routing achieves up to +44%
  improvement over Single Best Solver on ASlib benchmarks when diversity > 50%.
  Key finding: K_min = n_types (step function, not power law). Wilcoxon p = 0.0002.
  See `experiments/fra-scaling/` for reproducibility package and `papers/fra-scaling-en.md` for the paper.
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

Machine-readable project description is available at [about/llms.txt](./about/llms.txt).

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
