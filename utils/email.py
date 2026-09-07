import os
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


def send_email(recipient: str, subject: str, body: str) -> bool:
    smtp_host = os.environ.get("SMTP_HOST", "")
    if not smtp_host:
        print(f"[EMAIL] SMTP not configured — would send to {recipient}: {subject}")
        print(f"[EMAIL] Body: {body[:200]}...")
        return False

    smtp_port = int(os.environ.get("SMTP_PORT", "587"))
    smtp_user = os.environ.get("SMTP_USER", "")
    smtp_pass = os.environ.get("SMTP_PASS", "")
    smtp_from = os.environ.get("SMTP_FROM", "noreply@ananas.local")

    msg = MIMEMultipart("alternative")
    msg["From"] = smtp_from
    msg["To"] = recipient
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain", "utf-8"))
    msg.attach(MIMEText(body, "html", "utf-8"))

    try:
        ctx = ssl.create_default_context()
        with smtplib.SMTP(smtp_host, smtp_port, timeout=15) as server:
            server.ehlo()
            if server.has_extn("STARTTLS"):
                server.starttls(context=ctx)
                server.ehlo()
            if smtp_user and smtp_pass:
                server.login(smtp_user, smtp_pass)
            server.sendmail(smtp_from, [recipient], msg.as_string())
        print(f"[EMAIL] Sent to {recipient}: {subject}")
        return True
    except Exception as e:
        print(f"[EMAIL] Failed to send to {recipient}: {e}")
        return False