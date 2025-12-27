# oclasses Output Formats

The `oclasses` command supports two output modes: **compact** (default) and **verbose** (with `--verbose` flag).

## Compact Output (Default)

The default output is clean and minimal, showing only essential information on a single line:

```
(lldb) oclasses IDS*
Found 47 class(es) matching: IDS*:
  IDSAccount
  IDSAccountController
  IDSConnection
  IDSService
  ...

[10,234 total | 47 matched | 12.34s | 829 classes/sec]
```

**Cached results are even more concise:**
```
(lldb) oclasses IDS*
Found 47 class(es) matching: IDS*:
  IDSAccount
  IDSAccountController
  IDSConnection
  IDSService
  ...

[10,234 total | 47 matched | 0.003s | cached]
```

### Compact Format Details
The single-line summary shows:
- Total class count
- Number of matched classes
- Total execution time
- Throughput (classes/sec) OR "cached" indicator

## Verbose Output (--verbose)

For detailed performance analysis and debugging, use the `--verbose` flag:

```
(lldb) oclasses --verbose IDS*
Found 47 class(es) matching: IDS*:
  IDSAccount
  IDSAccountController
  IDSConnection
  IDSService
  ...

──────────────────────────────────────────────────────────────────────
Performance Summary:
  Total time:     12.34s
  Classes:        10,234 total, 47 matched
  Throughput:     829 classes/sec
  Batch size:     35

  Timing breakdown:
    Setup:        0.45s (3.6%)
    Bulk read:    0.12s (1.0%)
    Batching:     11.56s (93.7%)
    Cleanup:      0.21s (1.7%)

  Resource usage:
    Expressions:  296
    Memory reads: 586
──────────────────────────────────────────────────────────────────────
```

**Verbose output for cached results:**
```
(lldb) oclasses --verbose IDS*
Found 47 class(es) matching: IDS*:
  IDSAccount
  IDSAccountController
  IDSConnection
  IDSService
  ...

──────────────────────────────────────────────────────────────────────
Performance Summary: (from cache)
  Total time:     0.003s
  Classes:        10,234 total, 47 matched
  Source:         Cached (use --reload to refresh)
──────────────────────────────────────────────────────────────────────
```

### Verbose Format Details
The detailed summary includes:
- **Total time**: Complete execution time
- **Classes**: Total count and matched count
- **Throughput**: Processing speed (classes per second)
- **Batch size**: Current batch size setting
- **Timing breakdown**: Percentage of time spent in each phase
  - Setup: Initial allocation and configuration
  - Bulk read: Reading class pointer array from memory
  - Batching: Processing classes in batches
  - Cleanup: Memory deallocation
- **Resource usage**: Count of LLDB operations
  - Expressions: Number of `frame.EvaluateExpression()` calls
  - Memory reads: Number of `process.ReadMemory()` calls

## When to Use Each Mode

### Use Compact (Default)
- Normal daily usage
- Quick class searches
- When you just need the results
- Minimal terminal clutter

### Use Verbose (--verbose)
- Performance analysis
- Debugging caching behavior
- Optimizing batch size
- Understanding command performance
- Troubleshooting issues

## Examples

```bash
# Compact output (default)
oclasses NSString                    # Quick lookup
oclasses *Service                    # Quick pattern search

# Verbose output for analysis
oclasses --verbose --reload          # See detailed metrics for full reload
oclasses --verbose --batch-size=50   # Compare performance with different batch sizes
oclasses --verbose IDS*              # Analyze performance of filtered search
```
