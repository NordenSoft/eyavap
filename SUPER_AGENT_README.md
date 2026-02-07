# 🚀 EYAVAP Super Agent Engine

## Tüm Framework'lerin En İyi Özelliklerini Birleştiren Hibrit AI Agent Sistemi

Bu motor, dünya çapında popüler olan tüm AI agent framework'lerinin en güçlü özelliklerini tek bir sistemde birleştirir:

### 🧠 Framework Kombinasyonu

| Framework | Entegre Edilen Özellik | Kullanım Alanı |
|-----------|------------------------|----------------|
| **ReAct** | Think → Act → Observe döngüsü | Şeffaf reasoning, adım adım düşünme |
| **AutoGPT** | Görev ayrıştırma, hafıza, iteratif iyileştirme | Kompleks hedefleri alt görevlere bölme |
| **BabyAGI** | Görev önceliklendirme, vektör hafızası | Dinamik görev sıralama ve yönetim |
| **CrewAI** | Rol-bazlı işbirliği, delegasyon | Uzman ajanların koordinasyonu |
| **AutoGen** | Multi-agent sohbet, kod yürütme | Ajanlar arası iletişim ve işbirliği |
| **LangGraph** | Durum grafikleri, checkpoint sistemi | İlerleme kaydetme, geri dönüş |

---

## 📋 Temel Konseptler

### 1. Mission (Görev)
Yüksek seviye hedef. Örnek: *"Danimarka'daki iklim değişikliği politikalarını analiz et"*

### 2. Task (Alt Görev)
Mission'ın parçalanmış hali. Öncelik sırasına göre execute edilir.

### 3. Agent Role (Ajan Rolü)
Her ajan bir uzmanlık alanına sahip:
- **Researcher**: Veri toplama, araştırma
- **Analyzer**: Veri analizi, pattern tespiti
- **Implementer**: Çözüm uygulama, içerik üretimi
- **Reviewer**: Kalite kontrol
- **Coordinator**: Ekip koordinasyonu

### 4. ReAct Loop (Düşünme-Aksiyon-Gözlem)
Her task şu döngü ile execute edilir:
```
THINK → "Sırada ne yapmam lazım?"
ACT   → "Araştırma yapacağım"
OBSERVE → "5 kaynak buldum"
THINK → "Şimdi analiz edebilirim"
...
```

### 5. Collaboration (İşbirliği)
Ajanlar birbirinden yardım isteyebilir (AutoGen tarzı).

### 6. Checkpoint (Kontrol Noktası)
Her adımda ilerleme kaydedilir, hata durumunda geri dönülebilir.

---

## 🎯 Kullanım

### 1. Python Script İçinden

```python
from super_agent_engine import execute_mission

result = execute_mission(
    objective="Analyser de vigtigste politiske emner i Danmark denne uge",
    context={"timeframe": "7 days", "focus": "politik"}
)

print(result)
```

### 2. CLI Kullanımı

```bash
# Yeni mission başlat (tam tracking)
python super_agent_cli.py mission "Analyser klimaforandringer i Danmark"

# Hızlı one-shot mission
python super_agent_cli.py quick "Find de bedste AI-artikler denne uge"

# Mission durumunu görüntüle
python super_agent_cli.py status abc123def456

# Yardım
python super_agent_cli.py help
```

### 3. GitHub Actions (Otomatik)

Workflow her gün saat 06:00'da otomatik çalışır:
- `.github/workflows/super_agent_missions.yml`

Manuel tetikleme:
```bash
gh workflow run super_agent_missions.yml -f mission_objective="Din hedef buraya"
```

### 4. Dashboard Monitörü

Dashboard → Monitoring sayfası → "🚀 Super Agent Missions" paneli

---

## 🏗️ Mimari

```
┌─────────────────────────────────────────────────────┐
│                   MISSION                            │
│  "Analyser klimaforandringer i Danmark"             │
└─────────────────┬───────────────────────────────────┘
                  │
                  │ (AutoGPT: Goal Decomposition)
                  ▼
┌─────────────────────────────────────────────────────┐
│                    TASKS                             │
│  1. Indsaml data (Priority: 10)                     │
│  2. Analyser trends (Priority: 8)                   │
│  3. Lav rapport (Priority: 5)                       │
└─────────────────┬───────────────────────────────────┘
                  │
                  │ (BabyAGI: Prioritization)
                  ▼
┌─────────────────────────────────────────────────────┐
│               AGENT ASSIGNMENT                       │
│  Task 1 → Agent #42 (Researcher)                    │
│  Task 2 → Agent #89 (Analyzer)                      │
│  Task 3 → Agent #156 (Implementer)                  │
└─────────────────┬───────────────────────────────────┘
                  │
                  │ (CrewAI: Role Matching)
                  ▼
┌─────────────────────────────────────────────────────┐
│                REACT EXECUTION                       │
│  Agent #42:                                          │
│   THINK: "Jeg skal finde klimadata"                 │
│   ACT: research("klimadata")                         │
│   OBSERVE: "Fandt 5 kilder"                          │
│   THINK: "Tilstrækkeligt, go to next"               │
│   CHECKPOINT ✓                                       │
└─────────────────┬───────────────────────────────────┘
                  │
                  │ (ReAct Loop + LangGraph Checkpoint)
                  ▼
┌─────────────────────────────────────────────────────┐
│              COLLABORATION                           │
│  Agent #89 → "Agent #42, kan du dele dine kilder?"  │
│  Agent #42 → "Ja, her er de: [...]"                 │
└─────────────────┬───────────────────────────────────┘
                  │
                  │ (AutoGen: Multi-agent Chat)
                  ▼
┌─────────────────────────────────────────────────────┐
│                   RESULT                             │
│  Status: completed                                   │
│  Tasks: 3/3 completed                                │
│  Output: [final_analysis.json]                      │
└─────────────────────────────────────────────────────┘
```

---

## 🔍 Özellik Detayları

### ReAct: Reasoning + Acting
```python
task.add_reasoning("Jeg skal finde data om emissioner")
task.add_action({"action": "research", "details": "CO2 emissioner Danmark"})
task.add_observation("Fundet 5 relevante artikler fra 2024")
task.save_checkpoint()  # LangGraph checkpoint
```

### AutoGPT: Goal Decomposition
AI otomatik olarak yüksek seviye hedefi alt görevlere böler:
```
"Analyser klimaforandringer" →
  1. Indsaml data
  2. Identificer trends
  3. Sammenlign med EU-gennemsnit
  4. Lav konklusion
```

### BabyAGI: Task Prioritization
Görevler dinamik olarak önceliklendirilir:
```python
Task(priority=10, dependencies=[])        # Önce bu
Task(priority=8, dependencies=["task_1"]) # Sonra bu
Task(priority=5, dependencies=["task_2"]) # En son bu
```

### CrewAI: Role-based Collaboration
Her ajan bir rol alır ve görevler role göre atanır:
```python
agent.role = AgentRole.RESEARCHER
if task.type == "research":
    assign_to(agent)
```

### AutoGen: Multi-agent Chat
Ajanlar birbirinden yardım isteyebilir:
```python
engine.request_collaboration(
    mission_id="abc123",
    requester_id="agent_42",
    request="Jeg har brug for data om vindenergi"
)
```

### LangGraph: Checkpointing
Her adımda ilerleme kaydedilir:
```python
task.save_checkpoint()
# Daha sonra geri dönülebilir veya devam edilebilir
```

---

## 📊 Database Schema

Super Agent Engine şu tablolara yazıyor:

### `ai_activity_log`
```sql
task_name: "mission_created" | "mission_execution"
task_type: "super_agent"
status: "active" | "completed" | "failed"
result: JSON (mission_id, tasks_completed, total_tasks)
```

---

## 🎨 Dashboard Görünümü

Monitoring sayfasında yeni panel:

```
🚀 Super Agent Missions
ReAct+AutoGPT+BabyAGI+CrewAI+AutoGen+LangGraph hybrid engine

✅ mission_execution · abc123de · 2026-02-06 15:30
    Objective: Analyser de vigtigste politiske emner i Danmark denne uge
    Tasks Completed: 5/5
    Status: completed
```

---

## 🧪 Örnek Kullanım Senaryoları

### 1. Politik Analiz
```bash
python super_agent_cli.py quick "Analyser de 3 vigtigste politiske debatter i Danmark denne uge"
```

### 2. Ekonomi Araştırması
```bash
python super_agent_cli.py mission "Sammenlign Danmarks økonomiske vækst med andre nordiske lande"
```

### 3. Teknoloji Trend Analizi
```bash
python super_agent_cli.py quick "Hvad er de mest diskuterede AI-teknologier i Danmark?"
```

### 4. İklim Değişikliği
```bash
python super_agent_cli.py mission "Evaluer Danmarks klimamål for 2030 baseret på nuværende data"
```

---

## ⚙️ Konfigürasyon

### Environment Variables
```bash
OPENAI_API_KEY=sk-...
SUPABASE_URL=https://...
SUPABASE_KEY=eyJ...
```

### Workflow Schedule
```yaml
# .github/workflows/super_agent_missions.yml
schedule:
  - cron: "0 6 * * *"  # Her gün 06:00
```

---

## 🎯 Avantajlar

| Özellik | Avantaj |
|---------|---------|
| **ReAct Loop** | Şeffaf düşünme süreci, debug kolay |
| **Goal Decomposition** | Büyük görevler otomatik bölünür |
| **Prioritization** | En önemli işler önce yapılır |
| **Role Matching** | Doğru uzman doğru göreve |
| **Collaboration** | Ajanlar birlikte çalışır |
| **Checkpointing** | Hata durumunda geri dönüş |
| **999 Agent Power** | Paralel görev yürütme |

---

## 📈 İleri Seviye Kullanım

### Custom Agent Roles
```python
engine = SuperAgentEngine()
engine.agent_roles["agent_999"] = AgentRole.COORDINATOR
```

### Manual Task Creation
```python
mission_id = engine.create_mission("Custom objective")
task = Task(
    id="custom_1",
    goal="Do something specific",
    priority=10
)
engine.missions[mission_id].tasks.append(task)
engine.run_mission(mission_id)
```

### Mission State Inspection
```python
state = engine.get_mission_state(mission_id)
print(f"Completed: {state['tasks']}")
print(f"Reasoning steps: {state['tasks'][0]['reasoning_steps']}")
```

---

## 🔮 Gelecek Geliştirmeler

- [ ] Vektör hafızası (BabyAGI style long-term memory)
- [ ] Gerçek araç entegrasyonu (web scraping, API calls)
- [ ] Multi-mission paralel yürütme
- [ ] Agent performance scoring
- [ ] Collaboration graph visualization
- [ ] ReAct loop trace visualization

---

## 📞 Destek

Bu sistem EYAVAP'ın bir parçasıdır ve tam otomatik çalışır.

**Manuel Trigger**: `gh workflow run super_agent_missions.yml`
**Dashboard**: Monitoring → Super Agent Missions panel
**Logs**: `ai_activity_log` tablosunda

---

**🎉 Artık 999 ajanınız dünyaca ünlü tüm AI agent framework'lerinin birleşmiş gücüyle çalışıyor!**
