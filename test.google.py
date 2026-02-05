import google.generativeai as genai

# 1. Anahtarı direkt veriyoruz (Sadece bu test için)
TEST_KEY = "AIzaSyALCahjkadpMqCbRQne2F5P4r7k7MRilf8"
genai.configure(api_key=TEST_KEY)

print("\n➖➖➖➖➖➖➖➖➖➖➖➖➖➖➖➖➖➖")
print("📡 GOOGLE GENEL MERKEZİNE BAĞLANILIYOR...")
print("➖➖➖➖➖➖➖➖➖➖➖➖➖➖➖➖➖➖\n")

try:
    # Google'a "Bana kullanabileceğim modelleri listele" diyoruz
    model_listesi = genai.list_models()
    
    bulunanlar = []
    
    for m in model_listesi:
        # Sadece 'generateContent' (Sohbet) yapabilenleri bul
        if 'generateContent' in m.supported_generation_methods:
            print(f"✅ AÇIK MODEL: {m.name}")
            bulunanlar.append(m.name)
            
    if not bulunanlar:
        print("❌ HATA: Erişim izniniz olan hiçbir model bulunamadı!")
    else:
        print(f"\n🎉 TOPLAM {len(bulunanlar)} ADET MODEL BULUNDU.")

except Exception as e:
    print(f"\n🚨 BAĞLANTI HATASI: {e}")
    print("İpucu: VPN açık mı? Veya internet kısıtlaması var mı?")