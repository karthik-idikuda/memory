"""
╔══════════════════════════════════════════════════════════╗
║  NEURON-X Omega — Terminal Visualizer                    ║
║  Shows engram network and bonds in terminal              ║
╚══════════════════════════════════════════════════════════╝
"""

import time

try:
    from colorama import Fore, Style
except ImportError:
    class _NoColor:
        def __getattr__(self, name):
            return ""
    Fore = _NoColor()
    Style = _NoColor()


ZONE_ICONS = {
    "H": "🔥", "W": "🌡", "C": "❄", "S": "👻", "A": "⚓",
}

ZONE_COLORS = {
    "H": Fore.RED, "W": Fore.YELLOW, "C": Fore.CYAN,
    "S": Fore.BLUE, "A": Fore.MAGENTA,
}


def visualize_top_memories(brain, limit: int = 20):
    """
    Print the top N memories with zone, confidence, and heat.

    Format per memory:
    🔥 [H] 0.94 "user loves building AI systems" (conf:0.92, 3d ago)
    """
    engrams = sorted(
        brain.soma.engrams.values(),
        key=lambda e: e.heat,
        reverse=True,
    )[:limit]

    if not engrams:
        print(f"  {Fore.YELLOW}No memories to visualize.{Style.RESET_ALL}")
        return

    print(f"\n  {Fore.GREEN}🧠 Top {len(engrams)} Memories:{Style.RESET_ALL}")
    print(f"  {'─' * 65}")

    for e in engrams:
        icon = ZONE_ICONS.get(e.zone, "?")
        color = ZONE_COLORS.get(e.zone, "")
        age = f"{e.age_days:.0f}"
        raw = e.raw[:45] + ("…" if len(e.raw) > 45 else "")

        print(
            f"  {icon} {color}[{e.zone}]{Style.RESET_ALL} "
            f"{e.heat:.2f} "
            f'"{raw}" '
            f"{Fore.BLUE}(conf:{e.confidence:.2f}, {age}d){Style.RESET_ALL}"
        )

    print(f"  {'─' * 65}\n")


def visualize_bonds(brain, engram_id: str = None, limit: int = 15):
    """
    Visualize bonds either for a specific engram or the strongest overall.

    Shows connection strength as a bar chart:
    ████████████░░░░░░░░ 0.670 [WORD] "loves pizza" ⟷ "Italian food"
    """
    types = {0: "TIME", 1: "WORD", 2: "EMO", 3: "CLASH", 4: "REINF", 5: "HERALD"}

    if engram_id:
        # Show bonds for specific engram
        axons = brain.soma.get_axons_for(engram_id)
        engram = brain.soma.get_engram(engram_id)
        if not engram:
            print(f"  {Fore.RED}Engram {engram_id} not found.{Style.RESET_ALL}")
            return
        if not axons:
            print(f"  {Fore.YELLOW}No bonds for this engram.{Style.RESET_ALL}")
            return

        print(f"\n  {Fore.YELLOW}⟷ Bonds for: \"{engram.raw[:40]}…\"{Style.RESET_ALL}")
        axons = sorted(axons, key=lambda a: a.synapse, reverse=True)[:limit]
    else:
        # Show strongest overall bonds
        axons = sorted(brain.soma.axons, key=lambda a: a.synapse, reverse=True)[:limit]
        if not axons:
            print(f"  {Fore.YELLOW}No bonds formed yet.{Style.RESET_ALL}")
            return
        print(f"\n  {Fore.YELLOW}⟷ Strongest Bonds ({len(axons)}):{Style.RESET_ALL}")

    print(f"  {'─' * 65}")

    for a in axons:
        bar_len = int(a.synapse * 20)
        bar = "█" * bar_len + "░" * (20 - bar_len)
        t = types.get(a.axon_type, "?")

        from_e = brain.soma.get_engram(a.from_id)
        to_e = brain.soma.get_engram(a.to_id)
        from_text = from_e.raw[:20] if from_e else a.from_id[:8]
        to_text = to_e.raw[:20] if to_e else a.to_id[:8]

        print(
            f"  {Fore.YELLOW}{bar}{Style.RESET_ALL} "
            f"{a.synapse:.3f} [{t:6s}] "
            f'"{from_text}…" ⟷ "{to_text}…"'
        )

    print(f"  {'─' * 65}\n")


def visualize_network_map(brain, limit: int = 10):
    """
    Print a text-based network map showing connected clusters.

    ⊕ "user loves pizza" (H, 0.94)
       ├── 0.67 ── "Italian food"
       ├── 0.45 ── "cooking hobby"
       └── 0.23 ── "restaurant visit"
    """
    engrams = sorted(
        brain.soma.engrams.values(),
        key=lambda e: len(e.axons),
        reverse=True,
    )[:limit]

    if not engrams:
        print(f"  {Fore.YELLOW}No network to visualize.{Style.RESET_ALL}")
        return

    print(f"\n  {Fore.GREEN}🕸 Network Map (most connected):{Style.RESET_ALL}")
    print(f"  {'─' * 65}")

    for e in engrams:
        icon = ZONE_ICONS.get(e.zone, "?")
        color = ZONE_COLORS.get(e.zone, "")

        print(
            f"  {icon} {color}⊕ \"{e.raw[:40]}…\" "
            f"({e.zone}, {e.heat:.2f}){Style.RESET_ALL}"
        )

        # Sort connections by strength
        sorted_axons = sorted(
            e.axons.items(), key=lambda x: x[1], reverse=True
        )[:5]

        for i, (target_id, synapse) in enumerate(sorted_axons):
            is_last = i == len(sorted_axons) - 1
            connector = "└──" if is_last else "├──"
            target = brain.soma.get_engram(target_id)
            target_text = target.raw[:30] if target else target_id[:8]

            bar_len = int(synapse * 10)
            bar = "█" * bar_len

            print(
                f"       {connector} {Fore.YELLOW}{bar}{Style.RESET_ALL} "
                f"{synapse:.2f} ── \"{target_text}…\""
            )

        if not sorted_axons:
            print(f"       └── (no connections)")

    print(f"  {'─' * 65}\n")
