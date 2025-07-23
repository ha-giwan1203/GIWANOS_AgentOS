#!/usr/bin/env python
from giwanos_agent.base_agent import BaseAgent
from typing import Any, Dict, Optional
import subprocess, json, sys

class LoopAgent(BaseAgent):
    """Agent that executes loops based on a plan."""

    def plan(self, loop_name: str, parameters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        return {"loop_name": loop_name, "parameters": parameters or {}}

    def execute(self, plan: Dict[str, Any]) -> Dict[str, Any]:
        # GIWANOS 란처 스크립트 호출
        launcher = r"C:\giwanos\giwanos_launcher.py"
        loop_name: str = plan.get("loop_name", "")
        parameters: Dict[str, Any] = plan.get("parameters", {})

        args = ["python", launcher, loop_name]
        for k, v in parameters.items():
            args.append(f"--{k}={v}")

        try:
            result = subprocess.run(
                args,
                capture_output=True,
                encoding="utf-8",
                errors="ignore",
                check=True
            )
            return json.loads(result.stdout or "{}")
        except Exception as e:
            print("LoopAgent Error:", e, file=sys.stderr)
            return {"status": "failed", "error": str(e), "loop_name": loop_name}

    def reflect(self, *args: Any, **kwargs: Any) -> None:
        return None

    def report(self, *args: Any, **kwargs: Any) -> None:
        return None
