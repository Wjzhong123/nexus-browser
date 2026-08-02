import os
from contextlib import asynccontextmanager
from pathlib import Path

import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from nexus_browser.app_harness import AppHarness
from nexus_browser.evolution_host import EvolutionHost
from nexus_browser.skills.manager import SkillManager

# --- lifecycle ---

@asynccontextmanager
async def lifespan(app: FastAPI):
    # startup
    await harness.start()
    evolution.reload_helpers()
    evolution.skills.update(skill_manager.get_skill_map())
    yield
    # shutdown
    await skill_manager.close()
    await harness.close()

app = FastAPI(title="Nexus Browser API", version="0.1.0", lifespan=lifespan)

# --- singletons ---
harness = AppHarness()
workspace_path = Path(__file__).resolve().parents[2] / "agent_workspace"
workspace_path.mkdir(parents=True, exist_ok=True)
evolution = EvolutionHost(str(workspace_path))
skill_manager = SkillManager(harness)


# --- request models ---

class AttachRequest(BaseModel):
    host: str = "127.0.0.1"
    port: int = 9222

class ExecuteRequest(BaseModel):
    skill_name: str
    args: list = []
    kwargs: dict = {}

class EvolveRequest(BaseModel):
    code: str


# --- routes ---

@app.post("/attach")
async def attach(req: AttachRequest):
    result = await harness.attach(req.host, req.port)
    if result["status"] == "error":
        raise HTTPException(status_code=500, detail=result["message"])
    return result

@app.get("/pages")
async def get_pages():
    return await harness.get_pages_info()

@app.post("/execute")
async def execute_skill(req: ExecuteRequest):
    try:
        result = await evolution.execute_skill(req.skill_name, *req.args, **req.kwargs)
        return {"status": "success", "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/evolve")
async def evolve(req: EvolveRequest):
    success, message = evolution.write_helper_code(req.code)
    if not success:
        raise HTTPException(status_code=500, detail=message)
    return {"status": "success", "message": message}

@app.get("/status")
async def status():
    return {
        "attached": harness.browser is not None,
        "skills": list(evolution.skills.keys()),
        "workspace": str(workspace_path),
    }


# --- entry point ---

def main():
    uvicorn.run(app, host="0.0.0.0", port=8000)

if __name__ == "__main__":
    main()