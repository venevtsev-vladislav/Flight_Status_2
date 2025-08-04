import { serve } from "https://deno.land/std@0.168.0/http/server.ts"
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
}

interface FlightNotification {
  subscription: {
    id: string
    isActive: boolean
    subject: {
      type: string
      id: string
    }
  }
  flights: Array<{
    number: string
    status: string
    lastUpdatedUtc: string
    notificationSummary?: string
    notificationRemark?: string
    departure?: {
      airport: {
        iata: string
        name: string
      }
      scheduledTimeUtc: string
      actualTimeUtc?: string
      terminal?: string
      gate?: string
    }
    arrival?: {
      airport: {
        iata: string
        name: string
      }
      scheduledTimeUtc: string
      actualTimeUtc?: string
      terminal?: string
      gate?: string
      baggageBelt?: string
    }
  }>
}

serve(async (req) => {
  // Handle CORS preflight requests
  if (req.method === 'OPTIONS') {
    return new Response('ok', { headers: corsHeaders })
  }

  try {
    // Get Supabase client
    const supabaseUrl = Deno.env.get('SUPABASE_URL')!
    const supabaseAnonKey = Deno.env.get('SUPABASE_ANON_KEY')!
    const supabase = createClient(supabaseUrl, supabaseAnonKey)

    // Get notification data from AeroDataBox
    const notification: FlightNotification = await req.json()
    
    console.log('📡 Received webhook notification:', JSON.stringify(notification, null, 2))

    // Validate notification
    if (!notification.flights || notification.flights.length === 0) {
      console.log('❌ No flights in notification')
      return new Response(JSON.stringify({ error: 'No flights in notification' }), {
        status: 400,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' }
      })
    }

    const flight = notification.flights[0]
    const flightNumber = flight.number.replace(/\s+/g, '') // Remove spaces
    
    console.log(`🛫 Processing flight: ${flightNumber}, status: ${flight.status}`)

    // Get flight date from departure or arrival time
    let flightDate: string
    try {
      if (flight.departure?.scheduledTimeUtc) {
        flightDate = new Date(flight.departure.scheduledTimeUtc).toISOString().split('T')[0]
      } else if (flight.arrival?.scheduledTimeUtc) {
        flightDate = new Date(flight.arrival.scheduledTimeUtc).toISOString().split('T')[0]
      } else {
        // Fallback to current date if no valid time found
        flightDate = new Date().toISOString().split('T')[0]
      }
    } catch (error) {
      console.error('❌ Error parsing flight date:', error)
      // Fallback to current date
      flightDate = new Date().toISOString().split('T')[0]
    }

    // Get all users subscribed to this flight with their telegram_id
    const { data: subscriptions, error: subError } = await supabase
      .from('flight_subscriptions')
      .select(`
        user_id,
        users!inner(telegram_id)
      `)
      .eq('flight_number', flightNumber)
      .eq('flight_date', flightDate)
      .eq('status', 'active')

    if (subError) {
      console.error('❌ Error fetching subscriptions:', subError)
      return new Response(JSON.stringify({ error: 'Database error' }), {
        status: 500,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' }
      })
    }

    if (!subscriptions || subscriptions.length === 0) {
      console.log(`ℹ️ No active subscriptions for flight ${flightNumber} on ${flightDate}`)
      return new Response(JSON.stringify({ message: 'No subscriptions found' }), {
        status: 200,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' }
      })
    }

    console.log(`📱 Found ${subscriptions.length} subscriptions for flight ${flightNumber}`)

    // Format notification message
    const message = formatFlightNotification(flight)
    
    // Get Telegram bot token
    const botToken = Deno.env.get('BOT_TOKEN')
    if (!botToken) {
      console.error('❌ BOT_TOKEN not set')
      return new Response(JSON.stringify({ error: 'Bot token not configured' }), {
        status: 500,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' }
      })
    }

    // Send notifications to all subscribed users
    const notificationPromises = subscriptions.map(async (sub) => {
      const telegram_id = sub.users.telegram_id
      try {
        const response = await fetch(`https://api.telegram.org/bot${botToken}/sendMessage`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            chat_id: telegram_id,
            text: message,
            parse_mode: 'HTML'
          })
        })

        if (!response.ok) {
          const errorData = await response.json()
          console.error(`❌ Failed to send to user ${telegram_id}:`, errorData)
          return { success: false, user_id: telegram_id, error: errorData }
        }

        console.log(`✅ Notification sent to user ${telegram_id}`)
        return { success: true, user_id: telegram_id }
      } catch (error) {
        console.error(`❌ Error sending to user ${telegram_id}:`, error)
        return { success: false, user_id: telegram_id, error: error.message }
      }
    })

    const results = await Promise.all(notificationPromises)
    const successCount = results.filter(r => r.success).length
    const failureCount = results.filter(r => !r.success).length

    console.log(`📊 Notification results: ${successCount} sent, ${failureCount} failed`)

    // Log notification to audit
    await supabase.from('audit_logs').insert({
      action: 'flight_notification_sent',
      details: {
        flight_number: flightNumber,
        flight_date: flightDate,
        status: flight.status,
        subscribers_count: subscriptions.length,
        success_count: successCount,
        failure_count: failureCount
      }
    })

    return new Response(JSON.stringify({
      message: 'Notifications processed',
      sent: successCount,
      failed: failureCount,
      total: subscriptions.length
    }), {
      status: 200,
      headers: { ...corsHeaders, 'Content-Type': 'application/json' }
    })

  } catch (error) {
    console.error('❌ Webhook error:', error)
    return new Response(JSON.stringify({ error: 'Internal server error' }), {
      status: 500,
      headers: { ...corsHeaders, 'Content-Type': 'application/json' }
    })
  }
})

function formatFlightNotification(flight: any): string {
  const flightNumber = flight.number
  const status = flight.status
  const lastUpdated = new Date(flight.lastUpdatedUtc).toLocaleString('ru-RU', {
    timeZone: 'Europe/Moscow',
    hour: '2-digit',
    minute: '2-digit'
  })

  // Status emojis
  const statusEmoji = {
    'Unknown': '❓',
    'Expected': '⏳',
    'EnRoute': '✈️',
    'CheckIn': '📋',
    'Boarding': '🛂',
    'GateClosed': '🔒',
    'Departed': '✈️',
    'Delayed': '⏰',
    'Approaching': '🛬',
    'Arrived': '✅',
    'Canceled': '❌',
    'Diverted': '🔄'
  }

  const emoji = statusEmoji[status] || '📊'

  // Base message
  let message = `<b>${flightNumber}: ${status} ${emoji}</b>\n`
  message += `Updated: ${lastUpdated}\n\n`

  // Add specific details based on status
  switch (status) {
    case 'Boarding':
      if (flight.departure?.gate) {
        message += `Gate: ${flight.departure.gate}\n`
      }
      if (flight.departure?.terminal) {
        message += `Terminal: ${flight.departure.terminal}\n`
      }
      break

    case 'CheckIn':
      if (flight.departure?.gate) {
        message += `Gate: ${flight.departure.gate}\n`
      }
      if (flight.departure?.terminal) {
        message += `Terminal: ${flight.departure.terminal}\n`
      }
      break

    case 'Departed':
      if (flight.departure?.actualTimeUtc) {
        const actualTime = new Date(flight.departure.actualTimeUtc).toLocaleString('ru-RU', {
          timeZone: 'Europe/Moscow',
          hour: '2-digit',
          minute: '2-digit'
        })
        message += `Departed at ${actualTime}\n`
      }
      if (flight.arrival?.scheduledTimeUtc) {
        const arrivalTime = new Date(flight.arrival.scheduledTimeUtc).toLocaleString('en-US', {
          timeZone: 'Europe/Moscow',
          hour: '2-digit',
          minute: '2-digit'
        })
        message += `Arrival: ${arrivalTime}\n`
      }
      break

    case 'Arrived':
      if (flight.arrival?.actualTimeUtc) {
        const actualTime = new Date(flight.arrival.actualTimeUtc).toLocaleString('ru-RU', {
          timeZone: 'Europe/Moscow',
          hour: '2-digit',
          minute: '2-digit'
        })
        message += `Arrived at ${actualTime}\n`
      }
      if (flight.arrival?.gate) {
        message += `Gate: ${flight.arrival.gate}\n`
      }
      if (flight.arrival?.terminal) {
        message += `Terminal: ${flight.arrival.terminal}\n`
      }
      if (flight.arrival?.baggageBelt) {
        message += `Baggage belt: ${flight.arrival.baggageBelt}\n`
      }
      break

    case 'Delayed':
      if (flight.departure?.scheduledTimeUtc && flight.departure?.actualTimeUtc) {
        const scheduled = new Date(flight.departure.scheduledTimeUtc)
        const actual = new Date(flight.departure.actualTimeUtc)
        const delayMinutes = Math.round((actual.getTime() - scheduled.getTime()) / (1000 * 60))
        message += `Delay: ${delayMinutes} minutes\n`
        message += `New time: ${actual.toLocaleString('en-US', {
          timeZone: 'Europe/Moscow',
          hour: '2-digit',
          minute: '2-digit'
        })}\n`
      }
      if (flight.departure?.gate) {
        message += `Выход: ${flight.departure.gate}\n`
      }
      if (flight.departure?.terminal) {
        message += `Терминал: ${flight.departure.terminal}\n`
      }
      break

    case 'Approaching':
      if (flight.arrival?.scheduledTimeUtc) {
        const arrivalTime = new Date(flight.arrival.scheduledTimeUtc).toLocaleString('ru-RU', {
          timeZone: 'Europe/Moscow',
          hour: '2-digit',
          minute: '2-digit'
        })
        message += `Arrival: ${arrivalTime}\n`
      }
      if (flight.arrival?.gate) {
        message += `Gate: ${flight.arrival.gate}\n`
      }
      if (flight.arrival?.terminal) {
        message += `Terminal: ${flight.arrival.terminal}\n`
      }
      break

    default:
      // For other statuses show available information
      if (flight.departure?.gate) {
        message += `Gate: ${flight.departure.gate}\n`
      }
      if (flight.departure?.terminal) {
        message += `Terminal: ${flight.departure.terminal}\n`
      }
      if (flight.arrival?.baggageBelt) {
        message += `Лента багажа: ${flight.arrival.baggageBelt}\n`
      }
      break
  }

  // Add remark if available
  if (flight.notificationRemark) {
    message += `\n${flight.notificationRemark}`
  }

  return message
} 