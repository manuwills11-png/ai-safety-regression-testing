"""Pydantic models for the Vulnerability Archive."""
import time
from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field


class RiskCategory(str, Enum):
    ROLEPLAY_BYPASS = "roleplay_bypass"
    PROMPT_INJECTION = "prompt_injection"
    MULTI_TURN_ESCALATION = "multi_turn_escalation"
    TOOL_MISUSE = "tool_misuse"


class Attack(BaseModel):
    category: RiskCategory
    prompt: str
    refinement_reasoning: str


class Verdict(BaseModel):
    verdict: Literal["pass", "fail"]
    confidence: Literal["low", "medium", "high"]
    reasoning: str


class ArchiveRecord(BaseModel):
    iteration: int
    category: RiskCategory
    attack_prompt: str
    refinement_reasoning: str
    target_response: str
    verdict: Literal["pass", "fail"]
    confidence: Literal["low", "medium", "high"]
    reasoning: str
    timestamp: float = Field(default_factory=time.time)
