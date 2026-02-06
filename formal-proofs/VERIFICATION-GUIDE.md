# C4 Formal Verification Guide

A guide to what the Agda proofs verify, how to reproduce verification, and the scope boundaries of formal claims.

---

## Scope of Verification

### What IS formally verified (algebraic structure)

The file `c4-comp-v5.agda` contains 11 theorems about the algebraic structure of Z3^3 as a finite abelian group. Of these, 10 are fully machine-verified; Theorem 2 (minimality) uses a postulate that is mathematically justified but not yet machine-verified. Specifically:

**Verified properties:**
- Closure, associativity, identity, and inverse for group operations on Z3^3
- Commutativity (the group is abelian)
- Completeness/Reachability (Theorem 1): any state is reachable from any other via operator composition
- Shortest path construction (Theorem 9): the `belief-path` algorithm computes optimal transformation sequences
- Bounded diameter (Theorem 11): at most 6 operator applications connect any two states (at most 2 per axis)

**Verification method:**
- Agda proof assistant (Martin-Lof Type Theory)
- Compiled with `--without-K` flag (compatible with Homotopy Type Theory)
- Proofs are constructive -- they compute witnesses, not just assert existence

### What is NOT verified (cognitive interpretation)

The Agda proofs establish properties of a **mathematical structure** (a specific finite group). The following claims are **outside the scope** of formal verification and remain empirical hypotheses or conjectures:

- That human cognition is faithfully modeled by Z3^3
- That the three axes (T, D, A) are the correct or only decomposition of cognitive space
- That the 27 basis states have the cognitive interpretations assigned to them (e.g., that (0,0,0) = "Past, Concrete, Self")
- Minimality (Conjecture 2): that d=3 dimensions are necessary (not just sufficient)
- That Hamming distance in Z3^3 correlates with subjective difficulty of cognitive transitions
- Any neural or biological claim

**In summary:** The proofs guarantee that Z3^3 *has certain algebraic properties*. Whether those properties *map onto cognition* is an empirical question requiring separate validation.

---

## How to Verify

### Prerequisites

- Agda >= 2.6.3
- Agda standard library >= 1.7

### Running verification

```bash
# Clone the repository and run:
agda --without-K formal-proofs/c4-comp-v5.agda
```

If the file type-checks without errors, 10 of 11 theorems are fully verified. Theorem 2 (minimality) type-checks but relies on a postulate. No runtime execution is needed -- type-checking IS the proof.

### What "type-checks" means

In Agda, a type signature like `reachability : (s1 s2 : CogState) -> Path s1 s2` is a theorem statement. If the corresponding term (proof body) passes the type checker, the theorem is proven. Agda's type checker is itself a verified program, so the trust base is minimal.

---

## Theorem Summary

| # | Statement | Proof technique |
|---|-----------|----------------|
| 1 | Reachability (completeness) | Constructive path computation |
| 2 | Minimality (d=3 necessary) | **UNPROVEN (Conjecture)** |
| 3-8 | Group axioms (assoc, id, inv, comm) | Exhaustive case analysis on finite type |
| 9 | Shortest path (belief-path) | Constructive algorithm + Hamming bound |
| 10 | Operator independence | Case analysis showing distinct effects |
| 11 | Bounded diameter (max distance = 6 steps) | Follows from Theorem 9 |

---

## Key Design Decisions

The `--without-K` flag disables Streicher's Axiom K (uniqueness of identity proofs). This means:
- Proofs are valid under HoTT interpretations, not just classical type theory
- Some equality proofs require explicit transport rather than direct pattern matching on `refl`
- No hidden axioms beyond core Martin-Lof Type Theory

Many proofs proceed by exhaustive case analysis over Z3 (3 elements) or Z3^3 (27 elements). This is tractable for Agda's termination checker and produces fully computational proofs.

---

## Open Problems

**Conjecture 2 (Minimality)** is the primary open formal problem. A proof would require:
1. A formal definition of "adequate cognitive model" (which properties must be preserved)
2. A demonstration that any group with fewer than 27 elements fails at least one required property
3. This likely requires formalizing at least some empirical constraints, making it a hybrid formal/empirical problem

See `guides/for-agda-users.md` for contribution guidelines.

---

## Related Files

- `c4-comp-v5.agda` -- Main Agda proof file (all 11 theorems)
- `guides/for-agda-users.md` -- Detailed walkthrough of the proof structure
- `papers/c4-deep-dive-en.md` -- Full mathematical exposition
