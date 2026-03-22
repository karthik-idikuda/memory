"""
NEURON-X Omega CLI — Command-line interface.

Usage:
  neuronx remember "I love pizza"
  neuronx recall "What food?"
  neuronx stats
  neuronx audit
  neuronx export json output.json
  neuronx nrnlang 'FORGE engram("test")'
"""

import sys
import json


def main():
    from neuronx.brain.neuron import NeuronBrain

    args = sys.argv[1:]
    if not args:
        print("NEURON-X Omega CLI v1.0.0")
        print("Commands: remember, recall, stats, audit, export, nrnlang")
        return

    brain = NeuronBrain()
    cmd = args[0]

    if cmd == "remember" and len(args) > 1:
        result = brain.remember(" ".join(args[1:]))
        print(f"{result.action} → {result.engram_id[:8]}… (surprise={result.surprise_score:.2f})")

    elif cmd == "recall" and len(args) > 1:
        results = brain.recall(" ".join(args[1:]))
        for i, (e, score) in enumerate(results, 1):
            print(f"  [{i}] [{e.zone[0]}] {e.raw} (score={score:.3f})")

    elif cmd == "stats":
        stats = brain.get_stats()
        print(json.dumps(stats, indent=2))

    elif cmd == "audit":
        stats = brain.run_audit()
        print(json.dumps(stats, indent=2, default=str))

    elif cmd == "export" and len(args) > 1:
        fmt = args[1]
        path = args[2] if len(args) > 2 else None
        output = brain.export(format=fmt, path=path)
        if not path:
            print(output)

    elif cmd == "nrnlang" and len(args) > 1:
        from neuronx.language.nrnlang import NRNLangInterpreter
        interp = NRNLangInterpreter(brain=brain)
        result = interp.execute(" ".join(args[1:]))
        print(result.get("log", json.dumps(result, indent=2)))

    else:
        print(f"Unknown command: {cmd}")

    brain.end_session()


if __name__ == "__main__":
    main()
