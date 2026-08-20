"""
Vercel Serverless Function - Job Search API
Single file with all logic embedded for Vercel compatibility.
Configured for Peru job market.
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
from urllib.parse import urlparse, parse_qs, quote

import requests
from bs4 import BeautifulSoup

# ---- CONFIG ----
DB_PATH = "/tmp/jobs.db"
DEFAULT_KEYWORDS = "frontend remoto,react remoto,desarrollador junior,analista de datos,javascript remoto"

COMPUTRABAJO_BASE_URL = "https://www.computrabajo.com.pe"
BUMERAN_BASE_URL = "https://www.bumeran.com.pe"
INDEED_BASE_URL = "https://pe.indeed.com"
LINKEDIN_BASE_URL = "https://www.linkedin.com"

SENDER_EMAIL = os.getenv("SENDER_EMAIL", "")
SENDER_APP_PASSWORD = os.getenv("SENDER_APP_PASSWORD", "")
RECIPIENT_EMAILS = os.getenv(
    "RECIPIENT_EMAILS",
    "anamariatapiahurtado3@gmail.com,u20211e348@gmail.com"
).split(",")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "es-PE,es;q=0.9,en;q=0.8",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
}

PERU_CITIES = ["lima", "arequipa", "trujillo", "cusco", "piura", "chiclayo", "huancayo", "iquitos", "tacna", "callao", "peru", "remoto", "remote", "home"]
REMOTE_WORDS = ["remoto", "remote", "home office", "teletrabajo", "virtual", "trabajo desde casa", "work from home", "hibrido", "híbrido"]


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
    conn.execute("""
        CREATE TABLE IF NOT EXISTS filters (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            keyword TEXT NOT NULL UNIQUE,
            active INTEGER DEFAULT 1,
            created_date TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    """)
    existing = conn.execute("SELECT COUNT(*) FROM filters").fetchone()[0]
    if existing == 0:
        for kw in DEFAULT_KEYWORDS.split(","):
            kw = kw.strip()
            if kw:
                conn.execute(
                    "INSERT OR IGNORE INTO filters (keyword, active, created_date) VALUES (?, 1, ?)",
                    (kw, datetime.now().isoformat())
                )
        conn.execute(
            "INSERT OR IGNORE INTO settings (key, value) VALUES ('remote_only', 'true')"
        )
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
    for source in ["computrabajo", "bumeran", "indeed", "linkedin"]:
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


def get_active_keywords():
    init_db()
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute("SELECT keyword FROM filters WHERE active = 1").fetchall()
    conn.close()
    if rows:
        return [r[0] for r in rows]
    return [k.strip() for k in DEFAULT_KEYWORDS.split(",") if k.strip()]


def get_all_filters():
    init_db()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    rows = conn.execute("SELECT * FROM filters ORDER BY id").fetchall()
    remote_only = conn.execute("SELECT value FROM settings WHERE key = 'remote_only'").fetchone()
    conn.close()
    return {
        "filters": [dict(r) for r in rows],
        "remote_only": remote_only[0] == "true" if remote_only else True,
    }


def add_filter(keyword):
    init_db()
    conn = sqlite3.connect(DB_PATH)
    try:
        conn.execute(
            "INSERT INTO filters (keyword, active, created_date) VALUES (?, 1, ?)",
            (keyword.strip().lower(), datetime.now().isoformat())
        )
        conn.commit()
        result = True
    except sqlite3.IntegrityError:
        result = False
    conn.close()
    return result


def remove_filter(keyword):
    init_db()
    conn = sqlite3.connect(DB_PATH)
    conn.execute("DELETE FROM filters WHERE keyword = ?", (keyword.strip().lower(),))
    conn.commit()
    conn.close()


def toggle_filter(keyword, active):
    init_db()
    conn = sqlite3.connect(DB_PATH)
    conn.execute("UPDATE filters SET active = ? WHERE keyword = ?", (1 if active else 0, keyword.strip().lower()))
    conn.commit()
    conn.close()


def set_remote_only(value):
    init_db()
    conn = sqlite3.connect(DB_PATH)
    conn.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('remote_only', ?)", ("true" if value else "false",))
    conn.commit()
    conn.close()


def check_remote(text):
    return any(w in text.lower() for w in REMOTE_WORDS)


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
                    resp = session.get(url, timeout=6)
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
                                if any(w in t.lower() for w in PERU_CITIES):
                                    location = t
                                    break

                            is_remote = check_remote(title + " " + location)

                            jobs.append({
                                "id": hashlib.md5(href.encode()).hexdigest(),
                                "title": title,
                                "company": company,
                                "location": location or "Peru",
                                "salary": "",
                                "url": href,
                                "source": "computrabajo",
                                "is_remote": is_remote,
                            })
                        if jobs:
                            break
                except Exception:
                    continue
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
                    resp = session.get(url, timeout=6)
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
                            for span in el.find_all("span"):
                                t = span.get_text(strip=True)
                                if t and len(t) > 2 and t.lower() not in ["ver", "más", "nueva"]:
                                    company = t
                                    break

                            location = "Peru"
                            is_remote = check_remote(title)

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
    return jobs


def scrape_indeed(keywords, pages=1):
    jobs = []
    session = requests.Session()
    session.headers.update(HEADERS)

    for keyword in keywords:
        kw = keyword.strip()
        if not kw:
            continue
        for page in range(0, pages):
            start = page * 10
            url = f"{INDEED_BASE_URL}/jobs?q={quote(kw)}&l=Peru&start={start}"
            try:
                resp = session.get(url, timeout=6)
                if resp.status_code != 200:
                    continue
                soup = BeautifulSoup(resp.content, "html.parser")

                cards = soup.find_all("div", {"class": "job_seen_beacon"})
                if not cards:
                    cards = soup.find_all("div", {"class": "cardOutline"})
                if not cards:
                    cards = soup.find_all("td", {"class": "resultContent"})
                if not cards:
                    cards = soup.find_all("div", {"class": "slider_item"})

                for card in cards:
                    a = card.find("a")
                    if not a:
                        continue
                    title_el = card.find("h2") or card.find("span", {"title": True}) or a
                    title = title_el.get_text(strip=True) if title_el else a.get_text(strip=True)
                    href = a.get("href", "")

                    if not title or len(title) < 5:
                        continue
                    if not href.startswith("http"):
                        href = INDEED_BASE_URL + href

                    company_el = card.find("span", {"class": "companyName"}) or card.find("span", {"data-testid": "company-name"})
                    company = company_el.get_text(strip=True) if company_el else "Empresa"

                    location_el = card.find("div", {"class": "companyLocation"}) or card.find("div", {"data-testid": "text-location"})
                    location = location_el.get_text(strip=True) if location_el else "Peru"

                    salary_el = card.find("div", {"class": "salary-snippet-container"}) or card.find("span", {"class": "estimated-salary"})
                    salary = salary_el.get_text(strip=True) if salary_el else ""

                    is_remote = check_remote(title + " " + location)

                    jobs.append({
                        "id": hashlib.md5(href.encode()).hexdigest(),
                        "title": title,
                        "company": company,
                        "location": location,
                        "salary": salary,
                        "url": href,
                        "source": "indeed",
                        "is_remote": is_remote,
                    })
            except Exception:
                continue
    return jobs


def scrape_linkedin(keywords, pages=1):
    jobs = []
    session = requests.Session()
    session.headers.update(HEADERS)

    for keyword in keywords:
        kw = keyword.strip()
        if not kw:
            continue
        for page in range(0, pages):
            start = page * 25
            url = f"{LINKEDIN_BASE_URL}/jobs/search?keywords={quote(kw)}&location=Peru&f_WT=2&start={start}"
            try:
                resp = session.get(url, timeout=6)
                if resp.status_code != 200:
                    continue
                soup = BeautifulSoup(resp.content, "html.parser")

                cards = soup.find_all("div", {"class": "base-card"})
                if not cards:
                    cards = soup.find_all("li", {"class": "result-card"})
                if not cards:
                    cards = soup.find_all("div", {"class": "job-search-card"})

                for card in cards:
                    a = card.find("a")
                    if not a:
                        continue
                    title_el = card.find("h3") or card.find("span", {"class": "sr-only"})
                    title = title_el.get_text(strip=True) if title_el else a.get_text(strip=True)
                    href = a.get("href", "")

                    if not title or len(title) < 5:
                        continue
                    if "?" in href:
                        href = href.split("?")[0]

                    company_el = card.find("h4") or card.find("a", {"class": "hidden-nested-link"})
                    company = company_el.get_text(strip=True) if company_el else "Empresa"

                    location_el = card.find("span", {"class": "job-search-card__location"})
                    location = location_el.get_text(strip=True) if location_el else "Peru"

                    is_remote = check_remote(title + " " + location)

                    jobs.append({
                        "id": hashlib.md5(href.encode()).hexdigest(),
                        "title": title,
                        "company": company,
                        "location": location,
                        "salary": "",
                        "url": href,
                        "source": "linkedin",
                        "is_remote": is_remote,
                    })
            except Exception:
                continue
    return jobs


# ---- EMAIL ----
def send_email(jobs):
    if not SENDER_EMAIL or not SENDER_APP_PASSWORD or not jobs:
        return False

    subject = f"💼 {len(jobs)} nueva(s) oferta(s) de trabajo - {datetime.now().strftime('%d/%m/%Y %H:%M')}"

    source_colors = {
        "computrabajo": "#1976d2",
        "bumeran": "#7b1fa2",
        "indeed": "#2557a7",
        "linkedin": "#0a66c2",
    }

    cards = ""
    for j in jobs:
        remote_badge = '<span style="color:#4caf50;font-weight:bold;">✅ Remoto</span>' if j.get("is_remote") else f'📍 {j.get("location", "")}'
        color = source_colors.get(j.get("source", ""), "#667eea")
        salary_line = f'<p style="color:#555;margin:2px 0;">💰 {j["salary"]}</p>' if j.get("salary") else ""
        cards += f"""
        <div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin-bottom:12px;background:white;">
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:6px;">
                <h3 style="margin:0;color:#333;font-size:15px;">{j['title']}</h3>
                <span style="background:{color};color:white;padding:2px 10px;border-radius:12px;font-size:11px;">{j.get('source','').upper()}</span>
            </div>
            <p style="color:#666;margin:2px 0;">🏢 {j['company']}</p>
            <p style="color:#777;margin:2px 0;">{remote_badge}</p>
            {salary_line}
            <a href="{j['url']}" style="display:inline-block;margin-top:8px;padding:8px 16px;background:#667eea;color:white;text-decoration:none;border-radius:5px;font-size:13px;">Ver oferta →</a>
        </div>"""

    html = f"""
    <html><body style="font-family:sans-serif;background:#f5f5f5;padding:20px;">
    <div style="max-width:600px;margin:0 auto;">
        <div style="background:linear-gradient(135deg,#667eea,#764ba2);padding:20px;border-radius:10px 10px 0 0;text-align:center;">
            <h1 style="color:white;margin:0;font-size:20px;">💼 Nuevas ofertas de trabajo</h1>
            <p style="color:rgba(255,255,255,0.9);margin:6px 0 0;">{len(jobs)} oferta(s) encontrada(s) en Peru</p>
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

        elif path == "/api/filters":
            data = get_all_filters()
            self._json_response(200, {"success": True, **data})

        elif path == "/api/scrape_status":
            self._json_response(200, {"is_scraping": False, "progress": 100})

        elif path == "/api/cron":
            try:
                keywords = get_active_keywords()
                ct_jobs = scrape_computrabajo(keywords, pages=1)
                bm_jobs = scrape_bumeran(keywords, pages=1)
                in_jobs = scrape_indeed(keywords, pages=1)
                li_jobs = scrape_linkedin(keywords, pages=1)

                all_jobs = ct_jobs + bm_jobs + in_jobs + li_jobs
                added = 0
                for j in all_jobs:
                    added += save_job(j)

                email_sent = False
                if all_jobs:
                    email_sent = send_email(all_jobs)

                self._json_response(200, {
                    "success": True,
                    "message": f"Cron: {len(all_jobs)} ofertas, {added} nuevas.",
                    "email_sent": email_sent,
                    "jobs_found": len(all_jobs),
                })
            except Exception as e:
                self._json_response(500, {"success": False, "error": str(e)})

        else:
            self._json_response(404, {"success": False, "error": "Not found"})

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/")

        if path == "/api/scrape":
            try:
                keywords = get_active_keywords()

                ct_jobs = scrape_computrabajo(keywords, pages=1)
                bm_jobs = scrape_bumeran(keywords, pages=1)
                in_jobs = scrape_indeed(keywords, pages=1)
                li_jobs = scrape_linkedin(keywords, pages=1)

                all_jobs = ct_jobs + bm_jobs + in_jobs + li_jobs
                added = 0
                for j in all_jobs:
                    added += save_job(j)

                email_sent = False
                if all_jobs:
                    email_sent = send_email(all_jobs)

                self._json_response(200, {
                    "success": True,
                    "message": f"Encontradas {len(all_jobs)} ofertas, {added} nuevas guardadas.",
                    "email_sent": email_sent,
                    "jobs_found": len(all_jobs),
                    "by_source": {
                        "computrabajo": len(ct_jobs),
                        "bumeran": len(bm_jobs),
                        "indeed": len(in_jobs),
                        "linkedin": len(li_jobs),
                    }
                })
            except Exception as e:
                self._json_response(500, {"success": False, "error": str(e)})

        elif path == "/api/filters":
            try:
                content_length = int(self.headers.get("Content-Length", 0))
                body = json.loads(self.rfile.read(content_length)) if content_length else {}
                action = body.get("action", "add")
                keyword = body.get("keyword", "").strip().lower()

                if action == "add" and keyword:
                    ok = add_filter(keyword)
                    self._json_response(200, {"success": ok, "message": f"Filtro '{keyword}' agregado" if ok else "Filtro ya existe"})
                elif action == "remove" and keyword:
                    remove_filter(keyword)
                    self._json_response(200, {"success": True, "message": f"Filtro '{keyword}' eliminado"})
                elif action == "toggle":
                    active = body.get("active", True)
                    toggle_filter(keyword, active)
                    self._json_response(200, {"success": True, "message": f"Filtro '{keyword}' {'activado' if active else 'desactivado'}"})
                elif action == "set_remote":
                    set_remote_only(body.get("remote_only", True))
                    self._json_response(200, {"success": True})
                else:
                    self._json_response(400, {"success": False, "error": "Keyword requerido"})
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
