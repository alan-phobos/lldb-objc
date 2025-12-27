# HelloWorld Example

A simple Objective-C program for testing LLDB commands (`obrk`, `ofind`, etc.).

## Contents

- `HelloWorld/main.m` - Source code with a simple Greeter class
- `HelloWorld/HelloWorld` - Compiled binary (built with clang)
- `Makefile` - Build automation

## Directory Structure

```
examples/HelloWorld/
├── Makefile              # Build automation
├── README.md             # This file
└── HelloWorld/           # Source directory
    ├── main.m            # Objective-C source
    └── HelloWorld        # Compiled binary (output)
```

## Building

The HelloWorld binary is compiled manually using clang (not via Xcode):

```bash
# Build the binary
make

# Or manually with clang:
clang -framework Foundation -g -fobjc-arc -o HelloWorld/HelloWorld HelloWorld/main.m
```

### Build flags explained:
- `-framework Foundation` - Link against Foundation framework for Objective-C runtime
- `-g` - Include debug symbols (required for LLDB)
- `-fobjc-arc` - Enable Automatic Reference Counting
- `-o HelloWorld/HelloWorld` - Output binary to HelloWorld directory

## Running

```bash
# Run directly
./HelloWorld/HelloWorld

# Or use make
make run
```

## Testing with LLDB

This binary is used by the test scripts in `tests/`:

```bash
# Bootstrap LLDB with HelloWorld loaded
cd ../../tests
./test_bootstrap.py
# or
./test_bootstrap.sh
```

Once in LLDB, you can test commands like:
```
obrk -[Greeter sayHello:]
obrk -[Greeter add:to:]
ofind Greeter
```

## Clean

```bash
make clean
```
