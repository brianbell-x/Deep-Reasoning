# app/main.py

import os
import sys
import json
import datetime
import re
from typing import Optional, List, Dict, Any, Tuple, Set
from pydantic import BaseModel
import dotenv

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
from google.genai import types # Added for ToolCodeExecution
from google.genai.types import Tool, GoogleSearch

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

LOG_FILE_PATH: Optional[str] = None

def _strip_ansi_codes(text: str) -> str:
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    return ansi_escape.sub('', text)

def _build_prompt_xml_style(parts: List[Tuple[str, str]]) -> str:
    return "\n\n".join(
        f"<{tag}>{content}</{tag}>" for tag, content in parts if content is not None
    )

def _log_agent_activity(
    agent_name: str,
    phase: str,
    content: Any,
    color: str = BColors.WARNING,
    is_json: bool = False,
    snippet_length: Optional[int] = None,
):
    header = f"\n{BColors.OKCYAN}[{agent_name}]{BColors.ENDC} {phase}:"
    content_to_log = (
        content[:snippet_length] + "..." if snippet_length and isinstance(content, str) and len(content) > snippet_length
        else content
    )

    if is_json:
        if isinstance(content_to_log, list) and all(isinstance(item, BaseModel) for item in content_to_log):
            log_content = json.dumps([item.model_dump(exclude_none=True) for item in content_to_log], indent=2)
        elif isinstance(content_to_log, BaseModel):
            log_content = json.dumps(content_to_log.model_dump(exclude_none=True), indent=2)
        else:
            log_content = json.dumps(content_to_log, indent=2)
    elif isinstance(content_to_log, str):
        log_content = content_to_log
    else:
        log_content = str(content_to_log)

    print(f"{header}\n{color}{log_content}{BColors.ENDC}")

    global LOG_FILE_PATH
    if LOG_FILE_PATH:
        try:
            with open(LOG_FILE_PATH, "a", encoding="utf-8") as f:
                f.write(f"{_strip_ansi_codes(header)}\n{_strip_ansi_codes(log_content)}\n\n")
        except Exception as e:
            print(f"{BColors.FAIL}Error writing to log file {LOG_FILE_PATH}: {e}{BColors.ENDC}")

class PlannerAgent:
    def __init__(self, client, model):
        self.client = client
        self.model = model
        self.INSTRUCTIONS = PLANNER_INSTRUCTIONS

    def generate_plan(
        self,
        parent_task: str,
        review_guidance_str: Optional[str] = None,
    ) -> List[ExplorationPlan]:
        """
        Generates exploration plans based on the parent task and optional previous review guidance.

        The user_prompt is constructed in an XML-like format:

        ```
        <parent_task>The main goal or problem to be solved.</parent_task>

        <review_guidance>
        Guidance from the ReviewerAgent from the previous iteration.
        This can include:
        - Reviewer's reasoning for the guidance.
        - Target plan/step IDs for actions like DEEPEN, RETRY.
        - Previous output of a target step.
        - Original instruction of a target step.
        - Suggested modifications or focus.
        - Excluded strategies or new strategy suggestions for BROADEN.
        - Current DFS path summary for CONTINUE_DFS_PATH.
        </review_guidance>

        Note: The <review_guidance> tag and its content are only included
        if `review_guidance_str` is provided.
        ```
        """
        prompt_parts = [("parent_task", parent_task)]
        if review_guidance_str:
            prompt_parts.append(("review_guidance", review_guidance_str))
        user_prompt = _build_prompt_xml_style(prompt_parts)

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
        step_instructions: str,
        dependency_outputs_context: Optional[str] = None,
        overall_parent_task_context: Optional[str] = None,
    ) -> str:
        """
        Executes a specific task (a step in an exploration plan) using available tools.
        The ThinkerAgent's understanding comes from `step_instructions`,
        any `dependency_outputs_context`, and the `overall_parent_task_context` (if available).

        The user_prompt is constructed by concatenating XML-like segments:
        ```
        <overall_parent_task>
        The overall parent task for the entire job, if one exists.
        </overall_parent_task>

        <dependency_outputs>
          <output plan_id="PLAN_ID_OF_DEPENDENCY_1" step_id="STEP_ID_OF_DEPENDENCY_1">
            Output content from the first dependency step.
          </output>
          ...
        </dependency_outputs>

        <step_instructions>
        Specific instructions for the current step/task this ThinkerAgent instance needs to perform.
        </step_instructions>

        Notes:
        - <overall_parent_task> is included if `overall_parent_task_context` is provided.
        - <dependency_outputs> and its content are included if `dependency_outputs_context` is provided.
          This context itself is pre-formatted as an XML string.
        - <step_instructions> is always included.
        - The segments are joined by double newlines.
        ```
        """
        prompt_elements = []
        if overall_parent_task_context:
            prompt_elements.append(f"<overall_parent_task>{overall_parent_task_context}</overall_parent_task>")
        if dependency_outputs_context:
            # Assuming dependency_outputs_context is already a well-formed XML string
            prompt_elements.append(dependency_outputs_context)
        prompt_elements.append(f"<step_instructions>{step_instructions}</step_instructions>")
        
        user_prompt = "\n\n".join(prompt_elements)

        tools_to_use = [
            Tool(google_search=GoogleSearch()),
            types.Tool(code_execution=types.ToolCodeExecution()) # Added Code Execution
        ]

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
        iterations_no_progress: int,
        STAGNATION_THRESHOLD: int,
    ) -> ReviewerOut:
        """
        Reviews the outcomes of the current iteration's exploration plans and provides guidance.

        The user_prompt is constructed in an XML-like format:

        ```
        <parent_task>The main goal or problem to be solved.</parent_task>

        <current_iteration>Integer representing the current cycle number (e.g., 1, 2, 3...).</current_iteration>

        <STAGNATION_THRESHOLD>
        Integer threshold for determining stagnation (e.g., 2 or 3 iterations without progress).
        </STAGNATION_THRESHOLD>

        <iterations_no_progress>
        Integer count of iterations since the last time significant progress (new context gems) was made.
        </iterations_no_progress>

        <plans_with_responses>
        A JSON string representing a list of ExplorationPlan objects, including their steps and responses.
        Example structure:
        [
          {
            "plan_id": "alpha",
            "plan_description": "Initial approach to solve X.",
            "steps": [
              {
                "step_id": "1",
                "instructions": "Research topic A.",
                "dependencies": null, // or ["plan_id.step_id", ...]
                "response": "Findings about topic A..."
              },
              {
                "step_id": "2",
                "instructions": "Analyze results from step 1.",
                "dependencies": ["alpha.1"],
                "response": "Analysis of findings..."
              }
            ]
          },
          // ... more plans
        ]
        </plans_with_responses>
        ```
        """
        plans_json = json.dumps(
            [p.model_dump(exclude_none=True) for p in plans_with_responses], indent=2
        )

        prompt_parts = [
            ("parent_task", parent_task),
            ("current_iteration", str(current_iteration)),
            ("STAGNATION_THRESHOLD", str(STAGNATION_THRESHOLD)),
            ("iterations_no_progress", str(iterations_no_progress)),
            ("plans_with_responses", plans_json),
        ]
        user_prompt = _build_prompt_xml_style(prompt_parts)

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
                iteration_assessment="ERROR_IN_REVIEW_PROCESSING",
                synthesis_ready=False,
                selected_context=None,
                next_iteration_guidance=default_guidance,
            )

class SynthesizerAgent:
    def __init__(self, client, model):
        self.client = client
        self.model = model
        self.INSTRUCTIONS = SYNTHESIZER_INSTRUCTIONS

    def synthesize(
        self, parent_task: str, full_history: List[Dict[str, Any]]
    ) -> str:
        """
        Synthesizes the final solution based on the parent task and the full history of exploration.

        The user_prompt is constructed by concatenating XML-like segments:

        ```
        <parent_task>The main goal or problem to be solved.</parent_task>

        <process_history>
        --- Iteration 1 ---
        Plans & Responses: [JSON representation of ExplorationPlan objects for iteration 1]
        Review Assessment for this Iteration: Text assessment from the reviewer.
        Reviewer Guidance Action for Next Iteration: e.g., CONTINUE_DFS_PATH, BROADEN, HALT_SUFFICIENT
        Reviewer Reasoning: Text reasoning from the reviewer.
        --- Iteration 2 ---
        Plans & Responses: [JSON representation of ExplorationPlan objects for iteration 2]
        Review Assessment for this Iteration: ...
        ... and so on for all iterations.
        </process_history>

        <selected_step_responses>
        <step_response plan_id="PLAN_ID_1" step_id="STEP_ID_A">
        Content of the response from plan PLAN_ID_1, step STEP_ID_A, selected by the Reviewer.
        </step_response>
        <step_response plan_id="PLAN_ID_2" step_id="STEP_ID_B">
        Content of the response from plan PLAN_ID_2, step STEP_ID_B, selected by the Reviewer.
        </step_response>
        ...
        </selected_step_responses>

        Notes:
        - <parent_task> is always included.
        - <process_history> contains a structured text summary of each iteration,
          including plans, responses, and reviewer feedback.
        - <selected_step_responses> is included if the final review identified specific step
          responses (ContextSelection) to be used for synthesis. It contains the actual text
          of those selected responses.
        - The segments are joined by double newlines.
        ```
        """
        process_history_str, final_selected_context = self._build_process_history(full_history)
        
        prompt_parts = [
            ("parent_task", parent_task),
            ("process_history", f"\n{process_history_str}\n"),
        ]

        selected_responses_segment = self._build_selected_responses_segment(final_selected_context, full_history)
        if selected_responses_segment:
            user_prompt = "\n\n".join([
                _build_prompt_xml_style(prompt_parts),
                selected_responses_segment
            ])
        else:
            user_prompt = _build_prompt_xml_style(prompt_parts)

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

    def _build_process_history(self, full_history: List[Dict[str, Any]]) -> Tuple[str, Optional[List[ContextSelection]]]:
        history_summary_parts = []
        final_selected_context: Optional[List[ContextSelection]] = None

        for i, cycle in enumerate(full_history):
            cycle_summary = f"--- Iteration {i+1} ---\n"
            plans_with_responses_obj: List[ExplorationPlan] = cycle.get('plans_with_responses', [])
            plans_data_for_json = [p.model_dump(exclude_none=True) for p in plans_with_responses_obj]
            cycle_summary += f"Plans & Responses: {json.dumps(plans_data_for_json, indent=1)}\n"

            review_obj: Optional[ReviewerOut] = cycle.get('review')
            if review_obj:
                cycle_summary += f"Review Assessment for this Iteration: {review_obj.iteration_assessment}\n"
                if review_obj.next_iteration_guidance:
                    cycle_summary += f"Reviewer Guidance Action for Next Iteration: {review_obj.next_iteration_guidance.action}\n"
                    cycle_summary += f"Reviewer Reasoning: {review_obj.next_iteration_guidance.reasoning}\n"
                if i == len(full_history) - 1:
                    final_selected_context = review_obj.selected_context
            else:
                cycle_summary += "Review: N/A\n"
            history_summary_parts.append(cycle_summary)
        
        return "\n".join(history_summary_parts), final_selected_context

    def _build_selected_responses_segment(
        self, 
        final_selected_context: Optional[List[ContextSelection]], 
        full_history: List[Dict[str, Any]]
    ) -> Optional[str]:
        if not final_selected_context:
            return None

        all_step_responses: Dict[str, str] = {}
        for cycle_data in full_history:
            plans_obj_list: List[ExplorationPlan] = cycle_data.get('plans_with_responses', [])
            for plan_obj in plans_obj_list:
                for step_obj in plan_obj.steps:
                    key = f"{plan_obj.plan_id}.{step_obj.step_id}"
                    all_step_responses[key] = step_obj.response or "N/A"
        
        selected_responses_parts = ["<selected_step_responses>"]
        for selection_group in final_selected_context:
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
        process_history_str, final_selected_context = self._build_process_history(full_history)
        
        prompt_parts = [
            ("parent_task", parent_task),
            ("process_history", f"\n{process_history_str}\n"),
        ]

        selected_responses_segment = self._build_selected_responses_segment(final_selected_context, full_history)
        if selected_responses_segment:
            user_prompt = "\n\n".join([
                _build_prompt_xml_style(prompt_parts),
                selected_responses_segment
            ])
        else:
            user_prompt = _build_prompt_xml_style(prompt_parts)

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

class Orchestrator:
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
        for hist_item in reversed(full_history):
            plans_with_responses: List[ExplorationPlan] = hist_item.get('plans_with_responses', [])
            for p_hist in plans_with_responses:
                if p_hist.plan_id == plan_id:
                    for s_hist in p_hist.steps:
                        if s_hist.step_id == step_id:
                            details["original_instruction"] = s_hist.instructions
                            details["previous_output"] = s_hist.response or "No response recorded."
                            return details
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

        if previous_review_guidance.refinement_details:
            guidance_text_parts.append(f"Suggested modifications or focus: {previous_review_guidance.refinement_details}")
        if action == "BROADEN":
            if previous_review_guidance.excluded_strategies:
                guidance_text_parts.append(f"Excluded strategies: {', '.join(previous_review_guidance.excluded_strategies)}")
            if previous_review_guidance.suggested_strategy:
                guidance_text_parts.append(f"New strategy suggestion: {previous_review_guidance.suggested_strategy}")
        if action == "CONTINUE_DFS_PATH" and previous_review_guidance.dfs_path_summary:
            guidance_text_parts.append(f"Current DFS path summary: {previous_review_guidance.dfs_path_summary}")
        
        return "\n".join(guidance_text_parts)

    def _execute_exploration_steps(
        self,
        exploration_plans: List[ExplorationPlan],
        parent_task: str,
    ) -> List[ExplorationPlan]:
        if not exploration_plans:
            return []

        all_steps_to_process: List[Tuple[ExplorationPlan, PlanStep]] = [
            (plan_obj, step_obj)
            for plan_obj in exploration_plans
            for step_obj in plan_obj.steps
        ]

        completed_step_outputs: Dict[str, str] = {}
        executed_step_qnames: Set[str] = set()
        max_passes = len(all_steps_to_process)

        for pass_num in range(max_passes + 1):
            executed_in_this_pass = 0
            if len(executed_step_qnames) == len(all_steps_to_process):
                break

            for plan_obj, step_obj in all_steps_to_process:
                step_qname = f"{plan_obj.plan_id}.{step_obj.step_id}"
                if step_qname in executed_step_qnames:
                    continue

                dependencies_met = all(
                    dep_qname in completed_step_outputs
                    for dep_qname in (step_obj.dependencies or [])
                )

                if dependencies_met:
                    _log_agent_activity(
                        "ThinkerAgent",
                        f"Processing -> Plan {plan_obj.plan_id}-{step_obj.step_id}",
                        step_obj.instructions,
                        color=BColors.OKCYAN,
                        snippet_length=100
                    )

                    dependency_outputs_context_str = ""
                    if step_obj.dependencies:
                        dep_outputs_xml_parts = ["<dependency_outputs>"]
                        for dep_qname in step_obj.dependencies:
                            p_id, s_id = dep_qname.split('.', 1)
                            dep_output_content = completed_step_outputs.get(dep_qname, "Error: Dependency output not found!")
                            dep_outputs_xml_parts.append(
                                f'  <output plan_id="{p_id}" step_id="{s_id}">\n    {dep_output_content}\n  </output>'
                            )
                        dep_outputs_xml_parts.append("</dependency_outputs>")
                        dependency_outputs_context_str = "\n".join(dep_outputs_xml_parts)
                    
                    # Always pass the parent_task to the thinker
                    step_obj.response = self.thinker.think(
                        step_instructions=step_obj.instructions,
                        dependency_outputs_context=dependency_outputs_context_str if step_obj.dependencies else None,
                        overall_parent_task_context=parent_task
                    )
                    completed_step_outputs[step_qname] = step_obj.response or "No response recorded."
                    executed_step_qnames.add(step_qname)
                    executed_in_this_pass += 1

            if pass_num > 0 and executed_in_this_pass == 0 and len(executed_step_qnames) < len(all_steps_to_process):
                pending_qnames = [
                    f"{p.plan_id}.{s.step_id}"
                    for p, s in all_steps_to_process
                    if f"{p.plan_id}.{s.step_id}" not in executed_step_qnames
                ]
                _log_agent_activity(
                    "Pipeline",
                    f"Error: Could not execute any more steps in pass {pass_num}. Possible circular dependency or unmet/invalid dependency. Pending: {pending_qnames}",
                    "",
                    color=BColors.FAIL
                )
                break

        if len(executed_step_qnames) < len(all_steps_to_process):
            unexecuted_count = len(all_steps_to_process) - len(executed_step_qnames)
            _log_agent_activity(
                "Pipeline",
                f"Warning: Not all steps were executed. {unexecuted_count} steps remain pending.",
                "",
                color=BColors.WARNING
            )
        elif all_steps_to_process:
            _log_agent_activity(
                "Pipeline",
                f"All {len(all_steps_to_process)} steps executed successfully or attempted.",
                "",
                color=BColors.OKGREEN
            )

        return exploration_plans

    def run(self, parent_task: str) -> str:
        full_history: List[Dict[str, Any]] = []
        previous_review_guidance: Optional[NextIterationGuidance] = None
        current_iteration = 0
        iterations_no_progress = 0

        while True:
            current_iteration += 1
            guidance_prompt_segment = self._prepare_planner_guidance_prompt(previous_review_guidance, full_history)
            current_exploration_plans: List[ExplorationPlan] = self.planner.generate_plan(parent_task, guidance_prompt_segment)

            if not current_exploration_plans:
                _log_agent_activity("Pipeline", "Planner returned no new plans.", "", color=BColors.FAIL)
                if not full_history:
                    return f"{BColors.FAIL}Error: Planner failed to generate an initial plan and there's no history. Cannot proceed.{BColors.ENDC}"
                _log_agent_activity("Pipeline", "No new plans. Proceeding to synthesize or halt based on Reviewer.", "", color=BColors.OKCYAN)

            updated_exploration_plans = self._execute_exploration_steps(current_exploration_plans, parent_task)

            review_obj: ReviewerOut = self.reviewer.review(
                parent_task,
                updated_exploration_plans,
                current_iteration,
                iterations_no_progress,
                self.STAGNATION_THRESHOLD,
            )

            full_history.append({
                "plans_with_responses": updated_exploration_plans,
                "review": review_obj,
            })

            next_guidance = review_obj.next_iteration_guidance
            previous_review_guidance = next_guidance

            _log_agent_activity("ReviewerAgent", "Assessment", review_obj.iteration_assessment, color=BColors.OKGREEN)
            _log_agent_activity("ReviewerAgent", f"Next Action: {next_guidance.action}", f"Reason: {next_guidance.reasoning}", color=BColors.BOLD)

            if review_obj.selected_context:
                iterations_no_progress = 0
                _log_agent_activity("Pipeline", "Significant progress detected (new gems found). Resetting stagnation counter.", "", color=BColors.OKCYAN)
            else:
                iterations_no_progress += 1
                _log_agent_activity("Pipeline", f"No new gems. Iterations since last significant progress: {iterations_no_progress}", "", color=BColors.OKCYAN)

            if next_guidance.action in ["HALT_SUFFICIENT", "HALT_STAGNATION", "HALT_NO_FEASIBLE_PATH"] or \
               review_obj.iteration_assessment == "ERROR_IN_REVIEW_PROCESSING":
                halt_reason = next_guidance.action if review_obj.iteration_assessment != "ERROR_IN_REVIEW_PROCESSING" else "ERROR_IN_REVIEW_PROCESSING"
                _log_agent_activity("Pipeline", f"Process will STOP based on Reviewer: '{halt_reason}' after {current_iteration} iterations.", "", color=BColors.HEADER)
                break

            if current_iteration >= self.MAX_ITERATIONS:
                _log_agent_activity("Pipeline", f"Process will STOP due to MAX_ITERATIONS ({self.MAX_ITERATIONS}) reached.", "", color=BColors.HEADER)
                break

        if not full_history:
            return f"{BColors.FAIL}Error: No history was generated. Cannot synthesize.{BColors.ENDC}"

        return self.synthesizer.synthesize(parent_task, full_history)

def main():
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print(f"{BColors.FAIL}Error: GEMINI_API_KEY not found in environment variables.{BColors.ENDC}")
        sys.exit(1)

    global LOG_FILE_PATH
    log_dir = "app/log"
    os.makedirs(log_dir, exist_ok=True)
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    LOG_FILE_PATH = os.path.join(log_dir, f"run_{timestamp}.log")
    print(f"{BColors.OKBLUE}Logging to: {LOG_FILE_PATH}{BColors.ENDC}")

    parent_task_input = input(f"{BColors.BOLD}USER > {BColors.ENDC}").strip()
    if not parent_task_input:
        error_message = f"{BColors.FAIL}Error: No main task provided. Exiting.{BColors.ENDC}"
        print(error_message)
        if LOG_FILE_PATH:
            try:
                with open(LOG_FILE_PATH, "a", encoding="utf-8") as f:
                    f.write(_strip_ansi_codes(error_message) + "\n")
            except Exception as e:
                print(f"{BColors.FAIL}Error writing critical exit error to log: {e}{BColors.ENDC}")
        sys.exit(1)

    pipeline = Orchestrator(
        api_key=api_key,
        max_iterations=Orchestrator.MAX_ITERATIONS,
        stagnation_threshold=Orchestrator.STAGNATION_THRESHOLD,
    )
    pipeline.run(parent_task_input)

if __name__ == "__main__":
    main()
