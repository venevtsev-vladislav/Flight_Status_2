import { serve } from "https://deno.land/std@0.168.0/http/server.ts";
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2';

serve(async (req) => {
  if (req.method !== "POST") {
    return new Response("Method Not Allowed", { status: 405 });
  }

  const { user_id, flight_number, flight_date, callback_url } = await req.json();

  // 1. Создать подписку в AeroDataBox
  const aeroUrl = `https://aerodatabox.p.rapidapi.com/subscriptions/webhook/FlightByNumber/${flight_number}`;
  const headers = {
    "X-RapidAPI-Key": Deno.env.get("AERODATABOX_API_KEY"),
    "X-RapidAPI-Host": "aerodatabox.p.rapidapi.com",
    "Content-Type": "application/json"
  };
  const body = JSON.stringify({ url: callback_url });

  const aeroResp = await fetch(aeroUrl, { method: "POST", headers, body });
  if (!aeroResp.ok) {
    return new Response(JSON.stringify({ error: "AeroDataBox error", details: await aeroResp.text() }), { status: 400 });
  }
  const aeroData = await aeroResp.json();
  const subscription_id = aeroData.id;

  // 2. Сохранить подписку в Supabase
  const supabase = createClient(Deno.env.get('SUPABASE_URL'), Deno.env.get('SUPABASE_ANON_KEY'));
  
  // Проверяем, существует ли уже подписка
  const { data: existing } = await supabase.from('flight_subscriptions')
    .select('id')
    .eq('user_id', user_id)
    .eq('flight_number', flight_number)
    .eq('flight_date', flight_date)
    .single();
  
  let result;
  if (existing) {
    // Обновляем существующую подписку
    result = await supabase.from('flight_subscriptions')
      .update({ subscription_id, status: 'active' })
      .eq('user_id', user_id)
      .eq('flight_number', flight_number)
      .eq('flight_date', flight_date);
  } else {
    // Создаем новую подписку
    result = await supabase.from('flight_subscriptions').insert({
      user_id, flight_number, flight_date, subscription_id, status: 'active'
    });
  }
  
  const { error } = result;

  if (error) {
    return new Response(JSON.stringify({ error: "DB error", details: error }), { status: 500 });
  }

  return new Response(JSON.stringify({ success: true, subscription_id }), { status: 200 });
}); 