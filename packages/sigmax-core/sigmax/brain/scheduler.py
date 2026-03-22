"""
╔══════════════════════════════════════════════════════════╗
║  SIGMA-X Omega — Background Scheduler                     ║
║  CAULANG-Ω: SCHEDULER — the brain never sleeps            ║
╚══════════════════════════════════════════════════════════╝

Background tasks:
- Zone audit (reassign thermal zones)
- Prediction horizon checks (expire overdue predictions)
- Axiom crystallization scan
- NEURON-X bridge sync
- Decay application
"""

from __future__ import annotations

import time
from typing import Any, Callable, Dict, List, Optional

from sigmax.config import AUDIT_INTERVAL
from sigmax.core.causenode import CauseNode


class Scheduler:
    """
    Runs periodic background tasks for brain maintenance.
    Not a separate thread — triggered on every Nth operation.
    """

    def __init__(
        self,
        audit_interval: int = AUDIT_INTERVAL,
    ):
        self.audit_interval = audit_interval
        self._operation_count = 0
        self._last_audit_time = 0.0
        self._last_horizon_check = 0.0
        self._last_crystallization_scan = 0.0
        self._last_bridge_sync = 0.0
        self._audit_results: List[dict] = []

    def tick(self) -> bool:
        """
        Increment operation counter.
        Returns True if audit should run.
        """
        self._operation_count += 1
        return self._operation_count % self.audit_interval == 0

    def should_audit(self) -> bool:
        """Check if it's time for a zone audit."""
        return self._operation_count % self.audit_interval == 0

    def run_audit(
        self,
        nodes: List[CauseNode],
        zone_manager: Any = None,
        prediction_engine: Any = None,
        axiom_engine: Any = None,
        bridge: Any = None,
    ) -> dict:
        """
        Run a full background audit.

        Steps:
        1. Reassign thermal zones
        2. Check prediction horizons
        3. Scan for axiom candidates
        4. Sync with NEURON-X (if connected)
        """
        results: dict = {
            'timestamp': time.time(),
            'operation_count': self._operation_count,
        }

        # 1. Zone audit
        if zone_manager:
            zone_result = zone_manager.run_zone_audit(nodes)
            results['zone_audit'] = {
                'transitions': zone_result.get('transitions', 0),
                'distribution': zone_result.get('distribution', {}),
            }
            self._last_audit_time = time.time()

        # 2. Prediction horizon check
        if prediction_engine:
            expired = prediction_engine.check_horizons()
            results['predictions'] = {
                'expired': len(expired),
                'stats': prediction_engine.get_stats(),
            }
            self._last_horizon_check = time.time()

        # 3. Axiom crystallization scan
        if axiom_engine:
            crystallized = axiom_engine.scan_and_crystallize(nodes)
            results['crystallization'] = {
                'new_axioms': len(crystallized),
                'axiom_ids': [n.id[:8] for n in crystallized],
            }
            self._last_crystallization_scan = time.time()

        # 4. NEURON-X bridge sync
        if bridge and bridge.is_connected:
            try:
                pushed = bridge.push_conclusions_bulk(nodes)
                results['bridge_sync'] = {
                    'pushed': pushed,
                }
                self._last_bridge_sync = time.time()
            except Exception as e:
                results['bridge_sync'] = {'error': str(e)}

        self._audit_results.append(results)
        # Keep only last 100 audit results
        if len(self._audit_results) > 100:
            self._audit_results = self._audit_results[-100:]

        return results

    @property
    def operation_count(self) -> int:
        return self._operation_count

    @property
    def stats(self) -> dict:
        return {
            'operation_count': self._operation_count,
            'last_audit_time': self._last_audit_time,
            'last_horizon_check': self._last_horizon_check,
            'last_crystallization_scan': self._last_crystallization_scan,
            'last_bridge_sync': self._last_bridge_sync,
            'total_audits': len(self._audit_results),
        }

    @property
    def last_audit(self) -> Optional[dict]:
        return self._audit_results[-1] if self._audit_results else None
