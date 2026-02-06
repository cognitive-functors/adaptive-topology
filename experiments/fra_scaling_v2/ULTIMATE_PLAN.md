# 🔬 ULTIMATE RESEARCH PLAN: FRA Scaling Laws

## 🎯 MISSION
Полное научное исследование FRA (Fingerprint-Route-Adapt) паттерна для algorithm selection с публикацией результатов.

---

## PHASE 1: HYPOTHESIS REFINEMENT (Council of Geniuses)

### Исходная гипотеза (H1.4)
```
K = O(1/ε^d)
```
Количество стратегий K для достижения ε-оптимальности масштабируется как 1/ε^d.

### Наблюдения из экспериментов
- При K ≥ n_types: gap → 0 (сатурация)
- При K < n_types: gap > 0 (недостаточно)
- Это step function, НЕ power law

### Refined Hypotheses (H2.x)

**H2.1 (Threshold Hypothesis):**
```
K_critical = n_types
gap(K) ≈ 0 ⟺ K ≥ K_critical
```

**H2.2 (Diversity-Dependent Routing):**
```
improvement(FRA) > 0 ⟺ diversity(data) > threshold
```

**H2.3 (Feature Informativeness):**
```
routing_accuracy ∝ MI(features, optimal_strategy)
```
MI = mutual information

---

## PHASE 2: REAL DATA VALIDATION

### 2.1 Download Real ASlib Scenarios

```bash
# Priority scenarios (known diversity)
SAT11-RAND     # Random SAT, 5355 instances, 12 solvers
SAT11-INDU     # Industrial SAT, diverse structure
TSP-LION2015   # TSP instances, 4 algorithms
MAXSAT12-PMS   # Partial MaxSAT
```

### 2.2 Metrics to Compute

| Metric | Formula | Interpretation |
|--------|---------|----------------|
| VBS Gap | (FRA - VBS) / VBS | Gap to Virtual Best Solver |
| SBS Gap | (FRA - SBS) / SBS | Gap to Single Best Solver |
| PAR10 | penalized avg runtime | Standard ASlib metric |
| Diversity Index | H(best_solver) | Entropy of optimal solver distribution |

### 2.3 Experimental Grid

```yaml
scenarios: [SAT11-RAND, TSP-LION, MAXSAT12-PMS]
K_values: [2, 4, 8, 16, 32, all]
d_values: [4, 8, 16, 32, native]
cv_folds: 10  # Use ASlib official CV splits
```

---

## PHASE 3: STATISTICAL ANALYSIS

### 3.1 Correlation Analysis
- Spearman correlation: K vs gap
- Spearman correlation: d vs gap
- Spearman correlation: diversity vs improvement

### 3.2 Hypothesis Testing
- H0: FRA = SBS (no improvement)
- H1: FRA < SBS (FRA better)
- Test: Wilcoxon signed-rank (paired)
- Significance: α = 0.05 with Bonferroni correction

### 3.3 Model Fitting
- Step function fit for H2.1
- Logistic regression for H2.2
- Linear regression for H2.3

### 3.4 Bootstrap Confidence Intervals
- 1000 bootstrap samples
- 95% CI for all metrics

---

## PHASE 4: THEORETICAL FRAMEWORK

### 4.1 Connection to Existing Theory

| Theory | Connection |
|--------|------------|
| No Free Lunch | FRA works when NFL doesn't apply (structure exists) |
| Algorithm Selection | FRA = learned algorithm selector |
| PAC Learning | Router generalization bounds |
| Information Theory | MI(features, optimal) determines accuracy |

### 4.2 Novel Contributions

1. **Threshold Law:** K_critical = n_types (not power law)
2. **Diversity Requirement:** FRA needs diversity to work
3. **Feature-Routing Connection:** MI predicts accuracy

---

## PHASE 5: PAPER WRITING (Bilingual)

### 5.1 Structure

```
1. Abstract / Аннотация
2. Introduction / Введение
   - Algorithm Selection Problem
   - FRA Pattern
   - Our Contributions
3. Related Work / Обзор литературы
4. Methodology / Методология
   - FRA Router Architecture
   - Synthetic Experiments
   - ASlib Validation
5. Results / Результаты
   - Synthetic: Proof-of-Concept
   - ASlib: Real-World Validation
   - Statistical Analysis
6. Discussion / Обсуждение
   - Refined Hypotheses
   - Limitations
   - When FRA Works vs Doesn't
7. Conclusion / Заключение
8. Reproducibility / Воспроизводимость
```

### 5.2 Key Figures

1. **Fig 1:** FRA Architecture diagram
2. **Fig 2:** K vs Gap (synthetic) — step function
3. **Fig 3:** Diversity vs Improvement scatter
4. **Fig 4:** Routing accuracy heatmap (K × d)
5. **Fig 5:** ASlib results comparison

### 5.3 Tables

1. **Table 1:** Synthetic experiment results
2. **Table 2:** ASlib scenario results
3. **Table 3:** Statistical tests (p-values)
4. **Table 4:** Comparison with baselines

---

## PHASE 6: REPRODUCIBILITY PACKAGE

### 6.1 Repository Structure

```
fra-scaling-research/
├── README.md                    # Quick start
├── PAPER_EN.md                  # English paper
├── PAPER_RU.md                  # Russian paper
├── requirements.txt             # Dependencies
├── setup.py                     # Package installation
├── data/
│   ├── synthetic/               # Generated data
│   └── aslib/                   # Downloaded scenarios
├── src/
│   ├── problems/                # Problem definitions
│   ├── fra/                     # FRA router
│   └── analysis/                # Statistical tools
├── experiments/
│   ├── run_synthetic.py         # Phase 1
│   ├── run_aslib.py             # Phase 2
│   └── run_analysis.py          # Phase 3
├── results/                     # All JSON results
├── figures/                     # Generated plots
└── notebooks/
    └── analysis.ipynb           # Interactive exploration
```

### 6.2 One-Command Reproduction

```bash
# Full experiment reproduction
git clone https://github.com/user/fra-scaling-research
cd fra-scaling-research
pip install -e .
python -m experiments.run_all --full

# Quick validation (synthetic only)
python -m experiments.run_all --quick
```

---

## EXECUTION TIMELINE

| Phase | Tasks | Est. Time |
|-------|-------|-----------|
| 1 | Hypothesis refinement | 5 min |
| 2 | Download ASlib + run experiments | 15 min |
| 3 | Statistical analysis | 10 min |
| 4 | Theoretical framework | 10 min |
| 5 | Write papers (EN + RU) | 30 min |
| 6 | Reproducibility package | 10 min |
| **Total** | | **~80 min** |

---

## SUCCESS CRITERIA

### Minimum Success
- [ ] H2.1 confirmed on synthetic
- [ ] At least 1 ASlib scenario shows improvement
- [ ] Papers written (both languages)
- [ ] Code reproducible

### Full Success
- [ ] H2.1-H2.3 confirmed on real data
- [ ] Statistical significance (p < 0.05)
- [ ] Clear guidelines: when FRA works
- [ ] Ready for arxiv submission

### Legendary Success
- [ ] Novel theoretical insight discovered
- [ ] Applicable to other domains
- [ ] Community can build on results

---

## 🚀 LET'S GO LEGENDARY!
