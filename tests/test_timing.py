#!/usr/bin/env python3
"""
Detailed timing test for --ivars and --properties performance.
Measures the actual expression evaluation time.
"""

import subprocess
import tempfile
import os
import sys

# Get the script directory
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)

# Path to HelloWorld binary
hello_world_path = os.path.join(project_root, "examples/HelloWorld/HelloWorld/HelloWorld")

# Verify paths exist
if not os.path.exists(hello_world_path):
    print(f"Error: HelloWorld binary not found at: {hello_world_path}")
    sys.exit(1)

# Test with a few different classes
test_classes = [
    "NSObject",          # Small - 0 ivars, ~0 properties 
    "NSString",          # Medium
    "UIViewController",  # Medium-large
    "IDSServiceProperties"  # Large - 91 ivars, 95 properties
]

print(f"Timing comparison: Before (individual calls) vs After (batched)")
print(f"Binary path: {hello_world_path}\n")

for class_name in test_classes:
    # Create LLDB command sequence
    lldb_commands = f"""
file {hello_world_path}
b main
run
expr (void)dlopen("/System/Library/PrivateFrameworks/IDS.framework/IDS", 0x2)

# Test ivars
script import time; start = time.time()
ocls --ivars {class_name}
script elapsed = time.time() - start; print(f"\\n[IVARS_TIME: {{elapsed:.3f}}s]")

# Test properties  
script start = time.time()
ocls --properties {class_name}
script elapsed = time.time() - start; print(f"\\n[PROPS_TIME: {{elapsed:.3f}}s]")

quit
"""

    with tempfile.NamedTemporaryFile(mode='w', suffix='.lldb', delete=False) as f:
        f.write(lldb_commands)
        command_file = f.name

    try:
        result = subprocess.run(['lldb', '-s', command_file],
                              capture_output=True,
                              text=True,
                              check=False,
                              timeout=30)

        # Parse output
        output = result.stdout

        # Extract counts and timing
        import re
        ivars_match = re.search(r'Instance Variables \((\d+)\)', output)
        props_match = re.search(r'Properties \((\d+)\)', output)
        ivars_time = re.search(r'\[IVARS_TIME: ([\d.]+)s\]', output)
        props_time = re.search(r'\[PROPS_TIME: ([\d.]+)s\]', output)

        ivar_count = int(ivars_match.group(1)) if ivars_match else 0
        prop_count = int(props_match.group(1)) if props_match else 0
        ivar_sec = float(ivars_time.group(1)) if ivars_time else 0
        prop_sec = float(props_time.group(1)) if props_time else 0

        print(f"{class_name}:")
        print(f"  Ivars:      {ivar_count:3d}  in {ivar_sec:5.3f}s  ({ivar_sec/max(ivar_count,1)*1000:4.0f}ms per ivar)" if ivar_count > 0 else f"  Ivars:      {ivar_count:3d}")
        print(f"  Properties: {prop_count:3d}  in {prop_sec:5.3f}s  ({prop_sec/max(prop_count,1)*1000:4.0f}ms per property)" if prop_count > 0 else f"  Properties: {prop_count:3d}")
        print()

    except subprocess.TimeoutExpired:
        print(f"{class_name}: TIMEOUT")
    finally:
        os.unlink(command_file)
