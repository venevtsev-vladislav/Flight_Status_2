import { serve } from "https://deno.land/std@0.168.0/http/server.ts"
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
}

interface ParseRequest {
  text: string
  user_id?: string
}

interface ParseResponse {
  flight_number?: string
  date?: string
  confidence: number
  error?: string
}

serve(async (req) => {
  // Handle CORS preflight requests
  if (req.method === 'OPTIONS') {
    return new Response('ok', { headers: corsHeaders })
  }

  try {
    const { text, user_id }: ParseRequest = await req.json()

    if (!text) {
      return new Response(
        JSON.stringify({ error: 'Text is required' }),
        { 
          status: 400, 
          headers: { ...corsHeaders, 'Content-Type': 'application/json' } 
        }
      )
    }

    // Use regex parsing only (GPT temporarily disabled)
    const result = parseFlightRequest(text)
    console.log(`Parse request: input="${text}", result=`, JSON.stringify(result, null, 2))

    // Log the parsing attempt
    if (user_id) {
      const supabase = createClient(
        Deno.env.get('SUPABASE_URL') ?? '',
        Deno.env.get('SUPABASE_ANON_KEY') ?? ''
      )

      await supabase
        .from('audit_logs')
        .insert({
          user_id,
          action: 'parse_flight_request',
          details: {
            input_text: text,
            result: result,
            method: 'regex'
          }
        })
    }

    return new Response(
      JSON.stringify(result),
      { 
        status: 200, 
        headers: { ...corsHeaders, 'Content-Type': 'application/json' } 
      }
    )

  } catch (error) {
    return new Response(
      JSON.stringify({ error: error.message }),
      { 
        status: 500, 
        headers: { ...corsHeaders, 'Content-Type': 'application/json' } 
      }
    )
  }
})

async function parseFlightRequestWithGPT(text: string): Promise<ParseResponse | null> {
  const openaiKey = Deno.env.get('OPENAI_API_KEY')
  
  if (!openaiKey) {
    return null // Fallback to regex parsing
  }

  try {
    const response = await fetch('https://api.openai.com/v1/chat/completions', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${openaiKey}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        model: 'gpt-3.5-turbo',
        messages: [
          {
            role: 'system',
            content: 'Extract flight number and date from user input. Return only JSON with flight_number and date fields. Date should be in YYYY-MM-DD format. If no date found, use today. If no flight number found, return null for flight_number.'
          },
          {
            role: 'user',
            content: text
          }
        ],
        temperature: 0.1,
        max_tokens: 100
      })
    })

    if (!response.ok) {
      console.error('OpenAI API error:', response.status)
      return null
    }

    const data = await response.json()
    const content = data.choices[0]?.message?.content
    
    if (!content) {
      return null
    }

    try {
      const parsed = JSON.parse(content)
      return {
        flight_number: parsed.flight_number || undefined,
        date: parsed.date || undefined,
        confidence: 0.9
      }
    } catch (e) {
      console.error('Failed to parse GPT response:', e)
      return null
    }
  } catch (error) {
    console.error('GPT parsing error:', error)
    return null
  }
}

function parseFlightRequest(text: string): ParseResponse {
  const cleanText = text.toLowerCase().trim()
  
  // Flight number patterns: 2-3 letters + 1-4 digits
  const flightNumberPattern = /\b([a-z]{2,3}\d{1,4})\b/i
  const flightMatch = cleanText.match(flightNumberPattern)
  
  // Date patterns
  const todayPattern = /\b(today|сегодня|today|сегодня)\b/i
  const tomorrowPattern = /\b(tomorrow|завтра|tomorrow|завтра)\b/i
  const yesterdayPattern = /\b(yesterday|вчера|yesterday|вчера)\b/i
  const datePattern = /\b(\d{1,2}[\.\/\-]\d{1,2}[\.\/\-]\d{2,4})\b/
  const relativePattern = /\b(\d+)\s*(days?|дней?|дня?)\s*(ago|from now|назад|через)\b/i
  
  let flight_number: string | undefined
  let date: string | undefined
  let confidence = 0

  // Extract flight number
  if (flightMatch) {
    flight_number = flightMatch[1].replace(/\s+/g, '').toUpperCase()
    console.log(`Flight number parsing: match="${flightMatch[1]}", result="${flight_number}"`)
    confidence += 0.4
  }

  // Extract date
  if (todayPattern.test(cleanText)) {
    date = new Date().toISOString().split('T')[0]
    confidence += 0.3
  } else if (tomorrowPattern.test(cleanText)) {
    const tomorrow = new Date()
    tomorrow.setDate(tomorrow.getDate() + 1)
    date = tomorrow.toISOString().split('T')[0]
    confidence += 0.3
  } else if (yesterdayPattern.test(cleanText)) {
    const yesterday = new Date()
    yesterday.setDate(yesterday.getDate() - 1)
    date = yesterday.toISOString().split('T')[0]
    confidence += 0.3
  } else if (datePattern.test(cleanText)) {
    const dateMatch = cleanText.match(datePattern)
    if (dateMatch) {
      // Parse DD.MM.YYYY or DD/MM/YYYY format
      const dateStr = dateMatch[1].replace(/[\/\-]/g, '.')
      const parts = dateStr.split('.')
      if (parts.length === 3) {
        const day = parts[0].padStart(2, '0')
        const month = parts[1].padStart(2, '0')
        const year = parts[2].length === 2 ? '20' + parts[2] : parts[2]
        date = `${year}-${month}-${day}`
        console.log(`Date parsing: input="${dateMatch[1]}", parts=[${parts.join(', ')}], result="${date}"`)
        confidence += 0.3
      }
    }
  }

  // If we have both flight number and date, increase confidence
  if (flight_number && date) {
    confidence += 0.2
  }

  // If we have at least one piece of information, it's a valid request
  if (flight_number || date) {
    confidence = Math.max(confidence, 0.1)
  }

  return {
    flight_number,
    date,
    confidence
  }
} 