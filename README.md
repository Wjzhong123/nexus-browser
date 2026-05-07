# Nexus Browser 🚀

The Ultimate AI-Native Browser & App Control Harness.

Nexus Browser combines the best of **OpenHarness** (Visualization), **Browser-Harness** (Self-healing), and **OpenCLI** (Stability & Session Reuse).

## Key Features

1.  **System-Wide Automation**: Control both standard web browsers and **Electron Desktop Apps** (Cursor, Notion, ChatGPT Desktop, etc.) via CDP attachment.
2.  **Self-Healing (Dynamic Evolution)**: Agents can discover, write, and hot-reload their own Python "Skills" to solve complex UI interaction problems in real-time.
3.  **Session Transparency**: Reuse your existing browser sessions, logins, and cookies by attaching to your running browser or using persistent profiles.
4.  **Headless-to-Head Visuals**: Monitor agent actions in real-time through the integrated visualization panel.

## Architecture

-   **AppHarness**: Handles the low-level CDP connection to Web/Electron.
-   **EvolutionHost**: Manages the `agent_workspace` and dynamic code reloading.
-   **Skill Registry**: A library of stable, deterministic adapters for common websites.

## Quick Start

### 1. Launch a browser or app with remote debugging
```bash
# Chrome
google-chrome --remote-debugging-port=9222

# Cursor / Electron
/Applications/Cursor.app/Contents/MacOS/Cursor --remote-debugging-port=9222
```

### 2. Start Nexus Browser
```bash
python -m nexus_browser.main
```

### 3. Attach and Evolve
Use the API to attach to the app and let the Agent start writing skills in `agent_workspace/agent_helpers.py`.

## Example Skill
Agents can write code like this into `agent_helpers.py`:
```python
async def github_star(harness, repo_name):
    page = harness.current_page
    await page.goto(f"https://github.com/{repo_name}")
    # Intelligent selector finding and clicking logic...
    return "Starred!"
```
The skill is immediately available via `/execute`.
