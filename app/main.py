import os
import sys
import json
import dotenv

from app.instructions import (
    PLANNER_INSTRUCTIONS,
    THINKER_INSTRUCTIONS,
    REVIEWER_INSTRUCTIONS,
    SYNTHESIZER_INSTRUCTIONS,
)
from app.client import DeepThinkingAPIClient

dotenv.load_dotenv()

class PlannerAgent:
    def __init__(self, client, model):
        self.client = client
        self.model = model
        self.INSTRUCTIONS = PLANNER_INSTRUCTIONS

    def generate_plan(self, main_task, previous_review_guidance=None):
        prompt_parts = [
            f"<main_task>{main_task}</main_task>"
        ]
        if previous_review_guidance:
            prompt_parts.append(
                f"<previous_review_guidance>{previous_review_guidance}</previous_review_guidance>"
            )
        user_prompt = "\n".join(prompt_parts)

        response = self.client.planner_call(
            self.model,
            self.INSTRUCTIONS,
            user_prompt
        )
        print("\n[PlannerAgent]: Generating Exploration Plan...")
        content = response.output_text
        try:
            plan_data = json.loads(content)
            return plan_data.get("exploration_plan", [])
        except json.JSONDecodeError:
            print("[PlannerAgent] Error: Could not decode JSON plan. Returning empty plan.")
            return []

class ThinkerAgent:
    def __init__(self, client, model):
        self.client = client
        self.model = model
        self.INSTRUCTIONS = THINKER_INSTRUCTIONS

    def think(self, sub_task_description, main_task_context=None):
        prompt_parts = [
            f"<sub_task_description>{sub_task_description}</sub_task_description>"
        ]
        if main_task_context:
            prompt_parts.append(
                f"<main_task_context>{main_task_context}</main_task_context>"
            )
        user_prompt = "\n".join(prompt_parts)

        response = self.client.thinker_call(
            self.model,
            self.INSTRUCTIONS,
            user_prompt
        )
        return (response.output_text).strip()

class ReviewerAgent:
    def __init__(self, client, model):
        self.client = client
        self.model = model
        self.INSTRUCTIONS = REVIEWER_INSTRUCTIONS

    def review(self, main_task, current_plan, current_results, iteration_count):
        results_context_parts = []
        for i, res in enumerate(current_results):
            plan_step_context = current_plan[i] if i < len(current_plan) else "N/A (result out of sync with plan items)"
            results_context_parts.append(f"Result for plan step \"{plan_step_context}\":\n{res}\n---")
        results_context = "\n".join(results_context_parts)

        prompt_parts = [
            f"<main_task>{main_task}</main_task>",
            f"<current_iteration>{iteration_count}</current_iteration>",
            f"<current_plan>{json.dumps(current_plan, indent=2)}</current_plan>",
            f"<results_for_current_plan>\n{results_context}\n</results_for_current_plan>"
        ]
        user_prompt = "\n".join(prompt_parts)

        response = self.client.reviewer_call(
            self.model,
            self.INSTRUCTIONS,
            user_prompt
        )
        print("\n[ReviewerAgent]: Evaluating progress...")
        content = response.output_text
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            print("[ReviewerAgent] Error: Could not decode JSON review. Defaulting to REPLAN.")
            return {"decision": "REPLAN", "guidance": "Reviewer output was not valid JSON. The next plan should aim for greater clarity, ensure all aspects of the main task are covered, and that each thinking step is sufficiently deep."}

class SynthesizerAgent:
    def __init__(self, client, model):
        self.client = client
        self.model = model
        self.INSTRUCTIONS = SYNTHESIZER_INSTRUCTIONS

    def synthesize(self, main_task, full_history):
        history_summary_parts = []
        for i, cycle in enumerate(full_history):
            cycle_summary = f"--- Iteration {i+1} ---\n"
            plan_steps = cycle.get('plan', ["N/A"])
            cycle_summary += f"Plan Attempted: {json.dumps(plan_steps, indent=1)}\n"
            results = cycle.get('results', [])
            if results:
                cycle_summary += "Key Insights/Results Snippets:\n"
                for j, res in enumerate(results):
                    plan_step_context = plan_steps[j] if j < len(plan_steps) else "N/A"
                    res_snippet = (res[:200] + '...') if len(res) > 203 else res
                    cycle_summary += f"  - For plan step '{plan_step_context}': {res_snippet}\n"
            review = cycle.get('review', {})
            cycle_summary += f"Review Decision for this Iteration: {review.get('decision', 'N/A')}\n"
            if review.get('decision') == "REPLAN" and review.get('guidance'):
                cycle_summary += f"Guidance that shaped subsequent planning: {review.get('guidance', 'N/A')[:200]}...\n"
            history_summary_parts.append(cycle_summary)

        full_history_summary_for_prompt = "\n".join(history_summary_parts)

        prompt_parts = [
            f"<main_task>{main_task}</main_task>",
            f"<full_history_summary>\n{full_history_summary_for_prompt}\n</full_history_summary>"
        ]
        user_prompt = "\n".join(prompt_parts)

        response = self.client.synthesizer_call(
            self.model,
            self.INSTRUCTIONS,
            user_prompt
        )
        print("\n[SynthesizerAgent]: Generating Final Solution...")
        return (response.output_text).strip()

class DeepThinkingPipeline:
    def __init__(self, api_key):
        self.client = DeepThinkingAPIClient(api_key=api_key)
        strong_model = "o4-mini"
        capable_model = "o4-mini"
        self.planner = PlannerAgent(self.client, strong_model)
        self.thinker = ThinkerAgent(self.client, capable_model)
        self.reviewer = ReviewerAgent(self.client, strong_model)
        self.synthesizer = SynthesizerAgent(self.client, strong_model)

    def run(self, main_task):
        full_history = []
        previous_review_guidance = None
        current_iteration = 0

        while True:
            current_iteration += 1
            print(f"\n--- Starting Iteration {current_iteration} ---")

            exploration_plan_steps = self.planner.generate_plan(main_task, previous_review_guidance)

            if not exploration_plan_steps:
                print("[Pipeline] Planner returned an empty plan. This might indicate an issue or that the previous guidance suggested no further steps.")
                if not full_history:
                    return "Error: Planner failed to generate an initial plan and there's no history."
                print("[Pipeline] Proceeding to synthesize with available history as no new plan was generated.")
                break

            current_cycle_results = []
            for i, plan_step_desc in enumerate(exploration_plan_steps):
                plan_step_display = (plan_step_desc[:70] + '...') if len(plan_step_desc) > 73 else plan_step_desc
                print(f"\n[ThinkerAgent {i+1}/{len(exploration_plan_steps)}]: Processing Plan Step -> \"{plan_step_display}\"")
                result = self.thinker.think(plan_step_desc, main_task_context=main_task)
                current_cycle_results.append(result)

            review_obj = self.reviewer.review(main_task, exploration_plan_steps, current_cycle_results, current_iteration)

            full_history.append({
                "plan": exploration_plan_steps,
                "results": current_cycle_results,
                "review": review_obj
            })

            print(f"[ReviewerAgent] Decision: {review_obj.get('decision')}")
            guidance_for_log = review_obj.get('guidance', 'No guidance provided.')
            guidance_display = (guidance_for_log[:100] + '...') if len(guidance_for_log) > 103 else guidance_for_log
            print(f"[ReviewerAgent] Guidance Snippet: {guidance_display}")

            if review_obj.get("decision") == "SUFFICIENT":
                print(f"\n--- Solution deemed SUFFICIENT after {current_iteration} iterations. ---")
                break

            previous_review_guidance = review_obj.get("guidance")
            if not previous_review_guidance and review_obj.get("decision") == "REPLAN":
                print("[Pipeline] Reviewer decided REPLAN but provided no guidance. This may lead to unproductive loops. Consider adjusting Reviewer prompt or task. Stopping.")
                break

        if not full_history:
            return "Error: No history was generated (e.g., initial planner failure)."

        print(f"\n--- Total model cost: ${self.client.total_cost():.4f} ---")
        return self.synthesizer.synthesize(main_task, full_history)

if __name__ == "__main__":
    # Prefer OPENAI_API_KEY, fallback to OPENROUTER_API_KEY with warning
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        api_key = os.environ.get("OPENROUTER_API_KEY")
        if api_key:
            print("Warning: Using deprecated OPENROUTER_API_KEY. Please set OPENAI_API_KEY instead.")
        else:
            print("Error: OPENAI_API_KEY environment variable not set.")
            sys.exit(1)

    main_task = input("USER (Enter your main task) > ").strip()
    if not main_task:
        print("Error: No main task provided. Exiting.")
        sys.exit(1)

    print(f"\nProceeding with task: \"{main_task}\"\n")

    pipeline = DeepThinkingPipeline(api_key=api_key)
    final_answer = pipeline.run(main_task)
