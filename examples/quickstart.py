"""
NEURON-X Omega — Quick Start Example

Demonstrates basic memory operations: store, recall, context injection.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'packages', 'neuronx-core'))

from neuronx import NeuronBrain


def main():
    # Create a brain (stored in /tmp for this example)
    brain = NeuronBrain("quickstart", data_dir="/tmp/neuronx_example")
    print("╔══════════════════════════════════════╗")
    print("║  NEURON-X Omega — Quick Start Demo   ║")
    print("╚══════════════════════════════════════╝\n")

    # ── Store Memories ──
    memories = [
        "I love eating pizza at Italian restaurants",
        "I work as a software engineer at Google",
        "My favorite programming language is Python",
        "I live in San Francisco",
        "I enjoy hiking on weekends",
    ]

    print("⊕ Storing memories...")
    for mem in memories:
        result = brain.remember(mem)
        print(f"  {result.action} → {mem[:50]}… (surprise: {result.surprise_score:.2f})")

    # ── Recall Memories ──
    print("\n⊙ Recalling 'What food does user like?'...")
    results = brain.recall("What food does user like?", top_k=3)
    for engram, score in results:
        print(f"  [{engram.zone[0]}] {engram.raw} (score: {score:.3f})")

    # ── Echo (Reinforce) ──
    print("\n● Reinforcing pizza memory...")
    result = brain.remember("I love eating pizza")
    print(f"  {result.action} (surprise: {result.surprise_score:.2f})")

    # ── Get Context for AI ──
    print("\n◈ Getting AI context...")
    ctx = brain.get_context("Tell me about the user's hobbies")
    print(f"  Memories used: {len(ctx.memories_used)}")
    print(f"  Context preview: {ctx.system_prompt_addition[:100]}…")

    # ── Stats ──
    print("\n📊 Brain stats:")
    stats = brain.get_stats()
    for k, v in stats.items():
        print(f"  {k}: {v}")

    # ── End Session ──
    brain.end_session()
    print("\n✅ Session ended, brain saved.")


if __name__ == "__main__":
    main()
