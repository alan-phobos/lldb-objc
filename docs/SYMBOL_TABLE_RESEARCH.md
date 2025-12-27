# Symbol Table vs Runtime Reflection

## Conclusion

**Symbol tables are NOT recommended** for Objective-C method discovery. Runtime reflection is faster and more reliable.

### Comparison

| Aspect | Symbol Tables | Runtime Reflection |
|--------|---------------|-------------------|
| **Speed (first run)** | 30-120s | 10-30s |
| **Speed (cached)** | Not cached | <0.01s |
| **Coverage (release)** | 10-20% | 100% |
| **Private frameworks** | Poor | Perfect |

### Why Symbol Tables Fail

1. **Stripped binaries** - Most production builds lack debug symbols
2. **No caching** - LLDB doesn't cache symbol queries
3. **Noise** - Must filter through ALL symbols (C, C++, Swift, ObjC)
4. **Slow iteration** - Each module must be scanned separately

### When Symbol Tables Are Useful

- Cross-language symbol search (`.*network.*` across C/ObjC/Swift)
- Address-to-symbol resolution
- Debug-only analysis (line numbers, inline functions)

### LLDB Symbol APIs (Reference)

```python
# Find ObjC selectors
target.FindFunctions(name, lldb.eFunctionNameTypeSelector)

# Iterate module symbols
for symbol in module.symbol_iter():
    if symbol.GetName().startswith('-['):
        # Instance method
        pass

# Symbol types
lldb.eSymbolTypeObjCClass      # Class symbols
lldb.eSymbolTypeObjCMetaClass  # Metaclass symbols
lldb.eSymbolTypeCode           # Method implementations
```

**Note:** There is no `eSymbolTypeObjCMethod`. Methods appear as `eSymbolTypeCode` with names like `-[Class method:]`.
