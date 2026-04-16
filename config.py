import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Bot Configuration
BOT_TOKEN = os.getenv("BOT_TOKEN")

# API Configuration
API_KEY = os.getenv("API_KEY")
API_URL = os.getenv("API_URL")

# Channel Configuration (Force Subscribe)
CHANNEL_USERNAME = os.getenv("CHANNEL_USERNAME")

# Owner Configuration
OWNER_ID = int(os.getenv("OWNER_ID")) if os.getenv("OWNER_ID") else None

# Optional: Daily Limit (hardcoded or from .env)
DAILY_LIMIT = int(os.getenv("DAILY_LIMIT", 10))  # Default 10 if not in .env

# Database file name
DATABASE_NAME = os.getenv("DATABASE_NAME", "bot_database.db")

# Validate required configurations
def validate_config():
    """Check if all required configs are present"""
    errors = []
    
    if not BOT_TOKEN:
        errors.append("BOT_TOKEN is missing in .env file")
    if not API_KEY:
        errors.append("API_KEY is missing in .env file")
    if not API_URL:
        errors.append("API_URL is missing in .env file")
    if not CHANNEL_USERNAME:
        errors.append("CHANNEL_USERNAME is missing in .env file")
    if not OWNER_ID:
        errors.append("OWNER_ID is missing in .env file")
    
    if errors:
        print("❌ Configuration Errors:")
        for error in errors:
            print(f"   • {error}")
        print("\n⚠️ Please check your .env file!")
        return False
    
    print("✅ Configuration loaded successfully!")
    print(f"📊 Daily Limit: {DAILY_LIMIT} uses per user")
    print(f"📢 Channel: {CHANNEL_USERNAME}")
    print(f"👑 Owner ID: {OWNER_ID}")
    return True

# Export all variables
__all__ = [
    'BOT_TOKEN',
    'API_KEY', 
    'API_URL',
    'CHANNEL_USERNAME',
    'OWNER_ID',
    'DAILY_LIMIT',
    'DATABASE_NAME',
    'validate_config'
]
