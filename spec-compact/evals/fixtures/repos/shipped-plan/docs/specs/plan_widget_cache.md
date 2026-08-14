# Plan: Widget cache (Requirement 6.1 + 6.2 + 6.3)

Design: [`design_widget_cache.md`](design_widget_cache.md)

## Context

Dashboard renders re-read every widget definition on every paint. A 200-widget
board issues 200 sequential reads and lands at ~2.1 s. Target: under 400 ms on a
warm cache, with a live-read fallback so a miss is never fatal.

## Design Decisions

- Revision is part of the cache key (`widgetId:revision`), so an invalidation is
  an eviction and never a mutation. Rejected alternative: mutate-in-place, which
  made concurrent readers observe half-updated payloads.
- LRU capacity is a compile-time constant. A configurable knob invites per-tenant
  tuning we do not want to support.
- The invalidator subscribes to definition-change events rather than polling —
  polling at any interval short enough to be correct cost more than the cache saved.

## Implementation Plan

### Task 1 — Add the WidgetCache class

Files: Modify `src/cache/index.ts`, Add `src/cache/widget_cache.ts`

Steps:

1. Create `src/cache/widget_cache.ts` exporting `WidgetCache`.
2. Add the `CacheEntry` type:

```ts
export interface CacheEntry {
  key: string;
  payload: WidgetPayload;
  revision: number;
  insertedAt: number;
}

export class WidgetCache {
  private entries = new Map<string, CacheEntry>();

  get(widgetId: string, revision: number): WidgetPayload | undefined {
    return this.entries.get(`${widgetId}:${revision}`)?.payload;
  }
}
```

3. Re-export `WidgetCache` from `src/cache/index.ts`.

Verify: `pnpm typecheck` && `pnpm test src/cache`

tests: `caches a payload by revision`, `misses on a new revision`

### Task 2 — Wire invalidation

Files: Modify `src/cache/widget_cache.ts`, Modify `src/render/dashboard.ts`

Steps:

1. Subscribe `CacheInvalidator` to `definitionChanged` events.
2. Evict by `widgetId:` prefix on each event:

```ts
invalidate(widgetId: string): void {
  for (const key of this.entries.keys()) {
    if (key.startsWith(`${widgetId}:`)) this.entries.delete(key);
  }
}
```

3. In `src/render/dashboard.ts`, replace the direct `readDefinition` call with a
   `cache.get` followed by a live-read fallback.

Verify: `pnpm typecheck`

tests: `evicts every revision of a changed widget`, `falls back to a live read on miss`

## Cleanup of the Old Implementation

- Delete `src/render/definition_prefetch.ts` — superseded by the cache.
- Remove the `PREFETCH_BATCH_SIZE` env var from `src/config.ts`.

## Critical Files — Summary

| Path | Change |
|---|---|
| `src/cache/widget_cache.ts` | New — LRU keyed by `widgetId:revision`. |
| `src/cache/index.ts` | Re-exports `WidgetCache`. |
| `src/render/dashboard.ts` | Reads through the cache with a live-read fallback. |
| `docs/specs/plan_widget_cache.md` | This plan. |

## Error Handling

| Failure | Behaviour |
|---|---|
| Cache miss | Live read, then insert. |
| Live read throws | Propagate — the render surfaces the error, nothing is cached. |
| Eviction during read | Reader keeps its already-returned payload. |

## TODO

- TODO: decide whether the LRU capacity should be a constant. (Decided: yes.)

## Outstanding follow-ups

- Hit/miss counters are not implemented — tracked in `plan_widget_metrics.md`.

## Changelog

- 2026-05-02 — Implemented and shipped. Dashboard render at 200 widgets: 2.1 s → 310 ms.
