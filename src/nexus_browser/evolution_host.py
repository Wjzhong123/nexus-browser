import importlib
import importlib.util
import os
import sys
import logging
import asyncio
from typing import Any, Callable, Dict

logger = logging.getLogger("nexus_browser.evolution")

class EvolutionHost:
    """
    Handles dynamic loading and hot-reloading of Agent-generated code.
    This allows the Agent to 'evolve' its own browser control logic.
    """

    def __init__(self, workspace_path: str):
        self.workspace_path = workspace_path
        self.helpers_file = os.path.join(workspace_path, "agent_helpers.py")
        self.skills: Dict[str, Callable] = {}
        
        # Ensure the file exists
        if not os.path.exists(self.helpers_file):
            with open(self.helpers_file, "w") as f:
                f.write("# Nexus Browser Agent Helpers\n# Agent can edit this file to add new skills.\n\n")

    def reload_helpers(self):
        """Dynamic reload of the agent_helpers module."""
        module_name = "nexus_agent_helpers"
        
        try:
            spec = importlib.util.spec_from_file_location(module_name, self.helpers_file)
            if spec is None or spec.loader is None:
                raise Exception("Failed to load spec for agent_helpers.py")
                
            module = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = module
            spec.loader.exec_module(module)
            
            # Map all functions in the module to our skills dict
            new_skills = {}
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if callable(attr) and not attr_name.startswith("__"):
                    new_skills[attr_name] = attr
            
            self.skills = new_skills
            logger.info(f"Reloaded {len(self.skills)} skills from {self.helpers_file}")
            return True, f"Successfully reloaded {len(self.skills)} skills."
            
        except Exception as e:
            logger.error(f"Error reloading helpers: {e}")
            return False, str(e)

    async def execute_skill(self, skill_name: str, *args, **kwargs) -> Any:
        """Execute a dynamically loaded skill."""
        if skill_name not in self.skills:
            # Try one reload just in case
            self.reload_helpers()
            if skill_name not in self.skills:
                raise ValueError(f"Skill '{skill_name}' not found in agent_helpers.py")
        
        skill_func = self.skills[skill_name]
        
        if asyncio.iscoroutinefunction(skill_func):
            return await skill_func(*args, **kwargs)
        else:
            return skill_func(*args, **kwargs)

    def write_helper_code(self, code_snippet: str):
        """Allows the Agent to append or overwrite helper code."""
        # Simple implementation: append to the end
        with open(self.helpers_file, "a") as f:
            f.write("\n\n" + code_snippet + "\n")
        
        return self.reload_helpers()
