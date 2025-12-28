#!/usr/bin/env python3
"""
Test script to measure performance of --ivars and --properties flags.
"""

import subprocess
import tempfile
import os
import sys
import re
import time

# Get the script directory
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)

# Path to HelloWorld binary
hello_world_path = os.path.join(project_root, "examples/HelloWorld/HelloWorld/HelloWorld")

# Verify paths exist
if not os.path.exists(hello_world_path):
    print(f"Error: HelloWorld binary not found at: {hello_world_path}")
    sys.exit(1)

print(f"Testing ocls --ivars and --properties performance...")
print(f"Binary path: {hello_world_path}")
print()

# Create LLDB command sequence
lldb_commands = f"""
# Load the target binary
file {hello_world_path}

# Set breakpoint on main
b main

# Run the process
run

# Load IDS.framework
expr (void)dlopen("/System/Library/PrivateFrameworks/IDS.framework/IDS", 0x2)

# Test with --ivars flag (measure time)
script import time; start = time.time()
ocls --ivars IDSServiceProperties
script print(f"\\n[TIME: {{time.time() - start:.2f}}s]\\n")

# Test with --properties flag (measure time)
script start = time.time()
ocls --properties IDSServiceProperties  
script print(f"\\n[TIME: {{time.time() - start:.2f}}s]\\n")

quit
"""

# Write commands to a temporary file
with tempfile.NamedTemporaryFile(mode='w', suffix='.lldb', delete=False) as f:
    f.write(lldb_commands)
    command_file = f.name

try:
    start_time = time.time()
    # Launch LLDB with the command file
    result = subprocess.run(['lldb', '-s', command_file],
                          capture_output=True,
                          text=True,
                          check=False)
    total_time = time.time() - start_time

    # Parse output
    output = result.stdout

    # Extract ivar/property counts
    ivars_match = re.search(r'Instance Variables \((\d+)\)', output)
    props_match = re.search(r'Properties \((\d+)\)', output)

    # Extract timing
    times = re.findall(r'\[TIME: ([\d.]+)s\]', output)

    print(f"\nResults:")
    if ivars_match:
        print(f"  Instance variables: {ivars_match.group(1)}")
        if len(times) > 0:
            print(f"  Time for --ivars: {times[0]}s")
    if props_match:
        print(f"  Properties: {props_match.group(1)}")
        if len(times) > 1:
            print(f"  Time for --properties: {times[1]}s")

    print(f"\n  Total test time: {total_time:.2f}s")

    # Show a sample of the output
    print("\nSample output:")
    lines = output.split('\n')
    for i, line in enumerate(lines):
        if 'IDSServiceProperties' in line:
            # Show class line and next 10 lines
            for j in range(i, min(i + 15, len(lines))):
                print(lines[j])
            break

finally:
    # Clean up temporary file
    os.unlink(command_file)
