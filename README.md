# desktop_agent — a human-like computer-use agent for your machine

A standalone AI agent, powered by Claude (Opus 4.8), that controls your computer
the way a person does: it **looks at your screen** (screenshots), **moves and
clicks the mouse**, **types and uses keyboard shortcuts**, **scrolls**, **runs
terminal commands**, and **reads and writes files**. You give it a task in plain
English; it works through it step by step, checking the screen as it goes — the
same idea behind Perplexity's Comet assistant and OpenAI's Operator.

It runs **on your own machine**, so it can touch any app and any file your user
account can. Because that's powerful, it asks for your **y/N approval** before
running shell commands or writing files by default. You can turn that off (see
"YOLO mode"), but only do that inside a throwaway virtual machine.

---

## 1. What you need before starting (explained from zero)

You need three things. Don't worry, each is a one-time setup.

### a) Python (the language this is written in)
Open a terminal and type `python3 --version`.
- If you see something like `Python 3.10` or higher → you're good.
- If it says "command not found" → install Python from <https://www.python.org/downloads/>
  (Windows/macOS: download the installer and click through it. On the first
  Windows screen, **tick "Add Python to PATH"**.)

**What's a "terminal"?** It's the text window where you type commands:
- **Windows:** press Start, type `PowerShell`, hit Enter.
- **macOS:** press Cmd+Space, type `Terminal`, hit Enter.
- **Linux:** you already know 🙂 (or press Ctrl+Alt+T).

### b) An Anthropic API key (this is what powers the brain)
1. Go to <https://console.anthropic.com/> and sign in / sign up.
2. Click **API Keys → Create Key**. Copy the long string that starts with `sk-ant-...`.
3. Add a few dollars of credit under **Billing** (the agent calls the Claude API,
   which costs money per use — usually cents per task).

### c) This code
You already have it in this folder. The important files:
- `desktop_agent/` — the agent's code
- `requirements.txt` — the list of helper libraries to install
- `.env.example` — a template for your settings

---

## 2. Install it (copy-paste these, one block at a time)

In your terminal, go to this folder and install the libraries:

```bash
cd path/to/this/folder

# (recommended) make an isolated environment so this doesn't touch your system Python
python3 -m venv .venv
# turn it on:
#   macOS/Linux:
source .venv/bin/activate
#   Windows PowerShell:
#   .venv\Scripts\Activate.ps1

pip install -r requirements.txt
```

Then put in your API key:

```bash
cp .env.example .env       # Windows PowerShell: copy .env.example .env
```

Open the new `.env` file in any text editor and paste your key after
`ANTHROPIC_API_KEY=`. Save it.

### Platform notes (one-time permissions)
- **macOS:** the first time it tries to move the mouse / read the screen, macOS
  will pop up permission requests. Go to **System Settings → Privacy & Security**
  and switch **on** your terminal app under both **Accessibility** and **Screen
  Recording**, then restart the terminal. (This is macOS protecting you — it's
  expected.)
- **Linux:** screen control needs an X11 desktop session. If screenshots fail,
  install `scrot`: `sudo apt install scrot python3-tk python3-dev`.
- **Windows:** usually works out of the box.

---

## 3. Run it

**Watch-it-work interactive mode** (you type tasks, it does them):

```bash
python -m desktop_agent
```

You'll see a `you ▸` prompt. Type a task and press Enter, e.g.:

> open the calculator app and compute 1234 times 5678

**One-shot mode** (run a single task and exit):

```bash
python -m desktop_agent "open my browser, go to wikipedia.org, and search for octopus"
```

To stop at any time: press **Ctrl+C**.

> ⚠️ **It will take over your mouse and keyboard while working.** Keep your hands
> off, and keep a Ctrl+C ready. The very first run, try something harmless to get
> comfortable with how it behaves.

---

## 4. Where you SEE what it's doing

Everything streams live in the same terminal window:

- **`[thinking] ...`** (dim text) — the agent's reasoning about what to do next.
- **`🤖 ...`** — the agent talking to you (plans, summaries, questions).
- **`↳ computer: left_click`** etc. — each real action as it happens.
- The mouse and keyboard **physically move on your screen** — that's the agent
  acting. You're watching it operate the machine in real time.

When a task is done, it prints a short summary and returns to the `you ▸` prompt.

---

## 5. How you MANAGE / control it (safety)

By default it runs in **"ask" mode**: before any **shell command** or **file
write**, it pauses and shows you exactly what it wants to do:

```
┳ Agent wants to run a shell command:
┃   rm -rf ./build
┗ Allow? [y]es / [N]o / [a]llow-all-this-session:
```

- `y` → run it once
- `N` (or just Enter) → refuse; the agent is told "denied" and will adapt/ask you
- `a` → stop asking for the rest of this session

GUI clicks and typing aren't gated (you can see those happen on screen). Commands
that look destructive (`rm -rf`, disk formatting, force-push, pipe-to-shell
installs, etc.) get a loud `⚠️ LOOKS DESTRUCTIVE` warning.

**Settings** — change these in `.env`, or pass flags:
| Setting | `.env` | Flag | Default |
|---|---|---|---|
| Model | `DESKTOP_AGENT_MODEL` | `--model` | `claude-opus-4-8` |
| Thinking effort | `DESKTOP_AGENT_EFFORT` | `--effort` | `high` |
| Approval mode | `DESKTOP_AGENT_MODE` | `--yolo` | `ask` |
| Max steps/task | `DESKTOP_AGENT_MAX_STEPS` | `--max-steps` | `60` |

### YOLO mode (no approvals)
```bash
python -m desktop_agent --yolo "do the whole thing without asking"
```
This skips every approval. **Only run this inside a disposable virtual machine**
(see below). On your real machine, an unattended agent with full keyboard/file/
shell access can do real, irreversible damage and is vulnerable to prompt
injection (a malicious webpage telling it to do something you didn't ask for).

### The genuinely safe way to give it "full access to everything"
Run it inside a throwaway VM or container that has nothing of yours in it:
1. Install [VirtualBox](https://www.virtualbox.org/) or [Multipass](https://multipass.run/) and create a fresh Linux/Windows VM.
2. Copy this folder into the VM, install, and run with `--yolo` there.
3. The agent then has "no limits" — but only over a sandbox you can delete and
   recreate, not your actual files, passwords, and accounts.

---

## 6. How it works under the hood (1 paragraph)

`desktop_agent/agent.py` runs the **agent loop**: it sends Claude your task plus
the current screenshot; Claude replies with an action (click here, type this, run
this command); `desktop_agent/tools.py` performs that action with
[PyAutoGUI](https://pyautogui.readthedocs.io/) (mouse/keyboard/screen) or the
shell/filesystem; the result (a new screenshot or command output) goes back to
Claude; repeat until the task is done. It uses Claude's official **computer-use**,
**bash**, and **text-editor** tools, adaptive thinking, prompt caching, and
streaming. Old screenshots are pruned from history to keep cost down.

```
your task ─▶ Claude (sees screen) ─▶ action ─▶ PyAutoGUI/shell runs it
                ▲                                      │
                └────────── screenshot/result ◀────────┘   (loops)
```

---

## 7. This isn't the only one — open-source agents worth knowing

This project is modeled on **Anthropic's own reference implementation** and the
broader open-source ecosystem. If you want a ready-made GUI app or a
higher-scoring agent instead of (or alongside) this, these are the notable ones:

| Project | What it is | Link |
|---|---|---|
| **Anthropic computer-use-demo** | The official reference: tools + agent loop + Docker desktop + web UI. This repo follows its design. | <https://github.com/anthropics/anthropic-quickstarts/tree/main/computer-use-demo> |
| **NeuralAgent** | Free, open-source desktop agent that controls your computer like a human (clicks, types, browses, emails). | <https://www.scriptbyai.com/desktop-automation-neuralagent/> |
| **Agent S2 (simular-ai/Agent-S)** | Research agent, state-of-the-art on the OSWorld benchmark; strong on complex multi-app workflows. | <https://github.com/simular-ai/Agent-S> |
| **Open Computer Use (coasty-ai)** | Production-ready, high OSWorld score, local or remote, one API key. | <https://github.com/coasty-ai/open-computer-use> |
| **Self-Operating Computer (OthersideAI)** | Framework to operate the computer via multiple vision models. | <https://github.com/OthersideAI/self-operating-computer> |
| **Open Interpreter (OS mode)** | Natural-language interpreter that can drive the desktop via screenshots. | <https://github.com/OpenInterpreter/open-interpreter> |
| **computer-agent (suitedaces)** | Desktop app controlling computer via terminal, browser, mouse & keyboard. | <https://github.com/suitedaces/computer-agent> |
| **Browser Use** | If you mainly want *web* automation rather than full desktop control. | <https://github.com/browser-use/browser-use> |

**Why I still built this one:** it's small, readable, single-file-per-concern,
runs from one `python -m desktop_agent` command, has the human-approval safety
gate built in, and targets the latest Claude (Opus 4.8) tool versions — so it's
easy for you to read, trust, and modify. For a polished GUI, Docker sandbox, or
benchmark-topping accuracy, start from the Anthropic demo or Agent S2 above.

---

## 8. Troubleshooting

- **"Failed to start … Is ANTHROPIC_API_KEY set?"** → You didn't create `.env` or
  didn't paste the key. Redo step 2.
- **Mouse doesn't move / black screenshots (macOS)** → grant Accessibility +
  Screen Recording permissions and restart the terminal (step 2 platform notes).
- **`ModuleNotFoundError: pyautogui`** → activate your venv and re-run
  `pip install -r requirements.txt`.
- **It clicked the wrong spot** → lower your screen resolution a touch, or ask the
  task more specifically ("click the blue *Sign in* button top-right").
- **Costs adding up** → lower `DESKTOP_AGENT_EFFORT` to `medium`, and
  `DESKTOP_AGENT_MAX_STEPS`.
