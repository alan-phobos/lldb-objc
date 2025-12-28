# Related Tools Research

## Landscape Overview

| Tool | Focus | Status | Key Difference from lldb-objc |
|------|-------|--------|------------------------------|
| **Chisel** (Facebook) | View debugging | Archived (2023) | No private class support |
| **Derek Selander's LLDB** | Discovery/RE | Active | Discovery-focused, manual breakpoints |
| **Frida** | Instrumentation | Active | Different category (hooks, not debugging) |

## Feature Comparison

| Feature | lldb-objc | Chisel | Derek's LLDB | Frida |
|---------|-----------|--------|--------------|-------|
| Private class breakpoints | ✅ | ❌ | Manual | N/A |
| One-command syntax | ✅ | ✅ | ❌ | ❌ |
| Runtime resolution | ✅ | ❌ | ✅ | ✅ |
| Method discovery | ✅ | ⚠️ | ✅ | ✅ |
| View debugging | ❌ | ✅ | ❌ | ⚠️ |

## Why Build Our Own?

**Unique value:** One-command breakpoint setting on private Objective-C methods.

- Chisel's `bmessage` doesn't work for private symbols
- Derek's scripts require multiple discovery steps
- Neither provides streamlined `obrk -[PrivateClass method:]` workflow

## Key References

- **Chisel**: https://github.com/facebook/chisel (archived)
- **Derek Selander's LLDB**: https://github.com/DerekSelander/LLDB
- **Frida**: https://frida.re/
- **LLDB Python API**: https://lldb.llvm.org/use/python-reference.html
