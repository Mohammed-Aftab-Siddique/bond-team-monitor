"""
Shared utility functions for the Bond Team Monitor extension.

This module contains platform-independent helper functions that can be
used by both the Linux and Windows collectors.
"""

from __future__ import annotations

import json
import logging
import subprocess
from pathlib import Path

logger = logging.getLogger(__name__)


def run_command(command: list[str], timeout: int = 30) -> str | None:
    """
    Execute a system command and return its stdout.

    Args:
        command: Command and arguments.
        timeout: Maximum execution time in seconds.

    Returns:
        Command output as a string, or None if execution fails.
    """
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=True,
        )

        return result.stdout.strip()

    except subprocess.TimeoutExpired:
        logger.error("Command timed out: %s", " ".join(command))

    except subprocess.CalledProcessError as exc:
        logger.error(
            "Command failed (%s): %s",
            exc.returncode,
            " ".join(command),
        )

    except Exception as exc:
        logger.exception("Unexpected error while running command: %s", exc)

    return None


def read_file(path: str) -> str | None:
    """
    Safely read a text file.

    Args:
        path: Absolute file path.

    Returns:
        File contents, or None if the file cannot be read.
    """
    try:
        return Path(path).read_text(encoding="utf-8").strip()

    except FileNotFoundError:
        logger.warning("File not found: %s", path)

    except PermissionError:
        logger.error("Permission denied: %s", path)

    except Exception as exc:
        logger.exception("Unable to read %s: %s", path, exc)

    return None


def path_exists(path: str) -> bool:
    """
    Check whether a filesystem path exists.

    Args:
        path: Absolute path.

    Returns:
        True if the path exists.
    """
    return Path(path).exists()


def read_int_file(path: str, default: int = 0) -> int:
    """
    Safely read an integer value from a text file.

    Args:
        path: Absolute path to the file.
        default: Value to return if the file cannot be read
            or does not contain a valid integer.

    Returns:
        Integer value read from the file, or default.
    """
    contents = read_file(path)

    if contents is None:
        return default

    try:
        return int(contents.strip())

    except ValueError:
        logger.warning(
            "Invalid integer in file '%s': %s",
            path,
            contents,
        )

        return default


def run_powershell(command: str) -> list | dict | None:
    """
    Execute a PowerShell command that returns JSON.
    """
    output = run_command(
        [
            "powershell",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-Command",
            command,
        ]
    )

    if not output:
        return None

    try:
        return json.loads(output)
    except json.JSONDecodeError:
        logger.exception("Failed to parse PowerShell JSON.")
        return None
