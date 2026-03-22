/**
 * ╔══════════════════════════════════════════════════════════╗
 * ║  NEURON-X Omega — TypeScript SDK Types                   ║
 * ║  Complete type definitions for all API interactions       ║
 * ╚══════════════════════════════════════════════════════════╝
 */

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━
// Engram (Memory Unit)
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━

export type Zone = 'HOT' | 'WARM' | 'COLD' | 'SILENT';
export type Emotion = 'neutral' | 'happy' | 'sad' | 'curious' | 'excited' | 'angry' | 'love' | 'fear';
export type DecayClass = 'fact' | 'opinion' | 'emotion' | 'event' | 'identity';
export type TruthState = 'active' | 'expired' | 'contested';
export type Source = 'user' | 'inference' | 'import';
export type Action = 'ECHO' | 'FORGE' | 'CLASH';

export interface Engram {
  id: string;
  raw: string;
  born: number;
  last_seen: number;
  valid_from: number;
  valid_until: number | null;
  heat: number;
  surprise_score: number;
  weight: number;
  confidence: number;
  decay_class: DecayClass;
  emotion: Emotion;
  tags: string[];
  zone: Zone;
  truth: TruthState;
  superseded_by: string | null;
  contradicts: string[];
  source: Source;
  bonds: Record<string, number>;
  access_count: number;
  session_count: number;
  is_anchor: boolean;
}

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━
// Axon (Bond)
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━

export interface Axon {
  from_id: string;
  to_id: string;
  synapse: number;
  axon_type: number;
  created: number;
  reinforced: number;
}

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━
// API Requests
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━

export interface RememberRequest {
  text: string;
  source?: Source;
  emotion?: Emotion;
  decay_class?: DecayClass;
}

export interface RecallRequest {
  query: string;
  top_k?: number;
}

export interface ContextRequest {
  message: string;
  top_k?: number;
  remember?: boolean;
}

export interface NRNLangRequest {
  command: string;
}

export interface NRNLangScriptRequest {
  script: string;
}

export interface UpdateMemoryRequest {
  confidence?: number;
  weight?: number;
  tags?: string[];
  emotion?: Emotion;
}

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━
// API Responses
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━

export interface RememberResponse {
  action: Action;
  engram_id: string;
  surprise_score: number;
  is_new: boolean;
  conflict: ConflictInfo | null;
}

export interface ConflictInfo {
  old_id: string;
  new_id: string;
  resolution: 'SUPERSEDED' | 'CONTESTED' | 'TIE_CONTESTED';
  reason: string;
  confidence: number;
}

export interface RecallResult {
  id: string;
  raw: string;
  score: number;
  confidence: number;
  zone: Zone;
  emotion: Emotion;
  is_anchor: boolean;
  age_days: number;
}

export interface RecallResponse {
  results: RecallResult[];
}

export interface ContextResponse {
  system_prompt_addition: string;
  action: string;
  memories_count: number;
}

export interface BrainStats {
  brain_name: string;
  total_engrams: number;
  total_axons: number;
  session_engrams: number;
  interaction_count: number;
  zone_counts: Record<Zone, number>;
}

export interface AuditResult {
  promoted: number;
  demoted: number;
  reawakened: number;
  fossilized: number;
  crystallized: number;
  zone_counts: Record<Zone, number>;
  reawakened_ids: string[];
  crystallized_ids: string[];
}

export interface MemoryListResponse {
  memories: Engram[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface BondListResponse {
  bonds: Axon[];
  total: number;
}

export interface NRNLangResult {
  status: string;
  action?: string;
  id?: string;
  log?: string;
  stats?: Record<string, unknown>;
  error?: string;
}

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━
// SSE Events
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━

export interface NeuronXEvent {
  type: 'remember' | 'recall' | 'audit' | 'delete' | 'update' | 'nrnlang' | 'heartbeat';
  data: Record<string, unknown>;
  timestamp: number;
}

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━
// Client Options
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━

export interface NeuronXClientOptions {
  baseUrl?: string;
  apiKey?: string;
  timeout?: number;
  onEvent?: (event: NeuronXEvent) => void;
}
