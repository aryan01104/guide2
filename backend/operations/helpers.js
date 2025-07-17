// activity_rows -> session prod_score
export function calculateSessionScoreAndTime(activty_rows) {
  let totalWeightedScore = 0;
  let totalDuration = 0;
  for (const a of activity_rows) {
    totalWeightedScore += (a.productivity_score || 0) * a.duration_sec;
    totalDuration += a.duration_sec;
  }
  if (totalDuration === 0) {
    console.log(
      "[operations/helpers] a session with duration was created. check session creation logic"
    );
  }
  return [Math.round(totalWeightedScore / totalDuration), totalDuration];
}

/**
 * thought process
 * - can I use start id and end id
 *  -> what about deleted id's
 *      -> can we just skip over the ones that are missing bc because we wont repeat them?
 *    !!!!!!     -> :) yep I think we can just use start and end id. and if we change activty we can change the session score.
 *
 */

export async function fetchActivityLogsByIdRange(startId, endId) {
  if (startId > endId) [startId, endId] = [endId, startId]; // normalize order

  const { data, error } = await supabase
    .from("activity_logs")
    .select()
    .gte("id", startId)
    .lte("id", endId)
    .order("id", { ascending: true });

  if (error) {
    console.error(
      `[DATABASE] Error fetching activity logs by ID range ${startId}-${endId}:`,
      error
    );
    throw error;
  }

  return data;
}
