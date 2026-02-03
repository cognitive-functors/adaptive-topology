# Monoidal Category: Differential Linear Logic with Dependent Types

## 1. Basic Structure

### 1.1 The Category **Lin**

- **Objects**: Types A, B, C, ... (including dependent types)
- **Morphisms**: Hom(A, B) = { t | x:A |- t : B } -- linear terms
- **Composition**: Term substitution g . f = g[f/x]
- **Identity**: id_A = x:A |- x:A

## 2. Monoidal Structure

### 2.1 Symmetric Monoidal Category (tensor, 1)

**Tensor product**:
- Functor tensor : **Lin** x **Lin** -> **Lin**
- On objects: (A, B) |-> A tensor B
- On morphisms: (f : A -> C, g : B -> D) |-> f tensor g : A tensor B -> C tensor D

**Unit object**: I = 1

**Natural isomorphisms**:
- Associator: alpha_{A,B,C} : (A tensor B) tensor C iso A tensor (B tensor C)
- Left unitor: lambda_A : 1 tensor A iso A
- Right unitor: rho_A : A tensor 1 iso A
- Symmetry: sigma_{A,B} : A tensor B iso B tensor A

**Coherence diagrams**: The pentagon and the triangle commute.

### 2.2 Dual Monoidal Structure (par, bot)

The par product par gives a second monoidal structure with unit bot.

**Linear negation**: Contravariant functor (-)^perp : **Lin**^op -> **Lin**:
- (A tensor B)^perp = A^perp par B^perp
- (A par B)^perp = A^perp tensor B^perp
- 1^perp = bot, bot^perp = 1
- (A lollipop B)^perp = A tensor B^perp

## 3. Binoidal Structure (&, direct_sum)

The category **Lin** is binoidal with two additional products:

### 3.1 Categorical Product (&, top)

- A & B -- additive conjunction
- Projections: pi_1 : A & B -> A, pi_2 : A & B -> B
- Universal property: for f : C -> A and g : C -> B there exists a unique <f, g> : C -> A & B

### 3.2 Categorical Coproduct (direct_sum, 0)

- A direct_sum B -- additive disjunction
- Injections: inl : A -> A direct_sum B, inr : B -> A direct_sum B
- Universal property: for f : A -> C and g : B -> C there exists a unique [f, g] : A direct_sum B -> C

### 3.3 Distributivity

Tensor distributes over the coproduct:
```
A tensor (B direct_sum C) iso (A tensor B) direct_sum (A tensor C)
```

## 4. Dependent Types: Indexed Monoidal Structure

The category **Lin** possesses an indexed monoidal structure in which dependent types are represented through four separate constructions.

### 4.1 Multiplicative Dependent Types

#### 4.1.1 Dependent Sum Sigma_tensor

For each type A there exists a functor:
```
Sigma_tensor_A : Lin/A -> Lin
```
where Lin/A is the slice category over A (type families B with a map to A).

**Universal property**: For a family B : A -> Type there is an isomorphism:
```
Hom(C, Sigma_tensor(x:A).B(x)) iso Sigma_{f : Hom(C,A)} Hom(C, B(f))
```

**Relation to tensor**: Sigma_tensor extends the tensor product:
- If B does not depend on x, then Sigma_tensor(x:A).B iso A tensor B
- Projection: pi_1 : Sigma_tensor(x:A).B -> A

**Elimination**:
```
  C tensor Sigma_tensor(x:A).B(x)
  |
  v
  C tensor A tensor B (unpacking)
```

#### 4.1.2 Dependent Product Pi_par

For each type A there exists a functor:
```
Pi_par_A : Lin/A -> Lin
```

**Universal property**: For a family B : A -> Type:
```
Hom(Pi_par(x:A).B(x), C) iso Pi_{a : A} Hom(B(a), C)
```

**Relation to par**: Pi_par extends the par product:
- Application via par: (f : Pi_par(x:A).B) par (a : A) -> B(a)
- Contexts combine through par

**Introduction**:
```
  Gamma par A -> B
  ----------------
  Gamma -> Pi_par(x:A).B
```

### 4.2 Additive Dependent Types

#### 4.2.1 Indexed Product Pi_&

For an index set I, Pi_&(i:I).A(i) is the product of a type family.

**Categorical interpretation**: This is the limit of a cone:
```
      Pi_&(i:I).A(i)
      / | \
     /  |  \
    /   |   \
A(i_1) A(i_2) A(i_3) ...
```

**Projections**: For each i:I there exists:
```
pi_i : Pi_&(i:I).A(i) -> A(i)
```

**Universal property**: For any C with a family of morphisms {f_i : C -> A(i)}_{i:I} there exists a unique:
```
<f_i>_{i:I} : C -> Pi_&(i:I).A(i)
```

**Relation to &**:
- For I = {0, 1}: Pi_&(i:{0,1}).A(i) iso A(0) & A(1)
- The context Gamma is used uniformly for all indices

#### 4.2.2 Indexed Coproduct Sigma_direct_sum

For an index set I, Sigma_direct_sum(i:I).A(i) is the coproduct of a type family.

**Categorical interpretation**: This is the colimit of a cocone:
```
A(i_1) A(i_2) A(i_3) ...
    \   |   /
     \  |  /
      \ | /
  Sigma_direct_sum(i:I).A(i)
```

**Injections**: For each concrete index i_0:I and a value a : A(i_0):
```
in_{i_0} : A(i_0) -> Sigma_direct_sum(i:I).A(i)
```

**Universal property**: For any C with a family of morphisms {g_i : A(i) -> C}_{i:I} there exists a unique:
```
[g_i]_{i:I} : Sigma_direct_sum(i:I).A(i) -> C
```

**Relation to direct_sum**:
- For I = {0, 1}: Sigma_direct_sum(i:{0,1}).A(i) iso A(0) direct_sum A(1)
- Upon elimination, the context Delta is used linearly

### 4.3 Indexed Monoidal Category

Dependent types turn **Lin** into an **indexed monoidal category**:

**For multiplicative connectives**:
- A family of monoidal categories {Lin/A}_{A:Type}
- Base change (reindexing) functors between them
- Sigma_tensor and Pi_par are (co)limits in this structure

**For additive connectives**:
- Pi_& and Sigma_direct_sum are (co)limits over discrete index categories
- They preserve the binoidal structure (&, direct_sum)

### 4.4 Interaction Between Connectives

**Distributivity of Sigma_tensor over Sigma_direct_sum**:
```
Sigma_tensor(x:A).(Sigma_direct_sum(i:I).B(x,i)) iso Sigma_direct_sum(i:I).(Sigma_tensor(x:A).B(x,i))
```

**Distributivity of tensor over Sigma_direct_sum**:
```
C tensor Sigma_direct_sum(i:I).A(i) iso Sigma_direct_sum(i:I).(C tensor A(i))
```

**Commutation of Pi_& with Pi_&**:
```
Pi_&(i:I).(Pi_&(j:J).A(i,j)) iso Pi_&(j:J).(Pi_&(i:I).A(i,j))
```

## 5. (Co)inductive Types

### 5.1 Initial Algebras (mu)

The inductive type mu X.F(X) is the initial algebra for the functor F:
```
fold : F(mu X.F(X)) -> mu X.F(X)
```

**Universal property**: For any F-algebra alpha : F(C) -> C there exists a unique morphism (catamorphism):
```
cata(alpha) : mu X.F(X) -> C
```
such that the diagram commutes:
```
F(mu X.F(X)) --F(cata(alpha))--> F(C)
      |                            |
     fold                        alpha
      |                            |
      v                            v
  mu X.F(X) ----cata(alpha)-----> C
```

### 5.2 Terminal Coalgebras (nu)

The coinductive type nu X.F(X) is the terminal coalgebra:
```
unfold : nu X.F(X) -> F(nu X.F(X))
```

**Universal property**: For any F-coalgebra gamma : C -> F(C) there exists a unique morphism (anamorphism):
```
ana(gamma) : C -> nu X.F(X)
```

#### Positivity and Linear Negation

**Existence condition**: For the initial algebra (mu) and the terminal coalgebra (nu) to exist, the functor F : **Lin** -> **Lin** must be **strictly covariant**.

**In the context of MALL with linear negation (-)^perp**:

**Positive positions** (covariant) for variable X:
- X in A tensor X, X tensor A -- positive
- X in A par X, X par A -- positive
- X in A & X, X & A -- positive
- X in A direct_sum X, X direct_sum A -- positive
- X in A lollipop X -- positive (codomain of the function)

**Negative positions** (contravariant):
- X in X lollipop A -- negative (domain of the function)
- X^perp in any positive position -- negative (negation reverses variance)

**Current restriction of the system**:
```
mu X. F(X) and nu X. F(X)
```
where F may use only **positive occurrences** of X. Explicit use of X^perp inside the definition of F is **prohibited**.

**Categorical interpretation**: The functor F must be a covariant endofunctor on **Lin**:
```
F : Lin -> Lin (covariant)
```

If we admitted F(X, X^perp), it would be a functor:
```
F : Lin x Lin^op -> Lin (bivariant)
```
which requires more complex conditions for the existence of fixed points.

**Resolution**:
1. In the base system, only covariant functors are used
2. MALL connectives (tensor, par, &, direct_sum) are naturally covariant in both arguments
3. Linear implication A lollipop B is covariant in B but contravariant in A
4. Dependent connectives (Sigma_tensor, Pi_par, Pi_&, Sigma_direct_sum) also respect positivity

**Advantages of this restriction**:
- Guaranteed existence (of initial algebras / terminal coalgebras)
- Simplicity of checking the correctness of definitions
- Natural composition with other constructions

**Negation is available externally**:
```
(mu X.F(X))^perp and (nu X.F(X))^perp
```
are applied to completed types, not inside the recursive definition.

### 5.3 Sized Types

The category **Lin** includes **sized types**, providing precise control over (co)inductive types.

#### 5.3.1 Category of Sizes

**Sizes** form a partially ordered structure:
```
Size := {0, 1, 2, ..., infinity} where infinity := 100500^100500
```

with the ordering 0 <= 1 <= 2 <= ... <= infinity.

**Sized types**:
- mu^alpha X.F(X) -- inductive type of size alpha
- nu^alpha X.F(X) -- coinductive type of size alpha

#### 5.3.2 Functoriality by Size

For each functor F there exists a family of functors:
```
F^alpha : Lin -> Lin for each alpha : Size
```

with coherence morphisms:
```
alpha <= beta implies F^alpha => F^beta (natural transformation)
```

#### 5.3.3 Universal Properties with Sizes

**Initial algebra of size alpha**:
```
fold^alpha : F(mu^alpha X.F(X)) -> mu^alpha X.F(X)
```

with catamorphism:
```
cata^alpha : F-Alg -> Hom(mu^alpha X.F(X), C)
```

**Terminal coalgebra of size alpha**:
```
unfold^alpha : nu^alpha X.F(X) -> F(nu^alpha X.F(X))
```

#### 5.3.4 Ultrafinitism: Default Size

**Philosophy**: By default, all types have size infinity = 100500^100500. This implements a form of **ultrafinitism**:
- All types are theoretically finite
- infinity is sufficiently large for practical purposes
- Avoids paradoxes of actual infinity
- Permits finitary reasoning about "almost infinite" structures

**Categorical interpretation**: The category **Lin** factorizes through a family of subcategories:
```
Lin = union_{alpha:Size} Lin^alpha
```
where Lin^alpha contains types of size <= alpha.

#### 5.3.5 Subtyping

Functors:
```
forget_alpha^beta : Lin^alpha -> Lin^beta when alpha <= beta
```

yield subtyping:
```
mu^alpha X.F(X) <: mu^beta X.F(X) (covariant)
nu^beta X.F(X) <: nu^alpha X.F(X) (contravariant)
```

## 6. Differential Structure

### 6.1 Differential Category

**Lin** with operator d forms a differential category.

**Connection with sized types**: Ultrafinitism (infinity = 100500^100500 from Section 5.3) ensures the correctness of differentiation for **all** types of the category **Lin**:
- The derivative d(mu^alpha X.F(X)) is defined and computable for any alpha
- The derivative d(nu^alpha X.F(X)) is also defined thanks to the finiteness of alpha
- The default size infinity is sufficiently large practically but finite theoretically
- This permits universal differentiation of all (co)inductive types without restrictions

Finiteness is the key property for the correctness of the differential structure.

**Main properties**:

1. **Differentiation functor**: d : **Lin** -> **Lin**
   - On objects: A |-> dA
   - On morphisms: f : A -> B |-> df : A tensor dA -> dB

2. **Leibniz rule**:
   ```
   d(f tensor g) = (df tensor g) direct_sum (f tensor dg)
   ```

3. **Chain rule**:
   ```
   d(g . f) = (dg . f) tensor df
   ```

4. **Linearity of the derivative**: d^2 = 0 (the derivative of a linear map is constant)

### 6.2 Interaction of Differentiation with ! and d

Differentiation of the exponential object:
```
d(!A) iso !A tensor A
```

This expresses the classical fact: the derivative of e^x is e^x.

**Connection with coderivation**: A morphism f : !A -> B has derivative:
```
df : !A tensor A -> B
```

## 7. Monoidal Closure

### 8.1 Internal hom (lollipop)

The linear implication A lollipop B is the internal hom for tensor:
```
Hom(C tensor A, B) iso Hom(C, A lollipop B)
```

**Evaluation**: ev : (A lollipop B) tensor A -> B

**Currying**: Lambda : Hom(C tensor A, B) -> Hom(C, A lollipop B)

### 8.2 Closure for &

The implication for & (intuitionistic implication):
```
Hom(C & A, B) iso Hom(C, A => B)
```

where A => B = !A lollipop B.

## 8. Trace and Compact Closure

### 9.1 Compact Closure for Finite Types

For finite-dimensional types there exists a dual object:
```
A* = A lollipop 1
```

with natural isomorphisms:
```
eta_A : 1 -> A tensor A*
epsilon_A : A* tensor A -> 1
```

### 9.2 Trace Operator

For loops: Tr^A_B : Hom(A tensor X, B tensor X) -> Hom(A, B)

Connection with differentiation:
```
Tr(df) = d(Tr(f))
```

## 9. Enrichment and Double Categories

### 10.1 Self-enrichment

**Lin** is enriched over itself:
```
Hom(A, B) = A lollipop B
```

Composition:
```
. : (B lollipop C) tensor (A lollipop B) -> (A lollipop C)
```

### 10.2 Double Category

The differential structure induces a double category:
- **Horizontal morphisms**: Ordinary morphisms f : A -> B
- **Vertical morphisms**: Differentials dA -> dB
- **Cells**: Commuting squares of derivatives

## 10. Functorial Semantics

### 11.1 Interpretation in Vector Spaces

Functor [[- ]] : **Lin** -> **Vect**_k:
- [[A tensor B]] = [[A]] tensor_k [[B]]
- [[A direct_sum B]] = [[A]] direct_sum [[B]]
- [[dA]] = T[[A]] (tangent bundle)

### 11.2 Relational Semantics

Functor into **Rel** (the category of relations):
- Interprets linearity as "exactly one use"
- [[A tensor B]] = [[A]] x [[B]]
- [[A par B]] = [[A]] disjoint_union [[B]]

## 11. Modalities

**Important remark**: The basic structure of the category **Lin** (Sections 1--10) is defined via MALL connectives, dependent types, (co)inductive types, and differentiation. Modalities **are not part of the basic system**, but the structure of the category allows one to define them naturally through (co)inductive types.

### 11.1 Exponential Modalities: Comonad ! and Monad ?


The exponential modalities ! (of course) and ? (why not) allow one to manage non-linear resource usage in linear logic. They can be constructed as (co)inductive types in several ways.

### 11.1.1 Comonad ! (of course)

The comonad ! converts a linear type into a type that can be used an arbitrary number of times (including 0 and many).

#### 6.1.1 Main Construction: Coinductive Type with Additive Choice

**Definition**:
```
!A := nu X. 1 direct_sum (A & X)
```

**Categorical interpretation**: This is the terminal coalgebra for the functor F(X) = 1 direct_sum (A & X):
```
unfold : !A -> 1 direct_sum (A & !A)
```

Structure: a coinductive type with destructor:
- `unfold(x) = inl(*)` : termination (empty stream)
- `unfold(x) = inr(a, x')` where `(a, x') : A & !A` : offering an element with continuation

**Key semantics**: The additive conjunction `A & !A` means that the **consumer chooses**:
- pi_1 : take an element of type A (using dereliction)
- pi_2 : continue unfolding the stream !A (using the remainder)

This creates a "stream of possibilities" -- a coinductive structure where at each step a choice between an element and a continuation is available.

**Universal property** (anamorphism): For any coalgebra gamma : C -> 1 direct_sum (A & C) there exists a unique morphism:
```
ana(gamma) : C -> !A
```
such that:
```
    C ----------ana(gamma)--------> !A
    |                                |
  gamma                           unfold
    |                                |
    v                                v
1 direct_sum (A & C) --1 direct_sum (A & ana(gamma))--> 1 direct_sum (A & !A)
```

**Comonadic operations**:

**Counit** epsilon_A : !A -> A:
```
epsilon_A = ana([error, pi_1]) where error : 1 -> A is impossible
```
Extracts the first available element from the stream.

**Comultiplication** delta_A : !A -> !!A:
```
delta_A(x) = ana(lambda y. inr((y, delta_A(y))))
```
Creates a "stream of streams" -- each element is itself a stream !A.

**Weakening** w_A : !A -> 1:
```
w_A(x) = *
```
Ignores the stream.

**Connection with structures**: The coinductive definition via nu X. 1 direct_sum (A & X) naturally expresses a "lazy multiset" with nondeterministic consumer choice at each step.

#### 6.1.2 Alternative Constructions

**Indexed product**:
```
!A := Pi_&(n:Nat). (A^{tensor n})
```
A limit over the family of tensor powers. More abstract but equivalent representation.

**Via the free commutative monoid**:
```
!A := nu X. top & (A tensor X)
```
or as a limit with factorization:
```
!A := lim_{n:Nat} (A^{tensor n} / S_n)
```
where S_n is the symmetric group. Factorization by permutations yields commutativity.

**Operadic approach**:
```
!A := Sigma_direct_sum(n:Nat). (A^{tensor n} / S_n)
```
Uses the operad of commutative monoids.

### 11.1.2 Monad ? (why not)

The monad ? is dual to the comonad ! and describes finite multisets -- the ability to provide an arbitrary (but finite) number of values.

#### 6.2.1 Main Construction: Inductive Multiset Type

**Definition**:
```
?A := mu X. top direct_sum (A tensor X)
```

**Categorical interpretation**: This is the initial algebra for the functor F(X) = top direct_sum (A tensor X):
```
fold : top direct_sum (A tensor ?A) -> ?A
```

Structure: an inductive type with constructors:
- `empty : ?A` via fold(inl(*))
- `cons : A tensor ?A -> ?A` via fold(inr(-))

Elements of ?A are finite unordered multisets of elements of A.

**Universal property** (catamorphism): For any algebra alpha : top direct_sum (A tensor C) -> C there exists a unique morphism:
```
cata(alpha) : ?A -> C
```
such that:
```
top direct_sum (A tensor ?A) --top direct_sum (A tensor cata(alpha))--> top direct_sum (A tensor C)
         |                                                                       |
        fold                                                                   alpha
         |                                                                       |
         v                                                                       v
        ?A ----------cata(alpha)--------> C
```

**Monadic operations**:

**Unit** eta_A : A -> ?A (singleton multiset):
```
eta_A(a) = fold(inr(a, fold(inl(*))))
```

**Multiplication** mu_A : ??A -> ?A (multiset concatenation):
```
mu_A = cata([empty, lambda(xs, xss). append(xs, mu_A(xss))])
```
where `append : ?A tensor ?A -> ?A` concatenates multisets.

**Comparison with !**:
- **!A = Pi_&(n:Nat). A^{tensor n}**: coinductive, all arities simultaneously
- **?A = mu X. top direct_sum (A tensor X)**: inductive, finite multiset

#### 6.2.2 Alternative Constructions

**Via indexed sum with factorization**:
```
?A := Sigma_direct_sum(n:Nat). (A^{tensor n} / S_n)
```
where S_n is the symmetric group. Explicitly expresses finiteness and factorization by permutations (commutativity).

**Via duality**:
```
?A := (!(A^perp))^perp
```
Definition through linear negation, ensuring correct categorical duality.

### 11.1.3 Duality of ! and ? -- Problem and Resolution

#### 6.3.1 Checking the Duality of the Main Definitions

Let us verify whether our main definitions are dual:

**For !A = Pi_&(n:Nat). (A^{tensor n})**:
```
(!A)^perp = (Pi_&(n:Nat). A^{tensor n})^perp
          iso Sigma_direct_sum(n:Nat). (A^{tensor n})^perp   [Pi_&/Sigma_direct_sum duality]
          iso Sigma_direct_sum(n:Nat). ((A^perp)^{par n})    [de Morgan: (A tensor B)^perp = A^perp par B^perp]
```

where (A^perp)^{par n} = A^perp par A^perp par ... par A^perp.

**For ?A = mu X. top direct_sum (A tensor X)**:
```
(?A)^perp = (mu X. top direct_sum (A tensor X))^perp
          iso nu X. (top direct_sum (A tensor X))^perp       [mu/nu duality]
          iso nu X. (bot & (A^perp par X))                    [de Morgan]
          iso nu X. (A^perp par X)                            [bot & B iso B]
```

**Problem**: nu X. (A^perp par X) does not coincide with Pi_&(n:Nat). (A^perp)^{tensor n} !

Our definitions are **not fully dual** in the categorical sense.

#### 6.3.2 Resolution: Consistent Dual Definitions

There are several approaches to resolving this problem:

**Approach 1: Use a coinductive definition for !**

If we take:
```
!A := nu X. 1 direct_sum (A & X)
?A := mu X. top direct_sum (A tensor X)
```

Then:
```
(?A)^perp = (mu X. top direct_sum (A tensor X))^perp
          iso nu X. (bot & (A^perp par X))
          iso nu X. (A^perp par X)
```

This is closer to nu X. 1 direct_sum (A^perp & X), but requires an isomorphism between par and &, which does not always exist.

**Approach 2: Acknowledge partial duality**

The comonad ! and the monad ? are **functionally dual** (via the adjunction ! -| ?), but their concrete representations through (co)inductive types **are not direct categorical duals** via (-)^perp.

**Correct formulation**:
```
Hom(!A, B) iso Hom(A, ?B) (adjunction)
(?A)^perp iso !(A^perp) (not an exact isomorphism for our definitions)
```

**Approach 3: Use a single family of definitions**

For full duality via (-)^perp, one may define:
```
!A := Pi_&(n:Nat). (A^{tensor n})
?A := Sigma_direct_sum(n:Nat). (A^{par n})   [using par instead of tensor!]
```

Then:
```
(!A)^perp = (Pi_&(n:Nat). A^{tensor n})^perp
          iso Sigma_direct_sum(n:Nat). (A^perp)^{par n}
          = ?(A^perp)
```

#### 6.3.3 Fundamental Problem of Categorical Duality

**Problem with par**: The attempt to "fix" duality via:
```
?A := Sigma_direct_sum(n:Nat). (A^{par n})
```
**does not work**, because from A par A one cannot extract two independent copies of A! Par describes parallel composition of contexts, not an independent collection of elements.

**Deep reason**: In MALL, the semantics of connectives is:
- **tensor**: A tensor B gives independent access to A and B
- **par**: A par B requires a choice of one context (parallel composition, not independence)
- **&**: A & B allows a nondeterministic choice of one projection
- **direct_sum**: A direct_sum B requires a deterministic choice of one variant

These semantic differences render exact categorical duality via (-)^perp **impossible** while preserving correct operational semantics.

#### 6.3.4 Alternative Approaches

**Structural duality** (via (co)inductivity):
```
!A := nu X. 1 direct_sum (A & X) [coinductive]
?A := mu X. top direct_sum (A tensor X) [inductive]
```

Duality transformations: mu <-> nu, tensor <-> &, 1 <-> top, but direct_sum <-> direct_sum (unchanged).

This yields structural symmetry but not exact categorical duality via (-)^perp.

#### 6.3.5 Conclusion for Our System

In the category **Lin** with MALL and dependent types we have:

1. **Adjunction ! -| ?** -- the main property, ensuring functional duality
2. **Structural symmetry** between inductivity/coinductivity
3. **Exact categorical duality** via (-)^perp cannot be realized

**Theoretical remark**: This is a known problem in linear logic theory. Exponential modalities ! and ? in a *-autonomous category with MALL require additional structure (e.g., the modalities must form a *-autonomous subcategory), which goes beyond a simple application of (-)^perp.

**Practical position**: The adjunction ! -| ? is fully sufficient for:
- Correct operational semantics
- All computational applications
- Proofs of type system properties

Categorical duality via (-)^perp is an additional theoretical property that is not realized in this system.

#### 6.3.2 Adjunction ! -| ?

**Hom-set isomorphism**:
```
Hom(!A, B) iso Hom(A, ?B)
```

**Explicit construction (based on the actual semantics)**:

For f : !A -> B, we define curry(f) : A -> ?B:
```
curry(f)(a) = eta_?B(f(eta_!A(a)))
```
where eta_!A(a) creates a "minimal" element of !A containing a single a, and eta_?B wraps the result into a singleton multiset.

For g : A -> ?B, we define uncurry(g) : !A -> B:
```
uncurry(g)(x) = ... (consumes x piecewise, applying g and combining results)
```

**Intuitive interpretation**:
- A morphism f : !A -> B can use any number of copies of A to produce a single B
- A morphism g : A -> ?B produces a multiset (nondeterministic choice) of results B
- These two capabilities are dual: "consume many" <-> "produce many"

**Unit and counit of the adjunction**:

Unit eta : Id -> ? . ! :
```
eta_A : A -> ?(!A)
eta_A(a) = unit(!a) where !a is the "minimal" element of !A
```

Counit epsilon : ! . ? -> Id :
```
epsilon_A : !(?A) -> A
epsilon_A(x) = ... (extracts a single A from the multiset structure)
```

### 11.1.4 Categorical Properties

#### 6.4.1 Comonad !

**Functor**: ! : **Lin** -> **Lin**

**Comultiplication** delta : ! -> ! . ! (natural transformation):
```
delta_A : !A -> !!A
```

**Counit** epsilon : ! -> Id:
```
epsilon_A : !A -> A
```

**Comonad axioms**:
```
(! . delta) . delta = (delta . !) . delta (coassociativity)
(! . epsilon) . delta = id (left counitality)
(epsilon . !) . delta = id (right counitality)
```

**Diagrams**:
```
      delta         !delta
!A ------> !!A ------> !!!A
  \                     |
   \                    | delta . !
    \delta              |
     \                  v
      \--> !!A


      delta        !epsilon
!A ------> !!A ------> !A
  \         |         /
   \        |        /
    \id   epsilon.!  /id
     \      |      /
      \     v     /
       \--- A ---/
```

#### 6.4.2 Monad ?

**Functor**: ? : **Lin** -> **Lin**

**Multiplication** mu : ? . ? -> ? (natural transformation):
```
mu_A : ??A -> ?A
```

**Unit** eta : Id -> ?:
```
eta_A : A -> ?A
```

**Monad axioms**:
```
mu . (mu . ?) = mu . (? . mu) (associativity)
mu . (eta . ?) = id (left unitality)
mu . (? . eta) = id (right unitality)
```

#### 6.4.3 Algebras and Coalgebras

**Eilenberg-Moore coalgebras for !**:

A coalgebra is a pair (C, gamma : C -> !C) such that:
```
      gamma         !gamma
C ---------> !C ---------> !!C
  \           |             ^
   \          |            /
    \gamma  delta.gamma   /
     \        |          /
      \       v         /
       \---> !C -------/
```

The category **Cart** = **CoAlg(!)** is the category of Cartesian types (with duplication and discarding).

**Eilenberg-Moore algebras for ?**:

An algebra is a pair (C, alpha : ?C -> C) such that the monad diagrams commute.

### 11.1.5 Connection with (Co)inductive Types

#### 6.5.1 ! as Universal Coinduction

For any coinductive type nu X.F(X), where F is built from MALL connectives:
```
!(nu X.F(X)) iso nu Y. Pi_&(n:Nat). F^n(Y)
```

The comonad ! "stabilizes" coinduction, allowing one to observe an arbitrary number of unfoldings.

#### 6.5.2 ? as Universal Induction

For any inductive type mu X.F(X):
```
?(mu X.F(X)) iso mu Y. Sigma_direct_sum(n:Nat). F^n(Y)
```

The monad ? "stabilizes" induction, allowing one to choose the depth of construction.

### 11.1.6 Computational Interpretation

#### 6.6.1 ! and Resource Duplication

In computation, !A means:
- A value of type A is available in memory
- It can be read an arbitrary number of times
- It can be ignored (garbage collected)

**Example**: In programming languages this corresponds to:
- Immutable values
- Values with reference counting or GC
- Copy-on-write structures

#### 6.6.2 ? and Nondeterminism

In computation, ?A means:
- A nondeterministic choice of a value of type A
- The possibility of deferred computation (lazy evaluation)
- Multiple branches of computation

### 11.1.7 Functorial Properties

#### 11.1.7.1 ! as a Monoidal Functor

**! preserves monoidal structure**:
```
!(A tensor B) iso !A tensor !B
!1 iso 1
```

**! does not preserve additive structure**:
```
!(A direct_sum B) != !A direct_sum !B (in general)
!(A & B) iso !A & !B
```

#### 11.1.7.2 ? as a Functor over Additive Structure

**? interacts with direct_sum**:
```
?(A direct_sum B) -> ?A direct_sum ?B
```
(but not an isomorphism in general -- a multiset may contain elements from both components)

**? does not preserve &**:
```
?(A & B) != ?A & ?B (in general)
```

**? as a multiset functor**:
```
map_? : (A -> B) -> (?A -> ?B)
map_?(f)(xs) = rec_mu(xs, lambda t. match t with
  | inl(*) -> empty
  | inr(a, xs') -> cons(f(a), map_?(f)(xs')))
```

This makes ? an endofunctor on **Lin**, but with more complex functorial properties than !.


### 11.2 Other Modalities: Extensions of the Basic System

In addition to the exponential modalities ! and ?, the structure of the category **Lin** allows one to define many other modalities for various applications. All these modalities **are not part of the basic system** but can be added as extensions, using (co)inductive types and the MALL structure.

#### 11.2.1 Temporal Modalities

**"Always in the future" modality (Box)**:
```
Box A := nu X. A & X
```
A coinductive stream where A is true at each time step in the future.

**"Eventually in the future" modality (Diamond)**:
```
Diamond A := mu X. A direct_sum X
```
An inductive type: either A is true now, or it will be true later.

**Categorical interpretation**: They form a comonad (Box) and a monad (Diamond) on the category **Lin**.

**Adjunction**: Box -| Diamond in the presence of an appropriate temporal structure.

**With dependent types -- richer**:
- **Indexed by time**: Box_t A := Pi_&(t':Time, t' >= t).A(t') -- dependence on the moment in time
- **With duration**: Box^d A := Pi_&(t:Time, t in [now, now+d]).A(t) -- true within interval d
- **With metrics**: Box_mu A := Pi_&(t:Time).A(t) tensor Metric(t) -- with temporal metrics
- **Dependent until**: Sigma_tensor(t:Time).A(t) U_t B(t) -- until with time dependence

#### 11.2.2 Spatial Modalities

**"Everywhere in space" (Box_S)**:
```
Box_S A := Pi_&(l:Location).A(l)
```
A family indexed by spatial locations.

**"Somewhere in space" (Diamond_S)**:
```
Diamond_S A := Sigma_direct_sum(l:Location).A(l)
```
Existential choice of location.

**"Here" (at_l)**:
```
at_l : A -> Box_S A
at_l(a) = lambda loc. if loc = l then a else error
```

**With dependent types -- richer**:
- **With distance metric**: Box_r A := Pi_&(l:Location, d(l,here) <= r).A(l) -- within radius r
- **With topology**: Box_U A := Pi_&(l:U).A(l) for an open set U
- **Regional**: Sigma_tensor(r:Region).Pi_&(l:r).A(l) -- by regions with dependence
- **With resources**: Sigma_tensor(l:Location).(A(l) tensor Resources(l)) -- with local resources

#### 11.2.3 Deontic Modalities (Modalities of Obligation)

**"Obligatory" (O)**:
```
O A := A & Obligation
```
where Obligation is a special type representing an obligation.

**"Permitted" (P)**:
```
P A := A direct_sum Permission
```
where Permission is a permission type.

**Categorical interpretation**: O and P can be constructed as:
```
O A := nu X. A & (X direct_sum Violation)
P A := mu X. A direct_sum (X & Grant)
```

The coinductive "obligation" is a stream of compliance checks; the inductive "permission" is a finite chain of grants.

**With dependent types -- richer**:
- **With context**: O_c A := Sigma_tensor(c:Context).(A(c) & Obligation(c)) -- obligation depends on context
- **With priorities**: Pi_&(p:Priority).O_p A -- obligations of different levels
- **With agents**: Sigma_direct_sum(a:Agent).O_a A -- who is obligated to fulfill
- **Conditional**: Pi_par(cond:Condition).O A -- obligation under a condition

#### 11.2.4 Alethic Modalities (Modalities of Necessity/Possibility)

**"Necessarily" (Box_N)**:
```
Box_N A := Pi_&(w:World).A(w)
```
True in all possible worlds.

**"Possibly" (Diamond_N)**:
```
Diamond_N A := Sigma_direct_sum(w:World).A(w)
```
True in some possible world.

**Categorical interpretation**: These are precisely Pi_& and Sigma_direct_sum over the type of possible worlds, making them natural modalities in a system with dependent types.

**Connection with S4/S5**:
- For reflexivity: the current world is accessible
- For transitivity: the accessibility relation composes
- For symmetry (S5): the accessibility relation is symmetric

**With dependent types -- richer**:
- **With accessibility relation**: Pi_&(w:World, R(w_0,w)).A(w) -- through relation R
- **Modal depth**: Sigma_tensor(n:Nat).Box^n A -- with nesting depth
- **Contingency**: Sigma_direct_sum(w:World).A(w) & Pi_&(w':World).not A(w') -- true somewhere, but not everywhere
- **With probability**: Pi_&(w:World).A(w) tensor Prob(w) -- weighted necessity

#### 11.2.5 Epistemic Modalities (Modalities of Knowledge)

**"Agent knows" (K_a)**:
```
K_a A := Pi_&(s:State_a).A(s)
```
where State_a is the set of states that agent a considers possible.

**"Agent considers possible" (M_a)**:
```
M_a A := Sigma_direct_sum(s:State_a).A(s)
```

**"Common knowledge" (C)**:
```
C A := nu X. A & (Pi_&(a:Agent).K_a X)
```
A coinductive definition: A is true and all agents know this, and all know that all know, and so on.

**With dependent types -- richer**:
- **Knowledge about knowledge**: K_a(Sigma_tensor(b:Agent).K_b A) -- a knows that someone knows A
- **Distributed knowledge**: Sigma_tensor(G:Group).D_G A := Pi_&(s:union_{a in G} State_a).A(s) -- union of group knowledge
- **Temporal knowledge**: K_a^t := Pi_&(s:State_a(t)).A(s) -- knowledge at time t
- **Conditional knowledge**: Pi_par(e:Evidence).K_a A -- knowledge given evidence
- **With confidence**: Sigma_tensor(c:Confidence).K_a A tensor c -- knowledge with confidence level

#### 11.2.6 Probabilistic Modalities

**"With probability p" (Box_p)**:
```
Box_p A := A tensor Prob(p)
```
where Prob(p) is a type of probability distributions.

Alternatively, via a stochastic matrix:
```
Box_p A := Pi_&(s:Outcome).A(s) tensor R_[0,1]
```
with the constraint sum_s p_s = 1.

**Probabilistic choice monad (D)**:
```
D A := Sigma_direct_sum(n:Nat).(A^{tensor n} tensor Distribution(n))
```
A finite mixture of outcomes with a distribution.

**With dependent types -- richer**:
- **Conditional probability**: Sigma_tensor(e:Evidence).(A tensor Prob(A|e)) -- probability given e
- **Bayesian updating**: Pi_par(obs:Observation).Box_p A -> Box_{p'} A -- updating with observations
- **Markov processes**: nu X. Sigma_tensor(s:State).(A(s) tensor Prob(s) tensor X) -- with state dependence
- **Parameterized distributions**: Sigma_tensor(theta:Parameters).D_theta A -- family of distributions

#### 11.2.7 Linear Temporal Logic (LTL)

**"Until" (U)**:
```
A U B := mu X. B direct_sum (A tensor X)
```
A is true until B becomes true.

**"Release" (R)**:
```
A R B := nu X. B & (A par X)
```
B is true until it is "released" through A.

**With dependent types -- richer**:
- **Bounded Until**: Sigma_tensor(n:Nat).(A U_{<= n} B) -- with a time bound
- **With predicates**: Pi_par(P:Predicate).A U_P B -- until with condition P at each step
- **Metric until**: Sigma_tensor(t:Time).A U_{[0,t]} B -- with a metric time bound
- **Dependent eventually**: Sigma_direct_sum(t:Time).Diamond_t A(t) -- "eventually" with time dependence

#### 11.2.8 Affine and Relevant Modalities

**Affine modality (Circle)**:
```
Circle A := A direct_sum 1
```
A may be used once or not at all.

**Relevant modality (Bullseye)**:
```
Bullseye A := mu X. A direct_sum (A tensor X)
```
A may be used one or more times (but not zero).

**With dependent types -- richer**:
- **Conditional affinity**: Pi_par(cond:Condition).(A direct_sum 1(cond)) -- may discard under a condition
- **Relevance with accounting**: Sigma_tensor(n:Nat_{>0}).A^{tensor n} -- exactly n > 0 uses
- **Weighted relevance**: Sigma_tensor(uses:List(Weight)).tensor_{w in uses} A -- with usage weights
- **Contextual affinity**: Sigma_tensor(c:Context).(A(c) direct_sum 1) -- depends on context

#### 11.2.9 Graded Modalities

**"Exactly n uses" (Box_n)**:
```
Box_n A := A^{tensor n}
```

**"At most n uses" (Box_{<= n})**:
```
Box_{<= n} A := Sigma_direct_sum(k:Nat_{<= n}).A^{tensor k}
```

**"At least n uses" (Box_{>= n})**:
```
Box_{>= n} A := A^{tensor n} tensor !A
```

**With dependent types -- richer**:
- **Dependent grading**: Sigma_tensor(n:Nat).Box_n(A(n)) -- grading depends on type
- **Vector grading**: Sigma_tensor(v:Vector(Resource)).A^{tensor v} -- multidimensional resources
- **With constraints**: Pi_&(n:Nat, P(n)).Box_n A -- grading with a predicate
- **Parameterized**: Pi_par(params:Params).Box_{f(params)} A -- grading via a function of parameters
- **Interval**: Sigma_tensor(n:Nat, m:Nat, n <= m).Box_{[n,m]} A := Sigma_direct_sum(k:Nat, n <= k <= m).A^{tensor k} -- usage range

#### 11.2.10 General Modality Construction

**Theorem**: Any modality that can be expressed through:
- (Co)inductive types (mu, nu)
- MALL connectives (tensor, par, &, direct_sum, 1, bot, top, 0)
- Dependent types (Sigma_tensor, Pi_par, Pi_&, Sigma_direct_sum)

is naturally defined in the category **Lin**.

**Universal property**: To define a new modality M, it suffices to specify:
1. A functor M : **Lin** -> **Lin**
2. Either a monadic structure (eta : Id -> M, mu : M . M -> M)
3. Or a comonadic structure (epsilon : M -> Id, delta : M -> M . M)
4. Or a general endofunctorial structure

**Role of dependent types**: As shown above, dependent types (Sigma_tensor, Pi_par, Pi_&, Sigma_direct_sum) significantly enrich the expressiveness of modalities:
- **Indexing**: Pi_& and Sigma_direct_sum allow modalities to be indexed (by time, space, worlds, agents)
- **Parameterization**: Sigma_tensor allows modalities to depend on parameters
- **Conditionality**: Pi_par allows one to introduce conditional modalities
- **Compositeness**: Combinations of dependent connectives yield complex modal constructions

Thus, a system with four dependent connectives naturally supports a rich family of modalities without the need to embed them in the basic system.

### 11.3 Composition and Interaction of Modalities

**Composition of modalities**:
```
(! Box) A = !(Box A) -- unrestricted use of a temporal stream
(Box !) A = Box(!A) -- temporal stream of unrestricted values
```

**Distributive laws**: For correct composition of modalities M and N, a distributive law is required:
```
lambda : M . N -> N . M
```

**Examples of interaction**:
- ! Box : "one can request any number of future values"
- Box ! : "at each time step, the value can be used arbitrarily"
- Box_p . ? : "probability distribution over nondeterministic choices"

### 11.4 Summary of Modalities

Structure of the category **Lin**:
1. **Basic system** (Sections 1--10) -- MALL, dependent types, (co)induction, differentiation
2. **Modalities** (Section 11) -- extensions defined through the basic structure

**Advantages of this approach**:
- Modalities are not "built in" but "derived" from the basic structure
- Uniform technique for defining diverse modalities
- Composition of modalities through functorial structure
- Ability to add arbitrary domain-specific modalities

**Application examples**:
- Temporal logic of programs
- Spatial reasoning in distributed systems
- Knowledge logic for multi-agent systems
- Probabilistic programming
- Quantum computation (linearity + modalities)

## 12. Summary: Key Structures

### Basic System (Sections 1--10)

The monoidal category **Lin** possesses the following fundamental structure:

### Monoidal Structures:
1. **Symmetric monoidal structure** (tensor, 1) -- multiplicative
2. **Dual monoidal structure** (par, bot) with *-autonomy
3. **Binoidal structure** (&, direct_sum) -- additive
4. **Monoidal closure** (lollipop) -- linear implication

### Dependent Types:
5. **Indexed monoidal structure** for four dependent connectives:
   - Sigma_tensor -- multiplicative dependent sum (functor from the slice)
   - Pi_par -- multiplicative dependent product (dual functor)
   - Pi_& -- indexed product (limit)
   - Sigma_direct_sum -- indexed coproduct (colimit)

### (Co)inductive Types:
6. **Initial algebras** (mu) -- inductive types with catamorphisms
7. **Terminal coalgebras** (nu) -- coinductive types with anamorphisms
8. **Sized types** (mu^alpha, nu^alpha) -- with explicit size control and ultrafinitism (infinity = 100500^100500)

### Differential Structure:
9. **Differential structure** (d) with:
   - Leibniz rule for tensor
   - Chain rule for composition
   - Universality for all types thanks to finiteness (sized types)
10. **Trace structure** for compact objects with Tr(df) = d(Tr(f))

### Enrichment:
11. **Self-enrichment** -- Hom(A,B) = A lollipop B
12. **Double category structure** -- horizontal morphisms (ordinary), vertical (differentials)

### Semantics:
13. **Functorial semantics** in **Vect** ([[dA]] = T[[A]]) and **Rel**

---

### Extensions: Modalities (Section 11)

**Key remark**: Modalities **are not part of the basic system**. They are defined as extensions using (co)inductive types and MALL connectives.

**Exponential modalities**:
- **! (of course)**: nu X. 1 direct_sum (A & X) -- comonad for reuse
- **? (why not)**: mu X. top direct_sum (A tensor X) -- monad for multisets
- The adjunction ! -| ? ensures functional duality

**Other modalities** (examples):
- Temporal: Box (always), Diamond (eventually), U (until), R (release)
- Spatial: Box_S (everywhere), Diamond_S (somewhere)
- Deontic: O (obligatory), P (permitted)
- Alethic: Box_N (necessarily), Diamond_N (possibly)
- Epistemic: K_a (knowledge), C (common knowledge)
- Probabilistic: Box_p, D (distribution)
- Graded: Box_n, Box_{<= n}, Box_{>= n}

**Universality**: Any modality expressible through (co)inductive types and MALL connectives is naturally defined in **Lin**.

---

### Overall Architecture

This structure provides a complete categorical semantics for a type system with:
- **Linearity** (resource management through MALL)
- **Dependent types** (four connectives for different kinds of dependencies)
- **(Co)recursion** (initial algebras and terminal coalgebras)
- **Differentiation** (zipper structures and incremental computation)
- **Extensibility through modalities** (user-definable operators)
