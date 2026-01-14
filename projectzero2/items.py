from scrapy import Item, Field


class MiItem(Item):
    url = Field()
    titulo = Field()
    precio = Field()
    stock = Field()
    raw = Field()
