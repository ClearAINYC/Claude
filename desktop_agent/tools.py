"""Tool implementations that give the agent human-like control of the machine.

Three tools, matching Anthropic's built-in tool schemas so we don't have to
hand-write JSON schemas (the model already knows them):

  * computer (computer_20251124) — screenshot, mouse, keyboard, scroll, zoom
  * bash     (bash_20250124)     — run shell commands on the host
  * str_replace_based_edit_tool (text_editor_20250728) — read / write files

The computer tool is backed by PyAutoGUI, which works on Windows, macOS and
Linux (X11). Screenshots are captured, downscaled to fit Claude's vision
limits, and Claude's pixel coordinates are scaled back to real screen
coordinates — this also transparently handles Retina / HiDPI displays where the
screenshot is larger than the logical click space.
"""

from __future__ import annotations

import base64
import io
import os
import platform
import subprocess
import time
from pathlib import Path

import pyautogui
from PIL import Image

from .safety import Approver

# Claude Opus 4.x accepts images up to 2576 px on the long edge with
# coordinates 1:1 to image pixels — so as long as we declare the display size
# we send, no scale-factor guessing is needed on the model's side.
MAX_LONG_EDGE = 2576

# Don't let PyAutoGUI abort the whole program when the mouse hits a screen
# corner; we manage our own stop conditions instead.
pyautogui.FAILSAFE = False
pyautogui.PAUSE = 0.05

# Map the X11-style key names Claude emits to PyAutoGUI key names.
_KEYMAP = {
    "return": "enter",
    "enter": "enter",
    "kp_enter": "enter",
    "escape": "esc",
    "esc": "esc",
    "back_space": "backspace",
    "backspace": "backspace",
    "delete": "delete",
    "tab": "tab",
    "space": "space",
    "prior": "pageup",
    "page_up": "pageup",
    "next": "pagedown",
    "page_down": "pagedown",
    "home": "home",
    "end": "end",
    "up": "up",
    "down": "down",
    "left": "left",
    "right": "right",
    "ctrl": "ctrl",
    "control": "ctrl",
    "alt": "alt",
    "shift": "shift",
    "super": "command" if platform.system() == "Darwin" else "win",
    "cmd": "command",
    "meta": "command" if platform.system() == "Darwin" else "win",
}


def _norm_key(token: str) -> str:
    t = token.strip().lower()
    return _KEYMAP.get(t, t)


def _b64_png(img: Image.Image) -> str:
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return base64.standard_b64encode(buf.getvalue()).decode("utf-8")


def _image_block(img: Image.Image) -> dict:
    return {
        "type": "image",
        "source": {"type": "base64", "media_type": "image/png", "data": _b64_png(img)},
    }


class ComputerTool:
    """Screen + mouse + keyboard, the way a human uses them."""

    name = "computer"

    def __init__(self):
        # Logical screen size = the coordinate space PyAutoGUI clicks in.
        self.screen_w, self.screen_h = pyautogui.size()

        # Figure out the image size we report to Claude by measuring an actual
        # screenshot (which may be larger than logical size on HiDPI screens)
        # and downscaling to the vision limit.
        shot = pyautogui.screenshot()
        sw, sh = shot.size
        scale = min(1.0, MAX_LONG_EDGE / max(sw, sh))
        self.img_w = round(sw * scale)
        self.img_h = round(sh * scale)

    def tool_param(self) -> dict:
        return {
            "type": "computer_20251124",
            "name": "computer",
            "display_width_px": self.img_w,
            "display_height_px": self.img_h,
            "display_number": 1,
            "enable_zoom": True,
        }

    # --- coordinate translation -------------------------------------------------
    def _to_screen(self, coord) -> tuple[int, int]:
        x, y = coord
        sx = int(round(x / self.img_w * self.screen_w))
        sy = int(round(y / self.img_h * self.screen_h))
        sx = max(0, min(self.screen_w - 1, sx))
        sy = max(0, min(self.screen_h - 1, sy))
        return sx, sy

    def _screenshot_image(self) -> Image.Image:
        img = pyautogui.screenshot()
        if img.size != (self.img_w, self.img_h):
            img = img.resize((self.img_w, self.img_h), Image.LANCZOS)
        return img.convert("RGB")

    # --- main dispatch ----------------------------------------------------------
    def run(self, params: dict):
        """Execute one computer action. Returns a string or a content-block list."""
        action = params.get("action")
        mods = [_norm_key(m) for m in str(params.get("text", "")).split("+") if m] \
            if action in ("left_click", "right_click", "middle_click", "double_click",
                          "triple_click", "scroll") and params.get("text") else []

        if action == "screenshot":
            return [_image_block(self._screenshot_image())]

        if action == "cursor_position":
            x, y = pyautogui.position()
            ix = int(round(x / self.screen_w * self.img_w))
            iy = int(round(y / self.screen_h * self.img_h))
            return f"cursor at ({ix}, {iy})"

        if action == "mouse_move":
            x, y = self._to_screen(params["coordinate"])
            pyautogui.moveTo(x, y)
            return f"moved to ({x}, {y})"

        if action in ("left_click", "right_click", "middle_click", "double_click", "triple_click"):
            x, y = self._to_screen(params["coordinate"])
            button = {"left_click": "left", "right_click": "right", "middle_click": "middle",
                      "double_click": "left", "triple_click": "left"}[action]
            clicks = {"double_click": 2, "triple_click": 3}.get(action, 1)
            for m in mods:
                pyautogui.keyDown(m)
            try:
                pyautogui.click(x, y, clicks=clicks, interval=0.05, button=button)
            finally:
                for m in reversed(mods):
                    pyautogui.keyUp(m)
            return f"{action} at ({x}, {y})" + (f" with {'+'.join(mods)}" if mods else "")

        if action == "left_click_drag":
            x, y = self._to_screen(params["coordinate"])
            pyautogui.dragTo(x, y, duration=0.4, button="left")
            return f"dragged to ({x}, {y})"

        if action == "left_mouse_down":
            pyautogui.mouseDown()
            return "left mouse down"

        if action == "left_mouse_up":
            pyautogui.mouseUp()
            return "left mouse up"

        if action == "type":
            text = params.get("text", "")
            pyautogui.write(text, interval=0.01)
            return f"typed {len(text)} chars"

        if action == "key":
            keys = [_norm_key(k) for k in str(params.get("text", "")).split("+") if k]
            if len(keys) > 1:
                pyautogui.hotkey(*keys)
            elif keys:
                pyautogui.press(keys[0])
            return f"pressed {'+'.join(keys)}"

        if action == "hold_key":
            keys = [_norm_key(k) for k in str(params.get("text", "")).split("+") if k]
            duration = float(params.get("duration", 1))
            for k in keys:
                pyautogui.keyDown(k)
            time.sleep(duration)
            for k in reversed(keys):
                pyautogui.keyUp(k)
            return f"held {'+'.join(keys)} for {duration}s"

        if action == "scroll":
            x, y = self._to_screen(params["coordinate"]) if params.get("coordinate") else pyautogui.position()
            pyautogui.moveTo(x, y)
            direction = params.get("scroll_direction", "down")
            amount = int(params.get("scroll_amount", 3))
            clicks = amount * 100
            for m in mods:
                pyautogui.keyDown(m)
            try:
                if direction in ("up", "down"):
                    pyautogui.scroll(clicks if direction == "up" else -clicks, x=x, y=y)
                else:
                    pyautogui.hscroll(clicks if direction == "right" else -clicks, x=x, y=y)
            finally:
                for m in reversed(mods):
                    pyautogui.keyUp(m)
            return f"scrolled {direction} {amount}"

        if action == "wait":
            duration = float(params.get("duration", 1))
            time.sleep(min(duration, 10))
            return f"waited {duration}s"

        if action == "zoom":
            region = params.get("region")
            full = pyautogui.screenshot().convert("RGB")
            # region is in declared-image space; map to real screenshot pixels.
            fw, fh = full.size
            x1, y1, x2, y2 = region
            box = (int(x1 / self.img_w * fw), int(y1 / self.img_h * fh),
                   int(x2 / self.img_w * fw), int(y2 / self.img_h * fh))
            crop = full.crop(box)
            return [_image_block(crop)]

        return f"unsupported action: {action}"


class BashTool:
    """Run shell commands on the host (gated by the approver)."""

    name = "bash"

    def __init__(self, approver: Approver):
        self.approver = approver
        self.cwd = os.getcwd()

    def tool_param(self) -> dict:
        return {"type": "bash_20250124", "name": "bash"}

    def run(self, params: dict) -> str:
        if params.get("restart"):
            self.cwd = os.getcwd()
            return "bash session reset"

        command = params.get("command", "")
        if not command:
            return "no command provided"

        if not self.approver.confirm("shell command", command):
            return "DENIED by user — command was not run. Ask the user what to do instead."

        try:
            proc = subprocess.run(
                command, shell=True, cwd=self.cwd, capture_output=True,
                text=True, timeout=300,
            )
        except subprocess.TimeoutExpired:
            return "command timed out after 300s"

        out = (proc.stdout or "")[-12000:]
        err = (proc.stderr or "")[-4000:]
        parts = []
        if out:
            parts.append(out)
        if err:
            parts.append(f"[stderr]\n{err}")
        parts.append(f"[exit code {proc.returncode}]")
        return "\n".join(parts)


class EditTool:
    """Anthropic text-editor tool: view / create / str_replace / insert."""

    name = "str_replace_based_edit_tool"

    def __init__(self, approver: Approver):
        self.approver = approver

    def tool_param(self) -> dict:
        return {"type": "text_editor_20250728", "name": "str_replace_based_edit_tool"}

    def run(self, params: dict) -> str:
        cmd = params.get("command")
        path = Path(params.get("path", "")).expanduser()

        if cmd == "view":
            if path.is_dir():
                return "\n".join(sorted(str(p) for p in path.iterdir()))
            try:
                text = path.read_text(errors="replace")
            except Exception as e:  # noqa: BLE001
                return f"error reading {path}: {e}"
            rng = params.get("view_range")
            lines = text.splitlines()
            if rng:
                start, end = rng
                end = len(lines) if end == -1 else end
                lines = lines[start - 1:end]
                offset = start
            else:
                offset = 1
            return "\n".join(f"{i + offset:>6}\t{ln}" for i, ln in enumerate(lines))

        if cmd == "create":
            if not self.approver.confirm("file write (create)", str(path)):
                return "DENIED by user — file was not created."
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(params.get("file_text", ""))
            return f"created {path}"

        if cmd == "str_replace":
            if not self.approver.confirm("file write (edit)", str(path)):
                return "DENIED by user — file was not modified."
            text = path.read_text()
            old = params.get("old_str", "")
            count = text.count(old)
            if count == 0:
                return "old_str not found — no change made"
            if count > 1:
                return f"old_str matches {count} times — make it unique"
            path.write_text(text.replace(old, params.get("new_str", ""), 1))
            return f"edited {path}"

        if cmd == "insert":
            if not self.approver.confirm("file write (insert)", str(path)):
                return "DENIED by user — file was not modified."
            lines = path.read_text().splitlines(keepends=True)
            idx = int(params.get("insert_line", 0))
            new = params.get("new_str", "")
            if not new.endswith("\n"):
                new += "\n"
            lines.insert(idx, new)
            path.write_text("".join(lines))
            return f"inserted into {path} at line {idx}"

        return f"unsupported edit command: {cmd}"
