import asyncio
from typing import Optional
from aiogram import Bot
from aiogram.enums import ChatAction
from bot.config import TYPING_INDICATOR_ENABLED, TYPING_DURATION, TYPING_ACTION

class TypingService:
    """Service for managing typing indicators during API requests"""
    
    def __init__(self, bot: Bot):
        self.bot = bot
        self.enabled = TYPING_INDICATOR_ENABLED
        self.default_duration = TYPING_DURATION
        self.default_action = TYPING_ACTION
    
    async def show_typing(self, chat_id: int, duration: Optional[int] = None, 
                         action: Optional[str] = None) -> None:
        """
        Show typing indicator for specified duration
        
        Args:
            chat_id: Telegram chat ID
            duration: Duration in seconds (uses default if None)
            action: Typing action type (uses default if None)
        """
        if not self.enabled:
            return
        
        duration = duration or self.default_duration
        action = action or self.default_action
        
        try:
            # Send typing action
            await self.bot.send_chat_action(chat_id, action)
            
            # Keep typing indicator active for specified duration
            await asyncio.sleep(duration)
            
        except Exception as e:
            # Log error but don't fail the main operation
            print(f"Error showing typing indicator: {e}")
    
    async def show_typing_until(self, chat_id: int, future: asyncio.Future, 
                               action: Optional[str] = None) -> None:
        """
        Show typing indicator until a future completes
        
        Args:
            chat_id: Telegram chat ID
            future: Future to wait for
            action: Typing action type (uses default if None)
        """
        if not self.enabled:
            return
        
        action = action or self.default_action
        
        try:
            # Start typing indicator
            typing_task = asyncio.create_task(self._keep_typing(chat_id, action))
            
            # Wait for the main operation to complete
            await future
            
            # Cancel typing indicator
            typing_task.cancel()
            
        except Exception as e:
            print(f"Error in show_typing_until: {e}")
    
    async def _keep_typing(self, chat_id: int, action: str) -> None:
        """Keep typing indicator active"""
        try:
            while True:
                await self.bot.send_chat_action(chat_id, action)
                await asyncio.sleep(5)  # Telegram typing indicator expires after 5 seconds
        except asyncio.CancelledError:
            # Task was cancelled, which is expected
            pass
        except Exception as e:
            print(f"Error in _keep_typing: {e}")
    
    async def show_loading_message(self, chat_id: int, message: str, 
                                 duration: Optional[int] = None) -> None:
        """
        Show loading message with typing indicator
        
        Args:
            chat_id: Telegram chat ID
            message: Loading message to send
            duration: Duration to show typing (uses default if None)
        """
        if not self.enabled:
            return
        
        duration = duration or self.default_duration
        
        try:
            # Send loading message
            sent_message = await self.bot.send_message(chat_id, message)
            
            # Show typing indicator
            await self.show_typing(chat_id, duration)
            
            return sent_message
            
        except Exception as e:
            print(f"Error showing loading message: {e}")
            return None
    
    def get_typing_action(self, action_type: str) -> ChatAction:
        """Convert string action to ChatAction enum"""
        action_map = {
            "typing": ChatAction.TYPING,
            "upload_photo": ChatAction.UPLOAD_PHOTO,
            "record_video": ChatAction.RECORD_VIDEO,
            "upload_video": ChatAction.UPLOAD_VIDEO,
            "record_voice": ChatAction.RECORD_VOICE,
            "upload_voice": ChatAction.UPLOAD_VOICE,
            "upload_document": ChatAction.UPLOAD_DOCUMENT,
            "choose_sticker": ChatAction.CHOOSE_STICKER,
            "find_location": ChatAction.FIND_LOCATION
        }
        
        return action_map.get(action_type, ChatAction.TYPING) 