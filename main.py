#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════╗
║  NEURON-X OMEGA                                          ║
║  The World's First Self-Sovereign Permanent AI Memory     ║
║                                                          ║
║  Custom Language: NRNLANG-Ω                               ║
║  Custom Database: SOMA-DB                                 ║
║  Custom Protocol: NMP (Neural Memory Protocol)            ║
║                                                          ║
║  Run: python main.py                                      ║
╚══════════════════════════════════════════════════════════╝
"""

import os
import sys
import argparse
import logging
from pathlib import Path

from dotenv import load_dotenv


def setup_logging(debug: bool = False):
    """Configure logging for NEURON-X."""
    log_dir = Path(__file__).parent / "logs"
    log_dir.mkdir(exist_ok=True)

    handlers = [logging.FileHandler(log_dir / "neuronx.log")]
    if debug:
        handlers.append(logging.StreamHandler(sys.stdout))

    logging.basicConfig(
        level=logging.DEBUG if debug else logging.INFO,
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
        handlers=handlers,
    )


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="NEURON-X Omega — Self-Sovereign Permanent AI Memory System"
    )
    parser.add_argument(
        "--brain", type=str, default=None,
        help="Brain name (default: 'default' or BRAIN_NAME env var)"
    )
    parser.add_argument(
        "--data", type=str, default=None,
        help="Data directory (default: ./data)"
    )
    parser.add_argument(
        "--debug", action="store_true",
        help="Enable debug logging to console"
    )
    return parser.parse_args()


def main():
    """NEURON-X Omega entry point."""
    # Load environment
    load_dotenv()

    # Parse CLI args
    args = parse_args()
    setup_logging(debug=args.debug)

    # Configuration (CLI args override env vars)
    api_key = os.getenv("ANTHROPIC_API_KEY", "")
    brain_name = args.brain or os.getenv("BRAIN_NAME", "default")
    model = os.getenv("CLAUDE_MODEL", "claude-sonnet-4-20250514")

    # Data paths
    if args.data:
        data_dir = Path(args.data)
    else:
        data_dir = Path(__file__).parent / "data"
    data_dir.mkdir(exist_ok=True, parents=True)
    logs_dir = Path(__file__).parent / "logs"
    logs_dir.mkdir(exist_ok=True)

    soma_path = str(data_dir / f"{brain_name}.soma")

    # Initialize AI client (optional)
    ai_client = None
    if api_key and api_key != "sk-ant-your-key-here":
        try:
            import anthropic
            ai_client = anthropic.Anthropic(api_key=api_key)
            print(f"  ✓ Claude API connected ({model})")
        except Exception as e:
            print(f"  ⚠ Claude API unavailable: {e}")
            print("  Running in offline mode (memories still stored locally)")
    else:
        print("  ⚠ No API key found — running in offline mode")
        print("  Copy .env.example to .env and add your ANTHROPIC_API_KEY")

    # Initialize Brain
    from brain.neuron import NeuronBrain
    brain = NeuronBrain(
        soma_path=soma_path,
        ai_client=ai_client,
        model=model,
    )

    # Start Chat Interface
    from interface.chat import ChatInterface
    chat = ChatInterface(brain)
    chat.run()


if __name__ == "__main__":
    main()
