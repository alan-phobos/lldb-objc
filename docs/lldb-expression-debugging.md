# NSExpression API Runtime Tracing: Entry and Exit Breakpoints

## Executive Summary

NSExpression is a powerful component of Apple's Foundation framework that enables dynamic expression evaluation at runtime. This document identifies the key functions in the NSExpression API and recommends optimal entry and exit breakpoints for tracing invocations during runtime debugging. The primary entry point is the expression initialization phase, while the critical exit point is the `expressionValueWithObject:context:` evaluation method.

## Overview of NSExpression

NSExpression is a class provided by Apple's Foundation framework designed to dynamically evaluate expressions, perform operations, and execute calculations based on user inputs or changing data. Unlike traditional hardcoded logic, NSExpression allows developers to create flexible, runtime-evaluated expressions that can be constructed from strings or programmatically built using the API.

NSExpression is commonly used in conjunction with NSPredicate for filtering collections, performing mathematical calculations, and even executing arbitrary methods through the Objective-C runtime. This flexibility makes it a powerful tool for both legitimate application development and security research.

## Key Functions in the NSExpression API

### 1. Expression Creation Methods

**NSExpression(format:)** / **expressionWithFormat:**
The format-based initializer is the most common entry point for creating expressions. It accepts a string representation of an expression and parses it into an executable NSExpression object. This method supports a wide range of operations including arithmetic, function calls, and key path references.

```objective-c
NSExpression *expr = [NSExpression expressionWithFormat:@"4 + 5 * 2"];
```

**expressionForConstantValue:**
Creates an expression representing a constant value. This is the simplest form of NSExpression and is often used as arguments to more complex expressions.

```objective-c
NSExpression *constant = [NSExpression expressionForConstantValue:@42];
```

**init(forFunction:arguments:)** / **expressionForFunction:arguments:**
This method creates an expression that invokes one of NSExpression's predefined or custom functions. It's particularly powerful because in macOS 10.5 and later, it supports arbitrary method invocations using the syntax `FUNCTION(receiver, selectorName, arguments, ...)`.

```objective-c
NSExpression *funcExpr = [NSExpression expressionForFunction:@"sum:"
                                                    arguments:@[array1, array2]];
```

### 2. Expression Evaluation Method

**expressionValueWithObject:context:**
This is the critical evaluation method that executes the expression and returns a result. It takes two parameters: an object against which to evaluate the expression (often used for key path evaluation) and a context dictionary (typically nil for simple expressions).

```objective-c
id result = [expr expressionValueWithObject:nil context:nil];
```

This method is where the actual computation happens, making it the essential exit point for runtime tracing.

### 3. Built-in Functions

NSExpression provides numerous built-in functions including:

- **Arithmetic**: `add:to:`, `from:subtract:`, `multiply:by:`, `divide:by:`, `modulus:by:`
- **Mathematical**: `sqrt:`, `log:`, `ln:`, `raise:toPower:`, `exp:`, `abs:`, `floor:`, `ceiling:`, `trunc:`
- **Statistical**: `average:`, `sum:`, `count:`, `min:`, `max:`, `median:`, `mode:`, `stddev:`
- **String**: `uppercase:`, `lowercase:`
- **Bitwise**: `bitwiseAnd:with:`, `bitwiseOr:with:`, `bitwiseXor:with:`, `leftshift:by:`, `rightshift:by:`, `onesComplement:`
- **Utility**: `random`, `random:`, `now`

### 4. Custom Function Support

NSExpression supports custom functions through the Objective-C runtime, allowing arbitrary method invocations. This feature enables powerful dynamic behavior but also presents security considerations when processing untrusted input.

```objective-c
// Example: FUNCTION(@"/Developer/Tools/otest", @"lastPathComponent")
NSExpression *custom = [NSExpression expressionWithFormat:
    @"FUNCTION('/path/to/file', 'lastPathComponent')"];
```

## Recommended Breakpoint Strategy

### Entry Breakpoint: Expression Initialization

**Primary Entry Point:** `+[NSExpression expressionWithFormat:]`

This class method is the most common entry point for NSExpression usage. Setting a breakpoint here allows you to:

- Capture the expression string before parsing
- Inspect the call stack to understand where expressions are being created
- Log all expression formats for security auditing
- Detect potentially malicious expression injection

**LLDB Breakpoint Command:**
```
breakpoint set --name "+[NSExpression expressionWithFormat:]"
```

**Alternative Entry Points:**
- `+[NSExpression expressionForFunction:arguments:]` - For function-based expressions
- `+[NSExpression expressionForConstantValue:]` - For constant expressions
- `-[NSExpression initWithExpressionType:]` - Lower-level initializer

**Why This Entry Point?**
The initialization phase is where NSExpression objects are created from external input. This is the ideal location to intercept and inspect expressions before they are evaluated. For security research, this allows detection of injection attempts. For debugging, it provides visibility into what expressions are being constructed.

### Exit Breakpoint: Expression Evaluation

**Primary Exit Point:** `-[NSExpression expressionValueWithObject:context:]`

This instance method is where expressions are actually evaluated and produce results. Setting a breakpoint here allows you to:

- Inspect the evaluated result before it's returned
- Measure evaluation performance
- Detect runtime errors or exceptions
- Trace the complete lifecycle of an expression from creation to evaluation

**LLDB Breakpoint Command:**
```
breakpoint set --name "-[NSExpression expressionValueWithObject:context:]"
```

**Why This Exit Point?**
The evaluation method represents the culmination of NSExpression's purpose. Every expression, regardless of how it was created, must eventually call this method to produce a result. This makes it the universal exit point for tracing NSExpression behavior.

By placing breakpoints at both the entry (initialization) and exit (evaluation) points, you create a complete trace of NSExpression invocations, capturing both the input (expression format) and output (evaluated result).

## Runtime Tracing Implementation

### Using LLDB Conditional Breakpoints

To implement comprehensive runtime tracing without stopping execution, use LLDB breakpoint commands:

```
breakpoint set --name "+[NSExpression expressionWithFormat:]"
breakpoint command add 1
po $arg2
continue
DONE

breakpoint set --name "-[NSExpression expressionValueWithObject:context:]"
breakpoint command add 2
po $arg0
po [$arg0 expressionValueWithObject:$arg2 context:$arg3]
continue
DONE
```

### Method Swizzling Approach

For production runtime tracing, method swizzling provides a powerful alternative. By swizzling the entry and exit methods, you can inject logging or monitoring code:

```objective-c
#import <objc/runtime.h>

+ (void)load {
    static dispatch_once_t onceToken;
    dispatch_once(&onceToken, ^{
        Class class = [NSExpression class];

        SEL originalSelector = @selector(expressionValueWithObject:context:);
        SEL swizzledSelector = @selector(swizzled_expressionValueWithObject:context:);

        Method originalMethod = class_getInstanceMethod(class, originalSelector);
        Method swizzledMethod = class_getInstanceMethod(class, swizzledSelector);

        method_exchangeImplementations(originalMethod, swizzledMethod);
    });
}

- (id)swizzled_expressionValueWithObject:(id)object context:(NSMutableDictionary *)context {
    NSLog(@"[TRACE] Evaluating expression: %@", self);
    id result = [self swizzled_expressionValueWithObject:object context:context];
    NSLog(@"[TRACE] Result: %@", result);
    return result;
}
```

## Security Considerations

NSExpression's ability to execute arbitrary methods through the `FUNCTION()` syntax makes it a potential vector for code injection attacks. When processing untrusted input, always:

1. Validate expression strings before passing to `expressionWithFormat:`
2. Restrict available functions using allowlists
3. Consider using NSPredicate's more restrictive function set
4. Monitor expressions containing `FUNCTION` keywords
5. Set breakpoints on evaluation to detect suspicious behavior

## NSExpression in Exploitation Context

### NSKeyedUnarchiver Deserialization Gadgets

NSExpression has been weaponized in real-world exploits through deserialization attacks. Deserializing untrusted archives can instantiate arbitrary classes implementing NSCoding. Gadget classes like NSSortDescriptor accept selectors enabling method invocation chains.

The FORCEDENTRY exploit used NSKeyedArchive deserialization to trigger NSFunctionExpression evaluation. This demonstrates how NSExpression can serve as a powerful gadget in exploitation chains, particularly when combined with deserialization vulnerabilities.

### JBIG2 VM Chain

In the FORCEDENTRY exploit, a Turing-complete CPU was built from 70,000+ JBIG2 segment commands. This JBIG2 VM's only job was to trigger NSFunctionExpression deserialization. The zero-click exploit worked via iMessage with PDF files disguised as GIFs to bypass BlastDoor. (NSO/Project Zero 2021, CVE-2021-30860)

## Conclusion

NSExpression provides a sophisticated API for runtime expression evaluation in Objective-C and Swift applications. The recommended breakpoint strategy focuses on two critical methods:

- **Entry:** `+[NSExpression expressionWithFormat:]` - Captures expression creation
- **Exit:** `-[NSExpression expressionValueWithObject:context:]` - Captures evaluation and results

This dual-breakpoint approach provides complete visibility into NSExpression usage, enabling effective debugging, performance analysis, and security monitoring. Whether using LLDB breakpoints for development debugging or method swizzling for production monitoring, these two methods represent the essential chokepoints for tracing NSExpression invocations at runtime.

## References and Further Reading

- [NSExpression - NSHipster](https://nshipster.com/nsexpression/)
- [Evaluating Expressions in iOS with Objective-C and Swift](https://spin.atomicobject.com/2015/03/24/evaluate-string-expressions-ios-objective-c-swift/)
- [NSExpression | Apple Developer Documentation](https://developer.apple.com/documentation/foundation/nsexpression)
- [expressionValueWithObject:context: | Apple Developer Documentation](https://developer.apple.com/documentation/foundation/nsexpression/1410363-expressionvaluewithobject)
- [See No Eval: Runtime Dynamic Code Execution in Objective-C | CodeColorist](https://codecolor.ist/2021/01/16/see-no-eval-runtime-code-execution-objc/)
- [Method Swizzling - NSHipster](https://nshipster.com/method-swizzling/)
- [Advanced Apple Debugging & Reverse Engineering | Kodeco](https://www.kodeco.com/books/advanced-apple-debugging-reverse-engineering/v3.0/chapters/17-exploring-method-swizzling-objective-c-frameworks)
