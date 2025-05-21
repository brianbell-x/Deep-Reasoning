# Deep-Thinking

## Overview

Exploring the possibilty of making agents capable of iterative, reflective, and multi-path problem-solving, idea generation and question answering. To do this, I aim to design a system beyond simple prompt-response interactions or basic agentic loops, enabling a more profound and structured approach to tackling complex tasks, particularly those that are not primarily search intensive but require significant internal deliberation, strategic planning, and iterative refinement.

My original thoughts on this were:

"Deep research agents are cool. But sometimes my task doesn't require a deep research report because it researches all related sites and generates a long report with my answer to the problem usually scattered throughout the report. Sometimes just I need a strong thinker, or path explorer that can think through possible solutions/scenarios and return the best one(s). Or to simply help me expand on an idea.I want this to handle tasks like engineering, design, etc. Things that don't need search but definitely needs exploration, reflection, ..."



## Setup

1. **Install dependencies**

   ```
   pip install -r requirements.txt
   ```
2. **Environment variables**

   - Set `GEMINI_API_KEY` in your `.env` file or environment.
   - For backward compatibility, `OPENAI_API_KEY` or `OPENROUTER_API_KEY` will be used if `GEMINI_API_KEY` is not set, but this is deprecated.

   Example `.env`:

   ```
   GEMINI_API_KEY=your-gemini-key-here
   ```
3. **Run the pipeline**

   ```
   python -m app.main
   ```

   You will be prompted for a main task.

## Model selection

- Default model: `gemini-2.5-flash-preview-05-20`
- To use a different Gemini model, edit the model string in `app/main.py`.

## Key files

- `app/gemini_client.py` — Gemini API client (all LLM calls)
- `app/schemas.py` — Pydantic models for structured output
- `app/main.py` — Pipeline and agent orchestration
- `app/client.py` — (deprecated) OpenAI client, now raises ImportError

## Notes

- All outputs are validated using Pydantic schemas.
- Cost tracking uses Gemini Flash pricing by default.
- For more details on Gemini API usage and structured output, see `app/gemini.md`.

## Requirements

- Python 3.9+
- See `requirements.txt` for package list.
