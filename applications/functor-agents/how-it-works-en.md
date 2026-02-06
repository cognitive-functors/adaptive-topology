# HOW IT WORKS -- A PRACTICAL GUIDE TO C4-COMPOSER

## WHAT IT IS

**C4-Enhanced Composer** is a meta-agent that creates AI agent teams with **mathematically guaranteed completeness**.

**In plain terms:**
- You say: "I want a system for lead generation"
- Composer analyzes the task through the lens of **27 cognitive functions** (C4 functors)
- It creates a minimal team of agents that covers **all required functions**
- It shows: what is covered, what is missing, whether there are duplicates

**Result:** instead of "15 agents chosen at random," you get "6 agents with 100% coverage of critical functions"

---

## HOW IT WORKS (end-to-end)

### **STEP 1: The User Provides a Task**

```
User: "Create a system for finding and qualifying leads"
```

---

### **STEP 2: Composer Analyzes via C4 (Phase 1)**

**What Composer does internally:**

```
[Task analysis]
Domain: B2B sales, lead generation
Key operations:
 - Lead sourcing (data collection) -> tau Present, kappa (concrete data)
 - Qualification (distinction) -> delta
 - History check (past) -> tau Past
 - CRM integration -> sigma

[Determining required functors]
Basic:
 1. tau (Past) -- check whether contact was made previously
 2. tau (Present) -- collect leads now
 3. delta -- qualify (separate good from bad)
 4. sigma -- integrate into CRM

Coverage: 4/27 = 14.8%
Assessment: sufficient for the basic task
```

**Composer output:**
```json
{
 "requiredFunctors": ["tau", "delta", "sigma"],
 "modalities": {"tau": ["Past", "Present"]},
 "coverageNeeded": 14.8
}
```

---

### **STEP 3: Composer Selects Agents (Phase 2)**

**What it does:**

Examines the list of available agents with their C4 tags:

```
Available agents:
 - history_checker@domain [c4Functor: "tau", modality: "Past"]
 - lead_scraper@domain [c4Functor: "tau", modality: "Present"]
 - qualifier@domain [c4Functor: "delta"]
 - crm_integrator@domain [c4Functor: "sigma"]
 - pattern_analyzer@domain [c4Functor: "rho"] <- not needed for this task
 - scheduler@domain [c4Functor: "tau", modality: "Future"] <- not needed
```

**Matching result:**
```
 tau Past -> history_checker
 tau Present -> lead_scraper
 delta -> qualifier
 sigma -> crm_integrator

Gaps: none
Redundancy: none
```

---

### **STEP 4: Composer Creates the Map JSON (Phase 3)**

**Workflow structure:**

```
[Node 1: history_checker] -> [Node 2: lead_scraper] -> [Node 3: qualifier] -> [Node 4: crm_integrator]
 tau Past tau Present delta sigma
```

**JSON (simplified):**
```json
{
 "title": "leadgen-basic-system",
 "c4Coverage": {
 "baseFunctors": ["tau", "delta", "sigma"],
 "totalFunctors": 4,
 "coveragePercent": 14.8,
 "missingCritical": [],
 "redundant": []
 },
 "flow": {
 "nodes": [
 {
 "id": "n1",
 "data": {
 "uname": "history_check",
 "text": "Check: was this lead contacted before?",
 "c4Functor": "tau",
 "c4Modality": "Past"
 }
 },
 {
 "id": "n2",
 "data": {
 "uname": "scrape_leads",
 "text": "Scrape 50 leads from LinkedIn",
 "c4Functor": "tau",
 "c4Modality": "Present"
 }
 },
 {
 "id": "n3",
 "data": {
 "uname": "qualify",
 "text": "Score each lead 0-100, keep > 70",
 "c4Functor": "delta"
 }
 },
 {
 "id": "n4",
 "data": {
 "uname": "crm_add",
 "text": "Add qualified leads to CRM",
 "c4Functor": "sigma"
 }
 }
 ],
 "edges": [
 {
 "source": "n1",
 "target": "n2",
 "data": {
 "recipient": "history_checker@domain",
 "c4Functor": "tau",
 "sequence": 1
 }
 },
 // ... remaining edges
 ]
 }
}
```

---

### **STEP 5: Validation (Phases 4--5)**

**Composer verifies:**

 **Coverage check:** are all critical functors covered? -> YES
 **Redundancy check:** are there duplicates? -> NO
 **Sequence check:** is the order logical? -> YES (tau Past -> tau Present -> delta -> sigma)
 **Composition check:** are compositions needed? -> NO (simple task)

**Result:** the completed JSON is delivered to the user.

---

### **STEP 6: The User Sees the Result**

**UI display:**

```
+-----------------------------------------------------------+
| Workflow: leadgen-basic-system                            |
+-----------------------------------------------------------+
| C4 COVERAGE: 14.8% (4/27 functors)                       |
|                                                           |
| Functors used:                                            |
| - tau Past -- Check history                               |
| - tau Present -- Collect leads now                        |
| - delta -- Qualify (differentiate)                        |
| - sigma -- Integrate into CRM                            |
|                                                           |
| All critical functors covered                             |
| No redundancy                                             |
| Optimal sequence (Past -> Present -> Qualify -> CRM)      |
|                                                           |
| Optional enhancements:                                    |
| - Add rho (pattern detection) for conversion analysis     |
| - Add tau Future (scheduler) for follow-ups               |
+-----------------------------------------------------------+
```

**Workflow visualization:**

```
+--------------+  +--------------+  +--------------+  +--------------+
| tau Past     |--| tau Present  |--| delta        |--| sigma        |
| History      |  | Scraper      |  | Qualifier    |  | CRM          |
+--------------+  +--------------+  +--------------+  +--------------+
```

---

## HOW COMPOSER MAKES DECISIONS

### **The Functor Selection Algorithm**

```
+-----------------------------------------------------------+
| INPUT DATA:                                               |
| - User goal: "Create leadgen system"                      |
| - Available agents: 10 agents with c4Functor tags         |
+-----------------------------------------------------------+
 |
+-----------------------------------------------------------+
| STAGE 1: KEYWORD EXTRACTION                               |
| "leadgen" -> data collection, qualification               |
| "system" -> integration, process                          |
+-----------------------------------------------------------+
 |
+-----------------------------------------------------------+
| STAGE 2: MAPPING TO COGNITIVE OPERATIONS                  |
| - Data collection -> tau (Present) + kappa (concrete)     |
| - Qualification -> delta (distinction)                    |
| - History check -> tau (Past)                             |
| - Integration -> sigma                                    |
+-----------------------------------------------------------+
 |
+-----------------------------------------------------------+
| STAGE 3: PRIORITIZATION                                   |
| Critical: tau Past (avoid duplicates), tau Present,       |
|           delta, sigma                                    |
| Optional: rho (patterns), tau Future (planning)           |
+-----------------------------------------------------------+
 |
+-----------------------------------------------------------+
| STAGE 4: AGENT SELECTION                                  |
| tau Past -> history_checker                               |
| tau Present -> lead_scraper                               |
| delta -> qualifier                                        |
| sigma -> crm_integrator                                   |
+-----------------------------------------------------------+
 |
+-----------------------------------------------------------+
| OUTPUT: Map JSON + c4Coverage metadata                    |
+-----------------------------------------------------------+
```

---

## EXAMPLES BY COMPLEXITY

### **EXAMPLE 1: SIMPLE TASK (5--7 functors, 18--26% coverage)**

**User request:**
```
"Find 100 leads in fintech and add them to CRM"
```

**C4 Analysis:**
```
Operations:
 1. Lead collection -> tau Present
 2. Filtering by criteria -> delta
 3. Adding to CRM -> sigma

Functors: 3
Coverage: 11%
Team: 3 agents
```

**Result:**
```
Workflow:
 [Scraper] -> [Filter] -> [CRM]
 tau        delta       sigma

Creation time: 10 seconds
Agents: 3 (minimum)
```

---

### **EXAMPLE 2: MEDIUM TASK (8--12 functors, 30--44% coverage)**

**User request:**
```
"Create a lead generation system with automated outreach and results analysis"
```

**C4 Analysis:**
```
Operations:
 1. History check -> tau Past
 2. Lead collection -> tau Present
 3. Qualification -> delta
 4. Message adaptation -> phi (context)
 5. Touch scheduling -> tau Future
 6. CRM integration -> sigma
 7. Pattern analysis -> rho
 8. Effectiveness forecast -> tau o rho (composition!)

Functors: 8 (7 basic + 1 composition)
Coverage: 30%
Team: 8 agents
```

**Result:**
```
Main flow:
 [History] -> [Scraper] -> [Qualifier] -> [Adapter] -> [Scheduler] -> [CRM]
 tau-        tau0        delta         phi          tau+          sigma
 |
Parallel branch: [Analyzer] -> [Forecaster]
                  rho          tau o rho

Creation time: 15 seconds
Agents: 8 (optimized)
Compositions: 1 (tau o rho for forecasting)
```

---

### **EXAMPLE 3: COMPLEX TASK (13--18 functors, 48--67% coverage)**

**User request:**
```
"Build a complete sales system: from lead generation to deal closure,
with rejection cause analysis, process optimization, and agent training"
```

**C4 Analysis:**
```
Operations:
 BASE:
 1. tau Past -- client history
 2. tau Present -- current collection
 3. tau Future -- planning
 4. delta -- qualification, segmentation
 5. rho -- conversion/rejection patterns
 6. sigma -- data integration
 7. phi -- context adaptation
 8. mu -- process reflection
 9. iota -- alternative approaches

 COMPOSITIONS:
 10. tau o rho -- trend forecasting
 11. delta o iota -- multi-stakeholder analysis (client vs. company)
 12. rho o phi -- adaptive patterns
 13. mu o phi -- process optimization
 14. lambda o sigma -- building a general theory of sales
 15. sigma o iota -- synthesis of contradictions (speed vs. quality)

Functors: 15 (9 basic + 6 compositions)
Coverage: 56%
Team: 15-17 agents
```

**Result:**
```
Main pipeline:
 [History] -> [Scraper] -> [Qualifier] -> [Adapter] -> [Scheduler] -> [CRM] -> [Closer]
 tau-        tau0        delta         phi          tau+          sigma    sigma

Analysis layer (parallel):
 [Pattern Detector] -> [Forecaster] -> [Adaptive Engine]
 rho                   tau o rho       rho o phi

Optimization layer (feedback):
 [Process Reflector] -> [Optimizer] -> [Theory Builder]
 mu                     mu o phi       lambda o sigma

Alternative strategies:
 [Invertor] -> [Dialectician]
 iota          sigma o iota

Creation time: 30 seconds
Agents: 17 (full system)
Compositions: 6
Feedback loops: 2
```

---

## HOW TO READ C4 COVERAGE

### **Structure of c4Coverage (meaning of each field):**

```json
{
 "c4Coverage": {
 "baseFunctors": ["tau", "delta", "rho", "sigma", "phi"],
 // Which basic functors are used (out of 9)

 "baseFunctorModalities": {
 "tau": ["Past", "Present", "Future"]
 },
 // For tau: which temporal modalities are engaged

 "compositions": ["tau o rho", "rho o phi", "mu o phi"],
 // Which compositions are used (out of 18)

 "totalFunctors": 10,
 // Total number of unique functors

 "coveragePercent": 37.0,
 // Coverage percentage (10/27 = 37%)

 "missingCritical": [],
 // Critical functors that are MISSING
 // If non-empty -> WARNING!

 "missingOptional": ["iota o lambda", "lambda o sigma"],
 // Optional functors (may improve but are not required)

 "redundant": [],
 // Duplicates (two agents with the same functor)
 // If non-empty -> WASTE!

 "sequenceWarnings": [],
 // Warnings about unnatural ordering
 // Example: "tau+ before tau- (planning before history)"

 "compositionImplementation": {
 "tau o rho": "Dedicated agent (trend_forecaster@domain)",
 "rho o phi": "Chained (pattern_analyzer -> message_adapter)",
 "mu o phi": "Feedback loop (optimizer -> all agents)"
 },
 // HOW compositions are implemented

 "analysisNotes": "Full adaptive system. Optional: add iota o lambda for ICP challenge."
 // Composer's comments
 }
}
```

---

## INTERPRETING COVERAGE

### **By coverage percentage:**

```
+------------------------------------------------------------+
| 0-15%  | MINIMAL SYSTEM                                   |
|        | Suitable for: simple tasks (1-2 operations)       |
|        | Example: "Collect leads and put them in CRM"      |
+------------------------------------------------------------+

+------------------------------------------------------------+
| 15-30% | BASIC SYSTEM                                      |
|        | Suitable for: standard processes                  |
|        | Example: "Leadgen + qualification + outreach"      |
+------------------------------------------------------------+

+------------------------------------------------------------+
| 30-50% | ADVANCED SYSTEM                                   |
|        | Suitable for: complex tasks with adaptation        |
|        | Example: "Leadgen + analysis + optimization"       |
+------------------------------------------------------------+

+------------------------------------------------------------+
| 50-70% | COMPREHENSIVE SYSTEM                              |
|        | Suitable for: strategic tasks                     |
|        | Example: "Full sales cycle + training"             |
+------------------------------------------------------------+

+------------------------------------------------------------+
| 70-100%| UNIVERSAL SYSTEM (AGI-level)                      |
|        | Suitable for: open-ended problems                 |
|        | Example: "Build a company strategy from scratch"   |
+------------------------------------------------------------+
```

---

## TROUBLESHOOTING

### **Problem 1: missingCritical is non-empty**

**Example:**
```json
"missingCritical": ["tau"]
```

**What this means:**
- Composer did not find an agent for functor tau (Past)
- This is **critical**: without a history check, outreach will produce duplicates

**What to do:**
1. Add an agent with `c4Functor: "tau", modality: "Past"`
2. Or: accept the risk (if clients are new and history is not needed)

---

### **Problem 2: redundant is non-empty**

**Example:**
```json
"redundant": ["tau"]
```

**What this means:**
- Two agents are doing the same thing (both tau Present)
- This is **waste**: you are paying for tokens twice, and conflicts are possible

**What to do:**
1. Remove one of the agents
2. Or: differentiate through phi (context)
 - Agent_A: tau Present + phi (LinkedIn)
 - Agent_B: tau Present + phi (Email databases)

---

### **Problem 3: sequenceWarnings is non-empty**

**Example:**
```json
"sequenceWarnings": ["Edge 3->1: tau Future before tau Past (unnatural flow)"]
```

**What this means:**
- Composer created a workflow where planning precedes history analysis
- This is **logically incorrect** (one cannot plan without knowing the past)

**What to do:**
1. Reorder edges (change the sequence)
2. Or: if this is intentional, add a "WHY" comment

---

### **Problem 4: coveragePercent is too low for the task**

**Example:**
```
Task: "Build a company strategy"
coveragePercent: 11% (only tau, delta, sigma)
```

**What this means:**
- The task is complex, but coverage is minimal
- Most likely, **important aspects are missing**

**What to do:**
1. Add functors:
 - rho (industry patterns)
 - lambda (abstraction of principles)
 - iota (alternative strategies)
 - mu (process reflection)
2. Reconsider the task: perhaps it is simpler than it appeared?

---

## PRACTICAL SCENARIOS

### **Scenario 1: "An agent is missing"**

**Situation:**
```
Composer returned:
 "missingCritical": ["rho"]
 "analysisNotes": "Pattern detection needed but no agent available"
```

**Resolution:**

**Option A: Create a new agent**
```javascript
const newAgent = {
 address: "pattern_detector@domain",
 name: "Pattern Detector",
 c4Functor: "rho",
 description: "Detects conversion patterns in lead data"
}
```

**Option B: Use an existing agent with an addition**
```javascript
// There exists "data_analyzer@domain" (delta)
// We can add rho to it via composition
{
 address: "data_analyzer@domain",
 c4Functor: "delta o rho", // now performs analysis + pattern detection
}
```

**Option C: Skip (if non-critical)**
```
User: "I do not need patterns right now, skip"
-> Composer marks it as missingOptional and proceeds
```

---

### **Scenario 2: "Two agents duplicate a function"**

**Situation:**
```
Composer returned:
 "redundant": ["tau"]
 "analysisNotes": "lead_scraper and contact_finder both do tau Present"
```

**Resolution:**

**Option A: Merge**
```javascript
// Remove contact_finder, keep only lead_scraper
// Update its prompt to perform both actions
```

**Option B: Differentiate through context (phi)**
```javascript
{
 address: "lead_scraper@domain",
 c4Functor: "tau",
 c4Modality: "Present",
 c4Context: "LinkedIn" // <- specialization
}

{
 address: "contact_finder@domain",
 c4Functor: "tau",
 c4Modality: "Present",
 c4Context: "Email databases" // <- different specialization
}
```

Now these are not duplicates but **parallel sources**.

---

### **Scenario 3: "A composition is needed but no agent exists"**

**Situation:**
```
Task: "Forecast the best lead sources"
-> Required: tau o rho (temporal + pattern analysis)
-> Available: tau agent and rho agent separately
-> Missing: a dedicated tau o rho agent
```

**Resolution: Chaining (agent chain)**

```json
{
 "nodes": [
 {
 "id": "n1",
 "data": {"c4Functor": "tau", "text": "Analyze temporal trends in lead sources"}
 },
 {
 "id": "n2",
 "data": {"c4Functor": "rho", "text": "Detect patterns in [[n1]] trends"}
 }
 ],
 "edges": [
 {
 "source": "n1",
 "target": "n2",
 "data": {
 "c4Composition": "tau o rho",
 "compositionNote": "Implemented via chaining: temporal -> pattern"
 }
 }
 ]
}
```

**Result:** the composition is realized through a sequence of agents.

---

### **Scenario 4: "Coverage is too high -- overkill"**

**Situation:**
```
Task: "Send an email to 10 people"
Composer created: 15 agents, coverage 55%
```

**Problem:** Composer overcomplicated the design (the task is simple, but the system is not).

**Resolution:**

**Option A: Simplify the request**
```
User: "Just send the email, no analysis or optimization"
-> Composer will recreate with 2-3 agents
```

**Option B: Limit coverage**
```
User: "Maximum 5 agents"
-> Composer will select the top 5 critical functors
```

**Option C: Specify explicitly**
```
User: "I need only: tau Present (collection) and sigma (dispatch)"
-> Composer will create a minimal system
```

---

## CUSTOMIZATION

### **How to Add a Custom Functor**

**Example:** You want to add a functor "Psi" (Creativity) for generating creative ideas.

**Step 1: Update the functor list**
```javascript
// In 27_functor_agents_system_prompts.md, add:

### 28. Psi -- CREATIVITY (Creativity Agent)
**Role:** Generator of non-standard ideas
**Function:** I create unexpected solutions, break patterns
**Response:** `[Psi]: idea: ... | novelty: 0-1 | applicability: ...`
```

**Step 2: Update the Composer prompt**
```markdown
## COMPLETE 28-FUNCTOR REFERENCE (instead of 27)

#### **28. Psi -- CREATIVITY (Creativity Agent)**
- **Role:** Idea Generator
- **Function:** Creates unexpected solutions, breaks patterns
- **Use when:** Need creative breakthrough, challenge status quo
- **Examples:** "Brainstorm unconventional marketing", "Invent new product"
```

**Step 3: Create the agent**
```javascript
{
 address: "creative_engine@domain",
 name: "Creative Engine",
 c4Functor: "Psi",
 description: "Generates unconventional ideas"
}
```

**Result:** Composer will now use Psi for creative tasks.

---

### **How to Create a Custom Composition**

**Example:** You want the composition "Psi o lambda" (Creative Abstraction) -- creativity + generalization.

**Step 1: Define the meaning**
```
Psi o lambda = first generate creative ideas (Psi),
               then extract the general principle (lambda)

Use case: "Come up with 10 promotion ideas -> identify the pattern"
```

**Step 2: Add to Composer**
```markdown
#### **29. Psi o lambda -- CREATIVE ABSTRACTION**
- **Role:** Pattern Extractor from Brainstorm
- **Function:** Generates many ideas, then finds common thread
- **Use when:** Need creative strategy, not just tactics
- **Examples:** "Innovate marketing approach", "Design new business model"
```

**Step 3: Use it**
```
User: "Come up with a promotion strategy"
Composer: "Detected need for Psi o lambda composition"
-> Creates: Creative Engine -> Abstractor
```

---

## EFFECTIVENESS METRICS

### **How to Assess Whether C4-Composer Works**

**Metric 1: Coverage Accuracy**
```
For 10 test tasks:
 - Composer identified the needed functors
 - An expert verified: is everything covered?

Target: >= 90% accuracy (9/10 tasks covered correctly)
```

**Metric 2: Redundancy Rate**
```
Out of 100 created Maps:
 - How many contained redundant agents?

Target: <= 5% (at most 5 Maps out of 100)
```

**Metric 3: Time to Team**
```
Before C4: 2-4 hours of manual selection
After C4: 10-30 seconds of autogeneration

Target: <= 60 seconds for 90% of tasks
```

**Metric 4: Team Quality**
```
A/B test:
 - Group A: teams without C4 (manual selection)
 - Group B: teams with C4 (autogeneration)

Evaluation:
 - How many tasks were completed successfully?
 - How many failures due to team gaps?

Target: Group B >= Group A in success rate
```

---

## TRAINING EXAMPLES

### **Example A: Recruiting**

**Task:**
```
"Create a system for hiring developers: from sourcing to offer"
```

**C4 Analysis (step by step):**

1. **Candidate sourcing** -> tau Present (collect resumes)
2. **Screening** -> delta (filter out unsuitable candidates)
3. **Experience analysis** -> tau Past (review work history)
4. **Technical interview** -> lambda (assess abstraction level)
5. **Culture fit** -> rho (compare with successful employees)
6. **Offer** -> tau Future (future employment conditions)
7. **Data integration** -> sigma (compile evaluations into a single profile)

**Functors:** 7
**Coverage:** 26%
**Team:** 7 agents

**Map:**
```
[Sourcer] -> [Screener] -> [Experience_Analyzer] -> [Tech_Interviewer] -> [Culture_Checker] -> [Offer_Crafter] -> [Data_Integrator]
 tau0        delta         tau-                     lambda                rho                  tau+              sigma
```

---

### **Example B: Customer Support**

**Task:**
```
"Automate support: ticket handling + learning from errors"
```

**C4 Analysis:**

1. **Ticket intake** -> tau Present
2. **Classification** -> delta (simple/complex/escalation)
3. **Similar ticket search** -> rho (pattern matching against past tickets)
4. **Response generation** -> kappa (a concrete answer for this case)
5. **Tone adaptation** -> phi (friendly for B2C, formal for B2B)
6. **Learning** -> mu (what worked? what did not?)
7. **Knowledge base update** -> lambda o sigma (generalize the solution + add to the knowledge base)

**Functors:** 8 (7 basic + 1 composition)
**Coverage:** 30%
**Team:** 8 agents

**Map:**
```
Main flow:
 [Intake] -> [Classifier] -> [Pattern_Matcher] -> [Answer_Generator] -> [Tone_Adapter] -> [Sender]
 tau0        delta            rho                  kappa                  phi

Learning loop:
 [Feedback_Collector] -> [Knowledge_Updater]
 mu                      lambda o sigma
```

---

### **Example C: Contradiction Resolution (TRIZ case)**

**Task:**
```
"How to increase delivery speed without increasing cost?"
```

**C4 Analysis:**

1. **Problem history** -> tau Past (when did it begin? what was tried?)
2. **Current state** -> tau Present (facts: speed X, cost Y)
3. **Problem decomposition** -> delta (speed vs. cost = different axes)
4. **Inversion** -> iota (what if we do NOT ship the goods but produce on site?)
5. **Abstraction** -> lambda (the essence: not "delivery" but "availability")
6. **Synthesis** -> sigma o iota (reconciling contradictions through a new paradigm)
7. **Concretization** -> kappa (3D printing, micro-warehouses, pickup)
8. **Adaptation** -> phi (different solutions for different segments)

**Functors:** 8 (6 basic + 2 compositions: sigma o iota, lambda o sigma)
**Coverage:** 30%
**Team:** 6--7 agents (some compositions = chaining)

**Map:**
```
Analysis:
 [History] -> [Current_State] -> [Decomposer]
 tau-         tau0               delta

Innovation:
 [Invertor] -> [Abstractor] -> [Dialectician]
 iota          lambda          sigma o iota

Implementation:
 [Concretizer] -> [Adapter]
 kappa            phi
```

---

## QUICK START

### **Day 1: Minimal Integration**

**What to do:**
1. Update the Composer prompt -> `metaagent_composer_v2_c4.md`
2. Add the `c4Functor` field to 5 existing agents:
 ```javascript
 {
 address: "my_agent@domain",
 c4Functor: "tau", // <- add this
 c4Modality: "Present" // <- and this, if tau
 }
 ```
3. Test: create 1 Map, verify that `c4Coverage` is populated

**Success criterion:** Composer returns JSON with a `c4Coverage` field.

---

### **Days 2--3: Visualization**

**What to do:**
1. Create a `<C4Badge>` component for functors:
 ```jsx
 <C4Badge functor="tau" modality="Past" />
 // Renders as: [tau-] with tooltip "Temporal: Past"
 ```
2. Display the functor list for each Map in the UI:
 ```
 Functors used: [tau-] [tau0] [delta] [sigma]
 Coverage: 15% (4/27)
 ```

**Success criterion:** The user sees which functors are used.

---

### **Days 4--7: Coverage Dashboard**

**What to do:**
1. Create a "C4 Analysis" panel in the Map Editor
2. Display:
 - Coverage % (pie chart)
 - Functor list (green = covered, gray = not covered)
 - Warnings (if gaps/redundancy exist)
3. Click on a functor -> highlight the corresponding agent

**Success criterion:** The user clicks on "tau" -> the history_checker agent is highlighted.

---

## RESOURCES

**Project files:**
- `metaagent_composer_v2_c4.md` -- Composer prompt (MAIN)
- `27_functor_agents_system_prompts.md` -- description of all 27 functors
- `C4_INTEGRATION_GUIDE.md` -- technical documentation
- `HOW_IT_WORKS_GUIDE.md` -- this file (practical guide)

**Scientific foundation:**
- `../../papers/c4-deep-dive-en.md`
 - 11 formally proven theorems
 - Mathematical justification of the 27 functors

**Support:**
- GitHub Issues (if open-source project)
- Email: c4-cognitive@proton.me

---

## FAQ

### Q: Is 100% coverage always necessary?
**A:** No. Most tasks require 15--40%. 100% is needed only for AGI-level tasks.

### Q: What if Composer makes a mistake in functor selection?
**A:** You can specify explicitly: `"Use functors: tau, delta, sigma only"`. Composer will comply.

### Q: Can C4 be used without an LLM?
**A:** Yes. C4 is simply a structure. You can manually tag agents and verify coverage.

### Q: How quickly will users understand C4?
**A:** The basic concepts (tau, delta, sigma) take about 5 minutes. Full understanding of all 27 functors develops over 1--2 weeks of use.

### Q: Is knowledge of C4 mathematics required?
**A:** No. For users: "functors = cognitive operations." The mathematics operates under the hood.

---

**END OF GUIDE. YOU NOW KNOW HOW IT WORKS.**
