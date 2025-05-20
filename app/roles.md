## PlannerAgent
- **Purpose** - Generates an exploration plan for the main task.
- **Strategy** - Decides on best exploration strategys for the task (e.g., Comparative Analysis, SCAMPER).
- **Steps** - Breaks plan into minimal, independent steps with clear instructions.
- **Inputs** - Receives `main_task` and optional `previous_review_guidance`.
- **Outputs** - Returns a JSON object with a list of plans, each with a strategy and steps.

## ThinkerAgent
- **Purpose** - Performs deep reasoning on a single assigned step from the plan.
- **Instructions** - Follows the step’s instructions and the plan-level strategy.
- **Inputs** - Receives `sub_task_description` and optional `main_task_context`.
- **Outputs** - Returns a well-reasoned response for the assigned step.

## ReviewerAgent
- **Purpose** - Evaluates the ThinkerAgent’s outputs against the plan and main task.
- **Assessment** - Checks if the plan’s objectives were met and if the strategy was followed.
- **Guidance** - Provides actionable feedback for the next plan or signals when to stop.
- **Inputs** - Receives `main_task`, `current_plan`, `current_results`, and `iteration_count`.
- **Outputs** - Returns a JSON object with assessment, step reviews, guidance, and a `verdict` ("Continue" or "Stop").

## SynthesizerAgent
- **Purpose** - Synthesizes a final, comprehensive solution from all previous exploration.
- **Review** - Integrates the best insights and justifications from the full history.
- **Inputs** - Receives `main_task` and `full_history_summary`.
- **Outputs** - Returns the final answer to the main task.
