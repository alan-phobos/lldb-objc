#!/usr/bin/env python3
"""
Shared utilities for LLDB Objective-C automation scripts.

This module provides common functionality used by multiple commands:
- Method resolution (class, selector, IMP lookup)
- Method signature parsing (-[Class sel] or +[Class sel])
- String handling utilities
- Version import handling
"""

from __future__ import annotations

import lldb
import os
import sys
from typing import Optional, Tuple, List

# Add the script directory to path for version import
script_dir = os.path.dirname(os.path.abspath(__file__))
if script_dir not in sys.path:
    sys.path.insert(0, script_dir)

try:
    from version import __version__
except ImportError:
    __version__ = "unknown"


def unquote_string(s: Optional[str]) -> Optional[str]:
    """
    Remove exactly one pair of quotes from a string and unescape internal quotes.

    IMPORTANT: Never use strip('"') - it removes ALL consecutive quotes from both ends,
    corrupting strings like '"@\\"NSString\\""' to '@\\"NSString\\'.

    Args:
        s: A string that may be wrapped in double quotes

    Returns:
        The unquoted string with internal escaped quotes unescaped

    Examples:
        >>> unquote_string('"hello"')
        'hello'
        >>> unquote_string('"@\\"NSString\\""')
        '@"NSString"'
        >>> unquote_string('no quotes')
        'no quotes'
    """
    if s and len(s) >= 2 and s.startswith('"') and s.endswith('"'):
        return s[1:-1].replace('\\"', '"')
    return s


def parse_method_signature(command: str) -> Tuple[Optional[bool], Optional[str], Optional[str], Optional[str]]:
    """
    Parse a method signature like -[ClassName selector:], +[ClassName selector:], or [ClassName selector:]

    Args:
        command: The method signature string

    Returns:
        Tuple of (is_instance_method, class_name, selector, error_message)
        - is_instance_method: True for -, False for +, None for auto-detect (bare [)
        On error, all values are None except error_message
    """
    command = command.strip()

    # Determine method type based on prefix
    if command.startswith('-['):
        is_instance_method = True
        start_idx = 2
    elif command.startswith('+['):
        is_instance_method = False
        start_idx = 2
    elif command.startswith('['):
        is_instance_method = None  # Signal auto-detect needed
        start_idx = 1
    else:
        return None, None, None, "Expected -[ClassName selector:], +[ClassName selector:], or [ClassName selector:]"

    # Remove the leading prefix and trailing ]
    method_str = command[start_idx:-1] if command.endswith(']') else command[start_idx:]
    parts = method_str.split(None, 1)  # Split on first whitespace

    if len(parts) != 2:
        return None, None, None, "Invalid format. Expected: [ClassName selector:]"

    class_name = parts[0]
    selector = parts[1]

    return is_instance_method, class_name, selector, None


def resolve_method_address(
    frame: lldb.SBFrame,
    class_name: str,
    selector: str,
    is_instance_method: bool,
    verbose: bool = False
) -> Tuple[int, int, int, Optional[str]]:
    """
    Resolve an Objective-C method to its implementation address.

    Uses runtime introspection:
    1. NSClassFromString() to get Class pointer
    2. NSSelectorFromString() to get SEL pointer
    3. object_getClass() for metaclass (class methods)
    4. class_getMethodImplementation() to get IMP address

    Args:
        frame: The LLDB SBFrame to use for expression evaluation
        class_name: Name of the Objective-C class
        selector: The selector string (e.g., "initWithFrame:")
        is_instance_method: True for instance methods (-), False for class methods (+)
        verbose: If True, print resolution details

    Returns:
        Tuple of (imp_address, class_ptr, sel_ptr, error_message)
        On error, addresses are 0 and error_message describes the issue
    """
    # Step 1: Get the class using NSClassFromString
    class_expr = f'(Class)NSClassFromString(@"{class_name}")'
    class_result = frame.EvaluateExpression(class_expr)

    if not class_result.IsValid() or class_result.GetError().Fail():
        return 0, 0, 0, f"Failed to resolve class '{class_name}': {class_result.GetError()}"

    class_ptr = class_result.GetValueAsUnsigned()

    if verbose:
        print(f"  Class: {class_result.GetValue()}")

    if class_ptr == 0:
        return 0, 0, 0, f"Class '{class_name}' not found"

    # Step 2: Get the selector using NSSelectorFromString
    sel_expr = f'(SEL)NSSelectorFromString(@"{selector}")'
    sel_result = frame.EvaluateExpression(sel_expr)

    if not sel_result.IsValid() or sel_result.GetError().Fail():
        return 0, class_ptr, 0, f"Failed to resolve selector '{selector}': {sel_result.GetError()}"

    sel_ptr = sel_result.GetValueAsUnsigned()

    if verbose:
        print(f"  SEL: {sel_result.GetValue()}")

    if sel_ptr == 0:
        return 0, class_ptr, 0, f"Selector '{selector}' not found"

    # Step 3: For class methods, get the metaclass
    lookup_class_ptr = class_ptr
    if not is_instance_method:
        metaclass_expr = f'(Class)object_getClass((id)0x{class_ptr:x})'
        metaclass_result = frame.EvaluateExpression(metaclass_expr)

        if not metaclass_result.IsValid() or metaclass_result.GetError().Fail():
            return 0, class_ptr, sel_ptr, f"Failed to get metaclass: {metaclass_result.GetError()}"

        lookup_class_ptr = metaclass_result.GetValueAsUnsigned()

    # Step 4: Get the method implementation using class_getMethodImplementation
    imp_expr = f'(void *)class_getMethodImplementation((Class)0x{lookup_class_ptr:x}, (SEL)0x{sel_ptr:x})'
    imp_result = frame.EvaluateExpression(imp_expr)

    if not imp_result.IsValid() or imp_result.GetError().Fail():
        return 0, class_ptr, sel_ptr, f"Failed to get method implementation: {imp_result.GetError()}"

    imp_addr = imp_result.GetValueAsUnsigned()

    if imp_addr == 0:
        if verbose:
            print(f"  IMP: {imp_result.GetValue()}")
        return 0, class_ptr, sel_ptr, "Method implementation not found"

    # Step 5: Resolve symbol at IMP address to check for forwarding or inheritance
    target = frame.GetThread().GetProcess().GetTarget()
    addr = target.ResolveLoadAddress(imp_addr)
    inherited_from = None

    if addr.IsValid():
        symbol = addr.GetSymbol()
        if symbol.IsValid():
            symbol_name = symbol.GetName()
            if symbol_name:
                # Check for forwarding stub
                if 'msgForward' in symbol_name:
                    if verbose:
                        print(f"  IMP: {imp_result.GetValue()}")
                    method_type = "instance" if is_instance_method else "class"
                    return 0, class_ptr, sel_ptr, (
                        f"Method not implemented: {method_type} method '{selector}' "
                        f"on class '{class_name}' resolves to forwarding stub ({symbol_name})"
                    )

                # Check if method is inherited from a superclass
                # Symbol format: +[ClassName selector] or -[ClassName selector]
                inherited_from = _extract_inherited_class(
                    symbol_name, class_name, selector, is_instance_method
                )

    if verbose:
        if inherited_from:
            prefix = '-' if is_instance_method else '+'
            print(f"  IMP: {imp_result.GetValue()} \033[90m(inherited from {prefix}[{inherited_from} {selector}])\033[0m")
        else:
            print(f"  IMP: {imp_result.GetValue()}")

    return imp_addr, class_ptr, sel_ptr, None


def _extract_inherited_class(
    symbol_name: str,
    requested_class: str,
    selector: str,
    is_instance_method: bool
) -> Optional[str]:
    """
    Check if a symbol indicates the method is inherited from a superclass.

    Args:
        symbol_name: The symbol name at the IMP address (e.g., "+[NSObject hash]")
        requested_class: The class name we requested the method for
        selector: The selector we looked up
        is_instance_method: True for instance methods, False for class methods

    Returns:
        The superclass name if inherited, None if it's the requested class's own method
    """
    import re

    # Match Objective-C method symbol: +[ClassName selector] or -[ClassName selector]
    # The selector part can contain colons and arguments
    prefix = '-' if is_instance_method else '+'
    pattern = rf'^[+-]\[(\w+)\s+(.+)\]$'
    match = re.match(pattern, symbol_name)

    if match:
        symbol_class = match.group(1)
        symbol_selector = match.group(2)

        # Check if it's from a different class (i.e., inherited)
        if symbol_class != requested_class:
            # Verify the selector matches (it should, but let's be safe)
            if symbol_selector == selector:
                return symbol_class

    return None


def extract_category_from_symbol(symbol_name: str) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """
    Extract class name, category name, and selector from an Objective-C symbol.

    Args:
        symbol_name: Symbol like "-[NSString(CategoryName) methodName]" or "-[NSString methodName]"

    Returns:
        Tuple of (class_name, category_name, selector)
        category_name is None if the method is not from a category
    """
    import re
    # Match: +/-[ClassName(CategoryName) selector] or +/-[ClassName selector]
    pattern = r'^[+-]\[(\w+)(?:\((\w+)\))?\s+(.+)\]$'
    match = re.match(pattern, symbol_name)

    if match:
        return match.group(1), match.group(2), match.group(3)
    return None, None, None


def format_method_name(class_name: str, selector: str, is_instance_method: bool) -> str:
    """
    Format a method name in Objective-C syntax.

    Args:
        class_name: The class name
        selector: The selector string
        is_instance_method: True for instance methods, False for class methods

    Returns:
        Formatted string like "-[NSString length]" or "+[NSDate date]"
    """
    prefix = '-' if is_instance_method else '+'
    return f"{prefix}[{class_name} {selector}]"


def detect_method_type(
    frame: lldb.SBFrame,
    class_name: str,
    selector: str,
    verbose: bool = False
) -> bool:
    """
    Auto-detect whether a method is a class method (+) or instance method (-).

    Args:
        frame: The LLDB SBFrame to use for expression evaluation
        class_name: Name of the Objective-C class
        selector: The selector string
        verbose: If True, print detection details

    Returns:
        True for instance method, False for class method.

    Logic:
    - Check if the class has this method as a class method first
    - If not found as class method, check instance method
    - Default to instance method if we can't determine
    """
    # Check for class method first using class_getClassMethod
    # This is more reliable than class_respondsToSelector for our purposes
    check_expr = f'''(void *)({{
        Class cls = (Class)NSClassFromString(@"{class_name}");
        if (!cls) (void *)0;
        SEL sel = (SEL)NSSelectorFromString(@"{selector}");
        (void *)class_getClassMethod(cls, sel);
    }})'''

    class_result = frame.EvaluateExpression(check_expr)
    if class_result.IsValid() and not class_result.GetError().Fail():
        has_class_method = class_result.GetValueAsUnsigned() != 0
        if has_class_method:
            if verbose:
                print(f"Auto-detect: Class method +[{class_name} {selector}]")
            return False  # is_instance_method = False

    # Check for instance method using class_getInstanceMethod
    check_expr = f'''(void *)({{
        Class cls = (Class)NSClassFromString(@"{class_name}");
        if (!cls) (void *)0;
        SEL sel = (SEL)NSSelectorFromString(@"{selector}");
        (void *)class_getInstanceMethod(cls, sel);
    }})'''

    instance_result = frame.EvaluateExpression(check_expr)
    if instance_result.IsValid() and not instance_result.GetError().Fail():
        has_instance_method = instance_result.GetValueAsUnsigned() != 0
        if has_instance_method:
            if verbose:
                print(f"Auto-detect: Instance method -[{class_name} {selector}]")
            return True  # is_instance_method = True

    # Default to instance method if we can't determine
    if verbose:
        print(f"Auto-detect: Defaulting to instance method -[{class_name} {selector}]")
    return True


def get_arch_registers(frame: lldb.SBFrame) -> Tuple[str, str, List[str]]:
    """
    Get the appropriate register names for the current architecture.

    For Objective-C method calls:
    - ARM64: x0=self, x1=_cmd, x2-x7=args
    - x86_64: rdi=self, rsi=_cmd, rdx, rcx, r8, r9=args

    Args:
        frame: The LLDB SBFrame

    Returns:
        Tuple of (self_reg, cmd_reg, arg_regs) where arg_regs is a list of
        additional argument register names.
    """
    target = frame.GetThread().GetProcess().GetTarget()
    triple = target.GetTriple()

    if 'arm64' in triple or 'aarch64' in triple:
        # ARM64: x0=self, x1=_cmd, x2-x7=args
        return ('x0', 'x1', ['x2', 'x3', 'x4', 'x5', 'x6', 'x7'])
    else:
        # x86_64: rdi=self, rsi=_cmd, rdx, rcx, r8, r9=args
        return ('rdi', 'rsi', ['rdx', 'rcx', 'r8', 'r9'])
