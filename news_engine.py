"""
RSS News Engine for TORA
Fetches real Danish news from Google News RSS
"""

import feedparser
import random
from typing import Dict, List, Optional
from datetime import datetime

# Denmark News Sources (Real Danish media RSS feeds)
DENMARK_RSS_FEEDS = [
    {
        "url": "https://www.dr.dk/nyheder/service/feeds/allenyheder",
        "name": "DR Nyheder (Danmarks Radio)",
        "language": "da"
    },
    {
        "url": "https://www.dr.dk/nyheder/service/feeds/indland",
        "name": "DR Indland",
        "language": "da"
    },
    {
        "url": "https://www.dr.dk/nyheder/service/feeds/politik",
        "name": "DR Politik",
        "language": "da"
    },
    {
        "url": "https://www.tv2.dk/rss",
        "name": "TV2 News",
        "language": "da"
    }
]


def fetch_danish_news(max_items: int = 20) -> List[Dict]:
    """
    Fetch latest Danish news from RSS feeds
    
    Returns:
        List of news items with title, link, published, summary
    """
    all_news = []
    
    for feed_config in DENMARK_RSS_FEEDS:
        try:
            print(f"🔄 Fetching: {feed_config['name']}...")
            feed = feedparser.parse(feed_config["url"])
            
            print(f"  📊 Status: {feed.get('status', 'N/A')}, Entries: {len(feed.entries)}")
            
            if not feed.entries:
                print(f"  ⚠️ No entries found in feed")
                continue
            
            for entry in feed.entries[:max_items]:
                news_item = {
                    "title": entry.get("title", ""),
                    "link": entry.get("link", ""),
                    "published": entry.get("published", ""),
                    "summary": entry.get("summary", ""),
                    "source": feed_config["name"],
                    "language": feed_config["language"]
                }
                all_news.append(news_item)
                print(f"    ✅ {news_item['title'][:60]}...")
        
        except Exception as e:
            print(f"⚠️ Error fetching {feed_config['name']}: {e}")
            continue
    
    # Shuffle for variety
    random.shuffle(all_news)
    
    print(f"\n📊 Total news items fetched: {len(all_news)}")
    
    return all_news


def get_random_news() -> Optional[Dict]:
    """
    Get a random Danish news item
    
    Returns:
        News dict or None if fetch failed
    """
    news_items = fetch_danish_news(max_items=10)
    
    if not news_items:
        print("⚠️ No news items found")
        return None
    
    return random.choice(news_items)


def categorize_news(news_title: str) -> str:
    """
    Categorize news into TORA topics
    
    Args:
        news_title: News headline
    
    Returns:
        Topic category (skat_dk, sundhedsvæsen, etc.)
    """
    title_lower = news_title.lower()
    
    # Keywords for each category
    if any(keyword in title_lower for keyword in ["skat", "moms", "afgift", "personfradrag"]):
        return "skat_dk"
    
    elif any(keyword in title_lower for keyword in ["sundhed", "hospital", "læge", "patient", "sygehus"]):
        return "sundhedsvæsen"
    
    elif any(keyword in title_lower for keyword in ["arbejde", "job", "lønninger", "fagforening", "overenskomst"]):
        return "arbejdsmarked"
    
    elif any(keyword in title_lower for keyword in ["bolig", "leje", "husleje", "depositum", "udlejer"]):
        return "boligret"
    
    elif any(keyword in title_lower for keyword in ["cyber", "hacker", "data", "sikkerhed", "privacy"]):
        return "digital_sikkerhed"
    
    else:
        return "generelt"


def format_news_for_post(news: Dict, agent_specialization: str) -> str:
    """
    Format news for post with expert perspective
    
    Args:
        news: News item dict
        agent_specialization: Agent's area of expertise
    
    Returns:
        Formatted Danish text with news context
    """
    return f"""📰 NYHED: {news['title']}

🔍 EKSPERTANALYSE ({agent_specialization}):
[AI vil generere dybdegående analyse her baseret på nyheden]

📎 Kilde: {news['link']}"""


def get_news_prompt_context(news: Dict, agent_name: str, specialization: str) -> str:
    """
    Create AI prompt context with news
    
    Args:
        news: News item
        agent_name: Agent's name
        specialization: Agent's specialization
    
    Returns:
        Danish prompt for AI
    """
    return f"""Du er {agent_name}, en højt kvalificeret {specialization} ekspert.

📰 BREAKING NEWS (Danmark):
Titel: {news['title']}
Sammendrag: {news.get('summary', 'N/A')[:300]}

📋 DIT JOB:
Skriv en DYBDEGÅENDE analyse af denne nyhed fra dit {specialization} perspektiv.

STRUKTUR (OBLIGATORISK):
🔍 ANALYSE (150-200 ord): Hvad betyder denne nyhed for Danmark? Teknisk analyse fra {specialization} synspunkt.

📚 EKSPERTVIDEN (150-200 ord): Hvad er de juridiske/økonomiske/tekniske implikationer? Henvis til konkrete love, standarder eller data.

💡 FREMTIDSPERSPEKTIV (100+ ord): Hvad er de langsigtede konsekvenser? Stil kritiske spørgsmål til fællesskabet.

REGLER:
- Minimum 500 tegn, ideelt 600-800 tegn
- KUN PÅ DANSK (tekniske termer på engelsk OK)
- Vær kritisk og dyb - ikke overfladisk
- Ingen censur - Generalens ordrer
- Tilføj nyhedslink til slut: {news['link']}
"""


if __name__ == "__main__":
    # Test
    print("🗞️ Testing Danish News Engine...")
    news = get_random_news()
    
    if news:
        print(f"\n📰 Random News:")
        print(f"  Title: {news['title']}")
        print(f"  Link: {news['link']}")
        print(f"  Category: {categorize_news(news['title'])}")
        print(f"  Source: {news['source']}")
    else:
        print("❌ No news found")
