"""
╔══════════════════════════════════════════════════════════╗
║  NEURON-X Omega — Brain Exporter                         ║
║  NRNLANG-Ω: >> EXPORT brain → file                      ║
╚══════════════════════════════════════════════════════════╝

BUG-018 FIX: Export includes ALL required fields.
Supports 4 formats: JSON, Markdown, CSV, NRNLANG-Ω
"""

import json
import csv
import io
import time
from typing import Optional

from neuronx.core.soma import SomaDB
from neuronx.core.node import EngramNode

import logging
logger = logging.getLogger("NEURONX.EXPORT")


class BrainExporter:
    """Export brain data in multiple formats."""

    def __init__(self, soma: SomaDB):
        self.soma = soma

    def to_json(self, path: Optional[str] = None) -> str:
        """Export as JSON (BUG-018 FIX: all fields included)."""
        data = {
            "neuronx_version": "1.0.0",
            "exported_at": time.time(),
            "stats": self.soma.get_stats(),
            "engrams": {
                eid: e.to_dict()
                for eid, e in self.soma.engrams.items()
            },
            "axons": [a.to_dict() for a in self.soma.axons],
        }
        output = json.dumps(data, indent=2, ensure_ascii=False, default=str)
        if path:
            with open(path, "w") as f:
                f.write(output)
        return output

    def to_markdown(self, path: Optional[str] = None) -> str:
        """Export as Markdown report."""
        stats = self.soma.get_stats()
        lines = [
            "# NEURON-X Brain Export",
            f"Exported: {time.strftime('%Y-%m-%d %H:%M:%S')}",
            f"Total engrams: {stats['total_engrams']}",
            f"Total bonds: {stats['total_axons']}",
            "",
            "## Memories",
            "",
        ]
        for engram in sorted(self.soma.engrams.values(), key=lambda e: e.heat, reverse=True):
            anchor = " ◆" if engram.is_anchor else ""
            lines.append(
                f"- [{engram.zone[0]}] **{engram.raw}** "
                f"(conf={engram.confidence:.0%}, heat={engram.heat:.2f}{anchor})"
            )
        output = "\n".join(lines)
        if path:
            with open(path, "w") as f:
                f.write(output)
        return output

    def to_csv(self, path: Optional[str] = None) -> str:
        """Export as CSV."""
        buf = io.StringIO()
        writer = csv.writer(buf)
        writer.writerow([
            "id", "raw", "born", "last_seen", "zone", "heat",
            "weight", "confidence", "surprise_score", "decay_class",
            "emotion", "truth", "is_anchor", "access_count", "tags",
        ])
        for e in self.soma.engrams.values():
            writer.writerow([
                e.id, e.raw, e.born, e.last_seen, e.zone, e.heat,
                e.weight, e.confidence, e.surprise_score, e.decay_class,
                e.emotion, e.truth, e.is_anchor, e.access_count,
                "|".join(e.tags),
            ])
        output = buf.getvalue()
        if path:
            with open(path, "w") as f:
                f.write(output)
        return output

    def to_nrnlang(self, path: Optional[str] = None) -> str:
        """Export as NRNLANG-Ω script."""
        from neuronx.language.nrnlang import NRNLangInterpreter
        lines = [
            "# NEURON-X Brain Export — NRNLANG-Ω Format",
            f"# Exported: {time.strftime('%Y-%m-%d %H:%M:%S')}",
            f"# Engrams: {len(self.soma.engrams)}",
            "",
        ]
        for engram in self.soma.engrams.values():
            lines.append(NRNLangInterpreter.format_engram_nrnlang(engram))
        output = "\n".join(lines)
        if path:
            with open(path, "w") as f:
                f.write(output)
        return output
