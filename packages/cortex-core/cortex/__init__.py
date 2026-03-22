"""
╔══════════════════════════════════════════════════════════════╗
║  CORTEX-X Omega v1.0.0                                       ║
║  The World's First Metacognitive AI Brain                    ║
║                                                              ║
║  Usage:                                                      ║
║    from cortex import CortexAgent, ThoughtNode, CortexDB     ║
╚══════════════════════════════════════════════════════════════╝
"""

__version__ = "1.0.0"
__author__ = "Karthik"
__codename__ = "CORTEX-X Omega"

# ━━━ Clean Public API ━━━
from cortex.core.thought_node import ThoughtNode
from cortex.core.cortexdb import CortexDB
from cortex.core.integrity import IntegritySeal, CMPLock
from cortex.core.tokenizer import (
    tokenize, extract_keywords, semantic_overlap, detect_domain,
)
from cortex.meta.metacog import metacog_score, metacog_breakdown, metacog_health_label
from cortex.meta.confidence import ConfidenceTracker
from cortex.meta.contradiction import ContradictionDetector
from cortex.meta.hallucination import HallucinationShield
from cortex.meta.drift import DriftDetector
from cortex.meta.patterns import PatternRecognizer
from cortex.meta.wisdom import WisdomCrystallizer
from cortex.meta.strategy import StrategyEngine
from cortex.meta.thought_trace import ThoughtTrace, TraceLogger
from cortex.engine.agent import CortexAgent
from cortex.engine.router import LLMRouter
from cortex.engine.conversation import ConversationManager
from cortex.engine.tools import ToolRegistry
from cortex.engine.growth import GrowthEngine
from cortex.bridges.neuronx_bridge import NeuronXBridge
from cortex.bridges.sigmax_bridge import SigmaXBridge

__all__ = [
    "CortexAgent", "ThoughtNode", "CortexDB",
    "IntegritySeal", "CMPLock",
    "metacog_score", "metacog_breakdown", "metacog_health_label",
    "ConfidenceTracker", "ContradictionDetector", "HallucinationShield",
    "DriftDetector", "PatternRecognizer", "WisdomCrystallizer",
    "StrategyEngine", "ThoughtTrace", "TraceLogger",
    "LLMRouter", "ConversationManager", "ToolRegistry", "GrowthEngine",
    "NeuronXBridge", "SigmaXBridge",
    "tokenize", "extract_keywords", "semantic_overlap", "detect_domain",
]
