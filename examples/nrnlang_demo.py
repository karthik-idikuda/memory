"""
NEURON-X Omega — NRNLANG-Ω Example

Demonstrates the NEURON-X symbolic language.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'packages', 'neuronx-core'))

from neuronx import NeuronBrain
from neuronx.language.nrnlang import NRNLangInterpreter


def main():
    brain = NeuronBrain("nrnlang_demo", data_dir="/tmp/neuronx_nrnlang")
    interp = NRNLangInterpreter(brain=brain)

    print("╔═══════════════════════════════════════╗")
    print("║  NRNLANG-Ω Interactive Demo            ║")
    print("╚═══════════════════════════════════════╝\n")

    # Script of commands
    script = """
FORGE engram("User prefers dark mode interfaces")
FORGE engram("User is learning quantum computing")
FORGE engram("User enjoys classical music")
RECALL query("What does user like?")
STATS brain()
AUDIT brain()
"""

    print("Executing NRNLANG-Ω script:\n")
    results = interp.execute_script(script)

    for r in results:
        log = r.get("log", str(r))
        print(f"  {log}")

    brain.end_session()
    print("\n✅ Done.")


if __name__ == "__main__":
    main()
