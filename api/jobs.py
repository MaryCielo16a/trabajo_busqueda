import json
import sys
import os
from http.server import BaseHTTPRequestHandler

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.models import get_session, Job, init_db
from filters.job_filter import JobFilter

# Ensure DB exists
init_db()

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            job_filter = JobFilter(remote_only=True)
            jobs = job_filter.filter_jobs(limit=50)

            result = {
                "success": True,
                "count": len(jobs),
                "jobs": [
                    {
                        "id": job.id,
                        "title": job.title,
                        "company": job.company,
                        "location": job.location,
                        "salary": job.salary,
                        "url": job.url,
                        "source": job.source,
                        "is_remote": job.is_remote,
                        "posted_date": job.scraped_date.isoformat() if job.scraped_date else None,
                    }
                    for job in jobs
                ]
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
