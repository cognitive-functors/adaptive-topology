#!/usr/bin/env python3
"""
C4 Cognitive Classifier — Demo (Rule-Based)

Classifies text into one of 27 cognitive states using the C4 coordinate system:
  T (Time):   Past=0, Present=1, Future=2
  D (Scale):  Concrete=0, Abstract=1, Meta=2
  I (Agency): Self=0, Other=1, System=2

This is a simplified keyword-matching demo. For production-grade classification
using DeBERTa, see: https://github.com/ilyaselyutin/c4cogl

Usage:
    python3 c4_classifier_demo.py
    python3 c4_classifier_demo.py --config path/to/c4_states.yaml
"""

import os
import sys
import argparse
from typing import Tuple, Dict, List, Optional

# Try to load YAML config; fall back to built-in keywords if unavailable
try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False
    print("Warning: pyyaml not installed, using built-in keywords only.")


# ─── Keyword dictionaries for each axis ────────────────────────────────────

TIME_KEYWORDS: Dict[int, List[str]] = {
    0: ["yesterday", "last week", "last month", "last year", "used to",
        "back then", "in the past", "previously", "I did", "he did",
        "historically", "was changed", "crashed in"],
    1: ["right now", "currently", "at this moment", "today", "I am",
        "is doing", "is down", "I notice", "is stuck", "I'm thinking"],
    2: ["tomorrow", "next week", "will", "going to", "I hope to",
        "aspire", "will transform", "will become", "future of",
        "paradigm shift"],
}

SCALE_KEYWORDS: Dict[int, List[str]] = {
    0: ["specific", "email", "meeting", "server", "line 47", "call",
        "product", "task", "deploy", "send", "launch", "pipeline"],
    1: ["pattern", "tend to", "usually", "always", "habit", "trend",
        "cycle", "feedback loop", "dynamics", "culture"],
    2: ["paradigm", "mental model", "metacognition", "thinking about thinking",
        "framework", "ways of knowing", "epistemology", "mindset",
        "theory of mind", "collective cognition"],
}

AGENCY_KEYWORDS: Dict[int, List[str]] = {
    0: ["I ", "I'm", "my ", "myself", "me ", "I've", "I'll"],
    1: ["he ", "she ", "they ", "him", "her", "them", "his ", "their"],
    2: ["the system", "the organization", "the market", "society",
        "the field", "the company", "humanity", "science", "policy"],
}


def score_axis(text: str, keywords: Dict[int, List[str]]) -> int:
    """Score text against keyword lists, return axis value with highest match count."""
    text_lower = text.lower()
    scores = {v: 0 for v in keywords}
    for value, kws in keywords.items():
        for kw in kws:
            if kw.lower() in text_lower:
                scores[value] += 1
    # Default to 1 (Present/Concrete/Self) if no matches
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else 1


def classify(text: str) -> Tuple[int, int, int]:
    """Classify text into C4 coordinates (T, D, A)."""
    t = score_axis(text, TIME_KEYWORDS)
    d = score_axis(text, SCALE_KEYWORDS)
    i = score_axis(text, AGENCY_KEYWORDS)
    return (t, d, i)


def state_id(t: int, d: int, i: int) -> int:
    """Convert (T, D, A) to linear state index 0..26."""
    return t * 9 + d * 3 + i


def load_state_names(config_path: str) -> Dict[int, str]:
    """Load state names from c4_states.yaml if available."""
    if not HAS_YAML or not os.path.exists(config_path):
        return {}
    with open(config_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return {s["id"]: s["name"] for s in data.get("states", [])}


AXIS_LABELS = {
    "T": {0: "Past", 1: "Present", 2: "Future"},
    "D": {0: "Concrete", 1: "Abstract", 2: "Meta"},
    "I": {0: "Self", 1: "Other", 2: "System"},
}


def format_result(text: str, coords: Tuple[int, int, int],
                  names: Dict[int, str]) -> str:
    """Format classification result for display."""
    t, d, i = coords
    sid = state_id(t, d, i)
    label = names.get(sid, f"State #{sid}")
    return (
        f"  Text:  \"{text[:70]}{'...' if len(text) > 70 else ''}\"\n"
        f"  C4:    ({t}, {d}, {i})  =  "
        f"T:{AXIS_LABELS['T'][t]}, D:{AXIS_LABELS['D'][d]}, I:{AXIS_LABELS['I'][i]}\n"
        f"  State: {label} (id={sid})\n"
    )


# ─── Sample texts for demonstration ────────────────────────────────────────

SAMPLE_TEXTS = [
    "I made a mistake in yesterday's meeting",
    "The server is down and we need to fix it right now",
    "AI will transform the job market in the next decade",
    "I notice I'm avoiding this difficult task",
    "She tends to be late to every standup",
    "I used to believe my thoughts were facts",
    "The organization is stuck in bureaucracy",
    "I will send the report tomorrow morning",
    "Humanity will need to develop planetary-scale thinking",
    "He always makes excuses when deadlines approach",
]


def main() -> None:
    parser = argparse.ArgumentParser(description="C4 Cognitive Classifier Demo")
    parser.add_argument(
        "--config",
        default=os.path.join(
            os.path.dirname(__file__),
            "c4-fracture-analyzer", "configs", "c4_states.yaml"
        ),
        help="Path to c4_states.yaml config",
    )
    args = parser.parse_args()

    names = load_state_names(args.config)

    print("=" * 70)
    print("  C4 Cognitive Classifier — Rule-Based Demo")
    print("  Note: production classifier uses DeBERTa (see c4cogl)")
    print("=" * 70)

    for text in SAMPLE_TEXTS:
        coords = classify(text)
        print(format_result(text, coords, names))

    print("-" * 70)
    print("  Axes:  T=Time(Past/Present/Future)  D=Scale(Concrete/Abstract/Meta)")
    print("         I=Agency(Self/Other/System)   Total states: 27 = 3^3")
    print("=" * 70)


if __name__ == "__main__":
    main()
