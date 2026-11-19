# Prototype: how much time does analysis add?

Throwaway prototype for the ticket "How much time does analysis add, and is caching worth it?" (#111). Never merged.

- `bench.py`: read + parse + about 10 representative checks + per-file summaries + cross-file duplication. Times no cache, a content-hash cache and an mtime cache (cold, warm, one file changed).
- `parts.py`: splits out raw parse cost, a single-pass version of the work, and 8 processes.

## Results (median, 16 cores, Python 3.13)

| Suite | Files / tests | No cache, naive | No cache, single pass | Warm cache, nothing changed | Warm cache, 1 file changed |
|---|---|---|---|---|---|
| this repo | 22 / 134 | 145 ms | 42 ms | 0.7 ms | 6 ms |
| networkx | 267 / 4.5k | 6.8 s | 2.3 s (parse alone 0.8 s) | 25 ms | 29 ms |
| pandas | 981 / 22k | 41 s | 14.3 s (parse alone 7.5 s) | 212 ms | 245 ms |

- **Baseline:** pytest collection of networkx takes 7.7 s on the first run and 1.5 s warm (pytest caches rewritten modules as pyc).
- **Cross-file comparison** on summaries: 7 ms for networkx, 106 ms for pandas.
- **8 processes, cold:** pandas 14.3 s → 2.4 s.
- **Caveat:** only about 10 representative checks were run, not all ~25.
