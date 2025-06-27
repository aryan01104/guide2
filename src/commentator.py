from .user_config import load_user_config
from .llm_client import chat, PERSONA_DIGEST
from .config import COMMENT_STYLE

SYSTEM_COMMENTARY_INSTRUCTION = """
You are a productivity commentator for a highly motivated, analytically-minded user.
Base your commentary on the specific time allocation data provided.
- Connect activities to the user's stated main goal, side interests, and philosophical values.
- If there are moments of distraction or switching to less-productive activities, reflect on why that might have happened (e.g., avoidance, curiosity, frustration), using concepts like “bad faith” or “authentic engagement.”
- Give one clear, actionable suggestion for the next session—something concrete the user can do.
- Finish with a targeted reflective question about the user's choices today.
Avoid generic praise and vague statements. Analyze, synthesize, and offer actionable next steps with philosophical reflection.
""" + PERSONA_DIGEST + "\n\n" + COMMENT_STYLE

def comment(summary):
    config = load_user_config()
    bullets = ""
    for lens, total, acts in summary:
        acts_str = ", ".join(f"{a} ({int(m)}m)" for a, m in acts)
        bullets += f"• {lens} ({int(total)} min): {acts_str}\n"

    user_msg = (
        f"User profile: {config['profession']} working on {config['main_goal']}.\n"
        f"Side interests: {config['side_aims']}.\n"
        f"Breaks: {', '.join(config['break_activities'])}.\n"
        "Last 2-hour breakdown of your time:\n"
        f"{bullets.strip()}"
    )

    print("[COMMENTATOR] Generating commentary with user context and activities.")
    resp = chat(
        [
            {"role": "system", "content": SYSTEM_COMMENTARY_INSTRUCTION},
            {"role": "user", "content": user_msg}
        ],
        temperature=0.6
    )
    print("[COMMENTATOR] Commentary generated.")
    return resp.choices[0].message.content.strip()
