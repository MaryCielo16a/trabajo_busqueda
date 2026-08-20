#!/usr/bin/env python3
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import threading
import logging

from scrapers.computrabajo_scraper import ComputrabajoScraper
from scrapers.bumeran_scraper import BumeranScraper
from filters.job_filter import JobFilter
from database.models import get_session, Job
from config.settings import KEYWORDS

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global state
scraping_status = {"is_scraping": False, "progress": 0}

def scrape_background(pages: int):
    """Background scraping task"""
    try:
        scraping_status["is_scraping"] = True
        scraping_status["progress"] = 0

        keywords = [k.strip() for k in KEYWORDS if k.strip()]

        # Computrabajo
        logger.info("Scraping Computrabajo...")
        ct = ComputrabajoScraper()
        ct_jobs = ct.search_jobs(keywords, pages)
        ct.save_jobs(ct_jobs)
        scraping_status["progress"] = 50

        # Bumerán
        logger.info("Scraping Bumerán...")
        bm = BumeranScraper()
        bm_jobs = bm.search_jobs(keywords, pages)
        bm.save_jobs(bm_jobs)
        scraping_status["progress"] = 100

        logger.info("Scraping completed!")
    except Exception as e:
        logger.error(f"Scraping error: {e}")
    finally:
        scraping_status["is_scraping"] = False

@app.get("/")
async def root():
    """Serve main page"""
    return FileResponse("web/static/index.html")

@app.get("/api/jobs")
async def get_jobs(limit: int = 20, remote_only: bool = True):
    """Get filtered job listings"""
    try:
        job_filter = JobFilter(remote_only=remote_only)
        jobs = job_filter.filter_jobs(limit=limit)

        return {
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
    except Exception as e:
        logger.error(f"Error getting jobs: {e}")
        return {"success": False, "error": str(e)}

@app.get("/api/stats")
async def get_stats():
    """Get database statistics"""
    try:
        job_filter = JobFilter()
        stats = job_filter.get_stats()

        return {
            "success": True,
            "total_jobs": stats["total_jobs"],
            "remote_jobs": stats["remote_jobs"],
            "by_source": stats["by_source"]
        }
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        return {"success": False, "error": str(e)}

@app.post("/api/scrape")
async def scrape_jobs(pages: int = 3):
    """Start scraping jobs"""
    if scraping_status["is_scraping"]:
        return {
            "success": False,
            "error": "Scraping already in progress",
            "progress": scraping_status["progress"]
        }

    # Start scraping in background thread
    thread = threading.Thread(target=scrape_background, args=(pages,))
    thread.daemon = True
    thread.start()

    return {
        "success": True,
        "message": f"Starting scrape for {pages} pages per keyword..."
    }

@app.get("/api/scrape/status")
async def scrape_status():
    """Get scraping status"""
    return {
        "is_scraping": scraping_status["is_scraping"],
        "progress": scraping_status["progress"]
    }

@app.delete("/api/jobs")
async def clear_jobs():
    """Clear all jobs from database"""
    try:
        session = get_session()
        session.query(Job).delete()
        session.commit()
        session.close()

        return {
            "success": True,
            "message": "Database cleared"
        }
    except Exception as e:
        logger.error(f"Error clearing database: {e}")
        return {"success": False, "error": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
