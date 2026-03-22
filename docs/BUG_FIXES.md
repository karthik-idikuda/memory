# NEURON-X Omega — Bug Fixes Reference

All 20 documented bugs and their resolutions.

## BUG-001: SOMA-DB Uses JSON Instead of Binary
- **File**: `core/soma.py`
- **Fix**: True 5-layer binary format with struct packing, magic bytes `NRN\xCE`
- **Test**: `TestSomaDB.test_magic_bytes_in_file`

## BUG-002: WSRA-X Missing Components
- **File**: `core/retrieval.py`
- **Fix**: All 8 scoring components implemented with correct weights
- **Test**: `TestWSRAX.test_all_8_components_used`

## BUG-003: CLASH Gate Not Enforced
- **File**: `core/surprise.py`
- **Fix**: CLASH only triggers when `best_jaccard >= 0.15`
- **Test**: `TestAmygdala.test_clash_gate_enforcement`

## BUG-004: No Backup Restore
- **File**: `core/soma.py`
- **Fix**: `.soma.bak` created on every save, restored on corruption
- **Test**: `TestSomaDB.test_backup_restore`

## BUG-005: `is_anchor` Not a Real Field
- **File**: `core/node.py`
- **Fix**: Added `is_anchor` as a real boolean field, updated via `crystallize()`
- **Test**: `TestEngramNode.test_is_anchor`

## BUG-006: NMP Protocol Incomplete
- **File**: `core/soma.py`
- **Fix**: Creates `.nrnlock`, `.soma.bak`, `.soma.sig`, `.nrnlog` files
- **Test**: `TestSomaDB.test_sig_created`, `test_nrnlog_created`

## BUG-007: Reawakening Not Run at Session Start
- **File**: `core/zones.py`, `brain/neuron.py`
- **Fix**: `check_reawakenings()` called during `NeuronBrain.__init__()`
- **Test**: `TestThermalManager.test_reawakening_check`

## BUG-008: Bond Pruning One-Sided
- **File**: `core/bonds.py`
- **Fix**: `prune_weak_bonds()` removes from BOTH sides of each bond pair
- **Test**: `TestBondEngine.test_prune_both_sides`

## BUG-009: Audit Never Triggers
- **File**: `brain/scheduler.py`, `brain/neuron.py`
- **Fix**: Auto-audit at every `AUDIT_INTERVAL` (100) interactions
- **Test**: `TestScheduler.test_audit_at_interval`

## BUG-010: No Rate Limiting
- **File**: `app/main.py`
- **Fix**: In-memory rate limiter, 60 req/min per IP, returns 429

## BUG-011: API Key Not Persisted
- **File**: `neuronx-web/src/App.tsx`
- **Fix**: Settings saved to `localStorage`, setup screen on first visit

## BUG-012: Endpoints Not Validated
- **File**: `app/main.py`
- **Fix**: Pydantic models with `Field` validators on all request bodies

## BUG-013: Long Inputs Not Chunked
- **File**: `brain/extractor.py`
- **Fix**: Inputs >500 chars split into sentences, deduplicated by Jaccard >0.95
- **Test**: `TestExtractorInjector.test_extract_long_input_chunking`

## BUG-014: Contradiction Lookup O(n²)
- **File**: `brain/indexer.py`
- **Fix**: Subject index for O(n×k) lookup using tokenized subject matching
- **Test**: `TestSubjectIndex.test_index_and_find`

## BUG-015: No Pagination
- **File**: `core/retrieval.py`, `app/main.py`
- **Fix**: `page` and `page_size` params on retrieval and memory list endpoints
- **Test**: `TestWSRAX.test_top_k_limiting`

## BUG-016: No Streaming Endpoint
- **File**: `app/main.py`
- **Fix**: SSE endpoint at `/api/v1/stream/events` with heartbeat

## BUG-017: NRNLANG Output Not in UI
- **File**: `language/nrnlang.py`, `neuronx-web/src/App.tsx`
- **Fix**: NRNLANG interpreter returns structured output, web console displays it
- **Test**: `TestNRNLang.test_forge_command`, `test_format_engram`

## BUG-018: Exporter Missing Fields
- **File**: `utils/exporter.py`
- **Fix**: All 20 EngramNode fields exported in all formats (JSON/MD/CSV/NRN)
- **Test**: `TestExporter.test_export_json`, `test_export_csv`

## BUG-019: No Real-Time Zone Updates
- **File**: `app/main.py`, `neuronx-web/src/App.tsx`
- **Fix**: SSE events pushed on remember/recall/audit/delete, web EventsView

## BUG-020: File Lock Handling
- **File**: `core/soma.py`
- **Fix**: Stale lock detection (>30s), auto-clear with warning log
- **Test**: `TestSomaDB.test_stale_lock_handling`
