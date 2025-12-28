# UI Conventions

This document describes the visual styling conventions used in the LLDB Objective-C tools to ensure consistent, readable output across all commands.

## ANSI Color Codes

The project uses ANSI escape codes for terminal color output:
- `\033[90m` - Bright black (dim gray) - used for secondary/auxiliary information
- `\033[0m` - Reset - returns to normal terminal color

## Convention: Primary vs. Secondary Information

**Principle**: Primary information (the main subject) is displayed in normal text, while secondary/auxiliary information (metadata, attributes, context) is displayed in dim gray.

### Examples

#### Class Hierarchy Display
When showing class inheritance chains:
```
ClassName → Superclass → NSObject
```
- **Primary**: The target class name (`ClassName`)
- **Secondary**: The inheritance chain (`→ Superclass → NSObject`)

Implementation:
```python
print(f"  {hierarchy[0]} \033[90m→ {hierarchy_str}\033[0m")
```

#### Property Display
When showing Objective-C properties:
```
propertyName NSString (readonly, nonatomic)
```
- **Primary**: The property name (`propertyName`)
- **Secondary**: The type and attributes (`NSString (readonly, nonatomic)`)

Implementation:
```python
print(f"    {prop_name} \033[90m{type_str} ({attrs_str})\033[0m")
```

#### Instance Variable Display
When showing instance variables (ivars):
```
_ivarName NSString
```
- **Primary**: The ivar name (`_ivarName`)
- **Secondary**: The type (`NSString`)

Implementation:
```python
print(f"    {ivar_name} \033[90m{ivar_type}\033[0m")
```

## Guidelines for Future Features

When adding new output features:

1. **Identify the primary subject** - What is the user looking for? (class name, property name, method name, etc.)
2. **Display primary information in normal text** - No color codes
3. **Display metadata in dim gray** - Types, attributes, inheritance, counts, etc.
4. **Use consistent spacing** - Separate primary and secondary with a space
5. **Comment your code** - Include the ANSI codes comment for clarity:
   ```python
   # ANSI escape codes: \033[90m = bright black (dim gray), \033[0m = reset
   ```

## Rationale

This visual hierarchy helps users:
- Quickly scan for the information they're searching for (primary)
- See relevant context without visual clutter (secondary, dimmed)
- Distinguish between different types of information at a glance
- Maintain readability even with dense output

The dim gray color (`\033[90m`) was chosen because:
- It's supported by all modern terminals
- It's readable but clearly de-emphasized
- It doesn't conflict with other common terminal colors (errors, warnings)
- It maintains sufficient contrast for accessibility
