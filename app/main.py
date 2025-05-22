import os
import sys
import json
from typing import Optional, List, Dict, Any, Tuple, Set
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
        prompt_parts = [f"<parent_task>{parent_task}</parent_task>"]
        if previous_review_guidance_details_str:
            prompt_parts.append(
                f"<previous_review_guidance_details>{previous_review_guidance_details_str}</previous_review_guidance_details>"
            )
        user_prompt = "\n\n".join(prompt_parts)

        print(
            f"\n{BColors.OKCYAN}[PlannerAgent]{BColors.ENDC} Instructions (snippet):\n"
            f"{self.INSTRUCTIONS[:500]}...\n"
        )
        print(
            f"{BColors.OKCYAN}[PlannerAgent]{BColors.ENDC} User Prompt:\n"
            f"{BColors.WARNING}{user_prompt}{BColors.ENDC}"
        )

        try:
            response: PlannerOut = self.client.planner_call(
                self.model,
                self.INSTRUCTIONS,
                user_prompt,
                schema=PlannerOut,
            )
            print(f"\n{BColors.OKCYAN}[PlannerAgent]{BColors.ENDC}: Generating Exploration Plan...")
            if response and response.exploration_plans:
                plans_to_print = [p.model_dump() for p in response.exploration_plans]
                print(f"{BColors.OKGREEN}{json.dumps(plans_to_print, indent=2)}{BColors.ENDC}")
                return response.exploration_plans
            else:
                print(f"{BColors.FAIL}[PlannerAgent] Warning: Planner returned no exploration plans or an invalid response.{BColors.ENDC}")
                return []
        except Exception as e:
            print(f"{BColors.FAIL}[PlannerAgent] Error: {e}. Returning empty plan.{BColors.ENDC}")
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

        print(
            f"{BColors.OKCYAN}[ThinkerAgent]{BColors.ENDC} User Prompt:\n"
            f"{BColors.WARNING}{user_prompt}{BColors.ENDC}"
        )

        response = self.client.thinker_call(
            model=self.model,
            instructions=self.INSTRUCTIONS,
            user_prompt=user_prompt,
            tools=tools_to_use,
        )
        response_str = response.strip() if isinstance(response, str) else str(response)
        print(f"{BColors.OKCYAN}[ThinkerAgent]{BColors.ENDC} Full Response:\n{BColors.OKGREEN}{response_str}{BColors.ENDC}")
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

        prompt_parts = [
            f"<parent_task>{parent_task}</parent_task>",
            f"<current_iteration>{current_iteration}</current_iteration>",
            f"<STAGNATION_THRESHOLD>{STAGNATION_THRESHOLD}</STAGNATION_THRESHOLD>",
            f"<iterations_since_last_significant_progress>{iterations_since_last_significant_progress}</iterations_since_last_significant_progress>",
            f"<plans_with_responses>{plans_json}</plans_with_responses>",
        ]
        user_prompt = "\n\n".join(prompt_parts)

        print(f"\n{BColors.OKCYAN}[ReviewerAgent]{BColors.ENDC} Instructions (snippet):\n"
              f"{self.INSTRUCTIONS[:500]}...\n"
        )
        print(
            f"{BColors.OKCYAN}[ReviewerAgent]{BColors.ENDC} User Prompt:\n"
            f"{BColors.WARNING}{user_prompt}{BColors.ENDC}"
        )

        try:
            response: ReviewerOut = self.client.reviewer_call(
                self.model,
                self.INSTRUCTIONS,
                user_prompt,
                schema=ReviewerOut,
            )
            print(f"\n{BColors.OKCYAN}[ReviewerAgent]{BColors.ENDC}: Evaluating progress...")
            if not isinstance(response, ReviewerOut):
                raise ValueError(
                    f"Reviewer did not return a valid ReviewerOut object. Got: {type(response)}"
                )

            dumped_response = response.model_dump(exclude_none=True)
            print(f"{BColors.OKGREEN}{json.dumps(dumped_response, indent=2)}{BColors.ENDC}")
            return response
        except Exception as e:
            print(f"{BColors.FAIL}[ReviewerAgent] Error: {e}. Defaulting to HALT_NO_FEASIBLE_PATH.{BColors.ENDC}")
            default_guidance = NextIterationGuidance(
                action="HALT_NO_FEASIBLE_PATH",
                reasoning=f"Error during review processing: {str(e)}",
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

    def synthesize(
        self, parent_task: str, full_history: List[Dict[str, Any]]
    ) -> str:
        history_summary_parts = []
        final_context_to_use: Optional[List[ContextSelection]] = None

        for i, cycle in enumerate(full_history):
            cycle_summary = f"--- Iteration {i+1} ---\n"

            plans_with_responses_obj: List[ExplorationPlan] = cycle.get('plans_with_responses', [])
            plans_data_for_json = [p.model_dump(exclude_none=True) for p in plans_with_responses_obj]
            plans_json = json.dumps(plans_data_for_json, indent=1)
            cycle_summary += f"Plans & Responses: {plans_json}\n"

            review_obj: Optional[ReviewerOut] = cycle.get('review')
            if review_obj:
                cycle_summary += f"Review Assessment for this Iteration: {review_obj.assessment_of_current_iteration}\n"
                if review_obj.next_iteration_guidance:
                    cycle_summary += f"Reviewer Guidance Action for Next Iteration: {review_obj.next_iteration_guidance.action}\n"
                    cycle_summary += f"Reviewer Reasoning: {review_obj.next_iteration_guidance.reasoning}\n"
                if i == len(full_history) - 1:
                    final_context_to_use = review_obj.context_to_use
            else:
                cycle_summary += "Review: N/A\n"

            history_summary_parts.append(cycle_summary)

        full_history_summary_for_prompt = "\n".join(history_summary_parts)

        prompt_parts = [
            f"<parent_task>{parent_task}</parent_task>",
            f"<full_history_summary>\n{full_history_summary_for_prompt}\n</full_history_summary>",
        ]

        if final_context_to_use:
            selected_responses_parts = ["<selected_step_responses>"]
            all_step_responses: Dict[str, str] = {}
            for cycle_data in full_history:
                plans_obj_list: List[ExplorationPlan] = cycle_data.get('plans_with_responses', [])
                for plan_obj in plans_obj_list:
                    for step_obj in plan_obj.steps:
                        key = f"{plan_obj.plan_id}.{step_obj.step_id}"
                        all_step_responses[key] = step_obj.response or "N/A"

            for selection_group in final_context_to_use:
                plan_id = selection_group.plan_id
                for step_id in selection_group.step_ids:
                    q_step_id = f"{plan_id}.{step_id}"
                    response_text = all_step_responses.get(
                        q_step_id,
                        "Response not found for this step in history.",
                    )
                    selected_responses_parts.append(
                        f'<step_response plan_id="{plan_id}" step_id="{step_id}">\n{response_text}\n</step_response>'
                    )

            selected_responses_parts.append("</selected_step_responses>")
            if len(selected_responses_parts) > 2:
                prompt_parts.append("\n".join(selected_responses_parts))

        user_prompt = "\n\n".join(prompt_parts)

        print(f"\n{BColors.OKCYAN}[SynthesizerAgent]{BColors.ENDC} Instructions (snippet):\n"
              f"{self.INSTRUCTIONS[:500]}...\n"
        )
        print(
            f"{BColors.OKCYAN}[SynthesizerAgent]{BColors.ENDC} User Prompt:\n"
            f"{BColors.WARNING}{user_prompt}{BColors.ENDC}"
        )

        response = self.client.synthesizer_call(
            self.model,
            self.INSTRUCTIONS,
            user_prompt,
        )
        print(f"\n{BColors.OKCYAN}[SynthesizerAgent]{BColors.ENDC}: Generating Final Solution...")
        print(f"{BColors.OKGREEN}{response.strip()}{BColors.ENDC}")
        return response.strip()


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
        #model = "gemini-2.5-flash-preview-05-20"
        model = "gemini-2.5-pro-preview-05-06"
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

    def run(self, parent_task: str) -> str:
        full_history: List[Dict[str, Any]] = []
        previous_review_guidance: Optional[NextIterationGuidance] = None
        current_iteration = 0
        iterations_since_last_significant_progress = 0

        while True:
            current_iteration += 1
            guidance_prompt_segment: Optional[str] = None
            if previous_review_guidance:
                action = previous_review_guidance.action
                guidance_text_parts = [
                    f"The Reviewer has provided guidance for this iteration (action: {action}).",
                    f"Reviewer's reasoning: {previous_review_guidance.reasoning}",
                ]

                if action in ["DEEPEN", "CONTINUE_DFS_PATH", "RETRY_STEP_WITH_MODIFICATION"]:
                    if previous_review_guidance.target_plan_id and previous_review_guidance.target_step_id:
                        guidance_text_parts.append(f"Target Plan ID: {previous_review_guidance.target_plan_id}")
                        guidance_text_parts.append(f"Target Step ID: {previous_review_guidance.target_step_id}")

                        step_details = self._get_step_details_from_history(
                            previous_review_guidance.target_plan_id,
                            previous_review_guidance.target_step_id,
                            full_history,
                        )

                        if action in ["DEEPEN", "CONTINUE_DFS_PATH"]:
                            guidance_text_parts.append(
                                f"Previous output of target step: {step_details['previous_output'] or 'Not available'}"
                            )
                        elif action == "RETRY_STEP_WITH_MODIFICATION":
                            guidance_text_parts.append(
                                f"Original instruction of target step: {step_details['original_instruction'] or 'Not available'}"
                            )
                            guidance_text_parts.append(
                                f"Previous output of target step: {step_details['previous_output'] or 'Not available'}"
                            )
                    else:
                        guidance_text_parts.append(
                            "Warning: Target plan/step ID missing for DEEPEN/CONTINUE_DFS_PATH/RETRY action."
                        )

                if previous_review_guidance.suggested_modifications_or_focus:
                    guidance_text_parts.append(
                        f"Suggested modifications or focus: {previous_review_guidance.suggested_modifications_or_focus}"
                    )
                if action == "BROADEN":
                    if previous_review_guidance.excluded_strategies:
                        guidance_text_parts.append(
                            f"Excluded strategies: {', '.join(previous_review_guidance.excluded_strategies)}"
                        )
                    if previous_review_guidance.new_strategy_suggestion:
                        guidance_text_parts.append(
                            f"New strategy suggestion: {previous_review_guidance.new_strategy_suggestion}"
                        )
                if action == "CONTINUE_DFS_PATH" and previous_review_guidance.current_dfs_path_summary:
                    guidance_text_parts.append(
                        f"Current DFS path summary: {previous_review_guidance.current_dfs_path_summary}"
                    )
                guidance_prompt_segment = "\n".join(guidance_text_parts)

            exploration_plans: List[ExplorationPlan] = self.planner.generate_plan(parent_task, guidance_prompt_segment)

            if not exploration_plans:
                print(f"{BColors.FAIL}[Pipeline] Planner returned no new plans.{BColors.ENDC}")
                if not full_history:
                    return (
                        f"{BColors.FAIL}Error: Planner failed to generate an initial plan and there's no history. Cannot proceed.{BColors.ENDC}"
                    )
                print(
                    f"{BColors.OKCYAN}[Pipeline]{BColors.ENDC} No new plans generated by Planner. Proceeding to synthesize with available history or halt based on Reviewer."
                )

            all_steps_to_process: List[Tuple[ExplorationPlan, PlanStep]] = []
            for plan_obj in exploration_plans:
                for step_obj in plan_obj.steps:
                    all_steps_to_process.append((plan_obj, step_obj))

            completed_step_outputs: Dict[str, str] = {}
            executed_step_qnames: Set[str] = set()
            max_passes = len(all_steps_to_process) + 1

            for pass_num in range(max_passes):
                executed_in_this_pass = 0

                if len(executed_step_qnames) == len(all_steps_to_process):
                    break

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
                        display_instr = step_obj.instructions[:100] + "..." if len(step_obj.instructions) > 100 else step_obj.instructions
                        print(f"\n{BColors.OKCYAN}[ThinkerAgent]{BColors.ENDC}: Processing -> Plan {plan_obj.plan_id}-{step_obj.step_id}: \"{display_instr}\"")

                        dependency_outputs_context_str = ""
                        if step_obj.dependencies:
                            dep_outputs_xml_parts = ["<dependency_outputs>"]
                            for dep_qname in step_obj.dependencies:
                                p_id, s_id = dep_qname.split('.', 1)
                                dep_output_content = completed_step_outputs.get(dep_qname, "Error: Dependency output not found!")
                                dep_outputs_xml_parts.append(
                                    f'  <output plan_id="{p_id}" step_id="{s_id}">\n'
                                    f"    {dep_output_content}\n"
                                    f'  </output>'
                                )
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

                if executed_in_this_pass == 0 and len(executed_step_qnames) < len(all_steps_to_process):
                    pending_qnames = [f"{p.plan_id}.{s.step_id}" for p, s in all_steps_to_process if f"{p.plan_id}.{s.step_id}" not in executed_step_qnames]
                    print(f"{BColors.FAIL}[Pipeline] Error: Could not execute any more steps in pass {pass_num + 1}. Possible circular dependency or unmet/invalid dependency. Pending: {pending_qnames}{BColors.ENDC}")
                    break

            if len(executed_step_qnames) < len(all_steps_to_process):
                unexecuted_count = len(all_steps_to_process) - len(executed_step_qnames)
                print(f"{BColors.WARNING}[Pipeline] Warning: Not all steps were executed. {unexecuted_count} steps remain pending due to unmet dependencies or errors.{BColors.ENDC}")
            else:
                if all_steps_to_process:
                    print(f"{BColors.OKGREEN}[Pipeline] All {len(all_steps_to_process)} steps executed successfully or attempted.{BColors.ENDC}")

            review_obj: ReviewerOut = self.reviewer.review(
                parent_task,
                exploration_plans,
                current_iteration,
                iterations_since_last_significant_progress,
                self.STAGNATION_THRESHOLD,
            )

            full_history.append(
                {
                    "plans_with_responses": exploration_plans,
                    "review": review_obj,
                }
            )

            next_guidance = review_obj.next_iteration_guidance
            previous_review_guidance = next_guidance

            print(
                f"{BColors.OKCYAN}[ReviewerAgent]{BColors.ENDC} Assessment: {BColors.OKGREEN}{review_obj.assessment_of_current_iteration}{BColors.ENDC}"
            )
            print(
                f"{BColors.OKCYAN}[ReviewerAgent]{BColors.ENDC} Next Action: {BColors.BOLD}{next_guidance.action}{BColors.ENDC}, Reason: {next_guidance.reasoning}"
            )

            if review_obj.context_to_use:
                iterations_since_last_significant_progress = 0
                print(
                    f"{BColors.OKCYAN}[Pipeline]{BColors.ENDC} Significant progress detected (new gems found). Resetting stagnation counter."
                )
            else:
                iterations_since_last_significant_progress += 1
                print(
                    f"{BColors.OKCYAN}[Pipeline]{BColors.ENDC} No new gems in this iteration. Iterations since last significant progress: {iterations_since_last_significant_progress}"
                )

            if (
                next_guidance.action
                in ["HALT_SUFFICIENT", "HALT_STAGNATION", "HALT_NO_FEASIBLE_PATH"]
                or review_obj.assessment_of_current_iteration == "ERROR_IN_REVIEW_PROCESSING"
            ):
                halt_reason = (
                    next_guidance.action
                    if review_obj.assessment_of_current_iteration != "ERROR_IN_REVIEW_PROCESSING"
                    else "ERROR_IN_REVIEW_PROCESSING"
                )
                print(
                    f"\n{BColors.HEADER}--- Process will STOP based on Reviewer's guidance: '{halt_reason}' after {current_iteration} iterations. ---{BColors.ENDC}"
                )
                break

            if current_iteration >= self.MAX_ITERATIONS:
                print(
                    f"\n{BColors.HEADER}--- Process will STOP due to reaching MAX_ITERATIONS ({self.MAX_ITERATIONS}) after {current_iteration} iterations. ---{BColors.ENDC}"
                )
                break

        if not full_history:
            return (
                f"{BColors.FAIL}Error: No history was generated (e.g., initial planner failure and no subsequent iterations). Cannot synthesize.{BColors.ENDC}"
            )

        print(
            f"\n{BColors.HEADER}--- Total model cost: ${self.client.total_cost():.4f} ---{BColors.ENDC}"
        )
        return self.synthesizer.synthesize(parent_task, full_history)


def main():
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print(f"{BColors.FAIL}Error: GEMINI_API_KEY not found in environment variables.{BColors.ENDC}")
        sys.exit(1)

    parent_task_input = input(f"{BColors.BOLD}USER (Enter your main task) > {BColors.ENDC}").strip()
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
