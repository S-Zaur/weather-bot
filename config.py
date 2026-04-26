from dotenv import load_dotenv
import os

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
DATABASE_URL = os.getenv("DATABASE_URL")
CHAT_ID = os.getenv("CHAT_ID")
PROXY = os.getenv("PROXY")
LAT = 57.159890
LON = 65.591482
