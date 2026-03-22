"""
╔══════════════════════════════════════════════════════════╗
║  SIGMA-X Omega — Brain Health Metrics                      ║
║  Monitor the health and growth of the causal brain          ║
╚══════════════════════════════════════════════════════════╝
"""

from __future__ import annotations

import os
from typing import Dict, List

from sigmax.core.causenode import CauseNode
from sigmax.config import ZONE_AXIOM, ZONE_ACTIVE, ZONE_ARCHIVED


def compute_brain_health(nodes: List[CauseNode]) -> dict:
    """Compute comprehensive brain health metrics."""
    if not nodes:
        return {
            'health_score': 0.0,
            'total_chains': 0,
            'status': 'EMPTY',
        }

    total = len(nodes)
    avg_confidence = sum(n.confidence for n in nodes) / total
    avg_evidence = sum(n.evidence_net for n in nodes) / total
    axiom_count = sum(1 for n in nodes if n.zone == ZONE_AXIOM)
    active_count = sum(1 for n in nodes if n.zone == ZONE_ACTIVE)
    archived_count = sum(1 for n in nodes if n.zone == ZONE_ARCHIVED)
    total_predictions = sum(n.predictions_made for n in nodes)
    correct_predictions = sum(n.predictions_correct for n in nodes)
    pred_accuracy = correct_predictions / total_predictions if total_predictions > 0 else 0.0

    # Health score (0-100)
    confidence_score = avg_confidence * 25
    evidence_score = min(25, max(0, (avg_evidence + 5) / 10 * 25))
    prediction_score = pred_accuracy * 25
    activity_score = min(25, (active_count / max(1, total)) * 50)

    health = confidence_score + evidence_score + prediction_score + activity_score

    if health >= 80:
        status = "EXCELLENT"
    elif health >= 60:
        status = "GOOD"
    elif health >= 40:
        status = "MODERATE"
    elif health >= 20:
        status = "WEAK"
    else:
        status = "CRITICAL"

    return {
        'health_score': round(health, 1),
        'status': status,
        'total_chains': total,
        'avg_confidence': round(avg_confidence, 3),
        'avg_evidence_net': round(avg_evidence, 1),
        'axiom_count': axiom_count,
        'active_count': active_count,
        'archived_count': archived_count,
        'prediction_accuracy': round(pred_accuracy, 3),
        'total_predictions': total_predictions,
        'correct_predictions': correct_predictions,
        'confidence_score': round(confidence_score, 1),
        'evidence_score': round(evidence_score, 1),
        'prediction_score': round(prediction_score, 1),
        'activity_score': round(activity_score, 1),
    }


def compute_file_metrics(sigma_path: str) -> dict:
    """Compute .sigma file metrics."""
    if not os.path.exists(sigma_path):
        return {'exists': False}

    size = os.path.getsize(sigma_path)
    mtime = os.path.getmtime(sigma_path)

    return {
        'exists': True,
        'size_bytes': size,
        'size_kb': round(size / 1024, 2),
        'size_mb': round(size / (1024 * 1024), 4),
        'last_modified': mtime,
        'has_backup': os.path.exists(sigma_path + '.bak'),
        'has_signature': os.path.exists(sigma_path + '.sig'),
        'has_log': os.path.exists(sigma_path + '.log'),
    }
