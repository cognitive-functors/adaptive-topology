#!/usr/bin/env python3
"""
3D visualization of the 27 C4 cognitive states.

Plots all states as points in a 3D cube where:
  X = Time    (Past=0, Present=1, Future=2)
  Y = Scale   (Concrete=0, Abstract=1, Meta=2)
  Z = Agency  (Self=0, Other=1, System=2)

Points are colored by the Time axis (T).

Requirements: matplotlib, numpy
Usage: python3 visualize_27_states.py
"""

import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D  # noqa: F401 — needed for 3D projection

# Axis definitions
T_LABELS = ["Past", "Present", "Future"]
D_LABELS = ["Concrete", "Abstract", "Meta"]
I_LABELS = ["Self", "Other", "System"]

# Color map: one color per Time value
T_COLORS = {0: "#4A90D9", 1: "#50C878", 2: "#E8553D"}
T_COLOR_NAMES = {0: "Past (blue)", 1: "Present (green)", 2: "Future (red)"}


def generate_states():
    """Generate all 27 state coordinates and labels."""
    coords = []
    labels = []
    colors = []
    for t in range(3):
        for d in range(3):
            for i in range(3):
                coords.append((t, d, i))
                state_id = t * 9 + d * 3 + i
                label = f"{state_id}: {T_LABELS[t][:3]},{D_LABELS[d][:3]},{I_LABELS[i][:3]}"
                labels.append(label)
                colors.append(T_COLORS[t])
    return np.array(coords), labels, colors


def plot_states():
    """Create and display the 3D scatter plot of all 27 states."""
    coords, labels, colors = generate_states()

    fig = plt.figure(figsize=(12, 9))
    ax = fig.add_subplot(111, projection="3d")

    # Plot points
    ax.scatter(
        coords[:, 0], coords[:, 1], coords[:, 2],
        c=colors, s=120, edgecolors="black", linewidths=0.5, alpha=0.85,
        depthshade=True,
    )

    # Add labels to each point
    for (x, y, z), label in zip(coords, labels):
        ax.text(
            x + 0.06, y + 0.06, z + 0.06, label,
            fontsize=6, alpha=0.8, fontfamily="monospace",
        )

    # Axis labels and ticks
    ax.set_xlabel("T (Time)", fontsize=11, labelpad=10)
    ax.set_ylabel("D (Scale)", fontsize=11, labelpad=10)
    ax.set_zlabel("I (Agency)", fontsize=11, labelpad=10)

    ax.set_xticks([0, 1, 2])
    ax.set_xticklabels(T_LABELS)
    ax.set_yticks([0, 1, 2])
    ax.set_yticklabels(D_LABELS)
    ax.set_zticks([0, 1, 2])
    ax.set_zticklabels(I_LABELS)

    # Legend for Time-based coloring
    for t_val, color_name in T_COLOR_NAMES.items():
        ax.scatter([], [], [], c=T_COLORS[t_val], s=80, label=color_name,
                   edgecolors="black", linewidths=0.5)
    ax.legend(loc="upper left", fontsize=9)

    ax.set_title("C4 Cognitive State Space — 27 States (3x3x3)", fontsize=13, pad=15)

    # Set viewing angle for best readability
    ax.view_init(elev=25, azim=135)

    plt.tight_layout()
    plt.savefig("c4_27_states.png", dpi=150, bbox_inches="tight")
    print("Saved: c4_27_states.png")
    plt.show()


if __name__ == "__main__":
    plot_states()
