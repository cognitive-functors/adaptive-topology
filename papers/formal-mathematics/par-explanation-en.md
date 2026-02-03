### 1. Basic Concepts: Duality and Linear Implication

* **Duality (A^perp):** In linear logic, every formula has a "dual" or "perpendicular." Intuitively, this can be understood as "negation" or "the obligation to spend a resource." Key property: `(A^perp)^perp = A`.
* **Linear implication (A lollipop B):** The expression `A lollipop B` means: "**Given exactly one resource A, I can produce exactly one resource B**." This is not classical implication! Here `A` is *consumed* to produce `B`. This is an operation akin to a chemical reaction.
* **Multiplicative Disjunction (Par) (A par B):** This is harder to understand. Intuition: `A par B` means that I have **the ability to interact with an external environment that will provide either `A` or `B`**. This is not "or" in the classical sense. It is asynchronous interaction: "I offer a choice to the external world." It is sometimes described as "if I have `A^perp`, then I get `B`, and if I have `B^perp`, then I get `A`."

### 2. First Equality: A^perp lollipop B == A par B

This is perhaps the most important equality, as it establishes the very connection between implication and par.

**a) Explanation via the definition of implication:**

In linear logic, the implication `A lollipop B` is **defined** through duality and par:
`A lollipop B := A^perp par B`

This is an axiomatic definition. Why is it reasonable? Let us consider what `A lollipop B` means:
> "If I consume A, then I produce B."

And what does `A^perp par B` mean?
> "I have a choice, determined by the external environment: either I receive `A^perp` (which is equivalent to *giving away* `A`), or I receive `B`."

Let us connect these ideas: having `A^perp par B` means I can participate in a protocol where:
* If the external world provides me with `A` (which for me amounts to *consuming* `A`, since I "use" it), then I must provide it with `A^perp` (this is part of the deal). But under the rules of par, if I choose the `A^perp` path, I must carry it out. However, there is also a second path!
* Instead, I can say: "I will not provide `A^perp`. Instead, I will choose the second path and provide `B`."

In the end, the net effect of this protocol is: **the world gives me `A`, and I give the world `B`**. This is precisely the definition of the implication `A lollipop B`.

**Conclusion:** `A lollipop B` is by definition equal to `A^perp par B`. Now, if we replace `A` with `A^perp` in this equality, we obtain:
`(A^perp) lollipop B := (A^perp)^perp par B`
Since `(A^perp)^perp = A`, this simplifies to:
`A^perp lollipop B := A par B`

Which is what we wanted to show.

**b) Explanation via "transfer of obligations":**
* `A^perp lollipop B` means: "By spending the resource `A^perp`, I obtain `B`."
* But "spending the resource `A^perp`" is the same as "receiving the resource `A`" (because `A` and `A^perp` are opposites). Imagine that `A` is a promissory note. Spending the note (`A^perp`) means presenting it and receiving the money (`A`).
* Thus, the assertion `A^perp lollipop B` is equivalent to: "Having received the resource `A`, I produce the resource `B`."
* And this is, in essence, the description of the nature of `A par B`: I have a process that, upon receiving `A` (from the external environment), outputs `B`.

### 3. Second Equality: A par B == B^perp lollipop A

This equality demonstrates a remarkable symmetry.

**a) Simple proof via the first equality:**

We have just proved that `X lollipop Y := X^perp par Y` (for any X and Y).

1. Take our first equality: `A par B == A^perp lollipop B`.
2. Now apply the same fundamental formula `X lollipop Y := X^perp par Y`, but this time take `X = B^perp` and `Y = A`.
   * We obtain: `B^perp lollipop A := (B^perp)^perp par A`.
3. Simplify the duality: `(B^perp)^perp = B`. Substituting: `B^perp lollipop A := B par A`.
4. In linear logic, the operation par is commutative: `B par A := A par B`.
5. Therefore, `B^perp lollipop A := A par B`.

Thus, the chain is:
`A par B == A^perp lollipop B == ... == B^perp lollipop A`
(where the omitted step is the application of symmetry).

**b) Semantic interpretation:**

* `A par B`: I have a process ready for interaction. If the environment provides `A`, I give `B`. If the environment provides `B`, I give `A`. (This is not entirely precise, but a useful interpretation).
* `B^perp lollipop A`: "By spending the resource `B^perp`, I obtain `A`." But "spending `B^perp`" is the same as "receiving `B`."
  * That is, this assertion says: "If I am given `B`, then I produce `A`."

Compare:
* `A par B`: "If you give A, I give B. If you give B, I give A."
* `B^perp lollipop A`: "If you give B, I give A."

The second phrase is precisely one of the two possibilities encoded in the first. Thanks to symmetry and duality, in linear logic these assertions turn out to be equivalent. The protocol `A par B` is symmetric, and it can be described from the perspective of awaiting `A` as well as from the perspective of awaiting `B`.

### Summary and Reference Table

We obtain a chain of identical transformations based on the definition of implication and the properties of duality:

| Step | Equality | Justification |
| :--- | :--- | :--- |
| 1 (Definition) | **A lollipop B == A^perp par B** | Original definition of linear implication. |
| 2 (Substitution) | **(A^perp) lollipop B == (A^perp)^perp par B** | Replace `A` with `A^perp` in step 1. |
| 3 (Simplification) | **A^perp lollipop B == A par B** | Since `(A^perp)^perp = A`. **First equality proved.** |
| 4 (Symmetry) | **A par B == B par A** | Commutativity of the connective par. |
| 5 (Definition) | **B lollipop A == B^perp par A** | Apply step 1 to the formula `B lollipop A`. |
| 6 (Substitution) | **(B^perp) lollipop A == (B^perp)^perp par A** | Replace `B` with `B^perp` in step 5. |
| 7 (Simplification) | **B^perp lollipop A == B par A** | Since `(B^perp)^perp = B`. |
| 8 (Final step) | **A par B == B^perp lollipop A** | From steps 4 and 7: `A par B == B par A == B^perp lollipop A`. |

Thus, all three formulas `A^perp lollipop B`, `A par B`, and `B^perp lollipop A` are merely different syntactic representations of one and the same fundamental interaction process in linear logic. This is a powerful manifestation of the symmetry inherent in this logical system.
