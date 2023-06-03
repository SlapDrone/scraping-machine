import typing as ty

import scrapy
from scrapy.linkextractors import LinkExtractor
from scrapy.loader import ItemLoader
from scrapy.spiders import CrawlSpider, Rule
from scrapy_splash import SplashRequest

from scraper.items import ConferenceItem, NeurIPSLoaderItem
from scraper import models


# lua script for splash to expand abstract
expand_abstract_lua = ("""
function main(splash, args)
  splash.private_mode_enabled = false
  -- splash:set_user_agent("{user_agent}")
  url = args.url
  assert(splash:go(url))
  assert(splash:wait({splash_wait_time}))
  reveal_abstract = assert(splash:select(
  	".card-link"
  ))
  reveal_abstract:mouse_click()
  assert(splash:wait({splash_wait_time}))
  splash:set_viewport_full()
  return splash:html()
end
""")

# obtain links to each individual event
open_event = Rule(
    LinkExtractor(restrict_xpaths="//tr[contains(@class, 'search_result_tr')]/td[3]/a"),
    callback="parse_event",
    follow=True,
    process_request="set_user_agent"
)

# obtain link to next page
next_page = Rule(
    LinkExtractor(restrict_xpaths="//div[@class='pager']/span/a[3]"),
    follow=True,
    process_request="set_user_agent"
)

# if prompted to login, navigate to login page
go_to_login_page = Rule(
    LinkExtractor(restrict_xpaths="//a[contains(text(), 'logged in')][position() = 1]"),
    follow=True,
    process_request="set_user_agent"
)

class NeurIPS2022CrawlerSpider(CrawlSpider):
    name: str = 'neurips_2022_crawler'
    conference: str = "NeurIPS"
    year: int = 2022
    allowed_domains: ty.List[str] = ['neurips.cc']
    start_urls: ty.List[str] = [
        "https://neurips.cc/virtual/2022/search"
    ]

    # spoof a regular browser
    user_agent = ('Mozilla/5.0 (X11; Linux x86_64; rv:74.0) '
                  'Gecko/20100101 Firefox/74.0')
    splash_wait_time = 8.0
    rules = (
        open_event,
        next_page
    )

    # counter-anti-scraping: ensure headers always imply normal browser usage
    def start_requests(self):
        for s in self.start_urls:
            yield scrapy.Request(url=s, headers={'User-Agent':self.user_agent})

    def set_user_agent(self, request, response):
        request.headers['User-Agent'] = self.user_agent
        return request

    def parse_event(self, response):
        self.logger.info("Expanding abstract")
        resp = SplashRequest(
            url=response.url,
            endpoint="execute",
            args={
                "lua_source":expand_abstract_lua.format(user_agent=self.user_agent, splash_wait_time=self.splash_wait_time),
                "wait":2
            },
            callback=self.extract_item
        )
        yield resp

    def extract_item(self, response):
        self.logger.info("Extracting item")
        item = NeurIPSLoaderItem()
        loader = ItemLoader(item=item,
                            response=response)
        header = "//div[@class='card-header']"
        loader.add_value("url", response.url)
        # poster and slides are relative URLs
        poster_url = response.xpath("//a[contains(@class, 'href_Poster')]/@href").get()
        slides_url = response.xpath("//a[contains(@class, 'href_PDF') and contains(@title, 'Slides')]/@href").get()
        loader.add_value("poster_url", response.urljoin(poster_url))
        loader.add_value("slides_url", response.urljoin(slides_url))
        loader.add_xpath("paper_url", "//a[contains(@class, 'href_PDF') and contains(@title, 'Paper')]/@href")
        loader.add_xpath("openreview_url", "//a[contains(@class, 'href_URL') and contains(@title, 'OpenReview')]/@href")
        loader.add_value("conference", self.conference)
        loader.add_value("year", self.year)
        loader.add_xpath("item_type", f"{header}/h3[1]/text()")
        loader.add_xpath("title", f"{header}/h2[contains(@class, 'card-title')]/text()")
        loader.add_xpath("abstract", "//div[@id='abstractExample']/p/text()")
        loader.add_xpath("authors", f"{header}/h3[contains(@class, 'card-subtitle')]/text()")
        loader.add_xpath("keywords", f"{header}/p/a/text()")
        item = loader.load_item()
        yield item