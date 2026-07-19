#!/usr/bin/env python3
"""Render the RQ3 analysis figure from frozen aggregate results."""

from __future__ import annotations

import csv
import math
import os
import tempfile
from pathlib import Path

os.environ.setdefault("MPLBACKEND", "Agg")
os.environ.setdefault("MPLCONFIGDIR", str(Path(tempfile.gettempdir()) / "skillmisevo-mpl"))
os.environ.setdefault("XDG_CACHE_HOME", str(Path(tempfile.gettempdir()) / "skillmisevo-cache"))

import matplotlib.pyplot as plt
from matplotlib.lines import Line2D


ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "figures" / "rq3_exposure_schedule.csv"
OUTPUT = ROOT / "figures" / "rq3_exposure_schedule.pdf"

CONFIGS = {
    "Claude Code + AutoSkill": ("#0000b3", "o"),
    "Codex + EvoSkill": ("#d97706", "o"),
    "Hermes + Hermes-native": ("#b3262d", "o"),
}

PANELS = {
    "cumulative": {
        "title": "(a) Cumulative exposure",
        "levels": ["0", "3", "6", "9"],
        "xlabel": "Cumulative malicious exposure, $\\mathbf{K}$",
    },
    "timing": {
        "title": "(b) Exposure timing",
        "levels": ["Early", "Interleaved", "Late"],
        "xlabel": "Position in learning history",
    },
    "composition": {
        "title": "(c) Update-batch composition",
        "levels": ["Fully mixed", "Partially mixed", "Batched"],
        "ticklabels": ["Fully\nmixed", "Partially\nmixed", "Batched"],
        "xlabel": "Malicious-experience batching",
    },
}


def number(value: str) -> float | None:
    value = value.strip()
    return None if not value else float(value)


def load_rows() -> list[dict[str, str]]:
    with INPUT.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def level_key(value: str) -> str:
    try:
        return str(int(float(value)))
    except ValueError:
        return value


def main() -> None:
    plt.rcParams.update(
        {
            "font.family": "Times New Roman",
            "mathtext.fontset": "custom",
            "mathtext.rm": "Times New Roman",
            "mathtext.it": "Times New Roman:italic",
            "mathtext.bf": "Times New Roman:bold",
            "font.size": 8.8,
            "font.weight": "bold",
            "axes.titlesize": 10.0,
            "axes.titleweight": "bold",
            "axes.labelsize": 9.0,
            "axes.labelweight": "bold",
            "xtick.labelsize": 8.0,
            "ytick.labelsize": 8.0,
            "legend.fontsize": 8.0,
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
        }
    )

    rows = load_rows()
    observed = [number(row["mean"]) for row in rows]
    observed = [value for value in observed if value is not None]
    ymax = max(40.0, math.ceil(max(observed, default=35.0) / 10.0) * 10.0)

    fig, axes = plt.subplots(1, 3, figsize=(7.05, 2.58), sharey=True)
    for panel_index, (ax, (panel, spec)) in enumerate(zip(axes, PANELS.items(), strict=True)):
        levels = spec["levels"]
        positions = {level: index for index, level in enumerate(levels)}
        has_values = False

        for config, (color, marker) in CONFIGS.items():
            series = [row for row in rows if row["panel"] == panel and row["configuration"] == config]
            values = {level_key(row["x"]): row for row in series}
            xs, ys = [], []
            for level in levels:
                row = values.get(level)
                mean = number(row["mean"]) if row else None
                if mean is None:
                    continue
                xs.append(positions[level])
                ys.append(mean)
            if not xs:
                continue
            has_values = True
            ax.plot(
                xs, ys, color=color, marker=marker,
                markersize=4.5, markeredgecolor="white", markeredgewidth=0.4,
                linewidth=1.35, zorder=3,
            )

        ax.set_title(spec["title"], loc="left", fontweight="bold", pad=7)
        ax.set_xlabel(spec["xlabel"], labelpad=4)
        ax.set_xticks(range(len(levels)), spec.get("ticklabels", levels))
        ax.set_xlim(-0.18, len(levels) - 0.82)
        ax.set_ylim(0, ymax)
        for spine in ax.spines.values():
            spine.set_visible(True)
            spine.set_color("#777777")
            spine.set_linewidth(0.65)
        ax.tick_params(axis="x", color="#777777", labelcolor="#333333",
                       width=0.55, length=2.8, direction="out")
        ax.tick_params(axis="y", color="#777777", labelcolor="#333333",
                       width=0.55, length=2.8, direction="out")
        for label in (*ax.get_xticklabels(), *ax.get_yticklabels()):
            label.set_fontweight("bold")
        if panel_index > 0:
            ax.tick_params(axis="y", left=False, labelleft=False)
        if not has_values:
            ax.text(0.5, 0.51, "Results pending", transform=ax.transAxes,
                    ha="center", va="center", color="#888888",
                    fontsize=8.5, fontweight="bold")

    axes[0].set_ylabel("Carryover ASR (%)")
    legend = [
        Line2D([0], [0], color=color, marker=marker, markersize=4.5,
               markeredgecolor="white", markeredgewidth=0.4, linewidth=1.35,
               label=config)
        for config, (color, marker) in CONFIGS.items()
    ]
    fig.legend(handles=legend, loc="lower center", bbox_to_anchor=(0.5, -0.005),
               frameon=False, ncol=3, handlelength=1.7, columnspacing=1.25,
               prop={"family": "Times New Roman", "weight": "bold", "size": 8.0})
    fig.subplots_adjust(left=0.078, right=0.995, top=0.86, bottom=0.31, wspace=0.25)
    fig.savefig(OUTPUT, bbox_inches="tight", pad_inches=0.015)


if __name__ == "__main__":
    main()
