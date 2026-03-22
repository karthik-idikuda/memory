/**
 * NEURON-X Lite — Browser-Based Memory Engine
 * Persistent user memory using IndexedDB
 */

export interface MemoryEntry {
  id: string;
  type: 'preference' | 'pattern' | 'bug' | 'wisdom';
  content: string;
  confidence: number;
  createdAt: number;
  lastAccessed: number;
  accessCount: number;
  projectId?: string;
  tags: string[];
}

const DB_NAME = 'nexus-neuronx';
const DB_VERSION = 1;
const STORE_NAME = 'memories';

function openDB(): Promise<IDBDatabase> {
  return new Promise((resolve, reject) => {
    if (typeof window === 'undefined') {
      reject(new Error('IndexedDB not available on server'));
      return;
    }

    const request = indexedDB.open(DB_NAME, DB_VERSION);

    request.onupgradeneeded = () => {
      const db = request.result;
      if (!db.objectStoreNames.contains(STORE_NAME)) {
        const store = db.createObjectStore(STORE_NAME, { keyPath: 'id' });
        store.createIndex('type', 'type', { unique: false });
        store.createIndex('confidence', 'confidence', { unique: false });
        store.createIndex('lastAccessed', 'lastAccessed', { unique: false });
      }
    };

    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject(request.error);
  });
}

export async function storeMemory(entry: Omit<MemoryEntry, 'id' | 'createdAt' | 'lastAccessed' | 'accessCount'>): Promise<string> {
  const db = await openDB();
  const id = `mem-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
  const memory: MemoryEntry = {
    ...entry,
    id,
    createdAt: Date.now(),
    lastAccessed: Date.now(),
    accessCount: 0,
  };

  return new Promise((resolve, reject) => {
    const tx = db.transaction(STORE_NAME, 'readwrite');
    tx.objectStore(STORE_NAME).put(memory);
    tx.oncomplete = () => resolve(id);
    tx.onerror = () => reject(tx.error);
  });
}

export async function recallMemories(type?: MemoryEntry['type'], limit = 50): Promise<MemoryEntry[]> {
  const db = await openDB();

  return new Promise((resolve, reject) => {
    const tx = db.transaction(STORE_NAME, 'readonly');
    const store = tx.objectStore(STORE_NAME);
    const request = type
      ? store.index('type').getAll(type)
      : store.getAll();

    request.onsuccess = () => {
      const results = (request.result as MemoryEntry[])
        .sort((a, b) => b.lastAccessed - a.lastAccessed)
        .slice(0, limit);
      resolve(results);
    };
    request.onerror = () => reject(request.error);
  });
}

export async function searchMemories(query: string): Promise<MemoryEntry[]> {
  const all = await recallMemories();
  const q = query.toLowerCase();
  return all.filter(m =>
    m.content.toLowerCase().includes(q) ||
    m.tags.some(t => t.toLowerCase().includes(q))
  );
}

export async function updateAccess(id: string): Promise<void> {
  const db = await openDB();

  return new Promise((resolve, reject) => {
    const tx = db.transaction(STORE_NAME, 'readwrite');
    const store = tx.objectStore(STORE_NAME);
    const getReq = store.get(id);

    getReq.onsuccess = () => {
      const memory = getReq.result as MemoryEntry;
      if (memory) {
        memory.lastAccessed = Date.now();
        memory.accessCount++;
        store.put(memory);
      }
    };

    tx.oncomplete = () => resolve();
    tx.onerror = () => reject(tx.error);
  });
}

export async function clearAllMemories(): Promise<void> {
  const db = await openDB();

  return new Promise((resolve, reject) => {
    const tx = db.transaction(STORE_NAME, 'readwrite');
    tx.objectStore(STORE_NAME).clear();
    tx.oncomplete = () => resolve();
    tx.onerror = () => reject(tx.error);
  });
}

export async function getMemoryStats(): Promise<{
  total: number;
  byType: Record<string, number>;
  avgConfidence: number;
}> {
  const all = await recallMemories(undefined, 9999);
  const byType: Record<string, number> = {};

  for (const m of all) {
    byType[m.type] = (byType[m.type] || 0) + 1;
  }

  const avgConfidence = all.length > 0
    ? all.reduce((sum, m) => sum + m.confidence, 0) / all.length
    : 0;

  return { total: all.length, byType, avgConfidence };
}
