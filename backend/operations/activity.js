import supabase from "../../supabase-client.js";

// const [newActivityLog, setNewActivityLog] = useState({
//   timestamp_start: "", // or new Date().toISOString() if you want default current time as ISO string
//   details: "",
//   duration_sec: 0,
//   productivity_score: null,
//   user_provided: false,
// });

// C for Create: from all activty log details -> logs into SB (BACK)
export async function addActivityLog({
  timestamp_start,
  details,
  duration_sec,
  productivity_score = null,
  user_provided = false,
}) {
  const { data, error } = await supabase
    .from("activity_logs")
    .insert([
      {
        timestamp_start,
        details,
        duration_sec,
        productivity_score,
        user_provided,
      },
    ])
    .select()
    .single();

  if (error) {
    console.log("[operations.acitvity] Error adding activity log:", error);
  }

  return data;
}

// U for Update: only score is updatable, called from user interaction (FRONT)
export async function updateActivityScore(id, productivity_score, session_id) {
  const { data, error } = await supabase
    .from("activity_logs")
    .update({ productivity_score: productivity_score, user_provided: true })
    .eq("id", id)
    .select()
    .single();

  if (error) {
    console.error(
      "[operations.acitvity] Error updating activity scores:",
      error
    );
    throw error;
  }

  //   const { data_2, error_2} = await supabase
  //     .from("activity_session")
  //     .eq("id", session_id )
  //     .select()
  //     .single();

  //   if (error_2) {
  //     console.error("[operations.acitvity] Error fetching session for activty:", error_2);
  //   } else (
  //     if (!data_2.is_displayed){
  //         //
  //     }

  // Call session score recalculation separately if needed
  // await recalculateSessionScoresForActivity(data.timestamp_start);
}

// R for Read: returns activitiesBySesion, to be used by components for displaying sessions in window (FRONT)
export async function getActivitiesBySession(session_id) {
  if (!session_id) {
    throw new Error("Session ID is required");
  }

  const { data, error } = await supabase
    .from("activity_logs")
    .select()
    .eq("session_id", session_id)
    .order("timestamp_start", { ascending: true });

  if (error) {
    console.error(
      "[operations.activity] Error fetching activities by session:",
      error
    );
    throw error;
  }

  return data;
}
