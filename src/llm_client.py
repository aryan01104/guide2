#!/usr/bin/env python3
# ─── Thin Chat Completions Wrapper ───────────────────────────────────────────

import openai          # OpenAI Python SDK for API calls
import json            # For processing JSON payloads
from config import OPENAI_KEY, MODEL, ROOT  # Project-specific settings

# ─── API Key Configuration ──────────────────────────────────────────────────
# Set the OpenAI API key for authentication
openai.api_key = OPENAI_KEY

# ─── Load Persona Digest ─────────────────────────────────────────────────────
# Read the persona digest template once at import time to avoid repeated disk I/O
PERSONA_DIGEST = (ROOT / "resources/persona_digest.txt").read_text()


def chat(messages, *, fmt=None, temperature=0):
    """
    Send a list of messages to OpenAI's Chat Completions endpoint.

    Args:
      messages (list of dict): conversation history, each with 'role' and 'content'.
      fmt (str, optional): if 'json', request the response as a strict JSON object.
      temperature (float): controls randomness (0 = deterministic).

    Returns:
      OpenAI API response object containing the model's reply.
    """
    # Build optional response_format parameter for JSON output
    response_format = {"type": "json_object"} if fmt == "json" else None

    # Call the Chat Completions API
    return openai.chat.completions.create(
        model=MODEL,              # which model to use (e.g., "gpt-4")
        messages=messages,        # the conversation messages
        temperature=temperature,  # randomness control
        response_format=response_format,
    )
