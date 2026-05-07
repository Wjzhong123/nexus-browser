import asyncio
import os
import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any

from .app_harness import AppHarness
from .evolution_host import EvolutionHost

app = FastAPI(title="Nexus Browser API", version="0.1.0")

# Singletons
harness = AppHarness()
workspace_path = os.path.abspath(os.path.join(os.getcwd(), "agent_workspace"))
evolution = EvolutionHost(workspace_path)

class AttachRequest(BaseModel):
    host: str = "127.0.0.1"
    port: int = 9222

class ExecuteRequest(BaseModel):
    skill_name: str
    args: list = []
    kwargs: dict = {}

class EvolveRequest(BaseModel):
    code: str

@app.on_event("startup")
async def startup():
    await harness.start()
    evolution.reload_helpers()

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
        # We pass harness to the skill so it can control the browser
        result = await evolution.execute_skill(req.skill_name, harness, *req.args, **req.kwargs)
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
        "workspace": workspace_path
    }

def main():
    uvicorn.run(app, host="0.0.0.0", port=8000)

if __name__ == "__main__":
    main()
