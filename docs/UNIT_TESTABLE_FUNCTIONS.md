# Unit-Testable Functions Analysis

This document identifies functions across the codebase that can be extracted and unit tested without LLDB dependencies.

## Summary

**Current State**: Most logic is tightly coupled to LLDB APIs through `frame.EvaluateExpression()` calls.

**Strategy**: Extract pure Python logic (parsing, formatting, pattern matching, validation) into testable functions, leaving LLDB API calls in thin wrapper functions.

---

## Already Unit-Testable (No Changes Needed)

These functions are **pure Python** and can be tested immediately:

### objc_utils.py

| Function | Lines | Purpose | Test Complexity |
|----------|-------|---------|-----------------|
| `unquote_string(s)` | 30-53 | Remove quotes and unescape | **Easy** - has docstring examples |
| `parse_method_signature(command)` | 56-93 | Parse `-[Class sel:]` format | **Easy** - clear input/output |
| `format_method_name(class_name, selector, is_instance)` | 281-294 | Format method as `-[Class sel]` | **Easy** - simple formatting |
| `_extract_inherited_class(symbol, class, sel, is_inst)` | 221-257 | Parse symbol for inheritance | **Medium** - regex logic |
| `extract_category_from_symbol(symbol_name)` | 260-278 | Parse category from symbol | **Medium** - regex logic |

**Total: 5 functions, ~125 lines of pure Python logic**

---

## Extractable from objc_cls.py

Functions that can be extracted or are already pure:

### Pattern Matching & Filtering

| Function | Current Lines | Purpose | Extraction Effort |
|----------|---------------|---------|-------------------|
| (embedded in `find_objc_classes`) | ~150-180 | Wildcard pattern to regex conversion | **Easy** - extract to `pattern_to_regex(pattern)` |
| (embedded in `find_objc_classes`) | ~200-250 | Class name filtering logic | **Easy** - extract to `filter_classes(classes, pattern)` |
| (embedded in `find_objc_classes`) | ~300-320 | Dylib path filtering | **Medium** - extract to `filter_by_dylib(classes, dylib_pattern)` |

### Output Formatting

| Function | Current Lines | Purpose | Extraction Effort |
|----------|---------------|---------|-------------------|
| `parse_property_attributes(attr_string)` | 663-713 | Parse Objective-C property attributes | **Already pure** - can test now |
| (embedded in command) | Various | Format output based on match count | **Medium** - extract to `format_class_output(classes, show_ivars, show_props)` |

### Estimated Extractable Logic: ~300 lines

---

## Extractable from objc_sel.py

Similar pattern matching logic exists here:

| Function | Current Lines | Purpose | Extraction Effort |
|----------|---------------|---------|-------------------|
| (embedded) | ~120-150 | Wildcard pattern to regex | **Easy** - same as ocls, can share |
| (embedded) | ~180-220 | Selector filtering | **Easy** - extract to `filter_selectors(sels, pattern)` |
| (embedded) | ~250-300 | Format selector output | **Medium** - extract formatting logic |

### Estimated Extractable Logic: ~200 lines

---

## Extractable from objc_watch.py

| Function | Current Lines | Purpose | Extraction Effort |
|----------|---------------|---------|-------------------|
| `format_register_value(...)` | 155-180 | Format register values | **Already pure** - minor LLDB coupling |
| (embedded) | Various | Parse watch options | **Easy** - extract to `parse_watch_options(command)` |

### Estimated Extractable Logic: ~100 lines

---

## Extractable from objc_instance.py

| Function | Current Lines | Purpose | Extraction Effort |
|----------|---------------|---------|-------------------|
| `format_object_inspection(...)` | 245-290 | Format object details | **Medium** - extract pure formatting |
| (embedded) | ~50-80 | Parse address/variable/expression | **Easy** - extract to `parse_object_reference(ref)` |

### Estimated Extractable Logic: ~150 lines

---

## Priority Extraction Plan

### Phase 1: Quick Wins (Already Pure or Trivial)
1. ✅ `objc_utils.py` - 5 functions already testable (~125 lines)
2. ✅ `parse_property_attributes()` from `objc_cls.py` (~50 lines)

**Immediate value: ~175 lines of tested code**

### Phase 2: Pattern Matching (High Reuse Value)
3. Extract `pattern_to_regex(pattern)` - shared by ocls, osel, oprotos
4. Extract `filter_by_pattern(items, pattern)` - generic filtering
5. Extract `parse_command_flags(command, valid_flags)` - generic flag parser

**Estimated: ~150 lines, reused across 3+ commands**

### Phase 3: Command-Specific Logic
6. Extract parsing and formatting from each command
7. Focus on obrk first (reference implementation)

**Estimated: ~400 lines across all commands**

---

## Testing Strategy by Category

### String Parsing Tests (pytest)
```python
def test_parse_method_signature_instance():
    is_inst, cls, sel, err = parse_method_signature('-[NSString length]')
    assert is_inst == True
    assert cls == 'NSString'
    assert sel == 'length'
    assert err is None

def test_parse_method_signature_invalid():
    is_inst, cls, sel, err = parse_method_signature('invalid')
    assert err is not None
    assert 'Expected' in err
```

### Pattern Matching Tests (pytest)
```python
def test_pattern_to_regex_wildcard():
    regex = pattern_to_regex('IDS*')
    assert regex.match('IDSService')
    assert regex.match('IDS')
    assert not regex.match('NSString')

def test_pattern_to_regex_exact():
    regex = pattern_to_regex('NSString')
    assert regex.match('NSString')
    assert not regex.match('NSStringExtra')
```

### Formatting Tests (pytest)
```python
def test_format_method_name_instance():
    result = format_method_name('NSString', 'length', True)
    assert result == '-[NSString length]'

def test_format_method_name_class():
    result = format_method_name('NSDate', 'date', False)
    assert result == '+[NSDate date]'
```

### Regex/Symbol Tests (pytest)
```python
def test_extract_inherited_class():
    inherited = _extract_inherited_class(
        '-[NSObject hash]', 'NSString', 'hash', True
    )
    assert inherited == 'NSObject'

def test_extract_category_from_symbol():
    cls, cat, sel = extract_category_from_symbol(
        '-[NSString(Addition) isEmpty]'
    )
    assert cls == 'NSString'
    assert cat == 'Addition'
    assert sel == 'isEmpty'
```

---

## Recommended New File Structure

```
scripts/
├── objc_utils.py              # LLDB-dependent utilities (keep as-is)
├── objc_core.py               # NEW: Pure Python utilities
│   ├── parse_method_signature()      # Move from objc_utils
│   ├── format_method_name()          # Move from objc_utils
│   ├── unquote_string()              # Move from objc_utils
│   ├── extract_inherited_class()     # Move from objc_utils
│   ├── extract_category_from_symbol() # Move from objc_utils
│   ├── pattern_to_regex()            # Extract from multiple commands
│   ├── filter_by_pattern()           # Extract from multiple commands
│   ├── parse_command_flags()         # Extract from multiple commands
│   └── parse_property_attributes()   # Move from objc_cls
├── objc_breakpoint.py         # Command entry point (LLDB-dependent)
├── objc_cls.py                # Command entry point (LLDB-dependent)
└── ...
```

**Rationale**:
- `objc_core.py` - Pure Python, 100% unit testable
- `objc_utils.py` - LLDB-dependent (resolve_method_address, etc.)
- Commands import from both as needed

---

## Immediate Next Steps

1. **Create `tests/unit/` directory structure**
2. **Write tests for existing pure functions** (5 functions in objc_utils.py)
3. **Extract pattern matching logic** (high value, reused across commands)
4. **Refactor obrk** as reference implementation
5. **Migrate pure functions to objc_core.py** (optional, can test in place first)

---

## Expected Test Coverage Breakdown

After full extraction:

| Category | Functions | Lines | LLDB? | Test Type |
|----------|-----------|-------|-------|-----------|
| Pure Python Logic | ~15-20 | ~600 | ❌ | Unit (pytest) |
| LLDB Data Extraction | ~10-15 | ~800 | ✅ | Integration (current tests) |
| Command Entry Points | ~10 | ~400 | ✅ | Integration (current tests) |

**Target**: 40-50% of codebase as pure, unit-testable Python logic.
