#!/usr/bin/env python3
"""
Simplest C4 classifier example — no external dependencies.

Classifies a single text into one of 27 cognitive states
using the C4 coordinate system: (T, D, A) in {0,1,2}^3.

For production-grade classification, see: https://github.com/ilyaselyutin/c4cogl
"""

from typing import Tuple, Dict, List

# Axis labels
T_LABELS = {0: "Past", 1: "Present", 2: "Future"}
D_LABELS = {0: "Concrete", 1: "Abstract", 2: "Meta"}
I_LABELS = {0: "Self", 1: "Other", 2: "System"}

# Simple keyword matching per axis
KEYWORDS: Dict[str, Dict[int, List[str]]] = {
    "T": {
        0: ["yesterday", "last", "used to", "was", "did", "historically"],
        1: ["now", "currently", "today", "is", "am", "notice"],
        2: ["will", "tomorrow", "going to", "future", "hope to"],
    },
    "D": {
        0: ["email", "server", "meeting", "task", "code", "send"],
        1: ["pattern", "tend", "always", "usually", "trend", "habit"],
        2: ["paradigm", "metacognition", "framework", "thinking about"],
    },
    "I": {
        0: ["I ", "my ", "myself", "I'm", "I've"],
        1: ["he ", "she ", "they ", "him", "her", "their"],
        2: ["system", "organization", "society", "market", "company"],
    },
}


def classify(text: str) -> Tuple[int, int, int]:
    """Return (T, D, A) coordinate for the given text."""
    result = []
    for axis in ("T", "D", "I"):
        scores = {v: 0 for v in range(3)}
        for val, kws in KEYWORDS[axis].items():
            for kw in kws:
                if kw.lower() in text.lower():
                    scores[val] += 1
        result.append(max(scores, key=scores.get))
    return tuple(result)  # type: ignore[return-value]


if __name__ == "__main__":
    text = "I will send the report tomorrow morning"
    t, d, i = classify(text)
    state_id = t * 9 + d * 3 + i

    print(f"Text:     \"{text}\"")
    print(f"C4 coord: ({t}, {d}, {i})")
    print(f"  T = {T_LABELS[t]}")
    print(f"  D = {D_LABELS[d]}")
    print(f"  I = {I_LABELS[i]}")
    print(f"State ID: {state_id} / 26")
