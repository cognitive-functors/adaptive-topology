# Contributing to Adaptive Topology

Thank you for your interest in contributing to the Adaptive Topology project. This guide explains how to get involved, what kinds of contributions we welcome, and how the review process works.

**Authors:** Ilya Selyutin, Nikolai Kovalev
**Contact:** [comonoid@yandex.ru](mailto:comonoid@yandex.ru)

---

## Table of Contents

- [Welcome Contributions](#welcome-contributions)
- [Repository Structure Guidelines](#repository-structure-guidelines)
- [Getting Started](#getting-started)
- [Workflow](#workflow)
- [Code Standards](#code-standards)
- [Adding a New TSPLIB Benchmark to MASTm](#adding-a-new-tsplib-benchmark-to-mastm)
- [Adding a New Experiment](#adding-a-new-experiment)
- [Proposing a New Audience Guide](#proposing-a-new-audience-guide)
- [Review Process](#review-process)
- [Language Policy](#language-policy)
- [Code of Conduct](#code-of-conduct)

---

## Welcome Contributions

We welcome contributions in the following areas:

- **Bug reports** — If you find an error in the code, formal proofs, or documentation, please open an issue with a clear description and steps to reproduce.
- **New benchmarks for MASTm** — Adding TSPLIB instances or other combinatorial optimization benchmarks to evaluate MASTm performance.
- **Translations** — Translating audience guides, documentation, or the preprint into additional languages.
- **Theoretical extensions** — Proposing new theorems, conjectures, or formal proof extensions within the adaptive topology framework.
- **Documentation improvements** — Clarifying existing guides, fixing typos, improving examples, or adding diagrams.
- **Code improvements** — Performance optimizations, better test coverage, refactoring, or new utilities.

---

## Repository Structure Guidelines

This section defines the canonical structure for organizing files in the repository.

### Directory Layout

```
adaptive-topology/
├── papers/                    # All research papers and theoretical documents
│   ├── fractal-c4/           # Core C4 theory papers
│   ├── formal-mathematics/    # Category theory, type systems, Agda formalization
│   ├── algorithmic-topology/  # MASTm, TSP, optimization algorithms
│   └── *.md                  # Individual papers (ID3, FRA, etc.)
├── experiments/               # All experimental work
│   ├── fra-scaling/          # FRA routing experiments on ASlib
│   ├── id3/                  # Intrinsic dimensionality experiments
│   └── <experiment-name>/    # Future experiments
├── code/                      # Production-ready implementations
│   ├── mast/                 # MASTm TSP solver
│   ├── c4-classifier/        # C4 cognitive classifier demo
│   └── agda/                 # Formal proofs
├── guides/                    # Audience-specific entry points
├── start-here/               # Plain-language introductions
├── applications/             # Application examples (functor-agents)
├── visualizations/           # Interactive demos (3D hypercube)
├── formal-proofs/            # Agda verification guides
├── thinking/                 # Work-in-progress theoretical notes
└── about/                    # Meta-documentation (WHY-C4, TOPICS, llms.txt)
```

### File Naming Conventions

**Bilingual Files:**
- English version: `filename.md` or `filename-en.md`
- Russian version: `filename-ru.md` (ALWAYS use `-ru` suffix for Russian)
- Example: `FOR-EVERYONE-en.md` / `FOR-EVERYONE-ru.md`

**Papers:**
- Use descriptive names: `fra-scaling-en.md`, `ID3-INTRINSIC-DIMENSIONALITY-ru.md`
- Numbered series: `01_c4-fractal-en.md`, `02_c4-knowledge-ru.md`

**Experiments:**
- Each experiment gets its own subdirectory in `experiments/`
- Include: `README.md`, code files, `results/` subdirectory
- Keep raw data and analysis scripts together

### What Goes Where

| Content Type | Location | Notes |
|-------------|----------|-------|
| Research papers | `papers/` | Finalized theory and results |
| Experimental code | `experiments/<name>/` | Hypothesis testing, benchmarks |
| Production code | `code/<project>/` | Reusable implementations |
| Entry points | `guides/` or `start-here/` | Audience-oriented docs |
| Work-in-progress | `thinking/` | Theoretical explorations |
| Meta-info | `about/` | llms.txt, TOPICS, WHY-C4 |

### Internal vs. External Files

**Keep in repo:**
- Papers, code, results, documentation
- Benchmark data referenced in papers
- Visualization assets

**Do NOT commit:**
- Planning files (PLAN.md, ULTIMATE_PLAN.md)
- Personal notes and drafts
- API keys, credentials
- Large binary files (use Git LFS if needed)

---

## Getting Started

1. Read the [README.md](README.md) for an overview of the project.
2. Explore the `guides/` directory for audience-specific introductions.
3. Review the `formal-proofs/` directory if you plan to contribute Agda proofs.
4. Check existing [issues](../../issues) to see if your idea is already being discussed.

---

## Workflow

We follow a standard fork-and-pull-request workflow:

1. **Fork** the repository to your own GitHub account.
2. **Clone** your fork locally:
   ```bash
   git clone https://github.com/<your-username>/adaptive-topology.git
   cd adaptive-topology
   ```
3. **Create a branch** for your contribution:
   ```bash
   git checkout -b feature/your-descriptive-branch-name
   ```
4. **Make your changes**, committing with clear, concise messages.
5. **Push** your branch to your fork:
   ```bash
   git push origin feature/your-descriptive-branch-name
   ```
6. **Open a Pull Request** against the `main` branch of the upstream repository. In the PR description, explain:
   - What the change does
   - Why it is needed
   - How it was tested or verified

---

## Code Standards

### Python (`code/c4-classifier/`, `experiments/*/`)

- Follow **PEP 8** style conventions.
- Use **type hints** for all function signatures.
- Write docstrings for public functions and classes.
- Include unit tests for new functionality in the appropriate test directory.
- Use `python3` (3.10+) as the target runtime.

Example:

```python
def compute_metric(
    adjacency: list[list[float]],
    threshold: float = 0.5,
) -> float:
    """Compute the adaptive topology metric for a given adjacency matrix."""
    ...
```

### Agda (`formal-proofs/`)

- Follow the existing conventions in `formal-proofs/` (module structure, naming, indentation).
- Ensure all proofs type-check with the Agda version specified in the project.
- Add comments explaining the mathematical intuition behind non-trivial proof steps.
- If you introduce new axioms or postulates, document them explicitly and justify their use.

### General

- Keep commits atomic: one logical change per commit.
- Do not include generated files, editor configs, or OS-specific files.
- Ensure your changes do not break existing tests or proofs.

---

## Adding a New TSPLIB Benchmark to MASTm

To add a new TSPLIB instance for MASTm evaluation:

1. **Obtain the instance** from the [TSPLIB repository](http://comopt.ifi.uni-heidelberg.de/software/TSPLIB95/) or an equivalent source.
2. **Place the instance file** (`.tsp` format) in the appropriate benchmarks directory under `code/mast/`.
3. **Create a configuration entry** specifying:
   - Instance name and source
   - Known optimal tour length (if available)
   - Any instance-specific parameters
4. **Run the MASTm solver** on the new instance and record the results.
5. **Update the results table** in the relevant documentation or README, including:
   - Solution quality (gap from optimum)
   - Computation time
   - Number of iterations / topological transitions
6. **Add a brief description** of the instance characteristics (number of cities, geometry type, difficulty class).
7. Submit a PR following the standard [workflow](#workflow).

---

## Adding a New Experiment

To add a new hypothesis validation experiment:

1. **Create a subdirectory** in `experiments/` with a descriptive name:
   ```bash
   experiments/your-experiment-name/
   ```

2. **Structure your experiment directory:**
   ```
   experiments/your-experiment-name/
   ├── README.md           # Experiment description, hypothesis, methodology
   ├── run_experiment.py   # Main execution script
   ├── analysis.py         # Analysis and visualization code
   ├── requirements.txt    # Python dependencies (if any)
   ├── data/               # Input data (or links to external sources)
   └── results/            # Output files, charts, tables
   ```

3. **Write a clear README.md** with:
   - Hypothesis being tested
   - Methodology description
   - How to reproduce results
   - Key findings summary

4. **Write the research paper** in `papers/`:
   - `papers/your-experiment-name-en.md` (English)
   - `papers/your-experiment-name-ru.md` (Russian, optional)

5. **Update references** in main README.md if the experiment produces key results.

6. Submit a PR following the standard [workflow](#workflow).

---

## Proposing a New Audience Guide

The `guides/` directory contains introductions tailored for specific audiences (AI researchers, linguists, psychologists, philosophers, etc.). To propose a new audience guide:

1. **Open an issue** describing:
   - The target audience (e.g., "for-category-theorists", "for-educators")
   - Why this audience would benefit from a dedicated guide
   - A brief outline of the proposed content
2. **Wait for feedback** from maintainers before writing the full guide.
3. **Write the guide** following the existing naming convention:
   - `guides/for-<audience>.md` (English version)
   - `guides/for-<audience>-ru.md` (Russian version, if applicable)
4. Follow the structure and tone of existing guides for consistency.
5. Submit a PR following the standard [workflow](#workflow).

---

## Review Process

1. All contributions go through **pull request review** by at least one maintainer.
2. Reviewers will check for:
   - Correctness (mathematical, logical, and computational)
   - Adherence to code standards
   - Consistency with project conventions
   - Adequate documentation and test coverage
3. You may be asked to make revisions. Please respond to review comments in a timely manner.
4. Once approved, a maintainer will merge your PR.
5. For theoretical contributions or formal proof extensions, review may take longer due to the need for careful mathematical verification.

---

## Language Policy

- **English** is the primary language for code, commit messages, and documentation.
- **Bilingual contributions are welcome.** If you write a guide or document in another language, please also provide an English version (or vice versa). Russian translations are especially appreciated.
- Code comments should be in English.
- Issue discussions may be in English or Russian.

---

## Code of Conduct

This project follows the [Contributor Covenant Code of Conduct](CODE_OF_CONDUCT.md). By participating, you agree to uphold a respectful and inclusive environment.

---

## Questions?

If you have questions about contributing, feel free to reach out at [comonoid@yandex.ru](mailto:comonoid@yandex.ru) or open a discussion issue.

Thank you for helping advance adaptive topology research.
