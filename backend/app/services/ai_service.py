"""
Modular AI service layer.
Supports OpenAI (GPT), Google Gemini and Ollama.
Falls back to a fixed demo-mode response if no provider is configured.
"""

import logging
import os
import re
from typing import Any

from .gemini_service import (
    GeminiServiceError,
    generate_json_response as generate_gemini_json_response,
    generate_text_response,
)
from .ollama_service import (
    OllamaServiceError,
    generate_json as generate_ollama_json,
    generate_text as generate_ollama_text,
)

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = (
    "You are SecureAI, an enterprise assistant. "
    "Be helpful, professional, and concise. "
    "Never refuse reasonable workplace questions."
)

_TOKEN_PATTERN = re.compile(r"[a-z0-9]+")
_FOLLOW_UP_PREFIXES = (
    "and ",
    "also ",
    "what about",
    "how about",
    "tell me more",
    "more on",
    "more about",
    "can you explain",
    "can you elaborate",
)
_FOLLOW_UP_TOKENS = {
    "and", "also", "that", "this", "it", "they", "them", "those", "these",
    "he", "she", "more", "too", "same", "continue",
}


def get_ai_response(messages: list[dict]) -> str:
    """
    Dispatch to the configured AI provider.
    `messages` is a list of {role, content} dicts (OpenAI format).
    """
    provider = os.getenv("AI_PROVIDER", "gemini").lower()

    if provider == "openai":
        return _openai_response(messages)
    if provider == "gemini":
        return _gemini_response(messages)
    if provider == "ollama":
        return _ollama_response(messages)
    return _mock_response(messages)


def get_grounded_ai_response(messages: list[dict], system_prompt: str) -> str:
    """Generate a policy-grounded response without silently falling back to demo text."""
    provider = os.getenv("AI_PROVIDER", "gemini").lower()
    if provider == "openai":
        api_key = os.getenv("OPENAI_API_KEY", "").strip()
        if not api_key or api_key.startswith("your-"):
            raise RuntimeError("OPENAI_API_KEY is not configured")
        try:
            from openai import OpenAI
            response = OpenAI(api_key=api_key).chat.completions.create(
                model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
                messages=[{"role": "system", "content": system_prompt}, *messages],
                max_tokens=800,
                temperature=0.2,
            )
            answer = response.choices[0].message.content
            if not answer:
                raise RuntimeError("The LLM returned an empty response")
            return answer.strip()
        except RuntimeError:
            raise
        except Exception as exc:
            raise RuntimeError(f"OpenAI generation failed: {exc}") from exc
    if provider == "gemini":
        try:
            return generate_text_response(
                messages,
                system_prompt=system_prompt,
                model_name=os.getenv("GEMINI_MODEL"),
                temperature=0.2,
                max_output_tokens=800,
            )
        except Exception as exc:
            raise RuntimeError(f"Gemini generation failed: {exc}") from exc
    if provider == "ollama":
        try:
            prompt_lines = [system_prompt.strip(), ""]
            prompt_lines.extend(
                f"{'Assistant' if item.get('role') == 'assistant' else 'User'}: {item.get('content', '')}"
                for item in messages
            )
            prompt_lines.append("Assistant:")
            return generate_ollama_text("\n".join(prompt_lines))
        except Exception as exc:
            raise RuntimeError(f"Ollama generation failed: {exc}") from exc
    raise RuntimeError(f"Unsupported AI_PROVIDER '{provider}'. Use gemini, openai, or ollama.")


def llm_status() -> dict[str, Any]:
    provider = os.getenv("AI_PROVIDER", "gemini").strip().lower()
    if provider == "gemini":
        configured = bool(os.getenv("GEMINI_API_KEY", "").strip())
    elif provider == "openai":
        configured = bool(os.getenv("OPENAI_API_KEY", "").strip())
    elif provider == "ollama":
        configured = True
    else:
        configured = False
    return {"provider": provider, "configured": configured}


def get_ai_json_response(
    prompt: str,
    *,
    system_prompt: str | None = None,
    temperature: float = 0.2,
    max_output_tokens: int = 900,
) -> dict[str, Any]:
    provider = os.getenv("AI_PROVIDER", "gemini").lower()

    if provider == "gemini":
        return generate_gemini_json_response(
            prompt,
            system_prompt=system_prompt or SYSTEM_PROMPT,
            temperature=temperature,
            max_output_tokens=max_output_tokens,
        )
    if provider == "ollama":
        full_prompt = prompt
        if system_prompt:
            full_prompt = f"{system_prompt.strip()}\n\n{prompt.strip()}"
        return generate_ollama_json(full_prompt)

    raise ValueError(f"Structured AI provider is not configured: {provider}")


def resolve_contextual_query(messages: list[dict]) -> str:
    candidates = _build_contextual_query_candidates(messages)
    return candidates[0] if candidates else ""


def _openai_response(messages: list[dict]) -> str:
    api_key = os.getenv("OPENAI_API_KEY", "")
    if not api_key or api_key.startswith("your-"):
        return _mock_response(messages)

    try:
        from openai import OpenAI

        client = OpenAI(api_key=api_key)
        full_messages = [{"role": "system", "content": SYSTEM_PROMPT}] + messages
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=full_messages,
            max_tokens=800,
            temperature=0.7,
        )
        return response.choices[0].message.content.strip()
    except Exception as exc:
        logger.error("OpenAI error: %s", exc)
        return _fallback_error(str(exc))


def _gemini_response(messages: list[dict]) -> str:
    try:
        return generate_text_response(
            messages,
            system_prompt=SYSTEM_PROMPT,
            temperature=0.7,
            max_output_tokens=800,
        )
    except GeminiServiceError as exc:
        logger.error("Gemini error; using mock fallback: %s", exc)
        return _mock_response(messages)
    except Exception as exc:  # noqa: BLE001
        logger.error("Unexpected Gemini error: %s", exc)
        return _fallback_error(str(exc))


def _ollama_response(messages: list[dict]) -> str:
    try:
        return generate_ollama_text(_messages_to_prompt(messages))
    except OllamaServiceError as exc:
        logger.error("Ollama error; using mock fallback: %s", exc)
        return _mock_response(messages)
    except Exception as exc:
        logger.error("Unexpected Ollama error: %s", exc)
        return _fallback_error(str(exc))


def _messages_to_prompt(messages: list[dict]) -> str:
    lines = [SYSTEM_PROMPT, ""]
    for message in messages:
        role = str(message.get("role", "user")).strip().lower()
        content = str(message.get("content", "")).strip()
        if not content:
            continue
        if role == "assistant":
            lines.append(f"Assistant: {content}")
        else:
            lines.append(f"User: {content}")
    lines.append("Assistant:")
    return "\n".join(lines).strip()


def _mock_response(messages: list[dict]) -> str:
    return (
        "I'm SecureAI running in demo mode (no AI provider configured). "
        "Configure AI_PROVIDER and its API key in backend/.env for real responses."
    )


def _fallback_error(err: str) -> str:
    return (
        "I encountered an issue connecting to the AI provider. "
        "Please check your API key configuration. "
        f"Technical detail: {err[:120]}"
    )


def _build_contextual_query_candidates(messages: list[dict]) -> list[str]:
    current_user_message = ""
    previous_user_message = ""
    recent_assistant_message = ""

    for message in reversed(messages):
        role = message.get("role")
        content = str(message.get("content", "")).strip()
        if not content:
            continue
        if role == "user" and not current_user_message:
            current_user_message = content
            continue
        if role == "assistant" and not recent_assistant_message:
            recent_assistant_message = content
            continue
        if role == "user" and not previous_user_message:
            previous_user_message = content
            break

    if not current_user_message:
        return []

    candidates = [current_user_message.lower()]
    if not previous_user_message or not _looks_like_follow_up(current_user_message):
        return candidates

    combined_user_context = f"{previous_user_message} {current_user_message}".strip().lower()
    candidates.append(combined_user_context)

    if recent_assistant_message:
        candidates.append(f"{previous_user_message} {recent_assistant_message} {current_user_message}".strip().lower())

    return candidates


def _looks_like_follow_up(query: str) -> bool:
    normalized_query = " ".join((query or "").strip().lower().split())
    if not normalized_query:
        return False

    if normalized_query.startswith(_FOLLOW_UP_PREFIXES):
        return True

    tokens = _tokenize(normalized_query)
    if len(tokens) <= 5 and any(token in _FOLLOW_UP_TOKENS for token in tokens):
        return True

    return False


def _tokenize(text: str) -> list[str]:
    return [token for token in _TOKEN_PATTERN.findall(text.lower()) if token]
