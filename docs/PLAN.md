# Feature Roadmap

## Completed

| Command | Description | Status |
|---------|-------------|--------|
| `obrk` | Set breakpoints on ObjC methods | ✅ Done |
| `ofind` | Find methods in a class | ✅ Done |
| `ocls` | Find classes by pattern | ✅ Done (optimized + hierarchy) |
| Class hierarchy display | Show inheritance chain | ✅ Done (integrated into `ocls`) |

## Next Up

### 1. `ofind` Performance Optimization
Apply `ocls` batching pattern to method enumeration.
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

### 4. ~~`oclass` - Class Inspector~~ ✅ Completed (integrated into `ocls`)
Hierarchy display is now integrated into `ocls`:
- 1 match: Shows detailed hierarchy
- 2-20 matches: Compact hierarchy for each
- Use `ofind` for method discovery

### 5. `owatch` - Method Watcher
Auto-logging breakpoints without stopping.
```bash
owatch -[NSUserDefaults setObject:forKey:]
```

## Known Issues

### Bitfield Position Tracking
The `--ivars` output shows bitfields with their bit width (e.g., `(1 bit)`) but not their position within the byte. Multiple bitfields at the same byte offset are displayed without indicating which bit each occupies:
```
0x034  _allowLocalDelivery  (1 bit)
0x034  _allowWiProxDelivery  (1 bit)
0x034  _allowMagnetDelivery  (1 bit)
```

**Limitation**: The Objective-C runtime's `ivar_getOffset()` only returns the byte offset, not the bit position. The bit layout is determined by the compiler and not directly exposed through the runtime API.

**Possible solutions**:
1. Parse DWARF debug info (if available) for exact bit positions
2. Use `@encode()` heuristics to infer packing order
3. Accept the limitation and document that bit positions are compiler-dependent

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
