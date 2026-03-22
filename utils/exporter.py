"""
╔══════════════════════════════════════════════════════════╗
║  NEURON-X Omega — Export / Import Utilities              ║
║  Backup and share brain in human-readable formats        ║
╚══════════════════════════════════════════════════════════╝
"""

import json
import time
import os
import logging

from core.node import Engram
from core.integrity import generate_engram_id

logger = logging.getLogger("NEURONX.EXPORTER")


def export_json(brain, filepath: str) -> bool:
    """
    Export entire brain to a human-readable JSON file.

    Structure:
    {
        "neuronx_export": true,
        "exported_at": timestamp,
        "stats": {...},
        "engrams": [{...}, ...],
        "axons": [{...}, ...]
    }
    """
    try:
        data = {
            "neuronx_export": True,
            "version": 1,
            "exported_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "exported_timestamp": time.time(),
            "stats": brain.soma.get_stats(),
            "engrams": [e.to_dict() for e in brain.soma.engrams.values()],
            "axons": [a.to_dict() for a in brain.soma.axons],
        }

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        logger.info(f"Brain exported to {filepath}")
        return True

    except Exception as e:
        logger.error(f"Export failed: {e}")
        return False


def export_markdown(brain, filepath: str) -> bool:
    """
    Export brain as a human-readable markdown document.

    Useful for reviewing memories in a text editor or
    sharing with others (after privacy review).
    """
    try:
        stats = brain.soma.get_stats()
        lines = [
            "# 🧠 NEURON-X Brain Export",
            f"",
            f"**Exported:** {time.strftime('%Y-%m-%d %H:%M:%S')}",
            f"**Total Memories:** {stats['total_engrams']}",
            f"**Total Bonds:** {stats['total_axons']}",
            f"**Brain Age:** {stats['brain_age_days']:.0f} days",
            f"",
            "---",
            "",
        ]

        # Group by zone
        zones = {"H": "🔥 HOT", "W": "🌡 WARM", "C": "❄ COLD",
                 "S": "👻 SILENT", "A": "⚓ ANCHOR"}

        for zone_code, zone_name in zones.items():
            zone_engrams = [
                e for e in brain.soma.engrams.values() if e.zone == zone_code
            ]
            if not zone_engrams:
                continue

            lines.append(f"## {zone_name} Zone ({len(zone_engrams)} memories)")
            lines.append("")

            zone_engrams.sort(key=lambda e: e.last_seen, reverse=True)

            for e in zone_engrams:
                age = f"{e.age_days:.0f}"
                emotion_icons = {
                    "happy": "😊", "sad": "😢", "excited": "🤩",
                    "curious": "🤔", "angry": "😤", "neutral": "😐",
                    "love": "❤️", "fear": "😨",
                }
                emo = emotion_icons.get(e.emotion, "")
                tags_str = ", ".join(e.tags) if e.tags else ""

                lines.append(
                    f"- {emo} **{e.raw}** "
                    f"(conf: {e.confidence:.2f}, "
                    f"age: {age}d, "
                    f"class: {e.decay_class}"
                    f"{', tags: ' + tags_str if tags_str else ''})"
                )

            lines.append("")

        # Bonds section
        if brain.soma.axons:
            lines.append("## ⟷ Strongest Bonds")
            lines.append("")

            types = {0: "TIME", 1: "WORD", 2: "EMOTION", 3: "CLASH",
                     4: "REINFORCE", 5: "HERALD"}

            sorted_axons = sorted(
                brain.soma.axons, key=lambda a: a.synapse, reverse=True
            )[:20]

            for a in sorted_axons:
                from_e = brain.soma.get_engram(a.from_id)
                to_e = brain.soma.get_engram(a.to_id)
                from_text = from_e.raw[:40] if from_e else a.from_id[:8]
                to_text = to_e.raw[:40] if to_e else a.to_id[:8]
                t = types.get(a.axon_type, "?")

                lines.append(
                    f"- [{t}] {a.synapse:.3f}: "
                    f'"{from_text}" ⟷ "{to_text}"'
                )

            lines.append("")

        with open(filepath, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

        logger.info(f"Brain exported to {filepath} (markdown)")
        return True

    except Exception as e:
        logger.error(f"Markdown export failed: {e}")
        return False


def import_json(brain, filepath: str) -> dict:
    """
    Import memories from a JSON file into the brain.

    Handles:
    - NEURON-X export files (neuronx_export: true)
    - Simple JSON arrays of memory objects

    Returns: {"imported": count, "skipped": count, "errors": count}
    """
    result = {"imported": 0, "skipped": 0, "errors": 0}

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Determine format
        if isinstance(data, dict) and data.get("neuronx_export"):
            # NEURON-X export format
            engram_dicts = data.get("engrams", [])
        elif isinstance(data, list):
            # Simple array format
            engram_dicts = data
        else:
            logger.error("Unrecognized import format")
            result["errors"] = 1
            return result

        for ed in engram_dicts:
            try:
                if isinstance(ed, dict):
                    # Check if this engram already exists
                    eid = ed.get("id", "")
                    if eid and eid in brain.soma.engrams:
                        result["skipped"] += 1
                        continue

                    # If it has all engram fields, import directly
                    if "raw" in ed and "born" in ed:
                        engram = Engram.from_dict(ed)
                    elif "text" in ed:
                        # Simple format — create new engram
                        now = time.time()
                        engram = Engram(
                            id=generate_engram_id(ed["text"], now),
                            raw=ed["text"],
                            born=now,
                            last_seen=now,
                            valid_from=now,
                            decay_class=ed.get("decay_class", "fact"),
                            emotion=ed.get("emotion", "neutral"),
                            confidence=float(ed.get("confidence", 0.8)),
                            tags=ed.get("tags", []),
                        )
                    else:
                        result["errors"] += 1
                        continue

                    brain.soma.add_engram(engram)
                    result["imported"] += 1

            except Exception as e:
                logger.warning(f"Failed to import engram: {e}")
                result["errors"] += 1

        # Save after import
        if result["imported"] > 0:
            brain.soma.save()

        logger.info(
            f"Import complete: {result['imported']} imported, "
            f"{result['skipped']} skipped, {result['errors']} errors"
        )
        return result

    except Exception as e:
        logger.error(f"Import failed: {e}")
        result["errors"] += 1
        return result
