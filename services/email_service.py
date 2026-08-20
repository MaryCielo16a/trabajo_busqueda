import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SENDER_EMAIL = os.getenv("SENDER_EMAIL", "")
SENDER_PASSWORD = os.getenv("SENDER_APP_PASSWORD", "")
RECIPIENT_EMAILS = os.getenv(
    "RECIPIENT_EMAILS",
    "anamariatapiahurtado3@gmail.com,u20211e348@gmail.com"
).split(",")

SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))


def send_job_notification(new_jobs: list):
    if not SENDER_EMAIL or not SENDER_PASSWORD:
        logger.warning("Email not configured. Set SENDER_EMAIL and SENDER_APP_PASSWORD.")
        return False

    if not new_jobs:
        logger.info("No new jobs to notify about.")
        return False

    subject = f"🔔 {len(new_jobs)} nueva(s) oferta(s) de trabajo - {datetime.now().strftime('%d/%m/%Y %H:%M')}"

    html_body = _build_email_html(new_jobs)

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = SENDER_EMAIL

        html_part = MIMEText(html_body, "html", "utf-8")
        msg.attach(html_part)

        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SENDER_EMAIL, SENDER_PASSWORD)

            for recipient in RECIPIENT_EMAILS:
                recipient = recipient.strip()
                if recipient:
                    msg["To"] = recipient
                    server.sendmail(SENDER_EMAIL, recipient, msg.as_string())
                    logger.info(f"Email sent to {recipient}")
                    del msg["To"]

        logger.info(f"Notification sent for {len(new_jobs)} jobs")
        return True

    except smtplib.SMTPAuthenticationError:
        logger.error("Email auth failed. Check SENDER_EMAIL and SENDER_APP_PASSWORD.")
        return False
    except Exception as e:
        logger.error(f"Failed to send email: {e}")
        return False


def _build_email_html(jobs: list) -> str:
    job_cards = ""
    for job in jobs:
        source = getattr(job, 'source', job.get('source', '')) if isinstance(job, dict) else job.source
        title = getattr(job, 'title', job.get('title', '')) if isinstance(job, dict) else job.title
        company = getattr(job, 'company', job.get('company', '')) if isinstance(job, dict) else job.company
        location = getattr(job, 'location', job.get('location', '')) if isinstance(job, dict) else job.location
        salary = getattr(job, 'salary', job.get('salary', '')) if isinstance(job, dict) else job.salary
        url = getattr(job, 'url', job.get('url', '')) if isinstance(job, dict) else job.url
        is_remote = getattr(job, 'is_remote', job.get('is_remote', False)) if isinstance(job, dict) else job.is_remote

        source_color = "#1976d2" if source == "computrabajo" else "#7b1fa2"
        remote_badge = '<span style="color:#4caf50;font-weight:bold;">✅ Remoto</span>' if is_remote else f'📍 {location}'
        salary_line = f'<p style="color:#555;">💰 {salary}</p>' if salary and salary != "Not specified" else ""

        job_cards += f"""
        <div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin-bottom:12px;background:white;">
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;">
                <h3 style="margin:0;color:#333;font-size:16px;">{title}</h3>
                <span style="background:{source_color};color:white;padding:2px 10px;border-radius:12px;font-size:11px;">{source.upper()}</span>
            </div>
            <p style="color:#666;margin:4px 0;">🏢 {company}</p>
            <p style="color:#777;margin:4px 0;">{remote_badge}</p>
            {salary_line}
            <a href="{url}" style="display:inline-block;margin-top:8px;padding:8px 16px;background:#667eea;color:white;text-decoration:none;border-radius:5px;font-size:13px;">
                Ver oferta →
            </a>
        </div>
        """

    return f"""
    <!DOCTYPE html>
    <html>
    <head><meta charset="utf-8"></head>
    <body style="font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;background:#f5f5f5;padding:20px;">
        <div style="max-width:600px;margin:0 auto;">
            <div style="background:linear-gradient(135deg,#667eea,#764ba2);padding:20px;border-radius:10px 10px 0 0;text-align:center;">
                <h1 style="color:white;margin:0;font-size:22px;">💼 Job Search Automation</h1>
                <p style="color:rgba(255,255,255,0.9);margin:8px 0 0;">Se encontraron {len(jobs)} nueva(s) oferta(s)</p>
            </div>
            <div style="background:white;padding:20px;border-radius:0 0 10px 10px;box-shadow:0 4px 15px rgba(0,0,0,0.1);">
                <p style="color:#333;margin-bottom:16px;">
                    Hola! Encontramos ofertas de trabajo que coinciden con tus criterios:
                </p>
                {job_cards}
                <hr style="border:none;border-top:1px solid #eee;margin:20px 0;">
                <p style="color:#999;font-size:12px;text-align:center;">
                    Enviado automáticamente por Job Search Automation<br>
                    {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}
                </p>
            </div>
        </div>
    </body>
    </html>
    """
