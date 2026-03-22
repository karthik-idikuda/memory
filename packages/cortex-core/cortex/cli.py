"""
╔══════════════════════════════════════════════════════════════╗
║  CORTEX-X Omega — Terminal Chat CLI                          ║
║  Interactive chat with full thought traces                   ║
╚══════════════════════════════════════════════════════════════╝

Usage: cortex  (or: python -m cortex.cli)
"""

from __future__ import annotations

import sys
import os
from pathlib import Path


BANNER = """
╔══════════════════════════════════════════════════════════════╗
║         CORTEX-X Omega v1.0.0 — Metacognitive AI Brain      ║
║         The AI that thinks about its own thinking            ║
╚══════════════════════════════════════════════════════════════╝
"""

HELP_TEXT = """
Commands:
  /stats    — Show brain statistics
  /trace    — Show last thought trace
  /metacog  — Show METACOG-X score breakdown
  /wisdom   — List crystallized wisdom axioms
  /patterns — Show active error patterns
  /growth   — Show growth trend
  /save     — Save brain to disk
  /export   — Export brain to JSON
  /help     — Show this help
  /quit     — Exit
"""


def main():
    """Main CLI entry point."""
    print(BANNER)

    # Determine brain path
    brain_name = os.environ.get("CORTEX_BRAIN", "brain")
    brain_path = f"{brain_name}.cortex"

    from cortex.engine.agent import CortexAgent
    from cortex.meta.metacog import metacog_breakdown

    agent = CortexAgent(
        brain_path=brain_path,
        adapter_name=os.environ.get("CORTEX_LLM", "ollama"),
        model=os.environ.get("CORTEX_MODEL", "llama3.2"),
    )

    # Try to load existing brain
    if Path(brain_path).exists():
        if agent.load():
            print(f"  🧠 Loaded brain: {brain_path}")
            print(f"     Thoughts: {agent.db.thought_count} | "
                  f"Wisdom: {agent.db.wisdom_count} | "
                  f"Session: #{agent.interaction_count}")
        else:
            print(f"  🧠 New brain: {brain_path}")
    else:
        print(f"  🧠 New brain: {brain_path}")

    print(f"  🔌 LLM: {agent.adapter_name}/{agent.model}")
    print(f"  Type /help for commands\n")

    while True:
        try:
            user_input = input("You: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\n\n  Saving brain...")
            agent.save()
            print("  Goodbye! 🧠")
            break

        if not user_input:
            continue

        # Handle commands
        if user_input.startswith("/"):
            _handle_command(user_input, agent)
            continue

        # Think!
        result = agent.think(user_input)

        # Display response with metacognitive overlay
        conf = result["confidence"]
        zone = result["zone"]
        total_ms = result["total_ms"]
        metacog = result["metacog"]

        print(f"\n  🧠 [{zone}] conf={conf:.0%} | "
              f"patterns={metacog['active_patterns']} | "
              f"wisdom={metacog['wisdom_count']} | "
              f"{total_ms:.0f}ms")
        print(f"\nCORTEX-X: {result['response']}")
        print(f"\n  {result['trace_compact']}\n")


def _handle_command(cmd: str, agent):
    """Handle slash commands."""
    cmd = cmd.lower().strip()

    if cmd == "/help":
        print(HELP_TEXT)

    elif cmd == "/stats":
        stats = agent.stats
        brain = stats["brain"]
        print(f"\n  📊 Brain Statistics:")
        print(f"     Thoughts: {brain['thought_count']}")
        print(f"     Edges: {brain['edge_count']}")
        print(f"     Strategies: {brain['strategy_count']}")
        print(f"     Wisdom: {brain['wisdom_count']}")
        print(f"     Zones: {brain['zones']}")
        print(f"     Interactions: {stats['interactions']}\n")

    elif cmd == "/trace":
        traces = agent.trace_logger.recent(1)
        if traces:
            print(f"\n{traces[0].format_detailed()}\n")
        else:
            print("  No traces yet.\n")

    elif cmd == "/metacog":
        from cortex.meta.metacog import metacog_breakdown
        bd = metacog_breakdown(
            calibration_score=agent.confidence.calibration_score,
            contradiction_score=agent.contradictions.contradiction_score,
            hallucination_score=agent.hallucination.hallucination_score,
            drift_score=agent.drift.drift_score,
            pattern_score=agent.patterns.pattern_score,
            wisdom_score=agent.wisdom.wisdom_ratio,
            strategy_score=agent.strategies.strategy_score,
        )
        print(f"\n  🧠 METACOG-X Score: {bd.total_score:.0%} ({bd.health_label})")
        for c in bd.components:
            bar = "█" * int(c.raw_value * 10) + "░" * (10 - int(c.raw_value * 10))
            print(f"     {c.name:30s} {bar} {c.raw_value:.0%}")
        if bd.recommendations:
            print(f"\n  Recommendations:")
            for r in bd.recommendations:
                print(f"     • {r}")
        print()

    elif cmd == "/wisdom":
        axioms = agent.wisdom.get_axioms()
        if axioms:
            print(f"\n  ◆ Crystallized Wisdom ({len(axioms)} axioms):")
            for a in axioms[:10]:
                print(f"     • [{a.domain}] {a.content[:80]} (conf: {a.confidence:.0%})")
        else:
            print("  No wisdom crystallized yet.\n")

    elif cmd == "/patterns":
        patterns = agent.patterns.get_active_patterns()
        if patterns:
            print(f"\n  ⟳ Active Error Patterns ({len(patterns)}):")
            for p in patterns[:10]:
                print(f"     • {p.error_type} in {p.context_type} "
                      f"(seen {p.frequency}x, strength: {p.strength:.1f})")
        else:
            print("  No active patterns.\n")

    elif cmd == "/growth":
        print(f"\n  {agent.growth.growth_symbol} Growth: {agent.growth.trend}")
        print(f"     Current score: {agent.growth.current_score:+.2%}")
        print(f"     Measurements: {agent.growth.total_measurements}\n")

    elif cmd == "/save":
        agent.save()
        print(f"  💾 Brain saved to {agent.brain_path}\n")

    elif cmd == "/export":
        from cortex.utils.exporter import export_json
        path = agent.brain_path.replace(".cortex", "_export.json")
        export_json(agent.db, path)
        print(f"  📤 Exported to {path}\n")

    elif cmd in ("/quit", "/exit", "/q"):
        agent.save()
        print("  Saving brain... Goodbye! 🧠")
        sys.exit(0)

    else:
        print(f"  Unknown command: {cmd}. Type /help.\n")


if __name__ == "__main__":
    main()
