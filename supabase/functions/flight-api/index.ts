  import { serve } from "https://deno.land/std@0.168.0/http/server.ts"
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'
import { v4 as uuidv4 } from "https://deno.land/std@0.168.0/uuid/mod.ts"

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

      // Save flight details with UUID for each flight
      const flightDetailsUUIDs: string[] = [];
      
      if (Array.isArray(flightData)) {
        // Multiple flights
        for (const flight of flightData) {
          const dep = flight.departure || {};
          const arr = flight.arrival || {};
          const flight_number = (flight.number || '').replace(/\s/g, '');
          const departure_date = dep.scheduledTime?.local ? dep.scheduledTime.local.split(' ')[0] : null;
          const departure_time = dep.scheduledTime?.local ? dep.scheduledTime.local.split(' ')[1]?.slice(0,5) : null;
          const departure_airport = dep.airport?.iata || null;
          const arrival_airport = arr.airport?.iata || null;

          // Check if record already exists
          let { data: existingDetail } = await supabase
            .from('flight_details')
            .select('id')
            .eq('flight_number', flight_number)
            .eq('departure_date', departure_date)
            .eq('departure_time', departure_time)
            .eq('departure_airport', departure_airport)
            .eq('arrival_airport', arrival_airport)
            .single();

          let uuid = existingDetail?.id;
          if (!uuid) {
            // Insert new record
            const { data: newDetail } = await supabase
              .from('flight_details')
              .insert({
                flight_id: flight.id,
                flight_number,
                departure_date,
                departure_time,
                departure_airport,
                arrival_airport,
                data_source: 'aerodatabox',
                raw_data: flight,
                last_checked_at: new Date().toISOString(),
              })
              .select('id')
              .single();
            uuid = newDetail?.id;
          } else {
            // Update existing record
            await supabase
              .from('flight_details')
              .update({
                raw_data: flight,
                last_checked_at: new Date().toISOString(),
              })
              .eq('id', uuid);
          }
          if (uuid) flightDetailsUUIDs.push(uuid);
        }
      } else {
        // Single flight
        const dep = flightData.departure || {};
        const arr = flightData.arrival || {};
        const flight_number = (flightData.number || '').replace(/\s/g, '');
        const departure_date = dep.scheduledTime?.local ? dep.scheduledTime.local.split(' ')[0] : null;
        const departure_time = dep.scheduledTime?.local ? dep.scheduledTime.local.split(' ')[1]?.slice(0,5) : null;
        const departure_airport = dep.airport?.iata || null;
        const arrival_airport = arr.airport?.iata || null;

        // Check if record already exists
        let { data: existingDetail } = await supabase
          .from('flight_details')
          .select('id')
          .eq('flight_number', flight_number)
          .eq('departure_date', departure_date)
          .eq('departure_time', departure_time)
          .eq('departure_airport', departure_airport)
          .eq('arrival_airport', arrival_airport)
          .single();

        let uuid = existingDetail?.id;
        if (!uuid) {
          // Insert new record
          const { data: newDetail } = await supabase
              .from('flight_details')
              .insert({
                flight_id: flight?.id || null,
                flight_number,
                departure_date,
                departure_time,
                departure_airport,
                arrival_airport,
                data_source: 'aerodatabox',
                raw_data: flightData,
                last_checked_at: new Date().toISOString(),
              })
              .select('id')
              .single();
          uuid = newDetail?.id;
        } else {
          // Update existing record
          await supabase
            .from('flight_details')
            .update({
              raw_data: flightData,
              last_checked_at: new Date().toISOString(),
            })
            .eq('id', uuid);
        }
        if (uuid) flightDetailsUUIDs.push(uuid);
      }

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
          buttons = getDefaultButtons(); // Теперь buttons всегда массив массивов
        } else {
          const result = formatMultipleFlights(flightData, date, flightDetailsUUIDs);
          message = result.message;
          buttons = result.buttons;
        }
      } else if (flightData && typeof flightData === 'object') {
        message = formatTelegramMessage(flightData);
      } else {
        message = '⚠️ Sorry, could not find flight data.';
      }
      
      // Всегда возвращаем поле buttons, даже если оно пустое
      return new Response(
        JSON.stringify({
          success: true,
          data: flightData,
          message,
          buttons // массив массивов кнопок, каждая с уникальным callback_data
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

  function formatMultipleFlights(flights: any[], searchDate: string, flightDetailsUUIDs?: string[]): { message: string, buttons: any[] } {
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
    if (flights.length > 1 && flightDetailsUUIDs && flightDetailsUUIDs.length > 0) {
      // Кнопки выбора рейса с UUID для нескольких рейсов
      buttons = flights.map((flight, index) => {
        const uuid = flightDetailsUUIDs[index];
        if (!uuid) return null;
        
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

        const buttonText = `🛫 ${formatDateShort(depDate)} | ${direction} | ${depTime}`;
        const callbackData = `select_flight|${uuid}`;
        
        return [{ text: buttonText, callback_data: callbackData }];
      }).filter(button => button !== null);
    } else {
      // Стандартные кнопки действий для одного рейса
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
      callbackData = `select_flight|${flightNumber}|${arrDate}|${arrTime.slice(0,5)}|${depIata}|${arrIata}|arrival|${depDate}|${depTime.slice(0,5)}`;
    } else {
      buttonText = `🛫 ${formatDateShort(depDate)} | ${direction} | ${depTime}`;
      callbackData = `select_flight|${flightNumber}|${depDate}|${depTime.slice(0,5)}|${depIata}|${arrIata}|departure|${arrDate}|${arrTime.slice(0,5)}`;
    }
    return [{ text: buttonText, callback_data: callbackData }];
  }

  function formatTimeAMPM(dt: string | null): string {
    if (!dt) return '--:--';
    
    try {
      // Правильно парсим время из формата "2025-07-28 07:35+03:00"
      // Извлекаем время напрямую из строки
      const timeMatch = dt.match(/(\d{1,2}):(\d{2})/);
      if (!timeMatch) {
        return '--:--';
      }
      
      const hours = parseInt(timeMatch[1], 10);
      const minutes = parseInt(timeMatch[2], 10);
      const hoursStr = hours < 10 ? '0' + hours : hours.toString();
      const minStr = minutes < 10 ? '0' + minutes : minutes.toString();
      return `${hoursStr}:${minStr}`;
    } catch (error) {
      console.log('🔍 DEBUG: formatTimeAMPM error:', error, 'for input:', dt);
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
    
    // Отладочный лог
    console.log('🔍 DEBUG: formatTime12 input:', dt);
    
    try {
      // Правильно парсим время из формата "2025-07-28 07:35+03:00"
      // Извлекаем время напрямую из строки
      const timeMatch = dt.match(/(\d{1,2}):(\d{2})/);
      if (!timeMatch) {
        console.log('🔍 DEBUG: No time pattern found in:', dt);
        return dt;
      }
      
      const hours = parseInt(timeMatch[1], 10);
      const minutes = parseInt(timeMatch[2], 10);
      const hoursStr = hours < 10 ? '0' + hours : hours.toString();
      const minStr = minutes < 10 ? '0' + minutes : minutes.toString();
      const result = `${hoursStr}:${minStr}`;
      
      // Отладочный лог результата
      console.log('🔍 DEBUG: formatTime12 output:', result, 'from input:', dt);
      
      return result;
    } catch (error) {
      console.log('🔍 DEBUG: formatTime12 error:', error, 'for input:', dt);
      return dt;
    }
  }

  function formatTimeHHMM(dt: string | null): string | null {
    if (!dt) return null;
    try {
      const date = new Date(dt.replace(' ', 'T'));
      const hours = date.getHours();
      const minutes = date.getMinutes();
      const hh = hours < 10 ? '0' + hours : hours.toString();
      const mm = minutes < 10 ? '0' + minutes : minutes.toString();
      return `${hh}:${mm}`;
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
    
    // Отладочный лог для проверки времени
    console.log('🔍 DEBUG: Flight departure times:', {
      scheduled: flight.departure?.scheduledTime,
      actual: flight.departure?.actualTime,
      revised: flight.departure?.revisedTime
    });
    
    // Детальный отладочный лог для времени вылета
    console.log('🔍 DEBUG: Departure time details:', {
      scheduled_utc: flight.departure?.scheduledTime?.utc,
      scheduled_local: flight.departure?.scheduledTime?.local,
      revised_utc: flight.departure?.revisedTime?.utc,
      revised_local: flight.departure?.revisedTime?.local,
      actual_utc: flight.departure?.actualTime?.utc,
      actual_local: flight.departure?.actualTime?.local
    });
    
    const lines: string[] = [];
    
    const flightNumber = flight.number || '';
    const depIata = flight.departure?.airport?.iata;
    const arrIata = flight.arrival?.airport?.iata;
    const depName = flight.departure?.airport?.name;
    const arrName = flight.arrival?.airport?.name;
    const schedDep = flight.departure?.scheduledTime?.local;
    const status = flight.status || '';
    const statusIndicator = getStatusIndicator(status);

    // Header line
    let header = flightNumber;
    if (depIata && arrIata) {
      header += ` ${depIata}→${arrIata}`;
    }
    if (schedDep) {
      header += ` ${formatTime12(schedDep)}`;
      header += ` (${formatDate(schedDep)})`;
    }
    lines.push(header.trim());

    // Status line
    if (status) {
      lines.push(`${statusIndicator} Status: ${status}`);
      lines.push('');
    }

    // Codeshare line (only one, no duplicate)
    if (flight.codeshares && flight.codeshares.length > 0) {
      const codeshareList = flight.codeshares.join(', ');
      lines.push(`Also listed as: ${codeshareList}`);
      lines.push('');
    } else if (flight.codeshareNote) {
      // Only show codeshareNote if codeshares is empty
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
      // Time logic for departure
      const depActual = flight.departure?.actualTime?.local;
      const depRevised = flight.departure?.revisedTime?.local;
      const depScheduled = flight.departure?.scheduledTime?.local;
      let depCurrent = depActual || depRevised || depScheduled;
      let depLine = '';
      
      // Отладочный лог для времени вылета
      console.log('🔍 DEBUG: Departure times:', {
        actual: depActual,
        revised: depRevised,
        scheduled: depScheduled,
        current: depCurrent,
        formatted: depCurrent ? formatTime12(depCurrent) : null
      });
      
      if (depCurrent && depScheduled && depCurrent !== depScheduled) {
        depLine = `Departure: ${formatTime12(depCurrent)} (was ${formatTime12(depScheduled)})`;
      } else if (depCurrent) {
        depLine = `Departure: ${formatTime12(depCurrent)}`;
      }
      if (depLine) lines.push(depLine);
      lines.push('');
    }

    // Arrival section
    if (arrIata || arrName) {
      lines.push(`🛬 ${arrIata || '--'} / ${arrName || ''}`.trim());
      const arrActual = flight.arrival?.actualTime?.local;
      const arrRevised = flight.arrival?.revisedTime?.local;
      const arrPredicted = flight.arrival?.predictedTime?.local;
      const arrScheduled = flight.arrival?.scheduledTime?.local;
      let arrCurrent = arrActual || arrRevised || arrPredicted || arrScheduled;
      let arrLine = '';
      
      // Отладочный лог для времени прилета
      console.log('🔍 DEBUG: Arrival times:', {
        actual: arrActual,
        revised: arrRevised,
        predicted: arrPredicted,
        scheduled: arrScheduled,
        current: arrCurrent,
        formatted: arrCurrent ? formatTime12(arrCurrent) : null
      });
      
      if (arrCurrent && arrScheduled && arrCurrent !== arrScheduled) {
        arrLine = `Arrival: ${formatTime12(arrCurrent)} (was ${formatTime12(arrScheduled)})`;
      } else if (arrCurrent) {
        arrLine = `Arrival: ${formatTime12(arrCurrent)}`;
      }
      if (arrLine) lines.push(arrLine);
      if (flight.arrival?.baggageBelt) {
        lines.push(`Baggage: ${flight.arrival.baggageBelt}`);
      }
      lines.push('');
    }

    if (!flightIndex) {
      lines.push('__________________');
    }

    if (flight.aircraft?.model) {
      lines.push(`Aircraft: ${flight.aircraft.model}`);
    }
    if (flight.airline?.name) {
      lines.push(`Airline: ${flight.airline.name}`);
    }

    return lines.join('\n').replace(/\n{3,}/g, '\n\n').trim();
  } 