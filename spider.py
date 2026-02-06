import scrapy
import os
import openai
from scrapy.crawler import CrawlerProcess
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor
from database import veriyi_hafizaya_yaz # Supabase köprümüz

class SkatSpider(CrawlSpider):
    name = "skat_orumcegi"
    allowed_domains = ["skat.dk"]
    start_urls = ["https://skat.dk/borger", "https://skat.dk/erhverv"]

    rules = (
        Rule(LinkExtractor(allow=("/borger/", "/erhverv/")), callback="parse_item", follow=True),
    )

    def generate_embedding(self, text):
        # DeepInfra üzerinden metni vektöre çeviren ajan
        client = openai.OpenAI(
            api_key=os.getenv("DEEPINFRA_API_TOKEN"),
            base_url="https://api.deepinfra.com/v1/openai"
        )
        response = client.embeddings.create(
            model="BAAI/bge-large-en-v1.5", # Hızlı ve keskin vektörleme
            input=[text]
        )
        return response.data[0].embedding

    def parse_item(self, response):
        # Başlığı ve içeriği daha hassas yakalıyoruz
        baslik = response.xpath('//h1/text()').get() or response.css('title::text').get()
        icerik = " ".join(response.css('main p::text, main li::text').getall()).strip()

        if len(icerik) > 200:
            print(f"🧠 HAFIZAYA ALINIYOR: {baslik}")
            vektor = self.generate_embedding(icerik[:2000]) # İlk 2000 karakteri vektörle
            veriyi_hafizaya_yaz(icerik, response.url, vektor) # Supabase'e mühürle

if __name__ == "__main__":
    process = CrawlerProcess({
        'USER_AGENT': 'Mozilla/5.0 (Tora Bot 1.0)',
        'LOG_LEVEL': 'INFO',
        'CLOSESPIDER_PAGECOUNT': 10 # Şimdilik sadece 10 sayfa ile test edelim
    })
    process.crawl(SkatSpider)
    process.start()