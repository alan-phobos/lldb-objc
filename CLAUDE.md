# LLDB Objective-C Tools

LLDB commands for Objective-C runtime introspection, including private classes/methods.

## Commands

| Command | Purpose | Key Flags |
|---------|---------|-----------|
| `obrk` | Set breakpoints | `obrk -[Class sel:]` or `obrk +[Class method:]` |
| `osel` | Find methods | `--instance`, `--class`, `--reload`, `--verbose` |
| `ocls` | Find classes | `--ivars`, `--properties`, `--dylib`, `--batch-size=N` |
| `ocall` | Call methods | Supports `@"string"`, `@42`, expressions |
| `owatch` | Auto-log breakpoints | `--minimal`, `--stack` |
| `oprotos` | Protocol conformance | `--list [pattern]` |

### Quick Examples
```bash
ocls IDS*                           # Classes starting with IDS
ocls NSString --ivars --properties  # Show class details
ocls --dylib CoreFoundation CF*     # Classes from specific dylib
osel IDSService send*               # Methods matching pattern
osel NSString --instance *init*     # Instance methods only
obrk -[IDSService sendMessage:]     # Set breakpoint
owatch --minimal -[NSString init]   # Watch with timestamps
oprotos --list *Delegate            # List delegate protocols
```

## Installation
```bash
./install.py              # Install to ~/.lldbinit
./install.py --uninstall  # Remove
```

## Project Structure
```
objc_breakpoint.py  # obrk     objc_watch.py   # owatch
objc_sel.py         # osel     objc_protos.py  # oprotos
objc_cls.py         # ocls     objc_utils.py   # shared utilities
objc_call.py        # ocall    install.py      # installer
tests/              # test suite (run_all_tests.py)
```

## Performance Strategy
- `frame.EvaluateExpression()` is slow (10-50ms) → minimize
- `process.ReadMemory()` is fast (<1ms) → maximize
- Batch using Objective-C blocks, optimal batch size: **35**
- Cache per-process: first run ~12s, cached <0.01s

## Development Guidelines

### Adding Commands
1. Create `objc_<name>.py` with `__lldb_init_module()`
2. Add to `install.py`
3. Add tests in `tests/test_<name>.py`
4. Update README.md

### UI Convention
Primary info in normal text; secondary (types, hierarchy) in dim gray: `\033[90m...\033[0m`

### Common Pitfalls
- **String handling**: Use `s[1:-1]` not `strip('"')` for LLDB `GetSummary()` strings
- **F-strings with blocks**: Use `^{{` and `}}` for Objective-C blocks in f-strings

## Tests
```bash
./tests/run_all_tests.py          # All tests
./tests/run_all_tests.py --quick  # Quick subset
```

## Resolution Chain (obrk)
```
NSClassFromString() → Class → NSSelectorFromString() → SEL
→ object_getClass() (for +methods) → class_getMethodImplementation() → IMP
→ BreakpointCreateByAddress()
```

## Future Work
See [docs/PLAN.md](docs/PLAN.md) for roadmap including wildcard `osel`, `oheap`, `ocat`.
