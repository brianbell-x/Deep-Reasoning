from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, model_validator

# ──────────────────────────────
# Planner-side models
# ──────────────────────────────

class PlanStep(BaseModel):
    step_id: str
    instructions: str
    response: Optional[str] = None

class ExplorationPlan(BaseModel):
    plan_id: str
    strategy: str
    overview: Optional[str] = None
    steps: List[PlanStep]

    @model_validator(mode="after")
    def validate_strategy(self):
        if not self.strategy or not self.strategy.strip():
            raise ValueError("strategy is required and must be non-empty")
        return self

class PlannerOut(BaseModel):
    exploration_plans: List[ExplorationPlan]

    @model_validator(mode="after")
    def max_five_plans(cls, v):
        if len(v.exploration_plans) > 5:
            raise ValueError("At most 5 exploration plans allowed")
        return v

# ──────────────────────────────
# Reviewer-side models
# ──────────────────────────────

class ContextSelection(BaseModel):
    plan_id: str
    step_ids: List[str]

class ReviewerOut(BaseModel):
    assessment_of_current_iteration: str
    context_to_use: Optional[List[ContextSelection]] = None
