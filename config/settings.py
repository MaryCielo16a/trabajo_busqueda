import os
from dotenv import load_dotenv

load_dotenv()

# Database
DB_PATH = os.getenv("DB_PATH", "jobs.db")

# Search preferences
REMOTE_ONLY = os.getenv("REMOTE_ONLY", "true").lower() == "true"
KEYWORDS = os.getenv("KEYWORDS", "frontend,react,vue,angular,javascript,python,fullstack,data analyst").split(",")
MIN_EXPERIENCE_LEVEL = os.getenv("MIN_EXPERIENCE_LEVEL", "junior")  # junior, trainee, sin experiencia

# Scraping settings
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

# Job board URLs - Adjust for your country
# Colombia: .com.co | Argentina: .com.ar | Mexico: .com.mx | Chile: .cl
COMPUTRABAJO_BASE_URL = "https://www.computrabajo.com.co"  # Works for most countries
BUMERAN_BASE_URL = "https://www.bumeran.com.co"  # Adjust to your country

# Schedule settings
SCRAPE_INTERVAL_MINUTES = int(os.getenv("SCRAPE_INTERVAL_MINUTES", "60"))
