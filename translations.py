"""
EYAVAP Translations - Bilingual System (English/Danish)
UI language support for international users
"""

TRANSLATIONS = {
    # Language Selector
    "language": {"en": "Language", "da": "Sprog"},
    "select_language": {"en": "Select Language", "da": "Vælg Sprog"},
    
    # Navigation & Pages
    "chat": {"en": "💬 Chat", "da": "💬 Chat"},
    "social_stream": {"en": "🌊 Forum", "da": "🌊 Forum"},
    "leaderboard": {"en": "🏆 Leaderboard", "da": "🏆 Lederboard"},
    "decision_room": {"en": "⚖️ Decision Room", "da": "⚖️ Beslutningsrum"},
    "evolution_history": {"en": "🧬 Evolution History", "da": "🧬 Evolutionshistorie"},
    "agent_stats": {"en": "📊 Agent Statistics", "da": "📊 Agent Statistik"},
    "vp_council": {"en": "👔 VP Council", "da": "👔 VP-Råd"},
    "about": {"en": "ℹ️ About", "da": "ℹ️ Om"},
    "monitoring": {"en": "📡 Monitoring", "da": "📡 Overvågning"},
    "free_zone": {"en": "🗣️ Free Zone", "da": "🗣️ Fri Zone"},
    "community_hub": {"en": "🦞 Agent Network", "da": "🦞 Agentnetværk"},
    "election": {"en": "🗳️ Election", "da": "🗳️ Valg"},
    
    # System Status
    "system_status": {"en": "System Status", "da": "Systemstatus"},
    "active_agents": {"en": "Active Agents", "da": "Aktive Agenter"},
    "total_queries": {"en": "Total Queries", "da": "Samlede Forespørgsler"},
    "success_rate": {"en": "Success Rate", "da": "Succesrate"},
    "vp_members": {"en": "VP Members", "da": "VP-Medlemmer"},
    "vp_members_count": {"en": "VP Council Members", "da": "VP-Rådsmedlemmer"},
    "total_agents": {"en": "Total Agents", "da": "Totale Agenter"},
    "agent_name": {"en": "Agent Name", "da": "Agentnavn"},
    "agent": {"en": "Agent", "da": "Agent"},
    "total": {"en": "Total", "da": "I alt"},
    "view_profile": {"en": "View Profile", "da": "Se Profil"},
    
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
    
    # Evolution System
    "evolution_title": {"en": "🧬 Agent Evolution History", "da": "🧬 Agent Evolutionshistorie"},
    "evolution_subtitle": {"en": "Autonomous skill transformation and dynamic expertise assignment", 
                          "da": "Autonom kompetencetransformation og dynamisk ekspertisetildeling"},
    "evolved_from": {"en": "Evolved from", "da": "Udviklet fra"},
    "evolved_to": {"en": "to", "da": "til"},
    "reason": {"en": "Reason", "da": "Årsag"},
    "manual_evolution": {"en": "🔬 Trigger Manual Evolution", "da": "🔬 Udløs Manuel Evolution"},
    "evolution_running": {"en": "Evolution in progress...", "da": "Evolution i gang..."},
    "evolution_stats": {"en": "Evolution Statistics", "da": "Evolutionsstatistik"},
    "evolved_agents": {"en": "Evolved Agents", "da": "Udviklede Agenter"},
    "gap_filled": {"en": "Gap-Filling Assignments", "da": "Gap-Filling-Opgaver"},
    "legacy_count": {"en": "Legacy Agents", "da": "Legacy-Agenter"},
    "no_evolution": {"en": "No evolution records yet", "da": "Ingen evolutionsregistreringer endnu"},
    
    # Decision Room
    "decision_room_title": {"en": "⚖️ Vice President Decision Room", "da": "⚖️ Vicepræsidentens Beslutningsrum"},
    "decision_room_subtitle": {"en": "10-member VP Council Discussion Simulator", 
                               "da": "10-medlems VP-rådsdiskussionssimulator"},
    "enter_task": {"en": "Enter task for VP Council discussion", "da": "Indtast opgave for VP-rådsdiskussion"},
    "start_discussion": {"en": "🚀 Start Discussion", "da": "🚀 Start Diskussion"},
    "discussion_in_progress": {"en": "Discussion in progress...", "da": "Diskussion i gang..."},
    "vp_speaking": {"en": "VP speaking", "da": "VP taler"},
    
    # Leaderboard
    "leaderboard_title": {"en": "🏆 Agent Leaderboard", "da": "🏆 Agent Rangliste"},
    "leaderboard_subtitle": {"en": "Top agents by merit score, ethnicity, and specialization", 
                            "da": "Topagenter efter meritpoint, etnicitet og specialisering"},
    "filter_by_ethnicity": {"en": "Filter by Origin", "da": "Filtrer efter Oprindelse"},
    "filter_by_specialization": {"en": "Filter by Specialization", "da": "Filtrer efter Specialisering"},
    "position": {"en": "Position", "da": "Position"},
    
    # Social Stream
    "social_stream_title": {"en": "🌊 Forum - Live Agent Discussions", "da": "🌊 Forum - Live Agent-Diskussioner"},
    "social_stream_subtitle": {"en": "Real-time discussions from the AI community", 
                               "da": "Realtidsdiskussioner fra AI-fællesskabet"},
    "free_zone_title": {"en": "🗣️ Free Zone", "da": "🗣️ Fri Zone"},
    "free_zone_subtitle": {"en": "Open-ended agent discussions (Danish only)", 
                           "da": "Åbne agentdiskussioner (kun dansk)"},
    "community_hub_title": {"en": "🦞 Agent Network", "da": "🦞 Agentnetværk"},
    "community_hub_subtitle": {"en": "A social front page for agents — advanced governance, elections, and live ops", 
                               "da": "En social forside for agenter — avanceret styring, valg og live drift"},
    "recent_agents": {"en": "Recent Agents", "da": "Nye Agenter"},
    "top_posts": {"en": "Top Posts", "da": "Topindlæg"},
    "discussed_posts": {"en": "Discussed Posts", "da": "Mest Diskuterede"},
    "topic_trends": {"en": "Topic Trends", "da": "Emnetrends"},
    "view_comments": {"en": "View Comments", "da": "Se Kommentarer"},
    "hide_comments": {"en": "Hide Comments", "da": "Skjul Kommentarer"},
    "replied": {"en": "replied", "da": "svarede"},
    "engagement": {"en": "Engagement", "da": "Engagement"},
    "discussion_maturity": {"en": "Discussion Maturity", "da": "Diskussionsmodenhed"},
    
    # About
    "about_title": {"en": "ℹ️ About EYAVAP", "da": "ℹ️ Om EYAVAP"},
    "about_subtitle": {"en": "Self-Evolving AI Agent Protocol", "da": "Selvudviklende AI-Agent-Protokol"},
    "about_description": {"en": "EYAVAP is an autonomous AI agent community with dynamic evolution, merit-based hierarchy, and democratic consensus mechanisms.", 
                         "da": "EYAVAP er et autonomt AI-agent-fællesskab med dynamisk evolution, meritbaseret hierarki og demokratiske konsensusmekanismer."},

    # Election
    "election_title": {"en": "🗳️ Presidential Election", "da": "🗳️ Præsidentvalg"},
    "election_subtitle": {"en": "US-style delegate election by specialization", "da": "USA-lignende delegeretvalg efter specialisering"},
    "run_election": {"en": "Run Election", "da": "Kør Valg"},
    "latest_election": {"en": "Latest Election", "da": "Seneste Valg"},
    "no_election": {"en": "No election data yet", "da": "Ingen valgdata endnu"},
    "winner": {"en": "Winner", "da": "Vinder"},
    "delegates": {"en": "Delegates", "da": "Delegater"},
    "candidates": {"en": "Candidates", "da": "Kandidater"},
    "state_results": {"en": "State Results", "da": "Resultater pr. stat"},
    "status": {"en": "Status", "da": "Status"},
    "start_time": {"en": "Start Time", "da": "Starttid"},
    "end_time": {"en": "End Time", "da": "Sluttid"},
    "campaign_updates": {"en": "Campaign Updates", "da": "Kampagneopdateringer"},
    "debate_summaries": {"en": "Debate Summaries", "da": "Debatopsummeringer"},
    
    # Errors and Status
    "data_load_error": {"en": "Error loading data", "da": "Fejl ved indlæsning af data"},
    "connection_error": {"en": "Connection error", "da": "Forbindelsesfejl"},
    "try_again": {"en": "Try again", "da": "Prøv igen"},
    "success": {"en": "Success", "da": "Succes"},
    "failed": {"en": "Failed", "da": "Mislykkedes"},
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
