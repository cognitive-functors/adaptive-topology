# C4 for Linguists

How the Complete Cognitive Coordinate System provides a formal framework for discourse analysis, tense/aspect semantics, and perspective theory.

---

## Overview

C4 defines cognitive space as Z3^3 with three axes:

- **T (Time):** Past (0) / Present (1) / Future (2)
- **D (Scale):** Concrete (0) / Abstract (1) / Meta (2)
- **A (Agency):** Self (0) / Other (1) / System (2)

Each axis has direct linguistic correlates. The claim is that natural language *encodes* C4 coordinates as part of its deep structure, and that discourse movement can be modeled as trajectories through C4 space.

---

## T-Axis: Tense, Aspect, and Temporal Deixis

The T-axis maps to grammatical and semantic time:

| T-value | Linguistic Realization |
|---------|----------------------|
| Past (0) | Past tense morphology, narrative past, perfect aspect, retrospective markers ("used to," "back then") |
| Present (1) | Present tense, progressive aspect, deictic "now," habitual present |
| Future (2) | Future tense, prospective aspect, modal "will/shall," intentional constructions |

**Beyond simple tense:** The T-axis also captures:
- **Aspect** as fine-grained T-position (perfective = completed-past, imperfective = ongoing-present)
- **Temporal discourse markers** ("meanwhile," "subsequently," "in retrospect") as T-axis operators
- **Narrative time shifts** in fiction as T-axis trajectories

**Cross-linguistic note:** While tense marking varies (some languages lack obligatory tense), temporal *orientation* appears universal. C4 models the cognitive orientation, not the morphological encoding.

---

## D-Axis: Abstraction Level and Halliday's Strata

The D-axis aligns with Halliday's Systemic Functional Linguistics (SFL) stratification and with levels of abstraction in discourse:

| D-value | SFL Stratum | Discourse Markers |
|---------|-------------|-------------------|
| Concrete (0) | Lexicogrammar, specific reference | Proper nouns, definite articles, sensory verbs, direct speech |
| Abstract (1) | Semantics, generalization | Generic nouns, quantifiers ("all," "most"), nominalization, hedging |
| Meta (2) | Context of situation/culture, metalanguage | Discourse markers ("in other words"), reported speech, reflexive commentary |

**Key pattern:** Academic writing exhibits characteristic D-axis oscillation: concrete example (D=0) -> abstract principle (D=1) -> meta-discussion of methodology (D=2) -> back to data (D=0).

**Nominalization** is a primary linguistic device for D-axis upshift: "The government decided" (D=0, concrete actor) -> "The decision" (D=1, nominalized process) -> "Decision-making processes" (D=2, meta-category).

---

## A-Axis: Perspective, Voice, and Focalization

The A-axis maps to linguistic perspective-taking:

| A-value | Linguistic Realization |
|---------|----------------------|
| Self (0) | First person, subjective modality ("I think," "I feel"), experiencer constructions |
| Other (1) | Second/third person, reported speech, perspective shift ("she believed that"), empathetic deixis |
| System (2) | Passive voice, impersonal constructions ("it is known"), institutional voice, generic "one" |

**Narrative theory connection (Genette):**
- **Internal focalization** = Self (0): narrator sees through character's eyes
- **External focalization** = Other (1): narrator observes from outside
- **Zero focalization** = System (2): omniscient narrator

**Politeness theory (Brown & Levinson):**
- Face-threatening acts involve forced A-axis shifts
- Hedging = temporary shift to System (2) to depersonalize
- "You should" (A=1, direct) vs. "One might consider" (A=2, depersonalized)

---

## Discourse Analysis Framework

### Coding Scheme

For any clause or discourse unit, assign (T, D, A):

```
Input: "I remember when the whole team struggled with that deadline."
T = Past (0) -- "remember," past reference
D = Concrete (0) -- specific event ("that deadline")
A = Self (0) -- "I" as experiencer, though referencing team

C4 code: (0, 0, 0)

Input: "Organizations generally fail when communication breaks down."
T = Present (1) -- generic/habitual present
D = Abstract (1) -- generalized claim
A = System (2) -- "organizations" as systemic agent

C4 code: (1, 1, 2)
```

### Discourse Trajectory Analysis

A text or conversation can be represented as a sequence of C4 coordinates. This enables:

1. **Trajectory visualization:** Plot (T, D, A) over discourse time
2. **Movement patterns:** Identify habitual axis shifts (e.g., a speaker who never leaves D=0)
3. **Coherence metrics:** Adjacent discourse units with Hamming distance > 2 may signal incoherence
4. **Genre signatures:** Different genres have characteristic C4 distributions and movement patterns

### Genre Signatures (Hypothesized)

| Genre | Dominant Region | Characteristic Movement |
|-------|----------------|------------------------|
| Personal narrative | T=0, D=0, A=0 | Linear T-axis progression, occasional D-jumps |
| Scientific paper | T=1, D=1-2, A=2 | D-axis oscillation (data <-> theory), A fixed at System |
| Political speech | T=1-2, D=1, A=0-2 | A-axis oscillation (we/they/system), T biased toward Future |
| Therapy transcript | All T, D=0-1, A=0-1 | Gradual T-shifts, therapist induces A-shifts |
| Legal text | T=1, D=1-2, A=2 | Narrow region, high D, fixed System perspective |

---

## Computational Applications

### Automated Discourse Tagging

C4 coordinates can be predicted from text using NLP classifiers:

- **Architecture:** DeBERTa-v3 with multi-task heads for T, D, A
- **Training data:** Human-annotated discourse units with (T, D, A) labels
- **Output:** Per-sentence or per-clause C4 coordinate assignment
- **Application:** Automated discourse analysis, genre classification, coherence scoring

### Corpus Linguistics

C4 annotation enables quantitative questions:
- How does D-axis distribution differ between spoken and written registers?
- Do bilingual speakers show different C4 trajectories in L1 vs. L2?
- Is there a correlation between T-axis rigidity and cognitive bias in persuasive text?

---

## Theoretical Connections

| Linguistic Theory | C4 Connection |
|-------------------|---------------|
| Halliday's SFL | D-axis as stratification, A-axis as tenor |
| Genette's Narratology | A-axis as focalization, T-axis as narrative time |
| Lakoff's Conceptual Metaphor | Cross-domain mapping = C4 isomorphism detection |
| Discourse Representation Theory | C4 coordinates as discourse referent properties |
| Rhetorical Structure Theory | Rhetorical relations as C4 transitions |

---

## Limitations

- The three-valued discretization (0/1/2 per axis) is coarse; continuous or finer-grained models may be needed for detailed linguistic analysis.
- Inter-annotator agreement for C4 coding has not yet been established at scale.
- The framework currently addresses ideational meaning more than interpersonal or textual metafunctions.

---

## References

- Halliday, M.A.K. (1994). *An Introduction to Functional Grammar*.
- Genette, G. (1980). *Narrative Discourse*.
- Selyutin, I. & Kovalev, N. (2025). "C4: Complete Cognitive Coordinate System." Preprint.

---

*Contact: psy.seliger@yandex.ru*
