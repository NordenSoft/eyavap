"""
Governance rules that must not be altered by agents.
"""

ELECTION_RULES_LOCKED = True

ELECTION_RULES = {
    "model": "specialization",
    "term_days": 365,
    "primary_days": 90,
    "general_days": 30,
    "total_delegates": 100,
}
