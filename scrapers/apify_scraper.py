"""
Apify scraper for job boards (alternative when direct scraping fails)

Note: Requires Apify API key in environment variable APIFY_API_KEY
Get it from: https://apify.com
"""

import requests
import logging
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ApifyScraper:
    def __init__(self):
        self.api_key = os.getenv("APIFY_API_KEY")
        self.base_url = "https://api.apify.com/v2"

        if not self.api_key:
            logger.warning("APIFY_API_KEY not set. Apify scraper disabled.")
            self.enabled = False
        else:
            self.enabled = True

    def scrape_computrabajo(self, keywords: list, limit: int = 100):
        """Scrape jobs from Computrabajo using Apify"""
        if not self.enabled:
            return []

        try:
            actor_id = "shahidirfan/computrabajo-jobs-scraper"
            url = f"{self.base_url}/acts/{actor_id}/run-sync-get-dataset-items"

            payload = {
                "searchQuery": " OR ".join(keywords),
                "maxItems": limit
            }

            headers = {
                "Content-Type": "application/json"
            }

            response = requests.post(
                url,
                json=payload,
                headers=headers,
                params={"token": self.api_key},
                timeout=60
            )

            if response.status_code == 200:
                jobs = response.json()
                logger.info(f"Apify: Found {len(jobs)} jobs from Computrabajo")
                return self._format_apify_results(jobs, "computrabajo")
            else:
                logger.error(f"Apify error: {response.status_code}")
                return []

        except Exception as e:
            logger.error(f"Error using Apify scraper: {e}")
            return []

    def scrape_bumeran(self, keywords: list, limit: int = 100):
        """Scrape jobs from Bumerán using Apify"""
        if not self.enabled:
            return []

        try:
            actor_id = "blackfalcondata/bumeran-scraper"
            url = f"{self.base_url}/acts/{actor_id}/run-sync-get-dataset-items"

            payload = {
                "keyword": " ".join(keywords),
                "maxItems": limit
            }

            response = requests.post(
                url,
                json=payload,
                params={"token": self.api_key},
                timeout=60
            )

            if response.status_code == 200:
                jobs = response.json()
                logger.info(f"Apify: Found {len(jobs)} jobs from Bumerán")
                return self._format_apify_results(jobs, "bumeran")
            else:
                logger.error(f"Apify error: {response.status_code}")
                return []

        except Exception as e:
            logger.error(f"Error using Apify scraper: {e}")
            return []

    def _format_apify_results(self, jobs, source):
        formatted = []
        for job in jobs:
            formatted.append({
                "id": job.get("url", "").split("/")[-1],
                "title": job.get("title", ""),
                "company": job.get("company", ""),
                "location": job.get("location", ""),
                "salary": job.get("salary", ""),
                "url": job.get("url", ""),
                "source": source,
                "is_remote": "remoto" in str(job.get("location", "")).lower(),
            })
        return formatted
