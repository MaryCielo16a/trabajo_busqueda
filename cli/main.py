#!/usr/bin/env python3
import sys
import argparse
from datetime import datetime
from scrapers.computrabajo_scraper import ComputrabajoScraper
from scrapers.bumeran_scraper import BumeranScraper
from filters.job_filter import JobFilter
from database.models import init_db, get_session, Job
from config.settings import KEYWORDS

def init_database():
    init_db()
    print("✓ Database initialized")

def scrape_all(pages: int = 3):
    print(f"\n{'='*60}")
    print(f"Starting job scraping... ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')})")
    print(f"{'='*60}\n")

    computrabajo = ComputrabajoScraper()
    bumeran = BumeranScraper()

    keywords = [k.strip() for k in KEYWORDS if k.strip()]

    print(f"Keywords: {', '.join(keywords)}\n")

    print("[1/2] Scraping Computrabajo...")
    ct_jobs = computrabajo.search_jobs(keywords, pages)
    ct_added, ct_dups = computrabajo.save_jobs(ct_jobs)

    print(f"[2/2] Scraping Bumerán...")
    bm_jobs = bumeran.search_jobs(keywords, pages)
    bm_added, bm_dups = bumeran.save_jobs(bm_jobs)

    print(f"\n{'='*60}")
    print("Scraping completed!")
    print(f"Total new jobs: {ct_added + bm_added}")
    print(f"Total duplicates: {ct_dups + bm_dups}")
    print(f"{'='*60}\n")

def list_jobs(limit: int = 20, remote_only: bool = True):
    job_filter = JobFilter(remote_only=remote_only)
    jobs = job_filter.filter_jobs(limit=limit)

    if not jobs:
        print("No jobs found matching your criteria.")
        return

    print(f"\n{'='*60}")
    print(f"Found {len(jobs)} jobs matching your criteria")
    print(f"{'='*60}\n")

    for idx, job in enumerate(jobs, 1):
        print(f"{idx}. {job.title}")
        print(f"   Company: {job.company}")
        print(f"   Location: {job.location}")
        if job.salary and job.salary != "Not specified":
            print(f"   Salary: {job.salary}")
        print(f"   Source: {job.source.capitalize()}")
        print(f"   Remote: {'✓' if job.is_remote else '✗'}")
        print(f"   URL: {job.url}")
        print(f"   Posted: {job.scraped_date.strftime('%Y-%m-%d %H:%M:%S')}")
        print()

def show_stats():
    job_filter = JobFilter()
    stats = job_filter.get_stats()

    print(f"\n{'='*60}")
    print("Job Search Statistics")
    print(f"{'='*60}")
    print(f"Total jobs in database: {stats['total_jobs']}")
    print(f"Remote jobs: {stats['remote_jobs']}")
    print(f"\nBy source:")
    for source, count in stats['by_source'].items():
        print(f"  - {source.capitalize()}: {count}")
    print(f"{'='*60}\n")

def clear_database():
    session = get_session()
    session.query(Job).delete()
    session.commit()
    session.close()
    print("✓ Database cleared")

def main():
    parser = argparse.ArgumentParser(
        description="Job Search Automation - Find your dream job automatically!"
    )

    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # Scrape command
    scrape_parser = subparsers.add_parser('scrape', help='Scrape job listings')
    scrape_parser.add_argument('--pages', type=int, default=3, help='Number of pages to scrape per keyword (default: 3)')

    # List command
    list_parser = subparsers.add_parser('list', help='List filtered jobs')
    list_parser.add_argument('--limit', type=int, default=20, help='Number of jobs to display (default: 20)')
    list_parser.add_argument('--all-locations', action='store_true', help='Include non-remote jobs')

    # Stats command
    stats_parser = subparsers.add_parser('stats', help='Show database statistics')

    # Init command
    init_parser = subparsers.add_parser('init', help='Initialize database')

    # Clear command
    clear_parser = subparsers.add_parser('clear', help='Clear database')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    if args.command == 'init':
        init_database()
    elif args.command == 'scrape':
        scrape_all(pages=args.pages)
    elif args.command == 'list':
        list_jobs(limit=args.limit, remote_only=not args.all_locations)
    elif args.command == 'stats':
        show_stats()
    elif args.command == 'clear':
        clear_database()

if __name__ == "__main__":
    main()
