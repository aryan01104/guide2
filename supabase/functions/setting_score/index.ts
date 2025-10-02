
import { serve } from "https://deno.land/std@0.168.0/http/server.ts";
import { setActivityScore } from "../../../backend/operations/activity.js";

serve(async (req) => {
  try {
    const { record: activity } = await req.json();

    if (!activity || !activity.id || !activity.details) {
      return new Response(
        JSON.stringify({ error: "Invalid activity log provided." }),
        {
          status: 400,
          headers: { "Content-Type": "application/json" },
        }
      );
    }

    await setActivityScore(activity.id, activity.details);

    return new Response(JSON.stringify({ success: true }), {
      headers: { "Content-Type": "application/json" },
    });
  } catch (error) {
    console.error("Error processing activity:", error);
    return new Response(JSON.stringify({ error: "Internal Server Error" }), {
      status: 500,
      headers: { "Content-Type": "application/json" },
    });
  }
});
