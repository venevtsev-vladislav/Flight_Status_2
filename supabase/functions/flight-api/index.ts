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
    date_local_role?: string
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
      const { flight_number, date, user_id, date_local_role }: FlightApiRequest = await req.json()

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
      const flightData = await getAeroDataBoxFlightData(flight_number, date, date_local_role)

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
        // Check if requested flight is in codeshares
        const returnedFlight = flightData[0];
        const returnedNumber = (returnedFlight.number || '').replace(/\s/g, '');
        const requestedNumber = flight_number.replace(/\s/g, '');
        
        // Check if this is a codeshare situation
        const isCodeshare = returnedFlight.codeshareStatus === 'IsOperator' || 
                           returnedFlight.codeshareStatus === 'IsCodeshare' ||
                           returnedNumber !== requestedNumber;
        
        if (isCodeshare) {
          // Handle codeshare situation
          if (returnedNumber !== requestedNumber) {
            // Different flight number returned - add requested flight as codeshare
            const codeshares = returnedFlight.codeshares || [];
            if (!codeshares.includes(flight_number)) {
              codeshares.push(flight_number);
            }
            returnedFlight.codeshares = codeshares;
            
            // Add note about codeshare
            returnedFlight.codeshareNote = `Also flies as: ${requestedNumber}`;
            
            console.log(`Codeshare detected: Requested ${requestedNumber}, operating as ${returnedNumber}`);
          }
        }
        
        if (flightData.length === 1) {
          message = formatTelegramMessage(flightData[0]);
        } else {
          const result = formatMultipleFlights(flightData, date);
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

  function getDefaultButtons() {
    return [
      [{ text: '🔄 Refresh', callback_data: 'refresh' }],
      [{ text: '🔔 Subscribe', callback_data: 'subscribe' }],
      [{ text: '🔍 New search', callback_data: 'new_search' }],
      [{ text: '🗂 My flights', callback_data: 'my_flights' }]
    ];
  }

  async function getAeroDataBoxFlightData(flight_number: string, date: string, date_local_role?: string): Promise<any> {
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
      const url = `https://${apiHost}/flights/number/${flight_number}/${formattedDate}?withAircraftImage=false&withLocation=false&dateLocalRole=${date_local_role || 'Both'}`
      
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
        departure: {
          airport: flight.departure?.airport || null,
          scheduledTime: flight.departure?.scheduledTime || null,
          actualTime: flight.departure?.actualTime || null,
          revisedTime: flight.departure?.revisedTime || null,
          terminal: flight.departure?.terminal || null,
          gate: flight.departure?.gate || null,
          checkInDesk: flight.departure?.checkInDesk || null
        },
        arrival: {
          airport: flight.arrival?.airport || null,
          scheduledTime: flight.arrival?.scheduledTime || null,
          actualTime: flight.arrival?.actualTime || null,
          revisedTime: flight.arrival?.revisedTime || null,
          predictedTime: flight.arrival?.predictedTime || null,
          terminal: flight.arrival?.terminal || null,
          gate: flight.arrival?.gate || null,
          baggageBelt: flight.arrival?.baggageBelt || null
        },
        lastUpdatedUtc: flight.lastUpdatedUtc || null,
        number: flight.number || flight.flightNumber || null,
        status: flight.status || null,
        codeshareStatus: flight.codeshareStatus || null,
        isCargo: flight.isCargo || false,
        aircraft: flight.aircraft || null,
        airline: flight.airline || null,
        codeshares: flight.codeshares || [],
      });

      // Log mapped flight data to see what we get after mapping
      if (Array.isArray(data) && data.length > 0) {
        const mappedFlight = mapFlight(data[0]);
        console.log(`Mapped flight data:`, JSON.stringify(mappedFlight, null, 2));
        console.log(`Departure terminal:`, mappedFlight.departure?.terminal);
        console.log(`Departure gate:`, mappedFlight.departure?.gate);
        console.log(`Departure checkInDesk:`, mappedFlight.departure?.checkInDesk);
        console.log(`Arrival baggageBelt:`, mappedFlight.arrival?.baggageBelt);
      }

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

  function formatMultipleFlights(flights: any[], searchDate: string): { message: string, buttons: any[] } {
    if (!flights || flights.length === 0) {
      return {
        message: '⚠️ No flight data found.',
        buttons: getDefaultButtons()
      };
    }

    const lines: string[] = [];
    lines.push(`⚠️ Found ${flights.length} flight${flights.length > 1 ? 's' : ''} with number ${flights[0]?.number || ''}:`);

    flights.forEach((flight, index) => {
      lines.push('');
      lines.push('───────────────');
      lines.push(`Flight ${index + 1}:`);
      lines.push(formatTelegramMessage(flight, index + 1));
      if (index < flights.length - 1) {
        lines.push('───────────────');
      }
    });

    let buttons: any[] = [];
    if (flights.length > 1) {
      // Новые кнопки в формате: "09.07 | MMK→SVO | 6:50 PM"
      buttons = flights.map((flight, index) => {
        return formatFlightButton(flight, index, searchDate);
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

  function formatFlightButton(flight: any, index: number, searchDate: string, type: 'departure' | 'arrival' = 'departure'): any {
    const depScheduled = flight.departure?.scheduledTime?.local;
    const arrScheduled = flight.arrival?.scheduledTime?.local;
    const depDate = extractDateFromTime(depScheduled);
    const arrDate = extractDateFromTime(arrScheduled);
    const depIata = flight.departure?.airport?.iata || '';
    const arrIata = flight.arrival?.airport?.iata || '';
    const direction = `${depIata}→${arrIata}`;
    const depTime = formatTimeAMPM(depScheduled);
    const arrTime = formatTimeAMPM(arrScheduled);
    const flightNumber = flight.number || 'UNKNOWN';

    let buttonText, callbackData;
    if (type === 'arrival') {
      buttonText = `🛬 ${formatDateShort(arrDate)} | ${direction} | ${arrTime}`;
      callbackData = `select_flight|${flightNumber}|${arrDate}|${arrTime.slice(0,5)}|${depIata}|${arrIata}|arrival`;
    } else {
      buttonText = `🛫 ${formatDateShort(depDate)} | ${direction} | ${depTime}`;
      callbackData = `select_flight|${flightNumber}|${depDate}|${depTime.slice(0,5)}|${depIata}|${arrIata}|departure`;
    }
    return [{ text: buttonText, callback_data: callbackData }];
  }

  function formatTimeAMPM(dt: string | null): string {
    if (!dt) return '--:--';
    try {
      // Парсим локальное время из формата "2025-07-09 21:50+03:00"
      const date = new Date(dt.replace(' ', 'T'));
      let hours = date.getHours();
      const minutes = date.getMinutes();
      const ampm = hours >= 12 ? 'PM' : 'AM';
      hours = hours % 12;
      hours = hours ? hours : 12;
      const minStr = minutes < 10 ? '0' + minutes : minutes;
      return `${hours}:${minStr} ${ampm}`;
    } catch {
      return '--:--';
    }
  }

  function extractDateFromTime(dateTimeStr: string): string {
    if (!dateTimeStr) return '';
    try {
      // Парсим дату из строки вида "2025-07-09 21:50+03:00"
      const datePart = dateTimeStr.split(' ')[0];
      return datePart;
    } catch {
      return '';
    }
  }

  function formatDateShort(dateStr: string): string {
    if (!dateStr) return '';
    try {
      const date = new Date(dateStr);
      return `${date.getDate().toString().padStart(2, '0')}.${(date.getMonth() + 1).toString().padStart(2, '0')}`;
    } catch {
      return '';
    }
  }

  function formatTime12(dt: string | null): string | null {
    if (!dt) return null;
    try {
      // Правильно парсим локальное время из формата "2025-07-09 21:50+03:00"
      const date = new Date(dt.replace(' ', 'T'));
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
      const date = new Date(dt.replace(' ', 'T'));
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

  function formatDate(dt: string | null): string | null {
    if (!dt) return null;
    try {
      const date = new Date(dt.replace(' ', 'T'));
      const day = date.getDate().toString().padStart(2, '0');
      const month = (date.getMonth() + 1).toString().padStart(2, '0');
      const year = date.getFullYear();
      return `${day}.${month}.${year}`;
    } catch {
      return null;
    }
  }

  function getGateStatus(flight: any): { indicator: string, message: string | null } {
    const status = flight.status;
    const depSched = flight.departure?.scheduledTime?.local;
    const depRevised = flight.departure?.revisedTime?.local;
    
    // Если рейс уже вылетел или прилетел - гейт закрыт
    if (status === 'Departed' || status === 'Arrived' || status === 'GateClosed') {
      return { indicator: '🔴', message: null };
    }
    
    // Если идет посадка
    if (status === 'Boarding') {
      return { indicator: '🟢', message: 'boarding in progress' };
    }
    
    // Если регистрация открыта, но посадка еще не началась
    if (status === 'CheckIn') {
      const departureTime = depRevised || depSched;
      if (departureTime) {
        // Вычисляем время посадки (обычно за 20 минут до вылета)
        const boardingTime = new Date(departureTime);
        boardingTime.setMinutes(boardingTime.getMinutes() - 20);
        return { indicator: '🟠', message: formatTime12(boardingTime.toISOString()) };
      }
      return { indicator: '🟠', message: null };
    }
    
    // Если рейс задержан
    if (status === 'Delayed') {
      const departureTime = depRevised || depSched;
      if (departureTime) {
        // Вычисляем время посадки (обычно за 20 минут до вылета)
        const boardingTime = new Date(departureTime);
        boardingTime.setMinutes(boardingTime.getMinutes() - 20);
        return { indicator: '🟠', message: formatTime12(boardingTime.toISOString()) };
      }
      return { indicator: '🟠', message: null };
    }
    
    // Если рейс в пути или ожидается
    if (status === 'EnRoute' || status === 'Expected' || status === 'Approaching') {
      return { indicator: '🔴', message: null };
    }
    
    // По умолчанию - ожидается открытие
    const departureTime = depRevised || depSched;
    if (departureTime) {
      // Вычисляем время посадки (обычно за 20 минут до вылета)
      const boardingTime = new Date(departureTime);
      boardingTime.setMinutes(boardingTime.getMinutes() - 20);
      return { indicator: '🟠', message: formatTime12(boardingTime.toISOString()) };
    }
    
    return { indicator: '🟠', message: null };
  }

  function getStatusIndicator(status: string): string {
    switch ((status || '').toLowerCase()) {
      case 'scheduled': return '⏳';
      case 'checkin': return '🟠';
      case 'boarding': return '🟢';
      case 'gateclosed': return '🔴';
      case 'departed': return '🛫';
      case 'enroute': return '✈️';
      case 'arrived': return '🏁'; // Финиш
      case 'delayed': return '⏰';
      case 'cancelled': return '❌';
      case 'canceled': return '❌';
      case 'diverted': return '⚠️';
      default: return '⏳';
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
      case 'cancelled': return '🔴';
      case 'canceled': return '🔴';
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
      case 'cancelled': return '🔴';
      case 'canceled': return '🔴';
      default: return '⏳';
    }
  }

  function getArrivalIndicator(status: string): string {
    switch ((status || '').toLowerCase()) {
      case 'arrived': return '🛬';
      case 'enroute': return '✈️';
      case 'delayed': return '⏰';
      case 'departed': return '✈️';
      default: return '⏰';
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
    
    const flightNumber = flight.number || '';
    const depIata = flight.departure?.airport?.iata;
    const arrIata = flight.arrival?.airport?.iata;
    const depName = flight.departure?.airport?.name;
    const arrName = flight.arrival?.airport?.name;
    const schedDep = flight.departure?.scheduledTime?.local;
    const depTimeStr = schedDep ? formatTime12(schedDep) : '';
    const depDateStr = schedDep ? formatDate(schedDep) : '';
    const status = flight.status || '';
    const statusIndicator = getStatusIndicator(status);

    // Header line
    let header = flightNumber;
    if (depIata && arrIata) {
      header += ` ${depIata}→${arrIata}`;
    }
    if (depTimeStr) {
      header += ` ${depTimeStr}`;
    }
    if (depDateStr) {
      header += ` (${depDateStr})`;
    }
    lines.push(header.trim());

    // Status line
    if (status) {
      lines.push(`${statusIndicator} Status: ${status}`);
      lines.push(''); // пустая строка после статуса
    }

    // Codeshare line
    if (flight.codeshares && flight.codeshares.length > 0) {
      const codeshareList = flight.codeshares.join(', ');
      lines.push(`Also listed as: ${codeshareList}`);
      lines.push('');
    }

    // Codeshare note (when API returned different flight)
    if (flight.codeshareNote) {
      lines.push(`📋 ${flight.codeshareNote}`);
      lines.push('');
    }

    // Departure section
    if (depIata || depName) {
      lines.push(`🛫 ${depIata || '--'} / ${depName || ''}`.trim());
      if (flight.departure?.terminal) {
        lines.push(`Terminal: ${flight.departure.terminal}`);
      }
      if (flight.departure?.checkInDesk) {
        lines.push(`Check-in: ${flight.departure.checkInDesk}`);
      }
      if (flight.departure?.gate) {
        const gateStatus = getGateStatus(flight);
        if (gateStatus.message) {
          lines.push(`Gate: ${flight.departure.gate} (boarding at ${gateStatus.message})`);
        } else {
          lines.push(`Gate: ${flight.departure.gate}`);
        }
      }
      const depSched = flight.departure?.scheduledTime?.local;
      const depActual = flight.departure?.actualTime?.local;
      const depRevised = flight.departure?.revisedTime?.local;
      if (depActual && depSched && depActual !== depSched) {
        lines.push(`Departure: ${formatTime12(depActual)} (was ${formatTime12(depSched)})`);
      } else if (depRevised && depSched && depRevised !== depSched) {
        lines.push(`Departure: ${formatTime12(depRevised)} (was ${formatTime12(depSched)})`);
      } else if (depSched) {
        lines.push(`Departure: ${formatTime12(depSched)}`);
      }
      lines.push(''); // пустая строка после departure
    }

    // Arrival section
    if (arrIata || arrName) {
      lines.push(`🛬 ${arrIata || '--'} / ${arrName || ''}`.trim());
      const arrSched = flight.arrival?.scheduledTime?.local;
      const arrActual = flight.arrival?.actualTime?.local;
      const arrRevised = flight.arrival?.revisedTime?.local;
      const arrExpected = flight.arrival?.predictedTime?.local;
      if (arrActual) {
        if (arrSched && arrActual !== arrSched) {
          lines.push(`Arrival: ${formatTime12(arrActual)} (was ${formatTime12(arrSched)})`);
        } else {
          lines.push(`Arrival: ${formatTime12(arrActual)}`);
        }
      } else if (arrRevised) {
        if (arrSched && arrRevised !== arrSched) {
          lines.push(`Arrival: ${formatTime12(arrRevised)} (was ${formatTime12(arrSched)})`);
        } else {
          lines.push(`Arrival: ${formatTime12(arrRevised)}`);
        }
      } else if (arrExpected) {
        if (arrSched && arrExpected !== arrSched) {
          lines.push(`Expected arrival: ${formatTime12(arrExpected)} (scheduled: ${formatTime12(arrSched)})`);
        } else {
          lines.push(`Expected arrival: ${formatTime12(arrExpected)}`);
        }
      } else if (arrSched) {
        lines.push(`Arrival: ${formatTime12(arrSched)}`);
      }
      if (flight.arrival?.baggageBelt) {
        lines.push(`Baggage: ${flight.arrival.baggageBelt}`);
      }
      lines.push(''); // пустая строка после arrival
    }

    // Разделитель (только если это не часть множественного списка)
    if (!flightIndex) {
      lines.push('__________________');
    }

    // Aircraft and Airline
    if (flight.aircraft?.model) {
      lines.push(`Aircraft: ${flight.aircraft.model}`);
    }
    if (flight.airline?.name) {
      lines.push(`Airline: ${flight.airline.name}`);
    }

    return lines.join('\n').replace(/\n{3,}/g, '\n\n').trim();
  } 