#!/usr/bin/env python3
"""
Batch text analysis using the C4 cognitive coordinate system.

Reads texts from stdin (one per line) or uses built-in samples,
classifies each into a (T, D, A) state, and prints distribution statistics.

Usage:
    python3 analyze_text_batch.py
    cat texts.txt | python3 analyze_text_batch.py

For production-grade classification, see: https://github.com/ilyaselyutin/c4cogl
"""

import sys
from collections import Counter
from typing import List, Tuple, Dict

T_LABELS = {0: "Past", 1: "Present", 2: "Future"}
D_LABELS = {0: "Concrete", 1: "Abstract", 2: "Meta"}
I_LABELS = {0: "Self", 1: "Other", 2: "System"}

KEYWORDS: Dict[str, Dict[int, List[str]]] = {
    "T": {
        0: ["yesterday", "last", "used to", "was", "did", "historically"],
        1: ["now", "currently", "today", "is", "am", "notice", "right now"],
        2: ["will", "tomorrow", "going to", "future", "hope to", "aspire"],
    },
    "D": {
        0: ["email", "server", "meeting", "task", "code", "send", "deploy"],
        1: ["pattern", "tend", "always", "usually", "trend", "habit", "cycle"],
        2: ["paradigm", "metacognition", "framework", "thinking about", "mindset"],
    },
    "I": {
        0: ["I ", "my ", "myself", "I'm", "I've", "I'll"],
        1: ["he ", "she ", "they ", "him", "her", "their"],
        2: ["system", "organization", "society", "market", "humanity"],
    },
}

SAMPLE_TEXTS = [
    "I made a mistake in yesterday's meeting",
    "The server is down right now",
    "AI will transform the job market",
    "I notice I tend to avoid conflict",
    "She always arrives late to standups",
    "I used to believe my thoughts were facts",
    "The organization is stuck in bureaucracy",
    "I will finish the deploy tomorrow",
    "They never listen to feedback",
    "Humanity will need planetary-scale thinking",
    "I'm working on the pipeline right now",
    "The market crashed in 2008",
]


def classify(text: str) -> Tuple[int, int, int]:
    """Return (T, D, A) coordinate for a text using keyword matching."""
    result = []
    for axis in ("T", "D", "I"):
        scores = {v: 0 for v in range(3)}
        for val, kws in KEYWORDS[axis].items():
            for kw in kws:
                if kw.lower() in text.lower():
                    scores[val] += 1
        result.append(max(scores, key=scores.get))
    return tuple(result)  # type: ignore[return-value]


def print_bar(label: str, count: int, total: int, width: int = 30) -> str:
    """Render a simple text bar chart line."""
    pct = count / total if total > 0 else 0
    bar = "#" * int(pct * width)
    return f"  {label:<10s} {bar:<{width}s} {count:>3d} ({pct:5.1%})"


def main() -> None:
    # Read from stdin if piped, otherwise use samples
    if not sys.stdin.isatty():
        texts = [line.strip() for line in sys.stdin if line.strip()]
    else:
        texts = SAMPLE_TEXTS

    print(f"Analyzing {len(texts)} texts...\n")

    # Classify all texts
    results: List[Tuple[int, int, int]] = []
    for text in texts:
        coords = classify(text)
        results.append(coords)
        sid = coords[0] * 9 + coords[1] * 3 + coords[2]
        print(f"  [{sid:2d}] ({coords[0]},{coords[1]},{coords[2]})  {text[:60]}")

    # Distribution per axis
    t_counts = Counter(r[0] for r in results)
    d_counts = Counter(r[1] for r in results)
    i_counts = Counter(r[2] for r in results)
    total = len(results)

    print(f"\n{'='*50}")
    print(f"  DISTRIBUTION SUMMARY ({total} texts)")
    print(f"{'='*50}")

    print("\n  Time (T):")
    for v in range(3):
        print(print_bar(T_LABELS[v], t_counts.get(v, 0), total))

    print("\n  Scale (D):")
    for v in range(3):
        print(print_bar(D_LABELS[v], d_counts.get(v, 0), total))

    print("\n  Agency (A):")
    for v in range(3):
        print(print_bar(I_LABELS[v], i_counts.get(v, 0), total))

    # Most and least populated states
    state_counts = Counter(r[0] * 9 + r[1] * 3 + r[2] for r in results)
    covered = len(state_counts)
    print(f"\n  States covered:  {covered} / 27 ({covered/27:.0%})")
    if state_counts:
        top_id, top_n = state_counts.most_common(1)[0]
        t, d, i = top_id // 9, (top_id % 9) // 3, top_id % 3
        print(f"  Most common:     #{top_id} ({T_LABELS[t]},{D_LABELS[d]},{I_LABELS[i]}) x{top_n}")
    print()


if __name__ == "__main__":
    main()
