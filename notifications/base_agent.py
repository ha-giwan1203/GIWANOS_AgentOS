#!/usr/bin/env python
"""
Base classes for GIWANOS agents.

These classes define the common interface used by all agents in the system.
Each agent is responsible for one part of the overall workflow
(e.g., judgement, execution, reflection, reporting). Concrete agents should
subclass BaseAgent and implement the abstract methods accordingly.

The goal of this skeleton is to provide a clear extension point for
developers looking to add agent capabilities to the GIWANOS system.
The implementation details (such as calling existing GIWANOS scripts,
handling data formats, etc.) should be filled in based on the actual
application requirements.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

class BaseAgent:
    """Common interface for all GIWANOS agents."""

    def __init__(self, tools: Optional[List[Any]] = None, instructions: str = "") -> None:
        self.tools: List[Any] = tools or []
        self.instructions: str = instructions

    def plan(self, *args: Any, **kwargs: Any) -> Any:
        """Plan the next action based on provided input."""
        raise NotImplementedError("Agents must implement a plan method")

    def execute(self, plan: Any) -> Any:
        """Execute a plan and return results."""
        raise NotImplementedError("Agents must implement an execute method")

    def reflect(self, *args: Any, **kwargs: Any) -> Any:
        """Perform reflection or evaluation on the results."""
        raise NotImplementedError("Agents must implement a reflect method")

    def report(self, *args: Any, **kwargs: Any) -> None:
        """Send or persist the results of the workflow."""
        raise NotImplementedError("Agents must implement a report method")
