import os
import sys
import json
from typing import Optional, List, Dict, Any, Tuple, Set
from pydantic import BaseModel # Added for _log_agent_activity
import dotenv
from prompt_toolkit import PromptSession
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.keys import Keys
dotenv.load_dotenv()
from app.instructions import (
    PLANNER_INSTRUCTIONS,
    THINKER_INSTRUCTIONS,
    REVIEWER_INSTRUCTIONS,
    SYNTHESIZER_INSTRUCTIONS,
)
from app.client import Client
from app.schemas import (
    PlannerOut,
    ReviewerOut,
    NextIterationGuidance,
    ExplorationPlan,
    PlanStep,
    ContextSelection,
)
from google.genai.types import Tool, GoogleSearch


# ──────────────────────────────
# Helper Utilities
# ──────────────────────────────

class BColors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def _build_prompt_xml_style(parts: List[Tuple[str, str]]) -> str:
    """Builds a prompt string from parts, styled with XML-like tags."""
    return "\n\n".join([f"<{tag}>{content}</{tag}>" for tag, content in parts if content is not None])


def _log_agent_activity(
    agent_name: str,
    phase: str,
    content: Any,
    color: str = BColors.WARNING,
    is_json: bool = False,
    snippet_length: Optional[int] = None,
):
    """Logs agent activity with consistent formatting and colors."""
    header = f"\n{BColors.OKCYAN}[{agent_name}]{BColors.ENDC} {phase}:"
    
    if snippet_length and isinstance(content, str) and len(content) > snippet_length:
        content_to_log = content[:snippet_length] + "..."
    else:
        content_to_log = content

    if is_json:
        # Handle Pydantic models or lists of them
        if isinstance(content_to_log, list) and all(isinstance(item, BaseModel) for item in content_to_log):
            log_content = json.dumps([item.model_dump(exclude_none=True) for item in content_to_log], indent=2)
        elif isinstance(content_to_log, BaseModel):
            log_content = json.dumps(content_to_log.model_dump(exclude_none=True), indent=2)
        else: # Fallback for other types if is_json is true
            log_content = json.dumps(content_to_log, indent=2)
    elif isinstance(content_to_log, str):
        log_content = content_to_log
    else: # For non-string, non-JSON content, convert to string
        log_content = str(content_to_log)
        
    print(f"{header}\n{color}{log_content}{BColors.ENDC}")

# ──────────────────────────────
# Agent Classes
# ──────────────────────────────

class PlannerAgent:
    def __init__(self, client, model):
        self.client = client
        self.model = model
        self.INSTRUCTIONS = PLANNER_INSTRUCTIONS

    def generate_plan(
        self,
        parent_task: str,
        previous_review_guidance_details_str: Optional[str] = None,
    ) -> List[ExplorationPlan]:
        prompt_parts_tuples: List[Tuple[str, str]] = [("parent_task", parent_task)]
        if previous_review_guidance_details_str:
            prompt_parts_tuples.append(
                ("previous_review_guidance_details", previous_review_guidance_details_str)
            )
        user_prompt = _build_prompt_xml_style(prompt_parts_tuples)

        _log_agent_activity("PlannerAgent", "Instructions (snippet)", self.INSTRUCTIONS, color=BColors.OKCYAN, snippet_length=500)
        _log_agent_activity("PlannerAgent", "User Prompt", user_prompt)

        try:
            response: PlannerOut = self.client.planner_call(
                self.model,
                self.INSTRUCTIONS,
                user_prompt,
                schema=PlannerOut,
            )
            _log_agent_activity("PlannerAgent", "Generating Exploration Plan...", "", color=BColors.OKCYAN)
            if response and response.exploration_plans:
                _log_agent_activity("PlannerAgent", "Generated Plans", response.exploration_plans, color=BColors.OKGREEN, is_json=True)
                return response.exploration_plans
            else:
                _log_agent_activity("PlannerAgent", "Warning: Planner returned no exploration plans or an invalid response.", "", color=BColors.FAIL)
                return []
        except Exception as e:
            _log_agent_activity("PlannerAgent", f"Error: {e}. Returning empty plan.", "", color=BColors.FAIL)
            return []


class ThinkerAgent:
    def __init__(self, client, model):
        self.client = client
        self.model = model
        self.INSTRUCTIONS = THINKER_INSTRUCTIONS

    def think(
        self,
        your_task_description: str,
        parent_task_context: Optional[str] = None,
        dependency_outputs_context: Optional[str] = None,
    ) -> str:
        prompt_parts = []
        if parent_task_context:
            prompt_parts.append(f"<parent_task_context>{parent_task_context}</parent_task_context>")
        if dependency_outputs_context:
            prompt_parts.append(dependency_outputs_context)
        prompt_parts.append(f"<your_task_description>{your_task_description}</your_task_description>")
        user_prompt = "\n\n".join(prompt_parts)

        tools_to_use = [Tool(google_search=GoogleSearch())]

        _log_agent_activity("ThinkerAgent", "User Prompt", user_prompt)

        response = self.client.thinker_call(
            model=self.model,
            instructions=self.INSTRUCTIONS,
            user_prompt=user_prompt,
            tools=tools_to_use,
        )
        response_str = response.strip() if isinstance(response, str) else str(response)
        _log_agent_activity("ThinkerAgent", "Full Response", response_str, color=BColors.OKGREEN)
        return response_str


class ReviewerAgent:
    def __init__(self, client, model):
        self.client = client
        self.model = model
        self.INSTRUCTIONS = REVIEWER_INSTRUCTIONS

    def review(
        self,
        parent_task: str,
        plans_with_responses: List[ExplorationPlan],
        current_iteration: int,
        iterations_since_last_significant_progress: int,
        STAGNATION_THRESHOLD: int,
    ) -> ReviewerOut:
        plans_json = json.dumps(
            [p.model_dump(exclude_none=True) for p in plans_with_responses], indent=2
        )

        prompt_parts_tuples: List[Tuple[str, str]] = [
            ("parent_task", parent_task),
            ("current_iteration", str(current_iteration)),
            ("STAGNATION_THRESHOLD", str(STAGNATION_THRESHOLD)),
            ("iterations_since_last_significant_progress", str(iterations_since_last_significant_progress)),
            ("plans_with_responses", plans_json),
        ]
        user_prompt = _build_prompt_xml_style(prompt_parts_tuples)

        _log_agent_activity("ReviewerAgent", "Instructions (snippet)", self.INSTRUCTIONS, color=BColors.OKCYAN, snippet_length=500)
        _log_agent_activity("ReviewerAgent", "User Prompt", user_prompt)
        
        try:
            response: ReviewerOut = self.client.reviewer_call(
                self.model,
                self.INSTRUCTIONS,
                user_prompt,
                schema=ReviewerOut,
            )
            _log_agent_activity("ReviewerAgent", "Evaluating progress...", "", color=BColors.OKCYAN)
            if not isinstance(response, ReviewerOut):
                # This error is critical and should be raised to be caught by the outer try-except
                raise ValueError(
                    f"Reviewer did not return a valid ReviewerOut object. Got: {type(response)}"
                )

            _log_agent_activity("ReviewerAgent", "Reviewer Output", response, color=BColors.OKGREEN, is_json=True)
            return response
        except Exception as e:
            _log_agent_activity("ReviewerAgent", f"Error: {e}. Defaulting to HALT_NO_FEASIBLE_PATH.", "", color=BColors.FAIL)
            default_guidance = NextIterationGuidance(
                action="HALT_NO_FEASIBLE_PATH",
                reasoning=f"Error during review processing: {type(e).__name__} - {str(e)}",
            )
            return ReviewerOut(
                assessment_of_current_iteration="ERROR_IN_REVIEW_PROCESSING",
                is_sufficient_for_synthesis=False,
                context_to_use=None,
                next_iteration_guidance=default_guidance,
            )


class SynthesizerAgent:
    def __init__(self, client, model):
        self.client = client
        self.model = model
        self.INSTRUCTIONS = SYNTHESIZER_INSTRUCTIONS

    def _build_full_history_summary(self, full_history: List[Dict[str, Any]]) -> Tuple[str, Optional[List[ContextSelection]]]:
        history_summary_parts = []
        final_context_to_use: Optional[List[ContextSelection]] = None

        for i, cycle in enumerate(full_history):
            cycle_summary = f"--- Iteration {i+1} ---\n"
            plans_with_responses_obj: List[ExplorationPlan] = cycle.get('plans_with_responses', [])
            plans_data_for_json = [p.model_dump(exclude_none=True) for p in plans_with_responses_obj]
            cycle_summary += f"Plans & Responses: {json.dumps(plans_data_for_json, indent=1)}\n"

            review_obj: Optional[ReviewerOut] = cycle.get('review')
            if review_obj:
                cycle_summary += f"Review Assessment for this Iteration: {review_obj.assessment_of_current_iteration}\n"
                if review_obj.next_iteration_guidance:
                    cycle_summary += f"Reviewer Guidance Action for Next Iteration: {review_obj.next_iteration_guidance.action}\n"
                    cycle_summary += f"Reviewer Reasoning: {review_obj.next_iteration_guidance.reasoning}\n"
                if i == len(full_history) - 1: # Capture context from the very last review
                    final_context_to_use = review_obj.context_to_use
            else:
                cycle_summary += "Review: N/A\n"
            history_summary_parts.append(cycle_summary)
        
        return "\n".join(history_summary_parts), final_context_to_use

    def _build_selected_responses_segment(
        self, 
        final_context_to_use: Optional[List[ContextSelection]], 
        full_history: List[Dict[str, Any]]
    ) -> Optional[str]:
        if not final_context_to_use:
            return None

        all_step_responses: Dict[str, str] = {}
        for cycle_data in full_history: # Re-iterate to build a complete map of all step responses
            plans_obj_list: List[ExplorationPlan] = cycle_data.get('plans_with_responses', [])
            for plan_obj in plans_obj_list:
                for step_obj in plan_obj.steps:
                    key = f"{plan_obj.plan_id}.{step_obj.step_id}"
                    all_step_responses[key] = step_obj.response or "N/A"
        
        selected_responses_parts = ["<selected_step_responses>"]
        for selection_group in final_context_to_use:
            plan_id = selection_group.plan_id
            for step_id in selection_group.step_ids:
                q_step_id = f"{plan_id}.{step_id}"
                response_text = all_step_responses.get(q_step_id, "Response not found for this step in history.")
                selected_responses_parts.append(
                    f'<step_response plan_id="{plan_id}" step_id="{step_id}">\n{response_text}\n</step_response>'
                )
        selected_responses_parts.append("</selected_step_responses>")
        
        return "\n".join(selected_responses_parts) if len(selected_responses_parts) > 2 else None

    def synthesize(
        self, parent_task: str, full_history: List[Dict[str, Any]]
    ) -> str:
        full_history_summary_for_prompt, final_context_to_use = self._build_full_history_summary(full_history)
        
        prompt_parts_tuples: List[Tuple[str, str]] = [
            ("parent_task", parent_task),
            ("full_history_summary", f"\n{full_history_summary_for_prompt}\n"),
        ]

        selected_responses_segment = self._build_selected_responses_segment(final_context_to_use, full_history)
        if selected_responses_segment:
            # We don't use _build_prompt_xml_style here because selected_responses_segment is already XML-formatted
            # and _build_prompt_xml_style would wrap it in another tag.
            # Instead, we append it directly to a list that will be joined.
            user_prompt_parts_list = [
                _build_prompt_xml_style(prompt_parts_tuples),
                selected_responses_segment
            ]
            user_prompt = "\n\n".join(user_prompt_parts_list)
        else:
            user_prompt = _build_prompt_xml_style(prompt_parts_tuples)


        _log_agent_activity("SynthesizerAgent", "Instructions (snippet)", self.INSTRUCTIONS, color=BColors.OKCYAN, snippet_length=500)
        _log_agent_activity("SynthesizerAgent", "User Prompt", user_prompt)

        response = self.client.synthesizer_call(
            self.model,
            self.INSTRUCTIONS,
            user_prompt,
        )
        _log_agent_activity("SynthesizerAgent", "Generating Final Solution...", "", color=BColors.OKCYAN)
        response_str = response.strip() if isinstance(response, str) else str(response)
        _log_agent_activity("SynthesizerAgent", "Final Solution", response_str, color=BColors.OKGREEN)
        return response_str


class DeepThinkingPipeline:
    MAX_ITERATIONS = 7
    STAGNATION_THRESHOLD = 2

    def __init__(
        self,
        api_key: str,
        max_iterations: Optional[int] = None,
        stagnation_threshold: Optional[int] = None,
    ):
        self.client = Client(api_key=api_key)
        model = "gemini-2.5-flash-preview-05-20"
        #model = "gemini-2.5-pro-preview-05-06"
        self.planner = PlannerAgent(self.client, model)
        self.thinker = ThinkerAgent(self.client, model)
        self.reviewer = ReviewerAgent(self.client, model)
        self.synthesizer = SynthesizerAgent(self.client, model)

        if max_iterations is not None:
            self.MAX_ITERATIONS = max_iterations
        if stagnation_threshold is not None:
            self.STAGNATION_THRESHOLD = stagnation_threshold

    def _get_step_details_from_history(
        self, plan_id: str, step_id: str, full_history: List[Dict[str, Any]]
    ) -> Dict[str, Optional[str]]:
        details = {"original_instruction": None, "previous_output": None}
        if not full_history:
            return details
        # Iterate in reverse to find the most recent execution of the step
        for hist_item in reversed(full_history):
            plans_with_responses: List[ExplorationPlan] = hist_item.get('plans_with_responses', [])
            for p_hist in plans_with_responses:
                if p_hist.plan_id == plan_id:
                    for s_hist in p_hist.steps:
                        if s_hist.step_id == step_id:
                            details["original_instruction"] = s_hist.instructions
                            details["previous_output"] = s_hist.response or "No response recorded."
                            return details # Found the most recent, return
        return details

    def _prepare_planner_guidance_prompt(
        self,
        previous_review_guidance: Optional[NextIterationGuidance],
        full_history: List[Dict[str, Any]],
    ) -> Optional[str]:
        if not previous_review_guidance:
            return None

        action = previous_review_guidance.action
        guidance_text_parts = [
            f"The Reviewer has provided guidance for this iteration (action: {action}).",
            f"Reviewer's reasoning: {previous_review_guidance.reasoning}",
        ]

        if action in ["DEEPEN", "CONTINUE_DFS_PATH", "RETRY_STEP_WITH_MODIFICATION"]:
            if previous_review_guidance.target_plan_id and previous_review_guidance.target_step_id:
                guidance_text_parts.extend([
                    f"Target Plan ID: {previous_review_guidance.target_plan_id}",
                    f"Target Step ID: {previous_review_guidance.target_step_id}",
                ])
                step_details = self._get_step_details_from_history(
                    previous_review_guidance.target_plan_id,
                    previous_review_guidance.target_step_id,
                    full_history,
                )
                if action in ["DEEPEN", "CONTINUE_DFS_PATH"]:
                    guidance_text_parts.append(f"Previous output of target step: {step_details['previous_output'] or 'Not available'}")
                elif action == "RETRY_STEP_WITH_MODIFICATION":
                    guidance_text_parts.extend([
                        f"Original instruction of target step: {step_details['original_instruction'] or 'Not available'}",
                        f"Previous output of target step: {step_details['previous_output'] or 'Not available'}",
                    ])
            else:
                guidance_text_parts.append("Warning: Target plan/step ID missing for DEEPEN/CONTINUE_DFS_PATH/RETRY action.")

        if previous_review_guidance.suggested_modifications_or_focus:
            guidance_text_parts.append(f"Suggested modifications or focus: {previous_review_guidance.suggested_modifications_or_focus}")
        if action == "BROADEN":
            if previous_review_guidance.excluded_strategies:
                guidance_text_parts.append(f"Excluded strategies: {', '.join(previous_review_guidance.excluded_strategies)}")
            if previous_review_guidance.new_strategy_suggestion:
                guidance_text_parts.append(f"New strategy suggestion: {previous_review_guidance.new_strategy_suggestion}")
        if action == "CONTINUE_DFS_PATH" and previous_review_guidance.current_dfs_path_summary:
            guidance_text_parts.append(f"Current DFS path summary: {previous_review_guidance.current_dfs_path_summary}")
        
        return "\n".join(guidance_text_parts)

    def _execute_exploration_steps(
        self,
        exploration_plans: List[ExplorationPlan],
        parent_task: str,
    ) -> List[ExplorationPlan]: # Returns plans with responses filled in
        if not exploration_plans:
            return []

        all_steps_to_process: List[Tuple[ExplorationPlan, PlanStep]] = []
        for plan_obj in exploration_plans:
            for step_obj in plan_obj.steps:
                all_steps_to_process.append((plan_obj, step_obj))

        completed_step_outputs: Dict[str, str] = {}
        executed_step_qnames: Set[str] = set()
        # Max passes can be the number of steps if there's a perfect linear dependency chain
        max_passes = len(all_steps_to_process) 

        for pass_num in range(max_passes + 1): # +1 for a final check or in case of no steps
            executed_in_this_pass = 0
            if len(executed_step_qnames) == len(all_steps_to_process):
                break # All steps processed

            for plan_obj, step_obj in all_steps_to_process:
                step_qname = f"{plan_obj.plan_id}.{step_obj.step_id}"
                if step_qname in executed_step_qnames:
                    continue

                dependencies_met = True
                if step_obj.dependencies:
                    for dep_qname in step_obj.dependencies:
                        if dep_qname not in completed_step_outputs:
                            dependencies_met = False
                            break
                
                if dependencies_met:
                    _log_agent_activity(
                        "ThinkerAgent", 
                        f"Processing -> Plan {plan_obj.plan_id}-{step_obj.step_id}",
                        step_obj.instructions,
                        color=BColors.OKCYAN, # Using OKCYAN for processing messages
                        snippet_length=100
                    )
                    
                    dependency_outputs_context_str = ""
                    if step_obj.dependencies:
                        dep_outputs_xml_parts = ["<dependency_outputs>"]
                        for dep_qname in step_obj.dependencies:
                            p_id, s_id = dep_qname.split('.', 1)
                            dep_output_content = completed_step_outputs.get(dep_qname, "Error: Dependency output not found!")
                            dep_outputs_xml_parts.append(f'  <output plan_id="{p_id}" step_id="{s_id}">\n    {dep_output_content}\n  </output>')
                        dep_outputs_xml_parts.append("</dependency_outputs>")
                        dependency_outputs_context_str = "\n".join(dep_outputs_xml_parts)

                    step_obj.response = self.thinker.think(
                        your_task_description=step_obj.instructions,
                        parent_task_context=parent_task,
                        dependency_outputs_context=dependency_outputs_context_str
                    )
                    completed_step_outputs[step_qname] = step_obj.response or "No response recorded."
                    executed_step_qnames.add(step_qname)
                    executed_in_this_pass += 1
            
            if pass_num > 0 and executed_in_this_pass == 0 and len(executed_step_qnames) < len(all_steps_to_process):
                pending_qnames = [f"{p.plan_id}.{s.step_id}" for p, s in all_steps_to_process if f"{p.plan_id}.{s.step_id}" not in executed_step_qnames]
                _log_agent_activity("Pipeline", f"Error: Could not execute any more steps in pass {pass_num}. Possible circular dependency or unmet/invalid dependency. Pending: {pending_qnames}", "", color=BColors.FAIL)
                break
        
        if len(executed_step_qnames) < len(all_steps_to_process):
            unexecuted_count = len(all_steps_to_process) - len(executed_step_qnames)
            _log_agent_activity("Pipeline", f"Warning: Not all steps were executed. {unexecuted_count} steps remain pending.", "", color=BColors.WARNING)
        elif all_steps_to_process: # Only log success if there were steps to process
             _log_agent_activity("Pipeline", f"All {len(all_steps_to_process)} steps executed successfully or attempted.", "", color=BColors.OKGREEN)
        
        return exploration_plans # Return the original list, now with responses populated

    def run(self, parent_task: str) -> str:
        full_history: List[Dict[str, Any]] = []
        previous_review_guidance: Optional[NextIterationGuidance] = None
        current_iteration = 0
        iterations_since_last_significant_progress = 0

        while True:
            current_iteration += 1
            guidance_prompt_segment = self._prepare_planner_guidance_prompt(previous_review_guidance, full_history)
            
            current_exploration_plans: List[ExplorationPlan] = self.planner.generate_plan(parent_task, guidance_prompt_segment)

            if not current_exploration_plans:
                _log_agent_activity("Pipeline", "Planner returned no new plans.", "", color=BColors.FAIL)
                if not full_history: # Critical failure if initial planning fails
                    return f"{BColors.FAIL}Error: Planner failed to generate an initial plan and there's no history. Cannot proceed.{BColors.ENDC}"
                _log_agent_activity("Pipeline", "No new plans. Proceeding to synthesize or halt based on Reviewer.", "", color=BColors.OKCYAN)
                # If planner returns no plans, we still proceed to reviewer with empty plans for this iteration
                # The reviewer can then decide to HALT or the loop might terminate due to MAX_ITERATIONS.

            # Execute steps for the current plans
            updated_exploration_plans = self._execute_exploration_steps(current_exploration_plans, parent_task)

            review_obj: ReviewerOut = self.reviewer.review(
                parent_task,
                updated_exploration_plans, # Pass plans with responses
                current_iteration,
                iterations_since_last_significant_progress,
                self.STAGNATION_THRESHOLD,
            )

            full_history.append({
                "plans_with_responses": updated_exploration_plans, # Store plans with responses
                "review": review_obj,
            })

            next_guidance = review_obj.next_iteration_guidance
            previous_review_guidance = next_guidance # For the next loop

            _log_agent_activity("ReviewerAgent", "Assessment", review_obj.assessment_of_current_iteration, color=BColors.OKGREEN)
            _log_agent_activity("ReviewerAgent", f"Next Action: {next_guidance.action}", f"Reason: {next_guidance.reasoning}", color=BColors.BOLD)

            if review_obj.context_to_use: # "Gems" were found
                iterations_since_last_significant_progress = 0
                _log_agent_activity("Pipeline", "Significant progress detected (new gems found). Resetting stagnation counter.", "", color=BColors.OKCYAN)
            else:
                iterations_since_last_significant_progress += 1
                _log_agent_activity("Pipeline", f"No new gems. Iterations since last significant progress: {iterations_since_last_significant_progress}", "", color=BColors.OKCYAN)

            if next_guidance.action in ["HALT_SUFFICIENT", "HALT_STAGNATION", "HALT_NO_FEASIBLE_PATH"] or \
               review_obj.assessment_of_current_iteration == "ERROR_IN_REVIEW_PROCESSING":
                halt_reason = next_guidance.action if review_obj.assessment_of_current_iteration != "ERROR_IN_REVIEW_PROCESSING" else "ERROR_IN_REVIEW_PROCESSING"
                _log_agent_activity("Pipeline", f"Process will STOP based on Reviewer: '{halt_reason}' after {current_iteration} iterations.", "", color=BColors.HEADER)
                break

            if current_iteration >= self.MAX_ITERATIONS:
                _log_agent_activity("Pipeline", f"Process will STOP due to MAX_ITERATIONS ({self.MAX_ITERATIONS}) reached.", "", color=BColors.HEADER)
                break
        
        if not full_history:
             # This case should ideally be caught earlier if initial planner fails.
            return f"{BColors.FAIL}Error: No history was generated. Cannot synthesize.{BColors.ENDC}"

        _log_agent_activity("Pipeline", "Total model cost", f"${self.client.total_cost():.4f}", color=BColors.HEADER)
        return self.synthesizer.synthesize(parent_task, full_history)


def main():
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print(f"{BColors.FAIL}Error: GEMINI_API_KEY not found in environment variables.{BColors.ENDC}")
        sys.exit(1)

    # Setup key bindings for Ctrl+Enter to submit
    kb = KeyBindings()
    @kb.add(Keys.ControlJ)
    def _(event):
        event.app.exit(result=event.current_buffer.text)

    session = PromptSession(key_bindings=kb, multiline=True)
    
    print(f"{BColors.BOLD}USER > {BColors.ENDC} (Enter your main task. Press Ctrl+Enter to submit):")
    try:
        parent_task_input = session.prompt().strip()
    except EOFError: # Handle Ctrl+D or other EOF signals gracefully
        print(f"\n{BColors.WARNING}Input cancelled. Exiting.{BColors.ENDC}")
        sys.exit(0)


    if not parent_task_input:
        print(f"{BColors.FAIL}Error: No main task provided. Exiting.{BColors.ENDC}")
        sys.exit(1)

    max_iterations_override = DeepThinkingPipeline.MAX_ITERATIONS
    stagnation_threshold_override = DeepThinkingPipeline.STAGNATION_THRESHOLD

    pipeline = DeepThinkingPipeline(
        api_key=api_key,
        max_iterations=max_iterations_override,
        stagnation_threshold=stagnation_threshold_override,
    )
    pipeline.run(parent_task_input)


if __name__ == "__main__":
    main()
