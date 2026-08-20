from database.models import Job, get_session
from config.settings import REMOTE_ONLY, KEYWORDS
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class JobFilter:
    def __init__(self, remote_only: bool = REMOTE_ONLY, keywords: list = None):
        self.remote_only = remote_only
        self.keywords = keywords or KEYWORDS

    def filter_jobs(self, limit: int = 20):
        session = get_session()
        query = session.query(Job)

        if self.remote_only:
            query = query.filter(Job.is_remote == True)
            logger.info("Filtering for remote jobs only")

        jobs = query.order_by(Job.scraped_date.desc()).limit(limit).all()

        filtered_jobs = self._filter_by_keywords(jobs)
        session.close()

        return filtered_jobs

    def _filter_by_keywords(self, jobs):
        filtered = []
        for job in jobs:
            if self._matches_keywords(job):
                filtered.append(job)
        return filtered

    def _matches_keywords(self, job: Job):
        title_lower = job.title.lower()
        description_lower = (job.description or "").lower()
        text = f"{title_lower} {description_lower}"

        for keyword in self.keywords:
            keyword_lower = keyword.strip().lower()
            if keyword_lower in text:
                return True
        return False

    def get_stats(self):
        session = get_session()
        total = session.query(Job).count()
        remote = session.query(Job).filter(Job.is_remote == True).count()
        by_source = {}

        for source in ['computrabajo', 'bumeran', 'linkedin']:
            count = session.query(Job).filter(Job.source == source).count()
            if count > 0:
                by_source[source] = count

        session.close()

        return {
            "total_jobs": total,
            "remote_jobs": remote,
            "by_source": by_source
        }
