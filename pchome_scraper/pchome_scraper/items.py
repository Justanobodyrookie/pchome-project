# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class PchomeScraperItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    products_id = scrapy.Field()
    name = scrapy.Field()
    describe = scrapy.Field()
    price = scrapy.Field()
    original_price = scrapy.Field()
    rating = scrapy.Field()
    comment = scrapy.Field()
    img_url = scrapy.Field()
    pass