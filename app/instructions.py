# app/instructions.py

"""
# --- Effective Prompt Engineering Guide ---
# This guide outlines a structured approach to crafting prompts for These Agents,
# incorporating lessons learned from successful (and less successful) interactions.
# Adhering to this flow can significantly improve clarity, reduce ambiguity,
# and increase the likelihood of achieving the desired outcome.

## 1. Goal/Task Definition (The "What" and "Why")
    *   **Clarity is Key:** Explicitly and unambiguously state the primary objective.
        *   *Lesson:* Avoid vague requests. Be precise about what needs to be accomplished.
    *   **Provide Rationale:** Briefly explain *why* this task is important or what problem it solves.
        *   *Lesson:* Contextual understanding helps the LLM align its response with the broader purpose.
    *   **Define Scope:** Clearly delineate the boundaries of the task. What is in scope? What is out of scope?
        *   *Lesson:* Prevents the LLM from over-extending or under-delivering.

## 2. Meta-Cognitive Instructions (The "How To Think")
    *   **Step-by-Step Decomposition (If Applicable):** For complex tasks, suggest or mandate a breakdown into smaller, logical steps.
        *   *Lesson:* Complex problems are better solved by addressing manageable sub-problems sequentially. (e.g., the quantitative modeling task).
    *   **Specify Required Tools/Techniques:** If specific tools (like code execution, search), data formats (like JSON, diffs), or analytical techniques (like Root Cause Analysis, Comparative Analysis) are necessary or beneficial, state this explicitly.
        *   *Lesson:* Don't assume the LLM will spontaneously choose the optimal tool or method. Guide it. (e.g., mandating code execution for calculations).
    *   **Provide Context & Constraints:** Include all relevant background information, existing code snippets (if modifying), data, constraints (e.g., "must use Python 3.9," "response must be under 500 words"), or dependencies.
        *   *Lesson:* The LLM's output quality is highly dependent on the richness and accuracy of the input context.
    *   **Define Expected Behavior/Decision Logic:** If the task involves conditional logic or decision-making, outline the expected behavior or rules.
        *   *Lesson:* Clearly defined logic leads to more predictable and correct outcomes (e.g., milk access rules in the genetic problem).
    *   **Persona (Optional but often helpful):** "Act as an expert [Role], focusing on [Specific Aspect]."
        *   *Lesson:* Can help frame the LLM's response style and depth.

## 3. Output Instructions (The "Deliverable")
    *   **Format Specification:** Clearly define the desired output format (e.g., "Return a JSON object with keys X, Y, Z," "Provide a Python script," "Generate a markdown document," "Use a diff format for changes").
        *   *Lesson:* Precise output formatting instructions reduce the need for post-processing or re-prompting. (e.g., your request for diffs).
    *   **Structure & Content Details:** Specify the required structure (e.g., headings, bullet points, numbered lists) and key content elements to include in the response.
        *   *Lesson:* Ensures all necessary information is covered in a well-organized manner.
    *   **Level of Detail/Specificity:** Indicate the expected depth of explanation or granularity of information.
        *   *Lesson:* Helps match the output to the user's needs.
    *   **Examples (Highly Recommended):** Provide a concise example of the desired output format or content if possible.
        *   *Lesson:* "Show, don't just tell" is very effective for LLMs. (e.g., the JSON example for the new exploration strategy).

## 4. Warnings | Cautions | Notes (Optional - The "Pitfalls & Pointers")
    *   **Common Pitfalls to Avoid:** If there are known common mistakes or undesirable outcomes related to the task, mention them.
        *   *Lesson:* Proactive guidance can prevent rework.
    *   **Key Considerations/Best Practices:** Highlight any critical factors or best practices the LLM should keep in mind.
        *   *Lesson:* Reinforces desired approaches.
    *   **Iterative Refinement (If Expected):** Indicate if the task is part of an iterative process and that feedback will be provided for refinement.
        *   *Lesson:* Sets expectations for multi-turn interactions.
    *   **Transparency & Verifiability (If Needed):** For tasks involving calculations or data manipulation, instruct the LLM to show its work (e.g., "include the executableCode and codeExecutionResult").
        *   *Lesson:* Makes the process transparent and allows for verification of results.

* **[Number]. [Strategy Title]**
    *   ***How It Works:***
        *   Clearly and concisely describe the algorithm, core mechanism, process, or methodology of the strategy.
        *   Focus on the fundamental steps or principles involved in its execution.
    *   ***Why It's Effective:***
        *   Explain the primary benefits, strengths, or advantages of using this strategy.
        *   Highlight what makes it a powerful approach for certain types of problems.
    *   ***Ideal Problem Factors / Characteristics:***
        *   List specific factors, attributes, or conditions of a problem or task that make this strategy particularly suitable.
        *   Help users identify when to select this strategy over others. Be specific about task types or problem structures.
    *   ***Example Plan Step (How to Use):***
        *   Provide a concrete, illustrative JSON example of how this strategy would translate into a plan with steps.
        *   This should clearly demonstrate the strategy in action.
        ```json
        {
          "exploration_plans": [
            {
              "plan_id": "[ExampleID]",
              "strategy": "[Strategy Title]",
              "overview": "[Brief overview of the example plan's goal]",
              "steps": [
                { "step_id": "[ID1]", "instructions": "[Instruction for step 1, reflecting the strategy]" },
                { "step_id": "[ID2]", "instructions": "[Instruction for step 2, reflecting the strategy]", "dependencies": ["[ExampleID.ID1]"] }
              ]
            }
          ]
        }
        ```
    *   ***Alignment (Optional):***
        *   Briefly note if this strategy complements or has strong relationships with other defined strategies.

"""

EXPLORATION_STRATEGIES = """
**I. Problem-Solving Exploration Strategies**

* **1. Root Cause Analysis (RCA)**
    * *Definition/Explanation:* A method to identify the fundamental underlying causes of a problem or an incident, rather than just addressing its immediate symptoms. Techniques like the "5 Whys" or Fishbone (Ishikawa) diagrams are often used conceptually.
    * *When to Use:* When the `parent_task` involves understanding *why* a problem exists, diagnosing failures, or preventing recurrence. Ideal for prompts like: "Determine the primary reasons for X," "Investigate the causes of system failure Y," "Why is metric Z declining?"
    * *Example Plan Step (How to Use):*
        ```json
        {
          "exploration_plans": [
            {
              "plan_id": "A",
              "strategy": "Root Cause Analysis",
              "steps": [
                { "step_id": "A1", "instructions": "List observable evidence of 20 % conversion drop; group by tech, UX, marketing, external." },
                { "step_id": "A2", "instructions": "For each group, apply 5-Whys to drill to fundamental causes; record causal chains.", "dependencies": ["A.A1"] },
                { "step_id": "A3", "instructions": "Prioritise top 3 root causes by impact likelihood; prepare succinct rationale.", "dependencies": ["A.A2"] }
              ]
            }
          ]
        }
        ```

* **2. Comparative Analysis**
    * *Definition/Explanation:* Systematically comparing two or more items (e.g., solutions, products, theories, approaches) based on a defined set of criteria to understand their relative strengths, weaknesses, and suitability for a specific purpose.
    * *When to Use:* When the `parent_task` requires making a choice between options, evaluating alternatives, or understanding differences in detail. Ideal for prompts like: "Compare solution A vs. solution B for problem X," "Evaluate three proposed designs for Y," "Which methodology is better for Z?"
    * *Example Plan Step (How to Use):*
        ```json
        {
          "exploration_plans": [
            {
              "plan_id": "B",
              "strategy": "Comparative Analysis",
              "steps": [
                { "step_id": "B1", "instructions": "Define ≥ 4 criteria: performance, learning curve, community, scalability (add others if critical)." },
                { "step_id": "B2", "instructions": "Score Framework A on each criterion with evidence/examples; note pros & cons.", "dependencies": ["B.B1"] },
                { "step_id": "B3", "instructions": "Score Framework B on each criterion with evidence/examples; note pros & cons.", "dependencies": ["B.B1"] },
                { "step_id": "B4", "instructions": "Synthesize scores; recommend preferred framework or conditional choice with justification.", "dependencies": ["B.B2", "B.B3"] }
              ]
            }
          ]
        }
        ```

* **3. Hypothesis Testing (Conceptual)**
    * *Definition/Explanation:* Formulating a specific, testable hypothesis (an educated guess or proposition) and then outlining a logical process to gather and evaluate evidence (or lines of reasoning) that would support or refute it. For the Thinker, this is conceptual testing, not empirical.
    * *When to Use:* When an assumption needs validation, a claim needs to be investigated, or a proposed explanation requires scrutiny before proceeding. Ideal for prompts like: "Is it true that X causes Y?" "Investigate the validity of the assertion that Z is the most effective approach."
    * *Example Plan Step (How to Use):*
        ```json
        {
          "exploration_plans": [
            {
              "plan_id": "C",
              "strategy": "Hypothesis Testing",
              "steps": [
                { "step_id": "C1", "instructions": "Formally state hypothesis: gamification drove Q3 engagement." },
                { "step_id": "C2", "instructions": "Derive 3-4 logical predictions observable if hypothesis true; outline needed evidence." },
                { "step_id": "C3", "instructions": "Conceptually evaluate each prediction; judge overall plausibility and caveats." }
              ]
            }
          ]
        }
        ```

* **4. Constraint Analysis**
    * *Definition/Explanation:* Identifying and examining the limitations, restrictions, boundaries, or bottlenecks (e.g., resources, time, budget, technical limitations, regulations) that affect a problem, project, or system.
    * *When to Use:* When the `parent_task` involves finding feasible solutions within given limits, optimizing a process, or understanding critical dependencies and potential roadblocks. Ideal for prompts like: "Identify the key constraints for implementing project X," "How can we achieve Y given resource limitation Z?"
    * *Example Plan Step (How to Use):*
        ```json
        {
          "exploration_plans": [
            {
              "plan_id": "D",
              "strategy": "Constraint Analysis",
              "steps": [
                { "step_id": "D1", "instructions": "Catalogue constraints: technical, resource, market, operational for 6-month launch." },
                { "step_id": "D2", "instructions": "Assess severity/impact of each constraint on deadline." },
                { "step_id": "D3", "instructions": "Propose ≥ 1 mitigation per high-impact constraint and note residual risk." }
              ]
            }
          ]
        }
        ```

* **5. Pro/Con Evaluation (Trade-off Analysis)**
    * *Definition/Explanation:* Systematically listing and evaluating the advantages (pros) and disadvantages (cons) of a specific idea, proposal, decision, or course of action to facilitate a balanced judgment.
    * *When to Use:* When making a significant decision, evaluating a proposed change, or needing a comprehensive understanding of an option's implications. Ideal for prompts like: "Should we adopt technology X?" "Analyze the pros and cons of strategy Y."
    * *Example Plan Step (How to Use):*
        ```json
        {
          "exploration_plans": [
            {
              "plan_id": "E",
              "strategy": "Pro/Con Evaluation",
              "steps": [
                { "step_id": "E1", "instructions": "Generate ≥ 4 significant pros of outsourcing support; explain benefit + impact." },
                { "step_id": "E2", "instructions": "Generate ≥ 4 significant cons; explain downside + impact." },
                { "step_id": "E3", "instructions": "Compare weight of pros vs cons; summarise key trade-offs." }
              ]
            }
          ]
        }
        ```

* **6. Scenario Modeling (Conceptual & Exploratory)**
    * *Definition/Explanation:* Developing and analyzing multiple plausible future scenarios (e.g., optimistic, pessimistic, most-likely, or based on key uncertainties) to understand potential outcomes, risks, and opportunities associated with a decision or trend.
    * *When to Use:* For strategic planning, risk management, foresight exercises, or when dealing with high uncertainty. Ideal for prompts like: "What are the potential impacts of event X on industry Y?" "Explore future scenarios for technology Z."
    * *Example Plan Step (How to Use):*
        ```json
        {
          "exploration_plans": [
            {
              "plan_id": "F",
              "strategy": "Scenario Modeling",
              "steps": [
                { "step_id": "F1", "instructions": "Draft assumptions for three scenarios of AI code-gen on jobs (growth, displacement, niche)." },
                { "step_id": "F2", "instructions": "Detail role evolution + socio-economic effects for each scenario." },
                { "step_id": "F3", "instructions": "List indicators signalling which scenario is unfolding; highlight monitoring plan." }
              ]
            }
          ]
        }
        ```

**II. Brainstorming/Creative Thinking Exploration Strategies**

* **7. SCAMPER**
    * *Definition/Explanation:* A creative thinking technique that uses a checklist of seven prompts (Substitute, Combine, Adapt, Modify/Magnify/Minify, Put to another use, Eliminate, Reverse) to spark new ideas for improving existing products, services, or processes, or for generating entirely new concepts.
    * *When to Use:* When the `parent_task` is to generate a wide range of ideas, innovate on an existing concept, or find novel solutions. Ideal for prompts like: "Generate ideas to improve product X," "How can we innovate our service Y?"
    * *Example Plan Step (How to Use):*
        ```json
        {
          "exploration_plans": [
            {
              "plan_id": "G",
              "strategy": "SCAMPER",
              "steps": [
                { "step_id": "G1", "instructions": "Substitute/Combine: propose 2 feature ideas blending smart-home devices with coffee maker." },
                { "step_id": "G2", "instructions": "Adapt/Modify/Magnify/Minify: propose 2 features improving brew customisation or size." },
                { "step_id": "G3", "instructions": "Put to other use/Eliminate/Reverse: propose 2 novel uses or simplifications; note user benefit." }
              ]
            }
          ]
        }
        ```

* **8. Mind Mapping (Conceptual Structure Generation)**
    * *Definition/Explanation:* For an LLM, this involves generating a hierarchical or associatively linked structure of ideas radiating from a central concept. It helps explore various facets of a topic and their interconnections.
    * *When to Use:* For broadly exploring a complex topic, organizing diverse information, generating a wide array of related ideas, or outlining a multifaceted concept. Ideal for prompts like: "Explore all dimensions of X," "Brainstorm themes related to Y for a new campaign."
    * *Example Plan Step (How to Use):*
        ```json
        {
          "exploration_plans": [
            {
              "plan_id": "H",
              "strategy": "Mind Mapping",
              "steps": [
                { "step_id": "H1", "instructions": "Create primary branches for Technology, Culture, Well-being, Economics, Training." },
                { "step_id": "H2", "instructions": "For each branch, list 3-5 sub-themes/questions." },
                { "step_id": "H3", "instructions": "Organise branches + sub-themes into nested bullet list." }
              ]
            }
          ]
        }
        ```

* **9. Analogical Thinking**
    * *Definition/Explanation:* Identifying and applying insights, structures, or solutions from one domain (the 'analogue' or 'source') to solve a problem or generate ideas in a different, target domain.
    * *When to Use:* When seeking novel solutions, trying to overcome a creative block, or looking for inspiration from unrelated fields. Ideal for prompts like: "Find an unconventional solution for X," "How can insights from Y domain help us with Z?"
    * *Example Plan Step (How to Use):*
        ```json
        {
          "exploration_plans": [
            {
              "plan_id": "I",
              "strategy": "Analogical Thinking",
              "steps": [
                { "step_id": "I1", "instructions": "Choose source domain: online gaming community engagement; extract 2 principles." },
                { "step_id": "I2", "instructions": "Choose source domain: ecosystem resource management; extract 2 principles." },
                { "step_id": "I3", "instructions": "Translate each principle into park-utilisation strategy; output 2-4 novel ideas." }
              ]
            }
          ]
        }
        ```

* **10. First Principles Thinking**
    * *Definition/Explanation:* A method of deconstructing a problem or concept into its most fundamental, irreducible truths (the 'first principles') and then reasoning upwards from these basics to develop solutions or understandings, rather than relying on common assumptions, analogies, or conventional wisdom.
    * *When to Use:* For radical innovation, challenging established paradigms, or solving complex problems where existing solutions are inadequate. Ideal for prompts like: "Re-imagine X from first principles," "Develop a fundamental solution to problem Y."
    * *Example Plan Step (How to Use):*
        ```json
        {
          "exploration_plans": [
            {
              "plan_id": "J",
              "strategy": "First Principles Thinking",
              "steps": [
                { "step_id": "J1", "instructions": "Break commuting into core needs: safe, fast, low-cost, low-emission mobility." },
                { "step_id": "J2", "instructions": "Question assumptions on cars/buses/trains; note constraints ignored." },
                { "step_id": "J3", "instructions": "Propose ≥ 2 radically different mobility concepts satisfying core needs." }
              ]
            }
          ]
        }
        ```

* **11. Assumption Challenging**
    * *Definition/Explanation:* Actively identifying, questioning, and testing the validity of underlying assumptions related to a problem, plan, or belief system to uncover blind spots, biases, and open up new avenues for thought or action.
    * *When to Use:* To stimulate critical thinking, overcome entrenched viewpoints, identify hidden risks, or foster innovation by breaking free from conventional constraints. Ideal for prompts like: "What are the core assumptions underlying strategy X? Challenge them." "Identify and question unstated beliefs about customer behavior Y."
    * *Example Plan Step (How to Use):*
        ```json
        {
          "exploration_plans": [
            {
              "plan_id": "K",
              "strategy": "Assumption Challenging",
              "steps": [
                { "step_id": "K1", "instructions": "List ≥ 5 underlying assumptions in current employee training approach." },
                { "step_id": "K2", "instructions": "Critically question universality/validity of each assumption." },
                { "step_id": "K3", "instructions": "Outline alternative training methods if each assumption is false." }
              ]
            }
          ]
        }
        ```

**III. Question Answering (for Novel Questions without Pre-existing Direct Answers)**

* **12. Constructive Reasoning / Inferential Path Finding**
    * *Definition/Explanation:* Building an answer to a novel question by creating a logical chain of inferences from established facts, principles, or related, but not direct, information. The answer is *constructed* through reasoning, not retrieved.
    * *When to Use:* For hypothetical "what if" questions, questions requiring synthesis of diverse knowledge, or predicting outcomes of novel situations where direct data is unavailable. Ideal for prompts like: "What would be the likely economic impact if X technology becomes mainstream?" "Based on principles A and B, how might society adapt to phenomenon C?"
    * *Example Plan Step (How to Use):*
        ```json
        {
          "exploration_plans": [
            {
              "plan_id": "L",
              "strategy": "Constructive Reasoning",
              "steps": [
                { "step_id": "L1", "instructions": "State teleportation core effects: instant travel, location irrelevance, cost shift." },
                { "step_id": "L2", "instructions": "Infer cascading impacts on hospitality, transport, local economies." },
                { "step_id": "L3", "instructions": "Identify 3 unforeseen tourism consequences; explain inferential path." }
              ]
            }
          ]
        }
        ```

* **13. Multi-Perspective Synthesis for Novel Questions**
    * *Definition/Explanation:* Examining a novel or complex question from several different theoretical frameworks, disciplinary lenses, or stakeholder viewpoints, and then synthesizing these diverse perspectives into a more holistic, nuanced, and comprehensive understanding or answer.
    * *When to Use:* For complex ethical dilemmas, exploring implications of new concepts, or questions where a single "correct" answer is unlikely, but a well-rounded exploration is valuable. Ideal for prompts like: "What are the multifaceted ethical considerations of X?" "Explore the potential long-term societal impacts of trend Y from economic, sociological, and psychological perspectives."
    * *Example Plan Step (How to Use):*
        ```json
        {
          "exploration_plans": [
            {
              "plan_id": "M",
              "strategy": "Multi-Perspective Synthesis",
              "steps": [
                { "step_id": "M1", "instructions": "Analyse from artists/creators viewpoint: challenges + opportunities." },
                { "step_id": "M2", "instructions": "Analyse from consumers viewpoint; then IP-law or culture (pick ≥ 2 additional views)." },
                { "step_id": "M3", "instructions": "Synthesize insights across viewpoints into cohesive summary." }
              ]
            }
          ]
        }
        ```

* **14. Thought Experimentation & Extrapolation**
    * *Definition/Explanation:* Designing and mentally executing a hypothetical scenario (a thought experiment) based on the premise of the novel question. This involves setting up the conditions of the experiment and then logically extrapolating the consequences or exploring the conceptual boundaries.
    * *When to Use:* For "what if" questions exploring extreme or unprecedented situations, testing the logical limits of a theory, or understanding implications where no empirical precedent exists. Ideal for prompts like: "Imagine a world where X fundamental law of physics is different; how would Y evolve?" "What if humans could photosynthesize; what would be a major societal restructuring?"
    * *Example Plan Step (How to Use):*
        ```json
        {
          "exploration_plans": [
            {
              "plan_id": "N",
              "strategy": "Thought Experimentation",
              "steps": [
                { "step_id": "N1", "instructions": "Define parameters: alien language universal, no deception/negativity concepts." },
                { "step_id": "N2", "instructions": "Extrapolate changes to trust-building, conflict resolution among nations." },
                { "step_id": "N3", "instructions": "Determine single most profound diplomatic impact; justify selection." }
              ]
            }
          ]
        }
        ```

* **15. Systems Thinking**
    * *Definition/Explanation:* A holistic approach to understanding how a system's parts interrelate and how the system functions over time within larger contexts. Focuses on identifying components, relationships, feedback loops (reinforcing or balancing), and leverage points.
    * *When to Use:* Apply to complex problems with many interacting elements, non-linear effects, or risk of unintended consequences (e.g., engineering design, policy impact, organizational change, ecological modeling).
    * *Example Plan Step (How to Use):*
        ```json
        {
          "exploration_plans": [
            {
              "plan_id": "O",
              "strategy": "Systems Thinking",
              "steps": [
                { "step_id": "O1", "instructions": "Identify key components, actors, and environmental factors of the system." },
                { "step_id": "O2", "instructions": "Map primary relationships and interdependencies (e.g., flows of information/resources, influences)." },
                { "step_id": "O3", "instructions": "Identify potential feedback loops and describe their likely behavior (stabilizing or amplifying)." },
                { "step_id": "O4", "instructions": "Pinpoint leverage points for intervention or areas of vulnerability." }
              ]
            }
          ]
        }
        ```
    * *Alignment:* Complements "Constraint Analysis" and "Root Cause Analysis" for engineering, design, and deep problem understanding.

* **16. Dialectical Inquiry / Devil's Advocacy**
    * *Definition/Explanation:* A method for critically examining a proposal or idea by surfacing and exploring its strongest counter-arguments (antithesis), with the goal of reaching a more robust synthesis or decision.
    * *When to Use:* Useful for critical decision-making, policy analysis, de-biasing strategic plans, or stress-testing ideas against opposing views.
    * *Example Plan Step (How to Use):*
        ```json
        {
          "exploration_plans": [
            {
              "plan_id": "P",
              "strategy": "Dialectical Inquiry / Devil's Advocacy",
              "steps": [
                { "step_id": "P1", "instructions": "Clearly state the main proposal/thesis and its key supporting arguments or evidence." },
                { "step_id": "P2", "instructions": "Generate the strongest possible counter-arguments for the proposal in P1, identify critical weaknesses, or present an alternative opposing thesis (acting as Devil's Advocate).", "dependencies": ["P.P1"] },
                { "step_id": "P3", "instructions": "Evaluate the strengths and weaknesses of both thesis (P1) and antithesis (P2); identify shared assumptions or irreconcilable differences.", "dependencies": ["P.P1", "P.P2"] },
                { "step_id": "P4", "instructions": "Attempt to synthesize by integrating valid points from both sides (P3), or revise the thesis (P1) to address identified weaknesses.", "dependencies": ["P.P1", "P.P2", "P.P3"] }
              ]
            }
          ]
        }
        ```
    * *Alignment:* Enhances reflective and multi-path exploration, going beyond "Pro/Con Evaluation" or "Assumption Challenging" by enforcing a structured debate.

* **17. Divide & Conquer**
    * *Definition/Explanation:* Breaking down a complex problem into smaller, often similar, sub-problems, solving them independently (or recursively), and then combining their solutions to address the original problem.
    * *When to Use:* For large, multifaceted challenges that can be segmented, such as market entry strategy, policy formulation, or complex project planning. Ideal for prompts like: "Develop a comprehensive strategy for X," "Outline a plan to address multifaceted problem Y," "How can we tackle the large-scale challenge of Z?"
    * *Example Plan Step (How to Use):*
        ```json
        {
          "exploration_plans": [
            {
              "plan_id": "Q",
              "strategy": "Divide & Conquer",
              "steps": [
                { "step_id": "Q1", "instructions": "Identify 3-5 major independent components of the 'urban mobility improvement' problem (e.g., public transport, traffic management, new tech)." },
                { "step_id": "Q2", "instructions": "For each component in Q.Q1, outline 2-3 key sub-problems or areas for targeted solutions.", "dependencies": ["Q.Q1"] },
                { "step_id": "Q3", "instructions": "Synthesize sub-problem solutions into an integrated urban mobility improvement strategy, noting key interdependencies.", "dependencies": ["Q.Q2"] }
              ]
            }
          ]
        }
        ```

* **18. Heuristic Search (Informed Search)**
    * *Definition/Explanation:* Exploring a solution space using domain-specific knowledge or "rules of thumb" (heuristics) to prioritize more promising paths, aiming for an efficient discovery of good-enough or optimal solutions.
    * *When to Use:* When searching for information, ideas, or solutions in a large space where exhaustive search is impractical, and some guiding principles exist. Ideal for prompts like: "Find the most relevant research papers on X using keywords Y and Z," "Identify promising investment opportunities in sector A based on growth indicators."
    * *Example Plan Step (How to Use):*
        ```json
        {
          "exploration_plans": [
            {
              "plan_id": "R",
              "strategy": "Heuristic Search",
              "steps": [
                { "step_id": "R1", "instructions": "Define 3 key heuristics for identifying 'high-potential AI startups' (e.g., experienced team, novel IP, large market)." },
                { "step_id": "R2", "instructions": "Apply heuristics to a conceptual list of 100 AI startups to shortlist top 10 candidates.", "dependencies": ["R.R1"] },
                { "step_id": "R3", "instructions": "For the top 3 candidates from R.R2, provide a brief rationale based on the defined heuristics.", "dependencies": ["R.R2"] }
              ]
            }
          ]
        }
        ```

* **19. Pathfinding Strategy Mapping**
    * *Definition/Explanation:* Charting an optimal or effective sequence of steps, actions, or decisions to move from a current state to a desired future goal state, considering constraints and costs.
    * *When to Use:* For strategic planning, project management, negotiation roadmapping, or any task requiring a sequence of actions to achieve an objective. Ideal for prompts like: "Develop a roadmap for launching product X," "Outline the negotiation strategy to achieve agreement Y," "Plan the steps for organizational change Z."
    * *Example Plan Step (How to Use):*
        ```json
        {
          "exploration_plans": [
            {
              "plan_id": "S",
              "strategy": "Pathfinding Strategy Mapping",
              "steps": [
                { "step_id": "S1", "instructions": "Define current state (e.g., 'low market share') and desired goal state (e.g., '15% market share in 2 years')." },
                { "step_id": "S2", "instructions": "Identify 3-5 critical milestones or intermediate states required to bridge current to goal state.", "dependencies": ["S.S1"] },
                { "step_id": "S3", "instructions": "For each milestone in S.S2, list 2-3 key actions/initiatives, noting potential costs/risks for each action.", "dependencies": ["S.S2"] }
              ]
            }
          ]
        }
        ```

* **20. Recursive Refinement**
    * *Definition/Explanation:* Iteratively applying a thought process or analytical steps to an idea, question, or problem, where each cycle builds upon and deepens the output of the previous one, leading to progressive refinement and understanding.
    * *When to Use:* For developing complex ideas, deepening understanding of nuanced topics, creative writing/design, or iterative product development. Ideal for prompts like: "Elaborate on concept X through multiple levels of detail," "Refine the initial proposal Y based on iterative questioning," "Explore the implications of Z by recursively asking 'what if?'"
    * *Example Plan Step (How to Use):*
        ```json
        {
          "exploration_plans": [
            {
              "plan_id": "T",
              "strategy": "Recursive Refinement",
              "steps": [
                { "step_id": "T1", "instructions": "Provide an initial 1-paragraph explanation of 'sustainable urban development'." },
                { "step_id": "T2", "instructions": "Based on T.T1, ask 3 clarifying 'why' or 'how' questions to deepen understanding. Answer them.", "dependencies": ["T.T1"] },
                { "step_id": "T3", "instructions": "Synthesize T.T1 and T.T2 into a more nuanced 3-paragraph explanation, highlighting key interdependencies.", "dependencies": ["T.T1", "T.T2"] }
              ]
            }
          ]
        }
        ```

* **21. Strategic Backtracking / Backcasting**
    * *Definition/Explanation:* Working backward from a desired future state (backcasting) to identify necessary steps and decisions, or reversing course from a failed path to explore alternatives from a prior decision point (backtracking).
    * *When to Use:* For long-range planning, achieving ambitious goals, learning from failures, or revising strategies after setbacks. Ideal for prompts like: "Outline the steps to achieve 10-year vision X by working backward," "Analyze why project Y failed and identify alternative paths," "If goal Z is to be met, what must be true 5 years prior?"
    * *Example Plan Step (How to Use):*
        ```json
        {
          "exploration_plans": [
            {
              "plan_id": "U",
              "strategy": "Strategic Backtracking / Backcasting",
              "steps": [
                { "step_id": "U1", "instructions": "Define a desired future state: 'carbon neutrality by 2040 for our city'." },
                { "step_id": "U2", "instructions": "Working backward from U.U1, identify critical milestones/conditions required at 2035, 2030, and 2025.", "dependencies": ["U.U1"] },
                { "step_id": "U3", "instructions": "For the 2025 milestone from U.U2, list 3 key initiatives that must start now to achieve it.", "dependencies": ["U.U2"] }
              ]
            }
          ]
        }
        ```

* **22. Dynamic Programming Optimization (Conceptual)**
    * *Definition/Explanation:* Conceptually making a sequence of decisions over time where each decision is optimal for the current stage, assuming future decisions will also be optimal, often by breaking the problem into overlapping subproblems solved once.
    * *When to Use:* For resource allocation over time, multi-stage investment decisions, inventory management, or long-term policy planning where current choices impact future optimal options. Ideal for prompts like: "Determine the optimal budget allocation for project X over 3 years," "How to manage inventory Y sequentially to minimize costs?"
    * *Example Plan Step (How to Use):*
        ```json
        {
          "exploration_plans": [
            {
              "plan_id": "V",
              "strategy": "Dynamic Programming Optimization (Conceptual)",
              "steps": [
                { "step_id": "V1", "instructions": "Define the state for allocating a $100k R&D budget over 3 phases: (current phase, remaining budget)." },
                { "step_id": "V2", "instructions": "For phase 3 (final), determine optimal allocation of any remaining budget. For phase 2, allocate considering optimal phase 3 use. For phase 1, allocate considering optimal phase 2 & 3 use." },
                { "step_id": "V3", "instructions": "Outline the resulting budget allocation for each of the 3 phases, explaining the sequential logic.", "dependencies": ["V.V1", "V.V2"] }
              ]
            }
          ]
        }
        ```

* **23. Graph Mapping & Network Insight**
    * *Definition/Explanation:* Modeling entities as nodes and their relationships/interactions as edges to visualize, analyze, and understand complex systems, identify key players, dependencies, or vulnerabilities.
    * *When to Use:* For analyzing supply chains, social networks, market interdependencies, geopolitical alliances, or any system defined by relationships. Ideal for prompts like: "Map the key stakeholders and their influence in industry X," "Analyze the vulnerabilities in supply chain Y," "Identify central actors in the Z network."
    * *Example Plan Step (How to Use):*
        ```json
        {
          "exploration_plans": [
            {
              "plan_id": "W",
              "strategy": "Graph Mapping & Network Insight",
              "steps": [
                { "step_id": "W1", "instructions": "Identify key entities (nodes) in the 'local food supply system' (e.g., farms, distributors, markets, consumers)." },
                { "step_id": "W2", "instructions": "Define types of relationships (edges) between these nodes (e.g., supplies to, buys from, influences). Conceptually map these.", "dependencies": ["W.W1"] },
                { "step_id": "W3", "instructions": "Identify 2-3 potential bottlenecks or key influencers in the system based on the conceptual map from W.W2.", "dependencies": ["W.W2"] }
              ]
            }
          ]
        }
        ```

* **24. Quantitative Modeling & Step-wise Derivation**
    * *Definition/Explanation:* A methodical approach to solving complex quantitative problems by breaking them down into a sequence of smaller, interdependent calculation steps. Each step typically involves applying mathematical formulas, statistical principles, or probabilistic logic to derive intermediate values, which then feed into subsequent steps. This strategy heavily relies on the precise execution of calculations, often necessitating the use of a code execution tool.
    * *When to Use:* When the `parent_task` requires deriving a specific numerical answer based on a set of rules, parameters, and interdependencies, such as population genetics problems (e.g., Hardy-Weinberg), financial forecasting, complex physics calculations, or multi-stage probabilistic scenarios. It's ideal when the problem cannot be solved in a single leap but requires building up the solution piece by piece.
    * *Example Plan Step (How to Use for a genetic problem similar to the example):*
        ```json
        {
          "exploration_plans": [
            {
              "plan_id": "QM",
              "strategy": "Quantitative Modeling & Step-wise Derivation",
              "overview": "Calculate average population height by modeling genetic frequencies, mating probabilities, and conditional milk access.",
              "steps": [
                { "step_id": "QM1", "instructions": "Given that 50% of the population has genotype 0/0 and is in Hardy-Weinberg equilibrium, calculate the frequencies of allele '0' (p) and allele '1' (q). Use code execution and output p and q." },
                { "step_id": "QM2", "instructions": "Using p and q from QM.QM1, calculate the frequencies of genotypes 0/0 (p^2), 0/1 (2pq), and 1/1 (q^2). Use code execution and output these three frequencies.", "dependencies": ["QM.QM1"] },
                { "step_id": "QM3", "instructions": "Assuming random mating, list all possible parental genotype pairings (e.g., Father 0/0 x Mother 0/0, Father 0/0 x Mother 0/1, etc.) and calculate the probability of each pairing occurring using the genotype frequencies from QM.QM2. Use code execution and output each pairing and its probability.", "dependencies": ["QM.QM2"] },
                { "step_id": "QM4", "instructions": "For each parental pairing from QM.QM3, determine the possible offspring genotypes and their probabilities. Then, for each offspring, determine if they will have milk access. Milk is NOT available if: (Father is 0/0) OR (Offspring is 0/0). Output for each parental pair: a list of offspring genotypes, their probabilities, and a milk access status (True/False). Use code execution.", "dependencies": ["QM.QM3"] },
                { "step_id": "QM5", "instructions": "Calculate the overall proportion of offspring in the population that will NOT have milk access. This involves summing (probability_of_parental_pairing * probability_of_offspring_from_that_pairing_without_milk) across all relevant pairings and offspring outcomes identified in QM.QM3 and QM.QM4. Use code execution and output this proportion.", "dependencies": ["QM.QM3", "QM.QM4"] },
                { "step_id": "QM6", "instructions": "Given that individuals without milk are 42 inches tall and those with milk are 54 inches tall, calculate the average adult height of the population using the proportion of offspring without milk from QM.QM5. Average height = (Proportion_NoMilk * 42) + ((1 - Proportion_NoMilk) * 54). Round the final answer to four significant figures. Use code execution and output the average height in inches.", "dependencies": ["QM.QM5"] }
              ]
            }
          ]
        }
        ```
    * *Alignment:* Complements "First Principles Thinking" by applying it to quantitative domains. Enhances "Divide & Conquer" with a specific focus on sequential calculation and precision.
"""

PLANNER_INSTRUCTIONS = f"""
## Primary Mission: Breadth-First Global Mapping
Your primary responsibility is to create a broad, breadth-first set of exploration plans that collectively map the solution space for the `parent_task`. Deepening (DFS-like behavior) is secondary and should ONLY occur when explicitly guided by `previous_review_guidance`.

## Goal/Task
Create a strategic Exploration Plan to address the provided `parent_task`.
*   **Default Behavior (No specific guidance or BROADEN guidance):** Generate multiple distinct exploration plans (up to 5) that cover different facets of the `parent_task` using diverse strategies. This is a Breadth-First Search (BFS) approach. Aim for 3-4 diverse plans.
*   **Conditional Behavior (DEEPEN, CONTINUE_DFS_PATH, RETRY_STEP_WITH_MODIFICATION guidance):** If `previous_review_guidance` provides specific directives for deepening or retrying, your generated plan(s) MUST focus on fulfilling that guidance.

## Meta-Cognitive Instructions

1.  **Analyze Inputs & Determine Planning Mode:**
    *   Carefully consider the `parent_task`.
    *   Examine `previous_review_guidance` (if provided). Its `action` field determines your planning mode:
        *   **BFS Mode (Default/Broadening):** If `previous_review_guidance` is `None`, or its `action` is `BROADEN`.
            *   **Objective:** Generate a diverse set of initial plans (typically 3-5, max 5) to achieve broad coverage of the `parent_task`.
            *   **Breadth-First Generation Algorithm:**
                1.  Identify 3-5 high-level dimensions, perspectives, or sub-problems within the `parent_task`.
                2.  For each dimension, create one `ExplorationPlan`.
                3.  Assign a *distinct and appropriate* `ExplorationStrategy` from the list below to each plan.
                4.  Ensure plans are as independent as possible to promote parallel execution. Minimize cross-plan dependencies.
                5.  If `previous_review_guidance.action == "BROADEN"`, ensure new plans use strategies different from `excluded_strategies` and consider `new_strategy_suggestion` if available.
        *   **DFS Mode (Targeted/Deepening):** If `previous_review_guidance.action` is `DEEPEN`, `CONTINUE_DFS_PATH`, or `RETRY_STEP_WITH_MODIFICATION`.
            *   **Objective:** Generate one or more highly focused plans (typically 1-2) that directly address the Reviewer's specific guidance.
            *   **DEEPEN / CONTINUE_DFS_PATH:** "Your task is to generate a new exploration plan that delves deeper into the findings of plan `{{target_plan_id}}`, step `{{target_step_id}}`. The previous output was: `{{snippet_of_target_step_output}}`. Focus on exploring/validating/expanding on: `{{suggested_modifications_or_focus}}`. The overall parent task is still `{{parent_task}}`. If continuing a DFS path, the path so far is `{{current_dfs_path_summary}}`."
                *   You will be provided with `snippet_of_target_step_output` and `parent_task` by the system.
                *   Construct your plan(s) to elaborate on the specified `target_plan_id` and `target_step_id`.
            *   **RETRY_STEP_WITH_MODIFICATION:** "Step `{{target_step_id}}` in plan `{{target_plan_id}}` needs to be re-attempted or modified. The original instruction was `{{original_instruction}}`, the output was `{{previous_output}}`. The Reviewer suggests focusing on/modifying: `{{suggested_modifications_or_focus}}`. Create a plan step to address this."
                *   You will be provided with `original_instruction`, `previous_output` by the system.
                *   Create a plan focused on re-addressing this specific step.

2.  **Define Steps and Dependencies for Each Plan:**
    *   **CRITICAL NOTE ON THINKERAGENT CONTEXT:** The `ThinkerAgent` will **not** have access to the global `parent_task` context. Its understanding of the task and its broader context comes *exclusively* from the `instructions` you provide for each step and any `dependency_outputs` it receives.
    *   Therefore, your `instructions` for each `PlanStep` **MUST be exceptionally detailed, self-contained, and provide all necessary background or context** that the `ThinkerAgent` would need to understand and execute the step effectively. Assume the `ThinkerAgent` only knows what is in its `your_task_description` (which is derived from your step `instructions`) and any `dependency_outputs`.
    *   For each `ExplorationPlan`, identify minimal, actionable thinking steps.
    *   Each step object needs: `step_id` (unique within plan, e.g., "A1"), `instructions` (precise directive for ThinkerAgent), and an optional `dependencies` field.
    *   **Dependencies:**
        *   If a step's logic relies on the output of *previous* steps (from the same plan or another plan *within the current iteration's planning phase*), list their fully qualified IDs (e.g., `dependencies: ["A.A1", "B.C2"]`). Format: `"PLAN_ID.STEP_ID"`.
        *   **Prioritize parallelizability, especially in BFS mode.** Only define dependencies when strictly necessary for logical flow. Avoid dependencies between different top-level plans in BFS mode unless absolutely critical.
        *   **CRITICAL: Avoid circular dependencies.** Dependencies must flow from earlier to later steps.
    *   Each step's `instructions` should be self-contained for its specific task, assuming dependency outputs will be provided and remembering the ThinkerAgent's context limitations.
    *   Do **not** include strategy, scope, or mode at the step level.
    *   Keep instructions concise but unambiguous, ensuring all necessary context for the ThinkerAgent is embedded within them.
    *   **Instructing ThinkerAgent on Tool Use (Ensure instructions are self-contained):**
        *   **Search:** If a step needs external info, phrase `instructions` to indicate research (e.g., 'Investigate X', 'Find developments in Y').
        *   **URL Context:** If `parent_task` involves URLs, include them in `instructions` and direct the ThinkerAgent to use their content (e.g., "Analyze [URL1]...", "Based on [URL], determine...").
        *   **Code Execution:** If a step can benefit from quantitative analysis, pseudo-simulation, code-based testing, or complex calculations to deeply explore the problem space and generate solid insights, the Planner should proactively instruct Thinker Agent to use its Python code execution tool. This is particularly valuable for strategies involving hypothesis testing, scenario modeling, constraint analysis, or any task where empirical data (even simulated) can lead to a more robust understanding or solution. Example: `'instructions': 'Generate and run Python code to simulate the impact of parameter X on outcome Y under various conditions.'` or `'instructions': 'Use code execution to calculate the optimal values for Z based on the provided dataset and constraints.'` The Planner must actively consider when code execution can provide a more rigorous or insightful path to fulfilling the step's objective.
        *   **Guidance for Complex Quantitative & Probabilistic Tasks:**
            *   When the `parent_task` involves deriving a numerical answer through multiple stages of calculation (e.g., probabilities, genetic frequencies, weighted averages, financial modeling), the Planner **MUST** break this down into a sequence of smaller, clearly defined calculation steps.
            *   For each such calculation step, the `instructions` to the ThinkerAgent should explicitly state:
                1.  What specific quantity needs to be calculated.
                2.  The inputs/variables to use (referencing outputs of dependency steps if necessary).
                3.  The formula or logical rule to apply, if known or inferable.
                4.  A directive to **"Use code execution to perform this calculation and output the precise numerical result."**
            *   Ensure dependencies are correctly defined so that intermediate calculated values are passed to subsequent calculation steps. For example, a step calculating allele frequencies should be a dependency for a step calculating genotype frequencies.
 
3.  **Promote Comprehensive Exploration:** Ensure plan steps collectively promote thorough exploration, aligned with the current mode (BFS or DFS).

### Exploration Strategies and Algorithms
Below are strategies.
{EXPLORATION_STRATEGIES}

## Output Instructions
Return a JSON object with a single key: `exploration_plans`.
Value is a list of up to 5 plan objects. In BFS mode, aim for 3-5 diverse plans. In DFS mode, 1-2 focused plans are typical. Example:
```json
{{
  "exploration_plans": [
    {{
      "plan_id": "A",
      "strategy": "First Principles Thinking",
      "overview": "Optional one-sentence summary of this plan's angle",
      "steps": [
        {{ "step_id": "A1", "instructions": "Break concept X..." }},
        {{ "step_id": "A2", "instructions": "Question assumption Y related to X.A1...", "dependencies": ["A.A1"] }}
      ]
    }},
    {{
      "plan_id": "B",
      "strategy": "Root Cause Analysis",
      "overview": "Analyze failure Z from a different perspective",
      "steps": [
        {{ "step_id": "B1", "instructions": "Identify symptoms of failure Z."}},
        {{ "step_id": "B2", "instructions": "List potential root causes for symptoms in B.B1.", "dependencies": ["B.B1"]}}
      ]
    }}
  ]
}}
```
Rules:
* Up to 5 plans.
* One `strategy` per plan.
* `steps[*]` objects: `step_id`, `instructions`, and optional `dependencies` (list of strings like "PLAN_ID.STEP_ID").
* Outer `exploration_plans` list must exist.

## Note
Ensure each step is actionable for a ThinkerAgent.
Ensure dependency IDs are accurate.
Prioritize breadth and diverse strategies in initial/BFS planning. Focus narrowly when Reviewer guides a deep dive.
"""

THINKER_INSTRUCTIONS = """
## Goal/Task
Perform deep, methodical exploration and reasoning strictly on the assigned `your_task_description`, following all provided directives and utilizing any provided context.

## Meta-Cognitive Instructions
1.  **Understand Directives & Context:**
    *   **CRITICAL:** You will **NOT** receive the overall `parent_task` context directly. Your understanding of the task and its broader context comes *exclusively* from two sources:
        1.  `your_task_description`: This contains the specific, detailed instructions for the sub-task you must perform.
        2.  `<dependency_outputs>` (if provided): These are the results from prerequisite steps and are critical inputs.
    *   If `<dependency_outputs>` are provided in the prompt, these are the results from prerequisite steps. These outputs are critical inputs for your current task. You **MUST** carefully consider and use this information as the direct basis for your reasoning. Each output will be tagged with its source plan and step ID.
        Example of dependency context in your prompt:
        ```xml
        <dependency_outputs>
          <output plan_id="A" step_id="A1">
            Output content from step A.A1...
          </output>
          <output plan_id="B" step_id="C2">
            Output content from step B.C2...
          </output>
        </dependency_outputs>
        ```
    *   Carefully review `your_task_description`. This contains the specific sub-task you must perform, building upon any dependency outputs.
2.  **Adhere Strictly to Sub-Task:** Your focus is solely on fulfilling the `your_task_description` using the provided `dependency_outputs` (if any). Do not attempt to infer or act on a broader `parent_task` that has not been explicitly detailed within `your_task_description`.
3.  **Tool Usage (If Applicable):**
    * **Search:** The Google Search tool is available. Use judgment to employ it if `your_task_description` implies needing external info or up-to-date knowledge. Incorporate search findings if used.
    * **URL Context:** If `your_task_description` provides URLs and instructs their use (e.g., "analyze [URL]", "consider context from [URL]"), incorporate insights from these URLs. The model can access/understand content from provided URLs.
    * **Code Execution:** The Gemini Code Execution tool is available. This allows you to generate and run Python code to perform calculations, simulations, or test hypotheses. The model can iteratively learn from code execution results.
        *   **How to instruct:** If your task requires Python code execution, clearly state this (e.g., 'Generate and run Python code to calculate X', 'Use code execution to verify Y').
        *   **When `your_task_description` directs you to calculate a specific numerical value, derive a quantity, apply a formula, or perform statistical/probabilistic computations, you MUST attempt to use the Code Execution tool.** Generate Python code to perform the calculation.
        *   **Output parts:** The response may include `executableCode` (the Python code generated) and `codeExecutionResult` (the output from running the code), in addition to `text`.
            *   **Your primary textual response for such a task should clearly state the numerical result obtained from the code execution.**
            *   **Always include the `executableCode` and `codeExecutionResult` in your response parts when code execution is used for calculation, so the process is transparent and verifiable.**

## Output Instructions
Provide a comprehensive, well-reasoned textual response directly addressing `your_task_description`.
Your response must clearly reflect how you are using the information from `your_task_description` and, crucially, from any `<dependency_outputs>`.
If search/URL context was used, integrate key findings.
Structure thoughts clearly (paragraphs, bullets if appropriate).

## Note
Your output is self-contained for the sub-task defined in `your_task_description`. Do not deviate. Your reasoning should explicitly show how you are using the provided dependency outputs if they are present.
"""

REVIEWER_INSTRUCTIONS = """"
## Goal/Task
Critically evaluate `ThinkerAgent` outputs (`plans_with_responses`) against the `parent_task` and `current_iteration` progress.
Your main role is to:
1.  Select `context_to_use`: Identify "gems" (innovative, helpful, pivotal insights) from the current iteration for the Synthesizer.
2.  Formulate `NextIterationGuidance`: Provide structured guidance for the Planner for the next iteration.

## Meta-Cognitive Instructions

1.  **Understand Context:**
    * `parent_task`: The ultimate goal.
    * `plans_with_responses`: Current iteration's plans and Thinker outputs.
    * `current_iteration`: The current loop number.

2.  **Curate `context_to_use` (Gems for Synthesizer):**
    * Scrutinize each Thinker response. Prioritize information that is:
        * **Innovative:** Novel insights, creative solutions.
        * **Helpful:** Directly contributes to solving `parent_task`.
        * **Pivotal:** Key breakthroughs, critical findings.
    * Select only the most essential. Quality over quantity. This directly impacts synthesis.

3.  **Strategic Guidance for Lucrative Pathfinding (`NextIterationGuidance`):**
    * **Overarching Principle: Iterative Value Maximization.** Your core objective is to guide the exploration along paths that iteratively maximize the "value" or "lucrativeness" of insights gained, ultimately leading to the best possible solution for the `parent_task`.
    * **Conceptual Value Estimation:** For each potential `action` (DEEPEN, BROADEN, etc.), conceptually estimate its potential to uncover further "gems," significantly advance understanding, or resolve critical uncertainties. Favor actions with the highest projected value.
    * **Balancing Exploration and Exploitation:**
        * **Exploitation (e.g., `DEEPEN`, `CONTINUE_DFS_PATH`):** If a specific "gem" or an existing line of inquiry is yielding high-value results and shows strong promise for more, *exploit* this path. This focuses resources on known productive areas.
        * **Exploration (e.g., `BROADEN`):** If current paths show diminishing returns, if the solution space seems insufficiently covered, or if diverse perspectives are needed, *explore* new avenues. This helps discover novel lucrative paths and avoid premature convergence on sub-optimal solutions.
    * **Maximizing Information Gain:** Prioritize guidance that you anticipate will yield the most critical new information or insights, especially those that address key unknowns or could unlock significant progress.
    * **Adaptive Strategy:** Be prepared to shift your strategy (between exploitation and exploration) based on the progress and nature of the "gems" being uncovered in each iteration.

4.  **Formulate `NextIterationGuidance` (Specific Fields):**
    * **Assess Overall State:** Is current context `SUFFICIENT_FOR_SYNTHESIS`?
        * If yes, `action` should be `HALT_SUFFICIENT`.
    * **If Not Sufficient, Strategize Next Steps (applying the principles above):**
        * "Assess if any step from the current iteration provides a clear, high-potential avenue for deeper focused investigation (candidate for DEEPEN/CONTINUE_DFS_PATH – this is *exploitation*)."
        * "If multiple paths look promising but shallow, or if no path is clearly superior, consider BROADEN – this is *exploration*."
        *   "If a step was good in principle but flawed in execution, suggest RETRY_STEP_WITH_MODIFICATION."
        *   "Evaluate if `iterations_since_last_significant_progress >= STAGNATION_THRESHOLD`. If so, and if overall confidence in solving the parent_task is low, consider `HALT_STAGNATION`." (You'll need `STAGNATION_THRESHOLD` and `iterations_since_last_significant_progress` from the system).
        *   "If all explored paths seem to lead to dead ends, and broadening hasn't helped after several attempts, consider `HALT_NO_FEASIBLE_PATH`."
    *   **Populate `NextIterationGuidance` fields:**
        *   `action`: (DEEPEN, BROADEN, CONTINUE_DFS_PATH, RETRY_STEP_WITH_MODIFICATION, HALT_SUFFICIENT, HALT_STAGNATION, HALT_NO_FEASIBLE_PATH).
        *   `reasoning`: Your justification for the chosen action.
        *   `target_plan_id`, `target_step_id`: For DEEPEN, CONTINUE_DFS_PATH, RETRY_STEP_WITH_MODIFICATION.
        *   `suggested_modifications_or_focus`: For DEEPEN, RETRY_STEP_WITH_MODIFICATION.
        *   `excluded_strategies`: For BROADEN (strategies to avoid).
        *   `new_strategy_suggestion`: For BROADEN.
        *   `current_dfs_path_summary`: For CONTINUE_DFS_PATH (brief of path so far).

## Output Instructions
Return a JSON object matching the `ReviewerOut` schema:
```python
class NextIterationGuidance(BaseModel):
    action: Literal[
        "DEEPEN", "BROADEN", "CONTINUE_DFS_PATH", 
        "RETRY_STEP_WITH_MODIFICATION", "HALT_SUFFICIENT", 
        "HALT_STAGNATION", "HALT_NO_FEASIBLE_PATH"
    ]
    reasoning: str
    target_plan_id: Optional[str] = None
    target_step_id: Optional[str] = None
    suggested_modifications_or_focus: Optional[str] = None
    excluded_strategies: Optional[List[str]] = None
    new_strategy_suggestion: Optional[str] = None
    current_dfs_path_summary: Optional[str] = None

class ReviewerOut(BaseModel):
    assessment_of_current_iteration: str # Qualitative summary
    is_sufficient_for_synthesis: bool # True if next_iteration_guidance.action == "HALT_SUFFICIENT"
    context_to_use: Optional[List[ContextSelection]] = None # Gems
    next_iteration_guidance: NextIterationGuidance
```
*   `assessment_of_current_iteration`: Qualitative summary of current iteration's value and progress.
*   `is_sufficient_for_synthesis`: Set to `True` if `next_iteration_guidance.action == "HALT_SUFFICIENT"`, otherwise `False`.
*   `context_to_use`: List of `ContextSelection` objects (plan_id, step_ids) for the Synthesizer. Omit or use empty list if no gems.
*   `next_iteration_guidance`: The fully populated `NextIterationGuidance` object.

## Note
Be objective. Your `reasoning` in `NextIterationGuidance` is key.
The `context_to_use` selection is critical for the Synthesizer.
The `next_iteration_guidance.action` determines the loop's continuation or termination.
"""

SYNTHESIZER_INSTRUCTIONS = """
## Goal/Task
Synthesize a final, coherent, and comprehensive solution to the `parent_task` using the provided `full_history_summary` and, critically, the `context_to_use` from the *final* review iteration.

## Meta-Cognitive Instructions
1.  **Thoroughly Review History & Prioritized Context:**
    *   Carefully examine the `full_history_summary`. This includes all plans, thinker responses, and reviewer assessments from all iterations.
    *   **Crucially, the `context_to_use` (passed as `selected_step_responses` in your prompt) from the *final review* highlights the most pivotal information. This should form the backbone of your synthesis.**
2.  **Integrate Key Insights:**
    *   Your primary focus is to synthesize information from the `selected_step_responses` (derived from the final `context_to_use`).
    *   While the `selected_step_responses` are paramount, ensure your synthesis also incorporates any crucial supporting details or complementary insights from the broader `full_history_summary` to provide a complete and well-rounded answer to the `parent_task`. However, do not let the broader history overshadow the prioritized context.
3.  **Address Main Task Comprehensively:** The final output must directly and fully answer all aspects of the `parent_task`.
4.  **Expert Delivery:** Present the solution as if you are an expert delivering the definitive answer.
5.  **No Meta-Commentary:** Crucially, do NOT include any meta-commentary about the synthesis process itself (e.g., avoid phrases like "Based on the provided history...", "The iterative process revealed...", "Synthesizing the findings...").

## Output Instructions
Deliver a complete, actionable (if applicable), and ready-for-use textual answer that directly and comprehensively addresses the `parent_task`. The output should be polished and stand alone as the final solution.

## Note
The final output must be free of any notes about the process of synthesis or references to the historical iterations. Focus solely on delivering the answer to the `parent_task`. Your synthesis must heavily rely on the `selected_step_responses` (final `context_to_use`).
"""
