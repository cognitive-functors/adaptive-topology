# The FRA Meta-Pattern: Cross-Domain Isomorphism Table

## Fingerprint -> Route -> Adapt — One Pattern, Infinite Incarnations

**Authors:** Ilya Selyutin, Nikolai Kovalev
**Status:** Working document
**Date:** February 2026

---

## TL;DR

The **Fingerprint -> Route -> Adapt** (FRA) pattern is a meta-structure that manifests across dozens of independent systems. But in each domain it is *named differently*. This table reveals: behind different words lies the same mechanism.

---

## 1. MASTER TABLE: FRA Across Domains

### Column Legend

| Column | Meaning |
|--------|---------|
| **Domain** | Field of knowledge |
| **System** | Specific system or mechanism |
| **F — Fingerprint** | How the system "reads" input data |
| **R — Route** | How a strategy is selected |
| **A — Adapt** | How execution is corrected on the fly |
| **Vocabulary** | What FRA is called in this domain |

---

### 1.1 Cognitive Science and Psychology

| System | F — Fingerprint | R — Route | A — Adapt | Domain vocabulary |
|--------|-----------------|-----------|-----------|-------------------|
| **C4 (our model)** | Classify along (T, D, A) | Activate cognitive strategy | Correct via feedback | Classify -> Route -> Adapt |
| **Human attention** | Assess stimulus relevance | Direct focus (top-down / bottom-up) | Redirect on new data | Notice -> Focus -> Refocus |
| **CBT (therapy)** | Identify cognitive distortion | Apply restructuring technique | Check result, adjust | Identify -> Intervene -> Evaluate |
| **Metacognition** | Reflect on thinking process | Choose thinking strategy | Evaluate and switch | Monitor -> Select -> Regulate |
| **NLP (metaprograms)** | Identify client's metaprogram | Match communication | Calibrate by response | Calibrate -> Match -> Recalibrate |
| **System 1 / System 2** | Fast assessment: familiar? | System 1 (auto) or System 2 (deliberative) | Switch on error | Recognize -> Delegate -> Override |

---

### 1.2 Neuroscience

| System | F — Fingerprint | R — Route | A — Adapt | Domain vocabulary |
|--------|-----------------|-----------|-----------|-------------------|
| **Prefrontal cortex** | Encode task context | Route to executive sub-network | Update via reward signal | Encode -> Gate -> Update |
| **Basal ganglia** | Evaluate action value | Go / No-Go (direct / indirect pathway) | Dopamine correction | Evaluate -> Select -> Reinforce |
| **Hippocampus** | Place cells: "where am I?" | Replay -> route through memory | Reconsolidation | Locate -> Replay -> Reconsolidate |
| **Neuromodulation** | Detect mode (stress/rest/search) | Shift neurotransmitter balance | Homeostatic tuning | Sense -> Modulate -> Rebalance |
| **Cerebellum** | Compare prediction vs reality | Correct motor program | Minimize prediction error | Predict -> Correct -> Refine |

---

### 1.3 Biology and Evolution

| System | F — Fingerprint | R — Route | A — Adapt | Domain vocabulary |
|--------|-----------------|-----------|-----------|-------------------|
| **Immune system** | Antigen -> MHC presentation | Clonal selection (B/T cells) | Affinity maturation | Recognize -> Select -> Mature |
| **Chemotaxis** | Concentration gradient | Move toward/away | Receptor modulation | Sense -> Move -> Desensitize |
| **Gene regulation** | Signal molecule -> receptor | Activate transcription cascade | Negative feedback loops | Signal -> Transcribe -> Feedback |
| **Photosynthesis (C3/C4/CAM)** | Temperature + humidity + CO2 | Choose metabolic pathway | Seasonal restructuring | Sense -> Metabolize -> Acclimate |
| **Natural selection** | Environment -> selection pressure | Differential reproduction | Genetic drift + mutations | Pressure -> Select -> Drift |

---

### 1.4 Computer Science and Optimization

| System | F — Fingerprint | R — Route | A — Adapt | Domain vocabulary |
|--------|-----------------|-----------|-----------|-------------------|
| **MASTm (our solver)** | 7D instance fingerprint for TSP | Select decomposition strategy | V-cycle + boundary optimization | Fingerprint -> Decompose -> Refine |
| **SATzilla / AutoFolio** | SAT instance features | Select solver from portfolio | Restart on timeout | Profile -> Select -> Restart |
| **AutoML** | Dataset meta-features | Select architecture + hyperparameters | Early stopping + fine-tune | Characterize -> Configure -> Tune |
| **Compiler** | Code profile (loops, branches) | Choose optimizations (O1/O2/O3) | PGO (profile-guided optimization) | Profile -> Optimize -> Recompile |
| **Load balancing** | Server monitoring | Request routing | Autoscaling | Monitor -> Route -> Scale |
| **DNS/CDN** | Geolocation + latency | Route to nearest server | Failover on failure | Resolve -> Direct -> Failover |

---

### 1.5 Economics and Markets

| System | F — Fingerprint | R — Route | A — Adapt | Domain vocabulary |
|--------|-----------------|-----------|-----------|-------------------|
| **Market-making** | Order flow + volatility | Set bid/ask spread | Adjust by inventory | Read -> Quote -> Rebalance |
| **Central bank** | Macro indicators (CPI, GDP) | Set interest rate (Taylor rule) | Forward guidance | Measure -> Set -> Communicate |
| **Venture capital** | Due diligence -> startup valuation | Invest / pass | Follow-on rounds | Evaluate -> Bet -> Double-down |
| **Insurance** | Actuarial risk assessment | Set premium + terms | Reinsurance | Assess -> Price -> Hedge |

---

### 1.6 Ecology

| System | F — Fingerprint | R — Route | A — Adapt | Domain vocabulary |
|--------|-----------------|-----------|-----------|-------------------|
| **Niche partitioning** | Resource profile of environment | Species specialization | Plasticity under change | Survey -> Specialize -> Plasticity |
| **Migration** | Photoperiod + temperature | Choose migration route | Feeding stopovers | Sense -> Migrate -> Stopover |
| **Foraging** | Assess patch quality | Exploit / Explore (marginal value) | Switch on depletion | Assess -> Forage -> Switch |

---

### 1.7 Engineering and Control

| System | F — Fingerprint | R — Route | A — Adapt | Domain vocabulary |
|--------|-----------------|-----------|-----------|-------------------|
| **TRIZ** | Formulate contradiction | Choose from 40 principles | Iterative refinement | Contradict -> Resolve -> Iterate |
| **PID controller** | Error (e = setpoint - actual) | P + I + D components | Auto-tuning of coefficients | Measure -> Correct -> Autotune |
| **ADAS (autopilot)** | Cameras + lidar -> scene | Select maneuver | Adjust to traffic | Perceive -> Decide -> Steer |
| **Smart Grid** | Demand + generation forecast | Balance (demand response) | Storage / purchase | Forecast -> Balance -> Store |
| **DevOps/SRE** | Metric monitoring (SLI/SLO) | Alert -> runbook | Post-mortem -> update | Observe -> Respond -> Improve |

---

### 1.8 Education and Learning

| System | F — Fingerprint | R — Route | A — Adapt | Domain vocabulary |
|--------|-----------------|-----------|-----------|-------------------|
| **Adaptive learning** | Diagnose student's level | Select content/assignment | Correct based on results | Diagnose -> Prescribe -> Adjust |
| **Scaffolding (Vygotsky)** | Assess zone of proximal development | Provide appropriate hint | Remove support as competence grows | Assess -> Support -> Fade |
| **Socratic method** | Identify misconception | Ask the right question | Follow the answer | Probe -> Question -> Follow |

---

### 1.9 Medicine

| System | F — Fingerprint | R — Route | A — Adapt | Domain vocabulary |
|--------|-----------------|-----------|-----------|-------------------|
| **Clinical diagnosis** | History + tests + examination | Differential diagnosis -> treatment | Adjust by dynamics | Examine -> Diagnose -> Titrate |
| **Antibiotic therapy** | Culture + sensitivity test | Choose antibiotic | Switch on resistance | Culture -> Prescribe -> Escalate |
| **Triage (ER)** | Severity assessment (scale) | Prioritize patients | Reassess on change | Triage -> Prioritize -> Reassess |

---

### 1.10 Art and Creativity

| System | F — Fingerprint | R — Route | A — Adapt | Domain vocabulary |
|--------|-----------------|-----------|-----------|-------------------|
| **Improvisation (jazz)** | Listen to context (harmony, rhythm) | Choose scale / phrase | React to partners | Listen -> Play -> React |
| **Writing** | Sense the intent / mood | Choose style / technique | Edit on rereading | Sense -> Draft -> Revise |
| **Design** | User research / context | Prototype -> solution | User testing -> iteration | Research -> Prototype -> Iterate |

---

## 2. META-ANALYSIS: WHAT THE TABLE REVEALS

### 2.1 Universal Three-Phase Structure

Despite radically different domains, **all** systems implement three phases:

```
INPUT -> [READ STRUCTURE] -> [SELECT STRATEGY] -> [EXECUTE WITH CORRECTION] -> OUTPUT
           ^                    ^                     ^
        Fingerprint           Route                  Adapt
```

### 2.2 Domain Vocabulary Summary

| Domain | F | R | A |
|--------|---|---|---|
| Cognitive science | Classify / Notice / Identify | Route / Focus / Intervene | Adapt / Refocus / Evaluate |
| Neuroscience | Encode / Evaluate / Predict | Gate / Select / Correct | Update / Reinforce / Refine |
| Biology | Recognize / Sense / Signal | Select / Move / Transcribe | Mature / Desensitize / Feedback |
| CS / Optimization | Fingerprint / Profile / Monitor | Decompose / Select / Route | Refine / Restart / Scale |
| Economics | Read / Measure / Evaluate | Quote / Set / Bet | Rebalance / Communicate / Hedge |
| Ecology | Survey / Sense / Assess | Specialize / Migrate / Forage | Plasticity / Stopover / Switch |
| Engineering | Measure / Perceive / Observe | Correct / Decide / Respond | Autotune / Steer / Improve |
| Education | Diagnose / Assess / Probe | Prescribe / Support / Question | Adjust / Fade / Follow |
| Medicine | Examine / Culture / Triage | Diagnose / Prescribe / Prioritize | Titrate / Escalate / Reassess |
| Art | Listen / Sense / Research | Play / Draft / Prototype | React / Revise / Iterate |

### 2.3 Observation: Three Universal Verbs

Collapsing all domains to maximally abstract verbs:

| Phase | Universal verb | Essence |
|-------|----------------|---------|
| **F** | **Read** | Extract structural information from the input |
| **R** | **Direct** | Choose an action based on the structure read |
| **A** | **Refine** | Correct the action based on results |

Or even shorter: **Understand -> Choose -> Improve**.

---

## 3. WHY THIS IS ONE PATTERN, NOT AN ANALOGY

One might object: "This is just a trivial decomposition of any process into input -> processing -> output." But that is incorrect:

1. **Not every system implements FRA.** Counterexample: a *fixed strategy* (doing the same thing regardless of input) — no fingerprint, no routing. A rigid algorithm is not FRA.

2. **The theorem proves superiority.** FRA is *mathematically guaranteed* to be >= any fixed strategy (Theorem 1, Partitioning Bound). This is not an opinion — it is an inequality.

3. **Heterogeneity is the key condition.** FRA provides a *strict* advantage if and only if different strategies are optimal for different input subclasses (Theorem 2, Heterogeneity Bound). This is a testable condition.

4. **Convergent evolution.** 32+ systems across 6 domains *independently* arrived at the same structure. This is not borrowing — it is mathematical inevitability in heterogeneous environments.

---

## 4. OPEN QUESTIONS

1. Do **counterexample systems** exist — successful yet not implementing FRA?
2. What is the **minimum number of strategies** for a given domain?
3. Does a **universal fingerprint** exist that works across domains?
4. Is FRA a **necessary condition** for intelligence or only sufficient?

---

## See Also

- [Adaptive Routing Theorem](algorithmic-topology/03-adaptive-routing-theorem.md) — formal proof
- [Cross-Domain Evidence (32 systems)](algorithmic-topology/04-cross-domain-evidence.md)
- [Future Research Directions](FUTURE-RESEARCH-DIRECTIONS-en.md)
- [WHY-C4.md](../WHY-C4.md) — why the model is called C4

---

Copyright 2024-2026 Ilya Selyutin, Nikolai Kovalev and contributors.
