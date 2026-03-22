"""
╔══════════════════════════════════════════════════════════╗
║  NEURON-X Omega — NRNLANG-Ω Interpreter                  ║
║  The custom language parser, formatter, and executor      ║
║                                                          ║
║  NRNLANG-Ω: The soul of NEURON-X                         ║
║  Every symbol, keyword, grammar rule — invented from zero ║
╚══════════════════════════════════════════════════════════╝

NRNLANG-Ω (Neural Record Node Language — Omega Edition)

This module provides:
  1. PARSE    — Read .nrn files (NRNLANG-Ω scripts)
  2. FORMAT   — Convert engrams/operations to NRNLANG-Ω notation
  3. EXECUTE  — Run FORGE, INVOKE, WEAVE, TEMPER, AUDIT commands
  4. VALIDATE — Check NRNLANG-Ω syntax and report errors
  5. EXPORT   — Convert brain state to NRNLANG-Ω notation
"""

import re
import time
import logging

logger = logging.getLogger("NEURONX.NRNLANG")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# NRNLANG-Ω SYMBOL TABLES
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# GROUP A — EXISTENCE SYMBOLS
EXISTENCE_SYMBOLS = {
    "ENGRAM_BORN":   "╔══╗",
    "ENGRAM_DIED":   "╚══╝",
    "ENGRAM_LIVE":   "◈",
    "ENGRAM_SLEEP":  "◇",
    "ENGRAM_ANCHOR": "◆",
    "ENGRAM_GHOST":  "○",
    "ENGRAM_ECHO":   "●",
    "ENGRAM_FORGE":  "⊕",
    "ENGRAM_EXPIRE": "⊖",
}

# GROUP B — FLOW SYMBOLS
FLOW_SYMBOLS = {
    "FIRE":        "~>",
    "SUPPRESS":    "<~",
    "STORE":       ">>",
    "INVOKE":      "<<",
    "REAWAKEN":    "^^",
    "DECAY":       "~~",
    "IMPLIES":     "=>",
    "REQUIRES":    "<=",
    "LINKS":       "<=>",
    "DEEP_STORE":  "->>",
    "DEEP_RECALL": "<<-",
}

# GROUP C — COMPARISON SYMBOLS
COMPARISON_SYMBOLS = {
    "SAME":       "===",
    "UNIQUE":     "=/=",
    "DRIFT":      "~=",
    "CLASH":      "##",
    "CONTESTED":  "|?|",
    "SUPERSEDE":  "!!=",
    "EQUIVALENT": "<=>",
}

# GROUP D — STRENGTH SYMBOLS
STRENGTH_SYMBOLS = {
    "GROW":     "+++",
    "SHRINK":   "---",
    "PEAK":     "***",
    "REINFORCE":":::",
    "FAINT":    "¦¦¦",
    "STRONG":   "|||",
    "SEVERED":  "-x-",
    "SPARK":    "⚡",
}

# GROUP E — ZONE SYMBOLS
ZONE_SYMBOLS = {
    "H": "🔥 [H]",
    "W": "🌡 [W]",
    "C": "❄  [C]",
    "S": "👻 [S]",
    "G": "○  [G]",
    "F": "🪨 [F]",
    "A": "◆  [A]",
}

# GROUP F — TRUTH SYMBOLS
TRUTH_SYMBOLS = {
    "ACTIVE":    "◈ |-",
    "EXPIRED":   "◇ -|",
    "MAYBE":     "○ |?|",
    "CONFLICT":  "● |!|",
    "ANCHOR":    "◆ [A]",
}

# GROUP H — EMOTION SYMBOLS
EMOTION_SYMBOLS = {
    "happy":   ":+:",
    "sad":     ":-:",
    "excited": ":!:",
    "curious": ":?:",
    "angry":   ":x:",
    "neutral": ":~:",
    "love":    ":*:",
    "fear":    ":/:",
}

# NRNLANG-Ω KEYWORDS (verbs)
KEYWORDS = {
    "FORGE", "TEMPER", "WEAVE", "INVOKE", "AUDIT", "PRUNE",
    "HIBERNATE", "FOSSILIZE", "REAWAKEN", "HERALD", "SUPERSEDE",
    "RECONCILE", "CONSOLIDATE", "COMPRESS", "EXPAND", "CRYSTALLIZE",
    "PULSE", "GHOST", "ECHO", "CLASH",
}


class NRNLangInterpreter:
    """
    NRNLANG-Ω: INTERPRETER — the language engine.

    PARSE .nrn files → EXECUTE commands → DISPLAY results
    VALIDATE syntax → EXPORT brain state → FORMAT engrams

    Usage:
        nrn = NRNLangInterpreter(brain)
        nrn.engram_to_nrnlang(engram)    # format one engram
        nrn.operation_to_nrnlang(...)    # format one operation
        nrn.session_to_nrnlang(log)      # format whole session
        nrn.brain_to_nrnlang()           # export entire brain
        nrn.parse_nrn_file("file.nrn")   # execute a script
        nrn.validate_syntax(text)        # check syntax
    """

    def __init__(self, brain=None):
        """
        NRNLANG-Ω: INTERPRETER ╔══╗ BORN

        Initialize interpreter with optional brain reference.
        Brain is needed for EXECUTE and EXPORT commands.
        """
        self.brain = brain

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # FORMAT METHODS
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    def engram_to_nrnlang(self, engram) -> str:
        """
        NRNLANG-Ω: ENGRAM ~> NRNLANG notation string

        Converts an Engram node to full NRNLANG-Ω notation.

        Example output:
          ENGRAM {
            id        : "a3f9c2b1d4e5f6a7"
            raw       : "user loves building AI"
            born      : T[2026.02.27:14:32:01]
            heat      : 0.71  ~>  🔥 [H]
            spark     : 0.88  ⚡
            weight    : 2.3   *** PEAK
            ...
          }
        """
        # Zone symbol
        zone_sym = ZONE_SYMBOLS.get(engram.zone, engram.zone)

        # Truth symbol
        truth_map = {"ACTIVE": "ACTIVE", "EXPIRED": "EXPIRED",
                     "MAYBE": "MAYBE", "CONFLICT": "CONFLICT"}
        truth_key = engram.truth.upper() if hasattr(engram, 'truth') else "ACTIVE"
        truth_sym = TRUTH_SYMBOLS.get(truth_key, "◈ |-")

        # Emotion symbol
        emotion_sym = EMOTION_SYMBOLS.get(engram.emotion, ":~:")

        # Spark indicator
        spark_ind = "  ⚡ HIGH" if engram.spark >= 0.85 else ""

        # Weight indicator
        if engram.weight >= 3.0:
            weight_ind = "  *** PEAK"
        elif engram.weight >= 2.0:
            weight_ind = "  ||| STRONG"
        elif engram.weight <= 0.2:
            weight_ind = "  ¦¦¦ FAINT"
        else:
            weight_ind = ""

        # Format born timestamp
        born_str = self._timestamp_to_nrn(engram.born)
        last_seen_str = self._timestamp_to_nrn(engram.last_seen)

        # Decay class half-life
        half_lives = {
            "emotion": 69, "opinion": 139, "event": 231,
            "fact": 693, "identity": 6931,
        }
        halflife = half_lives.get(engram.decay_class, 693)

        # Format axons
        axon_parts = []
        for aid, syn in list(engram.axons.items())[:5]:
            if syn >= 0.5:
                axon_parts.append(f"{aid[:8]}:{syn:.2f} |||")
            elif syn >= 0.1:
                axon_parts.append(f"{aid[:8]}:{syn:.2f}")
            else:
                axon_parts.append(f"{aid[:8]}:{syn:.2f} ¦¦¦")
        axons_str = "  ".join(axon_parts) if axon_parts else "(none)"

        # Anchor indicator
        anchor = ""
        if getattr(engram, 'is_anchor', False):
            anchor = "  ◆ CRYSTALLIZED"
        elif engram.confidence >= 0.95:
            anchor = "  (ANCHOR candidate)"

        # Age
        age_days = engram.age_days if hasattr(engram, 'age_days') else 0

        return (
            f"ENGRAM {{\n"
            f"  id        : \"{engram.id}\"\n"
            f"  raw       : \"{engram.raw}\"\n"
            f"  born      : {born_str}\n"
            f"  last_seen : {last_seen_str}\n"
            f"  age       : {age_days:.0f}d\n"
            f"  heat      : {engram.heat:.2f}  ~>  {zone_sym}\n"
            f"  spark     : {engram.spark:.2f}{spark_ind}\n"
            f"  weight    : {engram.weight:.1f}{weight_ind}\n"
            f"  decay     : {engram.decay_class}  HALFLIFE[{halflife}d]\n"
            f"  axons     : [{axons_str}]\n"
            f"  truth     : {truth_sym}\n"
            f"  emotion   : {emotion_sym} {engram.emotion}\n"
            f"  confidence: {engram.confidence:.2f}{anchor}\n"
            f"  source    : {getattr(engram, 'source', 'user')}\n"
            f"  tags      : {engram.tags}\n"
            f"}}"
        )

    def operation_to_nrnlang(self, action: str, details: dict) -> str:
        """
        NRNLANG-Ω: OPERATION ~> NRNLANG notation string

        Converts a brain operation to NRNLANG-Ω notation.

        Actions: FORGE, ECHO, CLASH, REAWAKEN, SUPERSEDE, WEAVE, PRUNE
        """
        text = details.get("text", "")[:50]
        surprise = details.get("surprise", 0)
        emotion = details.get("emotion", "neutral")
        emo_sym = EMOTION_SYMBOLS.get(emotion, ":~:")

        if action == "FORGE":
            decay = details.get("decay_class", "fact")
            conf = details.get("confidence", 0.8)
            spark = f"  ⚡" if surprise > 0.85 else ""
            return (
                f"⊕ FORGE engram(\"{text}\") [{decay}] "
                f"{{conf:{conf:.2f}, emotion:{emo_sym}}}{spark}  >>  SOMA"
            )

        elif action == "ECHO":
            match_id = details.get("match_id", "????")[:8]
            return (
                f"● ECHO engram(\"{text}\") === engram[{match_id}]  "
                f"+++weight(+0.15)"
            )

        elif action == "CLASH":
            match_id = details.get("match_id", "????")[:8]
            resolution = details.get("clash_result", "CONTESTED")
            return (
                f"## CLASH engram(\"{text}\") ## engram[{match_id}]  "
                f"⚡ surprise:{surprise:.2f}  → {resolution}"
            )

        elif action == "REAWAKEN":
            zone = details.get("new_zone", "W")
            zone_sym = ZONE_SYMBOLS.get(zone, zone)
            return (
                f"^^ REAWAKEN engram(\"{text}\")  "
                f"○ GHOST ~> {zone_sym}"
            )

        elif action == "SUPERSEDE":
            old_id = details.get("old_id", "????")[:8]
            return (
                f"!!= SUPERSEDE engram[{old_id}]  "
                f"⊖ -| EXPIRED  ~>  engram(\"{text}\") ◈ |- ACTIVE"
            )

        elif action == "WEAVE":
            from_id = details.get("from_id", "????")[:8]
            to_id = details.get("to_id", "????")[:8]
            synapse = details.get("synapse", 0)
            bond_type = details.get("bond_type", "WORD")
            strength = "|||" if synapse >= 0.5 else ("¦¦¦" if synapse < 0.1 else "")
            return (
                f"WEAVE engram[{from_id}] <=> engram[{to_id}]  "
                f"{{synapse:{synapse:.2f}}} [{bond_type}] {strength}"
            )

        elif action == "PRUNE":
            count = details.get("count", 0)
            return f"PRUNE {count} axons  -x-  synapse < 0.05"

        elif action == "TEMPER":
            engram_id = details.get("id", "????")[:8]
            old_zone = details.get("old_zone", "?")
            new_zone = details.get("new_zone", "?")
            old_sym = ZONE_SYMBOLS.get(old_zone, old_zone)
            new_sym = ZONE_SYMBOLS.get(new_zone, new_zone)
            return (
                f"TEMPER engram[{engram_id}]  "
                f"{old_sym} ~> {new_sym}"
            )

        elif action == "CRYSTALLIZE":
            engram_id = details.get("id", "????")[:8]
            return f"CRYSTALLIZE engram[{engram_id}]  ◆ [A]  (never SILENT)"

        elif action == "AUDIT":
            promoted = details.get("promoted", 0)
            demoted = details.get("demoted", 0)
            reawakened = details.get("reawakened", 0)
            return (
                f"AUDIT SOMA  ~>  TEMPER[all] + REAWAKEN[ghosts]\n"
                f"  promoted:{promoted}  demoted:{demoted}  "
                f"reawakened:{reawakened}"
            )

        return f"# Unknown action: {action}"

    def session_to_nrnlang(self, session_log: list[dict]) -> str:
        """
        NRNLANG-Ω: PULSE ~> NRNLANG session script

        Converts entire session log to NRNLANG-Ω script.
        Returns readable .nrn format.
        """
        lines = [
            "# ═══════════════════════════════════════════════",
            f"# NEURON-X Omega — Session Log",
            f"# Generated: {self._timestamp_to_nrn(time.time())}",
            "# ═══════════════════════════════════════════════",
            "",
            f"PULSE begins {self._timestamp_to_nrn(time.time())}",
            "",
        ]

        for entry in session_log:
            action = entry.get("action", "FORGE")
            line = self.operation_to_nrnlang(action, entry)
            lines.append(line)
            lines.append("")

        lines.append("PULSE ends")
        lines.append("")

        return "\n".join(lines)

    def brain_to_nrnlang(self) -> str:
        """
        NRNLANG-Ω: SOMA ~> NRNLANG full brain export

        Exports entire brain state as NRNLANG-Ω document.
        Shows all engrams, axons, and zone distribution.
        """
        if not self.brain:
            return "# ERROR: No brain connected to interpreter"

        lines = [
            "# ═══════════════════════════════════════════════",
            "# NEURON-X Omega — Brain State Export",
            f"# Exported: {self._timestamp_to_nrn(time.time())}",
            "# Format: NRNLANG-Ω",
            "# ═══════════════════════════════════════════════",
            "",
        ]

        # Stats
        stats = self.brain.get_brain_stats()
        lines.append("# ── Brain Statistics ──")
        lines.append(f"# Total Engrams: {stats['total_engrams']}")
        lines.append(f"# Total Axons:   {stats['total_axons']}")
        lines.append(f"# Brain Age:     {stats['brain_age_days']:.0f}d")
        lines.append("")

        # Zone distribution
        lines.append("# ── Zone Distribution ──")
        lines.append(f"# 🔥 [H] HOT:    {stats['hot_count']}")
        lines.append(f"# 🌡 [W] WARM:   {stats['warm_count']}")
        lines.append(f"# ❄  [C] COLD:   {stats['cold_count']}")
        lines.append(f"# 👻 [S] SILENT: {stats['silent_count']}")
        lines.append(f"# ◆  [A] ANCHOR: {stats['anchor_count']}")
        lines.append("")

        # All engrams grouped by zone
        zone_order = [("H", "HOT"), ("A", "ANCHOR"), ("W", "WARM"),
                      ("C", "COLD"), ("S", "SILENT")]

        for zone_code, zone_name in zone_order:
            zone_engrams = [
                e for e in self.brain.soma.engrams.values()
                if e.zone == zone_code
            ]
            if not zone_engrams:
                continue

            zone_sym = ZONE_SYMBOLS.get(zone_code, zone_code)
            lines.append(f"# ── {zone_sym} {zone_name} Zone ({len(zone_engrams)}) ──")
            lines.append("")

            for e in sorted(zone_engrams, key=lambda x: x.heat, reverse=True):
                lines.append(self.engram_to_nrnlang(e))
                lines.append("")

        # Axon map
        if self.brain.soma.axons:
            lines.append("# ── Axon Map ──")
            lines.append("")
            types = {0: "TIME", 1: "WORD", 2: "EMOTION", 3: "CLASH",
                     4: "REINFORCE", 5: "HERALD"}
            sorted_axons = sorted(
                self.brain.soma.axons, key=lambda a: a.synapse, reverse=True
            )
            for a in sorted_axons[:30]:
                t = types.get(a.axon_type, "?")
                strength = "|||" if a.synapse >= 0.5 else (
                    "¦¦¦" if a.synapse < 0.1 else ""
                )
                lines.append(
                    f"WEAVE engram[{a.from_id[:8]}] <=> "
                    f"engram[{a.to_id[:8]}]  "
                    f"{{synapse:{a.synapse:.3f}}} [{t}] {strength}"
                )
            lines.append("")

        return "\n".join(lines)

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # PARSE & EXECUTE
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    def parse_nrn_file(self, filepath: str) -> list[dict]:
        """
        NRNLANG-Ω: PARSE .nrn file ~> EXECUTE commands

        Reads a .nrn file and executes each command.
        Returns list of {command, args, result, status}.
        """
        results = []

        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        return self.execute_nrn(content)

    def execute_nrn(self, nrn_text: str) -> list[dict]:
        """
        NRNLANG-Ω: EXECUTE nrn_text ~> results

        Parse and execute NRNLANG-Ω text line by line.
        """
        results = []

        for line_num, line in enumerate(nrn_text.split("\n"), 1):
            line = line.strip()

            # Skip comments and empty lines
            if not line or line.startswith("#"):
                continue

            # Skip PULSE markers and decorative lines
            if line.startswith("PULSE") or line.startswith("═"):
                results.append({
                    "line": line_num,
                    "command": "META",
                    "text": line,
                    "status": "OK",
                })
                continue

            # Parse known commands
            parsed = self._parse_command(line)
            if parsed:
                result = self._execute_command(parsed)
                result["line"] = line_num
                results.append(result)
            else:
                results.append({
                    "line": line_num,
                    "command": "UNKNOWN",
                    "text": line,
                    "status": "SKIPPED",
                })

        return results

    def _parse_command(self, line: str) -> dict | None:
        """
        NRNLANG-Ω: PARSE single command line

        Supports: FORGE, WEAVE, TEMPER, AUDIT, INVOKE, PRUNE,
                  REAWAKEN, CRYSTALLIZE, SUPERSEDE
        """
        # FORGE engram("text") [type] {props}
        forge_match = re.match(
            r'(?:⊕\s+)?FORGE\s+engram\("([^"]+)"\)\s*'
            r'(?:\[(\w+)\])?\s*(?:\{([^}]*)\})?',
            line
        )
        if forge_match:
            text = forge_match.group(1)
            decay_class = forge_match.group(2) or "fact"
            props_str = forge_match.group(3) or ""
            props = self._parse_props(props_str)
            return {"command": "FORGE", "text": text,
                    "decay_class": decay_class, "props": props}

        # WEAVE engram[id] <=> engram[id] {synapse:X}
        weave_match = re.match(
            r'WEAVE\s+engram\[(\w+)\]\s*(?:<=>|::)\s*engram\[(\w+)\]\s*'
            r'(?:\{([^}]*)\})?',
            line
        )
        if weave_match:
            from_id = weave_match.group(1)
            to_id = weave_match.group(2)
            props_str = weave_match.group(3) or ""
            props = self._parse_props(props_str)
            return {"command": "WEAVE", "from_id": from_id,
                    "to_id": to_id, "props": props}

        # AUDIT SOMA
        if re.match(r'AUDIT\s+SOMA', line):
            return {"command": "AUDIT"}

        # INVOKE CORTEX "query" @N AI
        invoke_match = re.match(
            r'INVOKE\s+CORTEX\s+(?:\?\?\s+)?"([^"]+)"\s*(?:@(\d+))?\s*(?:AI)?',
            line
        )
        if invoke_match:
            query = invoke_match.group(1)
            top_k = int(invoke_match.group(2) or 7)
            return {"command": "INVOKE", "query": query, "top_k": top_k}

        # PRUNE
        if re.match(r'PRUNE', line):
            return {"command": "PRUNE"}

        # TEMPER
        temper_match = re.match(
            r'TEMPER\s+engram\[(\w+)\]\s*.*~>\s*\[(\w+)\]', line
        )
        if temper_match:
            return {"command": "TEMPER", "id": temper_match.group(1),
                    "zone": temper_match.group(2)}

        # CRYSTALLIZE
        cryst_match = re.match(r'CRYSTALLIZE\s+engram\[(\w+)\]', line)
        if cryst_match:
            return {"command": "CRYSTALLIZE", "id": cryst_match.group(1)}

        # REAWAKEN
        reawaken_match = re.match(
            r'(?:\^\^\s+)?REAWAKEN\s+engram\[(\w+)\]', line
        )
        if reawaken_match:
            return {"command": "REAWAKEN", "id": reawaken_match.group(1)}

        return None

    def _execute_command(self, parsed: dict) -> dict:
        """
        NRNLANG-Ω: EXECUTE parsed command ~> result

        Requires brain reference for actual execution.
        Without brain, returns dry-run result.
        """
        cmd = parsed["command"]

        if not self.brain:
            return {
                "command": cmd,
                "status": "DRY_RUN",
                "detail": f"No brain connected — {cmd} logged only",
                "parsed": parsed,
            }

        if cmd == "FORGE":
            results = self.brain.process_input(parsed["text"])
            return {
                "command": "FORGE",
                "status": "OK",
                "detail": f"Forged {len(results)} memories",
                "results": results,
            }

        elif cmd == "INVOKE":
            results = self.brain.recall(
                parsed["query"], top_k=parsed.get("top_k", 7)
            )
            return {
                "command": "INVOKE",
                "status": "OK",
                "detail": f"Retrieved {len(results)} memories",
                "results": [(e.raw, s) for e, s in results],
            }

        elif cmd == "AUDIT":
            stats = self.brain.audit()
            return {
                "command": "AUDIT",
                "status": "OK",
                "detail": self.operation_to_nrnlang("AUDIT", stats),
                "stats": stats,
            }

        elif cmd == "PRUNE":
            self.brain.soma.prune_weak_axons()
            return {
                "command": "PRUNE",
                "status": "OK",
                "detail": "Weak axons pruned -x-",
            }

        elif cmd == "WEAVE":
            # Manual weave — connect two engrams
            from core.soma import AxonRecord
            from_id = parsed["from_id"]
            to_id = parsed["to_id"]
            synapse = float(parsed.get("props", {}).get("synapse", 0.5))
            axon = AxonRecord(from_id=from_id, to_id=to_id, synapse=synapse)
            self.brain.soma.axons.append(axon)
            return {
                "command": "WEAVE",
                "status": "OK",
                "detail": f"Woven {from_id[:8]} <=> {to_id[:8]} syn:{synapse:.2f}",
            }

        return {
            "command": cmd,
            "status": "UNIMPLEMENTED",
            "detail": f"Command {cmd} not yet wired to brain",
        }

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # VALIDATE
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    def validate_syntax(self, nrn_text: str) -> list[dict]:
        """
        NRNLANG-Ω: VALIDATE syntax → list of errors

        Checks NRNLANG-Ω syntax and reports errors.
        Returns empty list if all valid.
        """
        errors = []

        for line_num, line in enumerate(nrn_text.split("\n"), 1):
            line = line.strip()

            # Skip comments and empty lines
            if not line or line.startswith("#"):
                continue

            # Skip PULSE markers
            if line.startswith("PULSE") or line.startswith("═"):
                continue

            # Check for known command
            has_keyword = False
            for kw in KEYWORDS:
                if line.startswith(kw) or line.startswith(f"⊕ {kw}") or \
                   line.startswith(f"^^ {kw}") or line.startswith(f"● {kw}") or \
                   line.startswith(f"## {kw}"):
                    has_keyword = True
                    break

            # Also allow ENGRAM blocks
            if line.startswith("ENGRAM") or line.startswith("{") or \
               line.startswith("}") or ":" in line:
                has_keyword = True

            # Allow NRNLANG-Ω symbols as standalone
            for sym_group in [EXISTENCE_SYMBOLS, FLOW_SYMBOLS,
                              COMPARISON_SYMBOLS, STRENGTH_SYMBOLS]:
                for _, sym in sym_group.items():
                    if line.startswith(sym):
                        has_keyword = True
                        break

            if not has_keyword:
                # Check for property-like lines inside blocks
                if re.match(r'\s*(id|raw|born|heat|spark|weight|decay|axons|'
                            r'truth|emotion|confidence|source|tags|last_seen|'
                            r'age|zone)\s*:', line):
                    has_keyword = True

            if not has_keyword:
                # Mismatched braces
                open_count = line.count("{") + line.count("[") + line.count("(")
                close_count = line.count("}") + line.count("]") + line.count(")")
                if open_count != close_count:
                    errors.append({
                        "line": line_num,
                        "text": line,
                        "error": "Mismatched brackets",
                    })
                else:
                    errors.append({
                        "line": line_num,
                        "text": line,
                        "error": "Unknown NRNLANG-Ω command or symbol",
                    })

        return errors

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # HELPERS
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    @staticmethod
    def _timestamp_to_nrn(ts: float) -> str:
        """Convert Unix timestamp to NRNLANG-Ω T[YYYY.MM.DD:HH:MM:SS] format."""
        if not ts or ts <= 0:
            return "T[unknown]"
        t = time.localtime(ts)
        return f"T[{t.tm_year}.{t.tm_mon:02d}.{t.tm_mday:02d}:{t.tm_hour:02d}:{t.tm_min:02d}:{t.tm_sec:02d}]"

    @staticmethod
    def _parse_props(props_str: str) -> dict:
        """Parse {key:value, key:value} property strings."""
        props = {}
        if not props_str:
            return props
        for part in props_str.split(","):
            part = part.strip()
            if ":" in part:
                key, val = part.split(":", 1)
                key = key.strip()
                val = val.strip()
                # Try numeric conversion
                try:
                    val = float(val)
                except ValueError:
                    pass
                props[key] = val
        return props


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# CLI ENTRY POINT
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def main():
    """Run NRNLANG-Ω interpreter from command line."""
    import sys

    if len(sys.argv) < 2:
        print("NRNLANG-Ω Interpreter")
        print("Usage: python utils/nrnlang.py <file.nrn>")
        print("       python utils/nrnlang.py --validate <file.nrn>")
        sys.exit(0)

    mode = "execute"
    filepath = sys.argv[1]

    if sys.argv[1] == "--validate":
        mode = "validate"
        filepath = sys.argv[2] if len(sys.argv) > 2 else None

    if not filepath:
        print("Error: No file specified")
        sys.exit(1)

    # Add project root to path
    import os
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    nrn = NRNLangInterpreter()

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
    except FileNotFoundError:
        print(f"Error: File not found: {filepath}")
        sys.exit(1)

    if mode == "validate":
        errors = nrn.validate_syntax(content)
        if not errors:
            print("✓ NRNLANG-Ω syntax is valid")
        else:
            print(f"✗ {len(errors)} syntax errors found:")
            for e in errors:
                print(f"  Line {e['line']}: {e['error']}")
                print(f"    → {e['text']}")
        sys.exit(len(errors))

    else:
        print("═══════════════════════════════════════")
        print("  NRNLANG-Ω Interpreter — Executing")
        print(f"  File: {filepath}")
        print("═══════════════════════════════════════")
        print()

        results = nrn.execute_nrn(content)
        for r in results:
            status = r.get("status", "?")
            cmd = r.get("command", "?")
            detail = r.get("detail", r.get("text", ""))
            line = r.get("line", "?")

            status_sym = "✓" if status == "OK" else (
                "○" if status == "DRY_RUN" else "?"
            )
            print(f"  [{status_sym}] L{line:3d} {cmd:12s} {detail}")

        print()
        print(f"  Total: {len(results)} commands processed")


if __name__ == "__main__":
    main()
