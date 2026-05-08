# Nexus Browser Integration: Technical Architecture & Evolution Guide 🧠

## 1. Overview
Nexus Browser is the next-generation automation engine integrated into the **One Desktop** ecosystem. It provides a bridge between AI Agents and the digital world (both Web and Desktop Apps) by combining visual transparency with autonomous self-healing capabilities.

## 2. The Three Pillars

### I. CDP-Powered Attachment (The Bridge)
Unlike traditional tools that launch isolated, empty browsers, Nexus Browser **attaches** to your live environment.
- **Session Reuse**: Inherits all your logins, cookies, and local state from Chrome or Edge.
- **Electron Control**: Can control desktop apps like **Cursor, VS Code, Notion, and ChatGPT Desktop** by attaching to their remote debugging ports (`--remote-debugging-port=9222`).

### II. Dynamic Evolution (The Soul)
Nexus Browser implements a **Hot-Reload Engine**. 
- **Self-Healing**: When an Agent fails a task, it can analyze the failure, write a new Python helper script to `agent_workspace/agent_helpers.py`, and the engine will instantly reload it.
- **Zero Downtime**: The Agent evolves its own instruction set without restarting the backend.

### III. Deterministic Skill System (The Power)
We abstract complex UI interactions into **Stable Skills**.
- **Adapters**: Pre-built, robust adapters for major platforms:
  - **Domestic**: Bilibili, 知乎 (Zhihu), 微信公众号 (via visual mode).
  - **Global**: Google, GitHub, YouTube, Reddit, Wikipedia.
- **Pattern**: Uses "Parent-Climbing" logic instead of fragile CSS selectors to ensure stability during site UI updates.

## 3. Directory Structure
```text
packages/nexus-browser/
├── src/nexus_browser/
│   ├── app_harness.py      # Low-level CDP & Attachment logic
│   ├── evolution_host.py   # Dynamic code loading & reloading
│   └── skills/             # Pre-built site adapters (The "Brain")
├── agent_workspace/        # Sandbox where Agents write evolution code
└── README.md               # Quick start and API docs
```

## 4. How to Use with Agents

### For Comprehensive Search:
Agents are instructed to use the **Observer-Refiner Pattern**:
1. Use traditional AI Search for broad landscape.
2. Use `nexus_skill` (e.g., `search_bilibili`) to gather deep, real-world experience or private data.

### For Desktop Automation:
1. Start the target app with `--remote-debugging-port=9222`.
2. Agent calls `attach(port=9222)` to take over the desktop UI.

## 5. Security & Privacy
Nexus Browser runs locally. It respects your privacy by keeping all data within your own browser profile and only acting on your behalf when explicitly triggered by the Agent's task.
