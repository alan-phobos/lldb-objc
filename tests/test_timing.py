#!/usr/bin/env python3
"""
Quick timing test for oclasses phases.
Runs a simple query to check performance.
"""

import subprocess
import os
import sys

# Get the project root directory
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(script_dir, '..'))

# Path to the HelloWorld binary
hello_world_path = os.path.join(project_root, 'examples/HelloWorld/HelloWorld/HelloWorld')

# Check if binary exists
if not os.path.exists(hello_world_path):
    print(f"Error: HelloWorld binary not found at {hello_world_path}")
    print("Run 'cd examples/HelloWorld && make' first")
    sys.exit(1)

print(f"Testing with: {hello_world_path}")
print("="* 70)

# Create LLDB commands
lldb_commands = f"""
file {hello_world_path}
b main
run
oclasses Greeter
quit
"""

# Write commands to temp file
import tempfile
with tempfile.NamedTemporaryFile(mode='w', suffix='.lldb', delete=False) as f:
    f.write(lldb_commands)
    temp_file = f.name

try:
    # Run LLDB
    cmd = ['lldb', '-s', temp_file]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=180)

    print(result.stdout)

    if result.returncode != 0:
        print("STDERR:", result.stderr, file=sys.stderr)
        sys.exit(1)

    # Extract timing info
    for line in result.stdout.split('\n'):
        if 'Phase' in line and ('completed' in line or 'Performance' in line):
            print(f">>> {line.strip()}")

    print("\n" + "="*70)
    print("Test completed successfully!")

finally:
    os.unlink(temp_file)
