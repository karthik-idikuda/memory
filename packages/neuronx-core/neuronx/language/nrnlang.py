"""
╔══════════════════════════════════════════════════════════╗
║  NEURON-X Omega — NRNLANG-Ω Interpreter                  ║
║  NRNLANG-Ω: The custom memory description language       ║
╚══════════════════════════════════════════════════════════╝

NRNLANG-Ω is a custom symbolic language for expressing
memory operations in a human-readable, machine-parseable format.

Commands:
  FORGE engram("text") >> SOMA       → Create memory
  ECHO engram("text") |→ +0.15      → Reinforce
  RECALL ?? "query" @7 → RANKED     → Retrieve top-7
  WEAVE engram_A <=> engram_B :::   → Create bond
  TEMPER ~~ engram → [H]            → Zone assignment
  AUDIT 🔍 brain                    → Full thermal audit
  CLASH ## old_engram vs new_engram  → Contradiction
  EXPIRE engram ⊖ → COLD           → Mark expired
  CRYSTALLIZE engram ◆ → ANCHOR    → Lock as permanent
  EXPORT brain >> file.nrn          → Export
  STATS brain → report              → Get statistics
"""

import re
import logging
from typing import Optional, Dict, Any, List

from neuronx.config import (
    NRNLANG_ACTION_SYMBOLS, NRNLANG_ZONE_SYMBOLS,
    NRNLANG_EMOTION_SYMBOLS, NRNLANG_EXISTENCE_SYMBOLS,
    NRNLANG_TRUTH_SYMBOLS, DEFAULT_TOP_K,
)
from neuronx.exceptions import NRNSyntaxError, NRNRuntimeError

logger = logging.getLogger("NEURONX.NRNLANG")


class NRNLangInterpreter:
    """
    NRNLANG-Ω Interpreter — parses and executes NRNLANG-Ω commands.
    """

    # Command patterns
    FORGE_PATTERN = re.compile(r'FORGE\s+engram\("(.+?)"\)')
    ECHO_PATTERN = re.compile(r'ECHO\s+engram\("(.+?)"\)')
    RECALL_PATTERN = re.compile(r'RECALL\s*\?\?\s*"(.+?)"(?:\s+@(\d+))?')
    RECALL_ALT_PATTERN = re.compile(r'RECALL\s+query\("(.+?)"(?:,\s*top_k=(\d+))?\)')
    WEAVE_PATTERN = re.compile(r'WEAVE\s+(\w+)\s*<=>\s*(\w+)')
    TEMPER_PATTERN = re.compile(r'TEMPER\s+~~\s+(\w+)')
    AUDIT_PATTERN = re.compile(r'AUDIT\s+brain')
    STATS_PATTERN = re.compile(r'STATS\s+brain')
    EXPORT_PATTERN = re.compile(r'EXPORT\s+brain(?:\s*>>\s*(\S+)|\s*\(format="(\w+)"\))')
    EXPIRE_PATTERN = re.compile(r'EXPIRE\s+(?:engram\(id="(\w+)"\)|(\w+))')
    CRYSTALLIZE_PATTERN = re.compile(r'CRYSTALLIZE\s+(?:engram\(id="(\w+)"\)|(\w+))')

    def __init__(self, brain=None):
        self.brain = brain
        self.output_log: List[str] = []

    def execute(self, command: str) -> Dict[str, Any]:
        """Parse and execute a single NRNLANG-Ω command."""
        command = command.strip()
        if not command or command.startswith("#"):
            return {"status": "skip", "message": "Comment or empty"}

        # Try each pattern
        m = self.FORGE_PATTERN.match(command)
        if m:
            return self._exec_forge(m.group(1))

        m = self.ECHO_PATTERN.match(command)
        if m:
            return self._exec_echo(m.group(1))

        m = self.RECALL_PATTERN.match(command)
        if not m:
            m = self.RECALL_ALT_PATTERN.match(command)
        if m:
            top_k = int(m.group(2)) if m.group(2) else DEFAULT_TOP_K
            return self._exec_recall(m.group(1), top_k)

        m = self.AUDIT_PATTERN.match(command)
        if m:
            return self._exec_audit()

        m = self.STATS_PATTERN.match(command)
        if m:
            return self._exec_stats()

        m = self.EXPORT_PATTERN.match(command)
        if m:
            target = m.group(1) or m.group(2) or "json"
            return self._exec_export(target)

        m = self.EXPIRE_PATTERN.match(command)
        if m:
            eid = m.group(1) or m.group(2)
            return self._exec_expire(eid)

        m = self.CRYSTALLIZE_PATTERN.match(command)
        if m:
            eid = m.group(1) or m.group(2)
            return self._exec_crystallize(eid)

        raise NRNSyntaxError(f"Unknown command: {command}")

    def execute_script(self, script: str) -> List[Dict[str, Any]]:
        """Execute a multi-line NRNLANG-Ω script."""
        results = []
        for i, line in enumerate(script.strip().split("\n"), 1):
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            try:
                result = self.execute(line)
                results.append(result)
            except NRNSyntaxError as e:
                results.append({"status": "error", "line": i, "error": str(e)})
        return results

    def _exec_forge(self, text: str) -> dict:
        if not self.brain:
            raise NRNRuntimeError("No brain connected")
        result = self.brain.remember(text)
        sym = NRNLANG_ACTION_SYMBOLS.get(result.action, "?")
        msg = f"{sym} {result.action} id={result.engram_id[:8]}… surprise={result.surprise_score:.2f}"
        self.output_log.append(msg)
        return {"status": "ok", "action": result.action, "id": result.engram_id, "log": msg}

    def _exec_echo(self, text: str) -> dict:
        if not self.brain:
            raise NRNRuntimeError("No brain connected")
        result = self.brain.remember(text)
        msg = f"● ECHO id={result.engram_id[:8]}…"
        self.output_log.append(msg)
        return {"status": "ok", "action": "ECHO", "id": result.engram_id, "log": msg}

    def _exec_recall(self, query: str, top_k: int) -> dict:
        if not self.brain:
            raise NRNRuntimeError("No brain connected")
        results = self.brain.recall(query, top_k=top_k)
        lines = []
        for i, (engram, score) in enumerate(results, 1):
            lines.append(f"  [{i}] {engram.raw[:60]} (score={score:.3f})")
        msg = f"CORTEX ?? \"{query}\" @{top_k}\n" + "\n".join(lines)
        self.output_log.append(msg)
        return {"status": "ok", "count": len(results), "log": msg}

    def _exec_audit(self) -> dict:
        if not self.brain:
            raise NRNRuntimeError("No brain connected")
        stats = self.brain.run_audit()
        msg = f"🔍 AUDIT — promoted:{stats['promoted']} demoted:{stats['demoted']}"
        self.output_log.append(msg)
        return {"status": "ok", "stats": stats, "log": msg}

    def _exec_stats(self) -> dict:
        if not self.brain:
            raise NRNRuntimeError("No brain connected")
        stats = self.brain.get_stats()
        msg = f"STATS — {stats['total_engrams']} engrams, {stats['total_axons']} axons"
        self.output_log.append(msg)
        return {"status": "ok", "stats": stats, "log": msg}

    def _exec_export(self, filename: str) -> dict:
        if not self.brain:
            raise NRNRuntimeError("No brain connected")
        fmt = "nrnlang" if filename.endswith(".nrn") else "json"
        self.brain.export(format=fmt, path=filename)
        msg = f">> EXPORT brain → {filename}"
        self.output_log.append(msg)
        return {"status": "ok", "file": filename, "log": msg}

    def _exec_expire(self, engram_id: str) -> dict:
        if not self.brain:
            raise NRNRuntimeError("No brain connected")
        engram = self.soma_lookup(engram_id)
        if engram:
            engram.expire()
            msg = f"⊖ EXPIRE {engram_id[:8]}…"
            self.output_log.append(msg)
            return {"status": "ok", "log": msg}
        return {"status": "error", "error": f"Engram {engram_id} not found"}

    def _exec_crystallize(self, engram_id: str) -> dict:
        if not self.brain:
            raise NRNRuntimeError("No brain connected")
        engram = self.soma_lookup(engram_id)
        if engram:
            engram.crystallize()
            msg = f"◆ CRYSTALLIZE {engram_id[:8]}… → ANCHOR"
            self.output_log.append(msg)
            return {"status": "ok", "log": msg}
        return {"status": "error", "error": f"Engram {engram_id} not found"}

    def soma_lookup(self, partial_id: str):
        """Lookup engram by full or partial ID."""
        if partial_id in self.brain.soma.engrams:
            return self.brain.soma.engrams[partial_id]
        for eid, engram in self.brain.soma.engrams.items():
            if eid.startswith(partial_id):
                return engram
        return None

    @staticmethod
    def format_engram_nrnlang(engram) -> str:
        """Format an engram in NRNLANG-Ω notation."""
        zone_sym = NRNLANG_ZONE_SYMBOLS.get(engram.zone, "[?]")
        emo_sym = NRNLANG_EMOTION_SYMBOLS.get(engram.emotion, ":~:")
        truth_sym = NRNLANG_TRUTH_SYMBOLS.get(engram.truth, "|-")
        anchor = " ◆" if engram.is_anchor else ""

        return (
            f"ENGRAM {{ "
            f"id:\"{engram.id[:8]}…\" "
            f"raw:\"{engram.raw[:60]}\" "
            f"born:T[{engram.born:.0f}] "
            f"heat:{engram.heat:.2f}~>{zone_sym} "
            f"spark:{engram.surprise_score:.2f}⚡ "
            f"conf:{engram.confidence:.2f} "
            f"wt:{engram.weight:.2f} "
            f"{emo_sym} {truth_sym}{anchor}"
            f" }}"
        )
