# import scrapy
# import json
# # need to find out what's happend
# import re


# class PchomeSpider(scrapy.Spider):
#     # only put these things, not loop
#     name = "pchome"
#     # why list? because scrapy can handle more than just one web
#     # This is Domain
#     allowed_domains = ["ecshweb.pchome.com.tw"]
#     start_urls = ["https://ecshweb.pchome.com.tw/search/v4.3/all/results?q=Mac&page=1&pageCount=40"]
#     def parse(self, response):
#         try:
#             # as always use json.loads to read what come back, means(response.text)
#             data = json.loads(response.text)
#             # watch this 'https://ecshweb.pchome.com.tw/search/v4.3/all/results?q=Mac&page=2&pageCount=40'
#             products = data.get('Prods', [])
#             # use print to find out what's going on
#             print(f"This page got {len(products)} stuff")
#             # use loop to get what i want
#             for product in products:
#                 item = {}
#                 item['products_id'] = product['Id']
#                 item['name'] = product['Name']
#                 item['describe'] = product['Describe']
#                 item['price'] = product['Price']
#                 item['original_price'] = product['OriginPrice']
#                 item['message'] = product['reviewCount']
#                 item['rating'] = product['ratingValue']
#                 # in case crash
#                 if product.get('PicS'):
#                     item['image_url'] = 'https://cs-a.ecimg.tw' + product['PicS']
#                 else:
#                     item['image_url'] = None
#                 # send the package out
#                 yield item
#             # now we have to find out what's happend, so use a new way
#             current_url = response.url
#             # let url himself told us which page right now
#             match = re.search(r'page=(\d+)', current_url)
#                 # re's group(1)means we're find page=(\d+), and (\d+) is our (1)
#                 # here's an example, 2026-01-12 and use (\d+)-(\d+)-(\d+) (年-月-日)
#                 # group(0) -> "2026-01-12" , group(1) -> "2026"
#                 # group(2) -> "01" , group(3) -> "12"
#             if match:
#                 current_page = int(match.group(1))
#             else:
#                 current_page = 1
#             # current_page = data.get('Page', 1)
#             # # let us find out how many page Pchome they have
#             total_page = data.get('TotalPage', '?')

#             # let's see where we stuck
#             print('-----------------------------------------')
#             print(f"now on {current_page} page, there's total {total_page} page")
#             print('-----------------------------------------')
#             # i don't want so many garbage, so only got 10 page before
#             if current_page < 10:
#                 next_page = current_page + 1
#                 next_url = f'https://ecshweb.pchome.com.tw/search/v4.3/all/results?q=Mac&page={next_page}&pageCount=40'
#                 # let's see is it work or not work
#                 print('-----------------------------------------')
#                 print(f"ready for next page : {next_page} page")
#                 print('-----------------------------------------')
#                 # tell program don't stop working, let me finish thousand of stuff
#                 yield scrapy.Request(url=next_url, callback=self.parse)
#             else:
#                 print(f"finish")
#         except Exception as e:
#             print(f"發生錯誤 : {e}")

import scrapy
import json
import datetime

class PchomeSpider(scrapy.Spider):
    #give this spider a name
    name = 'pchome'
    allowed_domains = ['ecshweb.pchome.com.tw']
    # Cause dict's key is unqiue value, so have to use list 
    target = [
        {'id': 'DYAJ', 'name': 'Apple'},
        {'id': 'DAAO', 'name': '衛生紙'},
        {'id': 'DGBJ', 'name': '遊戲機'},
        {'id': 'DAAK', 'name': '洗衣精'},
        {'id': 'DAAL', 'name': '嘴巴清潔'},
        {'id': 'DAAZ', 'name': '家用清潔'},
        {'id': 'DAAA', 'name': '洗髮精'},
        {'id': 'DAAJ', 'name': '沐浴乳'},
        {'id': 'DAAT', 'name': '濕紙巾'}
    ]
    # start_requests is set up, can't change this name
    def start_requests(self):
        for con in self.target:
            cate_id = con['id']
            cate_name = con['name']
            url = f"https://ecshweb.pchome.com.tw/search/v4.3/all/results?cateid={cate_id}&page=1&pageCount=40"
            self.logger.info(f"let's get start, now is {cate_name}")
            # return page
            yield scrapy.Request(
                url=url,
                callback=self.parse,
                meta={
                'cate_id': cate_id,
                'cate_name': cate_name,
                'page': 1
                }
            )
    def parse(self, response):
        try:
            cate_name = response.meta['cate_name']
            cate_id = response.meta['cate_id']
            current_page = response.meta['page']
            data = json.loads(response.text)
            products = data.get('Prods', [])
            total_page = data.get('TotalPage', 1)
            for product in products:
                item = {}
                item['category'] = cate_name
                item['product_id'] = product.get('Id', 'X')
                item['name'] = product.get('Name', 'X')
                item['describe'] = product.get('Describe', 'X')
                #before go DB, trans number to int, before trouble coming for us
                item['price'] = int(product.get('Price', 0))
                item['original_price'] = int(product.get('OriginPrice', 0))
                have_image = product.get('PicS')
                if have_image:
                    item['img_url'] = 'https://cs-a.ecimg.tw' + have_image
                else:
                    item['img_url'] = 'X'
                item['rating'] = product.get('ratingValue', '0')
                item['comment'] = product.get('reviewCount', '0')
                item['crawled_at'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                yield item
            self.logger.info(f"working")
            if current_page < total_page and current_page < 11:
                next_page = current_page + 1
                next_url = f"https://ecshweb.pchome.com.tw/search/v4.3/all/results?cateid={cate_id}&page={next_page}&pageCount=40"
                yield scrapy.Request(
                    url=next_url,
                    callback=self.parse,
                    meta={
                        'cate_id': cate_id,
                        'cate_name': cate_name,
                        'page': next_page
                    }
                )
                self.logger.info(f"now is {cate_name},{current_page} page")
            elif current_page >= total_page:
                self.logger.info(f"finish")
        except Exception as e:
            self.logger.info(f"reason : {e}")
