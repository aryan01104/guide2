// Generate session name using OpenAI chat API
export async function generateSessionName(dominantType = "general") {
  if (!activities.length) return "Empty Session";

  const payload = activities.map((a) => ({
    timestamp: a.timestamp_start,
    duration_sec: a.duration_sec,
    details: a.details,
  }));

  const systemPrompt =
    "You are an expert at summarizing a series of user activities into a " +
    "concise session title. Each activity has a timestamp, duration, and details. " +
    "Return only a short (<5 words) session name that captures the main theme.";

  const userPrompt = `Activities (JSON):\n${JSON.stringify(
    payload,
    null,
    2
  )}\n\nDominant type: ${dominantType}\n\nGive me a one-line session name.`;

  const resp = await chat(
    [
      { role: "system", content: systemPrompt },
      { role: "user", content: userPrompt },
    ],
    { temperature: 0.0 }
  );

  return resp.choices?.[0]?.message?.content?.trim() || "Unnamed Session";
}

export async function addCommentaryToSession(
  sessionId,
  commentary,
  commentaryTime
) {
  const { data, error } = await supabase
    .from("activity_sessions")
    .update({
      commentary,
      commentary_time: commentaryTime,
    })
    .eq("id", sessionId);

  if (error) {
    console.error("[DATABASE] Error adding commentary:", error);
    throw error;
  }
}
