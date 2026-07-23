"""
llm_client.py
--------------
Wraps the Google Gemini API for the NARRATIVE sections of the playbook
(Threat Summary, Root Cause explanation, Executive Summary) — the sections
where fluent prose genuinely helps and isn't operationally dangerous if the
wording isn't perfect. Structured/technical content (commands, rules, MITRE
IDs, CVEs) comes from threat_intel.py's curated templates instead — see that
module's docstring for why an LLM is the wrong tool for that part.

WHY GEMINI: this is a student hackathon project — no budget for a paid API,
and no tolerance for a provider that could lock the account behind a broken
team-permissions state on demo day (that happened with Groq). Google AI
Studio's free tier (aistudio.google.com/apikey) requires no credit card,
sign-in is just your existing Google account. Module 4 only calls the LLM
for events that clear the risk>70 gate (empirically ~40% of a batch), so a
normal demo run stays well within free-tier rate limits regardless of which
model in the chain ends up serving the request.

MODEL VOLATILITY: Gemini's free-tier model lineup has been retired faster
than documented — gemini-2.5-flash and gemini-2.5-flash-lite both started
returning 404 "not found" in production testing of this file (confirmed
directly: every call to either model 404'd, while gemini-3.5-flash
responded successfully), despite Google's own deprecation page still
listing an Oct 16 2026 shutdown date at the time. Because of this,
call_llm() tries every model in MODEL_FALLBACK_CHAIN in order rather than
hard-coding one name — see that list's comment for how to update it if the
current entries get retired too.

THINKING TOKENS (Gemini 3.x-specific gotcha, also confirmed directly): all
Gemini 3.x models (including gemini-3.5-flash) have internal "thinking"
enabled by default, and thinking tokens are deducted from the SAME
maxOutputTokens budget as the visible answer — this is a real, documented
behavior change from Gemini 2.5, not a bug in this code. With a low
maxOutputTokens value, the model can burn its entire budget "thinking" and
return an empty or truncated response (finishReason=MAX_TOKENS) before
writing a single word of the actual answer. Fixed here two ways: (1) set
thinkingLevel to "low" in generationConfig, since these are short factual
summaries that don't need deep reasoning, and (2) size MAX_TOKENS well
above what the visible text alone would need, so there's headroom left
after thinking. Source: https://ai.google.dev/gemini-api/docs/generate-content/thinking
Do not "fix" a truncation problem by just raising MAX_TOKENS further
without also checking thinkingLevel is still set — an unset thinkingLevel
defaults to a heavier "medium" reasoning pass that will eat most of
whatever budget you give it.

Two layers:
    call_llm(prompt, ...)        — low-level: one API call, one prompt in, text out.
    generate_narrative(ctx, section) — high-level: builds the right grounded
                                        prompt for "threat_summary" /
                                        "root_cause" / "executive_summary"
                                        from the event's actual detected data.

GATING: the caller (playbook_generator.py / main.py) is responsible for
enforcing "never run unless final_risk_probability > 70" — this module does
not duplicate that check, to avoid two sources of truth for the same rule
silently drifting apart. It DOES refuse to run without a valid API key,
loudly rather than silently.

API KEY: reads GEMINI_API_KEY from the environment (never hardcoded). Get a
free key at https://aistudio.google.com/apikey (sign in with any Google
account, no card). If unset, call_llm() raises a clear EnvironmentError by
default. For development/testing without live API access, pass
mock_mode=True (or set SOC_LLM_MOCK_MODE=1) to get a deterministic,
clearly-labeled placeholder response instead of a real model call — this is
NOT a substitute for a live key in production, and every mock response is
prefixed so it can never be mistaken for real model output downstream.
"""

import os
import time

import requests

from utils import get_logger, require_env

logger = get_logger("llm_client")

GEMINI_API_URL_TEMPLATE = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"

# gemini-2.5-flash and gemini-2.5-flash-lite were confirmed dead (404 on
# every attempt) during live testing of this file on 2026-07-20; dropped
# from the chain rather than kept as guaranteed-fail dead weight. If
# gemini-3.5-flash also starts 404ing later, check
# https://ai.google.dev/gemini-api/docs/models for the current free-tier
# list and add the replacement to the FRONT of this list.
MODEL_FALLBACK_CHAIN = ["gemini-3.5-flash", "gemini-3-flash-preview"]
DEFAULT_MODEL = MODEL_FALLBACK_CHAIN[0]

# See "THINKING TOKENS" note above — this is not an arbitrary number, it's
# sized to leave headroom after "low"-level thinking consumes part of the
# budget. Confirmed directly: 800 was too low and caused MAX_TOKENS
# truncation on every real call; this value was NOT re-verified against a
# live key after raising it (no key available in this environment) —
# confirm the truncation warning is gone when you test with a real key.
MAX_TOKENS = 2048
THINKING_LEVEL = "low"  # "low" | "medium" | "high" — low is enough for short factual summaries
REQUEST_TIMEOUT_SECONDS = 60  # raised from 30s: thinking passes can be slow even at "low"
MOCK_PREFIX = "[MOCK LLM OUTPUT — SOC_LLM_MOCK_MODE=1, NOT A REAL MODEL RESPONSE] "

# Retry settings for transient API failures (timeouts, 429/503).
# Auth errors (401/403) are NOT retried — fail fast with the existing clear message.
RETRY_MAX_ATTEMPTS = 3
RETRY_BACKOFF_SECONDS = [1, 2, 4]  # exponential: 1s, 2s, 4s
RETRIABLE_STATUS_CODES = {429, 503}


def _mock_mode_enabled(explicit: bool = None) -> bool:
    if explicit is not None:
        return explicit
    return os.environ.get("SOC_LLM_MOCK_MODE", "").strip() in ("1", "true", "True")


def _is_retriable(exc: Exception) -> bool:
    """Return True for transient failures worth retrying (timeouts, 429/503).
    Auth errors (401/403) and other client errors are NOT retriable."""
    if isinstance(exc, (requests.exceptions.Timeout, requests.exceptions.ConnectionError)):
        return True
    if isinstance(exc, requests.exceptions.HTTPError) and exc.response is not None:
        return exc.response.status_code in RETRIABLE_STATUS_CODES
    return False


def _call_one_model(prompt: str, system_prompt: str, max_tokens: int, model: str, api_key: str) -> str:
    """Single attempt against one model, with retry/backoff for transient
    failures (timeouts, 429, 503). Auth errors (401/403) fail fast.
    Raises on any non-retriable failure — caller decides whether to fall
    back to the next model or give up."""
    payload = {
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": {
            "maxOutputTokens": max_tokens,
            "thinkingConfig": {"thinkingLevel": THINKING_LEVEL},
        },
    }
    if system_prompt:
        payload["system_instruction"] = {"parts": [{"text": system_prompt}]}

    url = GEMINI_API_URL_TEMPLATE.format(model=model)
    headers = {"x-goog-api-key": api_key, "Content-Type": "application/json"}

    # Retry loop for transient failures only
    last_exc = None
    for attempt in range(RETRY_MAX_ATTEMPTS):
        try:
            response = requests.post(
                url, headers=headers, json=payload,
                timeout=REQUEST_TIMEOUT_SECONDS,
            )
            response.raise_for_status()
            break  # success — proceed to parse
        except requests.exceptions.HTTPError as e:
            if not _is_retriable(e):
                raise  # 401/403/404 etc — fail fast, no retry
            last_exc = e
        except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
            last_exc = e

        # Transient failure — backoff and retry
        wait = RETRY_BACKOFF_SECONDS[min(attempt, len(RETRY_BACKOFF_SECONDS) - 1)]
        logger.warning(
            f"Transient error on attempt {attempt + 1}/{RETRY_MAX_ATTEMPTS} "
            f"for model '{model}': {last_exc}. Retrying in {wait}s..."
        )
        time.sleep(wait)
    else:
        # All retry attempts exhausted
        raise RuntimeError(
            f"All {RETRY_MAX_ATTEMPTS} retry attempts failed for model '{model}'. "
            f"Last error: {last_exc}"
        ) from last_exc

    data = response.json()

    block_reason = data.get("promptFeedback", {}).get("blockReason")
    if block_reason:
        raise RuntimeError(f"Gemini blocked this prompt (reason: {block_reason}) instead of returning a response.")

    candidates = data.get("candidates", [])
    if not candidates:
        raise RuntimeError(f"Gemini returned no candidates in the response: {data}")

    finish_reason = candidates[0].get("finishReason")
    parts = candidates[0].get("content", {}).get("parts", [])
    text = "".join(p.get("text", "") for p in parts)

    if finish_reason not in (None, "STOP"):
        if not text:
            # Truncated with nothing usable at all (e.g. thinking consumed
            # the entire budget) — this must fall back to the next model,
            # not return an empty string as if it succeeded.
            raise RuntimeError(
                f"Gemini response finished with reason '{finish_reason}' and produced no usable text "
                f"(likely maxOutputTokens too low for thinking + output combined)."
            )
        logger.warning(f"Gemini response finished with reason '{finish_reason}' — text may be truncated. Using it anyway since it's non-empty.")

    if not text:
        raise RuntimeError(f"Gemini returned an empty response (finishReason={finish_reason}): {data}")
    return text


def call_llm(prompt: str, system_prompt: str = None, max_tokens: int = MAX_TOKENS,
             model: str = None, mock_mode: bool = None) -> str:
    """
    Calls the Gemini API (generateContent). Raises EnvironmentError with a
    clear message if GEMINI_API_KEY isn't set and mock_mode isn't enabled —
    never silently proceeds with a fake key or skips the call without
    telling the caller.

    If `model` is not explicitly passed, tries every model in
    MODEL_FALLBACK_CHAIN in order and returns the first one that succeeds —
    this is what protects against a single retired/renamed model name
    breaking the whole pipeline (see MODEL_FALLBACK_CHAIN's comment for why
    this isn't hypothetical). Only raises if every model in the chain fails.
    """
    if _mock_mode_enabled(mock_mode):
        logger.warning("llm_client running in MOCK MODE — no real API call is being made.")
        return MOCK_PREFIX + f"(would have sent a {len(prompt)}-char prompt to {model or DEFAULT_MODEL})"

    api_key = require_env("GEMINI_API_KEY", "calling the Gemini API for playbook narrative generation")

    models_to_try = [model] if model else MODEL_FALLBACK_CHAIN
    last_error = None

    for candidate_model in models_to_try:
        try:
            text = _call_one_model(prompt, system_prompt, max_tokens, candidate_model, api_key)
            if candidate_model != models_to_try[0]:
                logger.warning(f"Fell back to model '{candidate_model}' after earlier model(s) in the chain failed.")
            return text
        except requests.exceptions.RequestException as e:
            logger.warning(f"Model '{candidate_model}' failed ({e}); trying next in fallback chain.")
            last_error = e
        except (KeyError, IndexError, RuntimeError) as e:
            logger.warning(f"Model '{candidate_model}' returned an unusable response ({e}); trying next in fallback chain.")
            last_error = e

    logger.error(f"All models in the fallback chain failed. Last error: {last_error}")
    raise RuntimeError(
        f"LLM call failed on every model tried ({models_to_try}). Last error: {last_error}. "
        f"Check https://ai.google.dev/gemini-api/docs/models for current free-tier model names "
        f"and update MODEL_FALLBACK_CHAIN in llm_client.py if all of these have been retired."
    ) from last_error


_SECTION_INSTRUCTIONS = {
    "threat_summary": (
        "Write a concise (3-5 sentence) Threat Summary for a SOC analyst, in plain "
        "professional language. State what was detected, how confident the detection is, "
        "and why it matters. Do not invent facts beyond the data provided below."
    ),
    "root_cause": (
        "Write a concise (3-5 sentence) Root Cause analysis explaining, based ONLY on the "
        "evidence provided (the SHAP feature contributions and event details), which "
        "specific signals most likely drove this detection and what that suggests about "
        "the underlying attack mechanism. Be explicit that this is a probable inference "
        "from the detection model's evidence, not a confirmed forensic finding."
    ),
    "executive_summary": (
        "Write a 3-4 sentence Executive Summary suitable for a non-technical leadership "
        "audience: what happened, potential business impact, and what the security team "
        "is doing about it. Avoid jargon."
    ),
}
_SYSTEM_PROMPT = (
    "You are a SOC (Security Operations Center) analyst assistant. Ground every statement "
    "strictly in the event data provided. Never invent IP addresses, CVEs, usernames, or "
    "facts not present in the input. If evidence is ambiguous, say so rather than guessing. "
    "Answer directly and concisely — do not include preamble, headers, or meta-commentary "
    "about the task itself."
)


def generate_narrative(prompt_context: dict, section: str, mock_mode: bool = None) -> str:
    """
    Generates one narrative section of the playbook.

    Args:
        prompt_context: dict with the event's key facts (risk scores, channel,
            top SHAP features, evidence text, etc.) — grounds the model in
            real detected data rather than letting it free-associate.
        section: "threat_summary" | "root_cause" | "executive_summary"
        mock_mode: passthrough to call_llm() for testing without a live key.

    Returns:
        Generated text.
    """
    instruction = _SECTION_INSTRUCTIONS.get(section, _SECTION_INSTRUCTIONS["threat_summary"])

    context_text = (
        f"Event data:\n"
        f"- risk_category: {prompt_context['risk_category']}\n"
        f"- final_risk_probability: {prompt_context['final_risk_probability']:.3f}\n"
        f"- anomaly_score: {prompt_context['anomaly_score']:.1f} / 100\n"
        f"- phishing_probability: {prompt_context['phishing_probability']:.3f}\n"
        f"- channel: {prompt_context['channel']}\n"
        f"- threat_category: {prompt_context['threat_category']}\n"
        f"- source_ip: {prompt_context['source_ip']}\n"
        f"- top_contributing_features (SHAP, ranked): {prompt_context['top_features']}\n"
        f"- evidence_text (raw content sample): {str(prompt_context.get('evidence_text', 'N/A'))[:300]}\n"
    )

    return call_llm(
        prompt=f"{instruction}\n\n{context_text}",
        system_prompt=_SYSTEM_PROMPT,
        mock_mode=mock_mode,
    )


if __name__ == "__main__":
    # Smoke test in mock mode — doesn't require a real API key, verifies the
    # gating/plumbing logic without incurring cost or requiring credentials.
    result = call_llm("Summarize this test threat event.", mock_mode=True)
    logger.info(f"Mock call_llm result: {result}")
    assert result.startswith(MOCK_PREFIX)

    sample_context = {
        "risk_category": "Critical", "final_risk_probability": 0.92, "anomaly_score": 88.0,
        "phishing_probability": 0.95, "channel": "email", "threat_category": "Phishing (Email)",
        "source_ip": "203.0.113.5", "top_features": ["burst_score", "failed_connection_rate"],
        "evidence_text": "URGENT verify your account now",
    }
    for section in ("threat_summary", "root_cause", "executive_summary"):
        text = generate_narrative(sample_context, section, mock_mode=True)
        assert text.startswith(MOCK_PREFIX)
        logger.info(f"[{section}] mock output OK")

    logger.info("llm_client.py self-tests passed (mock mode).")