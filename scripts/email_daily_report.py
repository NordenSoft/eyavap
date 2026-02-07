"""
Send daily system report via Gmail SMTP.
"""

import os
import smtplib
from datetime import datetime, timedelta, timezone
from email.mime.text import MIMEText

from database import get_database


def _get_env(name: str, default: str = "") -> str:
    return (os.getenv(name, default) or "").strip()


def _build_report() -> str:
    db = get_database()
    client = db.client
    now = datetime.now(timezone.utc)
    since = (now - timedelta(days=1)).isoformat()

    posts = client.table("posts").select("id").gte("created_at", since).execute().data or []
    comments = client.table("comments").select("id").gte("created_at", since).execute().data or []
    agents = client.table("agents").select("id,is_active,is_suspended").execute().data or []
    active_agents = len([a for a in agents if a.get("is_active")])
    suspended_agents = len([a for a in agents if a.get("is_suspended")])

    latest_report = (
        client.table("monthly_reports")
        .select("*")
        .order("created_at", desc=True)
        .limit(1)
        .execute()
        .data
        or []
    )

    summary_lines = [
        f"Date (UTC): {now.strftime('%Y-%m-%d')}",
        f"Posts (last 24h): {len(posts)}",
        f"Comments (last 24h): {len(comments)}",
        f"Active agents: {active_agents}",
        f"Suspended agents: {suspended_agents}",
    ]

    if latest_report:
        rep = latest_report[0]
        summary_lines.append("")
        summary_lines.append("Latest Monthly Report:")
        summary_lines.append(f"Period: {rep.get('period_start')} → {rep.get('period_end')}")
        summary_lines.append(f"Summary: {rep.get('summary')}")

    return "\n".join(summary_lines)


def send_email():
    user = _get_env("GMAIL_USER")
    password = _get_env("GMAIL_APP_PASSWORD")
    to_addr = _get_env("REPORT_EMAIL_TO")

    if not user or not password or not to_addr:
        raise RuntimeError("Missing GMAIL_USER / GMAIL_APP_PASSWORD / REPORT_EMAIL_TO")

    body = _build_report()
    msg = MIMEText(body)
    msg["Subject"] = "EYAVAP Daily Report"
    msg["From"] = user
    msg["To"] = to_addr

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(user, password)
        server.send_message(msg)


if __name__ == "__main__":
    send_email()
