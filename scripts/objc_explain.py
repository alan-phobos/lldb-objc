#!/usr/bin/env python3
"""
LLDB script for explaining disassembly using an LLM.

Usage: oexplain <address|$var|expression>   # Explain disassembly at address
       oexplain -a <address>                # Annotate each line of disassembly
       oexplain --claude <address>          # Use Claude CLI instead of llm
       oexplain 0x123456789abc              # Explain by hex address
       oexplain $0                          # Explain LLDB variable
       oexplain (IMP)[NSString class]       # Explain by expression

This command disassembles the function at the given address and sends it to
an LLM for analysis (llm by default, claude with --claude flag).
"""

from __future__ import annotations

import lldb
import os
import subprocess
import sys
import time
from typing import Any, Dict

# Add the script directory to path for version import
script_dir = os.path.dirname(os.path.abspath(__file__))
if script_dir not in sys.path:
    sys.path.insert(0, script_dir)

try:
    from version import __version__
except ImportError:
    __version__ = "unknown"


CLAUDE_PROMPT = """Here is some arm64 disassembly. Explain very concisely what this function does as you would to a security researcher. Avoid any boilerplate blurb. Include a compact view of the first 5 functions it will call."""

CLAUDE_ANNOTATE_PROMPT = """Here is some arm64 disassembly. Reproduce the disassembly exactly, but add concise high-level annotations as comments on lines where the purpose isn't obvious. Focus on what's happening semantically (e.g., "// get string length", "// check for nil", "// call objc_msgSend with selector"). Skip trivial operations like stack frame setup. Keep annotations brief."""


def get_disassembly(debugger: lldb.SBDebugger, address: str) -> tuple[bool, str]:
    """
    Get disassembly at the given address using LLDB's disass command.

    Args:
        debugger: LLDB debugger instance
        address: Address expression to disassemble

    Returns:
        (success, output) tuple
    """
    result = lldb.SBCommandReturnObject()
    ci = debugger.GetCommandInterpreter()

    # Use disass -a to disassemble at address
    ci.HandleCommand(f"disass -a {address}", result)

    if result.Succeeded():
        return True, result.GetOutput()
    else:
        return False, result.GetError()


def call_llm(disassembly: str, prompt: str = CLAUDE_PROMPT) -> tuple[bool, str]:
    """
    Send disassembly to llm CLI for explanation.

    Args:
        disassembly: The disassembly text to explain
        prompt: The prompt to use (default: CLAUDE_PROMPT)

    Returns:
        (success, output) tuple
    """
    full_prompt = f"{prompt}\n\n{disassembly}"

    try:
        result = subprocess.run(
            ["llm", full_prompt],
            capture_output=True,
            text=True,
            timeout=120,
        )

        if result.returncode == 0:
            return True, result.stdout
        else:
            error_msg = result.stderr.strip() or result.stdout.strip() or f"exit code {result.returncode}"
            return False, f"llm CLI error: {error_msg}"

    except subprocess.TimeoutExpired:
        return False, "Error: llm CLI timed out after 120 seconds"
    except FileNotFoundError:
        return False, "Error: 'llm' CLI not found. Install with: pip install llm"
    except Exception as e:
        return False, f"Error calling llm: {e}"


def call_claude(disassembly: str, prompt: str = CLAUDE_PROMPT) -> tuple[bool, str]:
    """
    Send disassembly to Claude via CLI for explanation.

    Args:
        disassembly: The disassembly text to explain
        prompt: The prompt to use (default: CLAUDE_PROMPT)

    Returns:
        (success, output) tuple
    """
    full_prompt = f"{prompt}\n\n{disassembly}"

    try:
        result = subprocess.run(
            [
                "claude",
                "-p", full_prompt,
                "--model", "opus",
            ],
            capture_output=True,
            text=True,
            timeout=60,
        )

        if result.returncode == 0:
            return True, result.stdout
        else:
            error_msg = result.stderr.strip() or result.stdout.strip() or f"exit code {result.returncode}"
            return False, f"Claude CLI error: {error_msg}"

    except subprocess.TimeoutExpired:
        return False, "Error: Claude CLI timed out after 60 seconds"
    except FileNotFoundError:
        return False, "Error: 'claude' CLI not found. Install with: npm install -g @anthropic-ai/claude-code"
    except Exception as e:
        return False, f"Error calling Claude: {e}"


def format_output(text: str) -> str:
    """Format output with >> prefix on each line."""
    lines = text.rstrip().split('\n')
    return '\n'.join(f">> {line}" for line in lines)


def parse_args(command: str) -> tuple[bool, bool, str]:
    """
    Parse command arguments.

    Args:
        command: Raw command string

    Returns:
        (annotate_mode, use_claude, address) tuple
    """
    parts = command.strip().split()
    annotate = False
    use_claude = False
    address_parts = []

    i = 0
    while i < len(parts):
        if parts[i] in ('-a', '--annotate'):
            annotate = True
        elif parts[i] == '--claude':
            use_claude = True
        else:
            address_parts.append(parts[i])
        i += 1

    return annotate, use_claude, ' '.join(address_parts)


def explain_command(
    debugger: lldb.SBDebugger,
    command: str,
    result: lldb.SBCommandReturnObject,
    internal_dict: Dict[str, Any]
) -> None:
    """
    LLDB command to explain disassembly using an LLM.

    Usage: oexplain [-a|--annotate] [--claude] <address|$var|expression>
    """
    target = debugger.GetSelectedTarget()
    process = target.GetProcess()

    if not process.IsValid() or process.GetState() != lldb.eStateStopped:
        result.SetError("Process must be running and stopped")
        return

    annotate, use_claude, address = parse_args(command)

    if not address:
        result.SetError("Usage: oexplain [-a|--annotate] [--claude] <address|$var|expression>")
        return

    # Get disassembly
    success, disasm = get_disassembly(debugger, address)
    if not success:
        result.SetError(f"Failed to disassemble: {disasm}")
        return

    if not disasm.strip():
        result.SetError("No disassembly output")
        return

    # Select prompt based on mode
    prompt = CLAUDE_ANNOTATE_PROMPT if annotate else CLAUDE_PROMPT
    mode_desc = "annotating" if annotate else "explaining"
    backend = "Claude" if use_claude else "llm"

    # Call LLM
    print(f"Sending {len(disasm.splitlines())} lines of disassembly to {backend} ({mode_desc})...")
    start_time = time.time()
    if use_claude:
        success, explanation = call_claude(disasm, prompt)
    else:
        success, explanation = call_llm(disasm, prompt)
    elapsed = time.time() - start_time

    if not success:
        result.SetError(explanation)
        return

    # Print formatted output
    print(format_output(explanation))
    print(f"\n\033[90m[{backend} responded in {elapsed:.1f}s]\033[0m")
    result.SetStatus(lldb.eReturnStatusSuccessFinishResult)


def __lldb_init_module(debugger: lldb.SBDebugger, internal_dict: Dict[str, Any]) -> None:
    """Initialize the oexplain command when this module is loaded in LLDB."""
    module_path = f"{__name__}.explain_command"
    debugger.HandleCommand(
        f'command script add -f {module_path} oexplain'
    )
    print(f"[lldb-objc v{__version__}] 'oexplain' installed - Explain disassembly with LLM")
