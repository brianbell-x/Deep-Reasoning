from typing import Any, Type, TypeVar, Optional
from google import genai
from google.genai import types
from pydantic import BaseModel
import json

T = TypeVar("T", bound=BaseModel)

class Client:
    """Centralizes Gemini API calls."""

    def __init__(self, api_key: str):
        self._client = genai.Client(api_key=api_key)

    def call(
        self,
        *,
        model: str,
        system_instruction: str,
        user_prompt: str,
        schema: Optional[Type[T]] = None,
        tools: Optional[list[types.Tool]] = None,
    ) -> T | str:
        gen_config_params: dict[str, Any] = {}

        if system_instruction:
            gen_config_params["system_instruction"] = system_instruction

        if schema:
            gen_config_params["response_mime_type"] = "application/json"
            gen_config_params["response_schema"] = schema

        if tools:
            gen_config_params["tools"] = tools

        config = types.GenerateContentConfig(**gen_config_params)

        resp = self._client.models.generate_content(
            model=model,
            contents=user_prompt,
            config=config,
        )

        if schema:
            try:
                parsed = resp.parsed
                if parsed is None:
                    prompt_feedback = str(getattr(resp, 'prompt_feedback', 'N/A'))
                    finish_reason = "N/A"
                    if getattr(resp, "candidates", None) and hasattr(resp.candidates[0], "finish_reason"):
                        finish_reason = str(resp.candidates[0].finish_reason)
                    raw_text = "N/A"
                    try:
                        c = resp.candidates[0]
                        if (
                            hasattr(c, "content")
                            and hasattr(c.content, "parts")
                            and c.content.parts
                            and hasattr(c.content.parts[0], "text")
                        ):
                            raw_text = c.content.parts[0].text
                            if raw_text and len(raw_text) > 200:
                                raw_text = raw_text[:200] + "..."
                        elif hasattr(resp, "text") and resp.text:
                            raw_text = resp.text
                            if raw_text and len(raw_text) > 200:
                                raw_text = raw_text[:200] + "..."
                    except Exception:
                        pass
                    raise ValueError(
                        f"Gemini API's `resp.parsed` was None for schema '{schema.__name__}'. "
                        f"This might indicate a Pydantic validation error suppressed by the Gemini library, "
                        f"or the model failed to produce valid JSON matching the schema. "
                        f"Prompt Feedback: {prompt_feedback}. Finish Reason: {finish_reason}. "
                        f"Raw text snippet: '{raw_text}'"
                    )
                if not isinstance(parsed, schema):
                    raise TypeError(
                        f"Gemini API's `resp.parsed` returned type '{type(parsed).__name__}', "
                        f"but expected schema type '{schema.__name__}'. Parsed object: {str(parsed)[:200]}"
                    )
                return parsed
            except (AttributeError, TypeError, ValueError) as e:
                raise ValueError(
                    f"Error processing Gemini JSON response with `resp.parsed` for schema '{schema.__name__}'. "
                    f"Error: {type(e).__name__} - {e}."
                ) from e
            except Exception as e:
                raise ValueError(
                    f"Unexpected error processing Gemini JSON response with `resp.parsed` for schema '{schema.__name__}'. "
                    f"Error: {type(e).__name__} - {e}."
                ) from e

        try:
            return resp.text
        except AttributeError:
            resp_summary = str(resp)[:200] + "..." if str(resp) else "N/A"
            raise ValueError(
                f"Gemini API response does not have a 'text' attribute for non-schema call. "
                f"Response summary: {resp_summary}"
            )

    def planner_call(self, model: str, instructions: str, user_prompt: str, schema: Optional[Type[T]] = None) -> T | str:
        return self.call(model=model, system_instruction=instructions, user_prompt=user_prompt, schema=schema)

    def thinker_call(self, model: str, instructions: str, user_prompt: str, tools: Optional[list[types.Tool]] = None) -> str:
        response = self.call(model=model, system_instruction=instructions, user_prompt=user_prompt, tools=tools)
        return response

    def reviewer_call(self, model: str, instructions: str, user_prompt: str, schema: Optional[Type[T]] = None) -> T | str:
        return self.call(model=model, system_instruction=instructions, user_prompt=user_prompt, schema=schema)

    def synthesizer_call(self, model: str, instructions: str, user_prompt: str) -> str:
        return self.call(model=model, system_instruction=instructions, user_prompt=user_prompt)
