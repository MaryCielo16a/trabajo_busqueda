"""
Vercel Serverless Function - Job Search API
Single file with all logic embedded for Vercel compatibility.
"""
import json
import hashlib
import os
import sqlite3
import time
import smtplib
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

import requests
from bs4 import BeautifulSoup

# ---- CONFIG ----
DB_PATH = "/tmp/jobs.db"
KEYWORDS = os.getenv(
    "KEYWORDS",
    "react,frontend,javascript,vue,angular,html,css,node.js,junior,trainee"
).split(",")
REMOTE_ONLY = os.getenv("REMOTE_ONLY", "true").lower() == "true"

COMPUTRABAJO_BASE_URL = os.getenv("COMPUTRABAJO_BASE_URL", "https://www.computrabajo.com.co")
BUMERAN_BASE_URL = os.getenv("BUMERAN_BASE_URL", "https://www.bumeran.com.co")

SENDER_EMAIL = os.getenv("SENDER_EMAIL", "")
SENDER_APP_PASSWORD = os.getenv("SENDER_APP_PASSWORD", "")
RECIPIENT_EMAILS = os.getenv(
    "RECIPIENT_EMAILS",
    "anamariatapiahurtado3@gmail.com,u20211e348@gmail.com"
).split(",")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "es-ES,es;q=0.9",
}


# ---- DATABASE ----
def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS jobs (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            company TEXT NOT NULL,
            location TEXT,
            salary TEXT,
            description TEXT,
            url TEXT UNIQUE NOT NULL,
            source TEXT,
            posted_date TEXT,
            scraped_date TEXT,
            is_remote INTEGER DEFAULT 0,
            required_experience TEXT
        )
    """)
    conn.commit()
    conn.close()


def get_jobs(limit=50, remote_only=True):
    init_db()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    if remote_only:
        rows = conn.execute(
            "SELECT * FROM jobs WHERE is_remote = 1 ORDER BY scraped_date DESC LIMIT ?",
            (limit,)
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM jobs ORDER BY scraped_date DESC LIMIT ?",
            (limit,)
        ).fetchall()

    conn.close()
    return [dict(r) for r in rows]


def get_stats():
    init_db()
    conn = sqlite3.connect(DB_PATH)
    total = conn.execute("SELECT COUNT(*) FROM jobs").fetchone()[0]
    remote = conn.execute("SELECT COUNT(*) FROM jobs WHERE is_remote = 1").fetchone()[0]

    by_source = {}
    for source in ["computrabajo", "bumeran", "linkedin"]:
        count = conn.execute("SELECT COUNT(*) FROM jobs WHERE source = ?", (source,)).fetchone()[0]
        if count > 0:
            by_source[source] = count

    conn.close()
    return {"total_jobs": total, "remote_jobs": remote, "by_source": by_source}


def save_job(job_data):
    init_db()
    conn = sqlite3.connect(DB_PATH)
    try:
        conn.execute("""
            INSERT OR IGNORE INTO jobs (id, title, company, location, salary, url, source, is_remote, scraped_date, posted_date)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            job_data["id"],
            job_data["title"],
            job_data["company"],
            job_data.get("location", ""),
            job_data.get("salary", ""),
            job_data["url"],
            job_data["source"],
            1 if job_data.get("is_remote") else 0,
            datetime.now().isoformat(),
            job_data.get("posted_date", datetime.now().isoformat()),
        ))
        conn.commit()
        added = conn.total_changes
    except Exception:
        added = 0
    finally:
        conn.close()
    return added


# ---- SCRAPERS ----
def scrape_computrabajo(keywords, pages=1):
    jobs = []
    session = requests.Session()
    session.headers.update(HEADERS)

    for keyword in keywords:
        kw = keyword.strip()
        if not kw:
            continue
        for page in range(1, pages + 1):
            urls = [
                f"{COMPUTRABAJO_BASE_URL}/trabajo-de-{kw.replace(' ', '-')}",
                f"{COMPUTRABAJO_BASE_URL}/bt_{kw.replace(' ', '-')}/p_{page}",
            ]
            for url in urls:
                try:
                    resp = session.get(url, timeout=8)
                    if resp.status_code != 200:
                        continue
                    soup = BeautifulSoup(resp.content, "html.parser")

                    for sel in [
                        ("article", {}),
                        ("div", {"class": "box_offer"}),
                        ("div", {"class": "aviso"}),
                        ("div", {"class": "iO"}),
                    ]:
                        elems = soup.find_all(sel[0], sel[1]) if sel[1] else soup.find_all(sel[0])
                        if not elems:
                            continue
                        for el in elems:
                            a = el.find("a")
                            if not a:
                                continue
                            title = a.get_text(strip=True)
                            href = a.get("href", "")
                            if not title or len(title) < 5:
                                continue
                            if not href.startswith("http"):
                                href = COMPUTRABAJO_BASE_URL + href

                            company_el = el.find("a", {"class": "fc_base"}) or el.find("span")
                            company = company_el.get_text(strip=True) if company_el else "Empresa"

                            location = ""
                            for loc_el in el.find_all("span"):
                                t = loc_el.get_text(strip=True)
                                if any(w in t.lower() for w in ["bogotá", "medellín", "cali", "remoto", "colombia", "home"]):
                                    location = t
                                    break

                            is_remote = any(w in (title + location).lower() for w in ["remoto", "remote", "home office", "teletrabajo", "virtual"])

                            jobs.append({
                                "id": hashlib.md5(href.encode()).hexdigest(),
                                "title": title,
                                "company": company,
                                "location": location or "Colombia",
                                "salary": "",
                                "url": href,
                                "source": "computrabajo",
                                "is_remote": is_remote,
                            })
                        if jobs:
                            break
                except Exception:
                    continue
            time.sleep(0.5)
    return jobs


def scrape_bumeran(keywords, pages=1):
    jobs = []
    session = requests.Session()
    session.headers.update(HEADERS)

    for keyword in keywords:
        kw = keyword.strip()
        if not kw:
            continue
        for page in range(1, pages + 1):
            urls = [
                f"{BUMERAN_BASE_URL}/empleos-busqueda-{kw.replace(' ', '-')}.html",
                f"{BUMERAN_BASE_URL}/empleos-buscar-{kw.replace(' ', '-')}-pagina-{page}.html",
            ]
            for url in urls:
                try:
                    resp = session.get(url, timeout=8)
                    if resp.status_code != 200:
                        continue
                    soup = BeautifulSoup(resp.content, "html.parser")

                    for sel in [
                        ("div", {"class": "aviso"}),
                        ("div", {"class": "listing-offer"}),
                        ("article", {}),
                    ]:
                        elems = soup.find_all(sel[0], sel[1]) if sel[1] else soup.find_all(sel[0])
                        if not elems:
                            continue
                        for el in elems:
                            a = el.find("a")
                            if not a:
                                continue
                            title = a.get_text(strip=True)
                            href = a.get("href", "")
                            if not title or len(title) < 5:
                                continue
                            if not href.startswith("http"):
                                href = BUMERAN_BASE_URL + href

                            company = "Empresa"
                            location = "Colombia"
                            is_remote = any(w in title.lower() for w in ["remoto", "remote", "home office", "virtual"])

                            jobs.append({
                                "id": hashlib.md5(href.encode()).hexdigest(),
                                "title": title,
                                "company": company,
                                "location": location,
                                "salary": "",
                                "url": href,
                                "source": "bumeran",
                                "is_remote": is_remote,
                            })
                        if jobs:
                            break
                except Exception:
                    continue
            time.sleep(0.5)
    return jobs


# ---- EMAIL ----
def send_email(jobs):
    if not SENDER_EMAIL or not SENDER_APP_PASSWORD or not jobs:
        return False

    subject = f"💼 {len(jobs)} nueva(s) oferta(s) de trabajo - {datetime.now().strftime('%d/%m/%Y %H:%M')}"

    cards = ""
    for j in jobs:
        remote_badge = '<span style="color:#4caf50;font-weight:bold;">✅ Remoto</span>' if j.get("is_remote") else f'📍 {j.get("location", "")}'
        cards += f"""
        <div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin-bottom:12px;background:white;">
            <h3 style="margin:0 0 4px;color:#333;font-size:15px;">{j['title']}</h3>
            <p style="color:#666;margin:2px 0;">🏢 {j['company']}</p>
            <p style="color:#777;margin:2px 0;">{remote_badge}</p>
            <a href="{j['url']}" style="display:inline-block;margin-top:8px;padding:8px 16px;background:#667eea;color:white;text-decoration:none;border-radius:5px;font-size:13px;">Ver oferta →</a>
        </div>"""

    html = f"""
    <html><body style="font-family:sans-serif;background:#f5f5f5;padding:20px;">
    <div style="max-width:600px;margin:0 auto;">
        <div style="background:linear-gradient(135deg,#667eea,#764ba2);padding:20px;border-radius:10px 10px 0 0;text-align:center;">
            <h1 style="color:white;margin:0;font-size:20px;">💼 Nuevas ofertas de trabajo</h1>
            <p style="color:rgba(255,255,255,0.9);margin:6px 0 0;">{len(jobs)} oferta(s) encontrada(s)</p>
        </div>
        <div style="background:white;padding:20px;border-radius:0 0 10px 10px;">
            {cards}
            <p style="color:#999;font-size:11px;text-align:center;margin-top:20px;">
                Enviado por Job Search Automation - {datetime.now().strftime('%d/%m/%Y %H:%M')}
            </p>
        </div>
    </div>
    </body></html>"""

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = SENDER_EMAIL
        msg.attach(MIMEText(html, "html", "utf-8"))

        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(SENDER_EMAIL, SENDER_APP_PASSWORD)
            for r in RECIPIENT_EMAILS:
                r = r.strip()
                if r:
                    msg["To"] = r
                    server.sendmail(SENDER_EMAIL, r, msg.as_string())
                    del msg["To"]
        return True
    except Exception as e:
        print(f"Email error: {e}")
        return False


# ---- HANDLER ----
class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/")
        params = parse_qs(parsed.query)

        if path == "/api/jobs":
            limit = int(params.get("limit", ["50"])[0])
            remote = params.get("remote_only", ["true"])[0].lower() == "true"
            jobs = get_jobs(limit=limit, remote_only=remote)
            self._json_response(200, {"success": True, "count": len(jobs), "jobs": jobs})

        elif path == "/api/stats":
            stats = get_stats()
            self._json_response(200, {"success": True, **stats})

        elif path == "/api/scrape_status":
            self._json_response(200, {"is_scraping": False, "progress": 100})

        else:
            self._json_response(404, {"success": False, "error": "Not found"})

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/")

        if path == "/api/scrape":
            try:
                keywords = [k.strip() for k in KEYWORDS if k.strip()]

                ct_jobs = scrape_computrabajo(keywords, pages=1)
                bm_jobs = scrape_bumeran(keywords, pages=1)

                all_jobs = ct_jobs + bm_jobs
                added = 0
                for j in all_jobs:
                    added += save_job(j)

                email_sent = False
                if all_jobs:
                    email_sent = send_email(all_jobs)

                self._json_response(200, {
                    "success": True,
                    "message": f"Found {len(all_jobs)} jobs, added {added} new.",
                    "email_sent": email_sent,
                    "jobs_found": len(all_jobs),
                })
            except Exception as e:
                self._json_response(500, {"success": False, "error": str(e)})

        elif path == "/api/clear":
            try:
                init_db()
                conn = sqlite3.connect(DB_PATH)
                conn.execute("DELETE FROM jobs")
                conn.commit()
                conn.close()
                self._json_response(200, {"success": True, "message": "Database cleared"})
            except Exception as e:
                self._json_response(500, {"success": False, "error": str(e)})
        else:
            self._json_response(404, {"success": False, "error": "Not found"})

    def do_DELETE(self):
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/")

        if path == "/api/jobs":
            try:
                init_db()
                conn = sqlite3.connect(DB_PATH)
                conn.execute("DELETE FROM jobs")
                conn.commit()
                conn.close()
                self._json_response(200, {"success": True, "message": "Database cleared"})
            except Exception as e:
                self._json_response(500, {"success": False, "error": str(e)})
        else:
            self._json_response(404, {"success": False, "error": "Not found"})

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def _json_response(self, status, data):
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())
