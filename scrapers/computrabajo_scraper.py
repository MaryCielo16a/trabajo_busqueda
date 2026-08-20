import requests
from bs4 import BeautifulSoup
from datetime import datetime
from config.settings import COMPUTRABAJO_BASE_URL, REMOTE_ONLY
from database.models import Job, get_session
import hashlib
import logging
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ComputrabajoScraper:
    def __init__(self):
        self.base_url = COMPUTRABAJO_BASE_URL
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "es-ES,es;q=0.9",
            "Referer": self.base_url,
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)

    def search_jobs(self, keywords: list, pages: int = 3):
        jobs = []
        for keyword in keywords:
            logger.info(f"Searching Computrabajo for: {keyword}")
            try:
                for page in range(1, pages + 1):
                    # Try multiple URL patterns
                    urls_to_try = [
                        f"{self.base_url}/bt_{keyword.replace(' ', '-')}/p_{page}",
                        f"{self.base_url}/busquedas/{keyword.replace(' ', '+')}/page/{page}",
                        f"{self.base_url}/busquedas/{keyword.replace(' ', '-')}/{page}",
                    ]

                    success = False
                    for url in urls_to_try:
                        try:
                            response = self.session.get(url, timeout=10)
                            if response.status_code == 200:
                                soup = BeautifulSoup(response.content, 'html.parser')
                                job_listings = self._find_job_elements(soup)

                                if job_listings:
                                    for job in job_listings:
                                        try:
                                            job_data = self._parse_job(job, keyword)
                                            if job_data:
                                                jobs.append(job_data)
                                        except Exception as e:
                                            logger.debug(f"Error parsing job: {e}")
                                            continue
                                    success = True
                                    break
                        except requests.RequestException as e:
                            continue

                    if not success:
                        logger.debug(f"No results for {keyword} page {page}")

                    time.sleep(1)  # Be nice to the server
            except Exception as e:
                logger.error(f"Error searching for {keyword}: {e}")

        return jobs

    def _find_job_elements(self, soup):
        # Try different selectors commonly used in job boards
        selectors = [
            ('div', {'class': 'aviso'}),
            ('div', {'class': 'job-item'}),
            ('div', {'class': 'offer'}),
            ('article', {'class': 'job'}),
            ('li', {'class': 'job-listing'}),
        ]

        for tag, attrs in selectors:
            elements = soup.find_all(tag, attrs)
            if elements:
                return elements

        return []

    def _parse_job(self, job_element, keyword):
        try:
            title_elem = job_element.find('a', {'class': 'aviso_titulo'})
            if not title_elem:
                return None

            title = title_elem.get_text(strip=True)
            url = title_elem.get('href', '')
            if not url.startswith('http'):
                url = self.base_url + url

            company_elem = job_element.find('div', {'class': 'aviso_empresa'})
            company = company_elem.get_text(strip=True) if company_elem else "Unknown"

            location_elem = job_element.find('div', {'class': 'aviso_lugar'})
            location = location_elem.get_text(strip=True) if location_elem else "Not specified"

            salary_elem = job_element.find('div', {'class': 'aviso_salario'})
            salary = salary_elem.get_text(strip=True) if salary_elem else "Not specified"

            is_remote = "remoto" in location.lower() or "home" in location.lower()

            job_id = hashlib.md5(url.encode()).hexdigest()

            return {
                "id": job_id,
                "title": title,
                "company": company,
                "location": location,
                "salary": salary,
                "url": url,
                "source": "computrabajo",
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

        logger.info(f"Computrabajo: Added {added} new jobs, {duplicates} duplicates")
        return added, duplicates
