"""
╔══════════════════════════════════════════════════════════╗
║  NEURON-X Omega — Terminal Chat Interface                ║
║  NRNLANG-Ω: The human gateway to the neural brain        ║
╚══════════════════════════════════════════════════════════╝

Complete command set (13 commands):
  /help          — Show all commands
  /stats         — Brain statistics
  /memories      — Show recent 20 memories
  /search <q>    — Search memories
  /forget <id>   — Expire a memory by ID
  /bonds [id]    — Show bonds (all or for specific ID)
  /zone <zone>   — List memories in a zone
  /conflicts     — Show active contradictions
  /audit         — Run thermal audit
  /export        — Export brain to JSON
  /import <file> — Import memories from file
  /backup        — Manual backup
  /clear         — Clear screen
  /exit          — End session, save, quit
"""

import os
import sys
import time
import shutil

try:
    from colorama import init, Fore, Back, Style
    init(autoreset=True)
except ImportError:
    class _NoColor:
        def __getattr__(self, name):
            return ""
    Fore = _NoColor()
    Back = _NoColor()
    Style = _NoColor()

from brain.neuron import NeuronBrain


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# VISUAL CONSTANTS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

BANNER = f"""
{Fore.CYAN}╔══════════════════════════════════════════════════════════╗
║                                                          ║
║   {Fore.WHITE}███╗   ██╗███████╗██╗   ██╗██████╗  ██████╗ ███╗   ██╗{Fore.CYAN}  ║
║   {Fore.WHITE}████╗  ██║██╔════╝██║   ██║██╔══██╗██╔═══██╗████╗  ██║{Fore.CYAN}  ║
║   {Fore.WHITE}██╔██╗ ██║█████╗  ██║   ██║██████╔╝██║   ██║██╔██╗ ██║{Fore.CYAN}  ║
║   {Fore.WHITE}██║╚██╗██║██╔══╝  ██║   ██║██╔══██╗██║   ██║██║╚██╗██║{Fore.CYAN}  ║
║   {Fore.WHITE}██║ ╚████║███████╗╚██████╔╝██║  ██║╚██████╔╝██║ ╚████║{Fore.CYAN}  ║
║   {Fore.WHITE}╚═╝  ╚═══╝╚══════╝ ╚═════╝ ╚═╝  ╚═╝ ╚═════╝ ╚═╝  ╚═══╝{Fore.CYAN}  ║
║                                                          ║
║   {Fore.YELLOW}██╗  ██╗        ██████╗ ███╗   ███╗███████╗ ██████╗  █████╗{Fore.CYAN} ║
║   {Fore.YELLOW}╚██╗██╔╝       ██╔═══██╗████╗ ████║██╔════╝██╔════╝ ██╔══██╗{Fore.CYAN}║
║   {Fore.YELLOW} ╚███╔╝  █████╗██║   ██║██╔████╔██║█████╗  ██║  ███╗███████║{Fore.CYAN}║
║   {Fore.YELLOW} ██╔██╗  ╚════╝██║   ██║██║╚██╔╝██║██╔══╝  ██║   ██║██╔══██║{Fore.CYAN}║
║   {Fore.YELLOW}██╔╝ ██╗       ╚██████╔╝██║ ╚═╝ ██║███████╗╚██████╔╝██║  ██║{Fore.CYAN}║
║   {Fore.YELLOW}╚═╝  ╚═╝        ╚═════╝ ╚═╝     ╚═╝╚══════╝ ╚═════╝ ╚═╝  ╚═╝{Fore.CYAN}║
║                                                          ║
║   {Fore.MAGENTA}Self-Sovereign Permanent AI Memory System{Fore.CYAN}               ║
║   {Fore.GREEN}NRNLANG-Ω{Fore.CYAN} | {Fore.GREEN}SOMA-DB{Fore.CYAN} | {Fore.GREEN}NMP Protocol{Fore.CYAN}                       ║
║                                                          ║
╚══════════════════════════════════════════════════════════╝
"""

ZONE_COLORS = {
    "H": Fore.RED, "W": Fore.YELLOW, "C": Fore.CYAN,
    "S": Fore.BLUE, "A": Fore.MAGENTA,
}

EMOTION_ICONS = {
    "happy": "😊", "sad": "😢", "excited": "🤩", "curious": "🤔",
    "angry": "😤", "neutral": "😐", "love": "❤️", "fear": "😨",
}

ACTION_ICONS = {
    "ECHO": f"{Fore.GREEN}● ECHO{Style.RESET_ALL}",
    "FORGE": f"{Fore.YELLOW}⊕ FORGE{Style.RESET_ALL}",
    "CLASH": f"{Fore.RED}⚡ CLASH{Style.RESET_ALL}",
}

ZONE_DISPLAY = {
    "H": "🔥 HOT", "W": "🌡 WARM", "C": "❄ COLD",
    "S": "👻 SILENT", "A": "⚓ ANCHOR",
}


class ChatInterface:
    """Terminal chat interface for NEURON-X Omega. 13 commands + AI chat."""

    def __init__(self, brain: NeuronBrain):
        self.brain = brain

    def run(self):
        """Main chat loop."""
        print(BANNER)
        self._show_brain_status_mini()
        print(
            f"\n{Fore.GREEN}Type anything to chat. "
            f"Use {Fore.YELLOW}/help{Fore.GREEN} for commands. "
            f"{Fore.RED}/exit{Fore.GREEN} to quit.{Style.RESET_ALL}\n"
        )

        self.brain.start_pulse()

        try:
            while True:
                try:
                    user_input = input(
                        f"{Fore.CYAN}YOU ▸ {Style.RESET_ALL}"
                    ).strip()
                except EOFError:
                    break

                if not user_input:
                    continue

                # Check for commands
                if user_input.startswith("/"):
                    should_quit = self._handle_command(user_input)
                    if should_quit:
                        break
                    continue

                # Chat with brain
                self._process_message(user_input)

        except KeyboardInterrupt:
            print(f"\n{Fore.YELLOW}Interrupted!{Style.RESET_ALL}")

        finally:
            self.brain.end_pulse()
            print(f"\n{Fore.GREEN}🧠 Brain saved. Goodbye!{Style.RESET_ALL}")

    def _process_message(self, message: str):
        """Process a user message through the brain."""
        print(f"{Fore.BLUE}  ⟳ Processing memories...{Style.RESET_ALL}", end="\r")

        # Process input (stores memories)
        results = self.brain.process_input(message)

        # Show what happened to memories
        self._show_memory_actions(results)

        # Get AI response
        response = self.brain.chat(message)

        # Display response
        print(f"\n{Fore.GREEN}AI ▸ {Style.RESET_ALL}{response}\n")

    def _show_memory_actions(self, results: list[dict]):
        """Show what happened to each processed idea."""
        if not results:
            return

        print(f"  {Fore.BLUE}╭─ Memory Activity ─────────────────────{Style.RESET_ALL}")
        for r in results:
            action = ACTION_ICONS.get(r["action"], r["action"])
            emo = EMOTION_ICONS.get(r.get("emotion", "neutral"), "")
            surprise = r.get("surprise", 0)

            spark = ""
            if surprise > 0.85:
                spark = f" {Fore.RED}⚡{surprise:.2f}{Style.RESET_ALL}"
            elif surprise > 0.5:
                spark = f" {Fore.YELLOW}☆{surprise:.2f}{Style.RESET_ALL}"

            text = r["text"][:50] + ("…" if len(r["text"]) > 50 else "")
            clash_info = ""
            if r.get("clash_result"):
                clash_info = f" → {Fore.RED}{r['clash_result']}{Style.RESET_ALL}"

            print(
                f"  {Fore.BLUE}│{Style.RESET_ALL} {action} {emo} "
                f'"{text}"{spark}{clash_info}'
            )

        print(f"  {Fore.BLUE}╰────────────────────────────────────────{Style.RESET_ALL}")

    def _handle_command(self, cmd: str) -> bool:
        """
        Handle slash commands. Returns True if should quit.

        Supports all 13 spec commands:
        /help, /stats, /audit, /memories, /search, /forget,
        /conflicts, /bonds, /zone, /export, /import, /backup, /clear, /exit
        """
        parts = cmd.strip().split(maxsplit=1)
        command = parts[0].lower()
        arg = parts[1] if len(parts) > 1 else ""

        if command in ("/quit", "/exit"):
            return True

        elif command == "/help":
            self._show_help()

        elif command == "/stats":
            self._show_stats()

        elif command == "/memories":
            self._show_memories()

        elif command == "/search":
            if arg:
                self._search_memories(arg)
            else:
                print(f"  {Fore.YELLOW}Usage: /search <query>{Style.RESET_ALL}")

        elif command == "/forget":
            if arg:
                self._forget_memory(arg)
            else:
                print(f"  {Fore.YELLOW}Usage: /forget <engram_id>{Style.RESET_ALL}")

        elif command == "/bonds":
            if arg:
                self._show_bonds_for(arg)
            else:
                self._show_bonds()

        elif command == "/zone":
            if arg:
                zone_map = {
                    "hot": "H", "warm": "W", "cold": "C",
                    "silent": "S", "anchor": "A",
                    "h": "H", "w": "W", "c": "C", "s": "S", "a": "A",
                }
                zone = zone_map.get(arg.lower(), arg.upper())
                self._show_zone(zone)
            else:
                self._show_zone_distribution()

        elif command == "/conflicts":
            self._show_conflicts()

        elif command == "/audit":
            self._run_audit()

        elif command == "/export":
            self._export_brain()

        elif command == "/import":
            if arg:
                self._import_memories(arg)
            else:
                print(f"  {Fore.YELLOW}Usage: /import <filepath>{Style.RESET_ALL}")

        elif command == "/backup":
            self._manual_backup()

        elif command == "/clear":
            os.system("clear" if os.name != "nt" else "cls")

        elif command == "/save":
            self.brain.soma.save()
            print(f"  {Fore.GREEN}✓ Brain saved to SOMA file{Style.RESET_ALL}")

        elif command == "/nrn":
            self._handle_nrn_command(arg)

        # Legacy zone shortcuts
        elif command in ("/hot", "/warm", "/cold", "/silent"):
            zone_map = {"/hot": "H", "/warm": "W", "/cold": "C", "/silent": "S"}
            self._show_zone(zone_map[command])

        elif command == "/zones":
            self._show_zone_distribution()

        else:
            print(
                f"  {Fore.RED}Unknown command: {command}. "
                f"Type /help for available commands.{Style.RESET_ALL}"
            )

        return False

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # Command Implementations
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    def _show_help(self):
        """Show available commands."""
        print(f"""
{Fore.CYAN}╔══ NEURON-X Commands ═══════════════════════════╗{Style.RESET_ALL}
{Fore.CYAN}║{Style.RESET_ALL}  {Fore.YELLOW}/help{Style.RESET_ALL}           Show this help message
{Fore.CYAN}║{Style.RESET_ALL}  {Fore.YELLOW}/stats{Style.RESET_ALL}          Brain statistics overview
{Fore.CYAN}║{Style.RESET_ALL}  {Fore.YELLOW}/memories{Style.RESET_ALL}        Show recent 20 memories
{Fore.CYAN}║{Style.RESET_ALL}  {Fore.YELLOW}/search <query>{Style.RESET_ALL}  Search memories, show top 10
{Fore.CYAN}║{Style.RESET_ALL}  {Fore.YELLOW}/forget <id>{Style.RESET_ALL}     Expire a memory by ID
{Fore.CYAN}║{Style.RESET_ALL}  {Fore.YELLOW}/bonds [id]{Style.RESET_ALL}      Show bonds (all or for ID)
{Fore.CYAN}║{Style.RESET_ALL}  {Fore.YELLOW}/zone <zone>{Style.RESET_ALL}     List memories in HOT/WARM/COLD/SILENT
{Fore.CYAN}║{Style.RESET_ALL}  {Fore.YELLOW}/conflicts{Style.RESET_ALL}       Show active contradictions
{Fore.CYAN}║{Style.RESET_ALL}  {Fore.YELLOW}/audit{Style.RESET_ALL}           Run thermal zone audit
{Fore.CYAN}║{Style.RESET_ALL}  {Fore.YELLOW}/export{Style.RESET_ALL}          Export brain to JSON file
{Fore.CYAN}║{Style.RESET_ALL}  {Fore.YELLOW}/import <file>{Style.RESET_ALL}   Import memories from JSON
{Fore.CYAN}║{Style.RESET_ALL}  {Fore.YELLOW}/backup{Style.RESET_ALL}          Manual backup of .soma file
{Fore.CYAN}║{Style.RESET_ALL}  {Fore.YELLOW}/clear{Style.RESET_ALL}           Clear terminal screen
{Fore.CYAN}║{Style.RESET_ALL}  {Fore.YELLOW}/exit{Style.RESET_ALL}            End session and quit
{Fore.CYAN}║{Style.RESET_ALL}
{Fore.CYAN}║{Style.RESET_ALL}  {Fore.MAGENTA}── NRNLANG-Ω Commands ──{Style.RESET_ALL}
{Fore.CYAN}║{Style.RESET_ALL}  {Fore.YELLOW}/nrn <id>{Style.RESET_ALL}        Show engram in NRNLANG-Ω notation
{Fore.CYAN}║{Style.RESET_ALL}  {Fore.YELLOW}/nrn session{Style.RESET_ALL}     Show session as NRNLANG-Ω script
{Fore.CYAN}║{Style.RESET_ALL}  {Fore.YELLOW}/nrn brain{Style.RESET_ALL}       Export brain in NRNLANG-Ω
{Fore.CYAN}║{Style.RESET_ALL}  {Fore.YELLOW}/nrn run <file>{Style.RESET_ALL}  Execute .nrn script
{Fore.CYAN}║{Style.RESET_ALL}  {Fore.YELLOW}/nrn validate{Style.RESET_ALL}    Validate NRNLANG-Ω syntax
{Fore.CYAN}╚════════════════════════════════════════════════╝{Style.RESET_ALL}
""")

    def _show_brain_status_mini(self):
        """Show compact brain status at startup."""
        stats = self.brain.get_brain_stats()
        total = stats["total_engrams"]
        axons = stats["total_axons"]
        size = stats["file_size_kb"]

        if total == 0:
            print(
                f"  {Fore.YELLOW}🧠 Empty brain — "
                f"start talking to build memories!{Style.RESET_ALL}"
            )
        else:
            print(
                f"  {Fore.GREEN}🧠 Brain loaded — "
                f"{total} memories, {axons} bonds, "
                f"{size:.1f} KB{Style.RESET_ALL}"
            )

    def _show_stats(self):
        """Show detailed brain statistics."""
        stats = self.brain.get_brain_stats()

        print(f"""
{Fore.CYAN}╔══ Brain Statistics ════════════════════════════╗{Style.RESET_ALL}
{Fore.CYAN}║{Style.RESET_ALL}  Total Engrams:    {Fore.WHITE}{stats['total_engrams']}{Style.RESET_ALL}
{Fore.CYAN}║{Style.RESET_ALL}  {Fore.RED}[H] HOT:{Style.RESET_ALL}          {stats['hot_count']}
{Fore.CYAN}║{Style.RESET_ALL}  {Fore.YELLOW}[W] WARM:{Style.RESET_ALL}         {stats['warm_count']}
{Fore.CYAN}║{Style.RESET_ALL}  {Fore.CYAN}[C] COLD:{Style.RESET_ALL}         {stats['cold_count']}
{Fore.CYAN}║{Style.RESET_ALL}  {Fore.BLUE}[S] SILENT:{Style.RESET_ALL}       {stats['silent_count']}
{Fore.CYAN}║{Style.RESET_ALL}  Total Axons:      {Fore.WHITE}{stats['total_axons']}{Style.RESET_ALL}
{Fore.CYAN}║{Style.RESET_ALL}  Conflicts:        {Fore.RED if stats['conflict_count'] > 0 else Fore.GREEN}{stats['conflict_count']}{Style.RESET_ALL}
{Fore.CYAN}║{Style.RESET_ALL}  Anchors:          {Fore.MAGENTA}{stats['anchor_count']}{Style.RESET_ALL}
{Fore.CYAN}║{Style.RESET_ALL}  File Size:        {stats['file_size_kb']:.1f} KB
{Fore.CYAN}║{Style.RESET_ALL}  Save Count:       #{stats['save_count']}
{Fore.CYAN}║{Style.RESET_ALL}  Brain Age:        {stats['brain_age_days']:.0f} days
{Fore.CYAN}║{Style.RESET_ALL}  Last Saved:       {stats['last_saved']}
{Fore.CYAN}╚════════════════════════════════════════════════╝{Style.RESET_ALL}""")

        if stats["top_hot"]:
            print(f"\n  {Fore.RED}🔥 Hottest Memories:{Style.RESET_ALL}")
            for m in stats["top_hot"]:
                print(f"    {Fore.RED}■{Style.RESET_ALL} [{m['heat']:.2f}] {m['raw']}")

        if stats["top_bonds"]:
            print(f"\n  {Fore.YELLOW}⟷ Strongest Bonds:{Style.RESET_ALL}")
            for b in stats["top_bonds"]:
                print(
                    f"    {Fore.YELLOW}═{Style.RESET_ALL} "
                    f"{b['from']}…⟷{b['to']}… syn={b['synapse']:.3f}"
                )

        print()

    def _show_memories(self, limit: int = 20):
        """Show recent memories."""
        memories = self.brain.get_all_memories(limit=limit)

        if not memories:
            print(f"  {Fore.YELLOW}No memories stored yet.{Style.RESET_ALL}")
            return

        print(f"\n  {Fore.GREEN}📝 Recent Memories ({len(memories)}):{Style.RESET_ALL}")
        for e in memories:
            zc = ZONE_COLORS.get(e.zone, "")
            emo = EMOTION_ICONS.get(e.emotion, "")
            zone_name = ZONE_DISPLAY.get(e.zone, e.zone)
            age = f"{e.age_days:.0f}"
            print(
                f"    [{zone_name} {e.heat:.2f}] {emo} "
                f'"{e.raw[:50]}{"…" if len(e.raw) > 50 else ""}" '
                f"{Fore.BLUE}(conf:{e.confidence:.2f}, {age}d ago){Style.RESET_ALL}"
            )
        print()

    def _search_memories(self, query: str, top_k: int = 10):
        """Search memories using WSRA-X and show results."""
        results = self.brain.recall(query, top_k=top_k)

        if not results:
            print(f"  {Fore.YELLOW}No matching memories found.{Style.RESET_ALL}")
            return

        print(f"\n  {Fore.GREEN}🔍 Search Results for \"{query}\" ({len(results)}):{Style.RESET_ALL}")
        for i, (engram, score) in enumerate(results, 1):
            zc = ZONE_COLORS.get(engram.zone, "")
            zone_name = ZONE_DISPLAY.get(engram.zone, engram.zone)
            emo = EMOTION_ICONS.get(engram.emotion, "")
            age = f"{engram.age_days:.0f}"
            print(
                f"    {i:2d}. [{zone_name} {score:.2f}] {emo} "
                f'"{engram.raw[:45]}{"…" if len(engram.raw) > 45 else ""}" '
                f"{Fore.BLUE}(conf:{engram.confidence:.2f}, {age}d ago){Style.RESET_ALL}"
            )
            print(f"        {Fore.BLUE}ID: {engram.id}{Style.RESET_ALL}")
        print()

    def _forget_memory(self, engram_id: str):
        """Expire a memory by ID."""
        engram = self.brain.soma.get_engram(engram_id)
        if not engram:
            # Try partial match
            matches = [
                eid for eid in self.brain.soma.engrams
                if eid.startswith(engram_id)
            ]
            if len(matches) == 1:
                engram = self.brain.soma.get_engram(matches[0])
            elif len(matches) > 1:
                print(f"  {Fore.YELLOW}Multiple matches:{Style.RESET_ALL}")
                for m in matches:
                    e = self.brain.soma.get_engram(m)
                    print(f"    {m}: \"{e.raw[:40]}…\"")
                return
            else:
                print(f"  {Fore.RED}Engram not found: {engram_id}{Style.RESET_ALL}")
                return

        old_raw = engram.raw[:50]
        engram.expire()
        engram.zone = "C"
        self.brain.soma.save()
        print(
            f"  {Fore.YELLOW}✓ Expired: \"{old_raw}…\"{Style.RESET_ALL}\n"
            f"    {Fore.BLUE}(Memory preserved in history, marked as expired){Style.RESET_ALL}"
        )

    def _show_bonds(self):
        """Show strongest bonds overall."""
        from utils.visualizer import visualize_bonds
        visualize_bonds(self.brain)

    def _show_bonds_for(self, engram_id: str):
        """Show bonds for a specific engram."""
        # Try partial match
        if engram_id not in self.brain.soma.engrams:
            matches = [
                eid for eid in self.brain.soma.engrams
                if eid.startswith(engram_id)
            ]
            if len(matches) == 1:
                engram_id = matches[0]
            else:
                print(f"  {Fore.RED}Engram not found: {engram_id}{Style.RESET_ALL}")
                return

        from utils.visualizer import visualize_bonds
        visualize_bonds(self.brain, engram_id=engram_id)

    def _show_zone(self, zone: str):
        """Show memories in a specific zone."""
        memories = self.brain.get_all_memories(zone=zone, limit=20)
        zone_name = ZONE_DISPLAY.get(zone, zone)

        if not memories:
            print(f"  {Fore.YELLOW}No memories in {zone_name} zone.{Style.RESET_ALL}")
            return

        zc = ZONE_COLORS.get(zone, "")
        print(f"\n  {zc}{zone_name} Zone ({len(memories)} memories):{Style.RESET_ALL}")
        for e in memories:
            emo = EMOTION_ICONS.get(e.emotion, "")
            print(
                f"    {zc}■{Style.RESET_ALL} {emo} {e.raw[:55]} "
                f"{Fore.BLUE}(heat={e.heat:.2f}, wt={e.weight:.1f}, id={e.id[:8]}…){Style.RESET_ALL}"
            )
        print()

    def _show_zone_distribution(self):
        """Show zone distribution as visual bars."""
        stats = self.brain.get_brain_stats()
        total = max(1, stats["total_engrams"])

        zones = [
            ("H", "HOT   ", stats["hot_count"], Fore.RED),
            ("W", "WARM  ", stats["warm_count"], Fore.YELLOW),
            ("C", "COLD  ", stats["cold_count"], Fore.CYAN),
            ("S", "SILENT", stats["silent_count"], Fore.BLUE),
        ]

        print(f"\n  {Fore.GREEN}📊 Zone Distribution:{Style.RESET_ALL}")
        for code, name, count, color in zones:
            pct = (count / total) * 100
            bar_len = int(pct / 2)
            bar = "█" * bar_len
            print(
                f"    {color}[{code}] {name} {bar} "
                f"{count} ({pct:.0f}%){Style.RESET_ALL}"
            )
        print()

    def _show_conflicts(self):
        """Show active contradictions."""
        conflicts = self.brain.get_active_conflicts()

        if not conflicts:
            print(f"  {Fore.GREEN}✓ No active contradictions.{Style.RESET_ALL}")
            return

        print(f"\n  {Fore.RED}⚠ Active Contradictions ({len(conflicts)}):{Style.RESET_ALL}")
        for a, b in conflicts:
            print(f"    {Fore.RED}⚡{Style.RESET_ALL}")
            print(
                f"       {a.truth} {a.raw[:45]} "
                f"{Fore.BLUE}(conf={a.confidence:.2f}){Style.RESET_ALL}"
            )
            print(
                f"       {b.truth} {b.raw[:45]} "
                f"{Fore.BLUE}(conf={b.confidence:.2f}){Style.RESET_ALL}"
            )
        print()

    def _run_audit(self):
        """Run thermal audit."""
        print(f"  {Fore.BLUE}⟳ Running thermal audit...{Style.RESET_ALL}")
        stats = self.brain.audit()
        print(f"""
  {Fore.GREEN}✓ Audit Complete:{Style.RESET_ALL}
    Promoted (→ hotter):  {Fore.GREEN}{stats['promoted']}{Style.RESET_ALL}
    Demoted (→ colder):   {Fore.YELLOW}{stats['demoted']}{Style.RESET_ALL}
    Reawakened (ghosts):  {Fore.MAGENTA}{stats['reawakened']}{Style.RESET_ALL}
    Fossilized:           {Fore.BLUE}{stats['fossilized']}{Style.RESET_ALL}
    Crystallized:         {Fore.MAGENTA}{stats['crystallized']}{Style.RESET_ALL}

    Zone Counts:
    {Fore.RED}[H] {stats['zone_counts']['H']}{Style.RESET_ALL}  \
{Fore.YELLOW}[W] {stats['zone_counts']['W']}{Style.RESET_ALL}  \
{Fore.CYAN}[C] {stats['zone_counts']['C']}{Style.RESET_ALL}  \
{Fore.BLUE}[S] {stats['zone_counts']['S']}{Style.RESET_ALL}  \
{Fore.MAGENTA}[A] {stats['zone_counts']['A']}{Style.RESET_ALL}
""")

    def _export_brain(self):
        """Export brain to JSON file."""
        from utils.exporter import export_json

        export_dir = os.path.dirname(self.brain.soma.filepath) or "."
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        filepath = os.path.join(export_dir, f"brain_export_{timestamp}.json")

        if export_json(self.brain, filepath):
            print(f"  {Fore.GREEN}✓ Brain exported to: {filepath}{Style.RESET_ALL}")
        else:
            print(f"  {Fore.RED}✗ Export failed.{Style.RESET_ALL}")

    def _import_memories(self, filepath: str):
        """Import memories from a JSON file."""
        if not os.path.exists(filepath):
            print(f"  {Fore.RED}File not found: {filepath}{Style.RESET_ALL}")
            return

        from utils.exporter import import_json

        result = import_json(self.brain, filepath)
        print(
            f"  {Fore.GREEN}✓ Import complete: "
            f"{result['imported']} imported, "
            f"{result['skipped']} skipped, "
            f"{result['errors']} errors{Style.RESET_ALL}"
        )

    def _manual_backup(self):
        """Manually trigger a .soma.bak backup."""
        if os.path.exists(self.brain.soma.filepath):
            backup_path = self.brain.soma.backup_path
            shutil.copy2(self.brain.soma.filepath, backup_path)
            size = os.path.getsize(backup_path) / 1024
            print(
                f"  {Fore.GREEN}✓ Backup created: {backup_path} "
                f"({size:.1f} KB){Style.RESET_ALL}"
            )
        else:
            print(f"  {Fore.YELLOW}No .soma file to backup yet.{Style.RESET_ALL}")

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # NRNLANG-Ω Commands
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    def _handle_nrn_command(self, arg: str):
        """
        NRNLANG-Ω: /nrn command handler

        /nrn <id>        → show engram in NRNLANG-Ω notation
        /nrn session     → show session as NRNLANG-Ω script
        /nrn brain       → export brain as NRNLANG-Ω document
        /nrn run <file>  → execute .nrn script
        /nrn validate    → validate NRNLANG-Ω syntax
        """
        from utils.nrnlang import NRNLangInterpreter

        nrn = NRNLangInterpreter(self.brain)

        if not arg:
            print(f"""
{Fore.MAGENTA}╔══ NRNLANG-Ω Commands ══════════════════════════╗{Style.RESET_ALL}
{Fore.MAGENTA}║{Style.RESET_ALL}  /nrn <id>        Show engram in NRNLANG-Ω
{Fore.MAGENTA}║{Style.RESET_ALL}  /nrn session     Session as NRNLANG-Ω script
{Fore.MAGENTA}║{Style.RESET_ALL}  /nrn brain       Full brain export
{Fore.MAGENTA}║{Style.RESET_ALL}  /nrn run <file>  Execute .nrn script
{Fore.MAGENTA}║{Style.RESET_ALL}  /nrn validate    Validate syntax
{Fore.MAGENTA}╚════════════════════════════════════════════════╝{Style.RESET_ALL}
""")
            return

        parts = arg.strip().split(maxsplit=1)
        subcmd = parts[0].lower()
        subarg = parts[1] if len(parts) > 1 else ""

        if subcmd == "session":
            # Show current session as NRNLANG-Ω
            session_log = getattr(self.brain, 'session_log', [])
            if not session_log:
                print(f"  {Fore.YELLOW}No session activity yet.{Style.RESET_ALL}")
                return
            output = nrn.session_to_nrnlang(session_log)
            print(f"\n{Fore.MAGENTA}{output}{Style.RESET_ALL}\n")

        elif subcmd == "brain":
            # Export entire brain as NRNLANG-Ω
            output = nrn.brain_to_nrnlang()
            print(f"\n{Fore.MAGENTA}{output}{Style.RESET_ALL}\n")

        elif subcmd == "run":
            # Execute a .nrn file
            if not subarg:
                print(f"  {Fore.YELLOW}Usage: /nrn run <file.nrn>{Style.RESET_ALL}")
                return
            if not os.path.exists(subarg):
                print(f"  {Fore.RED}File not found: {subarg}{Style.RESET_ALL}")
                return
            print(f"  {Fore.BLUE}⟳ Executing {subarg}...{Style.RESET_ALL}\n")
            results = nrn.parse_nrn_file(subarg)
            for r in results:
                status = r.get("status", "?")
                cmd = r.get("command", "?")
                detail = r.get("detail", r.get("text", ""))
                status_sym = f"{Fore.GREEN}✓{Style.RESET_ALL}" if status == "OK" else (
                    f"{Fore.YELLOW}○{Style.RESET_ALL}" if status == "DRY_RUN" else "?"
                )
                print(f"  {status_sym} {cmd:12s} {detail}")
            print(f"\n  {Fore.GREEN}Done: {len(results)} commands{Style.RESET_ALL}")

        elif subcmd == "validate":
            # Validate NRNLANG-Ω syntax from stdin or last session
            session_log = getattr(self.brain, 'session_log', [])
            if session_log:
                nrn_text = nrn.session_to_nrnlang(session_log)
            else:
                nrn_text = nrn.brain_to_nrnlang()
            errors = nrn.validate_syntax(nrn_text)
            if not errors:
                print(f"  {Fore.GREEN}✓ NRNLANG-Ω syntax is valid{Style.RESET_ALL}")
            else:
                print(f"  {Fore.RED}✗ {len(errors)} errors:{Style.RESET_ALL}")
                for e in errors[:10]:
                    print(f"    L{e['line']}: {e['error']}")

        else:
            # Treat as engram ID
            engram_id = subcmd
            # Try exact match first
            engram = self.brain.soma.get_engram(engram_id)
            if not engram:
                # Try partial match
                matches = [
                    eid for eid in self.brain.soma.engrams
                    if eid.startswith(engram_id)
                ]
                if len(matches) == 1:
                    engram = self.brain.soma.get_engram(matches[0])
                elif len(matches) > 1:
                    print(f"  {Fore.YELLOW}Multiple matches:{Style.RESET_ALL}")
                    for m in matches:
                        e = self.brain.soma.get_engram(m)
                        print(f"    {m}: \"{e.raw[:40]}…\"")
                    return
                else:
                    print(f"  {Fore.RED}Engram not found: {engram_id}{Style.RESET_ALL}")
                    return

            # Show in NRNLANG-Ω notation
            output = nrn.engram_to_nrnlang(engram)
            print(f"\n{Fore.MAGENTA}{output}{Style.RESET_ALL}\n")

