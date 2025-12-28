# LLDB Objective-C Automation Project

## Goal
Create an LLDB command that sets breakpoints on Objective-C methods using the format `-[Class selector]`, including support for private symbols.

## Approach
Since private symbols aren't directly accessible, we need to:
1. Use `NSClassFromString()` to resolve the class at runtime
2. Use `NSSelectorFromString()` to resolve the selector
3. Use `class_getMethodImplementation()` to get the actual IMP (implementation pointer)
4. Set a breakpoint on that address

## Current Status
- ✅ Initial implementation complete
- ✅ Created [objc_breakpoint.py](objc_breakpoint.py) with `obrk` command
- ✅ Debug output cleaned up and professionalized
- ✅ Command shows Class, SEL, and IMP values during resolution
- ✅ Production-ready with minimal, informative output
- ✅ Created [objc_sel.py](objc_sel.py) with `osel` command for selector discovery
- ✅ Implemented pattern matching and filtering for selector search
- ✅ Support for both instance and class method enumeration
- ✅ Added versioning system (v1.0.0)
- ✅ Created automatic installation script (install.py) for .lldbinit management
- ✅ Created [objc_cls.py](objc_cls.py) with `ocls` command for class discovery
- ✅ **Optimized implementation**: Batched class_getName() calls with consolidated string buffers
  - Uses compound expressions to batch 100 class_getName() calls at once
  - Consolidates class name strings into single buffers to minimize memory reads
  - Reduces expression evaluations from ~10K to ~100 (100x improvement!)
  - Reduces memory reads from ~10K to ~200
  - Includes graceful fallback for individual class processing if batch expressions fail
  - For 10,000 classes: typical performance is 10-30 seconds
- ✅ **Caching layer**: Per-process caching for instant subsequent queries
  - First run: ~10-30 seconds for 10K classes
  - Cached run: <0.01 seconds (1000x+ improvement!)
  - `--reload` flag to refresh cache when runtime state changes
  - `--clear-cache` flag to clear cache for current process
  - Automatic per-process isolation
- ✅ **Comprehensive timing metrics**: Reports detailed performance statistics
  - Shows total execution time and timing breakdown by operation phase (setup, bulk_read, batching, cleanup)
  - Reports expression evaluation count and memory read count
  - Indicates when results are from cache vs. fresh enumeration
  - Helps track optimization improvements
- ✅ **Automatic hierarchy display**: Shows class inheritance based on match count
  - 1 match: Detailed hierarchy view (e.g., "UIViewController → UIResponder → NSObject")
  - 2-20 matches: Compact one-liner hierarchy for each class
  - 21+ matches: Simple class name list
  - Uses `class_getSuperclass()` to walk the inheritance chain

## Learnings
- **Debug output needs actual values**: Don't just show if result is valid/error - need to see the actual Class/SEL/IMP values returned
- SBValue methods to use:
  - `GetValue()` - string representation of the value
  - `GetValueAsUnsigned()` - numeric value
  - `GetSummary()` - summary description
  - Need to print ALL of these to see what we're actually getting back
- **Performance optimization insights** (from ocls development):
  - `frame.EvaluateExpression()` is VERY slow (10-50ms per call)
  - `process.ReadMemory()` is fast (<1ms)
  - `process.ReadCStringFromMemory()` is fast (<1ms)
  - Bulk memory reads dramatically outperform individual expression evaluations
  - Compound expressions can batch multiple function calls into one evaluation
  - Consolidating strings into buffers eliminates per-string memory read overhead
  - **Performance for 10K classes**:
    - Naive: 20K expression calls = 3-16 minutes
    - Optimized (batch_size=35): ~540 expressions + ~540 memory reads = ~12 seconds
    - Cached: <0.01 seconds (1000x+ faster!)
  - **Batch size tuning** (tested 10-100, optimal is ~35):
    - Too small (10-20): too many expression calls
    - Too large (75-100): expression parsing overhead dominates
    - Sweet spot (30-40): balances expression count vs parsing complexity
  - **Key insights**:
    - Minimize expression evaluations at all costs, maximize memory reads, batch everything
    - Cache aggressively - runtime state changes infrequently
    - Use Objective-C blocks for compound expressions (GCC statement expressions not supported)
    - Configurable batch size via `--batch-size=N` or `--batch-size N` flag (supports both syntaxes)
    - Provide manual cache control for when state does change
    - **Fast-path for exact matches**: Use `NSClassFromString()` directly for non-wildcard patterns to bypass full enumeration
    - **Strict matching by default**: Exact match (case-sensitive) without wildcards prevents unwanted partial matches
  - **Performance for `--ivars` and `--properties` flags** (IDSServiceProperties with 91 ivars, 95 properties):
    - Before optimization: ~1.87s for ivars (~20ms per ivar), ~1.35s for properties (~14ms per property)
    - After optimization: ~1.72s for ivars (~19ms per ivar), ~1.16s for properties (~12ms per property)
    - Optimization strategy: Single batch expression fetches all pointers, then bulk memory reads for strings
    - Expression count reduction: 273 expressions → 6 expressions for ivars (45x reduction)
    - Expression count reduction: 190 expressions → 6 expressions for properties (31x reduction)
    - **Trade-off**: While expression count drops dramatically, large batch expressions have parsing overhead
    - **Result**: 8-14% performance improvement (modest but consistent)
    - **Key takeaway**: For features like ivars/properties where counts are typically <100, single-batch approach is acceptable

## Project Structure

```
lldb-objc/
├── objc_breakpoint.py          # LLDB command for setting breakpoints
├── objc_sel.py                 # LLDB command for finding selectors
├── objc_cls.py                 # LLDB command for finding classes (optimized)
├── version.py                  # Version information
├── install.py                  # Installation script for .lldbinit
├── VERSION                     # Version number file
├── README.md                   # Main documentation and usage guide
├── CLAUDE.md                   # Project context and implementation notes
├── docs/                       # Documentation
│   ├── IMPLEMENTATION_NOTES.md
│   ├── PLAN.md                 # Future feature roadmap
│   ├── PERFORMANCE_ANALYSIS.md # Performance optimization analysis
│   ├── CACHING_AND_PERFORMANCE.md # Caching implementation details
│   ├── BEFORE_AFTER.md         # Visual comparison of improvements
│   ├── UI_CONVENTIONS.md       # Visual styling conventions for output
│   ├── QUICKSTART.md
│   └── research.md
├── tests/                      # Test files and test cases
│   ├── test_bootstrap.py
│   ├── test_bootstrap.sh
│   └── test_runner.md
└── examples/                   # Example projects
    └── HelloWorld/             # Sample Xcode project for testing
```

### Installation
Use the `install.py` script to automatically configure `.lldbinit`:
```bash
./install.py              # Install to ~/.lldbinit
./install.py --status     # Check installation status
./install.py --uninstall  # Remove from ~/.lldbinit
```

### Command Syntax
```
# Set breakpoints
obrk -[ClassName selector:]
obrk +[ClassName classMethod:]

# Find selectors
osel ClassName
osel ClassName pattern

# Find classes (with wildcard support, caching, fast-path, and automatic hierarchy display)
ocls                        # List all classes (cached after first run)
ocls IDSService             # Exact match (case-sensitive, fast-path: <0.01s)
ocls IDS*                   # Wildcard: classes starting with "IDS"
ocls *Service               # Wildcard: classes containing "Service" anywhere
ocls *Navigation*           # Wildcard: classes containing "Navigation"
ocls UIViewController       # Exact match shows full hierarchy (fast-path)
ocls --reload               # Force reload from runtime, refresh cache
ocls --reload IDS*          # Reload and filter
ocls --clear-cache          # Clear cache for current process
ocls --verbose IDS*         # Show detailed timing breakdown
ocls --batch-size=50 --reload   # Performance tuning: use larger batches
ocls --batch-size 25 --reload   # Both syntaxes supported

# Matching rules:
# - No wildcards: exact match (case-sensitive) - uses fast-path NSClassFromString lookup
# - With wildcards: pattern match (case-insensitive)

# Output adapts to number of matches:
# - 1 match: Shows detailed hierarchy (e.g., "UIViewController → UIResponder → NSObject")
# - 2-20 matches: Shows compact one-liner hierarchy for each class
# - 21+ matches: Simple class name list
```

### Resolution Chain (obrk)
1. Parse input to extract class name and selector
2. Distinguish instance (`-`) vs class (`+`) methods
3. `NSClassFromString()` → Get Class pointer
4. `NSSelectorFromString()` → Get SEL pointer
5. For class methods: `object_getClass()` → Get metaclass
6. `class_getMethodImplementation()` → Get IMP address
7. `BreakpointCreateByAddress()` → Set breakpoint

### Selector Discovery Chain (osel)
1. Parse input to extract class name and optional pattern
2. `NSClassFromString()` → Get Class pointer
3. `class_copyMethodList()` → Get list of instance methods
4. `object_getClass()` → Get metaclass
5. `class_copyMethodList()` → Get list of class methods
6. For each method: `method_getName()` → Get selector
7. `sel_getName()` → Convert SEL to string
8. Filter by pattern (case-insensitive substring match)
9. Display sorted lists of instance and class methods

### Class Discovery Chain (ocls) - Optimized with Caching
1. Parse input to extract optional pattern and flags (`--reload`, `--clear-cache`)
2. **Check cache**: If cached and not force-reload, filter from cache and return (<0.01s)
3. If not cached or force-reload:
   a. `objc_copyClassList()` → Get array of all class pointers + count
   b. Bulk read entire class pointer array via `process.ReadMemory()` (eliminates 10K expression calls)
   c. Parse array in Python using `struct.unpack()` (fast, no LLDB overhead)
   d. Batch class pointers into groups of 100
   e. For each batch: Build compound expression that:
      - Calls `class_getName()` for 100 classes
      - Consolidates all strings into a single buffer with offset table
   f. Execute batch expression → Returns consolidated buffer (ONE expression call!)
   g. Bulk read offset table and string data via `process.ReadMemory()`
   h. Parse strings from consolidated buffer in Python
   i. **Store in cache** (per-process, unfiltered list)
4. Filter by pattern (wildcard or substring matching) from cached or fresh list
5. Display sorted list of matching classes with performance metrics
6. **Performance**:
   - First run: ~100 expression calls + ~200 memory reads for 10K classes (10-30s)
   - Cached run: 0 expressions, instant filtering (<0.01s)

## Technical Notes
- LLDB Python scripting API will be used
- Runtime resolution is necessary for private classes/methods
- Need to handle both instance and class methods

## Development Guidelines
- **When adding new commands**: Always update the following:
  1. **install.py** - Add the new command script to the lldbinit configuration
  2. **README.md** - Document the new command syntax, usage, and examples
  3. **CLAUDE.md** - Update Project Structure and Command Syntax sections as needed
  4. **CHANGELOG.md** - Document the new feature in the Unreleased section

- **When completing a feature**: Prompt the user to update the version number:
  - Ask if the feature completion warrants a version bump
  - Update VERSION file and version.py if needed
  - Move CHANGELOG entries from Unreleased to the new version section
  - Follow semantic versioning: MAJOR.MINOR.PATCH
    - MAJOR: Breaking changes
    - MINOR: New features (backward compatible)
    - PATCH: Bug fixes (backward compatible)

## UI Conventions
The project follows consistent visual styling for terminal output. See [docs/UI_CONVENTIONS.md](docs/UI_CONVENTIONS.md) for complete details.

**Key principle**: Primary information (the main subject) is displayed in normal text, while secondary/auxiliary information (metadata, attributes, context) is displayed in dim gray using ANSI escape code `\033[90m`.

**Examples**:
- **Class hierarchy**: `ClassName` (normal) + `→ Superclass → NSObject` (dim)
- **Properties**: `propertyName` (normal) + `NSString (readonly, nonatomic)` (dim)
- **Instance variables**: `_ivarName` (normal) + `NSString` (dim)

When adding new output features, follow this convention to maintain consistent visual hierarchy across all commands.

## Future Work
See [docs/PLAN.md](docs/PLAN.md) for a comprehensive roadmap of planned features and enhancements, including:
- **High priority features**: Wildcard support for `osel`, method caller (`ocall`), class hierarchy viewer (`oclass`), method watcher (`owatch`)
- **Advanced features**: Instance tracker, method swizzling, block inspector, and more

All new features in PLAN.md have detailed design specifications including technical approaches, resolution chains, implementation details, and example usage.

## Manual Hints
* Prefer using fewer calls to functions to achieve the same result as each is very slow.
* Prefer memory reads to calls where possible.

## Common Pitfalls

### Python string handling with LLDB summaries
- **Never use `strip('"')` to remove quotes from LLDB `GetSummary()` strings** - it removes ALL consecutive quotes from both ends, not just one. For type encodings like `"@\"NSString\""`, the trailing `""` gets stripped completely, leaving a corrupt backslash.
- **Correct approach**: Use `s[1:-1]` to remove exactly one character from each end, then `replace('\\"', '"')` to unescape internal quotes.

### Python f-string brace escaping
- In f-strings, `{{` produces `{` and `}}` produces `}`. A lone `}` is a syntax error.
- When building Objective-C block expressions in f-strings (e.g., `^{...}`), use `^{{` for opening and `}}` for closing.
- When appending to an f-string with a regular string (no `f` prefix), braces are literal - no escaping needed.
