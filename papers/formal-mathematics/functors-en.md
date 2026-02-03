# Basic Functors of the Category Lin

## Introduction

This document describes the **system of basic functors** through which any functor in the category **Lin** (differential linear logic with dependent types, MALL connectives, and (co)inductive types) can be expressed.

**Main Hypothesis** *(Conjecture)*: Any polynomial functor F : **Lin** -> **Lin** can be constructed from basic functors and functorial combinators. *(A complete proof requires formalization; below we provide a proof sketch.)*

**Inheritance Principle**: Functorial combinators (operations on functors) inherit notation and properties from the base category **Lin**:
- The combinator for functors uses from **Lin** pointwise
- Combinators &, direct sum, and par likewise inherit structure from **Lin**
- The differential operator d inherits the differential structure from **Lin**
- This creates uniformity between the level of objects and the level of functors

Thus, the category of endofunctors [**Lin**, **Lin**] reflects the structure of the base category **Lin**, including its monoidal, binoidal, and **differential** structure.

**Modalities**: In addition to basic functors, the system allows one to define **modal functors** (exponential, temporal, spatial, deontic, alethic, epistemic, probabilistic, graded) through combinations of (co)inductive types, MALL connectives, and dependent functors. Modalities **are not part of the base system** but are naturally expressible through it.

## 1. Primitive Functors

### 1.1 Identity Functor (Id)

```
Id : Lin -> Lin
Id(A) = A
Id(f : A -> B) = f : A -> B
```

**Properties**:
- Id . F = F . Id = F for any functor F
- Unit for vertical composition of functors

**Application**: Recursive variable in (co)inductive types.

### 1.2 Constant Functors (K_C)

For each object C in **Lin**:

```
K_C : Lin -> Lin
K_C(A) = C
K_C(f : A -> B) = id_C : C -> C
```

**Properties**:
- Ignores its argument
- K_C . F = K_C for any F
- Basis for base cases of (co)inductive types

**Examples**:
- K_1 -- constant functor for the unit (list termination)
- K_top -- constant functor for top (multiset termination)
- K_A -- constant functor for any type A

### 1.3 Diagonal Functor (Delta)

```
Delta : Lin -> Lin x Lin
Delta(A) = (A, A)
Delta(f : A -> B) = (f, f) : (A, A) -> (B, B)
```

**Properties**:
- Duplicates an object into a pair
- Natural transformation for copying

**Application**: Used for constructing functors that apply identical operations to both arguments (e.g., X tensor X).

**Remark**: The projections pi_1 : A & B -> A and pi_2 : A & B -> B exist only for the categorical product &, but are not separate basic functors -- they are built into the structure of the bifunctor &.

## 2. Functors for MALL Connectives

### 2.1 Tensor Functor (tensor)

**As a bifunctor**:
```
(-) tensor (-) : Lin x Lin -> Lin
(A, B) |-> A tensor B
(f : A -> A', g : B -> B') |-> f tensor g : A tensor B -> A' tensor B'
```

**Partial application** (yields a family of functors):
```
A tensor (-) : Lin -> Lin
(-) tensor B : Lin -> Lin
```

**Properties**:
- Strictly covariant in both arguments
- Symmetric: A tensor B iso B tensor A (via the symmetry sigma)
- Associative: (A tensor B) tensor C iso A tensor (B tensor C) (via the associator alpha)

**Functorial laws**:
```
id_A tensor id_B = id_{A tensor B}
(f . f') tensor (g . g') = (f tensor g) . (f' tensor g')
```

### 2.2 Par Functor (par)

```
(-) par (-) : Lin x Lin -> Lin
(A, B) |-> A par B
(f, g) |-> f par g
```

**Properties**:
- Dual to tensor via linear negation: (A tensor B)^perp = A^perp par B^perp
- Also covariant in both arguments
- Symmetric and associative

### 2.3 Additive Conjunction (&)

```
(-) & (-) : Lin x Lin -> Lin
(A, B) |-> A & B
(f : A -> A', g : B -> B') |-> <f . pi_1, g . pi_2> : A & B -> A' & B'
```

**Properties**:
- Categorical product
- Universal property via projections pi_1, pi_2
- Covariant in both arguments

**Functorial action on morphisms**:
```
f & g : A & B -> A' & B'
(f & g)(x) = <f(pi_1(x)), g(pi_2(x))>
```

### 2.4 Additive Disjunction (direct sum)

```
(-) direct_sum (-) : Lin x Lin -> Lin
(A, B) |-> A direct_sum B
(f : A -> A', g : B -> B') |-> [inl' . f, inr' . g] : A direct_sum B -> A' direct_sum B'
```

**Properties**:
- Categorical coproduct
- Universal property via injections inl, inr
- Covariant in both arguments

**Functorial action**:
```
f direct_sum g : A direct_sum B -> A' direct_sum B'
(f direct_sum g)(inl(a)) = inl'(f(a))
(f direct_sum g)(inr(b)) = inr'(g(b))
```

## 3. Functors for Dependent Types

### 3.1 Dependent Sum (Sigma_tensor)

For a family of types B : A -> Type:

```
Sigma_tensor_A(B) : Lin/A -> Lin
Sigma_tensor_A(B) = Sigma_tensor(x:A).B(x)
```

**Functorial action**: For a morphism sigma : B -> B' in Lin/A:
```
Sigma_tensor(sigma) : Sigma_tensor(x:A).B(x) -> Sigma_tensor(x:A).B'(x)
Sigma_tensor(sigma)(a, b) = (a, sigma_a(b))
```

**Property**: Left adjoint to the base change functor (pullback).

### 3.2 Dependent Product par (Pi_par)

```
Pi_par_A(B) : Lin/A -> Lin
Pi_par_A(B) = Pi_par(x:A).B(x)
```

**Functorial action**:
```
Pi_par(sigma) : Pi_par(x:A).B(x) -> Pi_par(x:A).B'(x)
Pi_par(sigma)(f)(a) = sigma_a(f(a))
```

### 3.3 Indexed Product (Pi_&)

```
Pi_&_I(A) : (I -> Lin) -> Lin
Pi_&(i:I).A(i)
```

**Functorial action**: For a natural transformation tau : A => B:
```
Pi_&(tau) : Pi_&(i:I).A(i) -> Pi_&(i:I).B(i)
Pi_&(tau)(f)(i) = tau_i(f(i))
```

**Categorical interpretation**: Limit of the diagram I -> **Lin**.

### 3.4 Indexed Coproduct (Sigma_direct_sum)

```
Sigma_direct_sum_I(A) : (I -> Lin) -> Lin
Sigma_direct_sum(i:I).A(i)
```

**Functorial action**:
```
Sigma_direct_sum(tau) : Sigma_direct_sum(i:I).A(i) -> Sigma_direct_sum(i:I).B(i)
Sigma_direct_sum(tau)(i, a) = (i, tau_i(a))
```

**Categorical interpretation**: Colimit of the diagram I -> **Lin**.

## 4. Fixed Point Functors

### 4.1 Initial Algebra Functor (mu)

For an endofunctor F : **Lin** -> **Lin**:

```
mu : [Lin -> Lin] -> Lin
mu(F) = mu X.F(X)
```

**Not a functor in the usual sense**, but an operator on endofunctors.

**Action on natural transformations**: For tau : F => G:
```
mu(tau) : mu F -> mu G
mu(tau) = cata(fold_G . G(mu(tau)) . tau_{mu F})
```

**Property**: Initial F-algebra with a universal morphism (catamorphism).

### 4.2 Terminal Coalgebra Functor (nu)

```
nu : [Lin -> Lin] -> Lin
nu(F) = nu X.F(X)
```

**Action on natural transformations**: For tau : F => G:
```
nu(tau) : nu F -> nu G
nu(tau) = ana(tau_{nu G} . F(nu(tau)) . unfold_F)
```

**Property**: Terminal F-coalgebra with a universal morphism (anamorphism).

### 4.3 Sized Functors (mu^alpha, nu^alpha)

For each size alpha:

```
mu^alpha : [Lin -> Lin] -> Lin
nu^alpha : [Lin -> Lin] -> Lin
```

Parameterized versions of mu and nu with size restrictions.

## 5. Functorial Combinators

Combinators over functors **inherit notation** from the base category **Lin**.

### 5.1 Functor Composition (.)

```
(.) : [Lin -> Lin] x [Lin -> Lin] -> [Lin -> Lin]
(G . F)(A) = G(F(A))
(G . F)(f) = G(F(f))
```

**Properties**:
- Associative: (H . G) . F = H . (G . F)
- Unit: Id . F = F . Id = F

**Application**: Construction of complex functors from simple ones (vertical composition).

### 5.2 Tensor Product of Functors (tensor)

**Inherits notation from the category Lin**:

```
(tensor) : [Lin -> Lin] x [Lin -> Lin] -> [Lin -> Lin]
(F tensor G)(A) = F(A) tensor G(A)
(F tensor G)(f) = F(f) tensor G(f)
```

**Properties**:
- Symmetric: F tensor G iso G tensor F (via sigma)
- Associative: (F tensor G) tensor H iso F tensor (G tensor H) (via alpha)
- Unit: K_1 tensor F iso F iso F tensor K_1

**Application**: Multiplicative combination of functors. The result contains both components independently.

**Example**:
```
(K_A tensor Id)(X) = A tensor X -- constant tensor with argument
(Id tensor Id)(X) = X tensor X -- quadratic functor
```

### 5.3 Par Product of Functors (par)

**Inherits notation from the category Lin**:

```
(par) : [Lin -> Lin] x [Lin -> Lin] -> [Lin -> Lin]
(F par G)(A) = F(A) par G(A)
(F par G)(f) = F(f) par G(f)
```

**Properties**:
- Dual to tensor at the level of functors
- Symmetric and associative
- Unit: K_bot

**Application**: Parallel composition of functorial effects.

### 5.4 Additive Conjunction of Functors (&)

**Inherits notation from the category Lin**:

```
(&) : [Lin -> Lin] x [Lin -> Lin] -> [Lin -> Lin]
(F & G)(A) = F(A) & G(A)
(F & G)(f) = F(f) & G(f)
```

**Properties**:
- Categorical product on functors
- Projections: tau_1 : F & G => F and tau_2 : F & G => G (natural transformations)
- Universal property: for sigma_1 : H => F and sigma_2 : H => G there exists <sigma_1, sigma_2> : H => F & G

**Application**: Nondeterministic choice between functorial effects.

**Example**:
```
(K_A & Id)(X) = A & X -- choice between constant and argument
(Id & Id)(X) = X & X -- choice between two copies
```

**Important**: Here the projections pi_1, pi_2 exist as natural transformations between functors, not as separate functors.

### 5.5 Additive Disjunction of Functors (direct sum)

**Inherits notation from the category Lin**:

```
(direct_sum) : [Lin -> Lin] x [Lin -> Lin] -> [Lin -> Lin]
(F direct_sum G)(A) = F(A) direct_sum G(A)
(F direct_sum G)(f) = F(f) direct_sum G(f)
```

**Properties**:
- Categorical coproduct on functors
- Injections: iota_1 : F => F direct_sum G and iota_2 : G => F direct_sum G (natural transformations)
- Universal property: for sigma_1 : F => H and sigma_2 : G => H there exists [sigma_1, sigma_2] : F direct_sum G => H

**Application**: Deterministic choice of a variant of the functorial effect.

**Example**:
```
(K_1 direct_sum (K_A tensor Id))(X) = 1 direct_sum (A tensor X) -- list functor (without mu)
```

### 5.6 Bifunctor Application Combinator (App)

For a bifunctor B and a functor F:

```
App(B, F) : Lin -> Lin
App(B, F)(X) = B(F(X), F(X))
```

**Examples**:
```
App(tensor, Id)(X) = X tensor X -- quadratic functor
App(&, K_A)(X) = A & A -- constant product
App(direct_sum, F)(X) = F(X) direct_sum F(X) -- disjunction of two F
```

**Application**: Construction of functors applying a bifunctor to the results of another functor.

### 5.7 Differential Combinator (d)

**Differentiation as a functorial combinator**:

```
d : [Lin -> Lin] -> [Lin -> Lin]
```

For any functor F, the derivative dF is a functor describing "one-hole contexts" in F.

#### Differentiation Rules

**Basic rules**:
```
d(Id)(A) = 1 -- derivative of a variable
d(K_C)(A) = 0 -- derivative of a constant
```

**Interaction with functorial combinators**:

1. **Tensor product** (Leibniz rule):
```
d(F tensor G)(A) = (dF(A) tensor G(A)) direct_sum (F(A) tensor dG(A))
```

Interpretation: The hole is either in the left component or in the right.

2. **Composition** (chain rule):
```
d(G . F)(A) = dG(F(A)) tensor dF(A)
```

Interpretation: Outer context tensor inner context.

3. **Additive combinators**:
```
d(F & G)(A) = dF(A) & dG(A) -- choice of derivative
d(F direct_sum G)(A) = dF(A) direct_sum dG(A) -- tagged derivative
```

4. **Par** (dual to tensor):
```
d(F par G)(A) = (dF(A) par G(A)) direct_sum (F(A) par dG(A))
```

#### Differentiation of Fixed Points

**Inductive types**:
```
d(mu F)(A) = Sigma_tensor(context : mu F(A)). dF(mu F(A))
```

**Interpretation**: A context is an element of the structure with a hole. The sum ranges over all possible positions of the hole.

**Example** (list):
```
F(X) = 1 direct_sum (A tensor X)
dF(X) = d(1) direct_sum d(A tensor X)
       = 0 direct_sum ((dA tensor X) direct_sum (A tensor dX))
       = (0 tensor X) direct_sum (A tensor 1)
       = A -- the hole can only be at an element position

d(List_A) = Sigma_tensor(context : List_A). A
           iso List_A tensor A -- pair: list before the hole and element after
```

More precisely:
```
d(List_A) = Sigma_tensor(prefix : List_A, suffix : List_A). 1
           iso List_A tensor List_A -- context = prefix tensor suffix
```

**Coinductive types**:
```
d(nu F)(A) = Sigma_tensor(n : Nat). dF^n(nu F(A))
```

**Interpretation**: A finite path to the hole in a potentially infinite structure.

#### Higher Derivatives

**n-th derivative**:
```
d^0(F) = F
d^{n+1}(F) = d(d^n(F))
```

**Semantics**: d^n(F)(A) describes contexts with **n holes** in the structure F(A).

**Symmetry property**:
```
d^n(F)(A) -- symmetric functor of n holes
```

#### Differential Calculus on Functors

**The differentiation operator commutes with certain operations**:

1. **Linearity over direct sum**:
```
d(F direct_sum G) = dF direct_sum dG
```

2. **Distributivity**:
```
d(F tensor (G direct_sum H)) = d(F tensor G) direct_sum d(F tensor H)
```

3. **The chain rule is preserved**:
```
d(H . G . F) = dH(G(F)) tensor dG(F) tensor dF
```

#### Connection with Modalities

**Differentiation of modalities**:
```
d(!A) = !A tensor A -- derivative of "of course"
d(?A) = ?A tensor A -- derivative of "why not"
```

**Interpretation**:
- d(!) singles out one use from many
- d(?) singles out one choice from the possible ones

#### Ultrafinitism and Differentiability

**Termination guarantee**: Thanks to sized types and the finiteness of all types:
- Differentiation always terminates
- d(mu F) is well-defined (finite depth)
- d(nu F) is well-defined (bounded paths)

**Universality**: All functors in **Lin** are differentiable without additional conditions.

## 6. The Complete System of Basic Functors

### 6.1 Minimal Basis

**Proposition** *(proof sketch)*: The following set of functors **generates** all polynomial functors on **Lin**:

1. **Id** -- identity functor
2. **K_C** -- constant functors (for each C)
3. **(-) tensor (-)** -- tensor product
4. **(-) & (-)** -- additive conjunction
5. **(-) direct_sum (-)** -- additive disjunction
6. **Sigma_tensor, Pi_&, Sigma_direct_sum** -- dependent functors
7. **mu, nu** -- fixed point operators

**Combinators**:
- Composition (.)
- Partial application of bifunctors

### 6.2 Expressiveness

**Any polynomial functor** F can be represented as:

```
F(X) = Sigma_direct_sum(i:I). C_i tensor X^{tensor n_i}
```

where:
- I is an index set (for variants)
- C_i are constant types (parameters of the variant)
- X^{tensor n_i} are tensor powers of the argument

**Construction example**:

List functor:
```
List : Lin -> Lin
List(A) = mu X. 1 direct_sum (A tensor X)

Decomposition:
List = mu . (K_1 + (lambda X. A tensor X))
     = mu . (K_1 direct_sum (K_A tensor Id))
```

Binary tree functor:
```
Tree(A) = mu X. A direct_sum (X tensor X)

Decomposition:
Tree = mu . (K_A direct_sum (Id tensor Id))
```

### 6.3 Extended Basis (with par)

If one includes:
- **(-) par (-)** -- par
- **Pi_par** -- dependent product par

Then one can express functors with parallel composition.

### 6.4 Differential Basis

For the differential category, one adds:
- **d** -- differentiation operator on functors

**Lin** is a differential category, and differentiation lifts to the level of functors.

#### Differential Functor

For any differentiable functor F there exists a differential functor **dF**:

```
d : [Lin -> Lin] -> [Lin -> Lin]
dF : Lin -> Lin
```

**Type of the derivative**:
```
dF(A) : Lin -- derivative of functor F at point A
```

**Interpretation**: dF(A) describes a "context" with one hole of type A inside the structure F(A).

#### Differentiation Rules for Functors

**Primitive functors**:
```
d(Id) = K_1 -- derivative of a variable is a constant
d(K_C) = K_0 -- derivative of a constant is zero
```

**MALL combinators** (Leibniz rule):
```
d(F tensor G) = (dF tensor G) direct_sum (F tensor dG) -- sum of partial derivatives
d(F & G) = (dF) & (dG) -- product of derivatives
d(F direct_sum G) = (dF) direct_sum (dG) -- coproduct of derivatives
d(F par G) = (dF par G) direct_sum (F par dG) -- dual to tensor
```

**Composition** (chain rule):
```
d(G . F) = (dG . F) tensor dF -- derivative of composition
```

**Fixed points**:
```
d(mu F) = Sigma_tensor(c : mu F). dF(mu F) -- context inside an inductive type
d(nu F) = Sigma_tensor(path : Nat). dF^n(nu F) -- finite paths in a coinductive type
```

Where F^n denotes the n-fold composition of F.

**Dependent types**:
```
d(Sigma_tensor_A(B)) = Sigma_tensor(a:A). (dB(a) direct_sum (B(a) tensor dA))
d(Pi_&_I(A)) = Pi_&(i:I). (dA(i) & (forall j != i. A(j)))
```

#### Ultrafinitism and Differentiability

**Theorem**: In the category **Lin** with sized types, all functors are differentiable.

**Justification**:
1. Every type has a finite size (by default 100500^100500)
2. All (co)inductive types have bounded depth
3. Differentiation always terminates
4. The derivative exists for any combination of basic functors

**Corollary**: No special positivity conditions are required for differentiability -- ultrafinitism guarantees correctness.

## 7. Examples of Functor Construction

### 7.1 List

```
List_A : Lin -> Lin
List_A = mu . F
  where F(X) = 1 direct_sum (A tensor X)
        F = K_1 direct_sum (K_A tensor Id)
```

**Decomposition**:
- Constant K_1 (empty list)
- Composition K_A tensor Id (head and tail)
- Coproduct direct_sum (variants)
- Fixed point mu (recursion)

### 7.2 Stream

```
Stream_A : Lin -> Lin
Stream_A = nu . F
  where F(X) = A & X
        F = (K_A) & Id
```

**Decomposition**:
- Constant K_A (head)
- Identity Id (tail)
- Additive conjunction & (both simultaneously)
- Fixed point nu (coinduction)

### 7.3 Dependent Vector (Vec)

```
Vec : Type -> Size -> Type
Vec(A, n) = mu^n V. (n = 0) & 1 direct_sum Sigma_tensor(m:Size). (n = s(m)) & (A tensor V(m))
```

**Decomposition**:
- Sigma_tensor -- dependent sum over the predecessor size
- & -- conjunction with the equality predicate
- tensor -- element and recursive tail
- direct_sum -- base case or recursion
- mu^n -- sized fixed point

### 7.4 Rose Tree Functor

```
Rose : Lin -> Lin
Rose(A) = mu X. A tensor (?(List(X)))
```

where ? is the multiset monad.

**Decomposition**:
- K_A tensor (? . List . Id)
- Functor composition: List then ?
- Tensor with constant
- Recursion via mu

### 7.5 Functor with Dependency

```
Sigma-List : (A : Type) -> (A -> Type) -> Type
Sigma-List(A, B) = mu X. 1 direct_sum Sigma_tensor(a:A). (B(a) tensor X)
```

**Decomposition**:
- Sigma_tensor -- dependent sum
- K_1 -- empty case
- tensor -- element of dependent type and tail
- direct_sum -- variants
- mu -- recursion

### 7.6 Examples of Functor Differentiation

#### 7.6.1 Differentiating a List

**Original functor**:
```
List_A = mu F, where F(X) = 1 direct_sum (A tensor X)
```

**Step 1**: Differentiate the body F
```
dF(X) = d(1 direct_sum (A tensor X))
       = d(1) direct_sum d(A tensor X)           -- rule for direct_sum
       = 0 direct_sum (dA tensor X direct_sum A tensor dX) -- Leibniz rule
       = 0 direct_sum (0 tensor X direct_sum A tensor 1)   -- dA = 0, dX = 1
       = A                                         -- simplification
```

**Step 2**: Apply the rule for mu
```
d(List_A) = Sigma_tensor(context : List_A). dF(List_A)
           = Sigma_tensor(context : List_A). A
           iso List_A tensor A
```

**Interpretation**: The derivative of a list is a list (position of the hole) tensor the element type.

**Alternative interpretation** (two fragments):
```
d(List_A) iso Sigma_tensor(prefix : List_A, suffix : List_A). 1
             iso List_A tensor List_A
```

The context splits the list into a prefix (before the hole) and a suffix (after the hole).

#### 7.6.2 Differentiating a Stream

**Original functor**:
```
Stream_A = nu F, where F(X) = A & X
```

**Step 1**: Differentiate the body
```
dF(X) = d(A & X)
       = dA & dX -- rule for &
       = 0 & 1   -- simplification
       iso 1
```

**Step 2**: Apply the rule for nu
```
d(Stream_A) = Sigma_tensor(n : Nat). dF^n(Stream_A)
             = Sigma_tensor(n : Nat). 1
             iso Nat
```

**Interpretation**: The derivative of a stream is a natural number (position in the stream, depth to the hole).

#### 7.6.3 Differentiating a Binary Tree

**Original functor**:
```
Tree_A = mu F, where F(X) = A direct_sum (X tensor X)
```

**Step 1**: Differentiate the body
```
dF(X) = d(A direct_sum (X tensor X))
       = dA direct_sum d(X tensor X)                   -- rule for direct_sum
       = 0 direct_sum (dX tensor X direct_sum X tensor dX) -- Leibniz rule
       = (1 tensor X) direct_sum (X tensor 1)           -- simplification
       = X direct_sum X
```

**Step 2**: Apply the rule for mu
```
d(Tree_A) = Sigma_tensor(context : Tree_A). (Tree_A direct_sum Tree_A)
           iso Sigma_tensor(context : Tree_A, direction : Bool). Tree_A
           iso Tree_A tensor Bool tensor Tree_A
```

**Interpretation**: A context in a tree is a tree (path to the hole), a direction (left/right subtree), and a tree (the other branch).

#### 7.6.4 Differentiating a Product

**Leibniz rule for functors**:
```
d(F tensor G)(A) = (dF(A) tensor G(A)) direct_sum (F(A) tensor dG(A))
```

**Example**: Pair of lists
```
F(A) = List_A tensor List_A

dF(A) = (d(List_A) tensor List_A) direct_sum (List_A tensor d(List_A))
       = ((List_A tensor A) tensor List_A) direct_sum (List_A tensor (List_A tensor A))
       iso (List_A tensor List_A tensor A) direct_sum (List_A tensor List_A tensor A)
```

**Interpretation**: The hole is either in the first list or in the second.

#### 7.6.5 Differentiating a Composition

**Chain rule**:
```
d(G . F)(A) = dG(F(A)) tensor dF(A)
```

**Example**: List of lists
```
F(A) = List_(List_A)

Let List = mu L, Inner = List_A
F = List . Inner

dF(A) = d(List)(Inner(A)) tensor d(Inner)(A)
       = (List_(Inner(A)) tensor Inner(A)) tensor (Inner(A) tensor A)
       iso List_(List_A) tensor List_A tensor List_A tensor A
```

**Interpretation**:
- Outer context: position in the list of lists
- Inner context: position in the inner list
- Their composition yields the full path to the element

#### 7.6.6 Differentiating a Dependent Sum

**Rule**:
```
d(Sigma_tensor_A(B)) = Sigma_tensor(a:A). (dB(a) direct_sum (B(a) tensor dA))
```

**Interpretation**: The hole is either in the dependent part B(a) or in the index a.

#### 7.6.7 Higher Derivatives

**Second derivative of a list**:
```
d^2(List_A) = d(d(List_A))
             = d(List_A tensor A)
             = d(List_A) tensor A direct_sum List_A tensor dA
             = (List_A tensor A) tensor A direct_sum List_A tensor 0
             iso List_A tensor A tensor A
             iso List_A tensor (A & A)
```

**Interpretation**: A context with two holes in a list.

**n-th derivative**:
```
d^n(List_A) iso List_A tensor A^{tensor n}
```

A context with n holes.

## 8. Functorial Laws and Correctness Verification

### 8.1 Functoriality Verification

For a functor F : **Lin** -> **Lin** the following must hold:

**Identity law**:
```
F(id_A) = id_{F(A)}
```

**Composition law**:
```
F(g . f) = F(g) . F(f)
```

### 8.2 Verification for Basic Functors

**Id**:
- Id(id_A) = id_A = id_{Id(A)}
- Id(g . f) = g . f = Id(g) . Id(f)

**K_C**:
- K_C(id_A) = id_C = id_{K_C(A)}
- K_C(g . f) = id_C = id_C . id_C = K_C(g) . K_C(f)

**tensor**:
- (f tensor g)(id_A tensor id_B) = id_A tensor id_B = id_{A tensor B}
- (f tensor g) . (f' tensor g') = (f . f') tensor (g . g')

### 8.3 Preservation of Functoriality by Combinators

**Composition**: If F and G are functors, then G . F is a functor.

**Proof**:
```
(G . F)(id_A) = G(F(id_A)) = G(id_{F(A)}) = id_{G(F(A))}
(G . F)(g . f) = G(F(g . f)) = G(F(g) . F(f)) = G(F(g)) . G(F(f))
```

**Tensor product**: If F and G are functors, then F tensor G is a functor.

**Proof**: Analogous, using the functorial laws for tensor in **Lin**.

**Coproduct**: If F and G are functors, then F direct_sum G is a functor.

### 8.4 Differential Laws

**Differentiation preserves functoriality**: If F is a functor, then dF is a functor.

#### Basic Differentiation Rules

**Constant rule**:
```
d(K_C) = K_0
```

**Variable rule**:
```
d(Id) = K_1
```

**Functoriality verification** for d(Id) = K_1:
```
K_1(id_A) = id_1 = id_{K_1(A)}
K_1(g . f) = id_1 = id_1 . id_1 = K_1(g) . K_1(f)
```

#### Leibniz Rule

**For tensor product**:
```
d(F tensor G) = (dF tensor G) direct_sum (F tensor dG)
```

**Functoriality proof**:

Let F and G be functors. We show that d(F tensor G) is a functor.

*Identity law*:
```
d(F tensor G)(id_A) = (dF tensor G)(id_A) direct_sum (F tensor dG)(id_A)
                     = (dF(id_A) tensor G(id_A)) direct_sum (F(id_A) tensor dG(id_A))
                     = (id_{dF(A)} tensor id_{G(A)}) direct_sum (id_{F(A)} tensor id_{dG(A)})
                     = id_{dF(A) tensor G(A)} direct_sum id_{F(A) tensor dG(A)}
                     = id_{(dF tensor G)(A) direct_sum (F tensor dG)(A)}
                     = id_{d(F tensor G)(A)}
```

*Composition law*: Verified analogously, through the distributivity of direct_sum.

#### Chain Rule

**For functor composition**:
```
d(G . F) = (dG . F) tensor dF
```

**Functoriality proof**:

*Identity law*:
```
d(G . F)(id_A) = (dG . F)(id_A) tensor dF(id_A)
                = dG(F(id_A)) tensor dF(id_A)
                = dG(id_{F(A)}) tensor id_{dF(A)}
                = id_{dG(F(A))} tensor id_{dF(A)}
                = id_{dG(F(A)) tensor dF(A)}
                = id_{d(G . F)(A)}
```

*Composition law*: Follows from the functoriality of tensor and composition.

#### Linearity of Differentiation

**Over additive disjunction**:
```
d(F direct_sum G) = dF direct_sum dG
```

**Proof**: direct_sum is functorial pointwise; the derivative of variants is the variant of derivatives.

**Over additive conjunction**:
```
d(F & G) = dF & dG
```

**Proof**: & is functorial pointwise; the derivative of a choice is the choice of derivatives.

#### Rules for Fixed Points

**Inductive types**:
```
d(mu F) = Sigma_tensor(context : mu F). dF(mu F)
```

**Property**: Functoriality follows from the functoriality of Sigma_tensor and dF.

**Coinductive types**:
```
d(nu F) = Sigma_tensor(depth : Nat). dF^depth(nu F)
```

**Property**: A finite sum of functors is functorial.

#### Differential Identities

**Idempotency of zero**:
```
d(K_0) = K_0
d(0) = 0
```

**Derivative of a sum**:
```
d(F direct_sum G direct_sum H) = dF direct_sum dG direct_sum dH
```

**Derivative of an n-ary tensor**:
```
d(F_1 tensor F_2 tensor ... tensor F_n) = sum_i (F_1 tensor ... tensor dF_i tensor ... tensor F_n)
```

Generalized Leibniz rule.

**Derivative of a power**:
```
d(X^{tensor n}) = n . X^{tensor (n-1)}
```

where . denotes the multiplicative constant (n-fold direct_sum).

#### Universality of Differentiation

**Theorem**: In the category **Lin** with sized types:
1. Every functor F is differentiable
2. dF is a functor
3. Differentiation preserves all functorial properties
4. Higher derivatives d^n F are well-defined for all n

**Corollary**: The category of functors [**Lin**, **Lin**] is a **differential category** with the operator d.

## 9. The Category of Endofunctors [Lin, Lin]

### 9.1 Structure of the Category

**Objects**: Endofunctors F : **Lin** -> **Lin**

**Morphisms**: Natural transformations tau : F => G

**Composition**: Vertical composition of natural transformations

**Identity**: Identity natural transformation id_F

### 9.2 Monoidal Structure

**Monoidal product 1**: Functor composition (.)
- Unit: Id
- Associator: alpha_{F,G,H} : (F . G) . H iso F . (G . H)

This makes [**Lin**, **Lin**] a monoidal category.

**Monoidal product 2**: Functor tensor (tensor)
- (F tensor G)(A) = F(A) tensor G(A)
- Unit: K_1
- Inherits symmetry and associativity from tensor in **Lin**

### 9.3 Binoidal Structure

**The functor category inherits the binoidal structure** from **Lin**:

**Additive conjunction of functors**: F & G
- (F & G)(A) = F(A) & G(A)
- Projections: tau_1 : F & G => F, tau_2 : F & G => G (natural transformations)
- Universal property of the product

**Additive disjunction of functors**: F direct_sum G
- (F direct_sum G)(A) = F(A) direct_sum G(A)
- Injections: iota_1 : F => F direct_sum G, iota_2 : G => F direct_sum G
- Universal property of the coproduct

**Dual monoidal structure**: F par G
- (F par G)(A) = F(A) par G(A)
- Dual to F tensor G

### 9.4 Inheritance of Structure from Lin

**Inheritance Principle**: The category of endofunctors [**Lin**, **Lin**] inherits structure from **Lin** pointwise.

For any structure in **Lin** (where the operation is any of {tensor, par, &, direct_sum}):
```
(F op G)(A) := F(A) op G(A) (applied pointwise)
(F op G)(f) := F(f) op G(f) (on morphisms)
```

**Inherited properties**:

1. **From monoidal structure** (tensor, 1):
   - F tensor G is monoidal if F and G are monoidal
   - K_1 is the unit for tensor on functors
   - Associativity and symmetry are preserved

2. **From binoidal structure** (&, direct_sum):
   - F & G has projections (natural transformations)
   - F direct_sum G has injections (natural transformations)
   - Universal properties lift to the level of functors

3. **From duality** (tensor <-> par):
   - (F tensor G)^perp iso F^perp par G^perp (if negation on functors is defined)

4. **From distributivity**:
   - F tensor (G direct_sum H) iso (F tensor G) direct_sum (F tensor H)
   - Preserved at the level of functors

**Categorical interpretation**: [**Lin**, **Lin**] with pointwise operations forms:
- A monoidal category (with . and tensor)
- A binoidal category (with & and direct_sum)
- A *-autonomous structure (via par)

All key properties of **Lin** "lift" to the functor category.

### 9.5 Differential Structure

**[Lin, Lin] is a differential category**.

#### Differentiation Operator on Functors

```
d : [Lin -> Lin] -> [Lin -> Lin]
```

**Properties**:
1. d is an endofunctor on the functor category
2. d preserves functoriality (if F is a functor, then dF is a functor)
3. d interacts with the monoidal and binoidal structure

#### Interaction with Monoidal Structure

**Leibniz rule for tensor**:
```
d(F tensor G) iso (dF tensor G) direct_sum (F tensor dG)
```

There exists a natural isomorphism (differentiation distributor):
```
delta_tensor : d(F tensor G) => (dF tensor G) direct_sum (F tensor dG)
```

**Rule for composition (chain rule)**:
```
d(G . F) iso (dG . F) tensor dF
```

Natural transformation:
```
chain : d(G . F) => (dG . F) tensor dF
```

#### Interaction with Binoidal Structure

**Linearity over direct_sum**:
```
d(F direct_sum G) iso dF direct_sum dG
```

The isomorphism is natural: differentiation commutes with the coproduct.

**Distributivity through &**:
```
d(F & G) iso dF & dG
```

The isomorphism is natural: differentiation commutes with the product.

#### Differential Categorical Structure

**Definition**: A differential category is a category K with:
1. A monoidal structure (tensor, I)
2. A differentiation functor d : K -> K
3. Natural transformations delta_tensor, chain satisfying the axioms

**Theorem**: [**Lin**, **Lin**] with the operator d is a differential category.

**Proof**:
- tensor on functors is monoidal (inherited from **Lin**)
- d is functorial (Section 8.4)
- delta_tensor and chain are natural and satisfy the axioms of a differential category

#### Universal Property of Differentiation

For any functor F, the derivative dF satisfies:
```
F(A direct_sum epsilon . B) iso F(A) direct_sum epsilon . (dF(A) tensor B)
```

where epsilon is a formal "infinitesimal" (epsilon^2 = 0).

**Interpretation**: dF(A) is the "directional derivative" of functor F at point A.

#### Operator Properties of d

**1. Idempotency on the constant**:
```
d(K_0) = K_0
d^2(K_C) = K_0 (for C != 0)
```

**2. Commutativity with natural transformations**:

If tau : F => G is a natural transformation, then:
```
d tau : dF => dG
```
is also a natural transformation.

**3. Preservation of fixed points**:

For an algebra alpha : F(A) -> A:
```
d alpha : dF(A) tensor A -> A
```

The derivative of an algebra is the "update" of the structure.

#### Higher Derivatives and Tensor Powers

**n-th derivative of a functor**:
```
d^n F : Lin -> Lin
d^0 F = F
d^{n+1} F = d(d^n F)
```

**Property**: d^n F(A) describes contexts with n holes of type A.

**Symmetry**:
```
d^n F(A) iso d^n F(A) tensor Sym_n
```

where Sym_n is the symmetric group of order n (permutations of holes).

#### Connection with the Gateaux Derivative

In **Lin**, differentiation of functors corresponds to the **Gateaux derivative**:
```
lim_{epsilon -> 0} [F(A direct_sum epsilon . B) minus F(A)] / epsilon = dF(A) tensor B
```

where minus is the inverse operation to direct_sum (in linear logic).

#### Practical Significance

**For programming**:
- dF describes "contexts" or "zippers"
- d^n F describes multipoint cursors
- Differentiation yields efficient data structures for navigation

**For type theory**:
- The derivative of a type is the type of its one-hole contexts
- The chain rule corresponds to context composition
- Higher derivatives are multipoint contexts

**For categorical semantics**:
- [**Lin**, **Lin**] is a differential category
- Differentiation is a universal operation on functors
- All constructions are differentiable thanks to ultrafinitism

## 10. Computational Interpretation

### 10.1 Functors as Containers

A functor F can be interpreted as a "container" with structure:
- **Shapes**: Sigma_direct_sum(s:Shape). ...
- **Positions**: ... tensor X^{tensor n}

**Example**: The list functor
- Shapes: lengths n in Nat
- Positions: n positions for elements

### 10.2 Functors as Syntax Trees

F(X) describes a syntax tree with variables of type X:
- Constants K_C are leaves
- Connectives tensor, &, direct_sum are nodes
- Id marks variable positions

### 10.3 Functors in Programming

Correspondence with functional programming:
- mu F -- inductive data type (data)
- nu F -- coinductive data type (codata)
- F -- functor signature (in Haskell: Functor, Bifunctor)
- Natural transformations -- polymorphic functions

## 11. Modal Functors

**Important remark**: Modal functors **are not part of the basic functor system** (Sections 1--8), but the structure of the category **Lin** and of the basic functors allows one to define them naturally through (co)inductive types.

### 11.1 Exponential Modalities

#### 11.1.1 Comonad "Of Course" (!)

**Definition as a (co)inductive functor**:
```
! : Lin -> Lin
!A = nu X. 1 direct_sum (A & X)
```

**Construction via basic functors**:
```
! = nu . F
where F(X) = 1 direct_sum (A & X)
      F = K_1 direct_sum ((K_A) & Id)
```

**Functoriality**:
```
!(f : A -> B) : !A -> !B
```

**Comonadic structure**:
- **counit (epsilon)**: epsilon : !A -> A
  - Extraction of a single use
  - Realized via the projection A & X -> A

- **comultiplication (delta)**: delta : !A -> !!A
  - Duplication of a resource
  - Realized via doubling of the coinductive stream

- **weakening (w)**: w : !A -> 1
  - Discarding of an unused resource

- **contraction (c)**: c : !A -> !A tensor !A
  - Splitting of a resource

**Derivative**:
```
d(!A) iso !A tensor A
```

**Interpretation**: !A is a potentially infinite stream of values of type A, available for unrestricted use.

#### 11.1.2 Monad "Why Not" (?)

**Definition as a (co)inductive functor**:
```
? : Lin -> Lin
?A = mu X. top direct_sum (A tensor X)
```

**Construction via basic functors**:
```
? = mu . F
where F(X) = top direct_sum (A tensor X)
      F = K_top direct_sum ((K_A) tensor Id)
```

**Functoriality**:
```
?(f : A -> B) : ?A -> ?B
```

**Monadic structure**:
- **unit (eta)**: eta : A -> ?A
  - Wrapping a single value
  - Realized via inr . (id_A tensor (inl top))

- **multiplication (mu)**: mu : ??A -> ?A
  - Flattening of nested multisets
  - Realized via catamorphism

- **absorption (a)**: a : top -> ?A
  - Empty multiset

- **addition (+)**: + : ?A tensor ?A -> ?A
  - Union of multisets

**Derivative**:
```
d(?A) iso ?A tensor A
```

**Interpretation**: ?A is a finite multiset (list with duplicates) of values of type A.

#### 11.1.3 Functional Duality ! -| ?

**Adjunction**:
```
Lin(!A, B) iso Lin(A, ?B)
```

**Natural transformations**:
- **Structural symmetry**: nu <-> mu, & <-> tensor, direct_sum <-> direct_sum
- **Functional duality**: comonad <-> monad

**Remark on linear negation**: Exact categorical duality via (-)^perp is not achieved due to differences in units (1 vs. top) and the nature of MALL connectives.

### 11.2 Temporal Modalities

#### 11.2.1 Always in the Future (Box)

**Definition**:
```
Box : Lin -> Lin
Box A = nu X. A & X
```

**Construction**:
```
Box = nu . ((K_A) & Id)
```

**Functoriality**: Obvious from the composition of basic functors.

**Interpretation**: A coinductive stream of values A at each moment of time.

**Rules**:
- **now**: pi_1 : Box A -> A (current value)
- **next**: pi_2 : Box A -> Box A (shift to the next moment)

**Derivative**:
```
d(Box A) iso Nat tensor A
```
Position in the stream and the value at that position.

**With dependent types**:
```
Box_t : (Time -> Type) -> Type
Box_t A = Pi_&(t':Time, t' >= t). A(t')
```
Using Pi_& from Section 3.

**Enrichment**:
- Box^d A -- with duration of the interval
- Sigma_tensor(t:Time). Box_{>= t} A(t) -- parameterization by time

#### 11.2.2 Eventually in the Future (Diamond)

**Definition**:
```
Diamond : Lin -> Lin
Diamond A = mu X. A direct_sum X
```

**Construction**:
```
Diamond = mu . ((K_A) direct_sum Id)
```

**Interpretation**: An inductive type -- either A now, or A later.

**Rules**:
- **now**: inl : A -> Diamond A
- **later**: inr : Diamond A -> Diamond A

**Derivative**:
```
d(Diamond A) iso Nat tensor A
```
The step number at which A is reached.

**Duality**: Box and Diamond are functionally dual (nu <-> mu, & <-> direct_sum).

**With dependent types**:
```
Diamond_t A = Sigma_direct_sum(t':Time, t' >= t). A(t')
```

#### 11.2.3 LTL Operators

**Until (U)**:
```
U : Lin x Lin -> Lin
(A U B) = mu X. B direct_sum (A tensor X)
```

**Functorial construction**:
```
U(A, B) = mu . (K_B direct_sum ((K_A) tensor Id))
```

**Interpretation**: A holds until B occurs.

**Release (R)**:
```
R : Lin x Lin -> Lin
(A R B) = nu X. B & (A par X)
```

**Duality**: U and R are dual (mu <-> nu, direct_sum <-> &, tensor <-> par).

**With dependent types**:
```
U_{<= n} : Sigma_tensor(k:Nat_{<= n}). ((A U_k B)) -- bounded until
```

**Derivative of Until**:
```
d(A U B) iso Sigma_tensor(n:Nat). (A^{tensor n} tensor B)
```
n steps of waiting until B.

### 11.3 Spatial Modalities

#### 11.3.1 Everywhere (Box_S)

**Definition**:
```
Box_S : (Location -> Type) -> Type
Box_S A = Pi_&(l:Location). A(l)
```

**Construction**: Via Pi_& (Section 3.3).

**Functoriality**: Inherited from Pi_&.

**Interpretation**: Indexed product over all locations.

**With dependent types**:
```
Box_r : Sigma_tensor(center:Location). Pi_&(l:Location, d(l,center) <= r). A(l)
```
Within radius r of the center.

#### 11.3.2 Somewhere (Diamond_S)

**Definition**:
```
Diamond_S : (Location -> Type) -> Type
Diamond_S A = Sigma_direct_sum(l:Location). A(l)
```

**Construction**: Via Sigma_direct_sum (Section 3.4).

**Interpretation**: Indexed coproduct over locations.

**Duality**: Box_S and Diamond_S are dual (Pi_& <-> Sigma_direct_sum).

**With dependent types**:
```
Diamond_Region : Sigma_tensor(r:Region). (Sigma_direct_sum(l:r). A(l))
```
By regions.

### 11.4 Deontic Modalities

#### 11.4.1 Obligatory (O)

**Definition**:
```
O : Lin -> Lin
O A = nu X. A & (X direct_sum Violation)
```

**Construction**:
```
O = nu . ((K_A) & (Id direct_sum K_Violation))
```

**Interpretation**: A coinductive sequence of obligation checks.

**Rules**:
- **current**: pi_1 : O A -> A (current fulfillment)
- **continue**: pi_2 : O A -> O A direct_sum Violation (continuation or violation)

**With dependent types**:
```
O_c : Sigma_tensor(c:Context). (A(c) & Obligation(c))
```
The obligation depends on context.

**Enrichment**:
- Pi_&(p:Priority). O_p A -- with priorities
- Sigma_direct_sum(a:Agent). O_a A -- who is obligated
- Pi_par(cond:Condition). O A -- conditional obligation

#### 11.4.2 Permitted (P)

**Definition**:
```
P : Lin -> Lin
P A = mu X. A direct_sum (X & Grant)
```

**Construction**:
```
P = mu . ((K_A) direct_sum (Id & K_Grant))
```

**Interpretation**: An inductive sequence of permissions.

**Duality**: O and P are functionally dual (nu <-> mu).

### 11.5 Alethic Modalities

#### 11.5.1 Necessarily (Box_N)

**Definition**:
```
Box_N : (World -> Type) -> Type
Box_N A = Pi_&(w:World). A(w)
```

**Construction**: Via Pi_& over possible worlds.

**Interpretation**: A is true in all possible worlds.

**With dependent types**:
```
Box_R : Sigma_tensor(w_0:World). Pi_&(w:World, R(w_0,w)). A(w)
```
Via the accessibility relation R.

**Enrichment**:
- Sigma_tensor(n:Nat). Box^n_N A -- with modal depth
- Pi_&(w:World). (A(w) tensor Prob(w)) -- weighted necessity

#### 11.5.2 Possibly (Diamond_N)

**Definition**:
```
Diamond_N : (World -> Type) -> Type
Diamond_N A = Sigma_direct_sum(w:World). A(w)
```

**Construction**: Via Sigma_direct_sum over worlds.

**Interpretation**: A is true in some world.

**Duality**: Box_N and Diamond_N are dual (Pi_& <-> Sigma_direct_sum).

### 11.6 Epistemic Modalities

#### 11.6.1 Agent Knowledge (K_a)

**Definition**:
```
K_a : (State_a -> Type) -> Type
K_a A = Pi_&(s:State_a). A(s)
```

**Construction**: Via Pi_& over the states of agent a.

**Interpretation**: Agent a knows A if A is true in all states that the agent considers possible.

**With dependent types**:
```
K_a^t : Pi_&(s:State_a(t)). A(s) -- temporal knowledge
```

**Enrichment**:
- K_a(Sigma_tensor(b:Agent). K_b A) -- knowledge about others' knowledge
- Sigma_tensor(c:Confidence). (K_a A tensor c) -- with confidence level
- Pi_par(e:Evidence). K_a A -- conditional knowledge

#### 11.6.2 Common Knowledge (C)

**Definition**:
```
C : (Agent -> Type) -> Type
C A = nu X. A & (Pi_&(a:Agent). K_a X)
```

**Construction**:
```
C = nu . ((K_A) & (Pi_&(a:Agent). K_a . Id))
```

**Interpretation**: Coinductive: everyone knows A, everyone knows that everyone knows A, and so on.

**Rules**:
- **base**: pi_1 : C A -> A
- **induction**: pi_2 : C A -> Pi_&(a:Agent). K_a(C A)

**With dependent types**:
```
C_G : Sigma_tensor(G:Group). (nu X. A & (Pi_&(a:G). K_a X))
```
Common knowledge within group G.

### 11.7 Probabilistic Modalities

#### 11.7.1 With Probability p (Box_p)

**Definition**:
```
Box_p : Lin -> Lin
Box_p A = A tensor Prob(p)
```

**Construction**: Simple tensor with the probability type.

**Functoriality**: Obvious (composition with K_Prob(p)).

**With dependent types**:
```
Box_cond : Sigma_tensor(e:Evidence). (A tensor Prob(A|e))
```
Conditional probability.

**Enrichment**:
- Pi_par(obs:Observation). (Box_p A -> Box_{p'} A) -- Bayesian updating

#### 11.7.2 Distribution (D)

**Definition**:
```
D : Lin -> Lin
D A = Sigma_direct_sum(n:Nat). (A^{tensor n} tensor Distribution(n))
```

**Construction**:
```
D = Sigma_direct_sum(n:Nat) . ((-)^{tensor n} tensor K_Distribution(n))
```

**Interpretation**: A discrete probability distribution over A.

**With dependent types**:
```
D_theta : Sigma_tensor(theta:Parameters). D_theta A
```
Parameterized distributions.

### 11.8 Affine and Relevant Modalities

#### 11.8.1 Affine (Circle)

**Definition**:
```
Circle : Lin -> Lin
Circle A = A direct_sum 1
```

**Construction**:
```
Circle = (-) direct_sum K_1
```

**Interpretation**: Resource A may be used or discarded.

**Rules**:
- **use**: inl : A -> Circle A
- **discard**: inr : 1 -> Circle A

**With dependent types**:
```
Circle_cond : Pi_par(cond:Condition). (A direct_sum 1(cond))
```
Conditional affinity.

#### 11.8.2 Relevant (Bullseye)

**Definition**:
```
Bullseye : Lin -> Lin
Bullseye A = mu X. A direct_sum (A tensor X)
```

**Construction**:
```
Bullseye = mu . ((K_A) direct_sum ((K_A) tensor Id))
```

**Interpretation**: At least one use of A, possibly more.

**With dependent types**:
```
Bullseye_n : Sigma_tensor(n:Nat_{>0}). A^{tensor n}
```
Exact relevance -- precisely n uses.

### 11.9 Graded Modalities

#### 11.9.1 Exactly n (Box_n)

**Definition**:
```
Box_n : Lin -> Lin
Box_n A = A^{tensor n}
```

**Construction**: n-fold tensor.

**Functoriality**: Composition of n copies of the functor.

**With dependent types**:
```
Box_dep : Sigma_tensor(n:Nat). Box_n(A(n))
```
The grade depends on the type.

#### 11.9.2 At Most n (Box_{<= n})

**Definition**:
```
Box_{<= n} : Lin -> Lin
Box_{<= n} A = Sigma_direct_sum(k:Nat_{<= n}). A^{tensor k}
```

**Construction**: Coproduct over k in [0, n].

**Interpretation**: From 0 to n uses of A.

#### 11.9.3 At Least n (Box_{>= n})

**Definition**:
```
Box_{>= n} : Lin -> Lin
Box_{>= n} A = A^{tensor n} tensor !A
```

**Construction**: n uses plus an unrestricted remainder.

**Interpretation**: At least n, possibly infinitely many.

**With dependent types**:
```
Box_interval : Sigma_tensor(n,m:Nat, n <= m). (Sigma_direct_sum(k:Nat_{[n,m]}). A^{tensor k})
```
Interval grading [n, m].

### 11.10 Categorical Structure of Modal Functors

#### Monads and Comonads

**Comonads**:
- ! -- exponential comonad
- O -- deontic comonad (obligation)
- C -- epistemic comonad (common knowledge)

**Structure**:
```
epsilon : Box A -> A (counit)
delta : Box A -> Box Box A (comultiplication)
```

**Monads**:
- ? -- exponential monad
- P -- deontic monad (permission)
- Diamond -- temporal monad (eventually)

**Structure**:
```
eta : A -> Diamond A (unit)
mu : Diamond Diamond A -> Diamond A (multiplication)
```

#### Adjunctions

**Temporal**: Box -| Diamond (functionally, via nu -| mu)

**Exponential**: ! -| ? (functional duality)

**Spatial**: Box_S -| Diamond_S (via Pi_& -| Sigma_direct_sum)

**Alethic**: Box_N -| Diamond_N (via Pi_& -| Sigma_direct_sum)

#### Composition of Modalities

Modalities compose as functors:

```
(! Box) : Lin -> Lin
(! Box) A = !(Box A) -- unrestricted use of a stream
```

```
(Box !) : Lin -> Lin
(Box !) A = Box(!A) -- stream of unrestricted values
```

```
(K_a . Box) : Lin -> Lin
(K_a . Box) A = K_a(Box A) -- agent knows that A always holds
```

**Commutativity**: Some modalities commute:
```
Box_S . Box_t iso Box_t . Box_S -- time and space are independent
```

**Non-commutativity**: Others do not:
```
K_a . Box != Box . K_a -- knowledge about the future vs. guaranteed future knowledge
```

### 11.11 Differentiation of Modalities

**Exponential**:
```
d(!A) iso !A tensor A -- single out one use
d(?A) iso ?A tensor A -- remove one element from the multiset
```

**Temporal**:
```
d(Box A) iso Nat tensor A -- position in the stream
d(Diamond A) iso Nat tensor A -- step number
d(A U B) iso Sigma_tensor(n:Nat). (A^{tensor n} tensor B) -- path to B
```

**Spatial**:
```
d(Box_S A) iso Sigma_tensor(l:Location). A(l) -- focus on one location
d(Diamond_S A) iso 0 -- location already chosen
```

**Alethic**:
```
d(Box_N A) iso Sigma_tensor(w:World). A(w) -- focus on one world
```

**Graded**:
```
d(Box_n A) iso n . A^{tensor (n-1)} -- remove one of n
d(Bullseye A) iso Sigma_tensor(n:Nat). A^{tensor n} -- position in the chain
```

**Interpretation**: The derivative of a modality describes the "focus context" within the modal structure.

### 11.12 The Role of Dependent Types in Modalities

**Enrichment through the four dependent connectives**:

1. **Sigma_tensor (dependent tensor sum)**:
   - Parameterization of modalities
   - Sigma_tensor(t:Time). Box_{>= t} A(t) -- temporal parameterization
   - Sigma_tensor(c:Context). O_c A -- contextual obligation

2. **Pi_par (dependent par product)**:
   - Conditional modalities
   - Pi_par(cond:Condition). O A -- conditional obligation
   - Pi_par(e:Evidence). K_a A -- conditional knowledge

3. **Pi_& (dependent additive product)**:
   - Indexed modalities
   - Pi_&(t:Time). A(t) -- temporal indexing
   - Pi_&(w:World). A(w) -- modal indexing
   - Pi_&(l:Location). A(l) -- spatial indexing
   - Pi_&(a:Agent). K_a A -- multi-agent indexing

4. **Sigma_direct_sum (dependent additive sum)**:
   - Variant choice with dependency
   - Sigma_direct_sum(w:World). A(w) -- world choice
   - Sigma_direct_sum(l:Location). A(l) -- location choice

**Theorem**: Dependent types increase the expressive power of modalities exponentially, enabling parameterized, indexed, and conditional modal systems.

### 11.13 Summary of Modal Functors

**Architecture**:
- **Basic functors (Sections 1--8)**: MALL, dependent types, (co)induction, differentiation
- **Modal functors (Section 11)**: Definable extensions

**Construction principle**: Any modality expressible through:
- (Co)inductive types (mu, nu)
- MALL connectives (tensor, par, &, direct_sum)
- Dependent functors (Sigma_tensor, Pi_par, Pi_&, Sigma_direct_sum)

can be defined as a functor in [**Lin**, **Lin**].

**Categorical structure of modalities**:
1. Many modalities are (co)monads
2. Adjunctions exist between dual modalities
3. Modalities compose functorially
4. All modalities are differentiable

**Practical significance**:
- **Verification**: Temporal modalities for model checking
- **Distributed systems**: Spatial modalities
- **Multi-agent systems**: Epistemic modalities
- **Normative systems**: Deontic modalities
- **Resources**: Graded and affine modalities
- **Probability**: Probabilistic modalities

**Advantages of the uniform approach**:
- General theory for all modalities
- Automatic inheritance of properties (functoriality, differentiability)
- Compositionality of modal systems
- The role of dependent types in enriching modalities

## 12. Summary: Universality of Basic Functors

**Architecture of the functor system**:
- **Sections 1--9**: Basic system (primitives, MALL, dependent, fixed points, combinators, differentiation)
- **Section 10**: Computational interpretation
- **Section 11**: Modal functors (definable extensions)
- **Section 12**: Summary and completeness theorems

### Complete System of Basic Functors

**Minimal basis for polynomial functors**:
1. **Primitives**: Id, K_C, Delta
2. **MALL functors**: tensor, &, direct_sum (bifunctors on objects)
3. **Dependent functors**: Sigma_tensor, Pi_&, Sigma_direct_sum
4. **Fixed point operators**: mu, nu

**Extended basis**:
5. **Dual multiplicatives**: par, Pi_par
6. **Differential**: d
7. **Modal**: !, ? (definable from the basis)

**Functorial combinators** (operations on functors):
- Composition (.)
- Tensor product of functors (tensor)
- Additive conjunction of functors (&)
- Additive disjunction of functors (direct_sum)
- Par of functors (par)
- Differentiation of functors (d)
- Partial application of bifunctors

**Inheritance of structure**: The combinators tensor, &, direct_sum, par on functors inherit the properties of the eponymous connectives from the category **Lin**. The differential operator d inherits the differential structure.

### Completeness of the Basis (Proposition -- proof sketch)

**Proposition**: Any strictly positive polynomial functor F : **Lin** -> **Lin** can be constructed from basic functors and combinators.

*Proof sketch*: By induction on the structure of the strictly positive functor. Base case: Id and K_C cover variables and constants. Inductive step: tensor, &, direct_sum are closed under strict positivity; Sigma_tensor, Pi_&, Sigma_direct_sum provide dependent generalizations; mu and nu give fixed points. Full formalization is a subject of further work (see also the Agda code in `code/agda/`).

**Corollary**: The system of basic functors is **universal** for describing data types in the category **Lin**.

### Differential Completeness

**Theorem**: For any functor F constructed from basic functors, the derivative dF is well-defined and is a functor.

**Corollary**: [**Lin**, **Lin**] is a **differential category**.

**Key properties of differentiation**:
1. **Leibniz rule**: d(F tensor G) = (dF tensor G) direct_sum (F tensor dG)
2. **Chain rule**: d(G . F) = (dG . F) tensor dF
3. **Linearity**: d(F direct_sum G) = dF direct_sum dG
4. **Universality**: All functors are differentiable (thanks to ultrafinitism)

**Interpretation**: dF(A) is the type of one-hole contexts ("holes") in the structure F(A). Higher derivatives d^n F describe n-point contexts.

### Modal Expressiveness

**Theorem**: Any modality expressible through (co)inductive types, MALL connectives, and dependent functors can be defined as a functor in [**Lin**, **Lin**].

**Examples of modal functors**:

1. **Exponential**:
   - ! = nu X. 1 direct_sum (A & X) -- comonad "of course"
   - ? = mu X. top direct_sum (A tensor X) -- monad "why not"
   - Functional duality: ! -| ?

2. **Temporal**:
   - Box = nu X. A & X -- always in the future
   - Diamond = mu X. A direct_sum X -- eventually
   - A U B = mu X. B direct_sum (A tensor X) -- until
   - A R B = nu X. B & (A par X) -- release

3. **Spatial**:
   - Box_S = Pi_&(l:Location). A(l) -- everywhere
   - Diamond_S = Sigma_direct_sum(l:Location). A(l) -- somewhere

4. **Deontic**:
   - O = nu X. A & (X direct_sum Violation) -- obligatory
   - P = mu X. A direct_sum (X & Grant) -- permitted

5. **Alethic**:
   - Box_N = Pi_&(w:World). A(w) -- necessarily
   - Diamond_N = Sigma_direct_sum(w:World). A(w) -- possibly

6. **Epistemic**:
   - K_a = Pi_&(s:State_a). A(s) -- agent knowledge
   - C = nu X. A & (Pi_&(a:Agent). K_a X) -- common knowledge

7. **Graded**:
   - Box_n = A^{tensor n} -- exactly n uses
   - Box_{<= n} = Sigma_direct_sum(k:Nat_{<= n}). A^{tensor k} -- at most n
   - Box_{>= n} = A^{tensor n} tensor !A -- at least n

**Categorical structure of modalities**:
- Many modalities are (co)monads
- Adjunctions exist between dual modalities
- Modalities compose functorially
- All modalities are differentiable

**The role of dependent types**: Dependent functors (Sigma_tensor, Pi_par, Pi_&, Sigma_direct_sum) exponentially increase the expressiveness of modalities, enabling parameterized, indexed, and conditional modal systems.

**Corollary**: The functor system of **Lin** provides a uniform foundation for diverse modal logics.

### Categorical Structure of [Lin, Lin]

The category of endofunctors inherits and enriches the structure of **Lin**:

1. **Monoidal structure**:
   - Composition (.) with unit Id
   - Tensor (tensor) with unit K_1

2. **Binoidal structure**:
   - Product (&) with projections
   - Coproduct (direct_sum) with injections

3. ***-autonomous structure**:
   - Dual tensor (par)
   - Inheritance of duality from **Lin**

4. **Differential structure**:
   - Operator d : [Lin -> Lin] -> [Lin -> Lin]
   - Distributor delta_tensor and chain rule chain
   - Higher derivatives d^n

### Practical Significance

**For category theory**:
- **Universality**: The basis expresses all polynomial functors
- **Differentiability**: All constructions have derivatives
- **Inheritance**: The structure of **Lin** lifts to [**Lin**, **Lin**]
- **Completeness**: The system is closed under all operations

**For programming**:
- **Modularity**: Complex data types are built from simple parts
- **Compositionality**: Properties of functors compose
- **Verification**: Functorial laws are verified on basic functors
- **Navigation**: Derivatives yield zippers (contexts with holes)
- **Efficiency**: Differentiation automatically generates traversal structures
- **Modalities**: Uniform foundation for effects, resources, time, space

**For type theory**:
- **Expressiveness**: Dependent types + (co)induction + differentials + modalities
- **Constructivity**: All constructions are computable
- **Ultrafinitism**: Sizes guarantee termination of differentiation
- **Implementation**: Basis for compilers and proof assistants
- **Modal systems**: Temporal, spatial, epistemic logics

**Applications of modalities**:
- **Verification**: Temporal modalities (Box, Diamond, U, R) for model checking
- **Distributed systems**: Spatial modalities (Box_S, Diamond_S)
- **Multi-agent systems**: Epistemic modalities (K_a, C)
- **Normative systems**: Deontic modalities (O, P)
- **Resource management**: Graded modalities (Box_n, Box_{<= n})
- **Probabilistic computation**: Probabilistic modalities (Box_p, D)
- **Linear logic**: Exponential modalities (!, ?)

**Examples of differentiation applications**:
- d(List_A) iso List_A tensor A -- zipper for a list
- d(Tree_A) iso Tree_A tensor Bool tensor Tree_A -- path in a tree
- d(Stream_A) iso Nat -- position in a stream
- d(!A) iso !A tensor A -- singling out one use from many
- d(Box A) iso Nat tensor A -- position in a temporal stream
- d^2 F -- editing with two cursors
