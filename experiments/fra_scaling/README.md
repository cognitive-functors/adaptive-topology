# FRA Scaling Hypothesis (1.4) Experiment

**Testing:** For any NP-hard problem and gap ε > 0, there exist fingerprint dimension d and number of strategies K such that FRA achieves gap < ε on (1−δ) fraction of instances, with K = O(1/ε^d) and d = O(log(1/δ)).

## Quick Start

### Local Test (Mac)

```bash
cd experiments/fra_scaling

# Install dependencies
pip install -r requirements.txt

# Run small-scale test
python run_experiment.py --local --instances 30 --problem tsp
```

### Full Experiment (vast.ai)

```bash
# Configure vast.ai
pip install vastai
vastai set api-key YOUR_KEY

# Deploy and run (fully automated)
python vast_launcher.py --deploy

# Monitor progress
python vast_launcher.py --status

# Download results when done
python vast_launcher.py --download

# Cleanup (important!)
python vast_launcher.py --destroy
```

## Experiment Design

### Problems Tested

| Problem | Instances | Strategies | Source |
|---------|-----------|------------|--------|
| TSP | 127 | 15 | TSPLIB |
| SAT | 300 | 12 | Random 3-SAT |
| MaxCut | 67 | 10 | Random graphs |

### Experimental Grid

**Vary K (at fixed d=16):**
- K ∈ {2, 4, 6, 8, 10, 12, 15}

**Vary d (at fixed K=10):**
- d ∈ {4, 8, 16, 32, 64}

### Success Criteria

Hypothesis is **CONFIRMED** if:
1. FRA beats best single strategy on >50% of configs (p < 0.01)
2. Spearman correlation (K vs gap) < -0.7 (negative = gap decreases with K)
3. Power law fit R² > 0.7

## Files

```
fra_scaling/
├── config.yaml           # Experiment configuration
├── requirements.txt      # Python dependencies
├── run_experiment.py     # Main experiment runner
├── vast_launcher.py      # Vast.ai auto-deployment
├── problems/
│   ├── base.py           # Abstract problem class
│   ├── tsp.py            # TSP implementation (15 strategies)
│   ├── sat.py            # SAT implementation (12 solvers)
│   └── maxcut.py         # MaxCut implementation (10 strategies)
├── fra/
│   └── router.py         # FRA router (MLP-based)
├── results/              # Output (created after run)
└── figures/              # Plots (created after analysis)
```

## Expected Results

Based on preliminary analysis:

- **TSP:** FRA expected to show clear K-scaling (we have MASTm as strong baseline)
- **SAT:** Mixed results expected (solver portfolio effect well-studied)
- **MaxCut:** FRA should outperform single heuristics

## Cost Estimate

**vast.ai (3x RTX 3090 @ $0.25/hr):**
- Runtime: ~2 hours
- Total: ~$1.50 - $3.00

**Budget buffer:** $25 available, using ~$3-5

## Author

Ilya Selyutin (psy.seliger@yandex.ru)

## Related

- Hypothesis 1.4 in `papers/FUTURE-RESEARCH-DIRECTIONS.md`
- MASTm TSP solver in `code/mast/`
- C4/FRA theory in `papers/algorithmic-topology/`
