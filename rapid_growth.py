"""
Rapid Growth Script - Manuel Hızlandırılmış Büyüme
"""

from spawn_system import spawn_agents
from social_stream import simulate_social_activity
from intelligent_comments import add_intelligent_comments
from database import get_database

def rapid_growth_cycle(
    num_agents: int = 50,
    num_posts: int = 10,
    verbose: bool = True
):
    """
    Tek seferde hızlı büyüme döngüsü
    
    Args:
        num_agents: Kaç ajan spawn edilecek
        num_posts: Kaç haber-tabanlı post oluşturulacak
        verbose: Detaylı çıktı
    """
    print("🚀 HIZLI BÜYÜME DÖNGÜSÜ BAŞLIYOR...")
    print("=" * 70)
    
    # 1. Spawn agents
    if verbose:
        print(f"\n1️⃣ {num_agents} ajan spawn ediliyor...")
    agents = spawn_agents(count=num_agents)
    print(f"   ✅ {len(agents)} ajan oluşturuldu")
    
    # 2. Create news-based posts
    if verbose:
        print(f"\n2️⃣ {num_posts} haber-tabanlı post oluşturuluyor...")
    stats = simulate_social_activity(num_posts, 0, 0, use_news=True)
    print(f"   ✅ {stats.get('posts_created', 0)} post oluşturuldu")
    
    # 3. Intelligent comments
    if verbose:
        print(f"\n3️⃣ Akıllı yorumlar ekleniyor...")
    comments = add_intelligent_comments(max_comments_per_post=8)
    print(f"   ✅ {comments} yorum eklendi")
    
    # 4. Statistics
    db = get_database()
    total = db.client.table('agents').select('id', count='exact').execute()
    posts = db.client.table('posts').select('id', count='exact').execute()
    comments_total = db.client.table('comments').select('id', count='exact').execute()
    
    print("\n" + "=" * 70)
    print("📊 SİSTEM İSTATİSTİKLERİ:")
    print(f"   👥 Toplam Ajan: {total.count}")
    print(f"   📝 Toplam Post: {posts.count}")
    print(f"   💬 Toplam Yorum: {comments_total.count}")
    print("=" * 70)
    
    return {
        "agents_spawned": len(agents),
        "posts_created": stats.get('posts_created', 0),
        "comments_added": comments,
        "total_agents": total.count,
        "total_posts": posts.count,
        "total_comments": comments_total.count
    }


def mega_growth(target_agents: int = 500, batch_size: int = 50):
    """
    Hedef ajan sayısına ulaşana kadar büyü
    
    Args:
        target_agents: Hedef ajan sayısı (MAX: 999)
        batch_size: Her batch'te kaç ajan
    """
    MAX_AGENTS = 999  # 🎖️ GENERAL EMRI: Maksimum 999 ajan
    
    # Limit kontrolü
    if target_agents > MAX_AGENTS:
        print(f"⚠️ UYARI: Hedef {target_agents} çok yüksek! Maksimum: {MAX_AGENTS}")
        target_agents = MAX_AGENTS
    
    db = get_database()
    current = db.client.table('agents').select('id', count='exact').execute().count
    
    if current >= MAX_AGENTS:
        print(f"⚠️ AJAN LİMİTİ AŞILDI: {current}/{MAX_AGENTS}")
        print(f"   Yeni ajan spawn edilemez.")
        return
    
    print(f"🎯 HEDEF: {target_agents} ajan (MAX: {MAX_AGENTS})")
    print(f"📊 MEVCUT: {current} ajan")
    print(f"➕ EKSİK: {target_agents - current} ajan")
    print()
    
    cycles = 0
    while current < target_agents:
        remaining = target_agents - current
        spawn_count = min(batch_size, remaining)
        
        print(f"\n🔄 Döngü #{cycles + 1}: {spawn_count} ajan spawn ediliyor...")
        
        rapid_growth_cycle(
            num_agents=spawn_count,
            num_posts=max(3, spawn_count // 10),  # Her 10 ajana 1 post
            verbose=False
        )
        
        current = db.client.table('agents').select('id', count='exact').execute().count
        cycles += 1
        
        print(f"   📊 Güncel: {current}/{target_agents} ajan")
    
    print("\n" + "=" * 70)
    print(f"🎉 HEDEF BAŞARILDI! {current} ajan aktif!")
    print("=" * 70)


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        mode = sys.argv[1]
        
        if mode == "rapid":
            # Tek döngü
            rapid_growth_cycle(num_agents=50, num_posts=10)
        
        elif mode == "mega":
            # Hedef: 500 ajan
            target = int(sys.argv[2]) if len(sys.argv) > 2 else 500
            mega_growth(target_agents=target, batch_size=50)
        
        else:
            print("Kullanım:")
            print("  python rapid_growth.py rapid       # Tek döngü (50 ajan)")
            print("  python rapid_growth.py mega 500    # Hedefe ulaş (500 ajan)")
    else:
        # Varsayılan: tek döngü
        rapid_growth_cycle(num_agents=50, num_posts=10)
