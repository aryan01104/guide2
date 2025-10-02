import { createClient } from "@supabase/supabase-js";

// Check if we are in a Deno environment (cloud) or Node.js (local)
const isDeno = typeof Deno !== 'undefined';

const supabaseUrl = isDeno ? Deno.env.get("SUPABASE_URL") : process.env.SUPABASE_URL;

// In the cloud, use the powerful service role key. Locally, use the public anon key.
const supabaseKey = isDeno ? Deno.env.get("SUPABASE_SERVICE_ROLE_KEY") : process.env.SUPABASE_KEY;

const supabase = createClient(supabaseUrl, supabaseKey);

export default supabase;
