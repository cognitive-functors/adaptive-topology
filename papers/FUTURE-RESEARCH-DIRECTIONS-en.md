# Future Research Directions

## C4 + MASTm + Adaptive Routing Theorem: What's Next?

**Authors:** Ilya Selyutin, Nikolai Kovalev
**Status:** Living document (updated as progress is made)
**Date:** February 2026

---

## TL;DR

Building on two independent research lines — the C4 cognitive coordinate system (Z3^3, 27 states) and the MASTm algorithmic solver for TSP — we formulated and proved the **Adaptive Routing Theorem** (Fingerprint -> Route -> Adapt), unifying results from cognitive science and combinatorial optimization. The FRA meta-pattern has been identified in 32+ independent systems across 6 domains. This document formulates **new hypotheses, open questions, and calls for collaboration** across disciplines.

---

## 1. OPEN THEOREMS AND HYPOTHESES

### 1.1 Minimality Conjecture (Conjecture 2) — LOW-HANGING FRUIT

**Status:** Not yet formalized in Agda. Essentially trivial: one needs to check only 2^3 - 1 = **7 proper subsets** of {T, D, A} and show that none of them generates all 27 states.

**Statement:** No proper subset of the operators {T, D, A} provides completeness (reachability of all 27 states).

**Why it matters:** This asserts that three dimensions are the *minimum necessary* representation of cognitive space. Mathematically the result is obvious (each operator acts only along its own axis; without it, the axis is "frozen"), but formal Agda verification would complete the proof base.

**Priority:** More of a formality than a research problem. Exhaustive enumeration of 7 cases is a day's work for an Agda developer.

---

### 1.2 Fractal Recursion Hypothesis (Conjecture 3)

**Statement:** Each of the 27 basis states can be recursively subdivided along the same three axes (T, D, A), producing a hierarchy:
- Level 1: 27 states
- Level 2: 729 states
- Level n: 27^n states

**Open questions:**
1. **Which algebraic structure is adequate?** Direct product Z3^3 x Z3^3? Tensor product? Free operad?
2. **Do levels commute?** Is F<Past,Concrete,Self>[Present,Meta,Self] the same as F<Present,Meta,Self>[Past,Concrete,Self]? Intuition says no.
3. **Does a natural measure exist on the fractal?** Prediction: power law (Zipf distribution) — most time is spent in a few "hub" states.
4. **How many levels do people actually use?** Hypothesis: 2-3 levels (working memory constraint of 4 +/- 1 chunks).

**Call to:**
- Algebraic topologists — formalization of operadic structure
- Cognitive neuroscientists — experimental level discrimination (reaction time, EEG patterns)
- Contemplative practitioners — meditative traditions may provide data on deeper recursion levels

---

### 1.3 Intrinsic Dimensionality Hypothesis (Hypothesis ID-3) — **CONFIRMED**

**Statement:** The intrinsic dimensionality of cognitive text embeddings is approximately 3.

**Status: CONFIRMED** (February 2026). A 10-phase experiment was conducted with 3 embedding models, 2 languages, N up to 5000.

**Key results:**

| Condition | N | Subspace ID | 95% CI | Perm p |
|-----------|---|-------------|--------|--------|
| Baseline (135 built-in) | 135 | 2.61 | — | <0.001 |
| MPNet-768d | 135 | 2.43 | — | <0.001 |
| Multilingual-384d | 135 | 2.93 | — | <0.001 |
| Controlled templates | 135 | 2.08 | — | <0.001 |
| c4factory (large-scale) | 1998 | 2.91 | — | <0.001 |
| English | 1620 | 3.14 | — | <0.001 |
| Russian | 1998 | 3.02 | — | <0.001 |
| **N=5000 (convergence)** | **4995** | **3.07** | **[2.91, 3.15]** | **<0.001** |

**Revised hypothesis (3 parts):**
- **H1 (confirmed):** cognitive texts occupy a statistically significant subspace (all p < 0.001)
- **H2 (confirmed):** C4-supervised 3D projection has ID ≈ 3.0 — robust across models, languages, datasets
- **H3 (partial):** three axes have unequal decodability: Scale >> Agency >> Time

**Additional findings:**
- Hamming distance in Z₃³ predicts confusion (r = −0.489) — topology is preserved
- Time axis is NOT decodable from sentence-transformers (R² < 0) — a property of NLP models, not C4
- Stability: subspace ID = 2.954 ± 0.069 across 5 independent seeds
- Per-axis slice: fixing one axis → ID ≈ 2.0 (as predicted by Z₃²)

**Full report:** `papers/ID3-INTRINSIC-DIMENSIONALITY-en.md`
**Code:** `experiments/id3/run_experiment.py`
**Data:** `experiments/id3/results/`

---

### 1.4 FRA Scaling Conjecture for NP-Hard Problems

**Statement:** For any NP-hard problem and gap epsilon > 0, there exist fingerprint dimension d and strategy count K such that FRA achieves gap < epsilon on a (1 - delta) fraction of instances, with K = O(1/epsilon^d) and d = O(log(1/delta)).

**Why it matters:** If true, FRA is the *practical answer to P != NP*: not solving the problem in general, but routing to the best heuristic for each specific instance.

**Call to:** Complexity theorists, algorithm portfolio researchers (SATzilla, AutoFolio, AutoML).

---

### 1.5 Strategies as Cognitive States

**New hypothesis** (not yet formalized):

> If each step of a strategy is a cognitive state in Z3^3, and Theorem 11 guarantees that any state is reachable from any other in at most 6 steps, then **any cognitive strategy is reachable from any other via a finite number of metacognitive transitions**.

**Implications:**
- A "stuck" person can *theoretically* reach any strategy in at most 6 steps via a meta-route
- Therapeutic protocol: compute a belief-path from the current strategy to the target
- This does not mean the transition is *easy* — energetic barriers may be substantial

**Call to:** Cognitive psychologists, CBT specialists, metacognition researchers.

---

## 2. NEW DIRECTIONS BY DOMAIN

### 2.1 Neuroscience

| Direction | Question | Method |
|-----------|----------|--------|
| Neural FRA | Do cortical columns implement the FRA pattern? | fMRI + multi-voxel pattern analysis |
| C4-EEG | Are the 27 states distinguishable by EEG signatures? | High-density EEG + classification |
| Hierarchical predictions | Do C4 fractal levels correspond to predictive processing tiers? | Mismatch negativity across levels |
| Attention routing | Is attention the brain's implementation of the FRA Router? | Eye-tracking + cognitive load |

**Key hypothesis:** The three C4 axes (T, D, A) map onto three distinct neural subsystems:
- T (time) -> hippocampus + medial prefrontal cortex
- D (scale) -> dorsal/ventral processing streams
- A (agency) -> mirror neurons + theory of mind network

---

### 2.2 Psychology and Psychotherapy

| Direction | Question | Method |
|-----------|----------|--------|
| C4-CBT | Are cognitive distortions attractors in Z3^3? | C4 analysis of CBT session protocols |
| Belief-path therapy | Can belief-path serve as a therapeutic route? | Clinical pilots (N >= 30) |
| C4-metaprograms | Exact mapping of NLP metaprograms <-> C4 | Correlational analysis |
| Meditation and levels | Do experienced meditators distinguish more fractal levels? | ESM: experienced vs beginners |
| Stress trajectories | Does stress narrow the C4 space to 2-3 states? | Longitudinal ESM under stress |

**Key hypothesis:** Mental health correlates with the "breadth" of used C4 subspace. Depression = being stuck in a small cluster; mania = chaotic wandering.

---

### 2.3 Linguistics and NLP

| Direction | Question | Method |
|-----------|----------|--------|
| Cross-linguistic validity | Does C4 work equally for different languages? | Multilingual classification (mDeBERTa already available) |
| Discourse navigation | Is coherent discourse a smooth path in Z3^3? | Sequence analysis of C4 coordinates in texts |
| Genre fingerprints | Do genres have characteristic C4 distributions? | Corpus analysis |
| C4 + LLM alignment | Can C4 serve as an interpretable layer for alignment? | Fine-tuning LLMs with C4-awareness |

**Key hypothesis:** Coherent text is a *smooth path* in Z3^3 (adjacent sentences differ by at most 1 in Hamming distance). Incoherent text is *jumps* across the entire space.

---

### 2.4 Combinatorial Optimization and CS

| Direction | Question | Method |
|-----------|----------|--------|
| FRA for SAT | Does fingerprint -> route work for SAT/CSP? | Adapting the MASTm approach |
| FRA for scheduling | Fingerprinting scheduling problems? | Spectral graph characteristics |
| Universal fingerprint | Does a domain-agnostic fingerprint exist? | Meta-learning across domains |
| Theoretical limits | Lower bound on FRA quality vs optimum? | Information-theoretic analysis |
| AutoML as FRA | Is AutoML (NAS, HPO) a special case of FRA? | Formal reduction |

**Key hypothesis:** *Any* successful meta-solver (SATzilla, AutoFolio, AutoML) implicitly implements FRA. This is not a coincidence but a mathematical necessity (consequence of the theorem).

---

### 2.5 Biology and Evolution

| Direction | Question | Method |
|-----------|----------|--------|
| Immune system as FRA | VDJ recombination = fingerprint; antibody = strategy; affinity maturation = adapt? | Formal mapping |
| Gene regulatory networks | Is gene expression FRA? | Transcriptomic data analysis |
| Evolution as meta-FRA | Is natural selection a meta-router? | In silico modeling |
| C3/C4/CAM photosynthesis | Literal FRA: plant fingerprints environment -> routes metabolism | Already described, needs formalization |

**Key hypothesis:** The immune system is the largest-scale FRA implementation in nature (10^9 strategies, combinatorial fingerprint).

---

### 2.6 Economics and Game Theory

| Direction | Question | Method |
|-----------|----------|--------|
| Market microstructure | Is market-making FRA? Order flow = fingerprint, strategy = bid/ask | High-frequency data analysis |
| Central banks | Is monetary policy FRA? (indicators -> rules -> adjust) | Comparing Taylor rule with FRA |
| Auction theory | Is optimal auction design = optimal FRA? | Formal reduction |
| Behavioral economics | Are cognitive biases errors in the fingerprint? | C4 analysis of problem framing |

---

### 2.7 Philosophy and Epistemology

| Direction | Question | Method |
|-----------|----------|--------|
| Koan of Awakening | Formalization as closure: "a thought about escaping C4 is in C4" | Logical analysis (modal logic?) |
| C4 and hard problem | Does C4 describe the structure of consciousness or only cognitive contents? | Philosophical analysis |
| C4 and Kant | Are T, D, A a priori forms of sensibility? | Comparative analysis |
| Model limits | What *can't* C4 describe? | Active search for counterexamples |

**Key hypothesis:** C4 describes the *structure* of cognitive content, not *quality* (qualia). It is not an answer to the hard problem, but it is the first formalization of "what can be formalized" in consciousness.

---

## 3. META-THEORETICAL DIRECTIONS

### 3.1 Category Theory and C4

**Current status:** C4-Cat is defined as a category (objects = 27 states, morphisms = paths). But connections to functors, natural transformations, and higher categories remain at the hypothesis level.

**Open questions:**
1. Is the C4 -> MASTm mapping a *functor* in the strict sense?
2. Do *natural transformations* exist between C4 representations across domains?
3. Is FRA an *adjunction* (fingerprint -| embed)?
4. Can the Yoneda lemma shed light on C4 completeness?

**Call to:** Category theorists, applied category theory researchers.

---

### 3.2 Information Theory and FRA

**New hypothesis (Information-Theoretic Characterization of FRA):**

> The quality of fingerprint F is determined by the mutual information I(F(X); S*(X)), where S* is the optimal strategy. The optimal fingerprint is a *sufficient statistic* with respect to strategy selection.

**Corollary:** The fingerprint learning problem reduces to the information bottleneck (Tishby et al., 2000):
```
min I(X; F(X))  subject to  I(F(X); S*(X)) >= beta
```

**Call to:** Information theorists, information bottleneck researchers.

---

### 3.3 Dynamical Systems and Attractors

**Hypothesis:** Cognitive strategies are attractors in a dynamical system on Z3^3. Switching between strategies is a *bifurcation*.

**Implications:**
- Some transitions are "easy" (small barrier) — adjacent attractors
- Some are "hard" (large barrier) — distant attractors
- Hamming distance <= 6 is the *structural* upper bound, but the *energetic* barrier may be larger

**Call to:** Nonlinear dynamical systems researchers, computational neuroscientists.

---

### 3.4 Quantum Analogies (Speculative)

**Observation:** Z3^3 is isomorphic to qutrit x qutrit x qutrit. Each axis is a qutrit (3-level quantum system).

**Questions:**
- Does "superposition" of cognitive states exist? (A distribution over 27 states ~= a quantum state?)
- Is "observation" (introspection) analogous to wavefunction collapse?
- Is there cognitive "entanglement" between axes?

**Important caveat:** This is an *analogy*, not a claim about the quantum nature of consciousness. The value lies in the mathematical apparatus (tensor products, operators, spectral decompositions), not in physical interpretation.

---

## 4. CALL TO THE RESEARCH COMMUNITY

### 4.1 What Is Needed for the Next Stage

| Priority | Task | Who is needed | Difficulty |
|----------|------|---------------|------------|
| **Green: Formality** | Prove Conjecture 2 (minimality) in Agda — enumeration of 7 cases | Agda developer | Trivial |
| **Red: Critical** | Large-scale empirical validation of C4 (N >= 500) | Cognitive psychologist + NLP | Medium |
| **Yellow: Important** | Intrinsic dimensionality estimation of embeddings | NLP researcher | Medium |
| **Yellow: Important** | FRA for SAT/CSP (porting the MASTm approach) | Optimization researcher | High |
| **Yellow: Important** | Neuroimaging of 27 states | Cognitive neuroscientist + fMRI | High |
| **Green: Promising** | Formalization of operadic structure | Algebraic topologist | High |
| **Green: Promising** | C4-CBT clinical pilot | Clinical psychologist | Medium |
| **Green: Promising** | Meta-analysis of AutoML as FRA | ML researcher | Medium |
| **White: Speculative** | Quantum-information formalization | Quantum information scientist | Very high |
| **White: Speculative** | C4 and the hard problem of consciousness | Philosopher | Conceptual |

---

### 4.2 What We Offer the Community

1. **Open data:** All 17 papers, code, benchmarks, models — open (Apache-2.0-NC / AGPL-3.0)
2. **Ready models:** 12 LoRA adapters for DeBERTa on HuggingFace — experiments can start today
3. **Formal proofs:** Agda code is reproducible — can be verified and extended
4. **Live demo:** c4cognitive.com — try it hands-on
5. **This document:** A concrete list of hypotheses with verification methods — ready to test

---

### 4.3 Potential Grant Directions

| Program | Direction | Argument |
|---------|-----------|----------|
| Cognitive science research | C4 as a formal model of cognition | First verified algebra of cognition |
| CS/optimization grants | FRA for NP-hard problems | Practical alternative to No Free Lunch |
| Neuroscience (fMRI) | Neural correlates of 27 states | Testable predictions |
| Clinical psychology | C4-CBT | Formalization of therapeutic trajectories |
| Interdisciplinary | FRA meta-pattern across 6 domains | Theory unification |

---

## 5. PROGRESS METRICS

How to measure forward movement:

| Metric | Current | Goal (1 year) | Goal (3 years) |
|--------|---------|---------------|-----------------|
| Theorems in Agda | 10/11 | 11/11 + fractal | 15+ |
| Empirical validation N | ~50 (informal) | 500+ | 5000+ |
| Domains with FRA confirmation | 6 (32 systems) | 8+ | 10+ |
| NP-hard problems with FRA | 1 (TSP) | 3 (+ SAT, scheduling) | 5+ |
| Publications (peer-reviewed) | 0 (preprint) | 2-3 | 5-10 |
| Citations | — | 10+ | 50+ |

---

## 6. PHILOSOPHICAL EPILOGUE

We started with two different tasks — modeling cognition and solving the travelling salesman problem. We discovered that both implement the same meta-pattern. We then found the same pattern in 32 independent systems. This cannot be coincidence.

Our hypothesis: **FRA is not one of many possible approaches to intelligence. It is the only approach that works in heterogeneous environments.** The Partitioning Bound (Theorem 1) proves this: if the environment is heterogeneous, adaptive routing *mathematically guarantees* superiority over any fixed strategy.

The next question: **is this a mathematical law or merely a powerful heuristic?** The answer depends on whether we can prove the FRA Scaling Conjecture. If so, FRA will become a *theorem about the nature of problem-solving*, analogous to thermodynamic laws for the world of strategies.

> *"The pattern which connects is a metapattern."*
> — Gregory Bateson

---

## See Also

- [WHY-C4.md](../about/WHY-C4.md) — four layers of meaning in the name C4
- [Adaptive Routing Theorem](algorithmic-topology/03-adaptive-routing-theorem.md) — formal proof
- [Cross-Domain Evidence](algorithmic-topology/04-cross-domain-evidence.md) — 32 systems across 6 domains
- [Koan of Awakening (EN)](c4-awakening-koan-en.md) | [(RU)](c4-awakening-koan-ru.md) — phenomenological proof
- [Fractal C4](fractal-c4/01_c4-fractal-en.md) — recursive structure
- [Multi-Domain FRA Table](FRA-CROSS-DOMAIN-TABLE-en.md) — FRA pattern across 15+ domains

---

Copyright 2024-2026 Ilya Selyutin, Nikolai Kovalev and contributors.
