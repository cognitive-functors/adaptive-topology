# Papers Summary for AI Agents

Authors: Ilya Selyutin, Nikolai Kovalev
Repository: Fractal27 / articles / papers

---

## Overview

**Total papers:** 17 unique research papers across 3 directories (12 bilingual EN+RU, 5 EN-only; excluding READMEs).
**Bilingual coverage:** fractal-c4 and formal-mathematics are fully bilingual (RU + EN); algorithmic-topology is EN only.

**Central thesis:** Human cognition can be modeled as a 27-state coordinate system (C4 = Z3^3), where three axes -- Time (Past/Present/Future), Scale (Concrete/Abstract/Meta), and Agency (Self/Other/System) -- generate a complete basis for cognitive states. This coordinate system admits fractal refinement, categorical formalization via linear logic (MALL), and practical application to algorithmic optimization through the principle of adaptive routing (fingerprint-route-adapt).

**Key result:** The Adaptive Routing Theorem proves that structure-aware strategy selection always outperforms any fixed strategy, with gain proportional to environment heterogeneity. This unifies cognitive modeling (C4) and combinatorial optimization (MASTm) under one formal principle.

---

## 1. fractal-c4/ (6 RU + 6 EN papers + README)

Core papers on the C4 cognitive coordinate system and its fractal extensions. All 6 papers available in both Russian (original) and English (-en suffix).

| File (RU / EN) | Title | Summary | Keywords |
|------|-------|---------|----------|
| 01_c4-fractal.md / -en.md | C4 Fractal -- Fractal Refinement of the Coordinate System | Proposes that each of the 27 states can be recursively subdivided into 27 sub-states (yielding 729, 19683, ...), preserving algebraic structure at every level. | fractal refinement, self-similarity, recursive decomposition, granularity |
| 02_c4-knowledge.md / -en.md | C4 Knowledge -- Modeling Knowledge via Fractal Coordinates | Models knowledge not as a static graph but as a topological space of cognitive states with a metric, composition operations, and hierarchical refinement. | epistemology, knowledge topology, cognitive metric, composition |
| 03_c4-system.md / -en.md | C4 System -- Systems Thinking through Fractal C4 | Applies C4 to system dynamics and holistic cognition, modeling feedback loops, emergent properties, and multi-scale system behavior. | systems thinking, system dynamics, feedback, emergence |
| 04_c4-formalism.md / -en.md | C4 Formalism -- On Rigor and Unambiguity of C4 Descriptions | Critical self-analysis of C4's formal adequacy. Examines whether C4 coordinates add predictive power beyond post-hoc labeling, proposes operadic composition. | formalism, operads, falsifiability, meta-analysis |
| 05_c4-content.md / -en.md | C4 Content -- Structure vs. Content | Investigates the structure/content problem: C4 provides structural coordinates but does not generate semantic content autonomously. Defines conditions for content-bearing C4 descriptions. | structure-content problem, autonomy, semantic grounding |
| 06_c4-language.md / -en.md | C4 Language -- A Controlled Language with Built-in Fractal Structure | Designs a controlled dialect of Russian where C4 coordinates are embedded directly into grammatical structure, making cognitive state explicit in every utterance. | controlled language, linguistic engineering, grammar-coordinate mapping |

**Reading order:** 01 (fractal core) -> 04 (formalism) -> 02, 03, 05, 06 (applications, any order).

---

## 2. formal-mathematics/ (6 RU + 6 EN papers + README)

Categorical and type-theoretic foundations. Formalizes the mathematical substrate underlying C4 and the transformation algebra. All 6 papers available in both Russian (original) and English (-en suffix).

| File (RU / EN) | Title | Summary | Keywords |
|------|-------|---------|----------|
| functors.md / -en.md | Basic Functors of the Category Lin | Defines the system of primitive functors (Id, Const, Tensor, Par, Hom, Sum, Product, differential) for the category Lin (MALL with dependent types and (co)inductive types). Proves any polynomial endofunctor decomposes into these primitives. | category theory, endofunctors, Lin, MALL, polynomial functors |
| functors-catalog.md / -en.md | Functor Catalog for the Belief Category within C4 | Systematic catalog of cognitive functors (tau, sigma, delta, rho, iota, lambda, kappa, mu, phi) operating on the 27-state Belief category. Covers compositional rules and connection to formal verification. | Belief category, cognitive functors, Z3^3, composition rules |
| monoidal-category.md / -en.md | Monoidal Category: Differential Linear Logic with Dependent Types | Specifies the base category Lin as a symmetric monoidal category with tensor, par, additive connectives, dependent types, and a differential operator. | monoidal category, DILL, dependent types, symmetric structure |
| type-system.md / -en.md | Type System: MALL with Dependent Types, (Co)inductive Types, and Differentiation | Full type system specification extending MALL with dependent types over four linear connectives, (co)inductive types, and differentiation in the style of DILL. | type system, MALL, dependent types, coinduction, DILL |
| MILL.md / -en.md | MILL Semantics in Distributed Processes | Explains multiplicative intuitionistic linear logic (MILL) via distributed process semantics: types as interaction protocols, proofs as processes, tensor as parallel composition. | MILL, process semantics, true concurrency, protocols |
| par-explanation.md / -en.md | Duality and Linear Implication: Par Explained | Tutorial on the Par connective, duality (A-perp), and linear implication (A -o B). Establishes the identity A-perp -o B = A par B. | Par, duality, linear implication, MALL connectives |

**Reading order:** monoidal-category.md -> type-system.md -> functors.md -> functors-catalog.md -> MILL.md -> par-explanation.md.

---

## 3. algorithmic-topology/ (5 EN papers + README)

The MASTm (Multi-scale Adaptive Spectral TSP meta-solver) and the Fingerprint-Route-Adapt (FRA) principle connecting optimization to cognitive theory. English only.

| File | Title | Summary | Keywords |
|------|-------|---------|----------|
| 00-mast-instance-adaptive-tsp.md | MASTm: Instance-Adaptive Spectral Decomposition for Large-Scale TSP | Presents MASTm v6.6, a six-stage meta-solver: 7D fingerprint -> router -> spectral decomposition -> parallel ILS -> stitching -> V-cycle refinement + EAX. Achieves 0.62% median gap on TSPLIB with O(N*k) memory. | TSP, MASTm, spectral decomposition, fingerprinting, metaheuristic, ILS, EAX |
| 01-universal-fingerprint-protocol.md | Universal Fingerprint Protocol for Adaptive Strategy Selection | Domain-independent protocol with five abstract axes (heterogeneity, decomposability, clustering, density, dynamics). Instantiated in TSP (MASTm), cognition (C4), and AI agent routing. Proves polynomial overhead and bounded regret. | fingerprint protocol, strategy selection, adaptive routing, bounded regret |
| 02-from-cognitive-coordinates-to-combinatorial-optimization.md | From Cognitive Coordinates to Combinatorial Optimization: A Unified Theory of Adaptive Routing | Unifies C4 and MASTm under the Fingerprint-Route-Adapt (FRA) principle. Connects FRA to No Free Lunch theorem, proposes intelligence = fingerprint quality * strategy repertoire size. | FRA principle, unified theory, No Free Lunch, intelligence measure, P vs NP |
| 03-adaptive-routing-theorem.md | The Adaptive Routing Theorem: A Formal Proof That Structure Predicts Strategy | Three theorems: (1) Partitioning Bound, (2) Heterogeneity Bound (adaptive > fixed iff H(F) > 0), (3) Monotonicity of Refinement. Includes Agda proof sketch. Connects to formal definition of intelligence. | adaptive routing, formal proof, heterogeneity, Agda, monotonicity |
| 04-cross-domain-evidence.md | Cross-Domain Evidence for Adaptive Routing: 32 Systems, 6 Domains, 80+ Citations | Survey of 32 systems across neuroscience, biology, CS, economics, ecology, and engineering that all implement fingerprint-route-adapt. Argues adaptive routing is an optimal structural motif, not just a heuristic. | cross-domain evidence, literature survey, 32 systems, universal pattern |

**Reading order:** 00 (concrete instantiation) -> 01 (abstract protocol) -> 02 (unified theory) -> 03 (formal proof) -> 04 (empirical evidence).

---

## Cross-Reference Map

The papers form a dependency graph with two roots (C4 cognitive theory and MASTm algorithmic solver) that merge into a unified framework:

```
fractal-c4/01-06 (fractal core, formalism, applications) [RU + EN]
    |
    +-- formal-mathematics/* (categorical foundations for C4) [RU + EN]
    |       |
    |       +-- functors.md -> functors-catalog.md (Lin -> Belief)
    |       +-- monoidal-category.md -> type-system.md (base structure)
    |
    +-- algorithmic-topology/02 (unified theory connecting C4 and MASTm) [EN]
            |
            +-- algorithmic-topology/00 (MASTm: concrete TSP solver)
            +-- algorithmic-topology/01 (universal fingerprint protocol)
            +-- algorithmic-topology/03 (adaptive routing theorem -- formal proof)
            +-- algorithmic-topology/04 (cross-domain evidence -- 32 systems)
```

**Key bridges between paper groups:**

| From | To | Connection |
|------|----|------------|
| fractal-c4/04 (Formalism) | formal-mathematics/functors.md | C4 operadic structure uses Lin category functors |
| fractal-c4/01 (Fractal) | algorithmic-topology/03 (Routing Theorem) | Fractal refinement enables the reachability bound |
| algorithmic-topology/00 (MASTm) | algorithmic-topology/01 (Fingerprint Protocol) | MASTm is the TSP instantiation of the universal protocol |
| algorithmic-topology/02 (Unified Theory) | fractal-c4/ | FRA principle as practical definition of intelligence |
| algorithmic-topology/03 (Routing Theorem) | algorithmic-topology/04 (Evidence) | Theorem provides formal basis; evidence paper validates empirically |

---

## Recommended Reading Orders

### For cognitive scientists and psychologists
1. fractal-c4/01_c4-fractal.md (fractal refinement)
2. fractal-c4/03_c4-system.md (systems thinking)
3. algorithmic-topology/03-adaptive-routing-theorem.md (central proof)

### For mathematicians and formal verification researchers
1. formal-mathematics/monoidal-category.md (base category)
2. formal-mathematics/type-system.md (type system)
3. formal-mathematics/functors.md (functor basis)
4. formal-mathematics/functors-catalog.md (cognitive instantiation)
5. algorithmic-topology/03-adaptive-routing-theorem.md (main theorem)

### For computer scientists and algorithm designers
1. algorithmic-topology/00-mast-instance-adaptive-tsp.md (concrete solver)
2. algorithmic-topology/01-universal-fingerprint-protocol.md (abstract protocol)
3. algorithmic-topology/03-adaptive-routing-theorem.md (formal proof)
4. algorithmic-topology/02-from-cognitive-coordinates-to-combinatorial-optimization.md (unified theory)
5. algorithmic-topology/04-cross-domain-evidence.md (validation)

### For philosophers and consciousness researchers
1. fractal-c4/04_c4-formalism.md (formal adequacy critique)
2. fractal-c4/05_c4-content.md (structure vs content)
3. algorithmic-topology/03-adaptive-routing-theorem.md (central proof)

### Minimal path (3 papers for the full picture)
1. algorithmic-topology/00-mast-instance-adaptive-tsp.md -- What MASTm is
2. algorithmic-topology/02-from-cognitive-coordinates-to-combinatorial-optimization.md -- How C4 and MASTm unify
3. algorithmic-topology/03-adaptive-routing-theorem.md -- The central proof

---

## Live Demo & Pretrained Models

| Resource | URL | Description |
|----------|-----|-------------|
| Interactive Demo | https://c4cognitive.com | Real-time C4 classification, 27-state space exploration |
| Pretrained Adapters | https://huggingface.co/HangJang/c4-cognitive-adapters | 12 LoRA adapters (65 heads) for mDeBERTa-v3-base, PyTorch + ONNX |

---

## Glossary of Core Terms

| Term | Definition |
|------|-----------|
| C4 | Complete Cognitive Coordinate System, Z3^3 = 27 states |
| T, D, A | Time, Scale, Agency -- the three C4 axes |
| Z3^3 | Direct product of three copies of the cyclic group of order 3 |
| MASTm | Multi-scale Adaptive Spectral TSP meta-solver |
| FRA | Fingerprint-Route-Adapt principle |
| Lin | Base category of differential linear logic with dependent types |
| MALL | Multiplicative-Additive Linear Logic |
| DILL | Differential Intuitionistic Linear Logic |
| Belief category | Category of cognitive states with C4 coordinates |
