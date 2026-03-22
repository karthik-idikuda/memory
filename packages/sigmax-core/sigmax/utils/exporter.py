"""
╔══════════════════════════════════════════════════════════╗
║  SIGMA-X Omega — Export Utilities                         ║
║  Export chains to JSON, Markdown, CSV                     ║
╚══════════════════════════════════════════════════════════╝
"""

from __future__ import annotations

import csv
import io
import json
import time
from typing import Dict, List, Optional

from sigmax.core.causenode import CauseNode


def export_json(
    nodes: List[CauseNode],
    predictions: Optional[List[dict]] = None,
    pretty: bool = True,
) -> str:
    """Export chains to JSON string."""
    data = {
        'export_time': time.strftime('%Y-%m-%d %H:%M:%S'),
        'format': 'sigma-x-export',
        'version': '1.0',
        'chain_count': len(nodes),
        'chains': [n.to_dict() for n in nodes],
    }
    if predictions:
        data['predictions'] = predictions
    indent = 2 if pretty else None
    return json.dumps(data, indent=indent, default=str)


def export_markdown(
    nodes: List[CauseNode],
    title: str = "SIGMA-X Causal Brain Export",
) -> str:
    """Export chains to Markdown."""
    lines = [
        f"# {title}",
        f"_Exported: {time.strftime('%Y-%m-%d %H:%M:%S')}_",
        f"_Chains: {len(nodes)}_",
        "",
    ]

    # Group by zone
    zones: Dict[str, List[CauseNode]] = {}
    for node in nodes:
        z = node.zone
        if z not in zones:
            zones[z] = []
        zones[z].append(node)

    for zone in ['AXIOM', 'ACTIVE', 'WARM', 'DORMANT', 'ARCHIVED']:
        zone_nodes = zones.get(zone, [])
        if not zone_nodes:
            continue
        lines.append(f"## {zone} ({len(zone_nodes)} chains)")
        lines.append("")
        for node in zone_nodes:
            lines.append(
                f"- **{node.cause}** → **{node.effect}** "
                f"(type={node.cause_type}, conf={node.confidence:.2f}, "
                f"evidence={node.evidence_net:+d})"
            )
        lines.append("")

    return "\n".join(lines)


def export_csv(nodes: List[CauseNode]) -> str:
    """Export chains to CSV string."""
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        'id', 'cause', 'effect', 'type', 'confidence', 'weight',
        'zone', 'evidence_for', 'evidence_against', 'predictions_made',
        'predictions_correct', 'decay_class', 'subject', 'tags',
        'access_count', 'age_days',
    ])
    for node in nodes:
        writer.writerow([
            node.id[:16], node.cause, node.effect, node.cause_type,
            f"{node.confidence:.3f}", f"{node.weight:.2f}",
            node.zone, node.evidence_for, node.evidence_against,
            node.predictions_made, node.predictions_correct,
            node.decay_class, node.subject, ';'.join(node.tags),
            node.access_count, f"{node.age_days:.1f}",
        ])
    return output.getvalue()


def import_json(json_str: str) -> List[CauseNode]:
    """Import chains from JSON string."""
    data = json.loads(json_str)
    chains = data.get('chains', [])
    return [CauseNode.from_dict(c) for c in chains]
