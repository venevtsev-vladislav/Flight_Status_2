#!/usr/bin/env python3
"""
Flight Status Bot - Main entry point for hosting
"""
import sys
import os

# Add the bot directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'bot'))

# Import and run the bot
from bot.main import main
import asyncio

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Bot stopped by user")
    except Exception as e:
        print(f"Bot stopped due to error: {e}")
        sys.exit(1) 