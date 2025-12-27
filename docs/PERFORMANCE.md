# Performance Optimization

## Summary

The `oclasses` command is optimized for enumerating ~10,000 Objective-C classes efficiently.

### Performance Results

| Scenario | Time | Notes |
|----------|------|-------|
| First run | ~12s | 9,326 classes, batch_size=35 |
| Cached run | <0.01s | 1000x+ improvement |

### Batch Size Tuning

Tested batch sizes from 10-100. Optimal is **35**:

| Batch Size | Time | Throughput | Analysis |
|------------|------|------------|----------|
| 10 | 22.1s | 421/s | Too many expression calls |
| 25 | 12.6s | 742/s | Good |
| **35** | **11.9s** | **781/s** | Optimal |
| 50 | 13.3s | 699/s | Parsing overhead increases |
| 100 | 15.7s | 593/s | Expression complexity hurts |

**Key insight:** Larger batches reduce expression count but increase per-expression parsing time. The sweet spot balances these factors.

## Implementation

### Approach
1. `objc_copyClassList()` → bulk read pointer array via `ReadMemory()`
2. Batch `class_getName()` calls using Objective-C blocks
3. Consolidate strings into single buffers
4. Cache per-process for instant subsequent queries

### Why This Works

| Operation | Speed | Notes |
|-----------|-------|-------|
| `frame.EvaluateExpression()` | 10-50ms | Very slow, minimize |
| `process.ReadMemory()` | <1ms | Fast, maximize |
| Python string ops | <1ms | Instant |

### Why Not Symbol Tables?

Symbol tables are **slower and less reliable**:
- Only 10-20% coverage in release builds (stripped symbols)
- Runtime reflection: 100% coverage on all builds
- No caching mechanism in LLDB symbol APIs

## Usage

```bash
oclasses                      # Use cache (instant after first run)
oclasses --reload             # Force refresh
oclasses --batch-size=50      # Override batch size
```
