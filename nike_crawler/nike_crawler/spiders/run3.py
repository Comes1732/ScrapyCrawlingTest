# -*- coding: utf-8 -*-
import scrapy
from scrapy.crawler import CrawlerProcess
from scrapy.http import HtmlResponse
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import platform
import time
import random

class SeleniumMiddleware:
    def __init__(self):
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--no-sandbox')  # 建议取消注释
        chrome_options.add_argument('--window-size=1920,1080')
        self.driver = webdriver.Chrome(options=chrome_options)

    def process_request(self, request, spider):
        if request.meta.get('selenium', False):
            wait_time = request.meta.get('wait_time', 5)
            scroll_times = request.meta.get('scroll_times', 0)
            
            try:
                # 打开页面
                self.driver.get(request.url)
                spider.logger.info(f"页面已打开，等待 {wait_time} 秒让数据加载...")
                
                # 等待页面基本加载
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )
                
                # 执行滚动
                if scroll_times > 0:
                    spider.logger.info(f"执行 {scroll_times} 次滚动...")
                    self.scroll_page_multiple(scroll_times)
                    time.sleep(3)
                
                # 额外等待JS数据加载
                time.sleep(wait_time)
                
                # 获取完全渲染后的页面
                body = self.driver.page_source
                
                return HtmlResponse(
                    url=request.url,
                    body=body,
                    encoding='utf-8',
                    request=request
                )
                
            except Exception as e:
                spider.logger.error(f"Selenium错误: {e}")
                return HtmlResponse(url=request.url, status=500)
        
        return None
    
    def scroll_page_multiple(self, times=3):
        """多次滚动页面"""
        for i in range(times):
            try:
                # 滚动到底部
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)
                
                # 随机滚动到中间位置
                scroll_height = self.driver.execute_script("return document.body.scrollHeight")
                if scroll_height > 1000:  # 确保有足够的滚动空间
                    random_position = random.randint(300, scroll_height - 500)
                    self.driver.execute_script(f"window.scrollTo(0, {random_position});")
                    time.sleep(1)
                
            except Exception as e:
                print(f"滚动时出错: {e}")
                break
    
    @classmethod
    def from_crawler(cls, crawler):
        middleware = cls()
        crawler.signals.connect(middleware.spider_closed, signal=scrapy.signals.spider_closed)
        return middleware

    def spider_closed(self):
        if hasattr(self, 'driver'):
            self.driver.quit()

class NikeJsSpider(scrapy.Spider):
    name = "nike_js"
    custom_settings = {
        'DOWNLOADER_MIDDLEWARES': {
            '__main__.SeleniumMiddleware': 543,
        },
        'CONCURRENT_REQUESTS': 1,
        'DOWNLOAD_DELAY': 3,
        'DUPEFILTER_CLASS': 'scrapy.dupefilters.BaseDupeFilter',  # 禁用去重
    }
    
    start_urls = ["https://www.nike.com.cn/w/"]
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.all_links = set()  # 用于存储所有找到的链接
        self.max_scroll_attempts = 4  # 最大滚动次数
        self.current_attempt = 0  # 当前滚动次数
    
    def parse(self, response):
        self.logger.info("开始解析列表页")
        
        # 第一次请求，执行4次滚动
        yield scrapy.Request(
            url=response.url,
            callback=self.parse_after_scroll,
            meta={
                'selenium': True,
                'wait_time': random.randint(3, 6),
                'scroll_times': 4,  # 直接执行4次滚动
                'dont_filter': True
            }
        )
    
    def parse_after_scroll(self, response):
        """滚动后解析页面"""
        self.current_attempt += 1
        self.logger.info(f"第 {self.current_attempt} 次滚动后解析页面")
        
        # 提取当前页面的所有链接
        new_links = self.extract_links(response)
        
        # 添加到总链接集合中
        before_count = len(self.all_links)
        self.all_links.update(new_links)
        after_count = len(self.all_links)
        
        self.logger.info(f"本次找到 {len(new_links)} 个链接，总共 {after_count} 个唯一链接")
        self.logger.info(f"新增 {after_count - before_count} 个新链接")
        
        # 如果已经达到最大滚动次数，开始处理所有链接
        if self.current_attempt >= self.max_scroll_attempts:
            self.logger.info(f"完成所有 {self.max_scroll_attempts} 次滚动，开始处理产品详情页")
            yield from self.process_all_links(response)
        else:
            # 继续下一次滚动
            time.sleep(2)
            yield scrapy.Request(
                url=response.url,
                callback=self.parse_after_scroll,
                meta={
                    'selenium': True,
                    'wait_time': random.randint(3, 6),
                    'scroll_times': 1,  # 每次额外滚动2次
                    'dont_filter': True
                }
            )
    
    def process_all_links(self, response):
        """处理所有收集到的链接"""
        s
        elf.logger.info(f"开始处理 {len(self.all_links)} 个产品链接")
        
        for i, link in enumerate(list(self.all_links)[:50]):
            absolute_url = response.urljoin(link)
            self.logger.info(f"处理第 {i + 1} 个产品: {absolute_url}")
            
            yield scrapy.Request(
                url=absolute_url,
                callback=self.parse_product,
                meta={
                    'selenium': True,
                    'wait_time': random.randint(5, 10),
                    'product_number': i + 1
                },
                dont_filter=True
            )
    
    def extract_links(self, response):
        """提取产品链接"""
        links = response.css("a.product-card__link-overlay::attr(href)").getall()
        # 去重并过滤空值
        return list(set(filter(None, links)))
    
    def parse_product(self, response):
        """解析产品详情页"""
        product_data = {
            "title": response.css("#pdp_product_title::text").get(),
            "price": response.css("#price-container > span::text").get(),
            "color": response.css("ul.css-1vql4bw > li")[-2].css("li::text").get() if len(response.css("ul.css-1vql4bw > li")) >= 2 else None,
            "size": response.css("div.pdp-grid-selector-grid label.u-full-width::text").getall(),
            "sku": response.css("ul.css-1vql4bw > li")[-1].css("li::text").get() if response.css("ul.css-1vql4bw > li") else None,
            "detail": response.css("p.nds-text.css-pxxozx::text").get(),
            "img_url": response.css("div.css-1wg28dk img::attr(src)").getall(),
            "url": response.url
        }
        
        self.logger.info(f"产品解析完成: {product_data.get('title')}")
        yield product_data


if __name__ == "__main__":
    process = CrawlerProcess(settings={
        'TELNETCONSOLE_ENABLED': False,
        'FEEDS': {
            'output.json': {
                'format': 'json',
                'encoding': 'utf8',
                'ensure_ascii': False,
                'indent': 4,
                'overwrite': True,  # 覆盖已存在的文件
            }
        },
        'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'LOG_LEVEL': 'INFO',  # 设置日志级别
    })
    process.crawl(NikeJsSpider)
    process.start()
    