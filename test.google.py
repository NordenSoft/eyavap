import os
import google.generativeai as genai
from dotenv import load_dotenv

# 1. Anahtarı .env'den oku
load_dotenv()
TEST_KEY = os.getenv("GEMINI_API_KEY", "").strip()
if not TEST_KEY:
    raise SystemExit("❌ GEMINI_API_KEY bulunamadı (.env dosyasını kontrol edin).")
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