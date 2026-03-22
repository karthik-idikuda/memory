"""
╔══════════════════════════════════════════════════════════╗
║  NEURON-X Omega — Background Scheduler                   ║
║  NRNLANG-Ω: AUDIT SCHEDULER — auto-triggers at interval ║
╚══════════════════════════════════════════════════════════╝

BUG-009 FIX: Auto-triggers audit at every AUDIT_INTERVAL interactions.
"""

import logging
from neuronx.config import AUDIT_INTERVAL

logger = logging.getLogger("NEURONX.SCHEDULER")


class AuditScheduler:
    """
    NRNLANG-Ω: SCHEDULER — tracks interaction count and triggers audits.

    BUG-009 FIX: Audit auto-runs at AUDIT_INTERVAL (100) interactions.
    """

    def __init__(self, interval: int = AUDIT_INTERVAL):
        self.interval = interval
        self.interaction_count: int = 0

    def tick(self) -> bool:
        """
        Increment interaction count. Returns True if audit should run.
        BUG-009 FIX: if count % AUDIT_INTERVAL == 0: run audit.
        """
        self.interaction_count += 1
        should_audit = (self.interaction_count % self.interval == 0)
        if should_audit:
            logger.info(
                f"🔍 AUDIT TRIGGERED at interaction #{self.interaction_count}"
            )
        return should_audit

    def reset(self) -> None:
        self.interaction_count = 0
