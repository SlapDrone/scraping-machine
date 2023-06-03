"""
middlewares.py
"""
# Define here the models for your spider middleware
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/spider-middleware.html

from scrapy import signals

# useful for handling different item types with a single interface
from itemadapter import is_item, ItemAdapter


class ScraperSpiderMiddleware:
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the spider middleware does not modify the
    # passed objects.

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_spider_input(self, response, spider):
        # Called for each response that goes through the spider
        # middleware and into the spider.

        # Should return None or raise an exception.
        return None

    def process_spider_output(self, response, result, spider):
        # Called with the results returned from the Spider, after
        # it has processed the response.

        # Must return an iterable of Request, or item objects.
        for i in result:
            yield i

    def process_spider_exception(self, response, exception, spider):
        # Called when a spider or process_spider_input() method
        # (from other spider middleware) raises an exception.

        # Should return either None or an iterable of Request or item objects.
        pass

    def process_start_requests(self, start_requests, spider):
        # Called with the start requests of the spider, and works
        # similarly to the process_spider_output() method, except
        # that it doesn’t have a response associated.

        # Must return only requests (not items).
        for r in start_requests:
            yield r

    def spider_opened(self, spider):
        spider.logger.info('Spider opened: %s' % spider.name)


class ScraperDownloaderMiddleware:
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the downloader middleware does not modify the
    # passed objects.

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_request(self, request, spider):
        # Called for each request that goes through the downloader
        # middleware.

        # Must either:
        # - return None: continue processing this request
        # - or return a Response object
        # - or return a Request object
        # - or raise IgnoreRequest: process_exception() methods of
        #   installed downloader middleware will be called
        return None

    def process_response(self, request, response, spider):
        # Called with the response returned from the downloader.

        # Must either;
        # - return a Response object
        # - return a Request object
        # - or raise IgnoreRequest
        return response

    def process_exception(self, request, exception, spider):
        # Called when a download handler or a process_request()
        # (from other downloader middleware) raises an exception.

        # Must either:
        # - return None: continue processing this exception
        # - return a Response object: stops process_exception() chain
        # - return a Request object: stops process_exception() chain
        pass

    def spider_opened(self, spider):
        spider.logger.info('Spider opened: %s' % spider.name)


class CustomCookieMiddleware:
    def __init__(self, crawler):
        self.crawler = crawler

    @classmethod
    def from_crawler(cls, crawler):
        middleware = cls(crawler)
        crawler.signals.connect(middleware.spider_opened, signal=signals.spider_opened)
        return middleware

    def spider_opened(self, spider):
        self.cookies = {}

    def process_response(self, request, response, spider):
        # Process cookies from Splash response
        if 'splash' in request.meta:
            splash_cookies = request.meta['splash'].get('cookies')
            if splash_cookies:
                for cookie in splash_cookies:
                    self.cookies[cookie['name']] = cookie['value']

        set_cookie_header = response.headers.getlist('Set-Cookie')
        if set_cookie_header:
            for cookie in set_cookie_header:
                cookie_str = cookie.decode('utf-8')
                key, value = cookie_str.split('=', 1)
                value = value.split(';', 1)[0]
                self.cookies[key] = value

        return response

    def process_request(self, request, spider):
        if self.cookies:
            cookie_str = "; ".join([f"{key}={value}" for key, value in self.cookies.items()])
            request.headers['Cookie'] = cookie_str
            request.headers['User-Agent'] = spider.settings.get('SPLASH_USER_AGENT')
            # Add cookies to Splash requests
            if 'splash' in request.meta:
                request.meta['splash']['args']['cookies'] = cookie_str
                request.meta['splash']['args']['headers'] = {
                    'User-Agent': spider.settings.get('SPLASH_USER_AGENT')
                }

class DebugHeaderMiddleware:
    @classmethod
    def from_crawler(cls, crawler):
        s = cls()
        crawler.signals.connect(s.response_received, signal=signals.response_received)
        return s

    def response_received(self, response, request, spider):
        spider.logger.debug("Request headers: %s", request.headers)
        spider.logger.debug("Response headers: %s", response.headers)

    def process_request(self, request, spider):
        
        if 'splash' in request.meta:
            spider.logger.debug(f"Request URL: {request.meta['splash']['args'].get('url')}")
            spider.logger.debug(f"Request Cookies: {request.meta['splash']['args'].get('cookies')}")
            spider.logger.debug(f"Request User-Agent: {request.meta['splash']['args'].get('headers')}")
        else:
            spider.logger.debug(f"Request Cookies: {request.headers.get('Cookie')}")
            spider.logger.debug(f"Request User-Agent: {request.headers.get('User-Agent')}")


# middlewares.py
class SplashUserAgentMiddleware:
    def __init__(self, user_agent):
        self.user_agent = user_agent

    @classmethod
    def from_crawler(cls, crawler):
        user_agent = crawler.settings.get('SPLASH_USER_AGENT')
        return cls(user_agent)

    def process_request(self, request, spider):
        if 'splash' in request.meta:
            request.meta['splash']['args']['headers'] = {
                'User-Agent': self.user_agent
            }
