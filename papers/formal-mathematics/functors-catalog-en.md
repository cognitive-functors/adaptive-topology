# Catalog of Functors of the Belief Category within the C4 Coordinate System

## Introduction

This document presents a systematic catalog of functors acting in the **Belief** category -- the category of cognitive states and transformations in the C4 coordinate system (Z_3^3 = 27 states).

The catalog supplements the document **functors.md**, which describes the basic functors of the **Lin** category (differential linear logic with dependent types, MALL connectives, and (co)inductive types). The present document focuses on applied cognitive functors, their compositional rules, and connections to formal verification.

**Context:**
- The C4 coordinate system defines the cognitive space through three axes (T, D, A)
- Each axis takes values from Z_3 = {0, 1, 2}
- MALL connectives (tensor, par, additive conjunction &, additive disjunction) provide the formal structure
- Fixed-point functors (mu, nu) define recursive cognitive patterns
- Nine basic functors (tau, sigma, delta, rho, iota, lambda, kappa, mu, phi) form a minimal and complete basis

**Authors:** Ilya Selyutin, Nikolai Kovalev

---

## 1. Axes of the C4 Coordinate System

### 1.1. Temporal Axis T (TimeOrientation)

#### 1.1.1. Structure
- **Past(0)**: retrospective cognitive states
- **Present(1)**: actual cognitive states, immediate perception
- **Future(2)**: prospective cognitive states, forecasting

#### 1.1.2. Cyclic Shift
- **shift-time**: Past -> Present -> Future -> Past (period 3)
- Formally verified: `lemma-time-cycle : forall t -> shift-time (shift-time (shift-time t)) = t`

### 1.2. Scale Axis D (ScaleLevel)

#### 1.2.1. The Concrete Level
- **Specific(0)**: concrete objects (facts, observations, sensory data)
- **Abstract(1)**: abstract categories (classes, generalizations, regularities)

#### 1.2.2. The Meta Level
- **Meta(2)**: meta-cognitive operations (reflection upon abstractions)
- **shift-scale**: Specific -> Abstract -> Meta -> Specific (period 3)

### 1.3. Agency Axis A (AgencyPosition)

#### 1.3.1. Agency Positions -- Subject (Self)
- **Self(0)**: first person, one's own perspective; subject position
- **Other(1)**: second person, interlocutor's perspective; object position

#### 1.3.2. Agency Positions -- System
- **System(2)**: third person, systemic perspective; suprasystemic position
- **shift-agency**: Self -> Other -> System -> Self (period 3)

### 1.4. State Space

The complete space is defined as a Cartesian product:

#### 1.4.1. State Definition
- **Functor_27**: a record with fields time : TimeOrientation, scale : ScaleLevel, agency : AgencyPosition
- Notation: F(t, s, a) where t in {0,1,2}, s in {0,1,2}, a in {0,1,2}

#### 1.4.2. Examples of Elementary States
- **F(0,0,0)** = Past-Specific-Self: a concrete first-person memory
- **F(1,1,1)** = Present-Abstract-Other: a current abstract representation of another
- **F(2,2,2)** = Future-Meta-System: a prognostic meta-reflection at the systemic level

#### 1.4.3. Total Number of States
- |Z_3^3| = 27 distinct cognitive states
- Each state is an object of the **Belief** category
- Morphisms between states are cognitive transformations

---

## 2. Nine Basic Functors

### 2.1. Temporal Functor tau

#### 2.1.1. Definition
- **tau** : Belief -> Belief
- Action: F(t, s, a) |-> F(shift-time(t), s, a)
- Preserves axes D and A, cyclically shifts axis T

#### 2.1.2. Properties
- Period: tau^3 = Id (three applications return to the initial state)
- Invariant I_tau: causal structure (partial temporal order)
- Inverse: tau^{-1} = tau^2

#### 2.1.3. Examples
- tau(Past-Specific-Self) = Present-Specific-Self (actualization of a memory)
- tau(Present-Abstract-Other) = Future-Abstract-Other (forecast of abstract behavior of another)
- tau^2(Future-Meta-System) = Past-Meta-System (retrospective systemic reflection)

#### 2.1.4. Formal Verification (Agda)
- Module: `c4-comp-v5.agda`, function `apply-T`
- Cyclicity lemma: `lemma-time-cycle`
- Distance: `time-dist : TimeOrientation -> TimeOrientation -> Nat`

### 2.2. Integration Functor sigma

#### 2.2.1. Definition
- **sigma** : Belief x Belief -> Belief
- Action: sigma(A, B) = tensor product of cognitive states A (x) B
- Categorical interpretation: a bifunctor realizing the multiplicative product

#### 2.2.2. Properties
- Associativity: sigma(sigma(A, B), C) = sigma(A, sigma(B, C))
- Commutativity: sigma(A, B) = sigma(B, A) (up to isomorphism)
- Unit: sigma(A, 1) = A
- Invariant I_sigma: sum of informational content (additivity)

#### 2.2.3. Cognitive Interpretation
- Binding disparate pieces of knowledge into a coherent structure
- Integration of perspectives: sigma(Self-view, Other-view) = comprehensive understanding
- Analogue in MALL: tensor product (x) -- parallel composition of resources

### 2.3. Differential Functor delta

#### 2.3.1. Definition
- **delta** : Belief -> Belief x Belief
- Action: delta(A (x) B) = (A, B) -- decomposition of a tensor into components
- Categorical interpretation: a comonoid operation (splitting)

#### 2.3.2. Properties
- Duality with sigma: delta o sigma ~ Id (up to natural transformation)
- Invariant I_delta: multiplicative structure -- decomposability
- Does not lose information; merely reveals a hidden decomposition

#### 2.3.3. Cognitive Interpretation
- Analytical decomposition: separating the complex into its constituents
- Distinction: isolating individual aspects from a whole
- Analogue in MALL: destructuring of the tensor product

### 2.4. Replication Functor rho

#### 2.4.1. Additive Replication
- **rho(&)** : Belief -> Belief & Belief -- copying with additive conjunction
- Defines a choice: both copies are available; one is consumed

#### 2.4.2. Multiplicative Replication
- **rho(x)** : Belief -> Belief (x) Belief -- parallel duplication
- Both copies exist and are consumed simultaneously

#### 2.4.3. Cognitive Interpretation
- Transfer of a pattern to a new context without loss of the original
- Creation of multiple instantiations of a single cognitive model
- Connection to the diagonal functor: Delta(A) = (A, A)

### 2.5. Inversion Functor iota

#### 2.5.1. Definition
- **iota** : Belief -> Belief^{op}
- Action: reversal of the direction of all morphisms (contravariance)
- Categorical interpretation: passage to the dual (opposite) category

#### 2.5.2. Properties
- **Involution**: iota o iota = Id (double reversal returns to the original)
- This is the only involutive functor in the basis
- Connection to linear negation: iota(A) ~ A^{perp}

#### 2.5.3. Cognitive Interpretation
- Reframing through reversal: perceiving the opposite interpretation
- Dualization: if A = "cause," then iota(A) = "effect"
- In MALL: linear negation (A (x) B)^{perp} = A^{perp} par B^{perp}

### 2.6. Abstraction Functor lambda

#### 2.6.1. Definition
- **lambda** : Belief_{detailed} -> Belief_{abstract}
- Action: forgetful functor, discarding structure

#### 2.6.2. Properties
- Preserves universal properties: lambda(lim X_i) = lim lambda(X_i)
- Invariant I_lambda: commutativity of universal property diagrams
- Has a left adjoint: kappa (concretization)
- Adjunction: Hom(lambda(A), B) = Hom(A, kappa(B))

#### 2.6.3. Cognitive Interpretation
- Ascent along axis D: Specific -> Abstract -> Meta
- Generalization: "oak, maple, pine" |-> "trees"
- Loss of detail with preservation of structural invariants

### 2.7. Concretization Functor kappa

#### 2.7.1. Definition
- **kappa** : Belief_{abstract} -> Belief_{detailed}
- Action: free functor, generating structure

#### 2.7.2. Properties
- Left adjoint to lambda: kappa -| lambda
- Invariant I_kappa: satisfiability of abstract properties
- Instantiation: from a set of symbols, generates all admissible combinations

#### 2.7.3. Cognitive Interpretation
- Descent along axis D: Meta -> Abstract -> Specific
- Generation of concrete examples from an abstract rule
- Deductive inference: general law |-> specific case

### 2.8. Meta-Functor mu

#### 2.8.1. Definition
- **mu** : Fun(Belief, Belief) -> Fun(Belief, Belief)
- Action: applies a functorial operation to the category of functors
- Categorical interpretation: an endofunctor on the category of endofunctors

#### 2.8.2. Properties
- Fixed point: mu(F) = F (self-reference)
- The only functor acting on the category of functors
- Invariant I_mu: reflexive structure

#### 2.8.3. Cognitive Interpretation
- Metacognition: thinking about thinking
- Self-reference: analysis of one's own cognitive strategies
- Connection to fixed points mu and nu from **Lin**

### 2.9. Modulation Functor phi

#### 2.9.1. Definition
- **phi** : Belief x Context -> Belief
- Action: F(A, ctx) = adaptation of cognitive state A to context ctx
- Categorical interpretation: a dependent functor (parameterized by context)

#### 2.9.2. Properties
- The kernel is invariant: ker(phi(A, ctx_1)) = ker(phi(A, ctx_2))
- Contextual dependency: the only functor with an explicit context parameter
- Invariant I_phi: kernel of the object under change of context

#### 2.9.3. Cognitive Interpretation
- Contextualization: the same piece of knowledge changes meaning depending on circumstances
- Modality: transforming "A is true" into "A is possible" or "A is necessary"
- Analogue in MALL: dependent types (Sigma, Pi)

---

## 3. Composition Rules for Functors

Composition of basic functors generates cognitive transformations of arbitrary complexity. The order of composition is essential: in general, F o G != G o F.

### 3.1. Sequential Composition (Vertical)

For functors F, G : Belief -> Belief, the composition is defined:

```
(G o F)(A) = G(F(A))
(G o F)(f) = G(F(f))
```

**Properties:**
- Associativity: (H o G) o F = H o (G o F)
- Unit: Id o F = F o Id = F
- Non-commutativity: lambda o delta != delta o lambda (in general)

### 3.2. Parallel Composition (Tensorial)

For functors F, G : Belief -> Belief, the tensor product is defined:

```
(F (x) G)(A) = F(A) (x) G(A)
```

**Properties:**
- Symmetry: F (x) G = G (x) F (up to isomorphism)
- Associativity: (F (x) G) (x) H = F (x) (G (x) H)
- Unit: K_1 (x) F = F
- Distributivity over (direct sum): F (x) (G (direct sum) H) = (F (x) G) (direct sum) (F (x) H)

### 3.3. Additive Compositions

#### 3.3.1. Additive Conjunction (&)
- **(F & G)(A)** = F(A) & G(A) -- choice between two results
- Projections: pi_1 : F & G => F, pi_2 : F & G => G (natural transformations)
- Universal property: for sigma_1 : H => F and sigma_2 : H => G there exists <sigma_1, sigma_2> : H => F & G

#### 3.3.2. Additive Disjunction (direct sum)
- **(F (direct sum) G)(A)** = F(A) (direct sum) G(A) -- tagged choice of variant
- Injections: iota_1 : F => F (direct sum) G, iota_2 : G => F (direct sum) G
- Universal property: for sigma_1 : F => H and sigma_2 : G => H there exists [sigma_1, sigma_2] : F (direct sum) G => H

### 3.4. Axis Operator Compositions

The operators T, D, A cyclically shift values along their respective axes. Their compositions form the commutative group Z_3 x Z_3 x Z_3.

#### 3.4.1. Basic Rules
- **T o T o T** = Id (cycle along axis T)
- **D o D o D** = Id (cycle along axis D)
- **A o A o A** = Id (cycle along axis A)

#### 3.4.2. Commutativity of Axes
- **T o D = D o T** (shifts along different axes commute)
- **T o A = A o T**
- **D o A = A o D**

#### 3.4.3. Canonical Path Form
- Any path reduces to canonical form: T^a o D^b o A^c, where a, b, c in {0, 1, 2}
- Formal verification: `belief-path` in `c4-comp-v5.agda`

### 3.5. Differential Composition

The differentiation operator partial lifts to the functor level:

#### 3.5.1. Differentiation Rules
- **partial(Id)** = K_1 (the derivative of the identity functor is constant)
- **partial(K_C)** = K_0 (the derivative of a constant is zero)
- **partial(F (x) G)** = (partial(F) (x) G) (direct sum) (F (x) partial(G)) (Leibniz rule)
- **partial(G o F)** = (partial(G) o F) (x) partial(F) (chain rule)

#### 3.5.2. Cognitive Interpretation of Differentiation
- partial(F)(A) describes a "one-hole context" -- a minimal local change
- The derivative of a cognitive functor = the sensitivity of the transformation to small variations of input
- Higher derivatives: partial^n(F) -- contexts with n holes (multiple local variations)

#### 3.5.3. Differentiation of Cognitive Patterns
- partial(List_A) = List_A (x) A (a position in a reasoning sequence)
- partial(Tree_A) = Tree_A (x) Bool (x) Tree_A (a path in a decision tree)

---

## 4. Catalog of Composite Functors

### 4.1. Temporal-Scale Functors

#### 4.1.1. tau o lambda: Retrospective Abstraction
- **Definition:** First abstract, then shift in time
- Action: F(t, s, a) |-> F(shift-time(t), lambda(s), a)
- Application: extracting lessons from past experience through generalization

#### 4.1.2. kappa o tau: Concretization of the Future
- **Definition:** First shift in time, then concretize
- Action: forecast followed by detailing
- Application: planning through concretization of abstract goals

#### 4.1.3. lambda o tau o kappa: Complete Temporal-Scale Cycle
- **Definition:** Concretization -> temporal shift -> abstraction
- Gives rise to an emergent property: narrative analysis
- Path length: 3

### 4.2. Temporal-Agency Functors

#### 4.2.1. tau o iota: Perspectival Reversal in Time
- **Definition:** Perspective inversion with temporal shift
- Application: "How will my past look from the perspective of another in the future?"

#### 4.2.2. iota o tau^2: Retrospective Dualization
- **Definition:** Double temporal shift followed by inversion
- Application: revision of future plans through a dual perspective

### 4.3. Scale-Agency Functors

#### 4.3.1. lambda o phi: Context-Dependent Abstraction
- **Definition:** Context modulation followed by abstraction
- Application: generalization accounting for specific circumstances

#### 4.3.2. mu o lambda: Meta-Abstraction
- **Definition:** Abstraction followed by meta-reflection
- Emergence: gives rise to the capacity for methodological thinking

### 4.4. Compositions Giving Rise to Emergent Capacities

According to the Emergence Theorem, certain compositions give rise to cognitive capacities irreducible to the sum of their components.

#### 4.4.1. Narrative Thinking
- **Formula:** mu o tau
- Reflection (mu) over a temporal sequence (tau)
- Result: the capacity to perceive life as a story

#### 4.4.2. Dialectical Thinking
- **Formula:** sigma o iota o lambda
- Abstraction (lambda), inversion (iota), synthesis (sigma)
- Result: thesis -> antithesis -> synthesis

#### 4.4.3. Analytical Insight
- **Formula:** lambda o delta
- Decomposition (delta), then abstraction (lambda)
- Result: discovery of a general pattern within the structure of a problem

#### 4.4.4. Context Reframing
- **Formula:** sigma o iota o lambda o phi o delta
- A complete five-step technique from NLP:
  1. delta: isolate the belief from its context
  2. phi: place it in a new context
  3. lambda: generalize the pattern
  4. iota: reverse the interpretation
  5. sigma: integrate both perspectives

### 4.5. Operator Paths

#### 4.5.1. Canonical Path
- **Definition:** belief-path(F_1, F_2) = T^a ++ D^b ++ A^c
- Path length: |path| = time-dist(t_1, t_2) + scale-dist(s_1, s_2) + agency-dist(a_1, a_2)
- Upper bound: |path| <= 6 (at most 2 steps along each axis)

#### 4.5.2. Optimality (Theorem 3)
- For any two states A, B in Belief, a shortest path exists
- The functorial metric d(A, B) satisfies the metric axioms
- d(A, B) = min{ n | exists F_1,...,F_n in B: F_n o ... o F_1(A) = B }

#### 4.5.3. Path Verification in Agda
- Path correctness: `theorem-path-correct` in `c4-comp-v5.agda`
- Optimality: verified by exhaustive check of all 27 x 27 = 729 pairs of states
- Connectivity: any state is reachable from any other in at most 6 steps (Theorem 11)

---

## 5. Correspondence Table

Correspondence between cognitive functors (Belief category) and formal functors (Lin category):

| N | Cognitive Functor | Formal Analogue in Lin |
|---|---------------------|------------------------|
| 1 | **tau** (temporality) | Cyclic shift, shift-time |
| 2 | **sigma** (integration) | Tensor product (x), Sigma-tensor, Sigma-direct-sum |
| 3 | **delta** (differentiation) | Tensor destructuring, differential operator partial |
| 4 | **rho** (replication) | Diagonal functor Delta, additive conjunction & |
| 5 | **iota** (inversion) | Linear negation (-)^{perp}, contravariance |
| 6 | **lambda** (abstraction) | Forgetful functor, projections pi_1, pi_2 |
| 7 | **kappa** (concretization) | Free functor, injections inl, inr |
| 8 | **mu** (meta-level) | Initial algebra mu, terminal coalgebra nu, fixed points |
| 9 | **phi** (modulation) | Dependent types Sigma-tensor(x:A).B(x), Pi-par(x:A).B(x) |

---

## 6. Properties of the Basis

### 6.1. Completeness (Theorem 1)

Any functor F : Belief -> Belief is expressible as a finite composition of basic functors:

F = F_n o F_{n-1} o ... o F_2 o F_1, where each F_i in {tau, sigma, delta, rho, iota, lambda, kappa, mu, phi}

The proof relies on the Yoneda lemma: a functor is completely determined by its action on universal constructions, each of which is covered by one of the nine basic functors.

### 6.2. Minimality (Theorem 2)

The set of nine functors is minimal:
- Each functor possesses a unique categorical invariant I_F
- No functor is expressible through composition of the remaining eight
- Removal of any one breaks completeness

### 6.3. Independence (Corollary of Theorem 2)

The nine functors form an orthogonal basis:
- tau: the only one operating on the temporal coordinate
- sigma: the only one that joins without information loss
- delta: the only one that systematically separates
- rho: the only one that creates multiple instances
- iota: the only involution (iota o iota = Id)
- lambda: the only forgetful functor
- kappa: the only free functor (left adjoint to lambda)
- mu: the only one acting on the category of functors
- phi: the only one with explicit context dependency

---

## 7. Formal Verification (Agda)

### 7.1. Verified Theorems

The file `c4-comp-v5.agda` contains formal verification of 11 theorems of C4 theory. Below we list the key results pertaining to the functor catalog.

**Theorem 1 (Completeness):** Any functor on Functor_27 is expressible through apply-T, apply-D, apply-A.

**Theorem 3 (Optimality):** belief-path always produces a correct path of minimal length.

**Theorem 5 (Cyclicity):** Each operator has period 3.

**Theorem 11 (6-Step Reachability):** Any state is reachable from any other in at most 6 steps.

### 7.2. Verification Structure

The module `c4-comp-v5.agda` is organized as follows:
- Part II: type system (TimeOrientation, ScaleLevel, AgencyPosition, Functor_27)
- Part III: operators and their properties (shift-time, shift-scale, shift-agency, apply-op)
- Part IV: canonical path algorithm (belief-path, distance functions)
- Part V: fundamental lemmas (cyclicity, path concatenation, distance bounds)

### 7.3. Verification Conditions

The module compiles with the flag `--without-K` (without axiom K), ensuring compatibility with homotopy type theory (HoTT). Of 11 theorems, 10 are fully proven with no postulates and no holes. Theorem 2 (minimality) uses a postulate that is mathematically justified but not yet machine-verified.

### 7.4. Extensions

The formal verification covers axis operators (T, D, A) but does not directly cover all nine cognitive functors. Full formalization of sigma, delta, rho, iota, lambda, kappa, mu, phi in Agda constitutes a separate task requiring modeling the Belief category as a dependent type with linear structure.

---

## 8. Connection to Cognitive Models

### 8.1. Neurological Levels (Dilts)

Axis D (scale) models the neurological levels: environment (Specific) -> behavior -> capabilities -> beliefs -> identity -> mission (Meta).

### 8.2. Perceptual Positions (Satir, NLP)

Axis A (agency) models the perceptual positions: first position (Self) -> second position (Other) -> third position (System).

### 8.3. Timelines (NLP)

Axis T (time) models timeline operations: working with the past (Past), presence in the present (Present), designing the future (Future).

### 8.4. Meta-Programs

The nine basic functors correspond to NLP meta-programs:
- tau: sorting by time (past/present/future)
- delta / sigma: detail / global focus
- iota: toward / away from
- lambda / kappa: induction / deduction
- rho: association (multiple perspectives)
- mu: meta-position
- phi: contextual flexibility

---

## 9. Conclusion

The presented catalog systematizes the functors of the C4 coordinate system, providing:
- A formal description of each of the 9 basic functors with categorical semantics
- Composition rules and examples of emergent cognitive capacities
- A correspondence table between the cognitive and formal-mathematical levels
- References to formal verification in Agda (11 theorems, 10 fully proven, 1 postulate for Theorem 2, zero holes)

The catalog serves as the foundation for practical application of FRACTAL-27 in the analysis of cognitive transformations, the design of psychotechniques, and the formal verification of cognitive models.

---

**Bibliography:**

1. Mac Lane, S. (1971). *Categories for the Working Mathematician*. Springer.
2. Girard, J.-Y. (1987). Linear Logic. *Theoretical Computer Science*, 50(1), 1--102.
3. Abramsky, S. (1993). Computational Interpretations of Linear Logic. *Theoretical Computer Science*, 111, 3--57.
4. Ehrhard, T. & Regnier, L. (2003). The Differential Lambda-Calculus. *Theoretical Computer Science*, 309(1--3), 1--41.
5. Selyutin, I. & Kovalev, N. (2025). FRACTAL-27: A Category-Theoretic Framework for Cognitive Transformations. Preprint.
