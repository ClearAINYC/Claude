# Your Computer Agent (like Perplexity's, but it has its own computer)

This sets up **Bytebot** — a free, open-source AI agent that works like Perplexity's
computer assistant: you give it a task in plain English, and it does the whole thing
on its own — browsing the web, filling forms, using apps, handling files. It runs on
**its own private computer** (a safe, self-contained desktop on your machine), so it
can do anything you ask without touching your personal files or passwords.

You watch and talk to it through a normal web page in your browser.

> You do **not** need to be a programmer. Follow the steps below in order.

---

## ✅ What you'll do (3 things, ~10 minutes once)
1. Install one free program called **Docker Desktop**.
2. Double-click a start file (or paste one line).
3. Open a web page and start giving the agent tasks.

---

## Step 1 — Install Docker Desktop (one time)
Docker is the free tool that runs the agent's private computer.

1. Go to **<https://www.docker.com/products/docker-desktop/>**
2. Download the version for your computer (Mac or Windows) and install it like any app.
3. **Open the Docker Desktop app.** Wait until the little whale icon / status says
   **"running"**. Leave it open.

That's the only install. You only ever do this once.

---

## Step 2 — Start the agent

**On a Mac:**
1. Open the **Terminal** app (press `Cmd+Space`, type `Terminal`, press Enter).
2. Type `bash ` (with a space), then **drag the `start-agent.sh` file** from this
   folder into the Terminal window, then press **Enter**.
3. The first time, it will ask you to paste your **Anthropic API key** — get one at
   <https://console.anthropic.com> → *API Keys* (and add a few dollars of credit under
   *Billing*). Paste it, press Enter.

**On Windows:**
1. **Right-click `start-agent.ps1`** in this folder → **"Run with PowerShell"**.
2. When asked, paste your **Anthropic API key** (from the same link above) and press Enter.

Either way, the first start takes **2–3 minutes** while it downloads. When it's ready
it prints a link and tries to open your browser automatically.

---

## Step 3 — Give it a task and watch it work
1. In your browser, go to **<http://localhost:9992>** (the start script opens this for you).
2. You'll see a chat box and a live view of the agent's screen.
3. **Type what you want in plain English**, for example:
   - *"Go to wikipedia.org, find the article on octopuses, and save a summary to a text file."*
   - *"Open the spreadsheet I describe and total column C."*
   - *"Research the top 3 standing desks under $400 and make me a comparison table."*
4. Press Enter and **watch it do the whole task by itself** on the screen view — clicking,
   typing, browsing — just like Perplexity's computer. You can type follow-up messages
   any time, or tell it to stop.

That's it. Give a task → it does it all.

---

## Turning it off / on
- **Stop it:** Mac → `bash stop-agent.sh` (or drag that file into Terminal). Windows →
  in PowerShell run `docker compose -f bytebot\docker\docker-compose.yml down`. You can
  also just quit Docker Desktop.
- **Start it again later:** repeat Step 2. It's instant after the first download.

---

## If something goes wrong
- **"Docker isn't installed / running"** → open the Docker Desktop app and wait for
  "running", then start again.
- **The page won't load at localhost:9992** → give it another minute (first run is slow),
  refresh the page.
- **It asks for the API key again** → that just means the key wasn't saved; paste it again.
- **Costs** → the agent uses the Claude API, which costs a few cents per task from your
  Anthropic credit. Keep an eye on usage in the Anthropic console.

---

## What's in this folder
| File | What it's for |
|---|---|
| `start-agent.sh` | Mac/Linux: sets up + starts the agent |
| `start-agent.ps1` | Windows: sets up + starts the agent |
| `stop-agent.sh` | Mac/Linux: stops the agent |
| `bytebot/` | The agent itself (downloaded automatically on first start) |

This is just a thin wrapper around **[Bytebot](https://github.com/bytebot-ai/bytebot)**
(open source, Apache 2.0). The start scripts download it and plug in your Claude key —
nothing custom to maintain.

> Safety note: the agent has full control of its **own** private computer, so it can do
> anything you ask there. It can't reach your personal files or accounts unless you hand
> it a file or log it into something. Avoid giving it real passwords or payment details
> until you trust how it behaves.
