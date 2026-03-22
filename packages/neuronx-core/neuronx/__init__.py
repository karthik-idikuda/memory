"""
╔══════════════════════════════════════════════════════════╗
║  NEURON-X Omega — World's First Self-Sovereign AI Memory ║
║  v1.0.0-omega                                            ║
╚══════════════════════════════════════════════════════════╝
"""

__version__ = "1.0.0"
__author__ = "NEURON-X Team"

from neuronx.brain.neuron import NeuronBrain
from neuronx.core.node import EngramNode
from neuronx.core.soma import SomaDB, AxonRecord
from neuronx.core.integrity import generate_engram_id
from neuronx.core.surprise import Amygdala, SurpriseResult
from neuronx.core.retrieval import RetrievalEngine
from neuronx.core.bonds import BondEngine
from neuronx.core.zones import ThermalManager
from neuronx.brain.contradiction import ContradictionEngine, ContradictionResult
from neuronx.brain.extractor import MemoryExtractor
from neuronx.brain.injector import ContextInjector
from neuronx.brain.scheduler import AuditScheduler
from neuronx.brain.indexer import SubjectIndex
from neuronx.language.nrnlang import NRNLangInterpreter
from neuronx.utils.tokenizer import tokenize, jaccard
from neuronx.utils.exporter import BrainExporter
from neuronx.utils.events import EventBus, events
from neuronx.integrations.base import (
    BaseIntegration, GenericIntegration,
    OpenAIIntegration, AnthropicIntegration,
    LangChainIntegration, LiteLLMIntegration,
)
from neuronx.exceptions import (
    NeuronXError, NeuronXCorruptionError, NeuronXLockTimeoutError,
    NeuronXIntegrityError, NRNSyntaxError, NRNRuntimeError,
)

__all__ = [
    "NeuronBrain",
    "EngramNode",
    "SomaDB", "AxonRecord",
    "generate_engram_id",
    "Amygdala", "SurpriseResult",
    "RetrievalEngine",
    "BondEngine",
    "ThermalManager",
    "ContradictionEngine", "ContradictionResult",
    "MemoryExtractor",
    "ContextInjector",
    "AuditScheduler",
    "SubjectIndex",
    "NRNLangInterpreter",
    "tokenize", "jaccard",
    "BrainExporter",
    "EventBus", "events",
    "BaseIntegration", "GenericIntegration",
    "OpenAIIntegration", "AnthropicIntegration",
    "LangChainIntegration", "LiteLLMIntegration",
    "NeuronXError", "NeuronXCorruptionError",
    "NeuronXLockTimeoutError", "NeuronXIntegrityError",
    "NRNSyntaxError", "NRNRuntimeError",
]
