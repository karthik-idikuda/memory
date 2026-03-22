"""
NEURON-X Omega — OpenAI Integration Example

Shows how to add persistent memory to any OpenAI chat in 2 lines.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'packages', 'neuronx-core'))

from neuronx import NeuronBrain, OpenAIIntegration


def main():
    brain = NeuronBrain("openai_demo", data_dir="/tmp/neuronx_openai")
    integration = OpenAIIntegration(brain=brain, top_k=7)

    print("╔═══════════════════════════════════════════╗")
    print("║  NEURON-X × OpenAI Integration Example    ║")
    print("╚═══════════════════════════════════════════╝\n")

    # Simulate a conversation
    conversations = [
        "My name is Karthik and I'm a Python developer",
        "I love building AI applications",
        "What do you know about me?",
    ]

    for user_msg in conversations:
        print(f"\n👤 User: {user_msg}")

        messages = [{"role": "user", "content": user_msg}]

        # PRE-CHAT: Inject memories into messages
        enriched = integration.pre_chat(messages)
        print(f"   → {len(enriched)} messages (enriched with memories)")

        # Simulated assistant response
        assistant_response = f"[AI Response to: {user_msg}]"

        # POST-CHAT: Store the conversation as memory
        integration.post_chat(assistant_response)
        print(f"   → Memory stored ✓")

    # Show what the brain knows
    print("\n\n📊 Brain after conversation:")
    stats = brain.get_stats()
    print(f"   Total memories: {stats['total_engrams']}")
    print(f"   Total bonds: {stats['total_axons']}")

    # Recall
    print("\n⊙ Recalling 'developer':")
    results = brain.recall("developer")
    for e, score in results:
        print(f"   [{e.zone[0]}] {e.raw} (score: {score:.3f})")

    brain.end_session()


if __name__ == "__main__":
    main()
