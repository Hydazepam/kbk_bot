import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("TELEGRAM_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))
DB_URL = os.getenv("DATABASE_URL")

# import os

# TOKEN = os.getenv("TELEGRAM_TOKEN")
# ADMIN_ID = int(os.getenv("ADMIN_ID"))
# DB_URL = os.getenv("DATABASE_URL")