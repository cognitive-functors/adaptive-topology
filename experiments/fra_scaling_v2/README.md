# FRA Scaling Research — Reproducibility Package

## 🎯 Quick Start

```bash
# Clone and setup
cd /Users/figuramax/LocalProjects/adaptive-topology/experiments/fra_scaling_v2

# Install dependencies
pip install numpy scipy scikit-learn torch

# Run full experiment (< 1 minute on CPU)
python3 run_experiment.py                    # Synthetic proof-of-concept
python3 experiments/parse_aslib.py           # Parse ASlib data
python3 experiments/run_aslib_full.py        # Real ASlib validation
```

## 📊 Key Results

| Scenario | Diversity | Best Improvement | P-value |
|----------|-----------|------------------|---------|
| Synthetic | controlled | +28% | — |
| SAT11-RAND | 78% | **+44%** | |
| SAT12-ALL | 99% | **+41%** | |
| CSP-2010 | 32% | -2% (fails) | |
| **Overall** | | **+17%** | **0.0002** ✅ |

## 📁 Repository Structure

```
fra_scaling_v2/
├── README.md                 # This file
├── PLAN.md                   # Research plan
├── ULTIMATE_PLAN.md          # Detailed methodology
│
├── PAPER_EN.md               # English paper
├── PAPER_RU.md               # Russian paper
│
├── run_experiment.py         # Main synthetic experiment
├── problems/
│   ├── synthetic.py          # Controlled diversity data
│   └── aslib.py              # ASlib-like scenarios
├── fra/
│   └── router.py             # FRA Router (MLP)
│
├── experiments/
│   ├── download_aslib.py     # Download ASlib scenarios
│   ├── parse_aslib.py        # Parse ARFF format
│   └── run_aslib_full.py     # Full ASlib experiment
│
├── data/
│   └── aslib/                # Downloaded scenarios
│       ├── SAT11-RAND/
│       ├── SAT12-ALL/
│       └── CSP-2010/
│
├── results/
│   ├── synthetic/            # Synthetic results
│   └── aslib_real/           # Real ASlib results
│
└── analysis/
    └── REPORT.md             # Analysis report
```

## 🔬 Reproducing Key Findings

### Finding 1: FRA works with diversity > 50%

```bash
# Run synthetic with controlled diversity
python3 run_experiment.py

# Check: improvement > 25%, routing accuracy > 90%
cat results/synthetic/experiment_results.json | python3 -c "
import json, sys
data = json.load(sys.stdin)
print('Mean improvement:', sum(r['improvement_over_single'] for r in data)/len(data))
"
```

### Finding 2: +44% on SAT11-RAND

```bash
python3 experiments/run_aslib_full.py

# Check K=8, d=native result
cat results/aslib_real/experiment_results.json | python3 -c "
import json, sys
data = json.load(sys.stdin)
best = max([r for r in data if r['scenario']=='SAT11-RAND'],
           key=lambda x: x['improvement_over_sbs'])
print(f'Best: K={best[\"K\"]}, d={best[\"d\"]}, improvement={best[\"improvement_over_sbs\"]:.1f}%')
"
```

### Finding 3: FRA fails on low diversity (CSP-2010)

```bash
# CSP-2010 has only 32% diversity, FRA doesn't help
cat results/aslib_real/experiment_results.json | python3 -c "
import json, sys
data = json.load(sys.stdin)
csp = [r for r in data if r['scenario']=='CSP-2010']
print('CSP-2010 mean improvement:', sum(r['improvement_over_sbs'] for r in csp)/len(csp))
"
# Expected: ~-2% (no improvement)
```

## 📈 Key Insight: Refined Hypothesis

**Original hypothesis (H1.4):** K = O(1/ε^d)

**Refined hypothesis (H1.4'):**
```
K_min = n_types  (number of distinct problem "types")

performance(K) = {
    suboptimal     if K < n_types
    near-oracle    if K ≥ n_types
}
```

This is a **step function**, not a continuous scaling law.

## 🧠 Connection to C4 (Cognitive Cube)

| FRA Concept | C4 Analog |
|-------------|-----------|
| Problem instance | Input stimulus/task |
| Fingerprint | Cognitive context encoding |
| K strategies | 27 cognitive states (T×D×I) |
| Router | Attention/routing mechanism |

**Key insight:** K_min = n_types means a C4-based AI needs **at most 27 specialized modules**, not infinite scaling.

## ⚠️ When FRA Works vs Doesn't

| Condition | FRA Works? | Reason |
|-----------|------------|--------|
| Diversity > 50% | ✅ Yes | Different algorithms win on different instances |
| Diversity < 50% | ❌ No | Single Best Solver dominates |
| K ≥ n_types | ✅ Yes | All "types" have optimal strategy |
| K < n_types | ⚠️ Partial | Some types not covered |

## 🔗 Data Sources

- **ASlib:** https://github.com/coseal/aslib_data
- Scenarios used: SAT11-RAND, SAT12-ALL, CSP-2010

## 📚 Citation

```bibtex
@article{fra_scaling_2026,
  title={FRA Scaling for Algorithm Selection: Empirical Investigation},
  author={...},
  year={2026},
  note={Reproducibility package available}
}
```

## 📧 Contact

For questions about reproducibility, see PAPER_EN.md or PAPER_RU.md.
