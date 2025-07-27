import { serve } from "https://deno.land/std@0.168.0/http/server.ts";

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type'
};

serve(async (req) => {
  // Handle CORS preflight requests
  if (req.method === 'OPTIONS') {
    return new Response('ok', { headers: corsHeaders });
  }

  try {
    const { telegram_id, message, parse_mode = 'HTML' } = await req.json();

    if (!telegram_id || !message) {
      return new Response(JSON.stringify({ error: 'telegram_id and message are required' }), {
        status: 400,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' }
      });
    }

    const bot_token = Deno.env.get('BOT_TOKEN');
    if (!bot_token) {
      return new Response(JSON.stringify({ error: 'BOT_TOKEN not configured' }), {
        status: 500,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' }
      });
    }

    // Send message to Telegram
    const telegram_url = `https://api.telegram.org/bot${bot_token}/sendMessage`;
    const telegram_payload = {
      chat_id: telegram_id,
      text: message,
      parse_mode: parse_mode
    };

    const response = await fetch(telegram_url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(telegram_payload)
    });

    const result = await response.json();

    if (response.ok && result.ok) {
      return new Response(JSON.stringify({ success: true, message_id: result.result.message_id }), {
        status: 200,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' }
      });
    } else {
      console.error('Telegram API error:', result);
      return new Response(JSON.stringify({ error: 'Failed to send Telegram message', details: result }), {
        status: 400,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' }
      });
    }

  } catch (error) {
    console.error('Error sending Telegram notification:', error);
    return new Response(JSON.stringify({ error: error.message }), {
      status: 500,
      headers: { ...corsHeaders, 'Content-Type': 'application/json' }
    });
  }
}); 