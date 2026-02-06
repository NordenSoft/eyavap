import scrapy
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor

# database.py dosyasını şimdilik opsiyonel yapıyoruz ki test sürüşünde hata vermesin
try:
    from database import veriyi_hafizaya_yaz
except ImportError:
    def veriyi_hafizaya_yaz(m, u, v): pass

class SkatSpider(CrawlSpider):
    name = "skat_orumcegi" # Bu isim Scrapy için kimliktir
    allowed_domains = ["skat.dk"]
    start_urls = [
        "https://skat.dk/borger",
        "https://skat.dk/erhverv"
    ]

    rules = (
        Rule(LinkExtractor(allow=("/borger/", "/erhverv/")), callback="parse_item", follow=True),
    )

    def parse_item(self, response):
        baslik = response.css('h1::text').get()
        # Ana metni daha geniş bir yelpazede yakalıyoruz
        metin_parcalari = response.css('main p::text, main h2::text, main li::text, main div::text').getall()
        tam_metin = " ".join([m.strip() for m in metin_parcalari if m.strip()])

        if len(tam_metin) > 100:
            print(f"🚀 TORA YAKALADI: {baslik} ({response.url})")
            # İleride buraya vektörleme gelecek
            
        return {'url': response.url, 'title': baslik}