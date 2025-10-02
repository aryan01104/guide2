import { chat } from "../llm/chat.js";

// NOTE: The following two functions were not updated as they were not part of the request.
// They might need adjustments to work correctly with the new logging and chat function.
export async function generateSessionName(dominantType = "general") {
  if (!activities.length) return "Empty Session";
  const payload = activities.map((a) => ({
    timestamp: a.timestamp_start,
    duration_sec: a.duration_sec,
    details: a.details,
  }));
  const systemPrompt =
    "You are an expert at summarizing a series of user activities into a concise session title. Each activity has a timestamp, duration, and details. Return only a short (<5 words) session name that captures the main theme.";
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
    .update({ commentary, commentary_time: commentaryTime })
    .eq("id", sessionId);
  if (error) {
    console.error("[DATABASE] Error adding commentary:", error);
    throw error;
  }
}

/**
 * Generates a personalized productivity score for a new activity.
 * The LLM first determines a general baseline score and then adjusts it based on the user's past corrections.
 *
 * @param {string} activityDetails - The details of the new activity to score.
 * @param {Array<Object>} userCorrectedData - An array of objects representing the user's feedback.
 *   Each object should have: { details: string, llm_score: number, user_corrected_score: number }
 * @returns {Promise<Object>} A promise that resolves to an object like { score: number, reasoning: string }.
 */
export async function generateActivityScore(
  activityDetails,
  userCorrectedData
) {
  console.log(
    '(1/4) [llm_helpers.js] Starting generateActivityScore for:", activityDetails'
  );

  const examples = userCorrectedData
    .map(
      (item) =>
        `Activity: "${item.details}"\nOriginal Score: ${item.llm_score}\nUser's Corrected Score: ${item.user_corrected_score}`
    )
    .join("\n---\n");

  const prompt = `
    You are an intelligent assistant that helps quantify user productivity.
    Your task is to provide a personalized productivity score by following two steps:
    1. First, use your general knowledge to determine a baseline productivity score for an activity.
    2. Second, adjust that baseline score based on the user's personal preferences, which are revealed in their past corrections below.

    The final score must be a single integer between -10 (highly unproductive) and +10 (highly productive).

    Here are examples of the user's past corrections. Analyze them to understand how their definition of productivity might differ from the norm:
    ---
    ${examples}
    ---

    Now, for the new activity below, first consider a general score, then adjust it based on the user's feedback history to produce a final, personalized score.

    New Activity: "${activityDetails}"

    You MUST respond with ONLY a valid JSON object with two keys: "score" (the final integer score) and "reasoning" (a brief, one-sentence explanation for your final score).
  `;

  console.log(
    "(2/4) [llm_helpers.js] Prompt constructed. Calling chat function."
  );

  try {
    const messages = [{ role: "user", content: prompt }];
    const response = await chat(messages, { fmt: "json" });
    console.log("(3/4) [llm_helpers.js] Received response from chat function.");

    const content = response.choices[0].message.content;
    const result = JSON.parse(content);

    console.log(
      "(4/4) [llm_helpers.js] Successfully parsed LLM response:",
      result
    );
    return result;
  } catch (error) {
    console.error("(5!/4) [llm_helpers.js] An error occurred:", error);
    return { score: 0, reasoning: "Failed to generate score due to an error." };
  }
}
