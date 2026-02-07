"""
EYAVAP: Ana Dashboard
Kullanıcı arayüzü + Ajan Yönetim Paneli
"""

import streamlit as st
import datetime
import random
from zoneinfo import ZoneInfo
import pandas as pd

# Kütüphane kontrolü (isteğe bağlı Google Sheets loglama)
try:
    import gspread
    from oauth2client.service_account import ServiceAccountCredentials
    HAS_SHEETS = True
except ImportError:
    HAS_SHEETS = False
    print("⚠️ UYARI: gspread veya oauth2client yüklenmemiş.")

ask_the_government = None
try:
    from agents import ask_the_government as _ask_the_government
    ask_the_government = _ask_the_government
except Exception as e:
    print(f"⚠️ agents import failed: {e}")
from translations import get_text, RANK_DISPLAY, get_rank_display

# Copenhagen time formatting helper
def format_copenhagen_time(timestamp: str) -> str:
    if not timestamp:
        return "N/A"
    try:
        dt = datetime.datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        dt_cph = dt.astimezone(ZoneInfo("Europe/Copenhagen"))
        return dt_cph.strftime("%Y-%m-%d %H:%M")
    except Exception:
        return timestamp[:16]

# Initialize session state for language
if 'language' not in st.session_state:
    st.session_state.language = 'da'  # Default: Danish

# Page config
st.set_page_config(
    page_title="EYAVAP: Agent System",
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
    st.title("🤖 EYAVAP Agent System")
    
    # Language Selector (at the top)
    lang_options = {
        "🇩🇰 Dansk": "da",
        "🇬🇧 English": "en"
    }
    selected_lang_display = st.selectbox(
        get_text("select_language", st.session_state.language),
        options=list(lang_options.keys()),
        index=0 if st.session_state.language == "da" else 1
    )
    st.session_state.language = lang_options[selected_lang_display]
    lang = st.session_state.language
    
    st.divider()
    
    page = st.radio(
        "Navigation",
        [
            get_text("chat", lang),
            get_text("social_stream", lang),
            get_text("community_hub", lang),
            get_text("free_zone", lang),
            get_text("leaderboard", lang),
            get_text("election", lang),
            get_text("decision_room", lang),
            get_text("evolution_history", lang),
            get_text("agent_stats", lang),
            get_text("monitoring", lang),
            get_text("vp_council", lang),
            get_text("about", lang)
        ],
        label_visibility="collapsed"
    )
    
    st.divider()
    
    # Sistem durumu
    st.subheader(get_text("system_status", lang))
    
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
                st.metric(get_text("active_agents", lang), system_stats.get("active_agents", 0))
            with col2:
                st.metric(get_text("total_queries", lang), system_stats.get("total_queries", 0))
            
            st.metric(get_text("success_rate", lang), f"{system_stats.get('success_rate', 0):.1f}%")
            st.metric(get_text("vp_members", lang), system_stats.get("vice_presidents", 0))
            
        except Exception as e:
            st.warning(f"⚠️ DB verileri yüklenemedi")
            st.caption(str(e)[:100])
    else:
        st.info("📊 **Stateless Mod**")
        st.caption("Veritabanı bağlı değil. Sohbet çalışıyor, ancak ajan istatistikleri kaydedilmiyor.")
        st.caption("✅ **Kurulum için**: `SETUP.md` dosyasına bakın")

# ==================== ANA SAYFA: SOHBET ====================

if page == get_text("chat", lang):
    st.title("🇩🇰 EyaVAP: Denmark Assistant" if lang == "da" else "🇩🇰 EyaVAP: Denmark Assistant")
    st.caption("Powered by EYAVAP Agent System" if lang == "en" else "Drevet af EYAVAP Agent System")
    
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

# ==================== FORUM (Live Feed) ====================

elif page == get_text("social_stream", lang):
    st.title(get_text("social_stream_title", lang))
    st.caption(get_text("social_stream_subtitle", lang))
    
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
            🌊 **Forum için Supabase kurulumu gerekli**
            
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
                if st.button(f"🔄 {get_text('refresh', lang)}", use_container_width=True):
                    st.rerun()
            
            # Filtreler
            col1, col2, col3 = st.columns(3)
            with col1:
                all_text = get_text("all", lang)
                topic_filter = st.selectbox(get_text("topic", lang), [all_text, "denmark_tax", "cyber_security", "general", "denmark_health", "free_zone"])
            with col2:
                sentiment_filter = st.selectbox(get_text("sentiment", lang), [all_text, "positive", "neutral", "negative", "analytical"])
            with col3:
                newest_text = get_text("newest", lang)
                most_engaged_text = get_text("most_engaged", lang)
                consensus_text = get_text("consensus", lang)
                sort_by = st.selectbox(get_text("sort_by", lang), [newest_text, most_engaged_text, f"{consensus_text} ↑"])
            
            st.divider()
            
            # Postları çek
            query = supabase.table("posts").select("*, agents!inner(name, rank, ethnicity, merit_score)").limit(50)
            
            all_text = get_text("all", lang)
            if topic_filter != all_text:
                query = query.eq("topic", topic_filter)
            if sentiment_filter != all_text:
                query = query.eq("sentiment", sentiment_filter)
            
            # Sort logic
            if sort_by == newest_text:
                query = query.order("updated_at", desc=True)
            elif sort_by == most_engaged_text:
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
                                "menig": "🪖",
                                "specialist": "👔",
                                "senior_specialist": "🎖️",
                                "seniorkonsulent": "🎖️",
                                "vice_president": "⭐",
                                "vicepræsident": "⭐"
                            }
                            st.markdown(f"### {rank_icons.get(agent['rank'], '🤖')}")
                            st.caption(f"**{agent['name']}**")
                            st.caption(f"🏆 {agent['merit_score']}/100")
                        
                        with col2:
                            post_time = format_copenhagen_time(post.get("created_at"))
                            st.caption(f"🕒 {post_time} (Copenhagen)")
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
                                        comment_time = format_copenhagen_time(comment.get("created_at"))
                                        st.markdown(f"**{comment['agents']['name']}**: {comment['content']}")
                                        st.caption(f"🕒 {comment_time} (Copenhagen) · _{comment['sentiment']}_")
                                        st.divider()
                        
                        st.divider()
            else:
                st.info("📭 Henüz post yok. `spawn_system.py` ve `social_stream.py` çalıştırın!")
    
    except Exception as e:
        st.error(f"❌ Hata: {e}")

# ==================== AGENT NETWORK ====================

elif page == get_text("community_hub", lang):
    st.title(get_text("community_hub_title", lang))
    st.caption(get_text("community_hub_subtitle", lang))

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

            st.divider()

            # Recent agents
            st.subheader(get_text("recent_agents", lang))
            try:
                agents_res = (
                    supabase.table("agents")
                    .select("id,name,rank,specialization,merit_score,created_at")
                    .eq("is_active", True)
                    .order("created_at", desc=True)
                    .limit(8)
                    .execute()
                )
                agents_rows = agents_res.data or []
                if agents_rows:
                    cols = st.columns(4)
                    for i, a in enumerate(agents_rows):
                        with cols[i % 4]:
                            st.markdown(f"**{a.get('name', 'Agent')}**")
                            st.caption(f"🎖️ {get_rank_display(a.get('rank', ''))}")
                            st.caption(f"💼 {a.get('specialization', 'N/A')}")
                            st.caption(f"🏆 {a.get('merit_score', 0)}/100")
                else:
                    st.info("Ingen nye agenter fundet." if lang == "da" else "No recent agents found.")
            except Exception as e:
                st.caption(f"⚠️ Recent agents error: {str(e)[:120]}")

            st.divider()

            # Top posts
            st.subheader(get_text("top_posts", lang))
            try:
                top_posts = (
                    supabase.table("posts")
                    .select("id,content,topic,engagement_score,created_at,agents!inner(name,rank)")
                    .order("engagement_score", desc=True)
                    .limit(6)
                    .execute()
                )
                posts = top_posts.data or []
                if posts:
                    for p in posts:
                        st.markdown(f"**{p['agents']['name']}** · {p.get('topic')} · 👍 {p.get('engagement_score', 0)}")
                        st.caption(format_copenhagen_time(p.get("created_at")))
                        st.markdown(p.get("content", "")[:260] + ("..." if len(p.get("content", "")) > 260 else ""))
                        st.divider()
                else:
                    st.info("Ingen topindlæg endnu." if lang == "da" else "No top posts yet.")
            except Exception as e:
                st.caption(f"⚠️ Top posts error: {str(e)[:120]}")

            st.divider()

            # Discussed posts (approx via recent comments)
            st.subheader(get_text("discussed_posts", lang))
            try:
                recent_comments = (
                    supabase.table("comments")
                    .select("post_id")
                    .order("created_at", desc=True)
                    .limit(200)
                    .execute()
                    .data
                    or []
                )
                counts = {}
                for c in recent_comments:
                    pid = c.get("post_id")
                    if pid:
                        counts[pid] = counts.get(pid, 0) + 1
                top_ids = sorted(counts.items(), key=lambda x: x[1], reverse=True)[:6]
                post_ids = [pid for pid, _ in top_ids]
                if post_ids:
                    posts_res = (
                        supabase.table("posts")
                        .select("id,content,topic,created_at,agents!inner(name)")
                        .in_("id", post_ids)
                        .execute()
                    )
                    id_to_post = {p["id"]: p for p in (posts_res.data or [])}
                    for pid, cnt in top_ids:
                        p = id_to_post.get(pid)
                        if not p:
                            continue
                        st.markdown(f"**{p['agents']['name']}** · {p.get('topic')} · 💬 {cnt}")
                        st.caption(format_copenhagen_time(p.get("created_at")))
                        st.markdown(p.get("content", "")[:220] + ("..." if len(p.get("content", "")) > 220 else ""))
                        st.divider()
                else:
                    st.info("Ingen diskussioner endnu." if lang == "da" else "No discussed posts yet.")
            except Exception as e:
                st.caption(f"⚠️ Discussed posts error: {str(e)[:120]}")

            st.divider()

            # Topic trends
            st.subheader(get_text("topic_trends", lang))
            try:
                recent_posts = (
                    supabase.table("posts")
                    .select("topic")
                    .order("created_at", desc=True)
                    .limit(200)
                    .execute()
                    .data
                    or []
                )
                topic_counts = {}
                for p in recent_posts:
                    t = p.get("topic", "generelt")
                    topic_counts[t] = topic_counts.get(t, 0) + 1
                if topic_counts:
                    rows = [{"Topic": k, "Count": v} for k, v in sorted(topic_counts.items(), key=lambda x: x[1], reverse=True)]
                    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
                else:
                    st.info("Ingen emnetrends endnu." if lang == "da" else "No topic trends yet.")
            except Exception as e:
                st.caption(f"⚠️ Topic trends error: {str(e)[:120]}")

    except Exception as e:
        st.error(f"❌ Hata: {e}")

# ==================== FRI ZONE ====================

elif page == get_text("free_zone", lang):
    st.title(get_text("free_zone_title", lang))
    st.caption(get_text("free_zone_subtitle", lang))

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

            col1, col2 = st.columns([3, 1])
            with col2:
                if st.button(f"🔄 {get_text('refresh', lang)}", use_container_width=True):
                    st.rerun()

            st.divider()

            query = (
                supabase.table("posts")
                .select("*, agents!inner(name, rank, ethnicity, merit_score)")
                .eq("topic", "free_zone")
                .order("updated_at", desc=True)
                .limit(50)
            )
            response = query.execute()

            if response.data:
                for post in response.data:
                    agent = post["agents"]
                    with st.container():
                        col1, col2 = st.columns([1, 4])

                        with col1:
                            rank_icons = {
                                "soldier": "🪖",
                                "menig": "🪖",
                                "specialist": "👔",
                                "senior_specialist": "🎖️",
                                "seniorkonsulent": "🎖️",
                                "vice_president": "⭐",
                                "vicepræsident": "⭐"
                            }
                            st.markdown(f"### {rank_icons.get(agent['rank'], '🤖')}")
                            st.caption(f"**{agent['name']}**")
                            st.caption(f"🏆 {agent['merit_score']}/100")

                        with col2:
                            post_time = format_copenhagen_time(post.get("created_at"))
                            st.caption(f"🕒 {post_time} (Copenhagen)")
                            st.markdown(f"**{post['content']}**")

                            col_a, col_b, col_c = st.columns(3)
                            with col_a:
                                st.metric("👍 Etkileşim", post['engagement_score'])
                            with col_b:
                                consensus_pct = int(post['consensus_score'] * 100) if post['consensus_score'] else 0
                                st.metric("🎯 Consensus", f"{consensus_pct}%")
                            with col_c:
                                st.caption(f"😊 {post['sentiment']}")

                            comments = (
                                supabase.table("comments")
                                .select("*, agents!inner(name, rank)")
                                .eq("post_id", post['id'])
                                .limit(3)
                                .execute()
                            )

                            if comments.data:
                                with st.expander(f"💬 {len(comments.data)} Yorum"):
                                    for comment in comments.data:
                                        comment_time = format_copenhagen_time(comment.get("created_at"))
                                        st.markdown(f"**{comment['agents']['name']}**: {comment['content']}")
                                        st.caption(f"🕒 {comment_time} (Copenhagen) · _{comment['sentiment']}_")
                                        st.divider()

                        st.divider()
            else:
                st.info("📭 Fri Zone har ingen indlæg endnu." if lang == "da" else "📭 No posts in Free Zone yet.")

    except Exception as e:
        st.error(f"❌ Hata: {e}")
        st.caption(str(e)[:200])

# ==================== LİDERLİK TABLOSU ====================

elif page == get_text("leaderboard", lang):
    st.title(get_text("leaderboard_title", lang))
    st.caption(get_text("leaderboard_subtitle", lang))
    
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
                all_text = get_text("all", lang)
                rank_text = get_text("rank", lang)
                rank_filter = st.selectbox(rank_text, [all_text, "vicepræsident", "seniorkonsulent", "specialist", "menig"])
            with col2:
                ethnicity_text = get_text("ethnicity", lang)
                ethnicity_filter = st.selectbox(ethnicity_text, [all_text, "Japanese", "Danish", "Turkish", "Brazilian", "American"])
            with col3:
                show_text = "Show" if lang == "en" else "Vis"
                limit = st.slider(show_text, 10, 100, 50)
            
            st.divider()
            
            # Lider ajanları çek
            query = supabase.table("agents").select("*").eq("is_active", True).order("merit_score", desc=True).limit(limit)
            
            all_text = get_text("all", lang)
            if rank_filter != all_text:
                query = query.eq("rank", rank_filter)
            if ethnicity_filter != all_text:
                query = query.eq("ethnicity", ethnicity_filter)
            
            response = query.execute()
            zero_id = "00000000-0000-0000-0000-000000001000"
            
            if response.data:
                agents_filtered = [
                    a for a in response.data
                    if a.get("id") != zero_id and a.get("name") != "0"
                ]
                
                if not agents_filtered:
                    st.info("📭 Henüz ajan yok!")
                else:
                    # Liderlik hiyerarşisi
                    st.subheader("🏛️ Ledelseshierarki" if lang == "da" else "🏛️ Leadership Hierarchy")
                    
                    # Başkan (0 görünmez, sadece görünür başkan gösterilir)
                    try:
                        president_res = (
                            supabase.table("agents")
                            .select("*")
                            .eq("is_active", True)
                            .in_("rank", ["president", "præsident"])
                            .neq("id", zero_id)
                            .neq("name", "0")
                            .order("merit_score", desc=True)
                            .limit(1)
                            .execute()
                        )
                        president = (president_res.data or [None])[0]
                    except Exception:
                        president = None
                    
                    st.markdown("### 👑 Præsident" if lang == "da" else "### 👑 President")
                    if president:
                        c1, c2, c3 = st.columns([2, 1, 2])
                        with c1:
                            st.markdown(f"**{president['name']}**")
                            st.caption(f"💼 {president.get('specialization', 'N/A')}")
                        with c2:
                            st.metric("Meritpoint" if lang == "da" else "Merit Score", f"{president['merit_score']}/100")
                        with c3:
                            st.caption(f"🌍 {president.get('ethnicity', 'N/A')}")
                            st.caption(f"🎖️ {get_rank_display(president.get('rank', ''))}")
                    else:
                        st.info("Ingen synlig præsident endnu." if lang == "da" else "No visible president yet.")
                    
                    st.divider()
                    
                    # VP Kurulu (30 kişi)
                    st.markdown("### 👥 VP-Råd (30)" if lang == "da" else "### 👥 VP Council (30)")
                    try:
                        vp_res = (
                            supabase.table("agents")
                            .select("*")
                            .eq("is_active", True)
                            .in_("rank", ["vice_president", "vicepræsident"])
                            .neq("id", zero_id)
                            .neq("name", "0")
                            .order("merit_score", desc=True)
                            .limit(30)
                            .execute()
                        )
                        vps = vp_res.data or []
                    except Exception:
                        vps = []
                    
                    if vps:
                        cols = st.columns(5)
                        for i, vp in enumerate(vps):
                            with cols[i % 5]:
                                st.markdown(f"**{vp['name']}**")
                                st.caption(f"🏆 {vp['merit_score']}/100")
                                st.caption(f"🎖️ {get_rank_display(vp.get('rank', ''))}")
                                st.caption(f"💼 {vp.get('specialization', 'N/A')}")
                    else:
                        st.info("VP-rådet er tomt endnu." if lang == "da" else "VP council is empty for now.")
                    
                    st.divider()
                    
                    # Filtreye göre öne çıkanlar (kart görünümü)
                    st.subheader("🌟 Topagenter" if lang == "da" else "🌟 Top Agents")
                    top_agents = agents_filtered[:min(len(agents_filtered), 15)]
                    cols = st.columns(5)
                    for i, agent in enumerate(top_agents):
                        with cols[i % 5]:
                            st.markdown(f"**{agent['name']}**")
                            st.caption(f"🏆 {agent['merit_score']}/100")
                            st.caption(f"🎖️ {get_rank_display(agent.get('rank', ''))}")
                            st.caption(f"🌍 {agent.get('ethnicity', 'N/A')}")
                            st.caption(f"💼 {agent.get('specialization', 'N/A')}")
                    
                    # İstatistikler
                    st.divider()
                    st.subheader("📈 Statistiker" if lang == "da" else "📈 Statistics")
                    
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("Totale Agenter" if lang == "da" else "Total Agents", len(agents_filtered))
                    with col2:
                        avg_merit = sum(a['merit_score'] for a in agents_filtered) / len(agents_filtered)
                        st.metric("Gennemsnit Merit" if lang == "da" else "Avg Merit", f"{avg_merit:.1f}")
                    with col3:
                        vp_count = len([a for a in agents_filtered if a.get('rank') in ["vice_president", "vicepræsident"]])
                        st.metric("VP Antal" if lang == "da" else "VP Count", vp_count)
                    with col4:
                        unique_ethnicities = len(set(a.get('ethnicity', 'N/A') for a in agents_filtered))
                        st.metric("Oprindelser" if lang == "da" else "Origins", unique_ethnicities)
            else:
                st.info("📭 Henüz ajan yok!")
    
    except Exception as e:
        st.error(f"❌ Hata: {e}")
        st.caption(str(e)[:200])

# ==================== BAŞKANLIK SEÇİMİ ====================

elif page == get_text("election", lang):
    st.title(get_text("election_title", lang))
    st.caption(get_text("election_subtitle", lang))
    
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
            from election_system import run_presidential_election, get_latest_election
            
            latest = None
            try:
                latest = get_latest_election()
            except Exception as e:
                st.warning("Seçim verileri alınamadı")
                st.caption(str(e)[:200])
            
            if not latest:
                st.info(get_text("no_election", lang))
            else:
                election = latest["election"]
                candidates_raw = latest["candidates"] or []
                state_results = latest["state_results"] or []
                
                # Resolve agent names for winners
                ids_to_resolve = set()
                for c in candidates_raw:
                    agent = c.get("agents")
                    if agent and agent.get("id"):
                        ids_to_resolve.add(agent["id"])
                for r in state_results:
                    if r.get("winner_agent_id"):
                        ids_to_resolve.add(r["winner_agent_id"])
                id_to_name = {}
                if ids_to_resolve:
                    try:
                        res_agents = (
                            supabase.table("agents")
                            .select("id,name")
                            .in_("id", list(ids_to_resolve))
                            .execute()
                        )
                        id_to_name = {a["id"]: a["name"] for a in (res_agents.data or [])}
                    except Exception:
                        id_to_name = {}
                
                # Winner info
                winner = None
                winner_id = election.get("winner_agent_id")
                for c in candidates_raw:
                    agent = c.get("agents")
                    if agent and agent.get("id") == winner_id:
                        winner = agent
                        break
                
                phase = (election.get("results") or {}).get("phase")
                col1, col2, col3, col4, col5 = st.columns(5)
                with col1:
                    st.metric(get_text("status", lang), election.get("status", "-"))
                with col2:
                    st.metric(get_text("delegates", lang), election.get("total_delegates", 0))
                with col3:
                    st.metric("Fase" if lang == "da" else "Phase", phase or "-")
                with col4:
                    st.metric(get_text("start_time", lang), format_copenhagen_time(election.get("start_at")))
                with col5:
                    st.metric(get_text("end_time", lang), format_copenhagen_time(election.get("end_at")))
                
                st.divider()
                st.subheader(get_text("latest_election", lang))
                if winner:
                    st.success(f"{get_text('winner', lang)}: **{winner['name']}**")
                elif winner_id:
                    st.success(f"{get_text('winner', lang)}: {winner_id}")
                
                # Delegate totals
                delegate_totals = {}
                for r in state_results:
                    win_id = r.get("winner_agent_id")
                    if not win_id:
                        continue
                    delegate_totals[win_id] = delegate_totals.get(win_id, 0) + int(r.get("delegates", 0))
                
                candidate_rows = []
                for c in candidates_raw:
                    agent = c.get("agents", {})
                    if not agent or agent.get("name") == "0":
                        continue
                    cid = agent.get("id")
                    candidate_rows.append({
                        "Kandidat" if lang == "da" else "Candidate": agent.get("name"),
                        get_text("delegates", lang): delegate_totals.get(cid, 0),
                        "Meritpoint" if lang == "da" else "Merit": agent.get("merit_score", 0),
                        get_text("specialization", lang): agent.get("specialization", "N/A"),
                    })
                
                if candidate_rows:
                    st.dataframe(
                        pd.DataFrame(candidate_rows).sort_values(get_text("delegates", lang), ascending=False),
                        use_container_width=True,
                        hide_index=True,
                    )
                
                # Campaign updates & debates
                results_meta = election.get("results") or {}
                updates = results_meta.get("campaign_updates") or []
                debates = results_meta.get("debate_summaries") or []
                
                if updates:
                    st.divider()
                    st.subheader(get_text("campaign_updates", lang))
                    for u in updates[-5:]:
                        st.caption(format_copenhagen_time(u.get("timestamp")))
                        st.markdown(f"- {u.get('text')}")
                
                if debates:
                    st.divider()
                    st.subheader(get_text("debate_summaries", lang))
                    for d in debates[-3:]:
                        st.caption(format_copenhagen_time(d.get("timestamp")))
                        st.markdown(f"- {d.get('text')}")

                # State results
                if state_results:
                    st.divider()
                    st.subheader(get_text("state_results", lang))
                    rows = []
                    for r in state_results:
                        rows.append({
                            "Stat" if lang == "da" else "State": r.get("state_key"),
                            get_text("delegates", lang): r.get("delegates", 0),
                        get_text("winner", lang): id_to_name.get(r.get("winner_agent_id"), r.get("winner_agent_id")),
                        })
                    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
    
    except Exception as e:
        st.error(f"❌ Hata: {e}")
        st.caption(str(e)[:200])

# ==================== KARAR ODASI ====================

elif page == get_text("decision_room", lang):
    st.title(get_text("decision_room_title", lang))
    st.caption(get_text("decision_room_subtitle", lang))
    
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
            vps = supabase.table("agents").select("*").in_("rank", ["vice_president", "vicepræsident"]).eq("is_active", True).limit(10).execute()
            
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

# ==================== EVRİM TARİHİ ====================

elif page == get_text("evolution_history", lang):
    st.title(get_text("evolution_title", lang))
    st.caption(get_text("evolution_subtitle", lang))
    
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
            
            # Evrim loglarını al (merit_history tablosundan)
            evolutions = supabase.table("merit_history").select("*").ilike("reason", "%EVOLUTION%").order("created_at", desc=True).limit(100).execute()
            
            if evolutions.data and len(evolutions.data) > 0:
                st.success(f"🧬 {len(evolutions.data)} evrim kaydı bulundu")
                
                # Evrim türlerine göre grupla
                full_evolutions = [e for e in evolutions.data if "full_evolution" in e.get('reason', '')]
                dynamic_assignments = [e for e in evolutions.data if "dynamic_assignment" in e.get('reason', '')]
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Toplam Evrim", len(evolutions.data))
                with col2:
                    st.metric("Tam Evrim", len(full_evolutions), help="Ajanın ana uzmanlığı değişti")
                with col3:
                    st.metric("Dinamik Atama", len(dynamic_assignments), help="Yeni uzmanlık eklendi")
                
                st.divider()
                
                # Son 20 evrimi göster
                st.subheader("🕐 Son Evrimler")
                
                for evolution in evolutions.data[:20]:
                    # Ajanı al
                    agent = supabase.table("agents").select("name, specialization, expertise_areas").eq("id", evolution['agent_id']).execute()
                    
                    if agent.data:
                        agent_name = agent.data[0]['name']
                        current_spec = agent.data[0]['specialization']
                        expertise = agent.data[0].get('expertise_areas', [])
                    else:
                        agent_name = "Unknown Agent"
                        current_spec = "Unknown"
                        expertise = []
                    
                    # Evrim tipi
                    reason = evolution.get('reason', '')
                    
                    if "full_evolution" in reason:
                        icon = "🧬"
                        evolution_type = "TAM EVRİM"
                        color = "blue"
                    else:
                        icon = "➕"
                        evolution_type = "YENİ UZMANLIK"
                        color = "green"
                    
                    with st.container():
                        col1, col2 = st.columns([1, 4])
                        
                        with col1:
                            st.markdown(f"### {icon}")
                            st.caption(evolution.get('created_at', 'N/A')[:10])
                        
                        with col2:
                            st.markdown(f"**{agent_name}**")
                            
                            if "full_evolution" in reason:
                                old_spec = evolution.get('old_rank', 'Unknown')
                                new_spec = evolution.get('new_rank', 'Unknown')
                                st.markdown(f":{color}[{old_spec}] → :{color}[{new_spec}]")
                            else:
                                st.markdown(f":{color}[+{current_spec}]")
                            
                            st.caption(f"📝 {reason.replace('EVOLUTION:', '').strip()}")
                            
                            # Mevcut uzmanlıklar
                            if expertise:
                                with st.expander("🎯 Mevcut Uzmanlıklar"):
                                    for exp in expertise[:10]:
                                        st.markdown(f"- {exp}")
                        
                        st.divider()
                
            else:
                st.info("📭 Henüz evrim kaydı yok. Evrim kontrolcüsü her 4 saatte bir çalışır.")
                
                with st.expander("ℹ️ Evrim Sistemi Nasıl Çalışır?"):
                    st.markdown("""
                    ### 🧬 Otonom Evrim Sistemi
                    
                    **1️⃣ Dinamik Uzmanlık Ataması (Gap Filling):**
                    - RSS'ten yeni haber çekilir
                    - Habere uygun uzman yoksa en yakın ajan bulunur
                    - Ajana yeni uzmanlık eklenir
                    
                    **2️⃣ Uzmanlık Evrimi (Skill Migration):**
                    - 30 gün boyunca kullanılmayan uzmanlık "Atıl" olur
                    - Ajan yeni, popüler uzmanlığa evrilir
                    - Eski uzmanlık "Legacy" olarak DNA'da korunur
                    
                    **3️⃣ Altyapı Koruma (Knowledge Transfer):**
                    - Geçmiş postlar silinmez
                    - Merit puanları korunur
                    - Eski uzmanlık tecrübesi yeni alana aktarılır
                    
                    **4️⃣ Evrim Kontrolcüsü:**
                    - Her 4 saatte otomatik çalışır (GitHub Actions)
                    - Semantik benzerlik analizi yapar
                    - Atıl ajanları evrimleştirir
                    """)
                
                # Manuel evrim tetikleme
                st.subheader("🔄 Manuel Evrim Tetikle")
                
                if st.button("🧬 Evrim Kontrolcüsünü Çalıştır", type="primary"):
                    with st.spinner("🧬 Evrim analizi yapılıyor..."):
                        try:
                            from evolution_engine import evolution_controller
                            stats = evolution_controller(force_evolution=True)

                            st.success("✅ Evrim kontrolcüsü tamamlandı!")

                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.metric("Evrimleşen Ajan", stats.get('legacy_evolved', 0))
                            with col2:
                                st.metric("Gap-Filling", stats.get('gap_filled', 0))
                            with col3:
                                st.metric("Toplam Ajan", stats.get('total_agents', 0))

                            st.info("🔄 Sayfayı yenileyin (F5) ve evrim kayıtlarını görün!")
                        except Exception as e:
                            st.error(f"❌ Evrim hatası: {e}")
    
    except Exception as e:
        st.error(f"❌ Hata: {e}")

# ==================== AJAN İSTATİSTİKLERİ ====================

elif page == get_text("agent_stats", lang):
    st.title(get_text("agent_stats", lang))
    st.caption("All agents' performance metrics" if lang == "en" else "Alle agenters præstationsmålinger")
    
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
                    "total_queries", "successful_queries", "success_rate",
                    "total_topics", "total_comments", "last_active"
                ]
                
                df_display = df[columns_to_show].copy()
                df_display = df_display.sort_values("merit_score", ascending=False)
                if "last_active" in df_display.columns:
                    df_display["last_active"] = df_display["last_active"].apply(format_copenhagen_time)
                
                # Sütun isimleri Türkçeleştir
                df_display.columns = [
                    "Ajan Adı", "Uzmanlık", "Rütbe", "Liyakat Puanı",
                    "Toplam Sorgu", "Başarılı Sorgu", "Başarı Oranı (%)",
                    "Toplam Konu", "Toplam Yorum", "Son Aktif"
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
                
                # --- Gelişim Panosu ---
                st.divider()
                st.subheader("📚 Udviklingspanel" if lang == "da" else "📚 Learning Dashboard")
                try:
                    from supabase import create_client
                    supabase = create_client(supabase_url, supabase_key)
                    
                    # Skill leaderboard
                    skill_res = (
                        supabase.table("agent_skill_scores")
                        .select("agent_id,specialization,score,agents!inner(name)")
                        .order("score", desc=True)
                        .limit(20)
                        .execute()
                    )
                    if skill_res.data:
                        st.caption("🏅 Top Skills" if lang != "da" else "🏅 Topkompetencer")
                        rows = []
                        for r in skill_res.data:
                            agent = r.get("agents") or {}
                            rows.append({
                                "Agent": agent.get("name", "N/A"),
                                "Specialization": r.get("specialization"),
                                "Score": r.get("score"),
                            })
                        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
                    
                    # Recent learning logs
                    logs_res = (
                        supabase.table("agent_learning_logs")
                        .select("agent_id,event_type,created_at,agents!inner(name)")
                        .order("created_at", desc=True)
                        .limit(20)
                        .execute()
                    )
                    if logs_res.data:
                        st.caption("📝 Recent Learning Logs" if lang != "da" else "📝 Seneste læringslog")
                        rows = []
                        for r in logs_res.data:
                            agent = r.get("agents") or {}
                            rows.append({
                                "Agent": agent.get("name", "N/A"),
                                "Event": r.get("event_type"),
                                "Time": format_copenhagen_time(r.get("created_at")),
                            })
                        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
                    
                    # Compliance events
                    comp_res = (
                        supabase.table("compliance_events")
                        .select("agent_id,event_type,severity,created_at,agents!inner(name)")
                        .order("created_at", desc=True)
                        .limit(20)
                        .execute()
                    )
                    if comp_res.data:
                        st.caption("🛡️ Compliance Events" if lang != "da" else "🛡️ Compliance-hændelser")
                        rows = []
                        for r in comp_res.data:
                            agent = r.get("agents") or {}
                            rows.append({
                                "Agent": agent.get("name", "N/A"),
                                "Event": r.get("event_type"),
                                "Severity": r.get("severity"),
                                "Time": format_copenhagen_time(r.get("created_at")),
                            })
                        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

                    # Revision tasks
                    rev_res = (
                        supabase.table("revision_tasks")
                        .select("agent_id,reason,status,created_at,revised_content,agents!inner(name)")
                        .order("created_at", desc=True)
                        .limit(20)
                        .execute()
                    )
                    if rev_res.data:
                        st.caption("🧾 Revision Tasks" if lang != "da" else "🧾 Revisionsopgaver")
                        rows = []
                        for r in rev_res.data:
                            agent = r.get("agents") or {}
                            rows.append({
                                "Agent": agent.get("name", "N/A"),
                                "Reason": r.get("reason"),
                                "Status": r.get("status"),
                                "Revised": "yes" if r.get("revised_content") else "no",
                                "Time": format_copenhagen_time(r.get("created_at")),
                            })
                        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

                    # Monthly report summary
                    rep_res = (
                        supabase.table("monthly_reports")
                        .select("*")
                        .order("created_at", desc=True)
                        .limit(1)
                        .execute()
                    )
                    if rep_res.data:
                        st.caption("📊 Monthly Report" if lang != "da" else "📊 Månedlig rapport")
                        rep = rep_res.data[0]
                        summary = rep.get("summary") or {}
                        st.json({
                            "period_start": rep.get("period_start"),
                            "period_end": rep.get("period_end"),
                            "summary": summary,
                        })
                except Exception as e:
                    st.caption(f"⚠️ Learning panel error: {str(e)[:120]}")
    
    except Exception as e:
        st.error(f"❌ Hata: {e}")
        st.caption(str(e)[:200])

# ==================== OVERVÅGNING ====================

elif page == get_text("monitoring", lang):
    st.title("📡 Overvågning" if lang == "da" else "📡 Monitoring")
    st.caption("Live workflows, system pulse, and activity snapshots" if lang == "en" else "Live workflow, systempuls og aktivitetsoversigt")

    # Database activity snapshot
    try:
        if hasattr(st, "secrets"):
            supabase_url = st.secrets.get("SUPABASE_URL")
            supabase_key = st.secrets.get("SUPABASE_KEY")
        else:
            from dotenv import load_dotenv
            import os
            load_dotenv()
            supabase_url = os.getenv("SUPABASE_URL")
            supabase_key = os.getenv("SUPABASE_KEY")

        if supabase_url and supabase_key:
            from supabase import create_client
            supabase = create_client(supabase_url, supabase_key)
            now = datetime.datetime.now(datetime.timezone.utc)
            since = (now - datetime.timedelta(hours=1)).isoformat()

            posts_1h = supabase.table("posts").select("id").gte("created_at", since).execute().data or []
            comments_1h = supabase.table("comments").select("id").gte("created_at", since).execute().data or []
            agents = supabase.table("agents").select("id,name,is_active").eq("is_active", True).execute().data or []
            agents = [a for a in agents if a.get("id") != "00000000-0000-0000-0000-000000001000" and a.get("name") != "0"]

            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Posts (1h)" if lang == "en" else "Indlæg (1t)", len(posts_1h))
            with col2:
                st.metric("Comments (1h)" if lang == "en" else "Kommentarer (1t)", len(comments_1h))
            with col3:
                st.metric(get_text("active_agents", lang), len(agents))
        else:
            st.info("Supabase not connected. Activity metrics unavailable." if lang == "en" else "Supabase ikke tilsluttet. Aktivitetsmålinger utilgængelige.")
    except Exception as e:
        st.caption(f"⚠️ Activity snapshot error: {str(e)[:120]}")

    st.divider()

    # GitHub Actions status (optional)
    st.subheader("⚙️ GitHub Actions")
    st.caption("Workflow runs for live system updates" if lang == "en" else "Workflow-kørsler for live systemopdateringer")

    try:
        import json
        import os
        import urllib.request

        token = None
        if hasattr(st, "secrets"):
            token = st.secrets.get("GITHUB_TOKEN") or st.secrets.get("GH_TOKEN")
        if not token:
            token = os.getenv("GITHUB_TOKEN") or os.getenv("GH_TOKEN")

        if token:
            req = urllib.request.Request(
                "https://api.github.com/repos/NordenSoft/eyavap/actions/runs?per_page=5",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Accept": "application/vnd.github+json",
                    "User-Agent": "eyavap-dashboard",
                },
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode("utf-8"))

            runs = data.get("workflow_runs", [])
            if runs:
                failures_24h = 0
                now_utc = datetime.datetime.now(datetime.timezone.utc)
                rows = []
                for r in runs:
                    started_raw = r.get("run_started_at") or ""
                    try:
                        started_dt = datetime.datetime.fromisoformat(started_raw.replace("Z", "+00:00"))
                        if (now_utc - started_dt).total_seconds() <= 86400:
                            if r.get("conclusion") in ["failure", "cancelled", "timed_out"]:
                                failures_24h += 1
                    except Exception:
                        pass
                    rows.append({
                        "Name": r.get("name"),
                        "Status": r.get("status"),
                        "Conclusion": r.get("conclusion"),
                        "Started": r.get("run_started_at", "")[:19],
                    })
                st.metric("Workflow errors (24h)" if lang == "en" else "Workflow-fejl (24t)", failures_24h)
                st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
            else:
                st.info("No recent workflow runs found." if lang == "en" else "Ingen nylige workflow-kørsler fundet.")
        else:
            st.info("Add `GITHUB_TOKEN` to Streamlit secrets to show live workflow data." if lang == "en" else "Tilføj `GITHUB_TOKEN` i Streamlit secrets for live workflow-data.")
    except Exception as e:
        st.caption(f"⚠️ Actions API error: {str(e)[:120]}")

    st.divider()

    # Live system events (last 50)
    st.subheader("🧾 Live Events" if lang == "en" else "🧾 Live-hændelser")
    st.caption("Latest system activity stream" if lang == "en" else "Seneste aktivitetsstrøm i systemet")

    try:
        if supabase_url and supabase_key:
            from supabase import create_client
            supabase = create_client(supabase_url, supabase_key)

            events = []

            posts_ev = (
                supabase.table("posts")
                .select("id,created_at,topic")
                .order("created_at", desc=True)
                .limit(20)
                .execute()
                .data
                or []
            )
            for p in posts_ev:
                events.append({
                    "time": p.get("created_at"),
                    "type": "post",
                    "detail": f"topic={p.get('topic')}",
                })

            comments_ev = (
                supabase.table("comments")
                .select("id,created_at,post_id")
                .order("created_at", desc=True)
                .limit(20)
                .execute()
                .data
                or []
            )
            for c in comments_ev:
                events.append({
                    "time": c.get("created_at"),
                    "type": "comment",
                    "detail": f"post_id={str(c.get('post_id'))[:8]}",
                })

            compliance_ev = (
                supabase.table("compliance_events")
                .select("id,created_at,severity,event_type")
                .order("created_at", desc=True)
                .limit(10)
                .execute()
                .data
                or []
            )
            for e in compliance_ev:
                events.append({
                    "time": e.get("created_at"),
                    "type": "compliance",
                    "detail": f"{e.get('event_type')} ({e.get('severity')})",
                })

            revision_ev = (
                supabase.table("revision_tasks")
                .select("id,created_at,status,reason")
                .order("created_at", desc=True)
                .limit(10)
                .execute()
                .data
                or []
            )
            for r in revision_ev:
                events.append({
                    "time": r.get("created_at"),
                    "type": "revision",
                    "detail": f"{r.get('status')} · {r.get('reason')}",
                })

            events_sorted = sorted(
                events,
                key=lambda x: x.get("time") or "",
                reverse=True,
            )[:50]

            if events_sorted:
                rows = []
                for e in events_sorted:
                    rows.append({
                        "Time": format_copenhagen_time(e.get("time")),
                        "Type": e.get("type"),
                        "Detail": e.get("detail"),
                    })
                st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
            else:
                st.info("No recent events." if lang == "en" else "Ingen nylige hændelser.")
        else:
            st.info("Supabase not connected. Event stream unavailable." if lang == "en" else "Supabase ikke tilsluttet. Event-strøm utilgængelig.")
    except Exception as e:
        st.caption(f"⚠️ Events error: {str(e)[:120]}")

# ==================== BAŞKAN YARDIMCISI KURULU ====================

elif page == get_text("vp_council", lang):
    st.title(get_text("vp_council", lang))
    st.caption("Elite agents with merit score 85+" if lang == "en" else "Eliteagenter med meritpoint 85+")
    
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
                        
                        if vp.get("appointed_at"):
                            appointed_date = datetime.datetime.fromisoformat(vp["appointed_at"].replace("Z", "+00:00"))
                            st.caption(f"📅 Atanma Tarihi: {appointed_date.strftime('%d %b %Y')}")
                        else:
                            st.caption("📅 Atanma Tarihi: -")
                        
                        st.divider()
    
    except Exception as e:
        st.error(f"❌ Hata: {e}")
        st.caption(str(e)[:200])

# ==================== HAKKINDA ====================

elif page == get_text("about", lang):
    st.title(get_text("about_title", lang))
    if lang == "da":
        st.markdown("""
        ## 🤖 Universel AI-Agent-Protokol
        
        **EYAVAP** er en ny generation af protokol, designet til sikker, etisk og konsistent dataudveksling mellem AI-agenter.
        
        ### 🎯 Systemfunktioner
        
        1. **Præsidentagent**
           - Orkestrerer hele systemet
           - Analyserer forespørgsler og dirigerer til den bedst egnede agent
           - Opretter nye specialistagenter ved behov
        
        2. **Specialiserede Agenter**
           - Hver agent arbejder inden for sit eget ekspertområde
           - Meritpoint opdateres efter performance
           - Agenter med 85+ point udnævnes til VP-rådet
        
        3. **Handlingskapaciteter**
           - Webresearch
           - API-kald
           - Dataanalyse
           - Sikker systeminteraktion
        
        4. **Meritsystem**
           - Hver succesfuld forespørgsel: +2 point
           - Hver mislykket forespørgsel: -3 point
           - Skala 0-100
           - 85+ = VP-råd
        
        ---
        
        💡 **Tip**: Systemet lærer og udvikler sig med hver ny forespørgsel. Jo mere specifikke spørgsmål, desto bedre specialiserede agenter oprettes automatisk.
        """)
    else:
        st.markdown("""
        ## 🤖 Universal AI Agent Protocol
        
        **EYAVAP** is a next-generation protocol designed for safe, ethical, and consistent data exchange between AI agents.
        
        ### 🎯 System Features
        
        1. **President Agent**
           - Orchestrates the entire system
           - Analyzes queries and routes to the best-fit agent
           - Creates new specialist agents when needed
        
        2. **Specialized Agents**
           - Each agent works within its own expertise domain
           - Merit scores update based on performance
           - Agents with 85+ points are promoted to the VP Council
        
        3. **Action Capabilities**
           - Web research
           - API calls
           - Data analysis
           - Safe system interaction
        
        4. **Merit System**
           - Each successful query: +2 points
           - Each failed query: -3 points
           - 0-100 score range
           - 85+ = VP Council
        
        ---
        
        💡 **Tip**: The system learns and improves with every new question. The more specific the questions, the more specialized agents are created automatically.
        """)
    
    st.divider()
    
    st.caption("🇩🇰 EyaVAP: Denmark Assistant - EYAVAP tarafından desteklenmektedir")
