"""
Mevcut ajanların isimlerini güncelle: Soyisimleri kaldır
"""

from database import get_database

def update_existing_agent_names():
    """
    Mevcut ajanların isimlerinden soyisimleri kaldır
    Örn: "Emma Jensen" → "Emma"
    """
    db = get_database()
    
    print("🔄 MEVCUT AJAN İSİMLERİ GÜNCELLENİYOR...")
    print("=" * 70)
    
    # Tüm ajanları al
    agents = db.client.table("agents").select("*").execute()
    
    if not agents.data:
        print("❌ Hiç ajan bulunamadı")
        return
    
    updated_count = 0
    
    for agent in agents.data:
        current_name = agent.get('name', '')
        
        # Eğer isim boşluk içeriyorsa (soyisim var demektir)
        if ' ' in current_name:
            # Sadece ilk kelimeyi al (isim)
            first_name = current_name.split()[0]
            
            # Güncelle
            try:
                db.client.table("agents").update({
                    "name": first_name
                }).eq("id", agent['id']).execute()
                
                print(f"  ✅ {current_name:30s} → {first_name}")
                updated_count += 1
            
            except Exception as e:
                print(f"  ⚠️ Güncelleme hatası ({current_name}): {e}")
        else:
            # Zaten tek isim
            print(f"  ⏭️ {current_name:30s} (zaten tek isim)")
    
    print("=" * 70)
    print(f"✅ {updated_count} ajan güncellendi")
    print(f"📊 Toplam ajan: {len(agents.data)}")


if __name__ == "__main__":
    update_existing_agent_names()
