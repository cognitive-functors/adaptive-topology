# Code

Executable code accompanying the articles: formal proofs and demonstration scripts.

---

## Structure

### `agda/` -- Agda Proofs

Mechanized proofs in Agda for the core type system, functor constructions, and key theorems described in the papers.

### `python/examples/` -- Python Demo Scripts

Example scripts demonstrating C4 classification, functor composition, and other concepts from the articles. These are intended for illustration, not production use.

### `mast/` -- MASTm TSP Solver

Run-ready implementation of the MASTm (Multi-scale Adaptive Spectral TSP meta-solver) for the Travelling Salesman Problem. Approximately 6K lines of Python, with 12 bundled TSPLIB instances and benchmark results. See `mast/README.md` for usage instructions.

### `python/requirements.txt`

Python dependencies for running the demo scripts. Install with:

```bash
pip install -r code/python/requirements.txt
```

---

## Pretrained Models & Live Demo

- **Live demo:** [c4cognitive.com](https://c4cognitive.com) -- interactive C4 classifier in the browser
- **Pretrained adapters:** [HuggingFace Hub](https://huggingface.co/HangJang/c4-cognitive-adapters) -- 12 LoRA adapters (65 classification heads) for mDeBERTa-v3-base, available in PyTorch and ONNX formats
