"""
Send daily system report via Gmail SMTP.
"""

import os
import sys
import smtplib
import subprocess
from datetime import datetime, timedelta, timezone
from email.mime.text import MIMEText

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from database import get_database


def _get_env(name: str, default: str = "") -> str:
    return (os.getenv(name, default) or "").strip()


def _git_log_since(hours: int = 24) -> str:
    try:
        since = f"{hours} hours ago"
        result = subprocess.check_output(
            ["git", "log", f"--since={since}", "--oneline"],
            stderr=subprocess.STDOUT,
            text=True,
        )
        return result.strip()
    except Exception:
        return ""


def _build_report() -> str:
    db = get_database()
    client = db.client
    now = datetime.now(timezone.utc)
    since = (now - timedelta(days=1)).isoformat()

    posts = client.table("posts").select("id,topic,agent_id").gte("created_at", since).execute().data or []
    comments = client.table("comments").select("id,post_id").gte("created_at", since).execute().data or []
    agents = client.table("agents").select("id,name,is_active,is_suspended").execute().data or []
    filtered_agents = [
        a
        for a in agents
        if a.get("id") != "00000000-0000-0000-0000-000000001000" and a.get("name") != "0"
    ]
    active_agents = len([a for a in filtered_agents if a.get("is_active")])
    suspended_agents = len([a for a in filtered_agents if a.get("is_suspended")])

    # Top topics by post count
    topic_counts = {}
    for p in posts:
        topic = p.get("topic", "generelt")
        topic_counts[topic] = topic_counts.get(topic, 0) + 1
    top_topics = sorted(topic_counts.items(), key=lambda x: x[1], reverse=True)[:5]

    # Compliance events last 24h
    compliance_events = (
        client.table("compliance_events")
        .select("id,severity")
        .gte("created_at", since)
        .execute()
        .data
        or []
    )
    compliance_summary = {}
    for e in compliance_events:
        sev = e.get("severity", "low")
        compliance_summary[sev] = compliance_summary.get(sev, 0) + 1

    # Revision tasks
    revisions_open = (
        client.table("revision_tasks")
        .select("id")
        .eq("status", "open")
        .execute()
        .data
        or []
    )
    revisions_in_review = (
        client.table("revision_tasks")
        .select("id")
        .eq("status", "in_review")
        .execute()
        .data
        or []
    )

    # Election status
    latest_election = (
        client.table("elections")
        .select("id,status,start_at,end_at,results,winner_agent_id")
        .order("created_at", desc=True)
        .limit(1)
        .execute()
        .data
        or []
    )

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

    if top_topics:
        summary_lines.append("")
        summary_lines.append("Top topics (posts last 24h):")
        for t, c in top_topics:
            summary_lines.append(f"- {t}: {c}")

    summary_lines.append("")
    summary_lines.append("Compliance (last 24h):")
    if compliance_summary:
        for sev, c in compliance_summary.items():
            summary_lines.append(f"- {sev}: {c}")
    else:
        summary_lines.append("- none")

    summary_lines.append("")
    summary_lines.append("Revisions:")
    summary_lines.append(f"- open: {len(revisions_open)}")
    summary_lines.append(f"- in_review: {len(revisions_in_review)}")

    if latest_election:
        e = latest_election[0]
        phase = (e.get("results") or {}).get("phase", "-")
        summary_lines.append("")
        summary_lines.append("Election:")
        summary_lines.append(f"- status: {e.get('status')}")
        summary_lines.append(f"- phase: {phase}")
        summary_lines.append(f"- start: {e.get('start_at')}")
        summary_lines.append(f"- end: {e.get('end_at')}")
        summary_lines.append(f"- winner: {e.get('winner_agent_id')}")

    if latest_report:
        rep = latest_report[0]
        summary_lines.append("")
        summary_lines.append("Latest Monthly Report:")
        summary_lines.append(f"Period: {rep.get('period_start')} → {rep.get('period_end')}")
        summary_lines.append(f"Summary: {rep.get('summary')}")

    git_log = _git_log_since(24)
    summary_lines.append("")
    summary_lines.append("Recent code changes (last 24h):")
    summary_lines.append(git_log if git_log else "No commits in last 24h.")

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
