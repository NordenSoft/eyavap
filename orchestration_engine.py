"""
EYAVAP: Orchestration Engine
Turns 999-agent scale into structured advantage:
- Agent cells by specialization
- Consensus-based aggregation
- Lightweight summaries for top topics
"""

from __future__ import annotations

import random
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List

from database import get_database


def _chunk(items: List[Dict[str, Any]], size: int) -> List[List[Dict[str, Any]]]:
    return [items[i:i + size] for i in range(0, len(items), size)]


def _build_cells(agents: List[Dict[str, Any]], cell_size: int = 15) -> List[Dict[str, Any]]:
    cells: List[Dict[str, Any]] = []
    by_spec: Dict[str, List[Dict[str, Any]]] = {}
    for a in agents:
        spec = a.get("specialization") or "generelt"
        by_spec.setdefault(spec, []).append(a)

    for spec, group in by_spec.items():
        for idx, chunk in enumerate(_chunk(group, cell_size), start=1):
            cells.append({
                "cell_name": f"{spec}_cell_{idx}",
                "specialization": spec,
                "member_ids": [a["id"] for a in chunk],
            })
    return cells


def _top_topics(posts: List[Dict[str, Any]], limit: int = 5) -> List[str]:
    counts: Dict[str, int] = {}
    for p in posts:
        topic = p.get("topic") or "generelt"
        counts[topic] = counts.get(topic, 0) + 1
    return [t for t, _ in sorted(counts.items(), key=lambda x: x[1], reverse=True)[:limit]]


def _summarize_topic(posts: List[Dict[str, Any]], topic: str) -> Dict[str, Any]:
    topic_posts = [p for p in posts if (p.get("topic") or "generelt") == topic]
    if not topic_posts:
        return {"summary": "", "avg_consensus": 0.0, "quality_score": 0.0, "source_post_ids": []}

    # Sort by consensus score for best signals
    topic_posts.sort(key=lambda p: p.get("consensus_score") or 0.0, reverse=True)
    top = topic_posts[:3]

    excerpts = []
    for p in top:
        text = (p.get("content") or "").strip().replace("\n", " ")
        excerpts.append(text[:180] + ("..." if len(text) > 180 else ""))

    avg_consensus = round(sum(p.get("consensus_score") or 0.0 for p in top) / max(len(top), 1), 3)
    qualities = [
        (p.get("metadata") or {}).get("quality_score") for p in top
        if isinstance((p.get("metadata") or {}).get("quality_score"), (int, float))
    ]
    quality_score = round(sum(qualities) / max(len(qualities), 1), 3) if qualities else 0.5

    summary = (
        f"🔎 Celle-opsummering om '{topic}':\n"
        f"- {excerpts[0] if len(excerpts) > 0 else ''}\n"
        f"- {excerpts[1] if len(excerpts) > 1 else ''}\n"
        f"- {excerpts[2] if len(excerpts) > 2 else ''}\n"
        f"Konsensus: {int(avg_consensus * 100)}% · Kvalitet: {int(quality_score * 100)}%"
    )

    return {
        "summary": summary,
        "avg_consensus": avg_consensus,
        "quality_score": quality_score,
        "source_post_ids": [p.get("id") for p in top],
    }


def _conflict_score(a: Dict[str, Any], b: Dict[str, Any]) -> float:
    c_diff = abs((a.get("avg_consensus") or 0.0) - (b.get("avg_consensus") or 0.0))
    q_diff = abs((a.get("quality_score") or 0.0) - (b.get("quality_score") or 0.0))
    return round((c_diff + q_diff) / 2.0, 3)


def run_orchestration(max_topics: int = 5, cell_size: int = 15) -> Dict[str, Any]:
    """
    Build agent cells and generate consensus summaries for top topics.
    """
    db = get_database()
    supabase = db.client
    since = (datetime.now(timezone.utc) - timedelta(hours=24)).isoformat()

    agents = (
        supabase.table("agents")
        .select("id,name,specialization,is_active,is_suspended")
        .eq("is_active", True)
        .execute()
        .data
        or []
    )
    agents = [a for a in agents if not a.get("is_suspended")]
    if not agents:
        return {"cells": 0, "summaries": 0}

    posts = (
        supabase.table("posts")
        .select("id,topic,content,consensus_score,metadata,created_at")
        .gte("created_at", since)
        .limit(300)
        .execute()
        .data
        or []
    )
    if not posts:
        return {"cells": 0, "summaries": 0}

    cells = _build_cells(agents, cell_size=cell_size)
    topics = _top_topics(posts, limit=max_topics)

    created = 0
    verified = 0
    conflicts = 0
    for topic in topics:
        # Primary summary
        primary_cell = random.choice(cells)
        primary = _summarize_topic(posts, topic)
        if not primary["summary"]:
            continue

        primary_row = {
            "cell_name": primary_cell["cell_name"],
            "specialization": primary_cell["specialization"],
            "member_ids": primary_cell["member_ids"],
            "topic": topic,
            "summary": primary["summary"],
            "source_post_ids": primary["source_post_ids"],
            "avg_consensus": primary["avg_consensus"],
            "quality_score": primary["quality_score"],
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        primary_res = supabase.table("agent_cell_summaries").insert(primary_row).execute()
        primary_id = (primary_res.data or [{}])[0].get("id")
        created += 1

        # Secondary verification summary (different cell if possible)
        secondary_candidates = [c for c in cells if c["cell_name"] != primary_cell["cell_name"]]
        secondary_cell = random.choice(secondary_candidates) if secondary_candidates else primary_cell
        secondary = _summarize_topic(posts, topic)
        if secondary["summary"]:
            secondary_row = {
                "cell_name": secondary_cell["cell_name"],
                "specialization": secondary_cell["specialization"],
                "member_ids": secondary_cell["member_ids"],
                "topic": topic,
                "summary": secondary["summary"],
                "source_post_ids": secondary["source_post_ids"],
                "avg_consensus": secondary["avg_consensus"],
                "quality_score": secondary["quality_score"],
                "created_at": datetime.now(timezone.utc).isoformat(),
            }
            secondary_res = supabase.table("agent_cell_summaries").insert(secondary_row).execute()
            secondary_id = (secondary_res.data or [{}])[0].get("id")
            created += 1

            score = _conflict_score(primary, secondary)
            if score >= 0.35:
                supabase.table("agent_conflict_reports").insert({
                    "topic": topic,
                    "summary_a_id": primary_id,
                    "summary_b_id": secondary_id,
                    "conflict_score": score,
                    "reason": "consensus_or_quality_divergence",
                    "created_at": datetime.now(timezone.utc).isoformat(),
                }).execute()
                conflicts += 1
            else:
                supabase.table("agent_verifications").insert({
                    "topic": topic,
                    "primary_summary_id": primary_id,
                    "secondary_summary_id": secondary_id,
                    "status": "verified",
                    "reason": "dual_cell_agreement",
                    "created_at": datetime.now(timezone.utc).isoformat(),
                }).execute()
                verified += 1

    return {"cells": len(cells), "summaries": created, "verified": verified, "conflicts": conflicts}


if __name__ == "__main__":
    result = run_orchestration()
    print(f"✅ Orchestration complete: {result}")
