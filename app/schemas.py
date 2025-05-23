from typing import List, Optional, Literal
from pydantic import BaseModel, model_validator

# ──────────────────────────────
# Planner-side models
# ──────────────────────────────

class PlanStep(BaseModel):
    step_id: str
    instructions: str
    dependencies: Optional[List[str]] = None
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

class NextIterationGuidance(BaseModel):
    action: Literal[
        "DEEPEN",
        "BROADEN",
        "CONTINUE_DFS_PATH",
        "RETRY_STEP_WITH_MODIFICATION",
        "HALT_SUFFICIENT",
        "HALT_STAGNATION",
        "HALT_NO_FEASIBLE_PATH"
    ]
    reasoning: str
    target_plan_id: Optional[str] = None
    target_step_id: Optional[str] = None
    refinement_details: Optional[str] = None
    excluded_strategies: Optional[List[str]] = None
    suggested_strategy: Optional[str] = None
    dfs_path_summary: Optional[str] = None

class ReviewerOut(BaseModel):
    iteration_assessment: str
    synthesis_ready: bool
    selected_context: Optional[List[ContextSelection]] = None
    next_iteration_guidance: NextIterationGuidance
