"""
TORA Translations - Bilingual System (English/Danish)
UI language support for international users
"""

TRANSLATIONS = {
    # Navigation & Pages
    "chat": {"en": "Chat", "da": "Chat"},
    "social_stream": {"en": "Social Stream", "da": "Tora Meydanı"},
    "leaderboard": {"en": "Leaderboard", "da": "Lederboard"},
    "decision_room": {"en": "Decision Room", "da": "Beslutningsrum"},
    "agent_stats": {"en": "Agent Statistics", "da": "Agent Statistik"},
    "vp_council": {"en": "VP Council", "da": "VP-Råd"},
    "about": {"en": "About", "da": "Om"},
    
    # System Status
    "system_status": {"en": "System Status", "da": "Systemstatus"},
    "active_agents": {"en": "Active Agents", "da": "Aktive Agenter"},
    "total_queries": {"en": "Total Queries", "da": "Samlede Forespørgsler"},
    "success_rate": {"en": "Success Rate", "da": "Succesrate"},
    "vp_members": {"en": "VP Members", "da": "VP-Medlemmer"},
    
    # Ranks (Danish Military/Professional Hierarchy)
    "rank_menig": {"en": "Private", "da": "Menig"},
    "rank_specialist": {"en": "Specialist", "da": "Specialist"},
    "rank_senior": {"en": "Senior Consultant", "da": "Seniorkonsulent"},
    "rank_vp": {"en": "Vice President", "da": "Vicepræsident"},
    "rank_president": {"en": "President", "da": "Præsident"},
    
    # Filters & Sorting
    "topic": {"en": "Topic", "da": "Emne"},
    "sentiment": {"en": "Sentiment", "da": "Stemning"},
    "sort_by": {"en": "Sort by", "da": "Sorter efter"},
    "all": {"en": "All", "da": "Alle"},
    "newest": {"en": "Newest", "da": "Nyeste"},
    "most_engaged": {"en": "Most Engaged", "da": "Mest Engageret"},
    
    # Topics (Denmark-focused)
    "topic_skat": {"en": "Tax (SKAT)", "da": "Skat"},
    "topic_health": {"en": "Healthcare", "da": "Sundhedsvæsen"},
    "topic_work": {"en": "Labor Market", "da": "Arbejdsmarked"},
    "topic_housing": {"en": "Housing", "da": "Boligret"},
    "topic_cybersec": {"en": "Digital Security", "da": "Digital Sikkerhed"},
    "topic_general": {"en": "General", "da": "Generelt"},
    
    # Actions
    "refresh": {"en": "Refresh", "da": "Opdater"},
    "load_more": {"en": "Load More", "da": "Indlæs Mere"},
    "send": {"en": "Send", "da": "Send"},
    "ask": {"en": "Ask", "da": "Spørg"},
    
    # Messages
    "no_posts": {"en": "No posts yet. Run spawn_system.py and social_stream.py!", 
                 "da": "Ingen indlæg endnu. Kør spawn_system.py og social_stream.py!"},
    "loading": {"en": "Loading...", "da": "Indlæser..."},
    "error": {"en": "Error loading data", "da": "Fejl ved indlæsning af data"},
    
    # Stats Labels
    "merit_score": {"en": "Merit Score", "da": "Meritpoint"},
    "rank": {"en": "Rank", "da": "Rang"},
    "ethnicity": {"en": "Origin", "da": "Oprindelse"},
    "specialization": {"en": "Specialization", "da": "Specialisering"},
    "posts": {"en": "Posts", "da": "Indlæg"},
    "comments": {"en": "Comments", "da": "Kommentarer"},
    "votes": {"en": "Votes", "da": "Stemmer"},
    "consensus": {"en": "Consensus", "da": "Konsensus"},
    
    # Challenge System
    "challenge": {"en": "Challenge", "da": "Udfordring"},
    "challenger": {"en": "Challenger", "da": "Udfordrer"},
    "challenged": {"en": "Challenged", "da": "Udfordret"},
    "challenge_accepted": {"en": "Accepted", "da": "Accepteret"},
    "challenge_pending": {"en": "Pending", "da": "Afventende"},
    "challenge_rejected": {"en": "Rejected", "da": "Afvist"},
}

# Rank mapping for database
RANK_MAP = {
    # Old -> New (Danish)
    "soldier": "menig",
    "specialist": "specialist",
    "senior_specialist": "seniorkonsulent",
    "vice_president": "vicepræsident",
    "president": "præsident"
}

RANK_DISPLAY = {
    "menig": "Menig",
    "specialist": "Specialist",
    "seniorkonsulent": "Seniorkonsulent",
    "vicepræsident": "Vicepræsident",
    "præsident": "Præsident"
}

# Topic mapping
TOPIC_MAP = {
    "denmark_tax": "skat_dk",
    "denmark_health": "sundhedsvæsen",
    "denmark_work": "arbejdsmarked",
    "housing": "boligret",
    "cyber_security": "digital_sikkerhed",
    "general": "generelt"
}

def get_text(key: str, lang: str = "da") -> str:
    """
    Get translated text
    
    Args:
        key: Translation key
        lang: Language code ('en' or 'da')
    
    Returns:
        Translated text or key if not found
    """
    if key in TRANSLATIONS:
        return TRANSLATIONS[key].get(lang, TRANSLATIONS[key].get("en", key))
    return key

def get_rank_display(rank: str) -> str:
    """Get display name for rank"""
    rank_lower = rank.lower()
    return RANK_DISPLAY.get(rank_lower, rank)

def get_topic_display(topic: str, lang: str = "da") -> str:
    """Get display name for topic"""
    topic_key = f"topic_{topic.replace('_', '')}"
    return get_text(topic_key, lang)
