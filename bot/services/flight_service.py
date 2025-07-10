import httpx
import logging
from typing import Optional, Dict, Any
from bot.config import PARSE_FLIGHT_URL, FLIGHT_API_URL, FLIGHT_API_TIMEOUT, MAX_RETRIES, SUPABASE_ANON_KEY

logger = logging.getLogger(__name__)

class FlightService:
    def __init__(self):
        self.parse_url = PARSE_FLIGHT_URL
        self.api_url = FLIGHT_API_URL
        self.timeout = FLIGHT_API_TIMEOUT
    
    async def parse_flight_request(self, text: str, user_id: Optional[str] = None) -> Dict[str, Any]:
        """Parse flight request using Edge Function"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                payload = {
                    "text": text,
                    "user_id": user_id
                }
                
                headers = {
                    "Authorization": f"Bearer {SUPABASE_ANON_KEY}"
                }
                
                # Логируем запрос
                logger.info(f"🔍 PARSE REQUEST to {self.parse_url}")
                logger.info(f"📤 Payload: {payload}")
                logger.info(f"📋 Headers: {headers}")
                
                response = await client.post(self.parse_url, json=payload, headers=headers)
                
                # Логируем ответ
                logger.info(f"📥 PARSE RESPONSE Status: {response.status_code}")
                logger.info(f"📥 Response Headers: {dict(response.headers)}")
                logger.info(f"📥 Response Body: {response.text}")
                
                response.raise_for_status()
                
                result = response.json()
                logger.info(f"✅ PARSE SUCCESS: {result}")
                return result
                
        except httpx.HTTPStatusError as e:
            logger.error(f"❌ HTTP error in parse_flight_request: {e}")
            logger.error(f"❌ Response status: {e.response.status_code}")
            logger.error(f"❌ Response body: {e.response.text}")
            return {"error": f"HTTP error: {e.response.status_code}"}
        except Exception as e:
            logger.error(f"❌ Error in parse_flight_request: {e}")
            return {"error": str(e)}
    
    async def get_flight_data(self, flight_number: str, date: str, user_id: Optional[str] = None) -> Dict[str, Any]:
        """Get flight data using Edge Function"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                payload = {
                    "flight_number": flight_number,
                    "date": date,
                    "user_id": user_id
                }
                
                headers = {
                    "Authorization": f"Bearer {SUPABASE_ANON_KEY}"
                }
                
                # Логируем запрос
                logger.info(f"🔍 FLIGHT API REQUEST to {self.api_url}")
                logger.info(f"📤 Payload: {payload}")
                logger.info(f"📋 Headers: {headers}")
                
                response = await client.post(self.api_url, json=payload, headers=headers)
                
                # Логируем ответ
                logger.info(f"📥 FLIGHT API RESPONSE Status: {response.status_code}")
                logger.info(f"📥 Response Headers: {dict(response.headers)}")
                logger.info(f"📥 Response Body: {response.text}")
                
                response.raise_for_status()
                
                result = response.json()
                logger.info(f"✅ FLIGHT API SUCCESS: {result}")
                return result
                
        except httpx.HTTPStatusError as e:
            logger.error(f"❌ HTTP error in get_flight_data: {e}")
            logger.error(f"❌ Response status: {e.response.status_code}")
            logger.error(f"❌ Response body: {e.response.text}")
            return {"error": f"HTTP error: {e.response.status_code}"}
        except Exception as e:
            logger.error(f"❌ Error in get_flight_data: {e}")
            return {"error": str(e)} 