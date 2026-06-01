"""Human-in-the-loop approval for irreversible actions.

The computer agent can do anything a person can do at the keyboard. GUI clicks
are visible on screen as they happen, so they're self-evident; but shell
commands and file writes can be destructive and silent. In the default "ask"
mode we pause and require explicit y/N approval for those before running them.

Set the mode to "yolo" (env DESKTOP_AGENT_MODE=yolo or the --yolo flag) to run
everything without prompting. Only do that inside a disposable VM.
"""

from __future__ import annotations

import re
import sys

# Commands that are destructive enough to always highlight loudly, even to
# remind a user who is clicking through approvals.
_DANGEROUS = re.compile(
    r"""(?xi)
    \brm\s+-[a-z]*[rf]      # rm -rf and friends
    | \bmkfs\b              # formatting a filesystem
    | \bdd\b.*\bof=/dev/    # writing straight to a device
    | \b(shutdown|reboot|halt|poweroff)\b
    | :\(\)\s*\{            # classic fork bomb
    | \b(curl|wget)\b.+\|\s*(sudo\s+)?(ba)?sh   # pipe-to-shell installs
    | \bgit\s+push\b.*--force
    | \bsudo\s+rm\b
    """
)


class Approver:
    """Decides whether a side-effecting action may run."""

    def __init__(self, mode: str = "ask"):
        # "ask" -> prompt every time; "yolo" -> never prompt.
        self.mode = mode

    @property
    def auto(self) -> bool:
        return self.mode == "yolo"

    def confirm(self, kind: str, detail: str) -> bool:
        """Return True if the action is allowed to proceed.

        kind:   short label, e.g. "shell command" or "file write".
        detail: the actual command or path being acted on.
        """
        if self.auto:
            return True

        dangerous = bool(_DANGEROUS.search(detail))
        banner = "  ⚠️  LOOKS DESTRUCTIVE" if dangerous else ""

        print(f"\n┳ Agent wants to run a {kind}:{banner}", file=sys.stderr)
        for line in detail.splitlines() or [detail]:
            print(f"┃   {line}", file=sys.stderr)
        print("┗ Allow? [y]es / [N]o / [a]llow-all-this-session: ", end="", file=sys.stderr, flush=True)

        try:
            answer = input().strip().lower()
        except (EOFError, KeyboardInterrupt):
            print(file=sys.stderr)
            return False

        if answer in ("a", "all"):
            # Drop into yolo for the rest of this run.
            self.mode = "yolo"
            return True
        return answer in ("y", "yes")
