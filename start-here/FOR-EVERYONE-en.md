# Why This Matters to You: C4 in Plain Language

> *Imagine someone drew a map of how your mind works. Not a metaphorical one, but a real map — with coordinates, distances, and routes. And this map turned out to be the same for everyone.*

---

## Why Should You Read This?

You're not a scientist. Maybe you've never heard of "groups" in mathematics and have no plans to learn about "functors." That's fine — you don't need to.

But this page is about things that affect you directly:
- Why you sometimes can't explain your thoughts to someone else
- Why some decisions come easily while others get stuck
- Why AI sometimes understands you better than people do, and sometimes worse
- Why "sleeping on a problem" actually helps

We (the authors of this repository) spent years creating a **mathematical model of thinking**. Sounds dry? Wait. The result turned out to be surprising: any person's thinking can be described as **navigation through a map of 27 points**.

And we proved it. Literally — with formulas, computer verification, and experiments.

---

## The Main Idea: Thinking Is a Journey

When you think, you're not just "processing information" like a computer. You're **moving** between different states of consciousness.

Think about it:
- In the morning, you think about what you'll do today (planning)
- In the evening — about what happened (analyzing the past)
- Sometimes you think about yourself ("how do I feel?")
- Sometimes — about others ("what did they mean?")
- Sometimes — about concrete things ("where are my keys?")
- Sometimes — about abstract ones ("what's the meaning of life?")

Every time you switch between these modes — you're **taking a step on the map of thinking**.

We called this map **C4** (Complete Cognitive Coordinate System).

---

## Three Dimensions of Your Thinking

Imagine your thinking as a room. You can move in three directions:

### 1. Time (forward-backward)

- **Past**: memories, analysis of what happened
- **Present**: what's happening right now, sensations
- **Future**: plans, dreams, predictions, fears

*Example*: You recall yesterday's conversation (past) → notice you're angry right now (present) → decide what you'll say tomorrow (future). Three steps along the time axis.

### 2. Scale (up-down)

- **Concrete**: facts, details, "what exactly"
- **Abstract**: ideas, concepts, "in general"
- **Meta**: thinking about thinking itself, "how am I thinking about this"

*Example*: You look at an apple (concrete) → think about healthy eating (abstract) → notice you're constantly thinking about food and ask yourself "why?" (meta). Three levels of scale.

### 3. Agency (me-you-system)

- **Self**: your personal experiences, thoughts, feelings
- **Other**: thoughts about a specific person, their state
- **System**: rules, norms, "how the world works"

*Example*: You feel hurt (self) → think "they didn't mean to offend me" (other) → understand "in our culture, that's not acceptable" (system). Three positions of perception.

---

## 27 States: The Complete Map

Three axes, each with three values: 3 × 3 × 3 = **27 states**.

This isn't a random number. It's the **minimally complete** set of cognitive states. Any thought you've ever had exists at one of these 27 points.

Some examples:

| State | Time | Scale | Agency | Example Thought |
|-------|------|-------|--------|-----------------|
| (0,0,0) | Past | Concrete | Self | "I forgot my keys yesterday" |
| (1,1,1) | Present | Abstract | Other | "They seem to be thinking about something important right now" |
| (2,2,2) | Future | Meta | System | "How will society reflect on its mistakes?" |
| (0,2,0) | Past | Meta | Self | "Why did I think that way back then?" |
| (2,0,1) | Future | Concrete | Other | "She'll buy that bag tomorrow" |

Try it yourself: think any thought and identify its coordinates. It works.

---

## What We Proved (and Why It Matters)

### 11 Theorems — The Mathematical Foundation

We didn't just come up with a nice metaphor. We **formally proved** 11 theorems about how this system works. 10 of them are computer-verified (in the Agda proof system — meaning errors are ruled out).

Here's what's proven:

1. **Completeness**: 27 states are *all* possible basic thinking states. Nothing is missing.

2. **Reachability**: From any state, you can reach any other in at most 6 steps. You never get "stuck" in one thinking mode forever.

3. **Distance**: There's an objective "distance" between states. The farther apart — the harder it is to switch.

4. **Adaptivity**: If you can recognize your current state and choose a strategy for it — you'll think more effectively than with any "universal" strategy.

### Hypothesis ID-3 — Experimental Confirmation

Now for the most interesting part. We tested: **does human thinking really fit into 3 dimensions?**

We took thousands of texts, labeled them by 27 states, and used neural networks to find the "intrinsic dimensionality" — how many independent axes are actually needed to describe the differences between texts.

**Result: 3.07** (with confidence interval 2.91–3.15).

Not 2. Not 5. Not 10. Exactly 3. Just as we predicted.

This was confirmed:
- Across 3 different neural networks
- In 2 languages (Russian and English)
- On different datasets
- Using different mathematical methods

Thinking really is three-dimensional.

---

## What This Means for You

### 1. You Can "See" Your Thinking

When you know about the 27 states, you start noticing where you are:
- "Ah, I'm stuck in the past on concrete details. Maybe I should zoom out?"
- "I'm only thinking about the system — what does this specific person feel?"
- "All focus on myself — how does this look from the outside?"

This isn't mysticism. It's navigation.

### 2. You Can Understand Why Others Don't Understand You

When you talk to someone, you might be in **different states**. You're focused on the future and abstract, they're in the past and concrete. You're literally on different parts of the map.

Solution: recognize the difference and either "go to them" or "bring them to you." This requires taking steps along the axes.

### 3. You Can Improve Your Thinking

There are two ways to think better:
1. **Improve navigation** — switch between states faster
2. **Improve selection** — understand which state is needed for which task

Creative task? You need "long jumps" — between opposite states.
Analytical task? You need "short steps" — sequentially through neighboring points.

### 4. You Can Communicate Better with AI

AI systems (like ChatGPT, Claude) are essentially machines for generating text in specific cognitive states. When you understand the coordinate system, you can formulate requests more precisely:

- Want a concrete plan? Ask for (2,0,0) — future, concrete, self.
- Want to understand someone else's perspective? Ask for (1,1,1) — present, abstract, other.
- Want systems analysis? Ask for (0,2,2) — past, meta, system.

---

## The Big Picture

### For Cognitive Science

We proposed a **unified coordinate system** for describing thinking. Before us, there were dozens of competing theories — now there's a chance to unite them in a common framework.

### For AI

If thinking is three-dimensional, then AI systems can be designed with this structure in mind. Not just "more parameters," but the **right architecture** that reflects how intelligence actually works.

We've already demonstrated this with the traveling salesman problem (finding the optimal route) — our MASTm algorithm, built on C4 principles, outperforms many classical methods.

### For Understanding Intelligence

What is intelligence? It's not "lots of knowledge" or "fast computation." It's the **ability to adaptively navigate through the space of possible states**, choosing the right state for each task.

Stupidity is getting stuck in one state.
Wisdom is freedom of movement across the entire map.

### For Humanity

We live in a world where people understand each other less and less. Political arguments, culture wars, generational misunderstandings — all of this is partly because people **get stuck in different parts of the cognitive map** and can't (or won't) move toward their conversation partner.

C4 provides language for describing these differences. Not "you're wrong," but "you're looking from point (0,0,0) and I'm at (2,2,2) — let's find a path to each other."

---

## Honest Limitations

We're scientists, so we must say:

1. **This is a model, not truth**. C4 is a way of describing thinking, not a claim about how the brain physically works.

2. **The time axis is problematic**. Neural networks currently struggle to distinguish texts along the time axis. This is an open question — either the axis is "weaker" or different measurement methods are needed.

3. **Data is labeled by AI**. Our experiments use texts labeled by neural networks. Studies with human annotation are needed.

4. **Practical applications are ahead**. We proved the theory, but tools for everyday use are yet to be created.

---

## What's Next?

If you're interested:

1. **Play with the classifier**: [c4cognitive.com](https://c4cognitive.com) — enter any text and see its coordinates.

2. **Read the popular introduction**: [start-here/popular-intro-en.md](popular-intro-en.md) — slightly more technical, but still accessible.

3. **See the visualization**: [visualizations/](../visualizations/) — interactive 3D hypercube.

4. **Go deeper**: [guides/](../guides/) — guides for different audiences (programmers, psychologists, philosophers).

---

## The Main Takeaway

**Your thinking is not chaos. It's navigation through a map of 27 states.**

Now you have this map.

---

*Author: Ilya Selyutin*
*Repository: [github.com/cognitive-functors/adaptive-topology](https://github.com/cognitive-functors/adaptive-topology)*

---

> *"The map is not the territory. But with a map, you can see the territory differently."*
> — Alfred Korzybski (paraphrased)
