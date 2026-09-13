"""
validators.py

Command-safety helpers. ALMUS PHONE LAB is built for legitimate,
owner-authorized device servicing and diagnostics only. This module:

- Flags destructive operations so the UI can force an explicit
  confirmation dialog before they run.
- Blocks a hard-coded blacklist of command patterns associated with
  FRP/account/lock bypass, IMEI manipulation, or other abuse - these
  are never executed regardless of confirmation.
"""
from __future__ import annotations

import re

DESTRUCTIVE_KEYWORDS = (
    "erase",
    "flash",
    "format",
    "delete",
    "rm ",
    "rm -",
    "uninstall",
    "wipe",
    "disable",
    "factory-reset",
    "flashall",
    "flashing unlock",
    "flashing lock",
)

# Patterns this application will refuse to build/execute under any
# circumstances. This list intentionally targets bypass/abuse tooling,
# not ordinary service operations. Account/lock patterns match in
# either word order (e.g. "remove google account" and "google account
# removal" both match) since real-world phrasing varies.
#
# NOTE: standalone-word patterns (frp, imei, bypass, icloud) use a
# custom boundary - (?<![A-Za-z0-9]) / (?![A-Za-z0-9]) - instead of
# \b, because \b treats underscores as word characters. Without this,
# something like "frp_bypass_tool" would slip past \bfrp\b entirely,
# since there is no boundary between "frp" and the following "_".
_WORD_START = r"(?<![A-Za-z0-9])"
_WORD_END = r"(?![A-Za-z0-9])"

BLOCKED_PATTERNS = [
    re.compile(_WORD_START + r"frp" + _WORD_END, re.IGNORECASE),
    re.compile(_WORD_START + r"imei" + _WORD_END, re.IGNORECASE),
    re.compile(r"factory[_\s-]?reset[_\s-]?protection", re.IGNORECASE),
    re.compile(_WORD_START + r"bypass" + _WORD_END, re.IGNORECASE),
    re.compile(r"(remov\w*|reset\w*|delet\w*|unlock\w*|disabl\w*).{0,20}(google|samsung)[_\s-]+account", re.IGNORECASE),
    re.compile(r"(google|samsung)[_\s-]+account.{0,20}(remov\w*|reset\w*|delet\w*|unlock\w*|bypass\w*|disabl\w*)", re.IGNORECASE),
    re.compile(_WORD_START + r"icloud" + _WORD_END, re.IGNORECASE),
    re.compile(r"network[_\s-]?unlock", re.IGNORECASE),
    re.compile(r"sim[_\s-]?unlock", re.IGNORECASE),
    re.compile(r"(remov\w*|reset\w*|delet\w*|bypass\w*).{0,20}(lock[_\s-]*screen|screen[_\s-]*lock|pattern[_\s-]*lock)", re.IGNORECASE),
    re.compile(r"(lock[_\s-]*screen|screen[_\s-]*lock|pattern[_\s-]*lock).{0,20}(remov\w*|reset\w*|delet\w*|bypass\w*)", re.IGNORECASE),
]


def is_blocked(command_text: str) -> bool:
    """Return True if the command text matches a permanently blocked
    pattern. Callers MUST refuse to execute if this returns True."""
    return any(p.search(command_text) for p in BLOCKED_PATTERNS)


def is_destructive(command_text: str) -> bool:
    """Return True if the command should require an explicit
    confirmation dialog before execution (but is otherwise legitimate)."""
    lowered = command_text.lower()
    return any(k in lowered for k in DESTRUCTIVE_KEYWORDS)


def validate_command(args: list[str]) -> tuple[bool, str]:
    """Validate a full command argument list before it is ever handed to
    a process runner.

    Returns (allowed, reason). `allowed` is False if the command is
    permanently blocked. `reason` explains the decision, used for both
    logging and, when blocked, the error shown to the user.
    """
    joined = " ".join(args)
    if is_blocked(joined):
        return False, (
            "This command matches a pattern associated with account, lock, "
            "or FRP bypass, or IMEI modification. ALMUS PHONE LAB does not "
            "support these operations and has refused to run it."
        )
    return True, "OK"
