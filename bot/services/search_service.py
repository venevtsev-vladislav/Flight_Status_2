import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from supabase import create_client, Client
from bot.config import SUPABASE_URL, SUPABASE_ANON_KEY

logger = logging.getLogger(__name__)

class SearchService:
    """Service for managing active searches in Supabase"""
    
    def __init__(self):
        self.supabase: Client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
    
    async def create_or_update_search(
        self, 
        telegram_id: int, 
        user_id: str,
        search_state: str,
        flight_number: Optional[str] = None,
        search_date: Optional[str] = None,
        parsed_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Create or update active search for user"""
        try:
            # Clean up expired searches first
            await self._cleanup_expired_searches()
            
            # Prepare data
            data = {
                'telegram_id': telegram_id,
                'user_id': user_id,
                'search_state': search_state,
                'updated_at': datetime.utcnow().isoformat(),
                'expires_at': (datetime.utcnow() + timedelta(hours=1)).isoformat()
            }
            
            if flight_number:
                data['flight_number'] = flight_number
            if search_date:
                data['search_date'] = search_date
            if parsed_data:
                data['parsed_data'] = parsed_data
            
            # Upsert (insert or update)
            result = self.supabase.table('active_searches').upsert(
                data,
                on_conflict='telegram_id'
            ).execute()
            
            if result.data:
                logger.info(f"✅ Search state updated for user {telegram_id}: {search_state}")
                return result.data[0]
            else:
                logger.error(f"❌ Failed to update search state for user {telegram_id}")
                return {}
                
        except Exception as e:
            logger.error(f"❌ Error updating search state: {e}")
            return {}
    
    async def get_active_search(self, telegram_id: int) -> Optional[Dict[str, Any]]:
        """Get active search for user"""
        try:
            result = self.supabase.table('active_searches').select('*').eq(
                'telegram_id', telegram_id
            ).execute()
            
            if result.data:
                search = result.data[0]
                # Check if search is expired
                expires_at = datetime.fromisoformat(search['expires_at'].replace('Z', '+00:00'))
                if datetime.utcnow().replace(tzinfo=expires_at.tzinfo) > expires_at:
                    # Search expired, delete it
                    await self.delete_active_search(telegram_id)
                    return None
                
                logger.info(f"📋 Found active search for user {telegram_id}: {search['search_state']}")
                return search
            else:
                logger.info(f"📋 No active search found for user {telegram_id}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Error getting active search: {e}")
            return None
    
    async def delete_active_search(self, telegram_id: int) -> bool:
        """Delete active search for user"""
        try:
            result = self.supabase.table('active_searches').delete().eq(
                'telegram_id', telegram_id
            ).execute()
            
            if result.data:
                logger.info(f"🗑️ Deleted active search for user {telegram_id}")
                return True
            else:
                logger.info(f"📋 No active search to delete for user {telegram_id}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error deleting active search: {e}")
            return False
    
    async def _cleanup_expired_searches(self):
        """Clean up expired searches"""
        try:
            # Delete searches that expired more than 1 hour ago
            cutoff_time = (datetime.utcnow() - timedelta(hours=1)).isoformat()
            
            result = self.supabase.table('active_searches').delete().lt(
                'expires_at', cutoff_time
            ).execute()
            
            if result.data:
                logger.info(f"🧹 Cleaned up {len(result.data)} expired searches")
                
        except Exception as e:
            logger.error(f"❌ Error cleaning up expired searches: {e}")
    
    async def update_search_with_flight_number(
        self, 
        telegram_id: int, 
        user_id: str,
        flight_number: str,
        parsed_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Update search with flight number"""
        return await self.create_or_update_search(
            telegram_id=telegram_id,
            user_id=user_id,
            search_state='waiting_for_date',
            flight_number=flight_number,
            parsed_data=parsed_data
        )
    
    async def update_search_with_date(
        self, 
        telegram_id: int, 
        user_id: str,
        search_date: str,
        parsed_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Update search with date"""
        return await self.create_or_update_search(
            telegram_id=telegram_id,
            user_id=user_id,
            search_state='waiting_for_number',
            search_date=search_date,
            parsed_data=parsed_data
        )
    
    async def complete_search(
        self, 
        telegram_id: int, 
        flight_number: str,
        search_date: str,
        parsed_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Complete search with both flight number and date"""
        return await self.create_or_update_search(
            telegram_id=telegram_id,
            user_id='',  # Will be updated by the calling function
            search_state='complete',
            flight_number=flight_number,
            search_date=search_date,
            parsed_data=parsed_data
        ) 