import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "9205773343:AAEIyfpGpLaB4H0iMFE0mau8uEeyvILhG9s")
BOT_USERNAME = "Rinku_PANEL_BOT"
STORE_NAME = "RINKU PANEL STORE"
CURRENCY = "USDT"
ADMIN_IDS = [8198898522]  # Rinku's Telegram ID
SUPPORT_USERNAME = "all_iosx"  # Administrator username
CHANNEL_LINK = "https://t.me/all_iosx"

# Default Deposit Wallets (Admin can change anytime)
USDT_TRC20_WALLET = "TNP39vXkmBqRtW76eL7hMvF198eP8aZxPq"
USDT_BEP20_WALLET = "0x89205A3A3b2A69De6Dbf7f01ED13B2108B2c43e7"
USDT_TON_WALLET = "EQCD39VS5jcptHL8vMjEXrzGaRcCVYto7HUn4bpAOg8xqB2N"
