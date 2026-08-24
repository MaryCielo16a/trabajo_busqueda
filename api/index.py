"""
Vercel Serverless Function - Job Search API v2
Single file with all logic embedded for Vercel compatibility.
Configured for Peru job market. Includes editable filters.
"""
import json
import hashlib
import os
import sqlite3
import time
import smtplib
import secrets
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
EMPLEOSPERU_BASE_URL = "https://www.empleosperu.gob.pe"
OPCIONEMPLEO_BASE_URL = "https://www.opcionempleo.pe"
JOBSFIRST_BASE_URL = "https://www.jobsfirst.pe"

CATEGORIES = {
    "frontend": ["frontend", "front-end", "front end", "react", "vue", "angular", "html", "css", "ui", "ux", "maquetador", "web developer"],
    "backend": ["backend", "back-end", "back end", "node", "python", "java", "php", "django", "fastapi", "spring", ".net", "c#"],
    "fullstack": ["fullstack", "full-stack", "full stack"],
    "data": ["data", "datos", "analista", "analyst", "bi", "power bi", "tableau", "sql", "excel", "etl", "ciencia de datos", "data science", "machine learning"],
    "mobile": ["mobile", "android", "ios", "flutter", "react native", "kotlin", "swift"],
    "devops": ["devops", "cloud", "aws", "azure", "docker", "kubernetes", "infraestructura", "sre"],
    "qa": ["qa", "testing", "tester", "quality", "calidad", "automatizacion de pruebas", "selenium"],
    "soporte": ["soporte", "support", "help desk", "mesa de ayuda", "tecnico", "helpdesk"],
    "otro": [],
}

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")

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
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            token TEXT UNIQUE,
            cv_profile TEXT,
            created_date TEXT,
            last_login TEXT
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
    for source in ["computrabajo", "bumeran", "indeed", "linkedin", "empleosperu", "opcionempleo", "jobsfirst"]:
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


def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


def register_user(name, email, password):
    init_db()
    conn = sqlite3.connect(DB_PATH)
    try:
        token = secrets.token_hex(32)
        conn.execute(
            "INSERT INTO users (name, email, password_hash, token, created_date, last_login) VALUES (?, ?, ?, ?, ?, ?)",
            (name.strip(), email.strip().lower(), hash_password(password), token, datetime.now().isoformat(), datetime.now().isoformat())
        )
        conn.commit()
        user = conn.execute("SELECT id, name, email, token FROM users WHERE email = ?", (email.strip().lower(),)).fetchone()
        conn.close()
        return {"id": user[0], "name": user[1], "email": user[2], "token": user[3]}
    except sqlite3.IntegrityError:
        conn.close()
        return None


def login_user(email, password):
    init_db()
    conn = sqlite3.connect(DB_PATH)
    row = conn.execute("SELECT id, name, email, password_hash, token FROM users WHERE email = ?", (email.strip().lower(),)).fetchone()
    if not row or row[3] != hash_password(password):
        conn.close()
        return None
    token = secrets.token_hex(32)
    conn.execute("UPDATE users SET token = ?, last_login = ? WHERE id = ?", (token, datetime.now().isoformat(), row[0]))
    conn.commit()
    conn.close()
    return {"id": row[0], "name": row[1], "email": row[2], "token": token}


def get_user_by_token(token):
    if not token:
        return None
    init_db()
    conn = sqlite3.connect(DB_PATH)
    row = conn.execute("SELECT id, name, email, token, cv_profile FROM users WHERE token = ?", (token,)).fetchone()
    conn.close()
    if not row:
        return None
    return {"id": row[0], "name": row[1], "email": row[2], "token": row[3], "cv_profile": row[4]}


def save_user_profile(token, cv_profile_json):
    init_db()
    conn = sqlite3.connect(DB_PATH)
    conn.execute("UPDATE users SET cv_profile = ? WHERE token = ?", (cv_profile_json, token))
    conn.commit()
    conn.close()


def update_user_info(token, name, email):
    init_db()
    conn = sqlite3.connect(DB_PATH)
    try:
        conn.execute("UPDATE users SET name = ?, email = ? WHERE token = ?", (name.strip(), email.strip().lower(), token))
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        conn.close()
        return False


def verify_google_token(id_token):
    try:
        resp = requests.get(
            f"https://oauth2.googleapis.com/tokeninfo?id_token={id_token}",
            timeout=10
        )
        if resp.status_code != 200:
            return None
        data = resp.json()
        if GOOGLE_CLIENT_ID and data.get("aud") != GOOGLE_CLIENT_ID:
            return None
        return {
            "email": data.get("email", ""),
            "name": data.get("name", ""),
            "picture": data.get("picture", ""),
            "google_id": data.get("sub", ""),
        }
    except Exception:
        return None


def google_auth_user(google_info):
    init_db()
    conn = sqlite3.connect(DB_PATH)
    email = google_info["email"].lower()
    row = conn.execute("SELECT id, name, email, token FROM users WHERE email = ?", (email,)).fetchone()
    token = secrets.token_hex(32)
    if row:
        conn.execute("UPDATE users SET token = ?, last_login = ? WHERE id = ?", (token, datetime.now().isoformat(), row[0]))
        conn.commit()
        conn.close()
        return {"id": row[0], "name": row[1], "email": row[2], "token": token}
    else:
        conn.execute(
            "INSERT INTO users (name, email, password_hash, token, created_date, last_login) VALUES (?, ?, ?, ?, ?, ?)",
            (google_info["name"], email, "google_oauth", token, datetime.now().isoformat(), datetime.now().isoformat())
        )
        conn.commit()
        user = conn.execute("SELECT id, name, email, token FROM users WHERE email = ?", (email,)).fetchone()
        conn.close()
        return {"id": user[0], "name": user[1], "email": user[2], "token": user[3]}


def classify_job(title):
    t = title.lower()
    for cat, words in CATEGORIES.items():
        if cat == "otro":
            continue
        if any(w in t for w in words):
            return cat
    return "otro"


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
                                "category": classify_job(title),
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
                                "category": classify_job(title),
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
                        "category": classify_job(title),
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
                        "category": classify_job(title),
                    })
            except Exception:
                continue
    return jobs


def scrape_empleosperu(keywords, pages=1):
    jobs = []
    session = requests.Session()
    session.headers.update(HEADERS)

    for keyword in keywords:
        kw = keyword.strip()
        if not kw:
            continue
        url = f"{EMPLEOSPERU_BASE_URL}/portal-empleos/buscar-empleo?keyword={quote(kw)}"
        try:
            resp = session.get(url, timeout=6)
            if resp.status_code != 200:
                continue
            soup = BeautifulSoup(resp.content, "html.parser")

            for sel in [
                ("div", {"class": "card"}),
                ("div", {"class": "job-item"}),
                ("div", {"class": "resultado"}),
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
                        href = EMPLEOSPERU_BASE_URL + href

                    company = "Estado Peruano"
                    for span in el.find_all(["span", "p", "div"]):
                        t = span.get_text(strip=True)
                        if t and len(t) > 3 and t != title and "empleo" not in t.lower():
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
                        "source": "empleosperu",
                        "is_remote": is_remote,
                        "category": classify_job(title),
                    })
                if jobs:
                    break
        except Exception:
            continue
    return jobs


def scrape_opcionempleo(keywords, pages=1):
    jobs = []
    session = requests.Session()
    session.headers.update(HEADERS)

    for keyword in keywords:
        kw = keyword.strip()
        if not kw:
            continue
        url = f"{OPCIONEMPLEO_BASE_URL}/buscar/empleos?s={quote(kw)}&l=Peru"
        try:
            resp = session.get(url, timeout=6)
            if resp.status_code != 200:
                continue
            soup = BeautifulSoup(resp.content, "html.parser")

            cards = soup.find_all("article")
            if not cards:
                cards = soup.find_all("div", {"class": "job"})
            if not cards:
                cards = soup.find_all("li", {"class": "job"})

            for card in cards:
                a = card.find("a")
                if not a:
                    continue
                title = a.get_text(strip=True)
                href = a.get("href", "")
                if not title or len(title) < 5:
                    continue
                if not href.startswith("http"):
                    href = OPCIONEMPLEO_BASE_URL + href

                company_el = card.find("span", {"class": "company"}) or card.find("p")
                company = company_el.get_text(strip=True) if company_el else "Empresa"

                location_el = card.find("span", {"class": "location"})
                location = location_el.get_text(strip=True) if location_el else "Peru"

                is_remote = check_remote(title + " " + location)

                jobs.append({
                    "id": hashlib.md5(href.encode()).hexdigest(),
                    "title": title,
                    "company": company,
                    "location": location,
                    "salary": "",
                    "url": href,
                    "source": "opcionempleo",
                    "is_remote": is_remote,
                    "category": classify_job(title),
                })
        except Exception:
            continue
    return jobs


def scrape_jobsfirst(keywords, pages=1):
    jobs = []
    session = requests.Session()
    session.headers.update(HEADERS)

    for keyword in keywords:
        kw = keyword.strip()
        if not kw:
            continue
        url = f"{JOBSFIRST_BASE_URL}/search?q={quote(kw)}&l=Peru"
        try:
            resp = session.get(url, timeout=6)
            if resp.status_code != 200:
                continue
            soup = BeautifulSoup(resp.content, "html.parser")

            cards = soup.find_all("div", {"class": "job-card"})
            if not cards:
                cards = soup.find_all("article")
            if not cards:
                cards = soup.find_all("div", {"class": "result"})
            if not cards:
                cards = soup.find_all("li", {"class": "job"})

            for card in cards:
                a = card.find("a")
                if not a:
                    continue
                title = a.get_text(strip=True)
                href = a.get("href", "")
                if not title or len(title) < 5:
                    continue
                if not href.startswith("http"):
                    href = JOBSFIRST_BASE_URL + href

                company_el = card.find("span", {"class": "company"}) or card.find("div", {"class": "company"}) or card.find("p")
                company = company_el.get_text(strip=True) if company_el else "Empresa"

                location_el = card.find("span", {"class": "location"}) or card.find("div", {"class": "location"})
                location = location_el.get_text(strip=True) if location_el else "Peru"

                is_remote = check_remote(title + " " + location)

                jobs.append({
                    "id": hashlib.md5(href.encode()).hexdigest(),
                    "title": title,
                    "company": company,
                    "location": location,
                    "salary": "",
                    "url": href,
                    "source": "jobsfirst",
                    "is_remote": is_remote,
                    "category": classify_job(title),
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
        "empleosperu": "#d32f2f",
        "opcionempleo": "#e65100",
        "jobsfirst": "#2e7d32",
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

        elif path == "/api/user/profile":
            auth = self.headers.get("Authorization", "")
            token = auth.replace("Bearer ", "") if auth.startswith("Bearer ") else ""
            if not token:
                self._json_response(401, {"success": False, "error": "Token requerido"})
                return
            user = get_user_by_token(token)
            if not user:
                self._json_response(401, {"success": False, "error": "Token invalido"})
                return
            cv_profile = None
            if user["cv_profile"]:
                try:
                    cv_profile = json.loads(user["cv_profile"])
                except Exception:
                    cv_profile = None
            self._json_response(200, {
                "success": True,
                "user": {"id": user["id"], "name": user["name"], "email": user["email"]},
                "cv_profile": cv_profile
            })

        elif path == "/api/auth/config":
            self._json_response(200, {
                "success": True,
                "google_client_id": GOOGLE_CLIENT_ID
            })

        elif path == "/api/cron":
            try:
                keywords = get_active_keywords()
                ct_jobs = scrape_computrabajo(keywords, pages=1)
                bm_jobs = scrape_bumeran(keywords, pages=1)
                in_jobs = scrape_indeed(keywords, pages=1)
                li_jobs = scrape_linkedin(keywords, pages=1)
                ep_jobs = scrape_empleosperu(keywords, pages=1)
                oe_jobs = scrape_opcionempleo(keywords, pages=1)
                jf_jobs = scrape_jobsfirst(keywords, pages=1)

                all_jobs = ct_jobs + bm_jobs + in_jobs + li_jobs + ep_jobs + oe_jobs + jf_jobs
                added = 0
                for j in all_jobs:
                    added += save_job(j)

                remote_jobs = [j for j in all_jobs if j.get("is_remote")]
                email_sent = False
                if remote_jobs:
                    email_sent = send_email(remote_jobs)

                self._json_response(200, {
                    "success": True,
                    "message": f"Cron: {len(all_jobs)} ofertas, {added} nuevas.",
                    "email_sent": email_sent,
                    "jobs_found": len(all_jobs),
                })
            except Exception as e:
                self._json_response(500, {"success": False, "error": str(e)})

        else:
            self._json_response(404, {"success": False, "error": "Not found", "path": path})

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
                ep_jobs = scrape_empleosperu(keywords, pages=1)
                oe_jobs = scrape_opcionempleo(keywords, pages=1)
                jf_jobs = scrape_jobsfirst(keywords, pages=1)

                all_jobs = ct_jobs + bm_jobs + in_jobs + li_jobs + ep_jobs + oe_jobs + jf_jobs
                added = 0
                for j in all_jobs:
                    added += save_job(j)

                remote_jobs = [j for j in all_jobs if j.get("is_remote")]
                email_sent = False
                if remote_jobs:
                    email_sent = send_email(remote_jobs)

                self._json_response(200, {
                    "success": True,
                    "message": f"Encontradas {len(all_jobs)} ofertas, {added} nuevas guardadas.",
                    "email_sent": email_sent,
                    "jobs_found": len(all_jobs),
                    "jobs": all_jobs,
                    "by_source": {
                        "computrabajo": len(ct_jobs),
                        "bumeran": len(bm_jobs),
                        "indeed": len(in_jobs),
                        "linkedin": len(li_jobs),
                        "empleosperu": len(ep_jobs),
                        "opcionempleo": len(oe_jobs),
                        "jobsfirst": len(jf_jobs),
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

        elif path == "/api/job-detail":
            try:
                content_length = int(self.headers.get("Content-Length", 0))
                body = json.loads(self.rfile.read(content_length)) if content_length else {}
                url = body.get("url", "")
                if not url:
                    self._json_response(400, {"success": False, "error": "URL requerida"})
                    return

                session = requests.Session()
                session.headers.update(HEADERS)
                resp = session.get(url, timeout=8)
                detail = {"description": "", "requirements": "", "salary": "", "modality": "", "schedule": "", "benefits": "", "raw_text": ""}

                if resp.status_code == 200:
                    soup = BeautifulSoup(resp.content, "html.parser")

                    for tag in soup.find_all(["script", "style", "nav", "footer", "header"]):
                        tag.decompose()

                    desc_el = (
                        soup.find("div", {"class": lambda c: c and any(x in (c if isinstance(c, str) else ' '.join(c)) for x in ["description", "descripcion", "detail", "detalle", "content", "body"])})
                        or soup.find("section", {"class": lambda c: c and "description" in (c if isinstance(c, str) else ' '.join(c))})
                        or soup.find("article")
                    )
                    if desc_el:
                        detail["description"] = desc_el.get_text(separator="\n", strip=True)[:3000]

                    salary_el = soup.find(string=lambda s: s and any(w in s.lower() for w in ["salario", "sueldo", "remuneración", "salary", "s/.", "pen"]))
                    if salary_el:
                        parent = salary_el.find_parent()
                        if parent:
                            detail["salary"] = parent.get_text(strip=True)[:200]

                    req_el = soup.find(string=lambda s: s and any(w in s.lower() for w in ["requisitos", "requirements", "perfil", "experiencia requerida"]))
                    if req_el:
                        parent = req_el.find_parent()
                        if parent:
                            next_el = parent.find_next_sibling()
                            if next_el:
                                detail["requirements"] = next_el.get_text(separator="\n", strip=True)[:2000]

                    mod_el = soup.find(string=lambda s: s and any(w in s.lower() for w in ["modalidad", "remoto", "hibrido", "presencial", "teletrabajo"]))
                    if mod_el:
                        parent = mod_el.find_parent()
                        if parent:
                            detail["modality"] = parent.get_text(strip=True)[:200]

                    if not detail["description"]:
                        main = soup.find("main") or soup.find("body")
                        if main:
                            detail["raw_text"] = main.get_text(separator="\n", strip=True)[:3000]

                self._json_response(200, {"success": True, "detail": detail})
            except Exception as e:
                self._json_response(500, {"success": False, "error": str(e)})

        elif path == "/api/parse-cert":
            try:
                content_length = int(self.headers.get("Content-Length", 0))
                body = json.loads(self.rfile.read(content_length)) if content_length else {}
                ocr_text = body.get("text", "")
                if not ocr_text:
                    self._json_response(400, {"success": False, "error": "No text provided"})
                    return

                groq_key = os.environ.get("GROQ_API_KEY", "")
                if not groq_key:
                    self._json_response(200, {"success": False, "error": "GROQ_API_KEY not configured"})
                    return

                system_prompt = """Eres un experto que analiza certificados educativos escaneados.
Extrae datos limpios del texto OCR y devuelve JSON.
REGLAS:
- "name" es SOLO el nombre del curso o certificación (NO el nombre de la persona). Máximo 10 palabras.
- "institution" es quien otorga el certificado.
- "tags" solo de: data, python, excel, frontend, backend, cloud, marketing, liderazgo, mobile, devops, qa, design

EJEMPLO: {"name":"Machine Learning Fundamentals","institution":"Coursera","date":"Marzo 2024","tags":["data","python"]}"""

                user_prompt = f"""Extrae los datos de este certificado y devuelve SOLO el JSON.

Texto OCR:
{ocr_text[:2000]}

JSON:"""

                resp = requests.post(
                    "https://api.groq.com/openai/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {groq_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "openai/gpt-oss-20b",
                        "messages": [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt}
                        ],
                        "temperature": 0.2,
                        "max_tokens": 400
                    },
                    timeout=15
                )

                if resp.status_code == 200:
                    ai_text = resp.json()["choices"][0]["message"]["content"].strip()
                    ai_text = ai_text.replace("```json", "").replace("```", "").strip()
                    parsed = json.loads(ai_text)
                    tags = parsed.get("tags", [])
                    if isinstance(tags, list):
                        tags = ", ".join(tags)
                    self._json_response(200, {
                        "success": True,
                        "name": parsed.get("name", ""),
                        "institution": parsed.get("institution", ""),
                        "date": parsed.get("date", ""),
                        "tags": tags
                    })
                else:
                    self._json_response(200, {"success": False, "error": f"Groq API error: {resp.status_code}"})
            except json.JSONDecodeError:
                self._json_response(200, {"success": True, "name": "", "date": "", "tags": "", "error": "Could not parse AI response"})
            except Exception as e:
                self._json_response(500, {"success": False, "error": str(e)})

        elif path == "/api/parse-experience":
            try:
                content_length = int(self.headers.get("Content-Length", 0))
                body = json.loads(self.rfile.read(content_length)) if content_length else {}
                ocr_text = body.get("text", "")
                if not ocr_text:
                    self._json_response(400, {"success": False, "error": "No text provided"})
                    return

                groq_key = os.environ.get("GROQ_API_KEY", "")
                if not groq_key:
                    self._json_response(200, {"success": False, "error": "GROQ_API_KEY not configured"})
                    return

                system_prompt = """Eres un experto en recursos humanos que analiza documentos laborales escaneados.
Tu trabajo: extraer datos limpios del texto OCR y devolver JSON.
REGLAS ESTRICTAS:
- "title" debe ser SOLO el cargo (ej: "Practicante de Sistemas", "Analista de Datos"). Máximo 6 palabras.
- "company" es el nombre de la empresa.
- "roles" son 3-5 funciones/logros en primera persona con verbos de acción. NO copies texto literal del documento.
- Si el documento no menciona funciones específicas, GENERA roles típicos del cargo mencionado.

EJEMPLO de respuesta correcta:
{"title":"Practicante de Sistemas","company":"Banco de Crédito del Perú","location":"Lima, PE","date":"Enero 2024 - Junio 2024","roles":["Desarrollé reportes automatizados con Python y SQL para el área de operaciones","Mantuve y actualicé bases de datos del sistema interno","Brindé soporte técnico a usuarios de la plataforma corporativa","Documenté procesos y procedimientos del área de TI","Colaboré en la migración de datos del sistema legacy"],"tags":["data","python","backend","analytics"]}"""

                user_prompt = f"""Extrae los datos de este documento laboral escaneado y devuelve SOLO el JSON.

Texto OCR:
{ocr_text[:3000]}

Responde UNICAMENTE con el JSON, sin texto adicional:"""

                resp = requests.post(
                    "https://api.groq.com/openai/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {groq_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "openai/gpt-oss-20b",
                        "messages": [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt}
                        ],
                        "temperature": 0.3,
                        "max_tokens": 800
                    },
                    timeout=20
                )

                if resp.status_code == 200:
                    ai_text = resp.json()["choices"][0]["message"]["content"].strip()
                    ai_text = ai_text.replace("```json", "").replace("```", "").strip()
                    parsed = json.loads(ai_text)
                    roles = parsed.get("roles", [])
                    if isinstance(roles, str):
                        roles = [r.strip() for r in roles.split("\n") if r.strip()]
                    tags = parsed.get("tags", [])
                    if isinstance(tags, list):
                        tags = ", ".join(tags)
                    self._json_response(200, {
                        "success": True,
                        "title": parsed.get("title", ""),
                        "company": parsed.get("company", ""),
                        "location": parsed.get("location", ""),
                        "date": parsed.get("date", ""),
                        "roles": roles,
                        "tags": tags
                    })
                else:
                    self._json_response(200, {"success": False, "error": f"Groq API error: {resp.status_code}"})
            except json.JSONDecodeError:
                self._json_response(200, {"success": False, "error": "Could not parse AI response"})
            except Exception as e:
                self._json_response(500, {"success": False, "error": str(e)})

        elif path == "/api/parse-extracurricular":
            try:
                content_length = int(self.headers.get("Content-Length", 0))
                body = json.loads(self.rfile.read(content_length)) if content_length else {}
                ocr_text = body.get("text", "")
                if not ocr_text:
                    self._json_response(400, {"success": False, "error": "No text provided"})
                    return

                groq_key = os.environ.get("GROQ_API_KEY", "")
                if not groq_key:
                    self._json_response(200, {"success": False, "error": "GROQ_API_KEY not configured"})
                    return

                system_prompt = """Eres un experto en recursos humanos que analiza certificados escaneados.
Tu trabajo: extraer datos limpios del texto OCR y devolver JSON.
REGLAS ESTRICTAS:
- "title" debe ser el NOMBRE del evento (ej: "Hackathon Desafío IA 2026"), NO una descripción larga. Máximo 10 palabras.
- "company" es quien organiza o certifica (ej: "Laboratorios Bagó del Perú").
- "roles" son 3-5 logros que TÚ GENERAS basándote en el contexto del evento. Usa primera persona y verbos de acción.
- NUNCA copies frases literales del certificado. Reescribe todo en formato profesional.

EJEMPLO de respuesta correcta:
{"title":"Hackathon Desafío IA Bagó 2026","company":"Laboratorios Bagó del Perú","location":"Lima, PE","date":"12-13 Junio 2026","roles":["Desarrollé solución tecnológica innovadora en equipo multidisciplinario","Apliqué técnicas de inteligencia artificial para resolver problema de negocio","Presenté proyecto ante panel de jueces expertos en industria farmacéutica","Colaboré en diseño y prototipado rápido bajo presión de tiempo","Obtuve reconocimiento por participación destacada en competencia"],"tags":["hackathon","ia","data","backend","design"]}"""

                user_prompt = f"""Extrae los datos de este certificado escaneado y devuelve SOLO el JSON.

Texto OCR:
{ocr_text[:3000]}

Responde UNICAMENTE con el JSON, sin texto adicional:"""

                resp = requests.post(
                    "https://api.groq.com/openai/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {groq_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "openai/gpt-oss-20b",
                        "messages": [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt}
                        ],
                        "temperature": 0.3,
                        "max_tokens": 800
                    },
                    timeout=20
                )

                if resp.status_code == 200:
                    ai_text = resp.json()["choices"][0]["message"]["content"].strip()
                    ai_text = ai_text.replace("```json", "").replace("```", "").strip()
                    parsed = json.loads(ai_text)
                    roles = parsed.get("roles", [])
                    if isinstance(roles, str):
                        roles = [r.strip() for r in roles.split("\n") if r.strip()]
                    tags = parsed.get("tags", [])
                    if isinstance(tags, list):
                        tags = ", ".join(tags)
                    self._json_response(200, {
                        "success": True,
                        "title": parsed.get("title", ""),
                        "company": parsed.get("company", ""),
                        "location": parsed.get("location", ""),
                        "date": parsed.get("date", ""),
                        "roles": roles,
                        "tags": tags
                    })
                else:
                    self._json_response(200, {"success": False, "error": f"Groq API error: {resp.status_code}"})
            except json.JSONDecodeError:
                self._json_response(200, {"success": False, "error": "Could not parse AI response"})
            except Exception as e:
                self._json_response(500, {"success": False, "error": str(e)})

        elif path == "/api/review-cv":
            try:
                content_length = int(self.headers.get("Content-Length", 0))
                body = json.loads(self.rfile.read(content_length)) if content_length else {}
                cv_text = body.get("cv_text", "")
                job_summary = body.get("job_summary", "")

                if not cv_text:
                    self._json_response(400, {"success": False, "error": "No CV text provided"})
                    return

                groq_key = os.environ.get("GROQ_API_KEY", "")
                if not groq_key:
                    self._json_response(200, {"success": False, "error": "GROQ_API_KEY not configured", "fallback": True})
                    return

                cv_text = cv_text[:3000]
                job_summary = job_summary[:1000]

                system_prompt = """Eres un reclutador senior de Recursos Humanos en Latinoamerica con 15 anos de experiencia revisando CVs para posiciones de tecnologia.

Recibes el perfil COMPLETO de un candidato y una oferta laboral. Tu trabajo es:
1. Seleccionar que experiencia, certificaciones y habilidades son RELEVANTES para este puesto especifico
2. Generar un resumen profesional adaptado al puesto
3. Dar feedback para mejorar el CV

Devuelve SOLO un JSON con esta estructura exacta:
{
  "score": <1-10>,
  "titulo_sugerido": "<titulo profesional que coincida con el puesto>",
  "perfil_profesional": "<resumen de 2-3 lineas adaptado al puesto, destacando experiencia relevante>",
  "experiencia_incluir": ["<titulo exacto de cada experiencia/actividad relevante>"],
  "experiencia_excluir": ["<titulo exacto de cada experiencia/actividad NO relevante>"],
  "certs_incluir": ["<nombre exacto de cada certificacion relevante>"],
  "certs_excluir": ["<nombre exacto de cada certificacion NO relevante>"],
  "skills_incluir": ["<nombre exacto de cada habilidad relevante>"],
  "skills_excluir": ["<nombre exacto de cada habilidad NO relevante>"],
  "alineamiento": ["<observacion sobre alineacion titulo-habilidades-puesto>"],
  "estructura": ["<problema de formato o seccion faltante>"],
  "mejoras": ["<accion concreta y especifica para mejorar>"]
}

Reglas:
- Usa los NOMBRES EXACTOS del perfil del candidato para incluir/excluir (copia el titulo tal cual)
- Incluye TODA experiencia que tenga alguna relacion con el puesto, aunque sea indirecta
- Excluye experiencia claramente irrelevante (ej: voluntariado de animales para puesto de programacion)
- El perfil_profesional debe mencionar logros cuantificables si los hay
- El titulo_sugerido debe coincidir con el nombre del puesto al que postula
- Maximo 3 items en alineamiento, estructura y mejoras
- Responde SOLO con el JSON, sin markdown ni explicaciones"""

                user_prompt = f"""Perfil completo del candidato:
\"\"\"
{cv_text}
\"\"\"

Oferta laboral:
\"\"\"
{job_summary}
\"\"\""""

                resp = requests.post(
                    "https://api.groq.com/openai/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {groq_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "openai/gpt-oss-20b",
                        "messages": [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt}
                        ],
                        "temperature": 0.3,
                        "max_tokens": 2000
                    },
                    timeout=20
                )

                if resp.status_code == 200:
                    ai_text = resp.json()["choices"][0]["message"]["content"].strip()
                    ai_text = ai_text.replace("```json", "").replace("```", "").strip()
                    review = json.loads(ai_text)
                    self._json_response(200, {"success": True, "review": review})
                elif resp.status_code == 429:
                    self._json_response(200, {"success": False, "error": "Limite de uso alcanzado. Intenta en un minuto.", "fallback": True})
                else:
                    self._json_response(200, {"success": False, "error": f"Groq API error: {resp.status_code}"})
            except json.JSONDecodeError:
                self._json_response(200, {"success": False, "error": "No se pudo interpretar la respuesta de la IA", "fallback": True})
            except Exception as e:
                self._json_response(500, {"success": False, "error": str(e)})

        elif path == "/api/register":
            try:
                content_length = int(self.headers.get("Content-Length", 0))
                body = json.loads(self.rfile.read(content_length)) if content_length else {}
                name = body.get("name", "").strip()
                email = body.get("email", "").strip()
                password = body.get("password", "")

                if not name or not email or not password:
                    self._json_response(400, {"success": False, "error": "Nombre, email y contrasena son requeridos"})
                    return
                if len(password) < 6:
                    self._json_response(400, {"success": False, "error": "La contrasena debe tener al menos 6 caracteres"})
                    return

                user = register_user(name, email, password)
                if user:
                    self._json_response(200, {"success": True, "user": user})
                else:
                    self._json_response(409, {"success": False, "error": "Ya existe una cuenta con ese email"})
            except Exception as e:
                self._json_response(500, {"success": False, "error": str(e)})

        elif path == "/api/login":
            try:
                content_length = int(self.headers.get("Content-Length", 0))
                body = json.loads(self.rfile.read(content_length)) if content_length else {}
                email = body.get("email", "").strip()
                password = body.get("password", "")

                if not email or not password:
                    self._json_response(400, {"success": False, "error": "Email y contrasena son requeridos"})
                    return

                user = login_user(email, password)
                if user:
                    self._json_response(200, {"success": True, "user": user})
                else:
                    self._json_response(401, {"success": False, "error": "Email o contrasena incorrectos"})
            except Exception as e:
                self._json_response(500, {"success": False, "error": str(e)})

        elif path == "/api/auth/google":
            try:
                content_length = int(self.headers.get("Content-Length", 0))
                body = json.loads(self.rfile.read(content_length)) if content_length else {}
                id_token = body.get("id_token", "")
                email = body.get("email", "")
                name = body.get("name", "")

                if id_token and id_token != "__access_token__":
                    google_info = verify_google_token(id_token)
                    if not google_info:
                        self._json_response(401, {"success": False, "error": "Token de Google invalido"})
                        return
                elif email:
                    google_info = {"email": email, "name": name or email.split("@")[0], "picture": "", "google_id": body.get("google_id", "")}
                else:
                    self._json_response(400, {"success": False, "error": "Token o email de Google requerido"})
                    return

                user = google_auth_user(google_info)
                self._json_response(200, {"success": True, "user": user})
            except Exception as e:
                self._json_response(500, {"success": False, "error": str(e)})

        elif path == "/api/user/profile":
            try:
                auth = self.headers.get("Authorization", "")
                token = auth.replace("Bearer ", "") if auth.startswith("Bearer ") else ""
                if not token:
                    self._json_response(401, {"success": False, "error": "Token requerido"})
                    return

                content_length = int(self.headers.get("Content-Length", 0))
                body = json.loads(self.rfile.read(content_length)) if content_length else {}
                action = body.get("action", "save")

                if action == "save":
                    cv_profile = body.get("cv_profile", {})
                    save_user_profile(token, json.dumps(cv_profile))
                    self._json_response(200, {"success": True, "message": "Perfil guardado"})
                elif action == "update_info":
                    name = body.get("name", "").strip()
                    email = body.get("email", "").strip()
                    if not name or not email:
                        self._json_response(400, {"success": False, "error": "Nombre y email requeridos"})
                        return
                    ok = update_user_info(token, name, email)
                    if ok:
                        self._json_response(200, {"success": True, "message": "Datos actualizados"})
                    else:
                        self._json_response(409, {"success": False, "error": "El email ya esta en uso"})
                else:
                    self._json_response(400, {"success": False, "error": "Accion no valida"})
            except Exception as e:
                self._json_response(500, {"success": False, "error": str(e)})

        elif path == "/api/improve-cv":
            try:
                content_length = int(self.headers.get("Content-Length", 0))
                body = json.loads(self.rfile.read(content_length)) if content_length else {}
                cv_text = body.get("cv_text", "")[:3000]
                job_summary = body.get("job_summary", "")[:1000]
                review_feedback = body.get("review_feedback", {})

                if not cv_text or not job_summary:
                    self._json_response(400, {"success": False, "error": "cv_text and job_summary required"})
                    return

                groq_key = os.environ.get("GROQ_API_KEY", "")
                if not groq_key:
                    self._json_response(200, {"success": False, "error": "GROQ_API_KEY not configured"})
                    return

                feedback_text = ""
                for key in ["alineamiento", "estructura", "mejoras"]:
                    items = review_feedback.get(key, [])
                    if items:
                        feedback_text += f"\n{key.upper()}:\n" + "\n".join(f"- {i}" for i in items)

                system_prompt = """Eres un experto en redaccion de CVs para el mercado latinoamericano de tecnologia con 15 anos de experiencia.

Recibes:
1. El CV actual del candidato en texto plano
2. El resumen de la oferta laboral a la que postula
3. El feedback de una revision previa con problemas identificados

Tu trabajo es MEJORAR el CV aplicando las sugerencias. Puedes:
- Reescribir descripciones de roles/logros para incluir keywords relevantes del puesto
- Mejorar el titulo profesional para que coincida mejor con la oferta
- Reescribir el perfil profesional para destacar experiencia relevante
- Cuantificar logros cuando el contexto lo permita
- Usar verbos de accion y lenguaje profesional

NO puedes:
- Inventar experiencia, empresas o logros que no existen en el CV original
- Agregar certificaciones o habilidades no mencionadas
- Cambiar fechas, empresas o datos facticos
- Exagerar o mentir sobre la experiencia

Responde SOLO con un JSON (sin markdown ni explicaciones):
{
  "titulo_sugerido": "<titulo profesional mejorado>",
  "perfil_profesional": "<resumen profesional mejorado de 2-3 lineas, adaptado al puesto>",
  "roles_mejorados": {
    "<titulo EXACTO de la experiencia tal como aparece en el CV>": ["logro mejorado 1", "logro mejorado 2", ...]
  }
}

Reglas para roles_mejorados:
- Usa los TITULOS EXACTOS del CV original como claves del objeto
- Solo incluye experiencias cuyos roles realmente necesitan mejora
- Cada logro debe ser conciso (1 linea) y usar verbos de accion
- Incorpora keywords de la oferta laboral de forma natural"""

                user_prompt = f"""CV ACTUAL:
{cv_text}

OFERTA LABORAL:
{job_summary}

FEEDBACK DE REVISION PREVIA (score: {review_feedback.get('score', 'N/A')}/10):
{feedback_text}

Mejora el CV aplicando las sugerencias. Responde SOLO con el JSON:"""

                resp = requests.post(
                    "https://api.groq.com/openai/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {groq_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "openai/gpt-oss-20b",
                        "messages": [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt}
                        ],
                        "temperature": 0.4,
                        "max_tokens": 2000
                    },
                    timeout=20
                )

                if resp.status_code == 200:
                    ai_text = resp.json()["choices"][0]["message"]["content"].strip()
                    ai_text = ai_text.replace("```json", "").replace("```", "").strip()
                    improvements = json.loads(ai_text)
                    self._json_response(200, {"success": True, "improvements": improvements})
                elif resp.status_code == 429:
                    self._json_response(200, {"success": False, "error": "Limite de uso alcanzado. Intenta en un minuto."})
                else:
                    self._json_response(200, {"success": False, "error": f"Groq API error: {resp.status_code}"})
            except json.JSONDecodeError:
                self._json_response(200, {"success": False, "error": "No se pudo interpretar la respuesta de la IA"})
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
