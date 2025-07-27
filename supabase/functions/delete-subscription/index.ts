import { serve } from "https://deno.land/std@0.168.0/http/server.ts";
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2';

serve(async (req) => {
  if (req.method !== "DELETE") {
    return new Response("Method Not Allowed", { status: 405 });
  }

  const { subscription_id, user_id } = await req.json();

  // 1. Удалить подписку в AeroDataBox
  const aeroUrl = `https://aerodatabox.p.rapidapi.com/subscriptions/${subscription_id}`;
  const headers = {
    "X-RapidAPI-Key": Deno.env.get("AERODATABOX_API_KEY"),
    "X-RapidAPI-Host": "aerodatabox.p.rapidapi.com"
  };

  const aeroResp = await fetch(aeroUrl, { method: "DELETE", headers });
  if (!aeroResp.ok) {
    return new Response(JSON.stringify({ error: "AeroDataBox error", details: await aeroResp.text() }), { status: 400 });
  }

  // 2. Обновить статус в Supabase
  const supabase = createClient(Deno.env.get('SUPABASE_URL'), Deno.env.get('SUPABASE_SERVICE_ROLE_KEY'));
  const { error } = await supabase
    .from('flight_subscriptions')
    .update({ status: 'deleted' })
    .eq('subscription_id', subscription_id)
    .eq('user_id', user_id);

  if (error) {
    return new Response(JSON.stringify({ error: "DB error", details: error }), { status: 500 });
  }

  return new Response(JSON.stringify({ success: true }), { status: 200 });
}); 