import json
import sys
import os
from http.server import BaseHTTPRequestHandler

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.models import init_db
from filters.job_filter import JobFilter

init_db()

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            job_filter = JobFilter()
            stats = job_filter.get_stats()

            result = {
                "success": True,
                "total_jobs": stats["total_jobs"],
                "remote_jobs": stats["remote_jobs"],
                "by_source": stats["by_source"]
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
