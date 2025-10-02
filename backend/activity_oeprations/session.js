import supabase from "../supabase-client.js";
import { chat } from "../helpers/operations_helpers.js";
import {
  calculateSessionScoreAndTime,
  fetchActivityLogsByIdRange,
} from "./helpers.js";
import { addCommentaryToSession, generateSessionName } from "./llm_helpers.js";

// to be called once we decide the window for sessions, the window must be sessions (BACK)
export async function colourAndPersistSession(
  activity_id_start,
  activity_id_end
) {
  let activity_rows;

  try {
    activity_rows = await fetchActivityLogsByIdRange(
      activity_id_start,
      activity_id_end
    );
  } catch (e) {
    console.error("[SESSION] Error fetching activity logs:", e);
  }

  let sessionScore, duration, sessionName;

  try {
    [sessionScore, duration] = calculateSessionScoreAndTime(activity_rows);
    sessionName = await generateSessionName(activity_rows);
    //TODO: add commentary generation here
    //NOTE: should the code here be moved into what chatgpt was calling the api file? since this is calling llm logic. this is the delegating function...
  } catch (e) {
    console.error(
      "[SESSION_GENERATION] Error generating session attributes:",
      e
    );
  }

  const { data, error } = await supabase
    .from("activity_sessions")
    .insert([
      {
        session_name: sessionName,
        productivity_score: sessionScore,
        start_id: activity_id_start,
        end_id: activity_id_end,
        total_duration_sec: duration,
        // TODO: input commentary argument here
        is_displayed: true,
      },
    ])
    .select()
    .single();

  if (error) {
    console.error("[DB] Error saving session:", error);
  } else {
    console.log(
      `[DATABASE] Saved session: ${sessionName} (score: ${sessionScore}, ${Math.floor(
        duration / 60
      )}min)`
    );
    return data.id;
  }
}

// probably a web call (FRONT)
export async function getSessionsByDate(date = null) {
  if (!date) date = new Date();
  const startOfDay = new Date(date);
  startOfDay.setHours(0, 0, 0, 0);
  const endOfDay = new Date(date);
  endOfDay.setHours(23, 59, 59, 999);

  const { data, error } = await supabase
    .from("activity_sessions")
    .select()
    .gte("start_time", startOfDay.toISOString())
    .lte("start_time", endOfDay.toISOString())
    .order("start_time", { ascending: true });

  if (error) {
    console.error("[DATABASE] Error fetching sessions by date:", error);
    throw error;
  }

  return data;
}

// probably a web call (FRONT)
export async function getSessionActivities(sessionId) {
  const { data, error } = await supabase
    .from("activity_logs")
    .select()
    .eq("session_id", sessionId)
    .order("timestamp_start", { ascending: true });

  if (error) {
    console.error("[DATABASE] Error fetching activities by session:", error);
    throw error;
  }

  return data;
}

// Helper function equivalents like find_smart_sessionization_ranges and calculate_processing_bounds
// would also be rewritten similarly, but omitted here for brevity.
