import { serve } from "https://deno.land/std@0.168.0/http/server.ts";

serve(async (req) => {
  if (req.method !== "GET") {
    return new Response("Method Not Allowed", { status: 405 });
  }

  const url = new URL(req.url);
  const subscription_id = url.searchParams.get("subscription_id");
  if (!subscription_id) {
    return new Response(JSON.stringify({ error: "subscription_id required" }), { status: 400 });
  }

  const aeroUrl = `https://aerodatabox.p.rapidapi.com/subscriptions/${subscription_id}`;
  const headers = {
    "X-RapidAPI-Key": Deno.env.get("AERODATABOX_API_KEY"),
    "X-RapidAPI-Host": "aerodatabox.p.rapidapi.com"
  };

  const aeroResp = await fetch(aeroUrl, { method: "GET", headers });
  const data = await aeroResp.json();

  return new Response(JSON.stringify(data), { status: aeroResp.status });
}); 