import os
import sys
import json
from typing import Optional
import dotenv

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

from app.instructions import (
    PLANNER_INSTRUCTIONS,
    THINKER_INSTRUCTIONS,
    REVIEWER_INSTRUCTIONS,
    SYNTHESIZER_INSTRUCTIONS,
)
from app.client import GeminiAPIClient
from app.schemas import PlannerOut, ReviewerOut
from google.genai.types import Tool, GoogleSearch

dotenv.load_dotenv()

class PlannerAgent:
    def __init__(self, client, model):
        self.client = client
        self.model = model
        self.INSTRUCTIONS = PLANNER_INSTRUCTIONS

    def generate_plan(self, parent_task, previous_review_guidance=None):
        prompt_parts = [f"<parent_task>{parent_task}</parent_task>"]
        if previous_review_guidance:
            prompt_parts.append(
                f"<previous_review_guidance>{previous_review_guidance}</previous_review_guidance>"
            )
        user_prompt = "\n".join(prompt_parts)

        print(
            f"\n{BColors.OKCYAN}[PlannerAgent]{BColors.ENDC} Instructions:\n"
            f"{BColors.OKBLUE}{self.INSTRUCTIONS}{BColors.ENDC}"
        )
        print(
            f"{BColors.OKCYAN}[PlannerAgent]{BColors.ENDC} User Prompt:\n"
            f"{BColors.WARNING}{user_prompt}{BColors.ENDC}"
        )

        try:
            response = self.client.planner_call(
                self.model,
                self.INSTRUCTIONS,
                user_prompt,
                schema=PlannerOut
            )
            print(f"\n{BColors.OKCYAN}[PlannerAgent]{BColors.ENDC}: Generating Exploration Plan...")
            plans_to_print = [p.model_dump() for p in response.exploration_plans]
            print(f"{BColors.OKGREEN}{json.dumps(plans_to_print, indent=2)}{BColors.ENDC}")
            return response.exploration_plans
        except Exception as e:
            print(f"{BColors.FAIL}[PlannerAgent] Error: {e}. Returning empty plan.{BColors.ENDC}")
            return []


class ThinkerAgent:
    def __init__(self, client, model):
        self.client = client
        self.model = model
        self.INSTRUCTIONS = THINKER_INSTRUCTIONS

    def think(self, your_task_description: str, parent_task_context: Optional[str] = None):
        prompt_parts = [f"<your_task_description>{your_task_description}</your_task_description>"]
        if parent_task_context:
            prompt_parts.append(f"<parent_task_context>{parent_task_context}</parent_task_context>")
        user_prompt = "\n".join(prompt_parts)

        print(
            f"\n{BColors.OKCYAN}[ThinkerAgent]{BColors.ENDC} Instructions:\n"
            f"{BColors.OKBLUE}{self.INSTRUCTIONS}{BColors.ENDC}"
        )
        print(
            f"{BColors.OKCYAN}[ThinkerAgent]{BColors.ENDC} User Prompt:\n"
            f"{BColors.WARNING}{user_prompt}{BColors.ENDC}"
        )
        tools_to_use = [Tool(google_search=GoogleSearch())]

        response = self.client.thinker_call(
            model=self.model,
            instructions=self.INSTRUCTIONS,
            user_prompt=user_prompt,
            tools=tools_to_use
        )
        response_str = response.strip() if isinstance(response, str) else str(response)
        print(f"{BColors.OKCYAN}[ThinkerAgent]{BColors.ENDC} Response:\n{BColors.OKGREEN}{response_str}{BColors.ENDC}")
        return response_str

class ReviewerAgent:
    def __init__(self, client, model):
        self.client = client
        self.model = model
        self.INSTRUCTIONS = REVIEWER_INSTRUCTIONS

    def review(self, parent_task, current_plan, iteration_count):
        prompt_parts = [
            f"<parent_task>{parent_task}</parent_task>",
            f"<current_iteration>{iteration_count}</current_iteration>",
            f"<current_plan>{json.dumps([p.model_dump() for p in current_plan], indent=2)}</current_plan>"
        ]
        user_prompt = "\n".join(prompt_parts)

        print(f"\n{BColors.OKCYAN}[ReviewerAgent]{BColors.ENDC} Instructions:\n{BColors.OKBLUE}{self.INSTRUCTIONS}{BColors.ENDC}")
        print(f"{BColors.OKCYAN}[ReviewerAgent]{BColors.ENDC} User Prompt:\n{BColors.WARNING}{user_prompt}{BColors.ENDC}")

        try:
            response = self.client.reviewer_call(
                self.model,
                self.INSTRUCTIONS,
                user_prompt,
                schema=ReviewerOut
            )
            print(f"\n{BColors.OKCYAN}[ReviewerAgent]{BColors.ENDC}: Evaluating progress...")
            dumped_response = response.model_dump()
            print(f"{BColors.OKGREEN}{json.dumps(dumped_response, indent=2)}{BColors.ENDC}")
            return dumped_response
        except Exception as e:
            print(f"{BColors.FAIL}[ReviewerAgent] Error: {e}. Defaulting to error assessment.{BColors.ENDC}")
            return {
                "assessment_of_current_iteration": "ERROR_IN_REVIEW_PROCESSING",
                "context_to_use": None
            }

class SynthesizerAgent:
    def __init__(self, client, model):
        self.client = client
        self.model = model
        self.INSTRUCTIONS = SYNTHESIZER_INSTRUCTIONS

    def synthesize(self, parent_task, full_history):
        history_summary_parts = []
        context_to_use = None

        for i, cycle in enumerate(full_history):
            cycle_summary = f"--- Iteration {i+1} ---\n"
            plans_with_responses = cycle.get('plans_with_responses', ["N/A"])
            # Serialize Pydantic models for JSON
            plans_json = json.dumps(
                [getattr(p, "model_dump", lambda: p)() for p in plans_with_responses],
                indent=1
            )
            if len(plans_json) > 1000:
                plans_json = plans_json[:1000] + "...(truncated)"
            cycle_summary += f"Plans & Responses: {plans_json}\n"

            review = cycle.get('review', {})
            cycle_summary += f"Review Assessment for this Iteration: {review.get('assessment_of_current_iteration', 'N/A')}\n"

            # Save context_to_use from the last iteration's review
            if i == len(full_history) - 1:
                context_to_use = review.get("context_to_use")

            history_summary_parts.append(cycle_summary)

        full_history_summary_for_prompt = "\n".join(history_summary_parts)

        prompt_parts = [
            f"<parent_task>{parent_task}</parent_task>",
            f"<full_history_summary>\n{full_history_summary_for_prompt}\n</full_history_summary>"
        ]

        if context_to_use:
            selected_responses_parts = ["<selected_step_responses>"]
            all_step_responses = {}
            for cycle_data in full_history:
                for plan_obj in cycle_data.get('plans_with_responses', []):
                    for step_obj in getattr(plan_obj, "steps", []):
                        key = (getattr(plan_obj, "plan_id", None), getattr(step_obj, "step_id", None))
                        all_step_responses[key] = getattr(step_obj, "response", None) or "N/A"

            for selection_group in context_to_use:
                plan_id = selection_group.get('plan_id')
                for step_id in selection_group.get('step_ids', []):
                    response_text = all_step_responses.get(
                        (plan_id, step_id),
                        "Response not found for this step in history."
                    )
                    selected_responses_parts.append(
                        f"<step_response plan_id='{plan_id}' step_id='{step_id}'>\n{response_text}\n</step_response>"
                    )

            selected_responses_parts.append("</selected_step_responses>")
            if len(selected_responses_parts) > 2:
                prompt_parts.append("\n".join(selected_responses_parts))

        user_prompt = "\n".join(prompt_parts)

        print(f"\n{BColors.OKCYAN}[SynthesizerAgent]{BColors.ENDC} Instructions:\n{BColors.OKBLUE}{self.INSTRUCTIONS}{BColors.ENDC}")
        print(f"{BColors.OKCYAN}[SynthesizerAgent]{BColors.ENDC} User Prompt:\n{BColors.WARNING}{user_prompt}{BColors.ENDC}")

        response = self.client.synthesizer_call(
            self.model,
            self.INSTRUCTIONS,
            user_prompt
        )
        print(f"\n{BColors.OKCYAN}[SynthesizerAgent]{BColors.ENDC}: Generating Final Solution...")
        print(f"{BColors.OKGREEN}{response.strip()}{BColors.ENDC}")
        return response.strip()


class DeepThinkingPipeline:
    def __init__(self, api_key):
        self.client = GeminiAPIClient(api_key=api_key)
        model = "gemini-2.5-flash-preview-05-20"
        self.planner = PlannerAgent(self.client, model)
        self.thinker = ThinkerAgent(self.client, model)
        self.reviewer = ReviewerAgent(self.client, model)
        self.synthesizer = SynthesizerAgent(self.client, model)

    def run(self, parent_task):
        full_history = []
        previous_review_guidance = None
        current_iteration = 0

        while True:
            current_iteration += 1

            exploration_plans = self.planner.generate_plan(parent_task, previous_review_guidance)
            previous_review_guidance = None  # Reset as reviewer no longer provides it

            if not exploration_plans:
                print(f"{BColors.FAIL}[Pipeline] Planner returned an empty plan. This might indicate an issue.{BColors.ENDC}")
                if not full_history:
                    return f"{BColors.FAIL}Error: Planner failed to generate an initial plan and there's no history.{BColors.ENDC}"
                print(f"{BColors.OKCYAN}[Pipeline]{BColors.ENDC} Proceeding to synthesize with available history as no new plan was generated.")
                break

            for plan in exploration_plans:
                for step in plan.steps:
                    display = f"{plan.plan_id}-{step.step_id}: {step.instructions}"
                    display_short = (display[:70] + '...') if len(display) > 73 else display
                    print(f"\n{BColors.OKCYAN}[ThinkerAgent]{BColors.ENDC}: Processing Plan Step -> \"{display_short}\"")
                    step.response = self.thinker.think(step.instructions, parent_task_context=parent_task)

            # Reviewer now receives the full enriched exploration_plans
            review_obj = self.reviewer.review(parent_task, exploration_plans, current_iteration)

            full_history.append({
                "plans_with_responses": exploration_plans,
                "review": review_obj
            })

            assessment = review_obj.get('assessment_of_current_iteration', '')
            print(f"{BColors.OKCYAN}[ReviewerAgent]{BColors.ENDC} Assessment: {BColors.OKGREEN}{assessment}{BColors.ENDC}")

            if assessment in ("SUFFICIENT_FOR_SYNTHESIS", "ERROR_IN_REVIEW_PROCESSING"):
                print(f"\n{BColors.HEADER}--- Process will STOP based on Reviewer's assessment ('{assessment}') after {current_iteration} iterations. ---{BColors.ENDC}")
                break

        if not full_history:
            return f"{BColors.FAIL}Error: No history was generated (e.g., initial planner failure).{BColors.ENDC}"

        print(f"\n{BColors.HEADER}--- Total model cost: ${self.client.total_cost():.4f} ---{BColors.ENDC}")
        return self.synthesizer.synthesize(parent_task, full_history)


if __name__ == "__main__":
    api_key = os.environ.get("GEMINI_API_KEY")

    parent_task = input(f"{BColors.BOLD}USER (Enter your main task) > {BColors.ENDC}").strip()
    if not parent_task:
        print(f"{BColors.FAIL}Error: No main task provided. Exiting.{BColors.ENDC}")
        sys.exit(1)

    print(f"\n{BColors.OKCYAN}Proceeding with task: \"{parent_task}\"{BColors.ENDC}\n")

    pipeline = DeepThinkingPipeline(api_key=api_key)
    final_answer = pipeline.run(parent_task)
