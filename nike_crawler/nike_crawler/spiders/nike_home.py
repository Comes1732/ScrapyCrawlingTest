import scrapy
import json
from datetime import datetime

"""
仅采集单页静态数据，无需多页面.多字段的统一数据结构；
仅需本地保存 JSON 文件，无需数据库存储、数据清洗等后续处理；
未涉及复杂反爬（如代理、Cookie 池），Scrapy 默认中间件已满足基础请求需求
"""
class NikeHomeSpider(scrapy.Spider):
    name = 'nike_home'
    allowed_domains = ['nike.com.cn']
    start_urls = ['https://www.nike.com.cn/']

    def parse(self, response):
        """全解析逻辑：从HTML中提取所有核心数据，无手动补充"""
        nike_data = {
            "crawl_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),  # 本地爬取时间（精确到分）
            "activity_info": self._parse_activities(response),  # 解析活动信息
            "product_info": self._parse_products(response),      # 解析产品信息
            "series_info": self._parse_series(response),        # 解析系列信息
            "page_meta": self._parse_page_meta(response)        # 解析页面元信息（可选，用于验证）
        }

        # 本地保存JSON（仅触发一次，保存全量解析数据）
        with open('nike_home_full_parsed.json', 'w', encoding='utf-8') as f:
            json.dump(nike_data, f, ensure_ascii=False, indent=4)
        self.logger.info(f"全解析数据已保存，共提取：活动{len(nike_data['activity_info'])}个，产品{len(nike_data['product_info'])}个，系列{len(nike_data['series_info'])}个")

    def _parse_activities(self, response):
        """子方法：解析活动信息（如专场、福利、限时活动）"""
        activities = []
        # 选择器逻辑：匹配包含"活动/专场/福利/限时"等关键词的容器（常见电商活动标签）
        activity_containers = response.xpath(
            '//div[contains(@class, "promo") or contains(@class, "activity") or contains(@class, "special")] | '
            '//section[contains(text(), "专场") or contains(text(), "福利") or contains(text(), "限时")]'
        )

        for container in activity_containers:
            # 提取活动核心字段（基于容器内常见子标签：标题h2/h3、描述p、时间span、折扣标签）
            activity = {
                "activity_theme": container.xpath('.//h2/text() | .//h3/text() | .//div[contains(@class, "title")]/text()').extract_first(default="").strip(),
                "activity_discount": container.xpath(
                    './/span[contains(text(), "折") or contains(text(), "低至") or contains(text(), "满减") or contains(text(), "限时价")]/text()'
                ).extract_first(default="").strip(),
                "activity_time": container.xpath(
                    './/span[contains(@class, "time") or contains(text(), "至") or contains(text(), "开始")]/text()'
                ).extract_first(default="").strip(),
                "activity_desc": container.xpath('.//p/text() | .//div[contains(@class, "desc")]/text()').extract_first(default="").strip(),
                "activity_link": response.urljoin(  # 拼接相对链接为绝对URL
                    container.xpath('.//a/@href').extract_first(default="")
                )
            }
            # 过滤空数据：至少包含主题或折扣才保留
            if activity["activity_theme"] or activity["activity_discount"]:
                activities.append(activity)
        return activities

    def _parse_products(self, response):
        """子方法：解析产品信息（鞋款、装备等，基于商品卡片布局）"""
        products = []
        # 选择器逻辑：匹配商品卡片容器（常见类名：product-item、goods-card、item-box）
        product_cards = response.xpath(
            '//div[contains(@class, "product-item") or contains(@class, "goods-card") or contains(@class, "item-box")] | '
            '//li[contains(@class, "product") or contains(@class, "goods")]'
        )

        for card in product_cards:
            # 提取产品核心字段（商品卡片标准结构：名称、价格、卖点、图片、链接）
            product = {
                "product_name": card.xpath(
                    './/span[contains(@class, "product-name") or contains(@class, "goods-name")]/text() | '
                    './/h3[contains(@class, "name")]/text()'
                ).extract_first(default="").strip(),
                "product_price": card.xpath(
                    './/span[contains(@class, "price") or contains(@class, "current-price")]/text() | '
                    './/div[contains(@class, "price")]/text()'
                ).extract_first(default="").strip(),
                "product_selling_point": card.xpath(
                    './/p[contains(@class, "selling-point") or contains(@class, "feature")]/text() | '
                    './/div[contains(@class, "desc") and not(contains(@class, "price"))]/text()'
                ).extract_first(default="").strip(),
                "product_image": response.urljoin(  # 商品主图URL
                    card.xpath('.//img[contains(@class, "product-img") or contains(@class, "goods-img")]/@src').extract_first(default="")
                ),
                "product_link": response.urljoin(  # 商品详情页链接
                    card.xpath('.//a[contains(@class, "product-link") or @href]/@href').extract_first(default="")
                ),
                "product_category": card.xpath(  # 商品分类（如"跑鞋"、"篮球鞋"）
                    './/span[contains(@class, "category") or contains(@class, "type")]/text()'
                ).extract_first(default="").strip()
            }
            # 过滤空数据：至少包含产品名称才保留（避免无效卡片）
            if product["product_name"]:
                products.append(product)
        return products

    def _parse_series(self, response):
        """子方法：解析系列信息（如DUNK、AIR FORCE 1等专属系列）"""
        series = []
        # 选择器逻辑：匹配系列专区容器（常见类名：series、collection、theme-section）
        series_containers = response.xpath(
            '//div[contains(@class, "series") or contains(@class, "collection") or contains(@class, "theme-section")] | '
            '//section[contains(text(), "系列") or contains(text(), "合集")]'
        )

        for container in series_containers:
            # 提取系列核心字段（系列名称、定位、包含产品数、链接）
            series_name = container.xpath(
                './/h2/text() | .//h3/text() | .//div[contains(@class, "series-name")]/text()'
            ).extract_first(default="").strip()
            # 若系列名称包含已知系列关键词（如DUNK、AIR FORCE），优先保留
            if any(keyword in series_name for keyword in ["DUNK", "AIR FORCE", "ZOOM", "SHox", "ACG", "儿童"]):
                series.append({
                    "series_name": series_name,
                    "series_positioning": container.xpath(
                        './/p[contains(@class, "positioning") or contains(@class, "intro")]/text() | '
                        './/div[contains(@class, "desc")]/text()'
                    ).extract_first(default="").strip(),
                    "series_product_count": len(container.xpath('.//div[contains(@class, "product-item")]')),  # 系列包含产品数
                    "series_link": response.urljoin(
                        container.xpath('.//a[contains(@class, "series-link")]/@href').extract_first(default="")
                    )
                })
        return series

    def _parse_page_meta(self, response):
        """子方法：解析页面元信息（用于验证爬取有效性）"""
        return {
            "page_title": response.xpath('//title/text()').extract_first(default="").strip(),
            "page_keywords": response.xpath('//meta[@name="keywords"]/@content').extract_first(default="").strip(),
            "page_description": response.xpath('//meta[@name="description"]/@content').extract_first(default="").strip(),
            "response_status": response.status  # 响应状态码（200为成功）
        }