import { updateActivityScore } from "./crud_helpers.js";
import { generateActivityScore } from "./llm_helpers.js";

export async function setActivityScore(id, details) {
  // Provide an empty array for userCorrectedData as we don't have any yet.
  const scoreResult = await generateActivityScore(details, []);
  await updateActivityScore(id, scoreResult.score);
}
