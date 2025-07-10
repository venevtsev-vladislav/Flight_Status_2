  import { serve } from "https://deno.land/std@0.168.0/http/server.ts"
  import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'

  const corsHeaders = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
  }

  interface FlightApiRequest {
    flight_number: string
    date: string
    user_id?: string
  }

  interface FlightApiResponse {
    success: boolean
    data?: any
    error?: string
  }

  serve(async (req) => {
    // Handle CORS preflight requests
    if (req.method === 'OPTIONS') {
      return new Response('ok', { headers: corsHeaders })
    }

    try {
      const { flight_number, date, user_id }: FlightApiRequest = await req.json()

      if (!flight_number || !date) {
        return new Response(
          JSON.stringify({ error: 'Flight number and date are required' }),
          { 
            status: 400, 
            headers: { ...corsHeaders, 'Content-Type': 'application/json' } 
          }
        )
      }

      // Get flight data from AeroDataBox API
      const flightData = await getAeroDataBoxFlightData(flight_number, date)

      // Save to database
      const supabase = createClient(
        Deno.env.get('SUPABASE_URL') ?? '',
        Deno.env.get('SUPABASE_ANON_KEY') ?? ''
      )

      // Get or create flight record
      let { data: flight } = await supabase
        .from('flights')
        .select('id')
        .eq('flight_number', flight_number)
        .eq('date', date)
        .single()

      if (!flight) {
        const { data: newFlight } = await supabase
          .from('flights')
          .insert({
            flight_number,
            date
          })
          .select('id')
          .single()
        flight = newFlight
      }

      // Save flight details
      await supabase
        .from('flight_details')
        .upsert({
          flight_id: flight.id,
          data_source: 'mock_api',
          raw_data: flightData,
          last_checked_at: new Date().toISOString()
        })

      // Log the API call
      if (user_id) {
        await supabase
          .from('audit_logs')
          .insert({
            user_id,
            action: 'flight_api_request',
            details: {
              flight_number,
              date,
              result: flightData
            }
          })
      }

      let message = '';
      let buttons: any[] = [];
      
      // Проверяем наличие ошибки в ответе API
      if (flightData && flightData.error) {
        if (flightData.error === 'api_error' && flightData.message?.includes('429')) {
          message = '🚦 Increased demand, I need a little more time to process';
        } else if (flightData.error === 'api_key_missing') {
          message = '🔧 Technical issue, our specialists are already solving';
        } else if (flightData.error === 'no_data') {
          message = '📋 Flight data is currently unavailable';
        } else {
          message = '🔌 Service temporarily unavailable';
        }
      } else if (Array.isArray(flightData) && flightData.length > 0) {
        if (flightData.length === 1) {
          message = formatTelegramMessage(flightData[0]);
        } else {
          const result = formatMultipleFlights(flightData);
          message = result.message;
          buttons = result.buttons;
        }
      } else if (flightData && typeof flightData === 'object') {
        message = formatTelegramMessage(flightData);
      } else {
        message = '⚠️ Sorry, could not find flight data.';
      }
      
      return new Response(
        JSON.stringify({
          success: true,
          data: flightData,
          message,
          buttons
        }),
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

  async function getAeroDataBoxFlightData(flight_number: string, date: string): Promise<any> {
    const apiKey = Deno.env.get('AERODATABOX_API_KEY')
    const apiHost = 'aerodatabox.p.rapidapi.com'
    
    if (!apiKey) {
      console.error('AERODATABOX_API_KEY not found in environment variables')
      return {
        error: 'api_key_missing',
        message: 'API key not configured'
      }
    }

    try {
      // Format date for API (YYYY-MM-DD)
      const formattedDate = new Date(date).toISOString().split('T')[0]
      
      // Call AeroDataBox Flight Status API
      const url = `https://${apiHost}/flights/number/${flight_number}/${formattedDate}?withAircraftImage=false&withLocation=false&dateLocalRole=Both`
      
      console.log(`Calling AeroDataBox API: ${url}`)
      
      const response = await fetch(url, {
        method: 'GET',
        headers: {
          'X-RapidAPI-Key': apiKey,
          'X-RapidAPI-Host': apiHost
        }
      })

      if (!response.ok) {
        console.error(`AeroDataBox API error: ${response.status} ${response.statusText}`)
        return {
          error: 'api_error',
          message: `API error: ${response.status}`
        }
      }

      const data = await response.json()
      
      console.log(`AeroDataBox API response status: ${response.status}`)
      console.log(`AeroDataBox API response data:`, JSON.stringify(data, null, 2))
      
      if (!data || (Array.isArray(data) && data.length === 0)) {
        return {
          error: 'no_data',
          message: 'No flight data found for this date'
        }
      }

      // Маппинг одного рейса
      const mapFlight = (flight: any) => ({
        greatCircleDistance: flight.greatCircleDistance || null,
        departure: flight.departure || null,
        arrival: flight.arrival || null,
        lastUpdatedUtc: flight.lastUpdatedUtc || null,
        number: flight.number || flight.flightNumber || null,
        status: flight.status || null,
        codeshareStatus: flight.codeshareStatus || null,
        isCargo: flight.isCargo || false,
        aircraft: flight.aircraft || null,
        airline: flight.airline || null,
        codeshares: flight.codeshares || [],
      });

      if (Array.isArray(data)) {
        return data.map(mapFlight)
      } else {
        return mapFlight(data)
      }
    } catch (error) {
      console.error('Error calling AeroDataBox API:', error)
      return {
        error: 'api_error',
        message: 'Failed to fetch flight data'
      }
    }
  } 

  function formatMultipleFlights(flights: any[]): { message: string, buttons: any[] } {
    if (!flights || flights.length === 0) {
      return {
        message: '⚠️ No flight data found.',
        buttons: getDefaultButtons()
      };
    }

    const lines: string[] = [];
    lines.push(`⚠️ Found ${flights.length} flight${flights.length > 1 ? 's' : ''} with number ${flights[0]?.number || ''}:
`);

    flights.forEach((flight, index) => {
      lines.push(formatTelegramMessage(flight, index + 1));
      if (index < flights.length - 1) lines.push('');
    });

    let buttons: any[] = [];
    if (flights.length > 1) {
      // Кнопки для выбора рейса
      buttons = flights.map((flight, index) => {
        const flightNumber = flight.number || '?';
        const schedDep = flight.departure?.scheduledTime?.local;
        const depTime = schedDep ? formatTimeHHMM(schedDep) : '--:--';
        return [{ text: `${flightNumber} | ${depTime}`, callback_data: `select_flight_${index}` }];
      });
    } else {
      // Обычные кнопки для одного рейса
      buttons = getDefaultButtons();
    }

    return {
      message: lines.join('\n'),
      buttons
    };
  }

  function formatTime12(dt: string | null): string | null {
    if (!dt) return null;
    try {
      const date = new Date(dt.replace(' ', 'T').replace(/([+-]\d{2}):(\d{2})$/, '$1$2'));
      let hours = date.getHours();
      const minutes = date.getMinutes();
      const ampm = hours >= 12 ? 'PM' : 'AM';
      hours = hours % 12;
      hours = hours ? hours : 12;
      const minStr = minutes < 10 ? '0' + minutes : minutes;
      return `${hours}:${minStr} ${ampm}`;
    } catch {
      return dt;
    }
  }

  function formatTimeHHMM(dt: string | null): string | null {
    if (!dt) return null;
    try {
      const date = new Date(dt.replace(' ', 'T').replace(/([+-]\d{2}):(\d{2})$/, '$1$2'));
      let hours = date.getHours();
      const minutes = date.getMinutes();
      const ampm = hours >= 12 ? 'PM' : 'AM';
      hours = hours % 12;
      hours = hours ? hours : 12;
      const hh = hours < 10 ? '0' + hours : '' + hours;
      const mm = minutes < 10 ? '0' + minutes : '' + minutes;
      return `${hh}:${mm} ${ampm}`;
    } catch {
      return dt;
    }
  }

  function getGateStatus(flight: any): { indicator: string, message: string } {
    const status = flight.status;
    const depSched = flight.departure?.scheduledTime?.local;
    const depRevised = flight.departure?.revisedTime?.local;
    
    // Если рейс уже вылетел или прилетел - гейт закрыт
    if (status === 'Departed' || status === 'Arrived' || status === 'GateClosed') {
      return { indicator: '🔴', message: 'boarding completed' };
    }
    
    // Если идет посадка
    if (status === 'Boarding') {
      return { indicator: '🟢', message: 'boarding in progress' };
    }
    
    // Если регистрация открыта, но посадка еще не началась
    if (status === 'CheckIn') {
      const departureTime = depRevised || depSched;
      if (departureTime) {
        const boardingTime = formatTime12(departureTime);
        return { indicator: '🟠', message: `boarding at ${boardingTime}` };
      }
      return { indicator: '🟠', message: 'boarding expected' };
    }
    
    // Если рейс задержан
    if (status === 'Delayed') {
      const departureTime = depRevised || depSched;
      if (departureTime) {
        const boardingTime = formatTime12(departureTime);
        return { indicator: '🟠', message: `boarding at ${boardingTime}` };
      }
      return { indicator: '🟠', message: 'boarding delayed' };
    }
    
    // Если рейс в пути или ожидается
    if (status === 'EnRoute' || status === 'Expected' || status === 'Approaching') {
      return { indicator: '🔴', message: 'gate closed' };
    }
    
    // По умолчанию - ожидается открытие
    const departureTime = depRevised || depSched;
    if (departureTime) {
      const boardingTime = formatTime12(departureTime);
      return { indicator: '🟠', message: `boarding at ${boardingTime}` };
    }
    
    return { indicator: '🟠', message: 'boarding expected' };
  }

  function getStatusIndicator(status: string): string {
    switch ((status || '').toLowerCase()) {
      case 'scheduled': return '⏳';
      case 'checkin': return '🟠';
      case 'boarding': return '🟢';
      case 'gateclosed': return '🔴';
      case 'departed': return '🛫';
      case 'enroute': return '✈️';
      case 'arrived': return '🛬';
      case 'delayed': return '⏰';
      case 'cancelled': return '❌';
      case 'diverted': return '⚠️';
      default: return '';
    }
  }

  function getCheckInIndicator(status: string): string {
    switch ((status || '').toLowerCase()) {
      case 'checkin': return '🟠';
      case 'boarding': return '🟢';
      case 'gateclosed': return '🔴';
      case 'departed': return '🔴';
      case 'enroute': return '🔴';
      case 'arrived': return '🔴';
      default: return '⏳';
    }
  }

  function getGateIndicator(status: string): string {
    switch ((status || '').toLowerCase()) {
      case 'boarding': return '🟢';
      case 'gateclosed': return '🔴';
      case 'departed': return '🔴';
      case 'enroute': return '🔴';
      case 'arrived': return '🔴';
      case 'checkin': return '🟠';
      default: return '⏳';
    }
  }

  function getBaggageIndicator(status: string): string {
    switch ((status || '').toLowerCase()) {
      case 'arrived': return '🟢';
      case 'delivered': return '🟢';
      case 'lastbag': return '🟡';
      case 'closed': return '🔴';
      default: return '';
    }
  }

  function formatTelegramMessage(flight: any, flightIndex?: number): string {
    if (!flight) return '⚠️ No flight data.';
    const lines: string[] = [];

    // Header
    if (typeof flightIndex === 'number') {
      lines.push(`Flight ${flightIndex}:`);
    }
    const flightNumber = flight.number || '';
    const depIata = flight.departure?.airport?.iata;
    const arrIata = flight.arrival?.airport?.iata;
    const depName = flight.departure?.airport?.name;
    const arrName = flight.arrival?.airport?.name;
    const schedDep = flight.departure?.scheduledTime?.local;
    const depTimeStr = schedDep ? formatTime12(schedDep) : '';
    const status = flight.status || '';
    const statusIndicator = getStatusIndicator(status);

    // Route
    let route = '';
    if (depIata && arrIata) {
      route = `${depIata}→${arrIata}`;
    } else if (depIata) {
      route = `${depIata}→${arrName || ''}`;
    } else if (arrIata) {
      route = `--→${arrIata}`;
    } else if (depName && arrName) {
      route = `${depName}→${arrName}`;
    } else if (depName) {
      route = `${depName}→`;
    } else if (arrName) {
      route = `→${arrName}`;
    }

    let header = `✈️ ${flightNumber}`;
    if (route) header += ` ${route}`;
    if (depTimeStr) header += ` ${depTimeStr}`;
    lines.push(header.trim());

    // Status (всегда в header)
    if (status) lines.push(`${statusIndicator} Status: ${status}`);

    // Departure block (только до вылета)
    const isAfterDeparture = ['departed', 'enroute', 'arrived', 'cancelled', 'diverted'].includes((status || '').toLowerCase());
    if (depIata || depName) {
      lines.push(`\n🛫 ${depIata || '--'} / ${depName || ''}`.trim());
      if (!isAfterDeparture) {
        if (flight.departure?.terminal) lines.push(`   🏢 Terminal: ${flight.departure.terminal}`);
        if (flight.departure?.checkInDesk) lines.push(`   ${getCheckInIndicator(status)} Check-in: ${flight.departure.checkInDesk}`);
        if (flight.departure?.gate) {
          lines.push(`   ${getGateIndicator(status)} Gate: ${flight.departure.gate} (${getGateStatus(flight).message})`);
        }
      }
      const depSched = flight.departure?.scheduledTime?.local;
      const depRevised = flight.departure?.revisedTime?.local;
      const depActual = flight.departure?.actualTime?.local;
      // Departure time logic
      if (depActual && depSched && depActual !== depSched) {
        lines.push(`   ⏰ Departure: ${formatTime12(depActual)} (was ${formatTime12(depSched)})`);
      } else if (depRevised && depSched && depRevised !== depSched) {
        lines.push(`   ⏰ Departure: ${formatTime12(depRevised)} (was ${formatTime12(depSched)})`);
      } else if (depSched) {
        lines.push(`   ⏰ Departure: ${formatTime12(depSched)}`);
      }
    }

    // Arrival block (после вылета)
    if (arrIata || arrName) {
      lines.push(`\n🛬 ${arrIata || '--'} / ${arrName || ''}`.trim());
      const arrSched = flight.arrival?.scheduledTime?.local;
      const arrActual = flight.arrival?.actualTime?.local;
      const arrExpected = flight.arrival?.predictedTime?.local;
      // Arrival time logic (по ТЗ)
      if (arrActual) {
        if (arrSched && arrActual !== arrSched) {
          lines.push(`   ⏰ Arrival: ${formatTime12(arrActual)} (was ${formatTime12(arrSched)})`);
        } else {
          lines.push(`   ⏰ Arrival: ${formatTime12(arrActual)}`);
        }
      } else if (arrExpected) {
        if (arrSched && arrExpected !== arrSched) {
          lines.push(`   🔮 Expected arrival: ${formatTime12(arrExpected)} (scheduled: ${formatTime12(arrSched)})`);
        } else {
          lines.push(`   🔮 Expected arrival: ${formatTime12(arrExpected)}`);
        }
      } else if (arrSched) {
        lines.push(`   ⏰ Arrival: ${formatTime12(arrSched)}`);
      }
      // Багаж только после вылета
      if (isAfterDeparture && flight.arrival?.baggageBelt) {
        // Если появится статус ленты — можно добавить getBaggageIndicator
        lines.push(`   🛄 Baggage: ${flight.arrival.baggageBelt} belt`);
      }
    }

    // Aircraft
    if (flight.aircraft?.model) lines.push(`\n✈️ Aircraft: ${flight.aircraft.model}`);
    // Airline
    if (flight.airline?.name) lines.push(`👨‍✈️ Airline: ${flight.airline.name}`);

    return lines.join('\n').replace(/\n{3,}/g, '\n\n').trim();
  }

  function getDefaultButtons() {
    return [
      [{ text: '🔄 Refresh', callback_data: 'refresh' }],
      [{ text: '🔔 Subscribe', callback_data: 'subscribe' }],
      [{ text: '🔍 New search', callback_data: 'new_search' }],
      [{ text: '🗂 My flights', callback_data: 'my_flights' }]
    ];
  } 