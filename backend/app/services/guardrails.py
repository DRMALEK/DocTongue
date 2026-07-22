"""Input guardrails that block prompt-injection and restricted-topic requests.

Pattern matching is intentionally conservative: false positives are preferred
over letting policy-bypass or explicit-content requests through.
"""

import re


SYSTEM_PROMPT_OVERRIDE_PATTERNS = (
    re.compile(
        r"\b(ignore|disregard|forget)\b.{0,120}\b(previous|prior|earlier)\b.{0,120}\b(instruction|instructions|prompt|system)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(show|reveal|print|display|tell)\b.{0,120}\b(system prompt|hidden prompt|developer prompt|internal instructions?)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(jailbreak|bypass|override)\b.{0,80}\b(safety|guardrail|policy|restriction)\b",
        re.IGNORECASE,
    ),
)

RESTRICTED_TOPIC_PATTERN = re.compile(
    r"\b(nude|nudity|naked|porn|pornography|sexual|erotic|nsfw)\b",
    re.IGNORECASE,
)


def validate_chat_question(question: str) -> str | None:
    """Check *question* against safety guardrails.

    Args:
        question: The raw user question string.

    Returns:
        A human-readable rejection reason if the question violates a guardrail,
        or ``None`` if the question is acceptable.
    """
    for pattern in SYSTEM_PROMPT_OVERRIDE_PATTERNS:
        if pattern.search(question):
            return "This request is blocked by safety guardrails."

    if RESTRICTED_TOPIC_PATTERN.search(question):
        return "This topic is not supported by this assistant."

    return None