# Deep-Thinking (Gemini Edition)

## Overview

This project implements a multi-agent pipeline (Planner, Thinker, Reviewer, Synthesizer) using Google's Gemini API for all LLM calls, with structured outputs validated by Pydantic models.

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
