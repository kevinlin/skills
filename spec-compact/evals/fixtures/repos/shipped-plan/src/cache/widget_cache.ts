export interface WidgetPayload {
  html: string;
}

export interface CacheEntry {
  key: string;
  payload: WidgetPayload;
  revision: number;
  insertedAt: number;
}

const CAPACITY = 512;

export class WidgetCache {
  private entries = new Map<string, CacheEntry>();

  get(widgetId: string, revision: number): WidgetPayload | undefined {
    return this.entries.get(`${widgetId}:${revision}`)?.payload;
  }

  set(widgetId: string, revision: number, payload: WidgetPayload): void {
    if (this.entries.size >= CAPACITY) {
      const oldest = this.entries.keys().next().value;
      if (oldest) this.entries.delete(oldest);
    }
    const key = `${widgetId}:${revision}`;
    this.entries.set(key, { key, payload, revision, insertedAt: 0 });
  }

  invalidate(widgetId: string): void {
    for (const key of this.entries.keys()) {
      if (key.startsWith(`${widgetId}:`)) this.entries.delete(key);
    }
  }
}
