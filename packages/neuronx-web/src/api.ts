/**
 * NEURON-X Omega — API Client Hook
 * Centralized API communication for the React dashboard
 */

const BASE_URL = '/api/v1';

async function api<T>(method: string, path: string, body?: unknown): Promise<T> {
  const response = await fetch(`${BASE_URL}${path}`, {
    method,
    headers: { 'Content-Type': 'application/json' },
    body: body ? JSON.stringify(body) : undefined,
  });
  if (!response.ok) {
    const err = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(err.detail || `API Error: ${response.status}`);
  }
  return response.json();
}

// ━━━━━━━━━━ Brain ━━━━━━━━━━

export const brainRemember = (text: string, source = 'user') =>
  api<any>('POST', '/brain/remember', { text, source });

export const brainRecall = (query: string, top_k = 7) =>
  api<any>('POST', '/brain/recall', { query, top_k });

export const brainContext = (message: string) =>
  api<any>('POST', '/brain/context', { message, remember: true });

export const brainChat = (message: string, provider: string, api_key: string, model: string) =>
  api<any>('POST', '/brain/chat', { message, provider, api_key, model });

export const brainStats = () =>
  api<any>('GET', '/brain/stats');

export const brainAudit = () =>
  api<any>('POST', '/brain/audit');

export const brainEndSession = () =>
  api<any>('POST', '/brain/end-session');

// ━━━━━━━━━━ Memories ━━━━━━━━━━

export const listMemories = (page = 0, pageSize = 50) =>
  api<any>('GET', `/memories?page=${page}&page_size=${pageSize}`);

export const getMemory = (id: string) =>
  api<any>('GET', `/memories/${id}`);

export const deleteMemory = (id: string) =>
  api<any>('DELETE', `/memories/${id}`);

// ━━━━━━━━━━ Bonds ━━━━━━━━━━

export const listBonds = () =>
  api<any>('GET', '/bonds');

export const getBondsFor = (id: string) =>
  api<any>('GET', `/bonds/${id}`);

// ━━━━━━━━━━ NRNLANG-Ω ━━━━━━━━━━

export const executeNRNLang = (command: string) =>
  api<any>('POST', '/nrnlang/execute', { command });

export const executeScript = (script: string) =>
  api<any>('POST', '/nrnlang/script', { script });

// ━━━━━━━━━━ Export ━━━━━━━━━━

export const exportBrain = async (format: string): Promise<string> => {
  const res = await fetch(`${BASE_URL}/export/${format}`);
  return res.text();
};

// ━━━━━━━━━━ SSE ━━━━━━━━━━

export function connectSSE(onEvent: (event: any) => void): EventSource {
  const es = new EventSource(`${BASE_URL}/stream/events`);
  es.onmessage = (e) => {
    try { onEvent(JSON.parse(e.data)); }
    catch { /* ignore parse errors */ }
  };
  return es;
}
