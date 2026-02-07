"""
EYAVAP: US-style presidential election (delegate model)
State model: specialization
"""

from __future__ import annotations

import datetime
import random
from typing import Dict, List, Any, Tuple

from database import get_database

ZERO_ID = "00000000-0000-0000-0000-000000001000"
MIN_TRUST_SCORE = 40


def _now_iso() -> str:
    return datetime.datetime.utcnow().isoformat()


def _get_active_agents(supabase) -> List[Dict[str, Any]]:
    res = (
        supabase.table("agents")
        .select("id,name,specialization,merit_score,rank,ethnicity,is_active,is_suspended,vetting_status,trust_score")
        .eq("is_active", True)
        .execute()
    )
    agents = res.data or []
    # Hide ZERO (0)
    filtered = [a for a in agents if a.get("id") != ZERO_ID and a.get("name") != "0"]
    eligible = []
    for a in filtered:
        if a.get("is_suspended") is True:
            continue
        if a.get("vetting_status") == "rejected":
            continue
        trust = a.get("trust_score")
        if trust is not None and trust < MIN_TRUST_SCORE:
            continue
        eligible.append(a)
    return eligible


def _compute_state_delegates(
    agents: List[Dict[str, Any]],
    total_delegates: int = 100,
) -> Dict[str, int]:
    counts: Dict[str, int] = {}
    for a in agents:
        spec = a.get("specialization", "general") or "general"
        counts[spec] = counts.get(spec, 0) + 1

    total_agents = sum(counts.values()) or 1
    delegates = {
        spec: max(1, round((cnt / total_agents) * total_delegates))
        for spec, cnt in counts.items()
    }

    # Normalize to exact total_delegates
    current = sum(delegates.values())
    if current != total_delegates:
        # Adjust largest states first
        sorted_specs = sorted(counts.keys(), key=lambda s: counts[s], reverse=True)
        idx = 0
        step = 1 if current < total_delegates else -1
        while current != total_delegates and sorted_specs:
            spec = sorted_specs[idx % len(sorted_specs)]
            if step > 0:
                delegates[spec] += 1
                current += 1
            else:
                if delegates[spec] > 1:
                    delegates[spec] -= 1
                    current -= 1
            idx += 1

    return delegates


def _select_candidates(
    agents: List[Dict[str, Any]],
    max_candidates: int = 5,
    min_candidates: int = 2,
) -> List[Dict[str, Any]]:
    sorted_agents = sorted(agents, key=lambda a: a.get("merit_score", 0), reverse=True)
    candidates = sorted_agents[:max_candidates]
    if len(candidates) < min_candidates:
        candidates = sorted_agents[:min_candidates]
    return candidates


def _weighted_choice(weights: Dict[str, float]) -> str:
    total = sum(weights.values())
    r = random.uniform(0, total)
    upto = 0.0
    for k, w in weights.items():
        upto += w
        if upto >= r:
            return k
    return list(weights.keys())[0]


def _build_manifesto(agent: Dict[str, Any]) -> str:
    name = agent.get("name", "Agent")
    spec = agent.get("specialization", "general")
    merit = agent.get("merit_score", 50)
    return (
        f"{name} vil styrke lederskabet med fokus på {spec}. "
        f"Mål: højere konsensus, stærkere ekspertise og stabil governance. "
        f"Meritpoint: {merit}/100."
    )


def _refresh_candidates(
    supabase,
    election_id: str,
    agents: List[Dict[str, Any]],
    max_candidates: int,
    min_candidates: int,
) -> List[Dict[str, Any]]:
    candidates = _select_candidates(agents, max_candidates=max_candidates, min_candidates=min_candidates)
    for c in candidates:
        try:
            supabase.table("election_candidates").insert(
                {
                    "election_id": election_id,
                    "agent_id": c["id"],
                    "manifesto": _build_manifesto(c),
                }
            ).execute()
        except Exception:
            pass
    return candidates


def _append_campaign_update(results: Dict[str, Any], text: str) -> Dict[str, Any]:
    updates = results.get("campaign_updates") or []
    updates.append({"timestamp": _now_iso(), "text": text})
    results["campaign_updates"] = updates[-20:]
    results["last_campaign_update"] = _now_iso()
    return results


def _append_debate_summary(results: Dict[str, Any], text: str) -> Dict[str, Any]:
    debates = results.get("debate_summaries") or []
    debates.append({"timestamp": _now_iso(), "text": text})
    results["debate_summaries"] = debates[-10:]
    return results


def _simulate_state_vote(
    state_key: str,
    state_agents: List[Dict[str, Any]],
    candidates: List[Dict[str, Any]],
) -> Dict[str, int]:
    vote_totals = {c["id"]: 0 for c in candidates}

    for agent in state_agents:
        weights = {}
        for c in candidates:
            merit = (c.get("merit_score", 50) or 50) / 100.0
            spec_bonus = 0.15 if c.get("specialization") == state_key else 0.0
            weights[c["id"]] = max(0.05, merit + spec_bonus)
        chosen = _weighted_choice(weights)
        vote_totals[chosen] += 1

    return vote_totals


def run_presidential_election(
    total_delegates: int = 100,
    max_candidates: int = 5,
    min_candidates: int = 2,
    apply_rank: bool = True,
    existing_election_id: str | None = None,
) -> Dict[str, Any]:
    """
    Runs a US-style delegate election by specialization.
    Returns election summary and persists results to Supabase.
    """
    db = get_database()
    supabase = db.client

    agents = _get_active_agents(supabase)
    if not agents:
        return {"success": False, "error": "No active agents"}

    candidates = _select_candidates(agents, max_candidates=max_candidates, min_candidates=min_candidates)
    if not candidates:
        return {"success": False, "error": "No candidates available"}

    if existing_election_id:
        election_id = existing_election_id
        supabase.table("elections").update(
            {"status": "active", "start_at": _now_iso(), "total_delegates": total_delegates}
        ).eq("id", election_id).execute()
    else:
        election_name = f"Presidential Election {datetime.datetime.utcnow().date().isoformat()}"
        election_row = (
            supabase.table("elections")
            .insert(
                {
                    "name": election_name,
                    "model": "specialization",
                    "status": "active",
                    "total_delegates": total_delegates,
                    "start_at": _now_iso(),
                }
            )
            .execute()
        )
        election_id = (election_row.data or [{}])[0].get("id")
        if not election_id:
            return {"success": False, "error": "Election create failed"}

    # Save candidates
    for c in candidates:
        try:
            supabase.table("election_candidates").insert(
                {"election_id": election_id, "agent_id": c["id"], "manifesto": _build_manifesto(c)}
            ).execute()
        except Exception:
            pass

    delegates_map = _compute_state_delegates(agents, total_delegates=total_delegates)

    # Seed for deterministic results
    random.seed(str(election_id))

    delegate_totals = {c["id"]: 0 for c in candidates}
    state_results = []

    for state_key, delegates in delegates_map.items():
        state_agents = [a for a in agents if a.get("specialization") == state_key]
        if not state_agents:
            continue
        vote_totals = _simulate_state_vote(state_key, state_agents, candidates)
        winner_id = max(
            vote_totals.items(),
            key=lambda x: (x[1], next((c.get("merit_score", 0) for c in candidates if c["id"] == x[0]), 0)),
        )[0]
        delegate_totals[winner_id] += delegates

        state_results.append(
            {
                "election_id": election_id,
                "state_key": state_key,
                "delegates": delegates,
                "winner_agent_id": winner_id,
                "vote_totals": vote_totals,
            }
        )

    if state_results:
        supabase.table("election_state_results").insert(state_results).execute()

    # Determine winner
    winner_id = max(delegate_totals.items(), key=lambda x: x[1])[0]
    winner = next((c for c in candidates if c["id"] == winner_id), None)

    results_payload = {
        "delegates": delegate_totals,
        "candidates": [{"id": c["id"], "name": c["name"]} for c in candidates],
        "model": "specialization",
    }

    supabase.table("elections").update(
        {
            "status": "closed",
            "end_at": _now_iso(),
            "winner_agent_id": winner_id,
            "results": results_payload,
        }
    ).eq("id", election_id).execute()

    if apply_rank and winner:
        # Demote current visible presidents (exclude ZERO)
        supabase.table("agents").update(
            {"rank": "vice_president"}
        ).in_("rank", ["president", "præsident"]).neq("id", ZERO_ID).neq("name", "0").execute()
        # Promote winner
        supabase.table("agents").update(
            {"rank": "president"}
        ).eq("id", winner_id).execute()

    return {
        "success": True,
        "election_id": election_id,
        "winner": winner,
        "delegate_totals": delegate_totals,
    }


def get_latest_election() -> Dict[str, Any] | None:
    db = get_database()
    supabase = db.client
    res = supabase.table("elections").select("*").order("created_at", desc=True).limit(1).execute()
    if not res.data:
        return None
    election = res.data[0]
    election_id = election.get("id")
    candidates = (
        supabase.table("election_candidates")
        .select("agents!inner(id,name,specialization,merit_score,rank),election_id")
        .eq("election_id", election_id)
        .execute()
    ).data or []
    state_results = (
        supabase.table("election_state_results")
        .select("*")
        .eq("election_id", election_id)
        .execute()
    ).data or []
    return {
        "election": election,
        "candidates": candidates,
        "state_results": state_results,
    }


def ensure_election_cycle(
    term_days: int = 365,
    primary_days: int = 90,
    general_days: int = 30,
    total_delegates: int = 100,
) -> Dict[str, Any]:
    """
    4/1 model: 4-year cycle compressed to 1 year.
    Primary: 3 months, General: 1 month, Term: 12 months.
    """
    db = get_database()
    supabase = db.client

    res = supabase.table("elections").select("*").order("created_at", desc=True).limit(1).execute()
    now = datetime.datetime.utcnow()

    if not res.data:
        election_name = f"Presidential Cycle {now.date().isoformat()}"
        results = {
            "phase": "primary",
            "phase_start": _now_iso(),
            "primary_end": (now + datetime.timedelta(days=primary_days)).isoformat(),
            "general_end": (now + datetime.timedelta(days=primary_days + general_days)).isoformat(),
            "term_end": (now + datetime.timedelta(days=term_days)).isoformat(),
            "campaign_updates": [],
            "debate_summaries": [],
        }
        row = (
            supabase.table("elections")
            .insert(
                {
                    "name": election_name,
                    "model": "specialization",
                    "status": "scheduled",
                    "total_delegates": total_delegates,
                    "start_at": _now_iso(),
                    "results": results,
                }
            )
            .execute()
        )
        return {"created": True, "election_id": (row.data or [{}])[0].get("id")}

    election = res.data[0]
    election_id = election.get("id")
    status = election.get("status")
    results = election.get("results") or {}

    def _parse_iso(s: str | None) -> datetime.datetime | None:
        if not s:
            return None
        try:
            return datetime.datetime.fromisoformat(s.replace("Z", "+00:00"))
        except Exception:
            return None

    primary_end = _parse_iso(results.get("primary_end"))
    general_end = _parse_iso(results.get("general_end"))
    term_end = _parse_iso(results.get("term_end"))
    if not term_end:
        end_at = _parse_iso(election.get("end_at"))
        if end_at:
            term_end = end_at + datetime.timedelta(days=term_days)

    # If closed and term ended, open new primary
    if status == "closed" and term_end and now >= term_end:
        return ensure_election_cycle(
            term_days=term_days,
            primary_days=primary_days,
            general_days=general_days,
            total_delegates=total_delegates,
        )

    if status == "scheduled":
        # Primary campaign updates (daily)
        last_update = _parse_iso(results.get("last_campaign_update"))
        if not last_update or (now - last_update).days >= 1:
            agents = _get_active_agents(supabase)
            _refresh_candidates(supabase, election_id, agents, max_candidates=5, min_candidates=2)
            results = _append_campaign_update(
                results,
                "Primærvalg: kandidaterne opdateret og kampagner intensiveret.",
            )
            supabase.table("elections").update({"results": results}).eq("id", election_id).execute()

        if primary_end and now >= primary_end:
            results["phase"] = "general"
            results = _append_debate_summary(
                results,
                "Generalvalg åbnet: kandidaterne mødes til hoveddebat.",
            )
            supabase.table("elections").update({"status": "active", "results": results}).eq("id", election_id).execute()
            return {"phase": "general_started", "election_id": election_id}
        return {"phase": "primary", "election_id": election_id}

    if status == "active":
        if general_end and now >= general_end:
            # Run general election and close
            out = run_presidential_election(
                total_delegates=total_delegates,
                existing_election_id=election_id,
            )
            return {"phase": "general_finished", "election_id": election_id, "result": out}
        # General phase debate summary (daily)
        last_debate = _parse_iso(results.get("last_debate_update"))
        if not last_debate or (now - last_debate).days >= 1:
            results = _append_debate_summary(
                results,
                "Hoveddebat: kandidaterne fokuserer på governance, kvalitet og stabilitet.",
            )
            results["last_debate_update"] = _now_iso()
            supabase.table("elections").update({"results": results}).eq("id", election_id).execute()
        return {"phase": "general", "election_id": election_id}

    return {"status": status, "election_id": election_id}
