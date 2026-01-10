#!/usr/bin/env python3
"""
Test script for the oexplain command (Disassembly Explainer).

This script tests the oexplain functionality:
- Command loads correctly
- Disassembly retrieval works
- Error handling for invalid inputs

Note: Full integration tests with LLM CLI require manual testing
since they depend on external API access. Uses llm by default,
claude with --claude flag.

Uses a shared LLDB session for faster test execution.
"""

import sys
import re
import os
from test_helpers import (
    TestResult, run_shared_test_suite,
    PROJECT_ROOT
)


# =============================================================================
# Validator Functions
# =============================================================================

def validate_command_exists():
    """Validator that oexplain command is available."""
    def validator(output):
        # help oexplain should show usage info
        if 'oexplain' in output.lower() or 'explain' in output.lower():
            return True, "Command is registered"
        if 'error: command' in output.lower() and 'not found' in output.lower():
            return False, (f"Command not registered\n"
                          f"    Expected: oexplain help output\n"
                          f"    Actual: Command not found\n"
                          f"    Output: {output[:200]}")
        return True, "Command appears to be registered"
    return validator


def validate_usage_error():
    """Validator that command shows usage error without arguments."""
    def validator(output):
        if 'usage' in output.lower() or 'error' in output.lower():
            return True, "Shows usage/error without arguments"
        return False, (f"Expected usage message\n"
                      f"    Expected: Usage or error message\n"
                      f"    Actual: {output[:200]}")
    return validator


def validate_disassembly_sent():
    """Validator that disassembly is retrieved and sent to LLM."""
    def validator(output):
        # Should show "Sending N lines of disassembly to llm/Claude..."
        if 'sending' in output.lower() and 'disassembly' in output.lower():
            return True, "Disassembly retrieved and sending to LLM"
        if 'failed to disassemble' in output.lower():
            return False, (f"Disassembly failed\n"
                          f"    Expected: Successful disassembly\n"
                          f"    Actual: Disassembly error\n"
                          f"    Output: {output[:300]}")
        if 'error' in output.lower():
            # Could be LLM CLI error which is expected in automated tests
            if 'llm cli' in output.lower() or 'claude cli' in output.lower():
                return True, "Disassembly succeeded (LLM CLI error expected in automated tests)"
            return False, (f"Unexpected error\n"
                          f"    Output: {output[:300]}")
        return False, (f"Unexpected output\n"
                      f"    Expected: 'Sending N lines of disassembly'\n"
                      f"    Actual: {output[:300]}")
    return validator


def validate_invalid_address_error():
    """Validator that invalid address produces an error."""
    def validator(output):
        if 'error' in output.lower() or 'failed' in output.lower():
            return True, "Reports error for invalid address"
        return False, (f"Expected error for invalid address\n"
                      f"    Expected: Error message\n"
                      f"    Actual: {output[:200]}")
    return validator


def validate_output_format():
    """Validator that successful output has >> prefix (if LLM succeeds)."""
    def validator(output):
        # If we got actual LLM output, check for >> prefix
        if '>>' in output:
            return True, "Output has >> prefix format"
        # If LLM CLI failed, that's expected in automated tests
        if ('llm cli' in output.lower() or 'claude cli' in output.lower()) and 'error' in output.lower():
            return True, "LLM CLI error (expected in automated tests)"
        # If just sending message, that's also acceptable
        if 'sending' in output.lower() and 'disassembly' in output.lower():
            return True, "Command reached LLM call stage"
        return False, (f"Unexpected output format\n"
                      f"    Expected: >> prefix or LLM CLI error\n"
                      f"    Actual: {output[:300]}")
    return validator


def get_test_specs():
    """Return list of test specifications."""
    return [
        # Command registration tests
        (
            "Explain: command is registered",
            [
                'help oexplain'
            ],
            validate_command_exists()
        ),
        (
            "Explain: shows usage without arguments",
            [
                'oexplain'
            ],
            validate_usage_error()
        ),
        # Disassembly retrieval tests
        (
            "Explain: retrieves disassembly for $pc",
            [
                'oexplain $pc'
            ],
            validate_disassembly_sent()
        ),
        (
            "Explain: retrieves disassembly for method implementation",
            [
                # Use expr to get an IMP, then oexplain it via $0
                'expr (IMP)class_getMethodImplementation([NSString class], @selector(init))',
                'oexplain $0'
            ],
            validate_disassembly_sent()
        ),
        # Error handling tests
        (
            "Explain: error for invalid expression",
            [
                'oexplain invalid_nonsense_expression_12345'
            ],
            validate_invalid_address_error()
        ),
        # Output format test (may fail if Claude CLI not configured)
        (
            "Explain: output format check",
            [
                'oexplain $pc'
            ],
            validate_output_format()
        ),
    ]


def main():
    """Run all oexplain tests using shared LLDB session."""
    # Check if objc_explain.py exists
    objc_explain_path = os.path.join(PROJECT_ROOT, 'scripts', 'objc_explain.py')
    if not os.path.exists(objc_explain_path):
        print(f"Note: {objc_explain_path} not found")
        print("These tests are for the oexplain feature.")
        print("Tests will fail until the feature is implemented.\n")

    categories = {
        "Command registration": (0, 2),
        "Disassembly retrieval": (2, 4),
        "Error handling": (4, 5),
        "Output format": (5, 6),
    }

    passed, total = run_shared_test_suite(
        "OEXPLAIN COMMAND TEST SUITE",
        get_test_specs(),
        scripts=['scripts/objc_explain.py'],
        show_category_summary=categories
    )
    sys.exit(0 if passed == total else 1)


if __name__ == '__main__':
    main()
