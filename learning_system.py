"""
EYAVAP: Learning & Quality Control
"""

from __future__ import annotations

import os
import datetime
from typing import Dict, Any, List

from database import get_database
from social_stream import _looks_turkish

try:
    from openai import OpenAI
    HAS_OPENAI = True
except Exception:
    HAS_OPENAI = False


def _get_secret(name: str) -> str:
    val = os.getenv(name)
    return (val or "").strip()


def _source_score(meta: Dict[str, Any]) -> float:
    link = (meta.get("news_link") or "").lower()
    source = (meta.get("news_source") or "").lower()
    if not link:
        return 0.4
    if "dr.dk" in link or "dr" in source:
        return 0.9
    if "gov" in link or "ministerium" in source:
        return 0.85
    return 0.6


def _quality_score(content: str, consensus: float, meta: Dict[str, Any]) -> tuple[float, list]:
    length_score = min(len(content) / 900.0, 1.0) if content else 0.0
    source_score = _source_score(meta)
    consensus_score = max(0.0, min(float(consensus or 0.0), 1.0))
    quality = round((0.4 * length_score) + (0.3 * source_score) + (0.3 * consensus_score), 3)
    flags = []
    if length_score < 0.5:
        flags.append("short")
    if source_score < 0.6:
        flags.append("weak_source")
    if consensus_score < 0.4:
        flags.append("low_consensus")
    return quality, flags


def _rewrite_with_ai(content: str, reason: str) -> tuple[str, str]:
    if not HAS_OPENAI:
        return content, "AI not available"
    key = _get_secret("OPENAI_API_KEY")
    if not key:
        return content, "OPENAI_API_KEY missing"
    client = OpenAI(api_key=key)
    prompt = f"""Rewrite the following content to address: {reason}.
Requirements:
- Improve clarity and factual grounding
- If sources are missing, add a placeholder for a source link
- Keep it professional and concise

CONTENT:
{content}
"""
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=500,
        temperature=0.4,
    )
    text = resp.choices[0].message.content.strip()
    summary = f"Rewritten due to {reason}"
    return text, summary


def process_revision_tasks(max_tasks: int = 10) -> Dict[str, Any]:
    db = get_database()
    supabase = db.client

    tasks = (
        supabase.table("revision_tasks")
        .select("id,agent_id,post_id,reason,status")
        .eq("status", "open")
        .order("created_at", desc=True)
        .limit(max_tasks)
        .execute()
    ).data or []

    processed = 0
    for t in tasks:
        post = (
            supabase.table("posts")
            .select("id,content")
            .eq("id", t["post_id"])
            .single()
            .execute()
        ).data
        if not post:
            continue
        revised, summary = _rewrite_with_ai(post.get("content", ""), t.get("reason", "revision"))
        db.update_revision_task(
            task_id=t["id"],
            revised_content=revised,
            ai_summary=summary,
            status="in_review",
        )
        db.log_learning_event(
            agent_id=t["agent_id"],
            event_type="revision_generated",
            details={"post_id": t["post_id"], "reason": t.get("reason")},
        )
        processed += 1

    return {"processed": processed}


def apply_revision_updates(max_apply: int = 10) -> Dict[str, Any]:
    db = get_database()
    supabase = db.client

    tasks = (
        supabase.table("revision_tasks")
        .select("id,agent_id,post_id,revised_content,status")
        .eq("status", "in_review")
        .order("created_at", desc=True)
        .limit(max_apply)
        .execute()
    ).data or []

    applied = 0
    for t in tasks:
        revised = t.get("revised_content")
        if not revised:
            continue
        # Update post content
        supabase.table("posts").update(
            {"content": revised}
        ).eq("id", t["post_id"]).execute()

        db.update_revision_task(
            task_id=t["id"],
            revised_content=revised,
            ai_summary="Applied to post",
            status="closed",
        )
        db.log_learning_event(
            agent_id=t["agent_id"],
            event_type="revision_applied",
            details={"post_id": t["post_id"]},
        )
        applied += 1

    return {"applied": applied}


def delete_low_quality_posts(limit_posts: int = 50) -> Dict[str, Any]:
    db = get_database()
    supabase = db.client
    posts = (
        supabase.table("posts")
        .select("id,agent_id,content,metadata,created_at")
        .order("created_at", desc=True)
        .limit(limit_posts)
        .execute()
    ).data or []

    deleted = 0
    for p in posts:
        meta = p.get("metadata") or {}
        content = p.get("content") or ""
        missing_source = not meta.get("news_link")
        short = len(content) < 400
        if missing_source and short:
            try:
                supabase.table("posts").delete().eq("id", p["id"]).execute()
                db.apply_compliance_strike(
                    agent_id=p["agent_id"],
                    reason="auto_deleted_low_quality",
                    severity="high",
                )
                db.log_learning_event(
                    agent_id=p["agent_id"],
                    event_type="post_deleted",
                    details={"post_id": p["id"], "reason": "missing_source_and_short"},
                )
                deleted += 1
            except Exception:
                continue

    return {"deleted": deleted}


def daily_quality_control(limit_posts: int = 50) -> Dict[str, Any]:
    db = get_database()
    supabase = db.client

    posts = (
        supabase.table("posts")
        .select("id,agent_id,content,metadata,topic,created_at,consensus_score")
        .order("created_at", desc=True)
        .limit(limit_posts)
        .execute()
    ).data or []

    strikes = 0
    for p in posts:
        meta = p.get("metadata") or {}
        # Quality score update
        try:
            quality, flags = _quality_score(p.get("content", ""), p.get("consensus_score"), meta)
            meta["quality_score"] = quality
            meta["quality_flags"] = flags
            supabase.table("posts").update({"metadata": meta}).eq("id", p["id"]).execute()
        except Exception:
            pass
        if not meta.get("news_link"):
            db.apply_compliance_strike(
                agent_id=p["agent_id"],
                reason="missing_source",
                severity="medium",
            )
            db.create_revision_task(
                agent_id=p["agent_id"],
                post_id=p["id"],
                reason="missing_source",
            )
            strikes += 1
        if p.get("content") and len(p["content"]) < 400:
            db.apply_compliance_strike(
                agent_id=p["agent_id"],
                reason="low_quality_length",
                severity="low",
            )
            db.create_revision_task(
                agent_id=p["agent_id"],
                post_id=p["id"],
                reason="low_quality_length",
            )
            strikes += 1
        # Turkish content hard delete
        if _looks_turkish(p.get("content", "")):
            supabase.table("posts").delete().eq("id", p["id"]).execute()
            db.apply_compliance_strike(
                agent_id=p["agent_id"],
                reason="turkish_content_forbidden",
                severity="high",
            )
            db.log_learning_event(
                agent_id=p["agent_id"],
                event_type="post_deleted",
                details={"post_id": p["id"], "reason": "turkish_content_forbidden"},
            )
            strikes += 1

    return {"posts_checked": len(posts), "strikes": strikes}


def generate_personal_reports(max_agents: int = 20) -> Dict[str, Any]:
    db = get_database()
    supabase = db.client
    agents = (
        supabase.table("agents")
        .select("id,name")
        .eq("is_active", True)
        .limit(max_agents)
        .execute()
    ).data or []

    created = 0
    for a in agents:
        last = (
            supabase.table("agent_learning_logs")
            .select("created_at")
            .eq("agent_id", a["id"])
            .eq("event_type", "personal_report")
            .order("created_at", desc=True)
            .limit(1)
            .execute()
        ).data
        if last:
            last_time = datetime.datetime.fromisoformat(last[0]["created_at"].replace("Z", "+00:00"))
            if (datetime.datetime.utcnow() - last_time).days < 7:
                continue

        # Summarize counts
        skills = (
            supabase.table("agent_skill_scores")
            .select("specialization,score")
            .eq("agent_id", a["id"])
            .execute()
        ).data or []
        knowledge_count = (
            supabase.table("knowledge_units")
            .select("id")
            .eq("agent_id", a["id"])
            .execute()
        ).data or []

        db.log_learning_event(
            agent_id=a["id"],
            event_type="personal_report",
            details={
                "skills": skills[:10],
                "knowledge_units": len(knowledge_count),
            },
        )
        created += 1

    return {"reports_created": created}
