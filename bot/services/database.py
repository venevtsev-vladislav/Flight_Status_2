from supabase import create_client
from typing import Optional, Dict, Any, List
import logging
from datetime import datetime
from bot.config import SUPABASE_URL, SUPABASE_ANON_KEY

logger = logging.getLogger(__name__)

class DatabaseService:
    def __init__(self):
        if not SUPABASE_URL or not SUPABASE_ANON_KEY:
            raise ValueError("SUPABASE_URL and SUPABASE_ANON_KEY must be set and not None")
        self.supabase = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
    
    async def get_or_create_user(self, telegram_id: int, username: Optional[str] = None, 
                                language_code: str = "en", platform: str = "telegram") -> Dict[str, Any]:
        """Get existing user or create new one"""
        try:
            # Try to get existing user
            response = self.supabase.table('users').select('*').eq('telegram_id', telegram_id).execute()
            
            if response.data:
                user = response.data[0]
                # Update last_active
                self.supabase.table('users').update({
                    'last_active': datetime.utcnow().isoformat(),
                    'username': username or user.get('username')
                }).eq('id', user['id']).execute()
                return user
            
            # Create new user
            new_user = {
                'telegram_id': telegram_id,
                'username': username,
                'language_code': language_code,
                'platform': platform,
                'version': '1.0.0',
                'first_seen': datetime.utcnow().isoformat(),
                'last_active': datetime.utcnow().isoformat()
            }
            
            response = self.supabase.table('users').insert(new_user).execute()
            return response.data[0]
            
        except Exception as e:
            logger.error(f"Error in get_or_create_user: {e}")
            raise
    
    async def save_message(self, user_id: str, message_id: int, content: str, 
                          parsed_json: Optional[Dict] = None) -> Dict[str, Any]:
        """Save user message to database"""
        try:
            message_data = {
                'user_id': user_id,
                'message_id': message_id,
                'content': content,
                'parsed_json': parsed_json
            }
            
            response = self.supabase.table('messages').insert(message_data).execute()
            return response.data[0]
            
        except Exception as e:
            logger.error(f"Error in save_message: {e}")
            raise
    
    async def get_or_create_flight(self, flight_number: str, date: str) -> Dict[str, Any]:
        """Get existing flight or create new one"""
        try:
            # Try to get existing flight
            response = self.supabase.table('flights').select('*').eq('flight_number', flight_number).eq('date', date).execute()
            
            if response.data:
                return response.data[0]
            
            # Create new flight
            flight_data = {
                'flight_number': flight_number,
                'date': date
            }
            
            response = self.supabase.table('flights').insert(flight_data).execute()
            return response.data[0]
            
        except Exception as e:
            logger.error(f"Error in get_or_create_flight: {e}")
            raise

    async def get_flight_by_id(self, flight_id: str) -> Dict[str, Any] | None:
        """Get flight by ID from flights table"""
        try:
            response = self.supabase.table('flights').select('*').eq('id', flight_id).single().execute()
            if response.data:
                return response.data
            return None
        except Exception as e:
            logger.error(f"Error in get_flight_by_id: {e}")
            return None
    
    async def save_flight_request(self, user_id: str, flight_id: str) -> Dict[str, Any]:
        """Save flight request"""
        try:
            request_data = {
                'user_id': user_id,
                'flight_id': flight_id
            }
            
            response = self.supabase.table('flight_requests').insert(request_data).execute()
            return response.data[0]
            
        except Exception as e:
            logger.error(f"Error in save_flight_request: {e}")
            raise
    
    async def update_flight_details(self, flight_id: str, data_source: str, 
                                   raw_data: Dict, normalized_data: Dict) -> Dict[str, Any]:
        """Update flight details"""
        try:
            details_data = {
                'flight_id': flight_id,
                'data_source': data_source,
                'raw_data': raw_data,
                'normalized': normalized_data,
                'last_checked_at': datetime.utcnow().isoformat()
            }
            
            response = self.supabase.table('flight_details').upsert(details_data).execute()
            return response.data[0]
            
        except Exception as e:
            logger.error(f"Error in update_flight_details: {e}")
            raise
    
    async def save_feature_request(self, user_id: str, feature_code: str, 
                                  flight_id: Optional[str] = None, comment: Optional[str] = None) -> Dict[str, Any]:
        """Save feature request"""
        try:
            request_data = {
                'user_id': user_id,
                'feature_code': feature_code,
                'flight_id': flight_id,
                'comment': comment
            }
            
            response = self.supabase.table('feature_requests').insert(request_data).execute()
            return response.data[0]
            
        except Exception as e:
            logger.error(f"Error in save_feature_request: {e}")
            raise
    
    async def get_translation(self, key: str, lang: str = "en") -> Optional[str]:
        """Get translation for key and language"""
        try:
            response = self.supabase.table('translations').select('value').eq('key', key).eq('lang', lang).execute()
            if response.data:
                return response.data[0]['value']
            return None
            
        except Exception as e:
            logger.error(f"Error in get_translation: {e}")
            return None
    
    async def log_audit(self, user_id: str, action: str, details: Optional[Dict] = None) -> Dict[str, Any]:
        """Log audit event"""
        try:
            audit_data = {
                'user_id': user_id,
                'action': action,
                'details': details
            }
            
            response = self.supabase.table('audit_logs').insert(audit_data).execute()
            return response.data[0]
            
        except Exception as e:
            logger.error(f"Error in log_audit: {e}")
            raise
    
    async def create_flight_subscription(self, subscription_data: dict) -> str | None:
        """Create or update a flight subscription in flight_subscriptions table"""
        try:
            # Check if subscription already exists
            existing = await self.get_flight_subscription(
                subscription_data['user_id'], 
                subscription_data['flight_number'], 
                subscription_data['flight_date']
            )
            
            if existing:
                # Update existing subscription
                logger.info(f"Updating existing subscription for flight {subscription_data['flight_number']}")
                response = self.supabase.table('flight_subscriptions')\
                    .update(subscription_data)\
                    .eq('user_id', subscription_data['user_id'])\
                    .eq('flight_number', subscription_data['flight_number'])\
                    .eq('flight_date', subscription_data['flight_date'])\
                    .execute()
                if response.data and len(response.data) > 0:
                    return response.data[0]['id']
            else:
                # Create new subscription
                logger.info(f"Creating new subscription for flight {subscription_data['flight_number']}")
                response = self.supabase.table('flight_subscriptions').insert(subscription_data).execute()
                if response.data and len(response.data) > 0:
                    return response.data[0]['id']
            
            return None
        except Exception as e:
            logger.error(f"Error in create_flight_subscription: {e}")
            return None

    async def get_flight_subscription(self, user_id: str, flight_number: str, flight_date: str) -> dict | None:
        """Get a flight subscription by user, flight_number and date from flight_subscriptions table"""
        try:
            response = self.supabase.table('flight_subscriptions').select('*')\
                .eq('user_id', user_id)\
                .eq('flight_number', flight_number)\
                .eq('flight_date', flight_date)\
                .execute()
            if response.data and len(response.data) > 0:
                return response.data[0]
            return None
        except Exception as e:
            logger.error(f"Error in get_flight_subscription: {e}")
            return None

    async def unsubscribe_from_flight(self, user_id: str, flight_id: str) -> bool:
        """Unsubscribe user from flight in flight_subscriptions table by id"""
        try:
            response = self.supabase.table('flight_subscriptions')\
                .delete()\
                .eq('user_id', user_id)\
                .eq('id', flight_id)\
                .execute()
            return response.data is not None
        except Exception as e:
            logger.error(f"Error in unsubscribe_from_flight: {e}")
            return False

    async def is_subscribed(self, user_id: str, subscription_id: str) -> bool:
        """Check if user is subscribed to flight in flight_subscriptions table by subscription id"""
        try:
            response = self.supabase.table('flight_subscriptions').select('id').eq('user_id', user_id).eq('id', subscription_id).execute()
            return len(response.data) > 0
        except Exception as e:
            logger.error(f"Error in is_subscribed: {e}")
            return False

    async def get_flight_detail_by_uuid(self, uuid: str) -> dict | None:
        try:
            response = self.supabase.table('flight_details').select('*').eq('id', uuid).single().execute()
            if response.data:
                return response.data
            return None
        except Exception as e:
            logger.error(f"Error in get_flight_detail_by_uuid: {e}")
            return None

    async def get_user_subscriptions(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all active flight subscriptions for a user"""
        try:
            response = self.supabase.table('flight_subscriptions')\
                .select('*')\
                .eq('user_id', user_id)\
                .eq('status', 'active')\
                .order('created_at', desc=True)\
                .execute()
            
            if response.data:
                return response.data
            return []
        except Exception as e:
            logger.error(f"Error in get_user_subscriptions: {e}")
            return []

    async def get_subscription_by_id(self, subscription_id: str) -> Dict[str, Any] | None:
        """Get subscription by ID"""
        try:
            response = self.supabase.table('flight_subscriptions')\
                .select('*')\
                .eq('id', subscription_id)\
                .single()\
                .execute()
            
            if response.data:
                return response.data
            return None
        except Exception as e:
            logger.error(f"Error in get_subscription_by_id: {e}")
            return None