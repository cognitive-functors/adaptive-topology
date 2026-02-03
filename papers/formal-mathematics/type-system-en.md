# Type System: MALL with Dependent Types, (Co)inductive Types, and Differentiation

## 1. Introduction

This type system constitutes an extension of multiplicative-additive linear logic (MALL) with the following components:
- **Dependent types** based on four linear connectives
- **(Co)inductive types** defined through MALL expressions with dependent types
- **Differentiation** in the style of differential linear logic (DILL)

## 2. Basic MALL Connectives

### 2.1 Multiplicative Connectives

#### Tensor Product (⊗)

**Introduction**:
```
Γ ⊢ t : A Δ ⊢ u : B
───────────────────────
Γ, Δ ⊢ t ⊗ u : A ⊗ B
```

**Elimination**:
```
Γ ⊢ t : A ⊗ B Δ, x:A, y:B ⊢ u : C
────────────────────────────────────
Γ, Δ ⊢ let x ⊗ y = t in u : C
```

**Semantics**: Linear product of resources

#### Par (⅋)

**Introduction**:
```
Γ, x:A, y:B ⊢ t : C
────────────────────────────
Γ ⊢ λ(x ⅋ y).t : A ⅋ B ⊸ C
```

> **Remark**: This introduction rule for ⅋ differs from the standard MILL rule, where the Par introduction yields a judgement of the form `Γ ⊢ t : A ⅋ B` with split contexts. Here we employ an alternative formulation via ⊸-abstraction, which allows working with Par constructively within the framework of dependent types. The standard introduction of Par in MALL is as follows: from `Γ ⊢ A` and `Δ ⊢ B` one derives `Γ, Δ ⊢ A ⅋ B` (which is dual to the elimination of ⊗).

**Elimination**: Dual to tensor via linear negation

**Semantics**: Parallel composition

#### Multiplicative Unit (1) and Bottom (⊥)

**1**:
```
────────────
· ⊢ () : 1
```

**⊥**: Dual to the unit

### 2.2 Additive Connectives

#### Additive Conjunction (&)

**Introduction**:
```
Γ ⊢ t : A Γ ⊢ u : B
──────────────────────
Γ ⊢ (t, u) : A & B
```

**Elimination**:
```
Γ ⊢ t : A & B Γ ⊢ t : A & B
───────────── ─────────────
Γ ⊢ π₁(t) : A Γ ⊢ π₂(t) : B
```

**Semantics**: Non-deterministic choice of context

#### Additive Disjunction (⊕)

**Introduction**:
```
Γ ⊢ t : A Γ ⊢ t : B
────────────── ──────────────
Γ ⊢ inl(t) : A ⊕ B Γ ⊢ inr(t) : A ⊕ B
```

**Elimination**:
```
Γ ⊢ t : A ⊕ B Δ, x:A ⊢ u : C Δ, y:B ⊢ v : C
──────────────────────────────────────────────────
Γ, Δ ⊢ case t of inl(x) ⇒ u | inr(y) ⇒ v : C
```

**Semantics**: Deterministic choice of value

#### Additive Units (⊤, 0)

**⊤**:
```
─────────────
Γ ⊢ * : ⊤
```

**0**: No introduction rules

## 3. Dependent Types

### 3.1 Dependent Tensor Product (Σ⊗)

**Introduction**:
```
Γ ⊢ t : A Γ ⊢ u : B[t/x]
────────────────────────────────
Γ ⊢ (t ⊗_Σ u) : Σ⊗(x:A).B
```

**Elimination**:
```
Γ ⊢ p : Σ⊗(x:A).B Δ, x:A, y:B ⊢ C : Type Δ, x:A, y:B ⊢ t : C
────────────────────────────────────────────────────────────────────
Γ, Δ ⊢ let_Σ⊗ (x ⊗ y) = p in t : C[p/x⊗y]
```

**Properties**:
- Linear use of the dependency
- The first component influences the type of the second component
- Both components are used linearly

### 3.2 Dependent Par (Π⅋)

**Introduction**:
```
Γ, x:A ⊢ t : B
──────────────────────
Γ ⊢ λ⅋x.t : Π⅋(x:A).B
```

**Elimination**:
```
Γ ⊢ f : Π⅋(x:A).B Δ ⊢ a : A
─────────────────────────────────
Γ ⅋ Δ ⊢ f ⅋ a : B[a/x]
```

**Properties**:
- Parallel application
- Contexts are combined via par
- Dependency on the argument

### 3.3 Dependent Additive Conjunction (Π&)

**Introduction** (for Boolean index):
```
Γ ⊢ t : A[0/i] Γ ⊢ u : A[1/i]
─────────────────────────────────
Γ ⊢ (t &_i u) : Π&(i:𝔹).A
```

**More generally**:
```
∀(x:I). Γ ⊢ tₓ : A[x/i]
────────────────────────
Γ ⊢ λ&(i:I).t_i : Π&(i:I).A
```

**Properties**:
- Indexed family of types
- Non-deterministic choice of index
- Context is reused for all variants

### 3.4 Dependent Additive Disjunction (Σ⊕)

**Introduction**:
```
Γ ⊢ a : I Γ ⊢ t : A[a/i]
────────────────────────────
Γ ⊢ (a, t)⊕ : Σ⊕(i:I).A
```

**Elimination**:
```
Γ ⊢ p : Σ⊕(i:I).A ∀x:I. Δ, y:A[x/i] ⊢ tₓ : C
─────────────────────────────────────────────────
Γ, Δ ⊢ case_Σ⊕ p of (x, y) ⇒ tₓ : C
```

**Properties**:
- Indexed sum
- Deterministic choice of variant
- Type depends on the index

## 4. (Co)inductive Types

### 4.1 Inductive Types (μ)

An inductive type is defined as the least fixed point of a functor constructed from MALL connectives with dependent types:

```
μX. F(X)
```

where F : Type → Type is a functor composed of:
- Dependent connectives: Σ⊗, Π⅋, Π&, Σ⊕
- Basic MALL connectives: ⊗, ⅋, &, ⊕
- The recursive variable X

#### Typing Rules

**Introduction** (constructor):
```
Γ ⊢ t : F(μX.F(X))
──────────────────────
Γ ⊢ fold(t) : μX.F(X)
```

**Elimination** (primitive recursion):
```
Γ ⊢ t : μX.F(X) Δ, x:F(C) ⊢ e : C
─────────────────────────────────────
Γ, Δ ⊢ rec_μ(t, x.e) : C
```

where recursive occurrences in x are replaced by recursive calls.

#### Examples

**Natural numbers** (linear):
```
Nat := μN. 1 ⊕ N
```

**Lists**:
```
List(A) := μL. 1 ⊕ (A ⊗ L)
```

**Dependent vectors**:
```
Vec(A, n) := μV. (n =_Nat 0) & 1 ⊕ Σ⊕(m:Nat). (n =_Nat s(m)) & (A ⊗ V(m))
```

### 4.2 Coinductive Types (ν)

A coinductive type is defined as the greatest fixed point:

```
νX. F(X)
```

#### Typing Rules

**Introduction** (coprimitive corecursion):
```
Γ ⊢ s : S Δ, x:S ⊢ t : F(S)
────────────────────────────────
Γ, Δ ⊢ corec_ν(s, x.t) : νX.F(X)
```

**Elimination** (destructor):
```
Γ ⊢ t : νX.F(X)
───────────────────────
Γ ⊢ unfold(t) : F(νX.F(X))
```

#### Examples

**Streams**:
```
Stream(A) := νS. A & S
```

**Lazy lists**:
```
CoList(A) := νL. 1 ⊕ (A & L)
```

### 4.3 Properties of (Co)inductive Types

1. **Linearity**: All (co)inductive types respect linear resource usage
2. **Positivity**: The recursive variable occurs only in positive positions
3. **Predicativity**: Indices of dependent types are bounded by a given universe
4. **Productivity/Termination**: Corecursion is productive; recursion terminates

#### Remark on Linear Negation and Positivity

In a system with linear negation (−)⊥, the following question arises: may one use X⊥ in the definition of (co)inductive types?

**Current approach** (strict positivity):
```
μX. F(X) where X occurs only covariantly (positively)
νX. F(X) where X occurs only covariantly (positively)
```

**Alternative with negation** (requires a variance condition):
```
μX. F(X, X⊥) where X is covariant, X⊥ is contravariant
νX. F(X, X⊥) similarly
```

**Problem**: In MALL, positivity depends on the connective:
- X in A ⊗ X -- positive (covariant)
- X in A ⅋ X -- positive
- X in A & X -- positive
- X in A ⊕ X -- positive
- X in X ⊗ A -- positive
- BUT: X in A ⊸ X -- positive (X in the codomain)
- BUT: X in X ⊸ A -- **negative** (X in the domain, contravariant!)
- AND: X⊥ in any position reverses the variance

**Correctness condition**: For the existence of (an initial algebra μ / a terminal coalgebra ν), the functor F must be **strictly covariant** in the recursive variable.

**Resolution in our system**:

1. **No explicit negation in the definition**:
 ```
 μX. F(X) and νX. F(X)
 ```
 where F uses only MALL connectives in positive positions. X⊥ is **not used** in the definition of F.

2. **Negation is applied to the completed type**:
 ```
 (μX. F(X))⊥ = νX. F(X⊥)⊥ (theoretically, given functor duality)
 ```
 But this is external negation, not inside the definition.

3. **Advantage**: There is no need to verify the covariance condition -- it holds automatically, since the MALL connectives (⊗, ⅋, &, ⊕) are all covariant in both arguments.

4. **What is permitted**:
 ```
 μX. 1 ⊕ (A ⊗ X) (list)
 νX. A & X (stream)
 μX. (A ⊸ B) ⊗ X (X is positive; it does not participate in A ⊸ B)
 ```

5. **What is forbidden**:
 ```
 μX. (X ⊸ A) ⊗ B (X in a contravariant position)
 μX. A ⊗ X⊥ (explicit negation of X)
 νX. F(X, X⊥) (mixed variance)
 ```

**Conclusion**: The inclusion of negation in the definition of (co)inductive types **is not part of** the base system, since:
- It requires a complex covariance check
- MALL connectives are naturally covariant, which suffices
- Negation is available as an external operation on completed types
- It preserves the simplicity and predictability of the system

If a type with X⊥ is required, it can be expressed through duality of completed types or through explicit encoding without built-in negation.

### 4.4 Sized Types

The system incorporates **sized types**, analogous to those in Agda, providing finer control over (co)inductive types and termination guarantees.

#### 4.4.1 Basic Notions

**Sizes**:
```
Size := 0 | s(Size) | ∞
```

where:
- `0` -- the minimal size (empty type)
- `s(α)` -- the successor of size α
- `∞` -- actual infinity (by default, `∞ := 100500^100500`)

**Inductive types with size**:
```
μ^α X. F(X) : Type
```
where α is a size bounding the depth of recursion.

**Coinductive types with size**:
```
ν^α X. F(X) : Type
```
where α is a size bounding the depth of coinduction (unfolding depth).

#### 4.4.2 Rules for Sized Types

**Introduction with explicit size**:
```
Γ ⊢ t : F(μ^α X.F(X))
───────────────────────────
Γ ⊢ fold^{s(α)}(t) : μ^{s(α)} X.F(X)
```

**Elimination with size decrease**:
```
Γ ⊢ t : μ^{s(α)} X.F(X) Δ, x:F(μ^α X.F(X)) ⊢ e : C
──────────────────────────────────────────────────────
Γ, Δ ⊢ rec_μ(t, x.e) : C
```

Recursive calls operate on a type of smaller size (α instead of s(α)), which guarantees termination.

**Coinductive introduction**:
```
Γ ⊢ s : S Δ, x:S ⊢ t : F(S)
────────────────────────────────────────
Γ, Δ ⊢ corec_ν^α(s, x.t) : ν^α X.F(X)
```

**Coinductive elimination with bound**:
```
Γ ⊢ t : ν^{s(α)} X.F(X)
────────────────────────────────
Γ ⊢ unfold(t) : F(ν^α X.F(X))
```

#### 4.4.3 Default Size: Ultrafinitism

**Convention**: If no size is specified explicitly, it is automatically set to **actual infinity**:
```
∞ := 100500^100500
```

This implements a form of **ultrafinitism**: all types in the system have a finite (albeit enormous) size, yet for practical purposes this is indistinguishable from infinity.

**Examples**:
```
Nat := μ Nat. 1 ⊕ Nat is equivalent to Nat := μ^∞ Nat. 1 ⊕ Nat
Stream(A) := νS. A & S is equivalent to Stream(A) := ν^∞ S. A & S
```

**Philosophy**:
- All real computations are finite
- ∞ = 100500^100500 is sufficiently large for any practical purpose
- Yet theoretically it is a finite number, thus avoiding the paradoxes of actual infinity
- It allows reasoning about "nearly infinite" structures by finitistic methods

#### 4.4.4 Subtyping by Size

There exists a subtyping relation:
```
α ≤ β ⟹ μ^α X.F(X) <: μ^β X.F(X)
α ≤ β ⟹ ν^β X.F(X) <: ν^α X.F(X) (contravariant!)
```

**Subsumption rule**:
```
Γ ⊢ t : A A <: B
────────────────────
Γ ⊢ t : B
```

#### 4.4.5 Practical Usage

**Termination guarantee**:
```
countdown : μ^n Nat → 1
countdown = rec_μ(λx. case x of
 | inl(*) → *
 | inr(n') → countdown(n')) -- n' : μ^{n-1} Nat, terminates at n=0
```

**Bounded productivity**:
```
take : ℕ → ν^∞ S. A & S → μ^n List. 1 ⊕ (A ⊗ List)
```
Takes a finite prefix of a coinductive stream.

**Sized polymorphism**:
```
map : ∀α. (A → B) → μ^α List(A) → μ^α List(B)
```
The function preserves the size of the data structure.

#### 4.4.6 Interaction with Dependent Types

Sizes may be dependent:
```
Vec : Type → Size → Type
Vec(A, 0) := 1
Vec(A, s(n)) := A ⊗ Vec(A, n)
```

Or with Σ and Π:
```
SizedList(A) := Σ⊗(n:Size). μ^n L. 1 ⊕ (A ⊗ L)
```
A list with explicit size.

## 5. Differentiation (DILL)

Differentiation in DILL builds upon the comonad ! from Section 5, adding a derivative operator.

### 6.2 Differential Operator (∂)

We introduce the differentiation operator ∂, which computes the "derivative" of a type:

```
∂(A) -- the type of "one-hole contexts of type A"
```

**Interaction with sized types**: The presence of sized types (Section 4.4) and ultrafinitism (∞ = 100500^100500) permits a correct definition of differentiation for **all** (co)inductive types. Finiteness guarantees that the derivative is always defined and computable:
- For inductive types μ^α X.F(X), the derivative ∂(μ^α X.F(X)) exists and is finite when α < ∞
- For coinductive types ν^α X.F(X), the derivative is also defined thanks to the size bound α
- The default size ∞ = 100500^100500 is sufficiently large for practical computation yet finite for theoretical guarantees

This is a key advantage of the ultrafinite approach: differentiation operates universally for all types in the system without special restrictions.

#### Rules for Type Differentiation

1. **Base cases**:
 - ∂(B) = 0 for a base type B
 - ∂(1) = 0
 - ∂(0) = 0

2. **Tensor product**:
 ```
 ∂(A ⊗ B) = (∂A ⊗ B) ⊕ (A ⊗ ∂B)
 ```

3. **Linear function**:
 ```
 ∂(A ⊸ B) = A ⊗ ∂B
 ```

4. **Additive conjunction**:
 ```
 ∂(A & B) = ∂A & ∂B
 ```

5. **Additive disjunction**:
 ```
 ∂(A ⊕ B) = ∂A ⊕ ∂B
 ```

6. **Dependent types**:
 - ∂(Σ⊗(x:A).B) = (∂A ⊗_Σ B) ⊕ Σ⊗(x:A).∂B
 - ∂(Π&(i:I).A) = Π&(i:I).∂A

7. **Inductive types**:
 ```
 ∂(μX. F(X)) = Σ⊗(c : F(μX.F(X))). ∂F(μX.F(X))
 ```

### 6.3 Typing Rules for Differentiation

**Differential introduction**:
```
Γ ⊢ t : A Δ ⊢ u : ∂A
───────────────────────────
Γ, Δ ⊢ 𝔻(t, u) : ∂A
```

**Derivative application**:
```
Γ ⊢ f : !A ⊸ B Δ ⊢ a : A Θ ⊢ h : ∂A
───────────────────────────────────────────
Γ, Δ, Θ ⊢ ∂f(a)(h) : ∂B
```

Interpretation: ∂f is the linearization of the function f at the point a.

### 6.4 Interaction with (Co)inductive Types

For an inductive type μX.F(X):
- **Derivative of the constructor**: Differentiating fold provides access to the "derivative data structure"
- **Zipper structures**: ∂(μX.F(X)) represents a zipper over the data structure

For a coinductive type νX.F(X):
- **Derivative of the destructor**: Differentiating unfold
- **Observation contexts**: ∂(νX.F(X)) describes the observation context

## 6. Semantics and Computation

### 7.1 Reductions

Principal β-reductions:

1. ```let x ⊗ y = (t ⊗ u) in v → v[t/x, u/y]```
2. ```π_i((t, u)) → t``` (for i=1) or u (for i=2)
3. ```case(inl(t), x.u, y.v) → u[t/x]```
4. ```rec_μ(fold(t), x.e) → e[t/x]```
5. ```unfold(corec_ν(s, x.t)) → t[s/x]```

For differentiation:
- ```∂(λx.t)(a)(h) → t[a/x, h/∂x]```

### 7.2 Properties of the System

1. **Subject reduction**: If Γ ⊢ t : A and t → t', then Γ ⊢ t' : A
2. **Weak normalization**: All well-typed terms reduce to normal form (for inductive types)
3. **Linearity**: Each variable is used exactly once (except for variables under !)
4. **Consistency**: There exists no term of type 0

## 7. Type Universes

We introduce a hierarchy of universes 𝓤₀ : 𝓤₁ : 𝓤₂ : ... to ensure consistency when working with dependent types and (co)inductive definitions.

**Rules**:

```
A : 𝓤ᵢ B : 𝓤ⱼ
──────────────────────
A ⊗ B : 𝓤_{max(i,j)}
```

```
A : 𝓤ᵢ x:A ⊢ B : 𝓤ⱼ
─────────────────────────────
Σ⊗(x:A).B : 𝓤_{max(i,j)}
```

```
F : 𝓤ᵢ → 𝓤ᵢ
──────────────
μX.F(X) : 𝓤ᵢ
```

## 8. Examples and Applications

### 9.1 Linear Natural Numbers with Differentiation

```
Nat := μN. 1 ⊕ N
```

```
∂(Nat) = Σ⊗(c : 1 ⊕ Nat). (0 ⊕ ∂(Nat))
```

In simplified form: ∂(Nat) ≅ Nat (the zipper is a position in a unary number)

### 9.2 Dependent Vectors with Differentiation

```
Vec(A, n) := μV. (n = 0) & 1 ⊕ (n > 0) & (A ⊗ V(n-1))
```

The derivative yields the structure of a "vector with a hole" -- a zipper over the vector.

### 9.3 Corecursive Streams with Differentiation

```
Stream(A) := νS. A & S
```

```
∂(Stream(A)) = ∂A & Stream(A)
```

This describes an "observation context" over the stream with a distinguished element.

## 9. Modalities

**Important remark**: The base type system (Sections 1--8) is defined through MALL connectives, dependent types, (co)inductive types, and differentiation. Modalities **are not part of the base system**, but the structure permits their natural definition via (co)inductive types.

### 9.1 Exponential Modalities ! and ?

To integrate nonlinearity into the linear type system, exponential modalities are introduced:
- **!** (of course) -- a comonad permitting duplication and erasure
- **?** (why not) -- a monad, structurally symmetric to !


### 9.1.1 Comonad ! (of course)

#### 5.1.1 Principal Definition: Coinductive Type with Additive Choice

```
!A := νX. 1 ⊕ (A & X)
```

**Intuition**: An element of type !A is a coinductive stream with a choice at each step:
- `unfold(x) = inl(*)` : stream termination (0 copies of A are provided)
- `unfold(x) = inr(a, x')` where a:A and x':!A : provision of element a with continuation x'
 - Here `(a, x') : A & !A` is an additive conjunction!
 - The consumer may non-deterministically choose either π₁ (take a) or π₂ (continue unfolding)

**Key distinction from lists**:
```
Stream(A) = νX. A & X -- deterministic stream (an element is always present)
!A = νX. 1 ⊕ (A & X) -- may terminate (via inl) or continue (via inr)
```

**Semantics**: The coinductive type describes a potentially infinite "stream of possibilities" for providing A. The connective & means that at each step the consumer chooses: take the element or continue.

#### 5.1.2 Alternative Constructions

**Indexed product**:
```
!A := Π&(n:ℕ). (A^⊗n)
```
A family of all arities simultaneously. A more abstract but equivalent definition.

**Via commutative monoid**:
```
!A := νX. ⊤ & (A ⊗ X)
```
An alternative coinductive formulation.

**Relationship between definitions**: In the presence of appropriate isomorphisms, these definitions are equivalent. The principal definition via νX. 1 ⊕ (A & X) is chosen for structural duality with ?.

#### 5.1.3 Typing Rules for !

**Introduction** (construction via corecursion):
```
───────────────────
Γ ⊢ empty! : !A
```
where `empty! = fold(inl(*))` -- the empty stream.

```
Γ ⊢ a : A Δ ⊢ xs : !A
─────────────────────────
Γ, Δ ⊢ offer(a, xs) : !A
```
where `offer(a, xs) = fold(inr((a, xs)))` -- offering element a with continuation xs.

**Elimination** (processing via anamorphism):
```
Γ ⊢ t : !A Δ ⊢ e₀ : B Θ ⊢ e₁ : A & !A → B
────────────────────────────────────────────────
Γ, Δ, Θ ⊢ match t with
 | empty! → e₀
 | offer(choice) → e₁(choice) : B
```

where `choice : A & !A` and the consumer selects π₁ (take A) or π₂ (continue with !A).

**Comonadic operations**:

**Dereliction** ε : !A → A (counit):
```
derel : !A → A
derel(x) = match unfold(x) with
 | inl(*) → error (empty stream)
 | inr(choice) → π₁(choice) -- select element
```

**Contraction** δ : !A → !!A (comultiplication):
```
copy : !A → !!A
copy(x) = fold(inr((x, copy(x)))) -- stream of streams
```

**Weakening** w : !A → 1:
```
discard : !A → 1
discard(x) = *
```

**Promotion**:
```
x₁:!A₁, ..., xₙ:!Aₙ ⊢ t : B
──────────────────────────────────────────
x₁:!A₁, ..., xₙ:!Aₙ ⊢ promote(t) : !B
```

#### 5.1.4 Examples of Using !

**Function with reuse of argument**:
```
dup : !(A ⊗ A) ⊸ !A
dup(x) = let z = derel(x) in
 let (a₁, a₂) = z in
 promote(a₁) -- use only the first element
```

**Iteration**:
```
iterate : ℕ → !(A ⊸ A) → A → A
iterate(0, f, x) = x
iterate(n+1, f, x) = derel(f)(iterate(n, copy₁(f), x))
```

where copy₁ copies the first component during contraction.

### 9.1.2 Monad ? (why not)

#### 5.2.1 Principal Definition: Inductive Type of Multisets

```
?A := μX. ⊤ ⊕ (A ⊗ X)
```

**Intuition**: An element of type ?A is a finite multiset of elements of type A. This is an inductive type with two constructors:
- `fold(inl(*))` : ?A -- the empty multiset
- `fold(inr(a, xs))` where a:A and xs:?A -- adding element a to the multiset xs

**Structure**:
```
?A = { ∅, {a₁}, {a₁,a₂}, {a₁,a₂,a₃}, ... }
```

Each multiset is finite (by inductivity) but may contain an arbitrary number of elements. This is dual to ! in the following sense:
- **!A**: one can _request_ an arbitrary number of copies (coinductively)
- **?A**: one can _provide_ an arbitrary number of copies (inductively)

**Comparison with lists**:
```
List(A) = μX. 1 ⊕ (A ⊗ X) -- ordered list
?A = μX. ⊤ ⊕ (A ⊗ X) -- unordered multiset (⊤ instead of 1)
```

The difference: for ?A the order is irrelevant (commutativity), which corresponds to the commutative monoidal structure of !.

#### 5.2.2 Alternative Constructions (briefly)

**Via indexed sum**:
```
?A := Σ⊕(n:ℕ). (A^⊗n / Sₙ)
```
where Sₙ is the symmetric group (quotient by permutations). This explicitly expresses finiteness and unorderedness.

**Via duality**:
```
?A := (!(A⊥))⊥
```
A definition through linear negation of the comonad !, ensuring correct duality.

#### 5.2.3 Typing Rules for ?

**Introduction** (multiset construction):
```
──────────────────
Γ ⊢ empty : ?A
```
where `empty = fold(inl(*))`.

```
Γ ⊢ a : A Δ ⊢ xs : ?A
─────────────────────────
Γ, Δ ⊢ cons(a, xs) : ?A
```
where `cons(a, xs) = fold(inr(a, xs))`.

**Elimination** (multiset processing):
```
Γ ⊢ t : ?A Δ ⊢ e₀ : B Θ, x:A, xs:?A ⊢ e₁ : B
──────────────────────────────────────────────────
Γ, Δ, Θ ⊢ match t with
 | empty → e₀
 | cons(x, xs) → e₁ : B
```

**Monadic operations**:

**Unit** (singleton multiset):
```
Γ ⊢ a : A
─────────────────────────
Γ ⊢ unit(a) : ?A
```
where `unit(a) = cons(a, empty)`.

**Multiplication** (flatten -- collapsing a multiset of multisets):
```
Γ ⊢ t : ??A
─────────────────
Γ ⊢ flatten(t) : ?A
```
where flatten recursively concatenates all inner multisets into one:
```
flatten(empty) = empty
flatten(cons(xs, xss)) = append(xs, flatten(xss))
```

#### 5.2.4 Operations via the Principal Definition

**Unit** (η of the monad):
```
unit : A → ?A
unit(a) = fold(inr(a, fold(inl(*))))
```

**Flatten** (μ of the monad):
```
flatten : ??A → ?A
flatten = rec_μ(λt. match t with
 | inl(*) → fold(inl(*)) -- empty multiset of multisets
 | inr(xs, xss) → append(xs, flatten(xss)))
```

where `append : ?A → ?A → ?A` concatenates two multisets:
```
append(xs, ys) = rec_μ(xs, λt. match t with
 | inl(*) → ys
 | inr(a, xs') → fold(inr(a, append(xs', ys))))
```

### 9.1.3 Interrelation of ! and ? -- Adjunction vs. Duality

#### 5.3.1 Adjunction ! ⊣ ? (principal property)

**Hom-set isomorphism**:
```
!A ⊸ B ≅ A → ?B
```
where A → B is an abbreviation for !A ⊸ B (intuitionistic implication).

**Explicit construction of the adjunction**:

For f : !A → B we construct curry(f) : A → ?B:
```
curry(f)(a) = unit(f(promote(a)))
```
where promote(a) creates a minimal element of !A.

For g : A → ?B we construct uncurry(g) : !A → B:
```
uncurry(g)(x) = match g(derel(x)) of
 | empty → error_or_default
 | cons(b, _) → b
```

**Intuition behind the adjunction**:
- f : !A → B may request any number of copies of A to produce one B
- g : A → ?B produces a multiset of results B from one A
- These capabilities are **functionally dual**: "consuming many" corresponds to "producing many"

#### 5.3.2 Verifying Exact Categorical Duality

We now verify the duality for the principal definitions:

**For !A = νX. 1 ⊕ (A & X)**:
```
(!A)⊥ = (νX. 1 ⊕ (A & X))⊥
 ≅ μX. (1 ⊕ (A & X))⊥ [ν/μ duality]
 ≅ μX. (1⊥ & (A & X)⊥) [de Morgan: (A⊕B)⊥ = A⊥ & B⊥]
 ≅ μX. (⊥ & (A⊥ ⊕ X)) [de Morgan: (A&B)⊥ = A⊥ ⊕ B⊥, 1⊥ = ⊥]
```

Now we use the property ⊥ & B. In linear logic:
- ⊥ & B ≅ 0 (no constructor, since the first alternative is impossible)

This yields μX. 0, which is incorrect.

**Alternative analysis**: The issue is that ⊥ & B does not simplify straightforwardly. Let us use a different property.

In fact, for correct duality one needs to use:
```
⊥ & B ≅ B (if ⊥ is treated as "always true" in the context of &)
```

Then:
```
(!A)⊥ ≅ μX. (⊥ & (A⊥ ⊕ X))
 ≅ μX. (A⊥ ⊕ X)
```

But this does not equal μX. ⊤ ⊕ (A⊥ ⊗ X) = ?(A⊥)!

**Correction**: A different identity must be used. If 1⊥ ≅ ⊥ and ⊥⊥ ≅ ⊤, then for proper duality one needs:

```
(!A)⊥ ≅ μX. (⊥ & (A⊥ ⊕ X))
```

And for ?A:
```
(?A)⊥ = (μX. ⊤ ⊕ (A ⊗ X))⊥
 ≅ νX. (⊤ ⊕ (A ⊗ X))⊥
 ≅ νX. (0 & (A⊥ ⅋ X)) [⊤⊥ = 0, (A⊕B)⊥ = A⊥&B⊥, (A⊗B)⊥ = A⊥⅋B⊥]
```

And 0 & B... this is problematic.

**Conclusion**: Even with the coinductive definition ! = νX. 1 ⊕ (A & X), exact categorical duality with ? = μX. ⊤ ⊕ (A ⊗ X) **still does not hold** due to a mismatch of units (1/⊤ and ⊥/0).

#### 5.3.3 Structural Symmetry vs. Exact Duality

With the principal definitions:
```
!A := νX. 1 ⊕ (A & X) [coinductive]
?A := μX. ⊤ ⊕ (A ⊗ X) [inductive]
```

**Structural symmetry**:
- ν ↔ μ (coinduction ↔ induction)
- & ↔ ⊗ (additive conjunction ↔ multiplicative conjunction)
- ⊕ remains ⊕ (deterministic choice)
- But: 1 ↔ ⊤ (different units!)

This structural symmetry ensures:

 **Functional duality** via the adjunction ! ⊣ ?:
```
!A ⊸ B ≅ A → ?B
```

 **Computational consistency**: the operations of ! and ? are mirror-symmetric

 **Exact categorical duality** via (−)⊥:
```
(?A)⊥ = (μX. ⊤ ⊕ (A ⊗ X))⊥
 ≅ νX. (0 & (A⊥ ⅋ X))
 ≠ νX. 1 ⊕ (A⊥ & X) = !(A⊥)
```

The mismatch arises from: ⊤⊥ = 0 ≠ 1 and (A⊗B)⊥ = A⊥ ⅋ B⊥ ≠ A⊥ & B⊥.

**Possibility of exact duality**: For exact categorical duality, one may use:
```
!A := νX. 1 ⊕ (A & X)
?A := μX. ⊥ & (A ⊕ X)
```

Then (!A)⊥ = ?(A⊥) holds exactly. However, μX. ⊥ & (A ⊕ X) has a peculiar semantics: ⊥ in & means "impossible alternative," so effectively this is ≅ μX. (A ⊕ X), which loses the multiset structure.

**Practical conclusion**:
1. The principal definitions with 1 and ⊤ provide **structural symmetry** and **functional duality** (! ⊣ ?)
2. Exact categorical duality via (−)⊥ requires sacrifices in computational semantics
3. For all practical applications, the adjunction ! ⊣ ? suffices
4. Structural symmetry (ν↔μ, &↔⊗) is more important for understanding the system than exact categorical duality

### 9.1.4 Interaction with Dependent Types

#### 5.4.1 ! and Dependent Types

**For Π&**:
```
!(Π&(i:I).A) ≅ Π&(i:I).!A
```
The comonad ! commutes with indexed products, since both are limits.

**For Σ⊗** (with care):
```
!(Σ⊗(x:A).B) → Σ⊗(x:!A).!B
```
A morphism exists, but the converse is not always correct due to the dependency.

**For ⊗**:
```
!(A ⊗ B) ≅ !A ⊗ !B
```
The comonad ! is a monoidal functor.

#### 5.4.2 ? and Dependent Types

**For ⊕**:
```
?(A ⊕ B) → ?A ⊕ ?B
```
The morphism maps a multiset with mixed elements to a choice between multisets. However, the converse does not always hold -- a multiset may contain elements of both types.

**For Σ⊕**:
```
?(Σ⊕(i:I).A) → Σ⊕(i:I).?A
```
Analogously -- one can partition a multiset by indices, but it is not always possible to reassemble.

**Important**: The monad ? (multisets) **does not** commute with most structures, since a multiset may contain a heterogeneous mixture of elements.

### 9.1.5 Monoidal Functors

#### 5.5.1 ! as a Monoidal Functor

```
m : !A ⊗ !B → !(A ⊗ B)
m(x, y) = promote(derel(x) ⊗ derel(y))
```

```
e : 1 → !1
e(*) = promote(*)
```

This makes ! a lax monoidal functor.

#### 5.5.2 ? as a Comonoidal Functor

```
Δ : ?(A & B) → ?A & ?B
Δ(x) = (corel(π₁(flatten(x))), corel(π₂(flatten(x))))
```

This makes ? a lax comonoidal functor with respect to &.

### 9.1.6 Nested Linearity

The system with ! and ? allows expressing nested levels of linearity:

**Level 0** (fully linear types): A, B, A ⊗ B, ...
**Level 1** (one level of nonlinearity): !A, ?(A ⊗ B), ...
**Level 2** (nested nonlinearity): !!A, !(?A), ...

**Example**: A matrix with linear coefficients but nonlinear structure:
```
Matrix(A) := !(Vec(A) ⊗ Vec(A))
```

### 9.1.7 Computational Semantics

#### 5.7.1 ! and Sharing/Memoization

A value of type !A can be stored in memory and reused:
- **Copy-on-write**: a physical copy is created only upon modification
- **Reference counting**: a reference counter manages the lifetime
- **Garbage collection**: automatic deallocation of unused values

#### 5.7.2 ? and Nondeterminism

A value of type ?A represents a nondeterministic choice:
- **Backtracking**: returning to previous choices upon failure
- **Parallel computation**: exploring all variants in parallel
- **Probabilistic computation**: choice with a probability distribution

### 9.1.8 Examples of Complete Definitions

#### 5.8.1 Natural Numbers with Ordinary Semantics

```
Nat := !Nat_lin
Nat_lin := μN. 1 ⊕ N

zero : Nat
zero = promote(fold(inl(*)))

succ : Nat → Nat
succ(n) = promote(fold(inr(derel(n))))

plus : Nat → Nat → Nat
plus(m, n) = rec_μ(derel(m),
 λx. case x of
 | inl(*) → n
 | inr(m') → succ(promote(plus(derel(promote(m')), copy(n)))))
```

#### 5.8.2 Lists with Random Access

```
List(A) := !(List_lin(A))
List_lin(A) := μL. 1 ⊕ (A ⊗ L)

map : (A → B) → List(A) → List(B)
map(f, xs) = promote(rec_μ(derel(xs),
 λx. case x of
 | inl(*) → fold(inl(*))
 | inr(a, xs') → fold(inr(derel(f)(a), map(copy(f), promote(xs'))))))
```


### 9.2 Other Modalities: Extensions of the Type System

In addition to ! and ?, the structure of the type system permits the definition of many other modalities. **None of them are part of the base system**, but they can be added via (co)inductive types.

#### 9.2.1 Temporal Modalities

**Always in the future (Box)**:
```
□A := νX. A & X
```
Rules: projection π₂ yields a transition to the next moment of time.

**Eventually in the future (Diamond)**:
```
◇A := μX. A ⊕ X
```
Rules: either A now (inl) or A later (inr).

**Richer with dependent types**: □_t A := Π&(t':Time, t'≥t).A(t') -- indexing by time; □^d A -- with interval duration; Σ⊗(t:Time).A(t) U_t B(t) -- until with dependency on the moment of time.

#### 9.2.2 Spatial Modalities

**Everywhere (Box_S)**:
```
□_S A := Π&(l:Location).A(l)
```
Using Π& from Section 3.3.

**Somewhere (Diamond_S)**:
```
◇_S A := Σ⊕(l:Location).A(l)
```
Using Σ⊕ from Section 3.4.

**Richer with dependent types**: □_r A := Π&(l:Location, d(l,here)≤r).A(l) -- within radius r with distance metric; Σ⊗(r:Region).Π&(l:r).A(l) -- by regions; Σ⊗(l:Location).(A(l) ⊗ Resources(l)) -- with local resources.

#### 9.2.3 Deontic Modalities

**Obligatory (O)**:
```
O A := νX. A & (X ⊕ Violation)
```
A coinductive sequence of obligation checks.

**Permitted (P)**:
```
P A := μX. A ⊕ (X & Grant)
```
An inductive sequence of permissions.

**Richer with dependent types**: O_c A := Σ⊗(c:Context).(A(c) & Obligation(c)) -- obligation depends on context; Π&(p:Priority).O_p A -- with priorities; Σ⊕(a:Agent).O_a A -- who is obligated; Π⅋(cond:Condition).O A -- conditional obligation.

#### 9.2.4 Alethic Modalities

**Necessarily (Box_N)**:
```
□_N A := Π&(w:World).A(w)
```
A holds in all possible worlds.

**Possibly (Diamond_N)**:
```
◇_N A := Σ⊕(w:World).A(w)
```
A holds in some world.

**Richer with dependent types**: Π&(w:World, R(w₀,w)).A(w) -- via an accessibility relation R; Σ⊗(n:ℕ).□ⁿ A -- with modal depth specification; Π&(w:World).A(w) ⊗ Prob(w) -- weighted necessity with world probabilities.

#### 9.2.5 Epistemic Modalities

**Agent knowledge (K_a)**:
```
K_a A := Π&(s:State_a).A(s)
```

**Common knowledge (C)**:
```
C A := νX. A & (Π&(a:Agent).K_a X)
```
Coinductive: everyone knows that everyone knows that...

**Richer with dependent types**: K_a(Σ⊗(b:Agent).K_b A) -- knowledge about others' knowledge; Σ⊗(G:Group).D_G A -- distributed knowledge of a group; K_a^t := Π&(s:State_a(t)).A(s) -- temporal knowledge; Σ⊗(c:Confidence).K_a A ⊗ c -- with confidence level; Π⅋(e:Evidence).K_a A -- conditional knowledge.

#### 9.2.6 Other Modalities

**Probabilistic**:
```
□_p A := A ⊗ Prob(p)
D A := Σ⊕(n:ℕ).(A^⊗n ⊗ Distribution(n))
```
**Richer with dependent types**: Σ⊗(e:Evidence).(A ⊗ Prob(A|e)) -- conditional probability; Π⅋(obs:Observation).□_p A → □_{p'} A -- Bayesian update; Σ⊗(θ:Parameters).D_θ A -- parameterized distributions.

**LTL (Until, Release)**:
```
A U B := μX. B ⊕ (A ⊗ X)
A R B := νX. B & (A ⅋ X)
```
**Richer with dependent types**: Σ⊗(n:ℕ).(A U_≤n B) -- bounded until; Π⅋(P:Predicate).A U_P B -- with a predicate at each step; Σ⊗(t:Time).A U_{[0,t]} B -- metric until.

**Affine/Relevant**:
```
◯A := A ⊕ 1 -- may be unused
◉A := μX. A ⊕ (A ⊗ X) -- at least one use
```
**Richer with dependent types**: Π⅋(cond:Condition).(A ⊕ 1(cond)) -- conditional affinity; Σ⊗(n:ℕ_{>0}).A^⊗n -- exact relevance; Σ⊗(c:Context).(A(c) ⊕ 1) -- contextual affinity.

**Graded**:
```
□_n A := A^⊗n -- exactly n uses
□_≤n A := Σ⊕(k:ℕ_{≤n}).A^⊗k -- up to n uses
□_≥n A := A^⊗n ⊗ !A -- at least n uses
```
**Richer with dependent types**: Σ⊗(n:ℕ).□_n(A(n)) -- grading depends on type; Σ⊗(v:Vector(Resource)).A^⊗v -- multidimensional resources; Σ⊗(n,m:ℕ, n≤m).□_{[n,m]} A -- interval grading; Π⅋(params:Params).□_{f(params)} A -- parameterized grading.

### 9.3 General Principle for Defining Modalities

**Rule**: Any modality expressible through:
- (Co)inductive types (μ, ν)
- MALL connectives (⊗, ⅋, &, ⊕)
- Dependent types (Σ⊗, Π⅋, Π&, Σ⊕)

can be defined within the system.

**Typing**: For a modality M, one adds:
1. Introduction rules (how to construct MA)
2. Elimination rules (how to use MA)
3. Monadic/comonadic structure (if applicable)

**Composition**: Modalities may be composed through functorial structure:
```
(!□)A = !(□A) -- unbounded use of a temporal stream
(□!)A = □(!A) -- a stream of unboundedly usable values
```

**Role of dependent types**: The four dependent connectives significantly enrich the modalities:
- **Σ⊗** -- parameterization of modalities (dependency on parameters, states)
- **Π⅋** -- conditional modalities (modality subject to a condition)
- **Π&** -- indexed modalities (by time, space, worlds, agents)
- **Σ⊕** -- choice of variant with dependency (indexed disjunctions)

Without dependent types, the modalities would be significantly less expressive. Dependent types enable the creation of rich modal systems tailored to specific domains.

### 9.4 Summary on Modalities

**System architecture**:
- **Sections 1--8**: Base system (MALL, dependent types, (co)induction, differentiation)
- **Section 9**: Modalities (extensions built upon the base structure)

**Advantages**:
- Uniform definition of diverse modalities
- Reuse of base constructions
- Extensibility without modifying the core system

**Applications**:
- Temporal logic of programs
- Distributed systems (spatial modalities)
- Multi-agent systems (epistemic modalities)
- Probabilistic programming
- Effect systems

## 10. Conclusion

### Architecture of the Type System

The system is organized in two levels:

**Base system (Sections 1--8)**:
- **MALL linear logic** for resource management (⊗, ⅋, &, ⊕)
- **Dependent types** from four connectives (Σ⊗, Π⅋, Π&, Σ⊕) for precise specification
- **(Co)inductive types** (μ, ν) for recursive data structures
- **Sized types** (μ^α, ν^α) with ultrafinitism (∞ = 100500^100500)
- **Differentiation** (∂) for working with contexts and derivative structures

**Extensions via modalities (Section 9)**:
- **Exponential**: ! (of course), ? (why not)
- **Temporal**: □ (always), ◇ (eventually), U (until), R (release)
- **Spatial**: □_S (everywhere), ◇_S (somewhere)
- **Deontic**: O (obligatory), P (permitted)
- **Alethic**: □_N (necessarily), ◇_N (possibly)
- **Epistemic**: K_a (knowledge), C (common knowledge)
- **And others**: probabilistic, graded, affine

### Key Properties

1. **Four dependent connectives** yield a rich system for specifying diverse kinds of dependencies:
 - Σ⊗ -- multiplicative dependent sum
 - Π⅋ -- multiplicative dependent product
 - Π& -- indexed product (limit)
 - Σ⊕ -- indexed coproduct (colimit)

2. **Modalities are not built in** but are **defined through the base structure**:
 - They use (co)inductive types
 - They use MALL connectives and dependent types
 - They can be added as needed

3. **Sized types and ultrafinitism**:
 - Every type has a size (default ∞ = 100500^100500)
 - Guarantees termination of inductive types and productivity of coinductive types
 - Ensures correctness of differentiation for all types

4. **Differentiation** interacts with all levels:
 - Yields zipper structures for (co)inductive types
 - Enables incremental computation
 - Is universally applicable thanks to the finiteness of sized types
 - Interacts with modalities (∂(!A) ≅ !A ⊗ A)

### Theoretical Properties

The system possesses:
- **Consistency** (there exists no term of type 0)
- **Subject reduction** (type preservation under reduction)
- **Weak normalization** (for inductive types)
- **Linearity** (each variable is used exactly once, except under modalities)

### Practical Applications

**Programming**:
- Resource management (linear types)
- Zipper structures (via differentiation)
- Incremental computation
- Effects and state (via modalities)

**Verification**:
- Temporal logic of programs
- Knowledge logic for multi-agent systems
- Spatial reasoning in distributed systems

**Specialized domains**:
- Quantum computation (linearity = no-cloning)
- Probabilistic programming (via probabilistic modalities)
- Real-time systems (temporal modalities)
