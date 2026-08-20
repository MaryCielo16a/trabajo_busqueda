import requests
from bs4 import BeautifulSoup
from datetime import datetime
from config.settings import BUMERAN_BASE_URL, HEADERS
from database.models import Job, get_session
import hashlib
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BumeranScraper:
    def __init__(self):
        self.base_url = BUMERAN_BASE_URL
        self.headers = HEADERS

    def search_jobs(self, keywords: list, pages: int = 3):
        jobs = []
        for keyword in keywords:
            logger.info(f"Searching Bumerán for: {keyword}")
            try:
                for page in range(1, pages + 1):
                    url = f"{self.base_url}/empleos-buscar-{keyword}-pagina-{page}.html"
                    response = requests.get(url, headers=self.headers, timeout=10)
                    response.encoding = 'utf-8'

                    if response.status_code == 200:
                        soup = BeautifulSoup(response.content, 'html.parser')
                        job_listings = soup.find_all('div', {'class': 'listing-offer'})

                        for job in job_listings:
                            try:
                                job_data = self._parse_job(job, keyword)
                                if job_data:
                                    jobs.append(job_data)
                            except Exception as e:
                                logger.error(f"Error parsing job: {e}")
                                continue
                    else:
                        logger.warning(f"Failed to fetch page {page} for {keyword}")
            except Exception as e:
                logger.error(f"Error searching for {keyword}: {e}")

        return jobs

    def _parse_job(self, job_element, keyword):
        try:
            title_elem = job_element.find('a', {'class': 'position-link'})
            if not title_elem:
                return None

            title = title_elem.get_text(strip=True)
            url = title_elem.get('href', '')
            if not url.startswith('http'):
                url = self.base_url + url

            company_elem = job_element.find('div', {'class': 'position-company'})
            company = company_elem.get_text(strip=True) if company_elem else "Unknown"

            location_elem = job_element.find('div', {'class': 'position-location'})
            location = location_elem.get_text(strip=True) if location_elem else "Not specified"

            salary_elem = job_element.find('div', {'class': 'position-salary'})
            salary = salary_elem.get_text(strip=True) if salary_elem else "Not specified"

            is_remote = "remoto" in location.lower() or "home" in location.lower() or "virtual" in location.lower()

            job_id = hashlib.md5(url.encode()).hexdigest()

            return {
                "id": job_id,
                "title": title,
                "company": company,
                "location": location,
                "salary": salary,
                "url": url,
                "source": "bumeran",
                "is_remote": is_remote,
                "keyword": keyword,
                "posted_date": datetime.now()
            }
        except Exception as e:
            logger.error(f"Error parsing job element: {e}")
            return None

    def save_jobs(self, jobs: list):
        session = get_session()
        added = 0
        duplicates = 0

        for job_data in jobs:
            try:
                existing = session.query(Job).filter_by(url=job_data['url']).first()
                if not existing:
                    job = Job(**job_data)
                    session.add(job)
                    added += 1
                else:
                    duplicates += 1
            except Exception as e:
                logger.error(f"Error saving job: {e}")

        session.commit()
        session.close()

        logger.info(f"Bumerán: Added {added} new jobs, {duplicates} duplicates")
        return added, duplicates
