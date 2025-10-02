import OpenAI from "openai";

console.log('(1/3) [chat.js] chat.js module loaded.');

// Check if we are in a Deno environment (cloud) or Node.js (local)
const isDeno = typeof Deno !== 'undefined';

const openai = new OpenAI({
  apiKey: isDeno ? Deno.env.get("OPENAI_API_KEY") : process.env.OPENAI_API_KEY,
});



async function chat(messages, { fmt = null, temperature = 0 } = {}) {
  console.log('(2/3) [chat.js] Calling OpenAI API with messages:', messages);
  const responseFormat = fmt === "json" ? { type: "json_object" } : null;

  try {
    const response = await openai.chat.completions.create({
      model: (isDeno ? Deno.env.get("MODEL") : process.env.MODEL) || "gpt-4o-mini",
      messages,
      temperature,
      response_format: responseFormat,
    });
    console.log('(3/3) [chat.js] Successfully received response from OpenAI API.');
    return response;
  } catch (error) {
    console.error('[chat.js] Error calling OpenAI API:', error);
    throw error;
  }
}

export { chat };