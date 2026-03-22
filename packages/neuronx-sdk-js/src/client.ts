/**
 * ╔══════════════════════════════════════════════════════════╗
 * ║  NEURON-X Omega — TypeScript SDK Client                  ║
 * ║  Full-featured client for the NEURON-X REST API          ║
 * ╚══════════════════════════════════════════════════════════╝
 */

import type {
  NeuronXClientOptions,
  RememberRequest, RememberResponse,
  RecallRequest, RecallResponse,
  ContextRequest, ContextResponse,
  BrainStats, AuditResult,
  MemoryListResponse, Engram,
  UpdateMemoryRequest,
  BondListResponse,
  NRNLangRequest, NRNLangResult, NRNLangScriptRequest,
  NeuronXEvent,
} from './types';

const DEFAULT_BASE_URL = 'http://localhost:8000';
const DEFAULT_TIMEOUT = 30000;

export class NeuronXClient {
  private baseUrl: string;
  private apiKey?: string;
  private timeout: number;
  private onEvent?: (event: NeuronXEvent) => void;
  private eventSource: EventSource | null = null;

  constructor(options: NeuronXClientOptions = {}) {
    this.baseUrl = (options.baseUrl || DEFAULT_BASE_URL).replace(/\/$/, '');
    this.apiKey = options.apiKey;
    this.timeout = options.timeout || DEFAULT_TIMEOUT;
    this.onEvent = options.onEvent;
  }

  // ━━━━━━━━━━━━━━━━━━━━━━━━━━━
  // HTTP Helper
  // ━━━━━━━━━━━━━━━━━━━━━━━━━━━

  private async request<T>(
    method: string,
    path: string,
    body?: unknown,
    params?: Record<string, string | number>,
  ): Promise<T> {
    let url = `${this.baseUrl}${path}`;
    if (params) {
      const qs = new URLSearchParams();
      for (const [k, v] of Object.entries(params)) {
        qs.set(k, String(v));
      }
      url += `?${qs.toString()}`;
    }

    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
    };
    if (this.apiKey) {
      headers['Authorization'] = `Bearer ${this.apiKey}`;
    }

    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), this.timeout);

    try {
      const response = await fetch(url, {
        method,
        headers,
        body: body ? JSON.stringify(body) : undefined,
        signal: controller.signal,
      });

      if (!response.ok) {
        const error = await response.json().catch(() => ({ detail: response.statusText }));
        throw new Error(`NEURON-X API Error (${response.status}): ${error.detail || JSON.stringify(error)}`);
      }

      return await response.json() as T;
    } finally {
      clearTimeout(timer);
    }
  }

  // ━━━━━━━━━━━━━━━━━━━━━━━━━━━
  // Brain Operations
  // ━━━━━━━━━━━━━━━━━━━━━━━━━━━

  /** Store a memory */
  async remember(text: string, options?: Partial<RememberRequest>): Promise<RememberResponse> {
    return this.request<RememberResponse>('POST', '/api/v1/brain/remember', {
      text,
      source: options?.source || 'user',
      emotion: options?.emotion,
      decay_class: options?.decay_class,
    });
  }

  /** Query memories */
  async recall(query: string, topK = 7): Promise<RecallResponse> {
    return this.request<RecallResponse>('POST', '/api/v1/brain/recall', {
      query,
      top_k: topK,
    });
  }

  /** Get context for AI injection */
  async getContext(message: string, options?: Partial<ContextRequest>): Promise<ContextResponse> {
    return this.request<ContextResponse>('POST', '/api/v1/brain/context', {
      message,
      top_k: options?.top_k || 7,
      remember: options?.remember ?? true,
    });
  }

  /** Get brain statistics */
  async getStats(): Promise<BrainStats> {
    return this.request<BrainStats>('GET', '/api/v1/brain/stats');
  }

  /** Run thermal audit */
  async runAudit(): Promise<AuditResult> {
    return this.request<AuditResult>('POST', '/api/v1/brain/audit');
  }

  /** End session (save + bond + audit) */
  async endSession(): Promise<{ status: string; message: string }> {
    return this.request('POST', '/api/v1/brain/end-session');
  }

  // ━━━━━━━━━━━━━━━━━━━━━━━━━━━
  // Memory CRUD
  // ━━━━━━━━━━━━━━━━━━━━━━━━━━━

  /** List memories (paginated) */
  async listMemories(page = 0, pageSize = 50, filters?: { zone?: string; emotion?: string }): Promise<MemoryListResponse> {
    const params: Record<string, string | number> = { page, page_size: pageSize };
    if (filters?.zone) params.zone = filters.zone;
    if (filters?.emotion) params.emotion = filters.emotion;
    return this.request<MemoryListResponse>('GET', '/api/v1/memories', undefined, params);
  }

  /** Get a single memory */
  async getMemory(id: string): Promise<Engram> {
    return this.request<Engram>('GET', `/api/v1/memories/${id}`);
  }

  /** Delete a memory */
  async deleteMemory(id: string): Promise<{ status: string; id: string }> {
    return this.request('DELETE', `/api/v1/memories/${id}`);
  }

  /** Update a memory */
  async updateMemory(id: string, updates: UpdateMemoryRequest): Promise<Engram> {
    return this.request<Engram>('PATCH', `/api/v1/memories/${id}`, updates);
  }

  // ━━━━━━━━━━━━━━━━━━━━━━━━━━━
  // Bonds
  // ━━━━━━━━━━━━━━━━━━━━━━━━━━━

  /** List all bonds */
  async listBonds(): Promise<BondListResponse> {
    return this.request<BondListResponse>('GET', '/api/v1/bonds');
  }

  /** Get bonds for a specific engram */
  async getBondsFor(engramId: string): Promise<BondListResponse> {
    return this.request<BondListResponse>('GET', `/api/v1/bonds/${engramId}`);
  }

  // ━━━━━━━━━━━━━━━━━━━━━━━━━━━
  // NRNLANG-Ω
  // ━━━━━━━━━━━━━━━━━━━━━━━━━━━

  /** Execute a single NRNLANG-Ω command */
  async executeNRNLang(command: string): Promise<NRNLangResult> {
    return this.request<NRNLangResult>('POST', '/api/v1/nrnlang/execute', { command });
  }

  /** Execute a NRNLANG-Ω script */
  async executeScript(script: string): Promise<{ results: NRNLangResult[] }> {
    return this.request('POST', '/api/v1/nrnlang/script', { script });
  }

  // ━━━━━━━━━━━━━━━━━━━━━━━━━━━
  // Export
  // ━━━━━━━━━━━━━━━━━━━━━━━━━━━

  /** Export brain data */
  async exportBrain(format: 'json' | 'markdown' | 'csv' | 'nrnlang' = 'json'): Promise<string> {
    const response = await fetch(`${this.baseUrl}/api/v1/export/${format}`, {
      headers: this.apiKey ? { Authorization: `Bearer ${this.apiKey}` } : {},
    });
    return response.text();
  }

  // ━━━━━━━━━━━━━━━━━━━━━━━━━━━
  // SSE Real-time Events
  // ━━━━━━━━━━━━━━━━━━━━━━━━━━━

  /** Connect to real-time event stream */
  connectEvents(onEvent?: (event: NeuronXEvent) => void): void {
    if (typeof EventSource === 'undefined') {
      console.warn('EventSource not available in this environment');
      return;
    }

    const handler = onEvent || this.onEvent;
    if (!handler) {
      console.warn('No event handler provided');
      return;
    }

    this.eventSource = new EventSource(`${this.baseUrl}/api/v1/stream/events`);
    this.eventSource.onmessage = (event) => {
      try {
        const parsed = JSON.parse(event.data) as NeuronXEvent;
        handler(parsed);
      } catch (e) {
        console.error('Failed to parse SSE event:', e);
      }
    };

    this.eventSource.onerror = () => {
      console.warn('SSE connection error, reconnecting...');
    };
  }

  /** Disconnect from event stream */
  disconnectEvents(): void {
    if (this.eventSource) {
      this.eventSource.close();
      this.eventSource = null;
    }
  }
}
