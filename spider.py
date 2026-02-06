import scrapy
import os
import openai
from scrapy.crawler import CrawlerProcess
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor
from database import veriyi_hafizaya_yaz
from dotenv import load_dotenv

load_dotenv()

class SkatSpider(CrawlSpider):
    name = "skat_orumcegi"
    allowed_domains = ["skat.dk"]
    start_urls = ["https://skat.dk/borger", "https://skat.dk/erhverv"]

    rules = (
        Rule(LinkExtractor(allow=("/borger/", "/erhverv/")), callback="parse_item", follow=True),
    )

    def generate_embedding(self, text):
        """Metni DeepInfra üzerinden vektöre çevirir"""
        client = openai.OpenAI(
            api_key=os.getenv("DEEPINFRA_API_TOKEN"),
            base_url="https://api.deepinfra.com/v1/openai"
        )
        response = client.embeddings.create(
            model="BAAI/bge-large-en-v1.5",
            input=[text]
        )
        return response.data[0].embedding

    def parse_item(self, response):
        baslik = response.xpath('//h1/text()').get() or response.css('title::text').get()
        # İçeriği temizle ve al
        metin_parcalari = response.css('main p::text, main li::text').getall()
        tam_metin = " ".join([m.strip() for m in metin_parcalari if m.strip()])

        if len(tam_metin) > 300:
            print(f"🧠 ANALİZ EDİLİYOR: {baslik}")
            vektor = self.generate_embedding(tam_metin[:1500]) # İlk 1500 karakter yeterli
            veriyi_hafizaya_yaz(tam_metin, response.url, vektor)

if __name__ == "__main__":
    process = CrawlerProcess({
        'USER_AGENT': 'Mozilla/5.0 (Tora Bot 1.0)',
        'LOG_LEVEL': 'INFO',
        'CLOSESPIDER_PAGECOUNT': 10 # Test için 10 sayfa sınırı
    })
    process.crawl(SkatSpider)
    process.start()