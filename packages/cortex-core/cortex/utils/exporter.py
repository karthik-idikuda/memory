"""CORTEX-X — Exporter (export brain data to JSON/Markdown)."""

from __future__ import annotations
import json
from typing import Dict, Any
from cortex.core.cortexdb import CortexDB


def export_json(db: CortexDB, path: str) -> None:
    """Export brain contents to a JSON file."""
    data = {
        "stats": db.stats(),
        "thoughts": [t.to_dict() for t in db.thoughts.values()],
        "metacog_state": db.get_metacog_state(),
        "strategies": db.get_strategies(),
        "growth_log": db.get_growth_log(),
    }
    with open(path, "w") as f:
        json.dump(data, f, indent=2, default=str)


def export_markdown(db: CortexDB, path: str) -> None:
    """Export brain summary to Markdown."""
    stats = db.stats()
    lines = [
        f"# CORTEX-X Brain Export",
        f"",
        f"**Thoughts:** {stats['thought_count']}",
        f"**Edges:** {stats['edge_count']}",
        f"**Strategies:** {stats['strategy_count']}",
        f"**Wisdom:** {stats['wisdom_count']}",
        f"",
        f"## Zone Distribution",
    ]
    for zone, count in stats.get("zones", {}).items():
        lines.append(f"- {zone}: {count}")

    lines.extend(["", "## Recent Thoughts", ""])
    thoughts = sorted(db.thoughts.values(), key=lambda t: t.created_at, reverse=True)
    for t in thoughts[:20]:
        lines.append(f"- **[{t.thought_type}]** {t.content[:100]} (conf: {t.confidence:.0%})")

    with open(path, "w") as f:
        f.write("\n".join(lines))
