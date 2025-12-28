# Quick Start Guide

## Installation

```bash
./install.py              # Install to ~/.lldbinit
./install.py --status     # Check installation status
./install.py --uninstall  # Remove from ~/.lldbinit
```

Or load manually:
```
(lldb) command script import /path/to/objc_breakpoint.py
(lldb) command script import /path/to/objc_find.py
(lldb) command script import /path/to/objc_cls.py
```

## Commands

### Find Classes (`ocls`)
```bash
ocls                    # List all classes (cached after first run)
ocls IDS*               # Classes starting with "IDS"
ocls *Service           # Classes ending with "Service"
ocls --reload           # Force cache refresh
```

### Find Methods (`ofind`)
```bash
ofind IDSService            # List all methods
ofind IDSService send       # Filter by pattern
ofind NSString              # Works with any class
```

### Set Breakpoints (`obrk`)
```bash
obrk -[IDSService sendMessage:]    # Instance method
obrk +[NSDate date]                # Class method
```

## Typical Workflow

1. **Discover classes:**
   ```
   ocls IDS*
   ```

2. **Explore methods:**
   ```
   ofind IDSService
   ofind IDSService send
   ```

3. **Set breakpoint:**
   ```
   obrk -[IDSService sendMessage:]
   ```

4. **Continue and debug:**
   ```
   continue
   ```

## Key Features

- **Private class/method support** via runtime resolution
- **Caching** for instant subsequent queries
- **Wildcard patterns** for class discovery
- **Works on stripped binaries** (runtime reflection, not symbol tables)
