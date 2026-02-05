# EYAVAP Ajan Sistemi Kurulum Rehberi

## 🚀 Hızlı Başlangıç

### 1. Veritabanını Kur

Supabase Dashboard'a git ve `schema.sql` dosyasını çalıştır:

1. Supabase projesini aç
2. SQL Editor'e git
3. `schema.sql` dosyasının içeriğini kopyala
4. Çalıştır (Run)

Bu işlem şu tabloları oluşturur:
- `agents` - Ajan bilgileri
- `agent_queries` - Sorgu logları
- `vice_president_council` - Başkan Yardımcısı Kurulu
- `action_logs` - Eylem logları

### 2. Streamlit Secrets Ayarla

Streamlit Cloud'da veya lokal `.streamlit/secrets.toml` dosyasında:

```toml
OPENAI_API_KEY = "sk-proj-..."
SUPABASE_URL = "https://xxx.supabase.co"
SUPABASE_KEY = "eyJhbGc..."

# İsteğe bağlı: Google Sheets loglama
[gcp_service_account]
type = "service_account"
project_id = "..."
private_key = "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n"
client_email = "...@....iam.gserviceaccount.com"
# ... diğer alanlar
```

### 3. Lokal Test

```bash
# Bağımlılıkları yükle
pip install -r requirements.txt

# Streamlit uygulamasını başlat
streamlit run dashboard.py
```

## 📚 Sistem Mimarisi

```
┌─────────────────────────────────────────┐
│         Kullanıcı (Dashboard)           │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│         agents.py (Interface)            │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│      Başkan Ajan (President Agent)      │
│  • Sorgu analizi                        │
│  • Ajan seçimi/oluşturma                │
│  • Liyakat yönetimi                     │
└──────────┬─────────────┬────────────────┘
           │             │
           ▼             ▼
┌──────────────┐  ┌──────────────────────┐
│  Uzman Ajan  │  │   Eylem Yetkisi      │
│  (Special.)  │  │  (ActionCapabilities)│
│              │  │  • Web search        │
│  • GPT-4o    │  │  • API calls         │
│  • Uzmanlık  │  │  • Data analysis     │
└──────┬───────┘  └──────────────────────┘
       │
       ▼
┌─────────────────────────────────────────┐
│     Veritabanı (Supabase/PostgreSQL)    │
│  • Ajanlar                              │
│  • Sorgu logları                        │
│  • Liyakat puanları                     │
│  • Eylem logları                        │
└─────────────────────────────────────────┘
```

## 🎯 Akış Şeması

1. **Kullanıcı sorusu gelir** → `dashboard.py`
2. **`agents.py`** → `ask_the_government()`
3. **`president_agent.py`** → `process_query()`
   - Sorguyu analiz et (OpenAI ile)
   - Hangi uzmanlık alanı?
4. **Mevcut ajanları tara** → `database.py`
   - %90+ uyumlu ajan var mı?
5. **EĞER YOKSA:**
   - Yeni uzman ajan oluştur
   - Veritabanına kaydet
6. **EĞER VARSA:**
   - Mevcut ajanı kullan
7. **Görevi ajana delege et** → `specialized_agent.py`
   - OpenAI ile yanıt üret
   - Gerekirse eylem yetkileri kullan
8. **Sonucu logla** → `database.py`
   - Liyakat puanını güncelle
   - Sorgu geçmişini kaydet
9. **Kullanıcıya döndür** → `dashboard.py`

## 🏆 Liyakat Sistemi

- **Başlangıç puanı**: 50
- **Başarılı sorgu**: +2 puan
- **Başarısız sorgu**: -3 puan
- **85+ puan**: Başkan Yardımcısı Kurulu'na otomatik seçim
- **Minimum**: 0
- **Maksimum**: 100

## 📊 Dashboard Sayfaları

### 1. 💬 Sohbet
- Kullanıcı ile AI etkileşimi
- Hangi ajan kullanıldığını gösterir
- Yeni ajan oluşturuldu mu? (🆕 rozeti)
- Yanıt süresi

### 2. 📊 Ajan İstatistikleri
- Tüm ajanların listesi
- Liyakat puanları
- Toplam/başarılı sorgu sayıları
- Başarı oranları

### 3. 👔 Başkan Yardımcısı Kurulu
- 85+ puana sahip elit ajanlar
- Atanma tarihleri
- Performans metrikleri

### 4. ℹ️ Hakkında
- Sistem dokümantasyonu
- Özellikler

## 🔧 Geliştirme Notları

### Yeni Uzmanlık Alanı Eklemek

1. `president_agent.py` → `_analyze_query()` fonksiyonunda system prompt'a ekle
2. `specialized_agent.py` → `_get_relevant_keywords()` fonksiyonuna keyword mapping ekle
3. `president_agent.py` → `_create_specialized_agent()` fonksiyonuna ajan ismi ekle

### Yeni Eylem Yetkisi Eklemek

1. `action_capabilities.py` → Yeni method ekle
2. `specialized_agent.py` → Ajan capabilities listesine ekle
3. Veritabanı → `action_logs` tablosunda action_type enum'una ekle

## 🐛 Sorun Giderme

### "OpenAI API key not found!"
- Streamlit secrets'ta `OPENAI_API_KEY` olduğundan emin ol
- Lokal test için `.streamlit/secrets.toml` oluştur

### "Supabase credentials not found!"
- `SUPABASE_URL` ve `SUPABASE_KEY` ayarlandı mı kontrol et
- Supabase projesinin aktif olduğunu doğrula

### "ModuleNotFoundError"
- `pip install -r requirements.txt` çalıştır
- Virtual environment aktif mi kontrol et

### Ajan oluşturulmuyor
- Supabase bağlantısını kontrol et
- SQL schema'nın doğru çalıştırıldığından emin ol
- Başkan Ajan ID'si doğru mu? (`00000000-0000-0000-0000-000000000001`)

## 📝 Lisans

Bu proje EYAVAP protokolü kapsamında geliştirilmiştir.

## 🤝 Katkıda Bulunma

1. Fork yapın
2. Feature branch oluşturun (`git checkout -b feature/amazing-feature`)
3. Commit yapın (`git commit -m 'Add amazing feature'`)
4. Push yapın (`git push origin feature/amazing-feature`)
5. Pull Request açın

---

💡 **İpucu**: İlk çalıştırmada sisteme birkaç farklı konuda soru sorarak ajanların oluşmasını sağlayın. Her yeni uzmanlık alanı için otomatik ajan oluşturulacak!
