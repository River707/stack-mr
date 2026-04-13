import subprocess
from pathlib import Path
from typing import Any, Iterable, Union

ShellCommand = Iterable[Union[str, Path]]

_DRY_RUN: bool = False


def set_dry_run(enabled: bool) -> None:
    """Enable or disable dry-run mode globally.

    When dry-run is enabled, side-effecting shell commands (those not capturing
    output) are printed instead of executed.
    """
    global _DRY_RUN
    _DRY_RUN = enabled

def is_dry_run() -> bool:
    """Check if dry-run mode is enabled."""
    return _DRY_RUN

def run_shell_command(
    cmd: ShellCommand, *, check: bool = True, **kwargs: Any
) -> subprocess.CompletedProcess:
    """Runs a shell command using the arguments provided.

    This is essentially a wrapper around subprocess.run, with more reasonable
    default arguments, and some debug logging.

    Args:
        cmd: shell command to run.
        check: see subprocess.run for semantics.
        **kwargs: see subprocess.run for semantics
            (https://docs.python.org/3/library/subprocess.html#subprocess.run).

    Returns:
        A subprocess.CompletedProcess object.
    """
    if "shell" in kwargs:
        raise ValueError("shell support has been removed")
    cmd_list = list(map(str, cmd))
    if _DRY_RUN and "capture_output" not in kwargs:
        print(f"[dry-run] {subprocess.list2cmdline(cmd_list)}")
        return subprocess.CompletedProcess(cmd_list, 0)
    kwargs.update({"check": check})
    return subprocess.run(cmd_list, **kwargs)


def get_command_output(cmd: ShellCommand, **kwargs: Any) -> str:
    """A wrapper over run_shell_command that captures stdout into a string.

    Args:
        cmd: shell command to run.
        **kwargs: see run_shell_command for semantics. Passing capture_output is
            not allowed.

    Returns:
        Captured stdout of the command as a string.

    Raises:
        ValueError: if the capture_output keyword argument is specified.
    """
    if "capture_output" in kwargs:
        raise ValueError("Cannot pass capture_output when using get_command_output")
    proc = run_shell_command(cmd, capture_output=True, **kwargs)
    return proc.stdout.decode("utf-8").rstrip()
