# Feature Roadmap

## Completed

| Command | Description | Status |
|---------|-------------|--------|
| `obrk` | Set breakpoints on ObjC methods | ✅ Done |
| `ofind` | Find methods in a class | ✅ Done |
| `oclasses` | Find classes by pattern | ✅ Done (optimized) |

## Next Up

### 1. `ofind` Performance Optimization
Apply `oclasses` batching pattern to method enumeration.
- Current: N expression calls for N methods (slow)
- Target: N/35 batch calls (50-100x speedup)
- Add per-class method caching

### 2. Wildcard `ofind`
Extend `ofind` to accept wildcard class patterns.
```bash
ofind IDS* sendMessage    # Find 'sendMessage' in all IDS* classes
ofind *Service delegate   # Find 'delegate' in all *Service classes
```

### 3. `ocall` - Method Caller
Call ObjC methods from command line.
```bash
ocall +[NSDate date]
ocall -[myString uppercaseString]
```
Simple wrapper around `frame.EvaluateExpression()`.

### 4. `oclass` - Class Inspector
Display class hierarchy, ivars, properties, methods.
```bash
oclass UIViewController
oclass -ivars NSString
```

### 5. `owatch` - Method Watcher
Auto-logging breakpoints without stopping.
```bash
owatch -[NSUserDefaults setObject:forKey:]
```

## Future Ideas

| Command | Description | Complexity |
|---------|-------------|------------|
| `oinstances` | Find live instances of a class | Complex |
| `oswizzle` | Runtime method swizzling | Complex |
| `oblock` | Block inspector | Complex |
| `oprotos` | Protocol conformance finder | Simple |
| `obt` | Enhanced backtrace | Medium |

## Performance Notes

**Batch size 35 is optimal** for expression batching. See [PERFORMANCE.md](PERFORMANCE.md).

Key optimizations:
- Bulk `ReadMemory()` instead of per-item expression calls
- Objective-C blocks for compound expressions
- Per-process caching (<0.01s on subsequent queries)
