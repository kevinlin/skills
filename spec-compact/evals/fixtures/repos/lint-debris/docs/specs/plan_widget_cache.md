# Plan: Widget cache (Requirement 6.1 + 6.2 + 6.3)

Design: [`design_widget_cach.md`](design_widget_cach.md)
Acceptance: [`requirements.md#9.9`](requirements.md#9.9)

## Context

Dashboard renders re-read every widget definition on every paint. A 200-widget
board issues 200 sequential reads and lands at ~2.1 s. Target: under 400 ms on a
warm cache, with a live-read fallback so a miss is never fatal.

## Design Decisions

- Revision is part of the cache key (`widgetId:revision`), so an invalidation is
  an eviction and never a mutation. Rejected alternative: mutate-in-place, which
  made concurrent readers observe half-updated payloads.
- LRU capacity is a compile-time constant.

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
```

3. Re-export `WidgetCache` from `src/cache/index.ts`.

Verify: `pnpm typecheck` && `pnpm test src/cache`

### Task 2 — Wire invalidation

Files: Modify `src/cache/widget_cache.ts`, Modify `src/render/dashboard.ts`

Steps:

1. Subscribe `CacheInvalidator` to `definitionChanged` events.
2. Evict by `widgetId:` prefix on each event.
3. Replace the direct `readDefinition` call with a `cache.get` plus fallback.

Verify: `pnpm typecheck`

## Critical Files — Summary

| Path | Change |
|---|---|
| `src/cache/widget_cache.ts` | New — LRU keyed by `widgetId:revision`. |
| `src/cache/index.ts` | Re-exports `WidgetCache`. |
| `src/render/dashboard.ts` | Reads through the cache with a live-read fallback. |

## Changelog

- 2026-05-02 — Implemented and shipped. Dashboard render at 200 widgets: 2.1 s → 310 ms.
