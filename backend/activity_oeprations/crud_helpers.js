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
export async function updateActivityScore(
  id,
  productivity_score,
  user_provided
) {
  const { data, error } = await supabase
    .from("activity_logs")
    .update({
      productivity_score: productivity_score,
      user_provided: user_provided,
    }) // if user_provided then so, else false
    .eq("id", id)
    .select()
    .single();

  if (error) {
    console.error(
      "[operations.crud_helpers.uAS] Error updating activity scores:",
      error
    );
    throw error;
  }
}
