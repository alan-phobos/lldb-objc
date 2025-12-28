# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed
- Renamed `oclasses` command to `ocls` for consistency with other commands (obrk, ofind)
- Updated all documentation to reflect the new command name

## [1.0.0] - Initial Release

### Added
- **obrk**: Set breakpoints on Objective-C methods using familiar syntax (`-[Class selector:]`)
- **ofind**: Search for selectors in any Objective-C class with pattern matching support
  - Wildcard pattern matching (`*` and `?`)
  - Case-insensitive substring matching
  - Lists both instance and class methods
- **ocls** (formerly oclasses): Find and list Objective-C classes with wildcard pattern matching
  - High-performance batched implementation
  - Per-process caching for instant subsequent queries
  - Wildcard and substring pattern matching
  - Configurable batch size for performance tuning
  - Verbose mode with detailed timing metrics
- Automatic installation script (`install.py`) for `.lldbinit` management
- Versioning system
- Comprehensive documentation

### Performance
- **ocls**: Optimized class enumeration
  - First run: ~10-30 seconds for 10,000 classes
  - Cached run: <0.01 seconds (1000x+ faster)
  - Batched `class_getName()` calls with consolidated string buffers
  - Reduces expression evaluations from ~10K to ~100 (100x improvement)
  - Reduces memory reads from ~10K to ~200

### Technical Details
- Runtime resolution using `NSClassFromString`, `NSSelectorFromString`, and `class_getMethodImplementation`
- Works with private classes and methods
- Supports both instance methods (`-`) and class methods (`+`)
- LLDB Python scripting API

[Unreleased]: https://github.com/yourusername/lldb-objc/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/yourusername/lldb-objc/releases/tag/v1.0.0
