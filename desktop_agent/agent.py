"""The agent loop: Claude looks at the screen, decides an action, we run it,
send back the result, and repeat — the same pattern Perplexity's Comet / Operator
style assistants use.

Powered by the Claude API (Opus 4.8 by default) with:
  * adaptive thinking + effort control
  * prompt caching on the stable system + tools prefix
  * streaming (so you see the agent think and act in real time)
  * automatic pruning of old screenshots to keep context (and cost) bounded
"""

from __future__ import annotations

import os
import platform

import anthropic

from .safety import Approver
from .tools import BashTool, ComputerTool, EditTool

COMPUTER_USE_BETA = "computer-use-2025-11-24"

# Keep only the few most recent screenshots in the running history. Older ones
# are replaced with a short placeholder so the conversation doesn't balloon.
KEEP_RECENT_IMAGES = 4

SYSTEM_PROMPT = """You are a fully autonomous computer-use agent running directly \
on the user's {system} machine. You control it exactly as a human would: you can \
take screenshots, move and click the mouse, type, use keyboard shortcuts, scroll, \
run shell commands, and read/write files. You have access to every application and \
the whole filesystem the user's account can reach.

Operating principles:
- Work toward the user's goal end to end. Break it into concrete steps.
- After each action that changes the screen, take a screenshot and verify the \
result before moving on. Say "I have verified step X..." in your reasoning.
- Prefer keyboard shortcuts over fiddly mouse targeting for dropdowns/menus when \
it's more reliable.
- Use the bash and file tools for anything faster done in a terminal than a GUI.
- Some shell commands and file writes will pause for the user's approval; if an \
action comes back DENIED, do not retry it blindly — ask the user how to proceed.
- For irreversible real-world actions (sending messages/email, purchases, deleting \
data, accepting terms), briefly state what you're about to do before doing it.
- When the task is complete, stop calling tools and give the user a short summary \
of what you did.

Current platform: {system} ({release})."""


def _prune_images(messages: list, keep: int = KEEP_RECENT_IMAGES) -> None:
    """Replace all but the most recent `keep` screenshot images (in user
    tool_result blocks) with a text placeholder, in place."""
    # Find indices of every image block, newest last.
    image_locs = []
    for mi, msg in enumerate(messages):
        content = msg.get("content")
        if not isinstance(content, list):
            continue
        for bi, block in enumerate(content):
            if isinstance(block, dict) and block.get("type") == "tool_result":
                inner = block.get("content")
                if isinstance(inner, list):
                    for ii, sub in enumerate(inner):
                        if isinstance(sub, dict) and sub.get("type") == "image":
                            image_locs.append((mi, bi, ii))

    for mi, bi, ii in image_locs[:-keep] if len(image_locs) > keep else []:
        messages[mi]["content"][bi]["content"][ii] = {
            "type": "text",
            "text": "[older screenshot removed to save context]",
        }


class DesktopAgent:
    def __init__(
        self,
        model: str | None = None,
        effort: str | None = None,
        mode: str | None = None,
        max_steps: int | None = None,
    ):
        self.client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY
        self.model = model or os.environ.get("DESKTOP_AGENT_MODEL", "claude-opus-4-8")
        self.effort = effort or os.environ.get("DESKTOP_AGENT_EFFORT", "high")
        self.max_steps = max_steps or int(os.environ.get("DESKTOP_AGENT_MAX_STEPS", "60"))

        self.approver = Approver(mode or os.environ.get("DESKTOP_AGENT_MODE", "ask"))

        self.computer = ComputerTool()
        self.bash = BashTool(self.approver)
        self.edit = EditTool(self.approver)
        self.tools_by_name = {
            "computer": self.computer,
            "bash": self.bash,
            "str_replace_based_edit_tool": self.edit,
        }

        self.tool_params = [
            self.computer.tool_param(),
            self.bash.tool_param(),
            self.edit.tool_param(),
        ]

        self.system = [{
            "type": "text",
            "text": SYSTEM_PROMPT.format(
                system=platform.system(),
                release=platform.release(),
            ),
            "cache_control": {"type": "ephemeral"},  # cache the stable prefix
        }]

        self.messages: list = []

    # --- run one tool call ------------------------------------------------------
    def _dispatch(self, block) -> dict:
        tool = self.tools_by_name.get(block.name)
        try:
            if tool is None:
                result, is_error = f"unknown tool: {block.name}", True
            elif block.name == "computer":
                result, is_error = tool.run(block.input), False
            else:
                result, is_error = tool.run(block.input), False
        except Exception as e:  # noqa: BLE001 — surface any failure back to Claude
            result, is_error = f"tool error: {e}", True

        out: dict = {"type": "tool_result", "tool_use_id": block.id}
        if isinstance(result, list):  # image content blocks
            out["content"] = result
        else:
            out["content"] = [{"type": "text", "text": str(result)}]
        if is_error:
            out["is_error"] = True
        return out

    # --- main loop --------------------------------------------------------------
    def run_task(self, task: str) -> None:
        self.messages.append({"role": "user", "content": task})

        for step in range(self.max_steps):
            _prune_images(self.messages)

            text_started = False
            thinking_started = False

            with self.client.beta.messages.stream(
                model=self.model,
                max_tokens=8192,
                system=self.system,
                tools=self.tool_params,
                messages=self.messages,
                thinking={"type": "adaptive", "display": "summarized"},
                output_config={"effort": self.effort},
                betas=[COMPUTER_USE_BETA],
            ) as stream:
                for event in stream:
                    if event.type == "content_block_delta":
                        if event.delta.type == "thinking_delta":
                            if not thinking_started:
                                print("\n\033[2m[thinking] ", end="", flush=True)
                                thinking_started = True
                            print(event.delta.thinking, end="", flush=True)
                        elif event.delta.type == "text_delta":
                            if thinking_started and not text_started:
                                print("\033[0m", flush=True)  # close dim
                            if not text_started:
                                print("\n🤖 ", end="", flush=True)
                                text_started = True
                            print(event.delta.text, end="", flush=True)
                    elif event.type == "content_block_start" and \
                            event.content_block.type == "tool_use":
                        if thinking_started and not text_started:
                            print("\033[0m", flush=True)
                response = stream.get_final_message()

            print()  # newline after streamed output

            # Record assistant turn verbatim (preserves thinking + tool_use blocks).
            self.messages.append({"role": "assistant", "content": response.content})

            tool_uses = [b for b in response.content if b.type == "tool_use"]
            if not tool_uses:
                return  # Claude is done — final text already streamed.

            tool_results = []
            for block in tool_uses:
                action = block.input.get("action", block.name) if isinstance(block.input, dict) else block.name
                print(f"   ↳ {block.name}: {action}")
                tool_results.append(self._dispatch(block))

            self.messages.append({"role": "user", "content": tool_results})

        print("\n⏹  Reached the maximum step limit for this task. "
              "Send another instruction to continue, or raise DESKTOP_AGENT_MAX_STEPS.")
