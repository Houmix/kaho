import { openDB, DBSchema, IDBPDatabase } from 'idb';

interface SyncRequest {
  id?: number;
  method: string;
  url: string;
  data?: any;
  timestamp: number;
}

interface CacheEntry {
  key: string;
  value: any;
  timestamp: number;
  ttl?: number;
}

interface KahoDB extends DBSchema {
  syncQueue: {
    key: number;
    value: SyncRequest;
  };
  cache: {
    key: string;
    value: CacheEntry;
  };
}

let db: IDBPDatabase<KahoDB> | null = null;

async function getDB(): Promise<IDBPDatabase<KahoDB>> {
  if (!db) {
    db = await openDB<KahoDB>('kaho-db', 1, {
      upgrade(db) {
        if (!db.objectStoreNames.contains('syncQueue')) {
          db.createObjectStore('syncQueue', { keyPath: 'id', autoIncrement: true });
        }
        if (!db.objectStoreNames.contains('cache')) {
          db.createObjectStore('cache', { keyPath: 'key' });
        }
      },
    });
  }
  return db;
}

export async function addToSyncQueue(request: SyncRequest): Promise<void> {
  const db = await getDB();
  await db.add('syncQueue', request);
}

export async function getSyncQueue(): Promise<SyncRequest[]> {
  const db = await getDB();
  return db.getAll('syncQueue');
}

export async function clearSyncQueue(): Promise<void> {
  const db = await getDB();
  const keys = await db.getAllKeys('syncQueue');
  for (const key of keys) {
    await db.delete('syncQueue', key);
  }
}

export async function setCacheEntry(key: string, value: any, ttl?: number): Promise<void> {
  const db = await getDB();
  await db.put('cache', {
    key,
    value,
    timestamp: Date.now(),
    ttl,
  });
}

export async function getCacheEntry(key: string): Promise<any | null> {
  const db = await getDB();
  const entry = await db.get('cache', key);

  if (!entry) {
    return null;
  }

  // Check TTL
  if (entry.ttl && Date.now() - entry.timestamp > entry.ttl) {
    await db.delete('cache', key);
    return null;
  }

  return entry.value;
}

export async function clearCache(): Promise<void> {
  const db = await getDB();
  const keys = await db.getAllKeys('cache');
  for (const key of keys) {
    await db.delete('cache', key);
  }
}
