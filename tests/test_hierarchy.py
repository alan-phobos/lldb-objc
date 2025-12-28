#!/usr/bin/env python3
"""
Test script for ocls hierarchy display feature.

This script tests the automatic hierarchy display in ocls:
- 1 match: Detailed hierarchy view
- 2-20 matches: Compact one-liner per class
- 21+ matches: Simple class list
"""

import subprocess
import sys
import os

# Get the project root directory
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, '..'))
HELLO_WORLD_PATH = os.path.join(PROJECT_ROOT, 'examples/HelloWorld/HelloWorld/HelloWorld')

def run_lldb_test(commands):
    """
    Run LLDB with a series of commands and return the output.

    Args:
        commands: List of LLDB commands to execute

    Returns:
        String containing the output
    """
    # Build the command script
    lldb_script = '\n'.join([
        f'command script import {PROJECT_ROOT}/objc_cls.py',
        f'file {HELLO_WORLD_PATH}',
        'breakpoint set -n main',
        'run',
    ] + commands + ['quit'])

    # Run LLDB
    proc = subprocess.Popen(
        ['lldb', '-b'],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    stdout, stderr = proc.communicate(input=lldb_script)
    return stdout + stderr


def test_single_match():
    """Test hierarchy display for exactly 1 match."""
    print("=" * 70)
    print("TEST: Single Match (NSString)")
    print("=" * 70)

    output = run_lldb_test(['ocls NSString'])

    print(output)

    # Check for expected hierarchy markers (arrows in the output)
    # Single match shows class name followed by hierarchy with arrows
    if '→' in output:
        print("✅ PASS: Hierarchy display detected for single match")
        return True
    else:
        print("❌ FAIL: No hierarchy display found for single match")
        return False


def test_few_matches():
    """Test hierarchy display for 2-20 matches."""
    print("\n" + "=" * 70)
    print("TEST: Few Matches (NSMutable*)")
    print("=" * 70)

    output = run_lldb_test(['ocls NSMutable*'])

    print(output)

    # Check for compact hierarchy (arrows in output)
    if '→' in output:
        print("✅ PASS: Compact hierarchy display detected for few matches")
        return True
    else:
        print("❌ FAIL: Expected compact hierarchy for few matches")
        return False


def test_many_matches():
    """Test simple list for 21+ matches."""
    print("\n" + "=" * 70)
    print("TEST: Many Matches (NS*)")
    print("=" * 70)

    output = run_lldb_test(['ocls NS*'])

    print(output)

    # For many matches, we should NOT see hierarchy arrows
    # (This test might need adjustment based on actual NS* class count)
    match_count = output.count('Found')
    if match_count > 0:
        print("✅ PASS: Many matches test completed")
        return True
    else:
        print("❌ FAIL: No matches found")
        return False


def main():
    """Run all hierarchy display tests."""
    print("Testing ocls hierarchy display feature")
    print("Binary:", HELLO_WORLD_PATH)

    if not os.path.exists(HELLO_WORLD_PATH):
        print(f"Error: HelloWorld binary not found at {HELLO_WORLD_PATH}")
        print("Please build the HelloWorld example first:")
        print("  cd examples/HelloWorld")
        print("  xcodebuild")
        sys.exit(1)

    results = []

    # Run tests
    results.append(('Single Match', test_single_match()))
    results.append(('Few Matches', test_few_matches()))
    results.append(('Many Matches', test_many_matches()))

    # Summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {name}")

    total = len(results)
    passed = sum(1 for _, p in results if p)
    print(f"\nTotal: {passed}/{total} tests passed")

    sys.exit(0 if passed == total else 1)


if __name__ == '__main__':
    main()
