import os
import openai
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

# Bağlantılar
supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_SERVICE_ROLE_KEY"))
ai_client = openai.OpenAI(
    api_key=os.getenv("DEEPINFRA_API_TOKEN"),
    base_url="https://api.deepinfra.com/v1/openai"
)

def eyavap_vergi_uzmani(soru):
    print(f"🔍 EyaVAP hafızasında araştırıyor: {soru}")
    
    # 1. Soruyu vektöre çevir (Arama yapmak için)
    emb_res = ai_client.embeddings.create(
        model="BAAI/bge-large-en-v1.5",
        input=[soru]
    )
    soru_vektoru = emb_res.data[0].embedding

    # 2. Supabase'de en benzer vergi kurallarını bul (Vektör Araması)
    # Not: Supabase'de 'match_documents' RPC fonksiyonu kurulu olmalıdır
    rpc_res = supabase.rpc("match_documents", {
        "query_embedding": soru_vektoru,
        "match_threshold": 0.5,
        "match_count": 3
    }).execute()
    
    baglam = "\n".join([d['icerik'] for d in rpc_res.data])

    # 3. Llama 3.1 405B ile cevabı oluştur
    response = ai_client.chat.completions.create(
        model="NousResearch/Hermes-3-Llama-3.1-405B",
        messages=[
            {"role": "system", "content": "Sen EyaVAP, Danimarka Vergi Uzmanısın. Sadece sana verilen resmi Skat verilerine dayanarak cevap ver. Danca terimleri açıkla."},
            {"role": "user", "content": f"Hafıza Kayıtları:\n{baglam}\n\nSoru: {soru}"}
        ]
    )
    return response.choices[0].message.content

# TEST EDELİM
if __name__ == "__main__":
    cevap = eyavap_vergi_uzmani("Hvad er personfradrag i 2025?")
    print(f"\n🧠 [EYAVAP]: {cevap}")