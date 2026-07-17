# Code Quality Checklist

Adapt examples below to the language of the code being reviewed. The patterns are universal even when the syntax differs.

## Error Handling

### Anti-patterns to Flag

- **Swallowed errors**: Empty catch/except/rescue blocks, or catch-and-log-only with no recovery
- **Overly broad catch**: Catching the base exception type instead of specific errors
- **Error info leakage**: Stack traces, internal paths, or SQL queries exposed to users
- **Missing error handling**: No protection around fallible operations (I/O, network, parsing, deserialization)
- **Async error gaps**: Unhandled promise rejections (JS), unchecked goroutine panics (Go), ignored `Result` (Rust), fire-and-forget tasks without error capture

### What Good Looks Like

- Errors caught at appropriate boundaries (not too deep, not too shallow)
- Error messages useful for debugging but safe for users
- Async errors propagated or handled — not silently dropped
- Fallback behavior defined for recoverable errors
- Critical failures trigger alerts or monitoring

### Questions to Ask
- "What happens when this operation fails?"
- "Will the caller know something went wrong?"
- "Is there enough context to debug this in production?"

---

## Performance & Caching

### CPU & Computation

- **Expensive ops in hot paths**: Regex compilation, JSON/XML parsing, crypto operations inside loops
- **Blocking the main thread/event loop**: Sync I/O in async context, heavy computation without offloading
- **Redundant computation**: Same calculation repeated when it could be cached or hoisted
- **Missing memoization**: Pure functions called repeatedly with identical inputs

### Database & I/O

- **N+1 queries**: Loop making one query per item instead of a batch query
- **Missing indexes**: Queries filtering or joining on unindexed columns
- **Over-fetching**: `SELECT *` or loading full objects when only a few fields are needed
- **No pagination**: Loading unbounded datasets into memory
- **Connection leaks**: Not closing DB connections, file handles, or HTTP clients

### Caching

- **Missing cache**: Repeated expensive calls for data that doesn't change often
- **Cache without TTL**: Stale data served indefinitely
- **No invalidation strategy**: Source data updated but cache not cleared
- **User-specific data cached globally**: Privacy and correctness issue

### Memory

- **Unbounded collections**: Lists, maps, or buffers that grow without limit
- **Large object retention**: Holding references that prevent garbage collection
- **String building in loops**: Concatenation instead of builder/join/buffer patterns
- **Loading large files entirely**: Should stream instead

### Questions to Ask
- "How does this behave with 10x or 100x the data?"
- "Is this result cacheable?"
- "Can this be batched instead of one-by-one?"

---

## Boundary Conditions

### Null/Empty/Missing Values

- **Missing null checks**: Accessing properties on potentially null/nil/None objects
- **Truthy/falsy confusion**: Boolean check that accidentally excludes valid values like `0`, `""`, or `false`
- **Overly defensive chaining**: Deep optional chaining (e.g., `a?.b?.c?.d`) hiding structural problems
- **Inconsistent null conventions**: Mixing null/undefined/None/nil without clear rules

### Empty Collections

- **Empty array not handled**: Code assumes collection has at least one element
- **First/last element access**: Indexing without length/size check
- **Aggregation on empty sets**: Sum, average, min/max on zero elements

### Numeric Boundaries

- **Division by zero**: Missing guard before division
- **Integer overflow**: Large numbers exceeding safe range (especially JS `Number`, 32-bit ints)
- **Floating point comparison**: Equality check on floats instead of epsilon/tolerance
- **Negative values**: Index, count, or amount that shouldn't be negative
- **Off-by-one errors**: Loop bounds, array slicing, pagination offsets

### String Boundaries

- **Empty string**: Not handled as edge case distinct from null
- **Whitespace-only**: Passes truthy/non-empty checks but is effectively blank
- **Very long input**: No length limits causing memory or display issues
- **Encoding edge cases**: Unicode, emoji, multi-byte characters, RTL text

### Questions to Ask
- "What if this is null/empty/missing?"
- "What if this collection has zero elements?"
- "What happens at the boundaries (0, -1, max value)?"
