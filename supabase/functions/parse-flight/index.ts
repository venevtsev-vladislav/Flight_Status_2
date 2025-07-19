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

    // Use improved regex parsing
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
            method: 'improved_regex'
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

function parseFlightRequest(text: string): ParseResponse {
  // Нормализуем пробелы и разделители (пробелы, табы, запятые, точки с запятой)
  const cleanText = text
    .toLowerCase()
    .replace(/[\s,;]+/g, ' ')
    .replace(/\s{2,}/g, ' ')
    .trim();
  console.log(`Normalized input: "${cleanText}"`);
  
  // Enhanced flight number patterns
  // Matches: AA8242, AA 8242, AA-8242, SU100, SU 100, SU-100
  // Also handles: aa8242, aa 8242, etc.
  const flightNumberPatterns = [
    /\b([a-z]{2,3})\s*(\d{1,5})\b/i,  // AA 8242, SU 100
    /\b([a-z]{2,3})-(\d{1,5})\b/i,    // AA-8242, SU-100
    /\b([a-z]{2,3})(\d{1,5})\b/i      // AA8242, SU100
  ]
  
  // Enhanced date patterns with multi-language support
  const todayPattern = /\b(today|сегодня|сегодня|today)\b/i
  const tomorrowPattern = /\b(tomorrow|завтра|завтра|tomorrow)\b/i
  const yesterdayPattern = /\b(yesterday|вчера|вчера|yesterday)\b/i
  const datePatterns = [
    /\b(\d{1,2})[\.,\/\-](\d{1,2})[\.,\/\-](\d{2,4})\b/,  // DD.MM.YYYY, DD/MM/YYYY, DD-MM-YYYY, DD,MM,YYYY
    /\b(\d{4})[\.,\/\-](\d{1,2})[\.,\/\-](\d{1,2})\b/,    // YYYY.MM.DD, YYYY/MM/DD, YYYY-MM-DD, YYYY,MM,DD
    /\b(\d{1,2})\s+(\d{1,2})\s+(\d{2,4})\b/             // DD MM YYYY
  ]
  
  let flight_number: string | undefined
  let date: string | undefined
  let confidence = 0

  // Extract flight number using multiple patterns
  for (const pattern of flightNumberPatterns) {
    const flightMatch = cleanText.match(pattern)
    if (flightMatch) {
      const airlineCode = flightMatch[1].toUpperCase()
      const flightNum = flightMatch[2]
      flight_number = airlineCode + flightNum
      console.log(`Flight number parsing: airline="${airlineCode}", number="${flightNum}", result="${flight_number}"`)
      confidence += 0.4
      break // Use first match
    }
  }

  // Extract date
  if (todayPattern.test(cleanText)) {
    date = new Date().toISOString().split('T')[0]
    console.log(`Date parsing: found "today", result="${date}"`)
    confidence += 0.3
  } else if (tomorrowPattern.test(cleanText)) {
    const tomorrow = new Date()
    tomorrow.setDate(tomorrow.getDate() + 1)
    date = tomorrow.toISOString().split('T')[0]
    console.log(`Date parsing: found "tomorrow", result="${date}"`)
    confidence += 0.3
  } else if (yesterdayPattern.test(cleanText)) {
    const yesterday = new Date()
    yesterday.setDate(yesterday.getDate() - 1)
    date = yesterday.toISOString().split('T')[0]
    console.log(`Date parsing: found "yesterday", result="${date}"`)
    confidence += 0.3
  } else {
    // Try different date patterns
    for (const pattern of datePatterns) {
      const dateMatch = cleanText.match(pattern)
      if (dateMatch) {
        let day, month, year
        
        if (dateMatch[1].length === 4) {
          // YYYY.MM.DD format
          year = dateMatch[1]
          month = dateMatch[2].padStart(2, '0')
          day = dateMatch[3].padStart(2, '0')
        } else {
          // DD.MM.YYYY format
          day = dateMatch[1].padStart(2, '0')
          month = dateMatch[2].padStart(2, '0')
          year = dateMatch[3].length === 2 ? '20' + dateMatch[3] : dateMatch[3]
        }
        
        date = `${year}-${month}-${day}`
        console.log(`Date parsing: input="${dateMatch[0]}", parts=[${day}, ${month}, ${year}], result="${date}"`)
        confidence += 0.3
        break // Use first match
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