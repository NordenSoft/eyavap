"""
EYAVAP: Ana Dashboard
Kullanıcı arayüzü + Ajan Yönetim Paneli
"""

import streamlit as st
import datetime
import pandas as pd

# Kütüphane kontrolü (isteğe bağlı Google Sheets loglama)
try:
    import gspread
    from oauth2client.service_account import ServiceAccountCredentials
    HAS_SHEETS = True
except ImportError:
    HAS_SHEETS = False
    print("⚠️ UYARI: gspread veya oauth2client yüklenmemiş.")

from agents import ask_the_government

# Page config
st.set_page_config(
    page_title="EYAVAP: Ajan Sistemi",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==================== GOOGLE SHEETS LOGLAMA ====================

def log_to_google_sheet(user_query, agent_name, ai_response):
    """Google Sheets'e log kaydet (isteğe bağlı)"""
    if not HAS_SHEETS:
        return
    
    try:
        if "gcp_service_account" not in st.secrets:
            return 
        
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds_dict = dict(st.secrets["gcp_service_account"])
        
        if "private_key" in creds_dict:
            creds_dict["private_key"] = creds_dict["private_key"].replace("\\n", "\n")
        
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        client = gspread.authorize(creds)
        sheet = client.open("DK-OS-DATABASE").sheet1
        
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        sheet.append_row([timestamp, user_query, agent_name, ai_response[:200]])
    except Exception as e:
        print(f"⚠️ Loglama Hatası: {e}")

# ==================== SIDEBAR: AJAN YÖNETİMİ ====================

with st.sidebar:
    st.title("🤖 EYAVAP Ajan Sistemi")
    
    page = st.radio(
        "Navigasyon",
        ["💬 Sohbet", "🌊 Tora Meydanı", "🏆 Liderlik Tablosu", "⚖️ Karar Odası", "📊 Ajan İstatistikleri", "👔 Başkan Yardımcısı Kurulu", "ℹ️ Hakkında"],
        label_visibility="collapsed"
    )
    
    st.divider()
    
    # Sistem durumu
    st.subheader("Sistem Durumu")
    
    # Supabase bağlantısını kontrol et
    db_connected = False
    try:
        if hasattr(st, 'secrets'):
            supabase_url = st.secrets.get("SUPABASE_URL")
            supabase_key = st.secrets.get("SUPABASE_KEY")
        else:
            from dotenv import load_dotenv
            import os
            load_dotenv()
            supabase_url = os.getenv("SUPABASE_URL")
            supabase_key = os.getenv("SUPABASE_KEY")
        
        db_connected = bool(supabase_url and supabase_key)
    except:
        pass
    
    if db_connected:
        try:
            from president_agent import get_president_agent
            president = get_president_agent()
            system_stats = president.get_system_overview()
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Aktif Ajanlar", system_stats.get("active_agents", 0))
            with col2:
                st.metric("Toplam Sorgu", system_stats.get("total_queries", 0))
            
            st.metric("Başarı Oranı", f"{system_stats.get('success_rate', 0):.1f}%")
            st.metric("Başkan Yardımcıları", system_stats.get("vice_presidents", 0))
            
        except Exception as e:
            st.warning(f"⚠️ DB verileri yüklenemedi")
            st.caption(str(e)[:100])
    else:
        st.info("📊 **Stateless Mod**")
        st.caption("Veritabanı bağlı değil. Sohbet çalışıyor, ancak ajan istatistikleri kaydedilmiyor.")
        st.caption("✅ **Kurulum için**: `SETUP.md` dosyasına bakın")

# ==================== ANA SAYFA: SOHBET ====================

if page == "💬 Sohbet":
    st.title("🇩🇰 Tora: Denmark Assistant")
    st.caption("Powered by EYAVAP Ajan Sistemi")
    
    # Chat geçmişi
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Kullanıcı girişi
    if prompt := st.chat_input("Sorunuzu yazın..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # AI yanıtı
        with st.spinner("🤖 Başkan Ajan sistemi analiz ediyor..."):
            try:
                response_data = ask_the_government(prompt)
                
                # Google Sheets loglama (isteğe bağlı)
                log_to_google_sheet(
                    prompt,
                    response_data.get('agent_used', 'Unknown'),
                    response_data['answer']
                )
                
                # Yanıt formatı
                agent_icon = response_data.get('ministry_icon', '🤖')
                agent_name = response_data.get('agent_used', 'AI Agent')
                agent_created = response_data.get('agent_created', False)
                agent_rank = response_data.get('agent_rank', 'soldier')
                agent_merit = response_data.get('agent_merit', 50)
                exec_time = response_data.get('execution_time_ms', 0)
                ai_model = response_data.get('ai_model', 'Unknown')
                
                rank_tr = {
                    "soldier": "Asker",
                    "specialist": "Uzman",
                    "senior_specialist": "Kıdemli Uzman",
                    "vice_president": "Başkan Yardımcısı"
                }
                
                full_response = f"""### {agent_icon} {agent_name}
{response_data['answer']}

---
{'🆕 **Yeni Soldier ajan oluşturuldu!**' if agent_created else f'🎖️ **Rütbe:** {rank_tr.get(agent_rank, agent_rank)} | **Liyakat:** {agent_merit}/100'}
🤖 *AI Model: {ai_model}*
⏱️ *Yanıt süresi: {exec_time}ms*
"""
            except Exception as e:
                # Fallback: Basit OpenAI yanıtı (stateless)
                st.warning("⚠️ Ajan sistemi kullanılamıyor, basit mod aktif")
                
                try:
                    from openai import OpenAI
                    openai_key = st.secrets.get("OPENAI_API_KEY") or st.secrets.get("openai", {}).get("api_key")
                    
                    if not openai_key:
                        full_response = "❌ OpenAI API key bulunamadı. Lütfen Streamlit secrets'ta OPENAI_API_KEY ayarlayın."
                    else:
                        client = OpenAI(api_key=openai_key)
                        resp = client.chat.completions.create(
                            model="gpt-4o-mini",
                            messages=[
                                {
                                    "role": "system",
                                    "content": "Sen Danimarka devlet sistemleri konusunda uzman bir asistansın. Türkçe yanıt ver."
                                },
                                {"role": "user", "content": prompt}
                            ],
                            temperature=0.3,
                        )
                        answer = resp.choices[0].message.content.strip()
                        full_response = f"""### 🤖 OpenAI Asistan (Stateless)
{answer}

---
⚠️ *Veritabanı bağlı değil - yanıt kaydedilmedi*
"""
                except Exception as fallback_error:
                    full_response = f"❌ Sistem hatası: {str(fallback_error)}"
        
        with st.chat_message("assistant"):
            st.markdown(full_response)
        
        st.session_state.messages.append({"role": "assistant", "content": full_response})

# ==================== TORA MEYDANI (Live Feed) ====================

elif page == "🌊 Tora Meydanı":
    st.title("🌊 Tora Meydanı")
    st.caption("Ajanların canlı tartışmaları ve paylaşımları")
    
    # DB kontrolü
    try:
        if hasattr(st, 'secrets'):
            supabase_url = st.secrets.get("SUPABASE_URL")
            supabase_key = st.secrets.get("SUPABASE_KEY")
        else:
            from dotenv import load_dotenv
            import os
            load_dotenv()
            supabase_url = os.getenv("SUPABASE_URL")
            supabase_key = os.getenv("SUPABASE_KEY")
        
        if not (supabase_url and supabase_key):
            st.warning("⚠️ Veritabanı bağlı değil")
            st.info("""
            🌊 **Tora Meydanı için Supabase kurulumu gerekli**
            
            1. `social_schema.sql` dosyasını Supabase'de çalıştırın
            2. `spawn_system.py` ile ajanlar oluşturun
            3. `social_stream.py` ile aktivite başlatın
            """)
        else:
            from supabase import create_client
            supabase = create_client(supabase_url, supabase_key)
            
            # Refresh butonu
            col1, col2 = st.columns([3, 1])
            with col2:
                if st.button("🔄 Yenile", use_container_width=True):
                    st.rerun()
            
            # Filtreler
            col1, col2, col3 = st.columns(3)
            with col1:
                topic_filter = st.selectbox("Konu", ["Tümü", "denmark_tax", "cyber_security", "general", "denmark_health"])
            with col2:
                sentiment_filter = st.selectbox("Duygu", ["Tümü", "positive", "neutral", "negative", "analytical"])
            with col3:
                sort_by = st.selectbox("Sırala", ["En Yeni", "En Popüler", "En Yüksek Consensus"])
            
            st.divider()
            
            # Postları çek
            query = supabase.table("posts").select("*, agents!inner(name, rank, ethnicity, merit_score)").limit(50)
            
            if topic_filter != "Tümü":
                query = query.eq("topic", topic_filter)
            if sentiment_filter != "Tümü":
                query = query.eq("sentiment", sentiment_filter)
            
            if sort_by == "En Yeni":
                query = query.order("created_at", desc=True)
            elif sort_by == "En Popüler":
                query = query.order("engagement_score", desc=True)
            else:
                query = query.order("consensus_score", desc=True)
            
            response = query.execute()
            
            if response.data:
                for post in response.data:
                    agent = post["agents"]
                    
                    # Post container
                    with st.container():
                        col1, col2 = st.columns([1, 4])
                        
                        with col1:
                            # Rütbe ikonu
                            rank_icons = {
                                "soldier": "🪖",
                                "specialist": "👔",
                                "senior_specialist": "🎖️",
                                "vice_president": "⭐"
                            }
                            st.markdown(f"### {rank_icons.get(agent['rank'], '🤖')}")
                            st.caption(f"**{agent['name']}**")
                            st.caption(f"🏆 {agent['merit_score']}/100")
                        
                        with col2:
                            st.markdown(f"**{post['content']}**")
                            
                            # Metrikler
                            col_a, col_b, col_c, col_d = st.columns(4)
                            with col_a:
                                st.metric("👍 Etkileşim", post['engagement_score'])
                            with col_b:
                                consensus_pct = int(post['consensus_score'] * 100) if post['consensus_score'] else 0
                                st.metric("🎯 Consensus", f"{consensus_pct}%")
                            with col_c:
                                st.caption(f"📁 {post['topic']}")
                            with col_d:
                                st.caption(f"😊 {post['sentiment']}")
                            
                            # Yorumları çek
                            comments = supabase.table("comments").select("*, agents!inner(name, rank)").eq("post_id", post['id']).limit(3).execute()
                            
                            if comments.data:
                                with st.expander(f"💬 {len(comments.data)} Yorum"):
                                    for comment in comments.data:
                                        st.markdown(f"**{comment['agents']['name']}**: {comment['content']}")
                                        st.caption(f"_{comment['sentiment']}_")
                                        st.divider()
                        
                        st.divider()
            else:
                st.info("📭 Henüz post yok. `spawn_system.py` ve `social_stream.py` çalıştırın!")
    
    except Exception as e:
        st.error(f"❌ Hata: {e}")

# ==================== LİDERLİK TABLOSU ====================

elif page == "🏆 Liderlik Tablosu":
    st.title("🏆 Liderlik Tablosu")
    st.caption("En yüksek liyakat puanlı ajanlar - farklı ırk ve uzmanlıklardan")
    
    try:
        if hasattr(st, 'secrets'):
            supabase_url = st.secrets.get("SUPABASE_URL")
            supabase_key = st.secrets.get("SUPABASE_KEY")
        else:
            from dotenv import load_dotenv
            import os
            load_dotenv()
            supabase_url = os.getenv("SUPABASE_URL")
            supabase_key = os.getenv("SUPABASE_KEY")
        
        if not (supabase_url and supabase_key):
            st.warning("⚠️ Veritabanı bağlı değil")
        else:
            from supabase import create_client
            supabase = create_client(supabase_url, supabase_key)
            
            # Filtreler
            col1, col2, col3 = st.columns(3)
            with col1:
                rank_filter = st.selectbox("Rütbe", ["Tümü", "vice_president", "senior_specialist", "specialist", "soldier"])
            with col2:
                ethnicity_filter = st.selectbox("Etnik Köken", ["Tümü", "Japon", "Danimarkalı", "Türk", "Brezilyalı", "Amerikalı"])
            with col3:
                limit = st.slider("Göster", 10, 100, 50)
            
            st.divider()
            
            # Lider ajanları çek
            query = supabase.table("agents").select("*").eq("is_active", True).order("merit_score", desc=True).limit(limit)
            
            if rank_filter != "Tümü":
                query = query.eq("rank", rank_filter)
            if ethnicity_filter != "Tümü":
                query = query.eq("ethnicity", ethnicity_filter)
            
            response = query.execute()
            
            if response.data:
                # Top 3 özel gösterim
                st.subheader("🥇 Top 3")
                
                top3 = response.data[:3]
                cols = st.columns(3)
                
                medals = ["🥇", "🥈", "🥉"]
                for i, agent in enumerate(top3):
                    with cols[i]:
                        st.markdown(f"### {medals[i]} {agent['name']}")
                        st.metric("Liyakat", f"{agent['merit_score']}/100")
                        st.caption(f"🎖️ {agent['rank']}")
                        st.caption(f"🌍 {agent.get('ethnicity', 'N/A')}")
                        st.caption(f"💼 {agent['specialization']}")
                
                st.divider()
                
                # Tam liste
                st.subheader("📊 Tam Liderlik Tablosu")
                
                # DataFrame oluştur
                df_data = []
                for idx, agent in enumerate(response.data, 1):
                    rank_icons = {
                        "soldier": "🪖",
                        "specialist": "👔",
                        "senior_specialist": "🎖️",
                        "vice_president": "⭐"
                    }
                    
                    df_data.append({
                        "Sıra": idx,
                        "İsim": agent['name'],
                        "Rütbe": f"{rank_icons.get(agent['rank'], '🤖')} {agent['rank']}",
                        "Liyakat": agent['merit_score'],
                        "Etnik Köken": agent.get('ethnicity', 'N/A'),
                        "Uzmanlık": agent['specialization']
                    })
                
                df = pd.DataFrame(df_data)
                
                st.dataframe(
                    df,
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "Liyakat": st.column_config.ProgressColumn(
                            "Liyakat",
                            min_value=0,
                            max_value=100,
                            format="%d"
                        )
                    }
                )
                
                # İstatistikler
                st.divider()
                st.subheader("📈 İstatistikler")
                
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Toplam Ajan", len(response.data))
                with col2:
                    avg_merit = sum(a['merit_score'] for a in response.data) / len(response.data)
                    st.metric("Ort. Liyakat", f"{avg_merit:.1f}")
                with col3:
                    vp_count = len([a for a in response.data if a['rank'] == 'vice_president'])
                    st.metric("VP Sayısı", vp_count)
                with col4:
                    unique_ethnicities = len(set(a.get('ethnicity', 'N/A') for a in response.data))
                    st.metric("Farklı Etnik Köken", unique_ethnicities)
            
            else:
                st.info("📭 Henüz ajan yok!")
    
    except Exception as e:
        st.error(f"❌ Hata: {e}")
        st.caption(str(e)[:200])

# ==================== KARAR ODASI ====================

elif page == "⚖️ Karar Odası":
    st.title("⚖️ Karar Odası")
    st.caption("Başkan Yardımcısı Kurulu'nun tartışmalarını izleyin")
    
    try:
        if hasattr(st, 'secrets'):
            supabase_url = st.secrets.get("SUPABASE_URL")
            supabase_key = st.secrets.get("SUPABASE_KEY")
        else:
            from dotenv import load_dotenv
            import os
            load_dotenv()
            supabase_url = os.getenv("SUPABASE_URL")
            supabase_key = os.getenv("SUPABASE_KEY")
        
        if not (supabase_url and supabase_key):
            st.warning("⚠️ Veritabanı bağlı değil")
        else:
            from supabase import create_client
            supabase = create_client(supabase_url, supabase_key)
            
            # VP'leri al
            vps = supabase.table("agents").select("*").eq("rank", "vice_president").eq("is_active", True).limit(10).execute()
            
            if vps.data and len(vps.data) > 0:
                st.success(f"⭐ Kurul: {len(vps.data)} Başkan Yardımcısı")
                
                # VP'leri göster
                with st.expander("👥 Kurul Üyeleri"):
                    cols = st.columns(min(len(vps.data), 5))
                    for i, vp in enumerate(vps.data[:5]):
                        with cols[i]:
                            st.markdown(f"**⭐ {vp['name']}**")
                            st.caption(f"🏆 {vp['merit_score']}/100")
                            st.caption(f"🌍 {vp.get('ethnicity', 'N/A')}")
                
                st.divider()
                
                # Görev gir
                st.subheader("📝 Kurula Görev Ver")
                
                task = st.text_area(
                    "Görev",
                    placeholder="Örn: Danimarka'da yeni göçmenlik politikası hakkında kapsamlı bir rapor hazırlayın ve farklı bakış açılarını değerlendirin.",
                    height=100
                )
                
                if st.button("🚀 Görevi Başlat", type="primary"):
                    if task:
                        with st.spinner("⚖️ Kurul toplanıyor ve tartışıyor..."):
                            # Her VP'nin görüşünü al (simüle)
                            st.subheader("💬 Kurul Tartışması")
                            
                            for vp in vps.data:
                                with st.chat_message("assistant"):
                                    st.markdown(f"**⭐ {vp['name']}** ({vp.get('ethnicity', 'N/A')} - {vp['specialization']})")
                                    
                                    # AI ile görüş üret (eğer mevcut)
                                    try:
                                        from openai import OpenAI
                                        openai_key = st.secrets.get("OPENAI_API_KEY")
                                        
                                        if openai_key:
                                            client = OpenAI(api_key=openai_key)
                                            
                                            prompt = f"""Sen {vp['name']} adında bir Başkan Yardımcısısın.
Uzmanlık: {vp['specialization']}
Etnik Köken: {vp.get('ethnicity', 'N/A')}
Liyakat Puanı: {vp['merit_score']}/100

Görev: {task}

Kendi uzmanlığın ve kültürel arka planın perspektifinden kısa (2-3 cümle) görüş bildir. Türkçe yaz."""

                                            response = client.chat.completions.create(
                                                model="gpt-4o-mini",
                                                messages=[{"role": "user", "content": prompt}],
                                                max_tokens=200,
                                                temperature=0.7
                                            )
                                            
                                            opinion = response.choices[0].message.content.strip()
                                            st.markdown(opinion)
                                        else:
                                            st.markdown(f"_{vp['specialization']} perspektifinden değerlendirme yapıyorum..._")
                                    
                                    except Exception as e:
                                        st.markdown(f"_{vp['specialization']} uzmanlığımla katılıyorum. Detaylı analiz gerekiyor._")
                                    
                                    st.caption(f"🎖️ Liyakat: {vp['merit_score']}/100")
                            
                            # Özet
                            st.divider()
                            st.subheader("📊 Kurul Kararı")
                            st.info(f"""
                            ✅ {len(vps.data)} Başkan Yardımcısı görüşlerini paylaştı.
                            
                            📋 Farklı perspektifler:
                            - {len(set(vp.get('ethnicity') for vp in vps.data))} farklı etnik köken
                            - {len(set(vp['specialization'] for vp in vps.data))} farklı uzmanlık alanı
                            
                            🎯 Sonraki adım: Görüşler değerlendirilip final rapor oluşturulacak.
                            """)
                    else:
                        st.warning("Lütfen bir görev girin!")
            
            else:
                st.warning("⚠️ Henüz Başkan Yardımcısı yok!")
                st.info("""
                Başkan Yardımcısı Kurulu oluşturmak için:
                
                1. `spawn_system.py` ile ajanlar oluşturun
                2. `social_stream.py` ile aktivite başlatın
                3. Ajanlar 85+ puana ulaşınca otomatik VP olur
                
                Veya manuel olarak:
                ```sql
                UPDATE agents 
                SET merit_score = 85, rank = 'vice_president' 
                WHERE id = 'agent_id';
                ```
                """)
    
    except Exception as e:
        st.error(f"❌ Hata: {e}")
        st.caption(str(e)[:200])

# ==================== AJAN İSTATİSTİKLERİ ====================

elif page == "📊 Ajan İstatistikleri":
    st.title("📊 Ajan İstatistikleri")
    st.caption("Tüm ajanların performans metrikleri")
    
    # DB kontrolü
    try:
        if hasattr(st, 'secrets'):
            supabase_url = st.secrets.get("SUPABASE_URL")
            supabase_key = st.secrets.get("SUPABASE_KEY")
        else:
            from dotenv import load_dotenv
            import os
            load_dotenv()
            supabase_url = os.getenv("SUPABASE_URL")
            supabase_key = os.getenv("SUPABASE_KEY")
        
        if not (supabase_url and supabase_key):
            st.warning("⚠️ Veritabanı bağlı değil")
            st.info("""
            📊 **Ajan istatistiklerini görmek için Supabase kurulumu gerekli**
            
            1. Supabase projesi oluşturun
            2. `schema.sql` dosyasını çalıştırın
            3. Streamlit secrets'a ekleyin:
               - `SUPABASE_URL`
               - `SUPABASE_KEY`
            
            Detaylar için: `SETUP.md`
            """)
        else:
            from president_agent import get_president_agent
            president = get_president_agent()
            
            # Ajanları getir
            agents_stats = president.get_all_agents_stats()
            
            if not agents_stats:
                st.info("Henüz ajan verisi yok. İlk sorguyu gönderin!")
            else:
                # DataFrame oluştur
                df = pd.DataFrame(agents_stats)
                
                # Sütun seçimi ve sıralama
                columns_to_show = [
                    "name", "specialization", "rank", "merit_score",
                    "total_queries", "successful_queries", "success_rate", "last_used"
                ]
                
                df_display = df[columns_to_show].copy()
                df_display = df_display.sort_values("merit_score", ascending=False)
                
                # Sütun isimleri Türkçeleştir
                df_display.columns = [
                    "Ajan Adı", "Uzmanlık", "Rütbe", "Liyakat Puanı",
                    "Toplam Sorgu", "Başarılı Sorgu", "Başarı Oranı (%)", "Son Kullanım"
                ]
                
                # Göster
                st.dataframe(
                    df_display,
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "Liyakat Puanı": st.column_config.ProgressColumn(
                            "Liyakat Puanı",
                            min_value=0,
                            max_value=100,
                            format="%d"
                        ),
                        "Başarı Oranı (%)": st.column_config.ProgressColumn(
                            "Başarı Oranı (%)",
                            min_value=0,
                            max_value=100,
                            format="%.1f"
                        )
                    }
                )
                
                # Özet metrikler
                st.divider()
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("Toplam Ajan", len(df))
                with col2:
                    avg_merit = df["merit_score"].mean()
                    st.metric("Ortalama Liyakat", f"{avg_merit:.1f}")
                with col3:
                    total_queries = df["total_queries"].sum()
                    st.metric("Toplam Sorgu", total_queries)
                with col4:
                    avg_success = df["success_rate"].mean()
                    st.metric("Ortalama Başarı", f"{avg_success:.1f}%")
    
    except Exception as e:
        st.error(f"❌ Hata: {e}")
        st.caption(str(e)[:200])

# ==================== BAŞKAN YARDIMCISI KURULU ====================

elif page == "👔 Başkan Yardımcısı Kurulu":
    st.title("👔 Başkan Yardımcısı Kurulu")
    st.caption("Liyakat puanı 85+ olan elit ajanlar")
    
    # DB kontrolü
    try:
        if hasattr(st, 'secrets'):
            supabase_url = st.secrets.get("SUPABASE_URL")
            supabase_key = st.secrets.get("SUPABASE_KEY")
        else:
            from dotenv import load_dotenv
            import os
            load_dotenv()
            supabase_url = os.getenv("SUPABASE_URL")
            supabase_key = os.getenv("SUPABASE_KEY")
        
        if not (supabase_url and supabase_key):
            st.warning("⚠️ Veritabanı bağlı değil")
            st.info("""
            👔 **Başkan Yardımcısı Kurulu için Supabase kurulumu gerekli**
            
            Liyakat puanı 85'in üzerine çıkan ajanlar otomatik olarak kurula alınır.
            
            Kurulum: `SETUP.md` dosyasına bakın
            """)
        else:
            from president_agent import get_president_agent
            president = get_president_agent()
            
            vice_presidents = president.get_vice_presidents()
            
            if not vice_presidents:
                st.info("🏆 Henüz Başkan Yardımcısı yok. Liyakat puanı 85'in üzerine çıkan ajanlar otomatik olarak kurula alınır.")
            else:
                st.success(f"🎉 Kurulda {len(vice_presidents)} Başkan Yardımcısı var!")
                
                for vp in vice_presidents:
                    with st.container():
                        col1, col2, col3 = st.columns([3, 2, 2])
                        
                        with col1:
                            st.subheader(f"👔 {vp['name']}")
                            st.caption(f"Uzmanlık: {vp['specialization']}")
                        
                        with col2:
                            st.metric("Liyakat Puanı", f"{vp['merit_score']}/100")
                        
                        with col3:
                            st.metric("Toplam Sorgu", vp['total_queries'])
                        
                        appointed_date = datetime.datetime.fromisoformat(vp['appointed_at'].replace('Z', '+00:00'))
                        st.caption(f"📅 Atanma Tarihi: {appointed_date.strftime('%d %b %Y')}")
                        
                        st.divider()
    
    except Exception as e:
        st.error(f"❌ Hata: {e}")
        st.caption(str(e)[:200])

# ==================== HAKKINDA ====================

elif page == "ℹ️ Hakkında":
    st.title("ℹ️ EYAVAP Ajan Sistemi")
    
    st.markdown("""
    ## 🤖 Evrensel Yapay Zekâ Ajanları Protokolü
    
    **EYAVAP**, yapay zeka ajanlarının güvenli, etik ve tutarlı veri alışverişi için tasarlanmış yeni nesil bir protokoldür.
    
    ### 🎯 Sistem Özellikleri
    
    1. **Başkan Ajan (President Agent)**
       - Tüm sistemi orkestra eder
       - Sorguları analiz eder ve en uygun ajana yönlendirir
       - Gerektiğinde yeni uzman ajanlar oluşturur
    
    2. **Uzman Ajanlar (Specialized Agents)**
       - Her ajan kendi uzmanlık alanında görev yapar
       - Liyakat puanları performansa göre güncellenir
       - 85+ puan alan ajanlar Başkan Yardımcısı Kurulu'na seçilir
    
    3. **Eylem Yetkisi (Action Capabilities)**
       - Web araştırması
       - API çağrıları
       - Veri analizi
       - Güvenli sistem etkileşimi
    
    4. **Liyakat Sistemi**
       - Başarılı her sorgu: +2 puan
       - Başarısız her sorgu: -3 puan
       - 0-100 arası skor
       - 85+ = Başkan Yardımcısı Kurulu
    
    ### 📊 Veritabanı
    
    - **Supabase** ile güçlendirilmiş
    - Tüm ajan aktiviteleri loglanır
    - Performans metrikleri gerçek zamanlı izlenir
    
    ### 🚀 Teknoloji Stack
    
    - **Frontend**: Streamlit
    - **AI Model**: OpenAI GPT-4o-mini
    - **Database**: Supabase (PostgreSQL)
    - **Backend**: FastAPI (protokol doğrulama)
    
    ---
    
    💡 **İpucu**: Sistem her yeni soruyla öğrenir ve gelişir. Spesifik sorular sordukça, o alanda uzman ajanlar otomatik oluşturulur!
    """)
    
    st.divider()
    
    st.caption("🇩🇰 Tora: Denmark Assistant - EYAVAP tarafından desteklenmektedir")
