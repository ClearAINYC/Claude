"""Entry point.

    python -m desktop_agent                 # interactive: type tasks, watch it work
    python -m desktop_agent "your task"      # run one task and exit
    python -m desktop_agent --yolo "task"    # no approval prompts (disposable VM only)
"""

from __future__ import annotations

import argparse
import sys

# Load a local .env file if python-dotenv is available (optional convenience).
try:
    from dotenv import load_dotenv

    load_dotenv()
except Exception:  # noqa: BLE001
    pass

from .agent import DesktopAgent


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="desktop_agent",
        description="A human-like computer-use agent that controls your machine.",
    )
    parser.add_argument("task", nargs="*", help="The task to perform. Omit for interactive mode.")
    parser.add_argument("--yolo", action="store_true",
                        help="Run all shell commands and file writes without asking. Disposable VM only.")
    parser.add_argument("--model", default=None, help="Override the model (default: claude-opus-4-8).")
    parser.add_argument("--effort", default=None, help="low | medium | high | xhigh | max")
    parser.add_argument("--max-steps", type=int, default=None, help="Max agent steps per task.")
    args = parser.parse_args()

    try:
        agent = DesktopAgent(
            model=args.model,
            effort=args.effort,
            mode="yolo" if args.yolo else None,
            max_steps=args.max_steps,
        )
    except Exception as e:  # noqa: BLE001
        print(f"Failed to start: {e}\n\nIs ANTHROPIC_API_KEY set? (copy .env.example to .env)", file=sys.stderr)
        return 1

    print(f"🖥️  desktop_agent ready — model={agent.model}, effort={agent.effort}, "
          f"mode={'YOLO (no approvals)' if agent.approver.auto else 'ask (approvals on)'}")
    print(f"    screen={agent.computer.screen_w}x{agent.computer.screen_h} "
          f"-> sent to model as {agent.computer.img_w}x{agent.computer.img_h}\n")

    if args.task:
        agent.run_task(" ".join(args.task))
        return 0

    # Interactive mode
    print("Type a task and press Enter. Ctrl+C or 'exit' to quit.\n")
    while True:
        try:
            task = input("you ▸ ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nbye 👋")
            return 0
        if task.lower() in ("exit", "quit"):
            print("bye 👋")
            return 0
        if task:
            agent.run_task(task)
            print()


if __name__ == "__main__":
    raise SystemExit(main())
