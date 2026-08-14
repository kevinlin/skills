# Design: Widget cache

Canonical design for the widget cache (Requirement 6.1–6.3).

## Components

- `WidgetCache` — in-process LRU keyed by `widgetId:revision`.
- `CacheInvalidator` — subscribes to definition-change events and evicts by prefix.

## Data model

`CacheEntry { key: string, payload: WidgetPayload, revision: number, insertedAt: number }`

## Decisions

- Revision is part of the key, so invalidation is an eviction, never a mutation.
- LRU capacity is a constant, not configurable — one knob fewer to tune.
