"""
╔══════════════════════════════════════════════════════════╗
║  SIGMA-X Omega — Persistent Causal Reasoning Engine      ║
║  The world's first self-sovereign causal brain           ║
╚══════════════════════════════════════════════════════════╝

SIGMA-X stores WHY things happen and WHAT will happen.
Partner to NEURON-X (which stores WHAT the AI knows).
Together they form the complete AI brain.

Public API:
    from sigmax import SigmaBrain, CauseNode, CausaDB
"""

__version__ = "1.0.0"
__author__ = "SIGMA-X Team"

# Core
from sigmax.core.causenode import CauseNode
from sigmax.core.causadb import CausaDB
from sigmax.core.sigma import sigma_score, sigma_rank, sigma_score_breakdown
from sigmax.core.evidence import EvidenceEngine, EvidenceRecord
from sigmax.core.zones import ZoneManager
from sigmax.core.integrity import (
    IntegritySeal, NMPLock,
    generate_node_id, generate_brain_id,
    sha256_hex, sha256_bytes, sha256_dict,
)
from sigmax.core.tokenizer import (
    tokenize, causal_resonance, has_causal_language,
    detect_causal_signals, word_overlap,
)

# Brain
from sigmax.brain.sigma_brain import SigmaBrain
from sigmax.brain.chain_builder import ChainBuilder
from sigmax.brain.predictor import PredictionEngine, Prediction
from sigmax.brain.counterfactual import CounterfactualEngine, Counterfactual
from sigmax.brain.multihop import MultiHopBuilder, CausalPath
from sigmax.brain.axiom_engine import AxiomEngine
from sigmax.brain.neuronx_bridge import NeuronXBridge
from sigmax.brain.injector import ContextInjector
from sigmax.brain.scheduler import Scheduler

# Language
from sigmax.language.symbols import get_symbol, lookup_symbol, ALL_SYMBOLS
from sigmax.language.keywords import is_keyword, get_category
from sigmax.language.grammar import validate_chain_notation, CaulangEmitter
from sigmax.language.caulang import parse_chain, parse_chains, parse_session, to_causenode

# Utils
from sigmax.utils.exporter import export_json, export_markdown, export_csv, import_json
from sigmax.utils.events import EventBus, SigmaEvent
from sigmax.utils.metrics import compute_brain_health, compute_file_metrics
from sigmax.utils.compressor import zlib_compress, zlib_decompress, auto_compress
from sigmax.utils.crypto import encrypt, decrypt, encrypt_file, decrypt_file

# Config + Exceptions (wildcard for convenience)
from sigmax.config import *
from sigmax.exceptions import *

__all__ = [
    # Core
    'CauseNode', 'CausaDB', 'sigma_score', 'sigma_rank', 'sigma_score_breakdown',
    'EvidenceEngine', 'EvidenceRecord', 'ZoneManager',
    'IntegritySeal', 'NMPLock', 'generate_node_id', 'generate_brain_id',
    'sha256_hex', 'sha256_bytes', 'sha256_dict',
    'tokenize', 'causal_resonance', 'has_causal_language',
    # Brain
    'SigmaBrain', 'ChainBuilder', 'PredictionEngine', 'Prediction',
    'CounterfactualEngine', 'Counterfactual', 'MultiHopBuilder', 'CausalPath',
    'AxiomEngine', 'NeuronXBridge', 'ContextInjector', 'Scheduler',
    # Language
    'get_symbol', 'lookup_symbol', 'ALL_SYMBOLS', 'is_keyword', 'get_category',
    'validate_chain_notation', 'CaulangEmitter',
    'parse_chain', 'parse_chains', 'parse_session', 'to_causenode',
    # Utils
    'export_json', 'export_markdown', 'export_csv', 'import_json',
    'EventBus', 'SigmaEvent', 'compute_brain_health', 'compute_file_metrics',
    'encrypt', 'decrypt', 'encrypt_file', 'decrypt_file',
]
