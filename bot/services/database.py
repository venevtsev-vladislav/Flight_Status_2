from supabase import create_client, Client
from typing import Optional, Dict, Any, List
import logging
from datetime import datetime
from bot.config import SUPABASE_URL, SUPABASE_ANON_KEY

logger = logging.getLogger(__name__)

class DatabaseService:
    def __init__(self):
        self.supabase: Client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
    
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
    
    async def get_user_subscriptions(self, user_id: str) -> List[Dict[str, Any]]:
        """Get user's flight subscriptions"""
        try:
            response = self.supabase.table('subscriptions').select('*, flights(*)').eq('user_id', user_id).execute()
            return response.data
            
        except Exception as e:
            logger.error(f"Error in get_user_subscriptions: {e}")
            return []
    
    async def subscribe_to_flight(self, user_id: str, flight_id: str) -> Dict[str, Any]:
        """Subscribe user to flight updates"""
        try:
            subscription_data = {
                'user_id': user_id,
                'flight_id': flight_id
            }
            
            response = self.supabase.table('subscriptions').upsert(subscription_data).execute()
            return response.data[0]
            
        except Exception as e:
            logger.error(f"Error in subscribe_to_flight: {e}")
            raise
    
    async def unsubscribe_from_flight(self, user_id: str, flight_id: str) -> bool:
        """Unsubscribe user from flight updates"""
        try:
            response = self.supabase.table('subscriptions').delete().eq('user_id', user_id).eq('flight_id', flight_id).execute()
            return len(response.data) > 0
            
        except Exception as e:
            logger.error(f"Error in unsubscribe_from_flight: {e}")
            return False
    
    async def is_subscribed(self, user_id: str, flight_id: str) -> bool:
        """Check if user is subscribed to flight"""
        try:
            response = self.supabase.table('subscriptions').select('id').eq('user_id', user_id).eq('flight_id', flight_id).execute()
            return len(response.data) > 0
            
        except Exception as e:
            logger.error(f"Error in is_subscribed: {e}")
            return False
    
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