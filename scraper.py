import requests
from bs4 import BeautifulSoup

def skat_kaziyici(url):
    print(f"📡 Hedef taranıyor: {url}")
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    
    # Skat.dk üzerindeki ana metin alanını yakala
    icerik = soup.find('main') # Genellikle ana içerik buradadır
    if icerik:
        return icerik.get_text(separator=' ', strip=True)
    return "İçerik bulunamadı."

# Örnek Hedef: Danimarka Şahıs Vergi Rehberi
url = "https://skat.dk/borger/fradrag/personfradrag"
veri = skat_kaziyici(url)
print("✅ Veri başarıyla çekildi.")