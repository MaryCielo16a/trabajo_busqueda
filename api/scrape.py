import json
import sys
import os
from http.server import BaseHTTPRequestHandler

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scrapers.computrabajo_scraper import ComputrabajoScraper
from scrapers.bumeran_scraper import BumeranScraper
from database.models import init_db
from config.settings import KEYWORDS

init_db()

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            keywords = [k.strip() for k in KEYWORDS if k.strip()]

            ct = ComputrabajoScraper()
            ct_jobs = ct.search_jobs(keywords, pages=1)
            ct_added, _ = ct.save_jobs(ct_jobs)

            bm = BumeranScraper()
            bm_jobs = bm.search_jobs(keywords, pages=1)
            bm_added, _ = bm.save_jobs(bm_jobs)

            result = {
                "success": True,
                "message": f"Scraping completed. Added {ct_added + bm_added} new jobs."
            }

            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(result).encode())
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"success": False, "error": str(e)}).encode())

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
