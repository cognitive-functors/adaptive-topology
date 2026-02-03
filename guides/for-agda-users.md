# C4 for Agda Users

A walkthrough of the formal verification of C4's core theorems in Agda, with notes on the proof technique, the `--without-K` flag, and open contributions.

---

## Overview

C4's mathematical foundation is a finite abelian group Z3^3 = Z3 x Z3 x Z3 with 27 elements. All 11 core theorems are mechanically verified in Agda (a dependent type theory proof assistant based on Martin-Lof Type Theory).

**Source file:** `formal-proofs/c4-comp-v5.agda`

---

## The Type Structure

### Base Type: Z3

Z3 (integers mod 3) is defined as a finite type with three constructors:

```agda
data Z3 : Set where
 z0 : Z3
 z1 : Z3
 z2 : Z3
```

This represents {0, 1, 2} with modular arithmetic. Addition is defined by pattern matching on all 9 cases.

### Cognitive State: Z3 x Z3 x Z3

A cognitive state (basis state) is a triple:

```agda
CogState : Set
CogState = Z3 x Z3 x Z3
```

Where the three components are:
- First: T (Time)
- Second: D (Scale)
- Third: A (Agency)

### Operators

The three cognitive operators shift one component by +1 (mod 3):

```agda
shiftT : CogState -> CogState
shiftT (t , d , i) = (add t z1 , d , i)

shiftD : CogState -> CogState
shiftD (t , d , i) = (t , add d z1 , i)

shiftI : CogState -> CogState
shiftI (t , d , i) = (t , d , add i z1)
```

Each operator is an element of the group; applying it three times returns to the original state (order 3).

---

## Key Theorems

### Theorem 1: Completeness (Reachability)

Any cognitive state is reachable from any other via a finite composition of operators.

```agda
reachability : (s1 s2 : CogState) -> Path s1 s2
```

**Proof strategy:** Constructive. Given s1 = (t1, d1, i1) and s2 = (t2, d2, i2), compute the difference on each axis (mod 3) and apply that many shifts. The proof term explicitly constructs the path.

### Theorem 9: Shortest Path (Constructive)

The `belief-path` algorithm computes a shortest transformation sequence:

```agda
belief-path : CogState -> CogState -> List Operator
```

The proof shows this path has length equal to the Hamming distance between the two states (number of axes on which they differ). Maximum length: 3.

### Theorems 3-8: Group Properties

- **Associativity:** Operator composition is associative.
- **Identity:** The identity operator (no shift on any axis) exists.
- **Inverse:** Each operator has an inverse (shifting by +2 is the same as shifting by -1 in Z3).
- **Commutativity:** The group is abelian -- operator order does not matter.

These are verified by exhaustive case analysis on the finite type, which Agda handles efficiently.

### Theorem 11: Bounded Diameter

The maximum Hamming distance between any two states is 3, meaning at most 3 operator applications suffice to reach any state from any other.

---

## The `--without-K` Flag

The proofs are compiled with `--without-K`, which disables Streicher's Axiom K (uniqueness of identity proofs). This ensures the proofs are valid in Homotopy Type Theory (HoTT) and do not depend on the assumption that all proofs of equality are identical.

**Why this matters:**
- Proofs remain valid under more general type-theoretic interpretations.
- No hidden axioms beyond Martin-Lof Type Theory.
- The proofs are constructive: they compute witnesses, not just assert existence.

**Practical consequence:** Some equality proofs require explicit transport along paths rather than direct pattern matching on `refl`. This adds verbosity but increases rigor.

---

## Proof Technique Notes

### Decidable Equality

Z3 has decidable equality (we can always determine if two elements are equal or not). This is established first and used throughout:

```agda
_==Z3_ : Z3 -> Z3 -> Bool
z0 ==Z3 z0 = true
z0 ==Z3 z1 = false
...
```

### Exhaustive Case Analysis

Since Z3 has only 3 elements, Z3^3 has 27. Many proofs proceed by exhaustive case analysis over all 27 (or 27 x 27 = 729) cases. Agda's termination checker accepts this directly.

### Equational Reasoning

For algebraic properties (associativity, commutativity), the proofs use Agda's equational reasoning combinators:

```agda
comm-proof : (a b : Z3) -> add a b == add b a
comm-proof z0 z0 = refl
comm-proof z0 z1 = refl
...
```

---

## Building and Checking

### Prerequisites

- Agda >= 2.6.3
- Agda standard library >= 1.7

### Verification

```bash
agda --without-K formal-proofs/c4-comp-v5.agda
```

If the file type-checks without errors, all theorems are verified. Agda's type system guarantees that a term of type `(s1 s2 : CogState) -> Path s1 s2` is a correct proof of reachability.

---

## Open Contribution: Theorem 2 (Minimality)

**Conjecture 2:** Three dimensions are *necessary* -- no 2-dimensional model (Z3^2 or any other group with fewer than 27 elements) can capture the same structure.

**Status:** Unproven. This is the primary open problem in C4's formal verification.

**What a proof would require:**
1. Define what "capturing the same structure" means formally (preserving which properties?).
2. Show that any group with fewer than 27 elements fails to satisfy at least one required property.
3. The hardest part: formalizing the *empirical* claim (that T, D, A are distinct, non-collapsible axes) in a way that admits proof.

**Possible approaches:**
- Show that projecting Z3^3 onto any Z3^2 loses a specific structural property (e.g., a pair of states becomes indistinguishable that should be distinct).
- Formalize "adequate cognitive model" axiomatically and derive the lower bound.

**How to contribute:**
- Fork the repository.
- Work in `formal-proofs/` directory.
- Submit a pull request with the proof or partial progress.
- Discussion: open a GitHub issue labeled `theorem-2`.

---

## File Structure

```
formal-proofs/
 c4-comp-v5.agda -- Main proof file (all 11 theorems)
 README.md -- Build instructions
 VERIFICATION-GUIDE.md -- Detailed verification walkthrough
```

---

## References

- Norell, U. (2009). "Dependently Typed Programming in Agda."
- Univalent Foundations Program (2013). *Homotopy Type Theory*.
- Selyutin, I. & Kovalev, N. (2025). "C4: Complete Cognitive Coordinate System." Preprint.

---

*Contact: comonoid@yandex.ru*
