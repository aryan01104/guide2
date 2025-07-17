try:
    from ..helpers.operations_helpers import PERSONA_DIGEST, chat
except ImportError:
    from backend.helpers.operations_helpers import PERSONA_DIGEST, chat


def generate_transition_commentary(
    prev_session_meta,
    prev_activities,
    new_session_meta,
    new_activities,
    persona_digest=PERSONA_DIGEST,
    user_traits=None,
):
    """
    Generates a context-aware philosophical commentary on session transitions.

    prev_session_meta: dict with info about previous session (or None if none).
    prev_activities: list of activities from previous session.
    new_session_meta: dict with info about new session.
    new_activities: list of activities from new session.
    persona_digest: the book-extracted value system.
    user_traits: optional, dict with user traits or behavior patterns.
    """

    # --- EARLY EXIT for empty previous session ---
    if not prev_session_meta and not prev_activities:
        return ""

    # Summarize previous and new contexts for the prompt
    def summarize(meta, acts):
        if not meta:
            return "No prior session (blank context)."
        activity_str = ", ".join(
            f"{a.details} ({a.duration_sec // 60}m)" for a in acts[:3]
        )
        return f"Session type: {meta.get('session_type', 'unknown')} | Activities: {activity_str or 'none'} | Duration: {meta.get('duration', 0) // 60} min"

    prev_summary = (
        summarize(prev_session_meta, prev_activities)
        if prev_session_meta
        else "No previous session."
    )
    new_summary = summarize(new_session_meta, new_activities)

    # (Optional) User traits/notes
    user_traits_note = ""
    if user_traits:
        user_traits_note = "User traits: " + ", ".join(
            f"{k}: {v}" for k, v in user_traits.items()
        )

    # Main prompt construction
    prompt = (
        "You are a philosophical productivity commentator. Your worldview, language, and judgements must be deeply shaped by the following value system:\n"
        f"{persona_digest}\n\n"
        "Your task: When a user transitions between two contexts (such as from an unproductive session to a productive session, or vice versa), you must:\n"
        "- Briefly describe the prior context.\n"
        "- Note what has changed in the new context.\n"
        "- Offer an observation, critique, or praise based on the book's core values and tone. Use signature terms, attitudes, and personality from the persona digest.\n"
        "- If improvement: Reinforce with lessons/terms from the book.\n"
        "- If backslide: Call out avoidance, rationalization, or whatever the book would condemn. Be honest, not encouraging for its own sake.\n"
        "- End with one actionable challenge, framed in the author’s style, for the user to carry forward.\n"
        "- Avoid generic praise or empty motivational language. Make every sentence reflect the book’s philosophy.\n"
        f"{user_traits_note}\n\n"
        f"---\nPrevious session:\n{prev_summary}\n\nNew session:\n{new_summary}\n---"
    )

    resp = chat([{"role": "system", "content": prompt}], temperature=0.6)
    return resp.choices[0].message.content.strip()
