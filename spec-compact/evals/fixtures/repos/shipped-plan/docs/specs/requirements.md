# Requirements

## 6. Widget rendering

- **6.1** A dashboard with 200 widgets renders in under 400 ms on a warm cache.
- **6.2** Cache entries are invalidated when the underlying widget definition changes.
- **6.3** A cache miss never blocks the render — it falls back to the live read.
