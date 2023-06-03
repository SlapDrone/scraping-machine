"""
aaai_crawler.py
"""
import asyncio
import inspect
import json
import os
import re
import typing as ty
from pathlib import Path
from typing import Callable, TypeVar, Any
from functools import wraps
from urllib.parse import urljoin

import playwright._impl
import pydantic
import scrapy
from scrapy_playwright.page import PageMethod
from scrapy.linkextractors import LinkExtractor
from scrapy.loader import ItemLoader
from scrapy.spiders import CrawlSpider, Rule
from scrapy.http import Response
from scrapy import FormRequest
from scrapy.utils.log import configure_logging
from scrapy.selector import Selector

from scraper.items import ConferenceItem, AAAILoaderItem
from scraper import models


configure_logging(settings = None, install_root_handler = True)

T = TypeVar("T", bound=Callable[..., Any])

class AAAISettings(pydantic.BaseModel):
    """
    This conference requires authentication on the platform to get session cookie
    """
    underline_email: pydantic.EmailStr = pydantic.Field(default=os.getenv("UNDERLINE_EMAIL"), env="UNDERLINE_EMAIL")
    underline_password: str = pydantic.Field(default=os.getenv("UNDERLINE_PASSWORD"))
    remember_me: bool = pydantic.Field(default=False, env="UNDERLINE_REMEMBER_ME")


async def wait_idle_then_sleep(page, sleep: float = 3):
    """"""
    await page.wait_for_load_state("networkidle")
    await asyncio.sleep(sleep)


async def click_with_retry(element, logger, retries=3):
    for i in range(retries):
        try:
            logger.debug(f"Click attempt #{i + 1}")
            await element.click()
            logger.debug(f"Click succeeded on attempt #{i + 1}")
            return
        except Exception as e:
            logger.exception(e)
            logger.warning(f"Click failed on attempt #{i + 1}: {str(e)}")
            await asyncio.sleep(1)

    logger.error("Failed to click the element after retries")
    raise Exception("Failed to click the element after retries")


# --
import pandas as pd

def in_csv(url, csv="./scraped.csv"):
    try:
        df = pd.read_csv(csv, index_col=0)
        urls = df.url
        return (urls == url).any()
    except FileNotFoundError:
        return False

def write_to_csv(url, csv="./scraped.csv"):
    if Path(csv).exists():
        df = pd.read_csv(csv, index_col=0)
        urls = pd.concat([df.url, pd.Series([url])])
        urls.name = "url"
    else:
        urls = pd.Series([url], name="url")
    urls.to_csv(csv)

async def async_iterator_with_timeout(async_iter, timeout):
    async def get_next_item(iterator):
        try:
            return await iterator.__anext__()
        except StopAsyncIteration:
            return None

    while True:
        try:
            next_item = await asyncio.wait_for(get_next_item(async_iter), timeout)
            if next_item is None:
                break
            yield next_item
        except asyncio.TimeoutError:
            print("Timeout reached")
            break


class AAAI2023CrawlerSpider(scrapy.Spider):#scrapy.Spider):
    name: str = 'aaai_2023_crawler'
    conference: str = "AAAI"
    custom_settings = {
        'LOG_LEVEL': 'INFO', # can also scrapy crawl aaai_2023_crawler --loglevel=DEBUG
        'DOWNLOADER_MIDDLEWARES': {
            'scraper.middlewares.DebugHeaderMiddleware': 1000,
        },
        'DOWNLOAD_DELAY': 5,
        'CONCURRENT_REQUESTS_PER_DOMAIN':1, 
        'ITEM_PIPELINES' : {
        'scraper.pipelines.AsyncSQLModelItemPipeline': 300,
        }
    }
    year: int = 2023
    allowed_domains: ty.List[str] = ['underline.io']
    start_urls: ty.List[str] = [
        "https://underline.io/log-in?redirectUrl=/events/380/reception"
    ]
    posters_url: str = "https://underline.io/events/380/posters"
    # spoof a regular browser
    #user_agent = ('Mozilla/5.0 (X11; Linux x86_64; rv:74.0) '
    #              'Gecko/20100101 Firefox/74.0')
    # credentials from env vars
    aaai_settings: AAAISettings = AAAISettings()

    async def errback(self, failure):
        self.logger.error(f"Error: {failure}")
        page = failure.request.meta["playwright_page"]
        await page.close()

    def start_requests(self):
        """
        Log in to receive session cookies. Then proceed with scraping
        """
        for url in self.start_urls:
            # login
            self.logger.info(f"Start scraping URL: {url}")
            self.logger.info("Login")
            yield scrapy.Request(
                url,
                callback=self.open_poster_page,
                meta=dict(
                    playwright=True,
                    playwright_include_page=True, # keep page object to work with
                    playwright_page_methods = [
                        PageMethod("wait_for_selector", "button[type=submit]"),#productListing")
                        PageMethod("fill", "input#email", self.aaai_settings.underline_email),
                        PageMethod("fill", "input#password", self.aaai_settings.underline_password),
                        PageMethod("click", "label[for=rememberMe]"),
                        PageMethod("screenshot", path="login.png"),
                        PageMethod("click", "button[type=submit]"),
                        PageMethod("wait_for_load_state", "networkidle"),
                    ],
                    errback=self.errback,
                )
            )
            # yield scrapy.Request(
            #     url,
            #     callback=self.open_session_page,
            #     meta=dict(
            #         playwright=True,
            #         playwright_include_page=True, # keep page object to work with
            #         playwright_page_methods = [
            #             PageMethod("wait_for_selector", "button[type=submit]"),#productListing")
            #             PageMethod("fill", "input#email", self.aaai_settings.underline_email),
            #             PageMethod("fill", "input#password", self.aaai_settings.underline_password),
            #             PageMethod("click", "label[for=rememberMe]"),
            #             PageMethod("screenshot", path="login.png"),
            #             PageMethod("click", "button[type=submit]"),
            #             PageMethod("wait_for_load_state", "networkidle"),
            #         ],
            #         errback=self.errback,
            #     )
            # )


    async def capture_screenshot(self, response):
        page = response.meta["playwright_page"]
        screenshot_name = response.meta.get("screenshot_name", "untitled_screenshot.png")
        if not screenshot_name.endswith(".png"):
            screenshot_name += ".png"
        screenshot_name = Path(screenshot_name)
        ix = 1
        while screenshot_name.exists():
            ix += 1
            if re.match(".*-\d+", screenshot_name.stem):
                stem = screenshot_name.stem.split("-")[0]
            else:
                stem = screenshot_name.stem
            screenshot_name = screenshot_name.parent / (stem + f"-{ix}.png")
        # do stuff like populate item from response html + selectors...
        screenshot = await page.screenshot(path=screenshot_name, full_page=True)
        self.logger.info(f"screenshot captured at: {screenshot_name}")
        await page.close()

    def get_screenshot_name(self, response):
        screenshot_name = response.meta.get("screenshot_name", "untitled_screenshot.png")
        if not screenshot_name.endswith(".png"):
            screenshot_name += ".png"
        screenshot_name = Path(screenshot_name)
        ix = 1
        while screenshot_name.exists():
            ix += 1
            if re.match(".*-\d+", screenshot_name.stem):
                stem = screenshot_name.stem.split("-")[0]
            else:
                stem = screenshot_name.stem
            screenshot_name = screenshot_name.parent / (stem + f"-{ix}.png")
        return screenshot_name

    async def open_poster_page(self, response):
        page = response.meta["playwright_page"]
        # do stuff like populate item from response html + selectors...
        screenshot = await page.screenshot(path="./after_login.png", full_page=True)
        self.logger.info("screenshot captured")
        await page.close()
        # open the page to all posters
        self.logger.info("Open posters page")
        yield scrapy.Request(
            response.url,
            callback=self.open_events,#self.open_events,
            meta=dict(
                playwright=True,
                playwright_include_page=True, # keep page object to work with
                playwright_page_methods = [
                    PageMethod("wait_for_selector", "a[href='/events/380/posters']"),#productListing")
                    PageMethod("click", "a[href='/events/380/posters']"),
                    PageMethod("wait_for_load_state", "networkidle"),
                ],
                errback=self.errback,
                screenshot_name=inspect.currentframe().f_code.co_name
            )
        )

    async def open_session_page(self, response):
        page = response.meta["playwright_page"]
        # do stuff like populate item from response html + selectors...
        await page.close()
        # open the page to all posters
        self.logger.info("Open session page")
        yield scrapy.Request(
            response.url,
            callback=self.open_sessions,#self.open_events,
            meta=dict(
                playwright=True,
                playwright_include_page=True, # keep page object to work with
                playwright_page_methods = [
                    PageMethod("wait_for_selector", "a[href='/events/380/sessions']"),#productListing")
                    PageMethod("click", "a[href='/events/380/sessions']"),
                    PageMethod("wait_for_load_state", "networkidle"),
                ],
                errback=self.errback,
                screenshot_name=inspect.currentframe().f_code.co_name
            )
        )

    async def scroll_to_bottom(self, page, item_xpath, sleep=2.5, min_items: int = 0):
        await asyncio.sleep(sleep)
        ix = 1
        while True:
            n_poster_elements = len(await asyncio.wait_for(page.query_selector_all(item_xpath), timeout=30.))
            await page.keyboard.press("End")
            self.logger.info(f"scrolling key press: {ix} on {page.url}, n elements {n_poster_elements}")
            await asyncio.sleep(sleep)
            n_poster_elements_after = len(await asyncio.wait_for(page.query_selector_all(item_xpath), timeout=30.))
            ix += 1
            if n_poster_elements_after == n_poster_elements and n_poster_elements_after > min_items:
                self.logger.info(f"stop scroll, items haven't changed and minimum of {min_items} items exceeded")
                await page.wait_for_load_state("networkidle")
                break

    async def open_sessions(self, response, n_sessions_expected=1154, grace_factor=0.97):
        """
        1154 `a` elements on https://underline.io/events/380/sessions
        """
        page = response.meta["playwright_page"]
        sessions_url = page.url
        session_xpath = "//img[contains(@class, 'chakra-image') and @alt]"
        await page.screenshot(path=self.get_screenshot_name(response))
        middle_of_page_xpath = "//main/div/div[2]/div[2]"
        self.logger.info("Click middle of page")
        await page.wait_for_selector(middle_of_page_xpath)
        await page.click(middle_of_page_xpath)
        await self.scroll_to_bottom(page, item_xpath=session_xpath, min_items=int(n_sessions_expected*grace_factor))
        session_elements = await page.query_selector_all(session_xpath) # "xpath=//main//a"
        # Loop over each poster on the fully loaded event page
        session_links = await page.query_selector_all("xpath=//main/div/div[2]//a[not(@target='blank') and not(@target='_blank')]")
        session_urls = [urljoin(page.url, await (link := p.get_attribute('href'))) for p in session_links]
        self.logger.info(f"{len(session_elements)} elements, {len(session_urls)} links")
        self.logger.info(f"Identified {len(session_urls)} sessions by their link")
        self.logger.info(f"Identified {len(session_elements)} elements to scrape")
        for i, (session_element, session_url) in enumerate(zip(session_elements, session_urls)):
            if i < 466:
                continue
            self.logger.info(f"Scraping session: {i} at {session_url}")
            # await page.screenshot(path=f"poster-{i}-before.png")
            # await page.goto(poster_url, wait_until="networkidle")
            # await wait_idle_then_sleep(page, sleep=2.)
            # await page.screenshot(path=f"poster-{i}.png")
            #self.logger.warning(await page.content())
            # Wait for the specific poster element using its index before fetching it
            self.logger.info(f"Check if session {session_url} scraped already")
            if in_csv(session_url, csv="./scraped-sessions.csv"):
                self.logger.info(f"Already scraped {session_url}, skipping...")
                continue
            try:
                self.logger.info("Click middle of page")
                await page.wait_for_selector(middle_of_page_xpath)
                await page.click(middle_of_page_xpath)
                self.logger.info(f"Waiting for selector for session {i} to appear")
                await self.scroll_to_bottom(page, item_xpath=session_xpath, min_items=int(n_sessions_expected*grace_factor))
                session_element = await page.wait_for_selector(f"({session_xpath})[{i+1}]", timeout=20_000)
            except (TimeoutError, playwright._impl._api_types.TimeoutError):
                self.logger.warning(f"Session element {i} not found after waiting")
                # Log the page content for debugging purposes
                await page.screenshot(path=f"no_selector_sessions_{i}.png")
                #self.logger.info(f"Page content: {await page.content()}")
                #await page.go_back()
                self.logger.warning(f"Going back to sessions page: {sessions_url}")
                await page.goto(sessions_url)
                await wait_idle_then_sleep(page, sleep=3.)
                await self.scroll_to_bottom(
                    page,
                    item_xpath=sessions_xpath,
                    min_items=int(n_sessions_expected*grace_factor)
                )
                await page.screenshot(path="except_sessions.png")
                continue
            else:
                self.logger.info("Selector appeared, click")

            #Click on the session link and navigate to the session page
            ixx = 0
            while page.url != session_url:
                self.logger.warning(f"({ixx} click attempts) Page URL {page.url} != Session URL {session_url}")
                try:
                    session_element = await page.wait_for_selector(f"({session_xpath})[{i+1}]", timeout=20_000)
                    await click_with_retry(session_element, self.logger)
                except Exception as e:
                    self.logger.exception(e)
                    self.logger.error(f"Failed to click through to page {session_url}")
                    with open("./failed-sessions.log", "a") as fp:
                        fp.write(page.url + "\n")
                    continue
                await wait_idle_then_sleep(page, sleep=3.)
                ixx += 1
                if ixx >= 20:
                    raise Exception

            # Scrape an item from the poster page using a callback
            #ix = 1 
            ixx = 0
            try:
                self.logger.info("Parsing session page")
                async for item in self.parse_poster(page):
                    yield item
                self.logger.info("Write to CSV")
                write_to_csv(session_url, csv="./scraped-sessions.csv")
            except Exception as e:
                self.logger.error(f"Failed to parse item at {page.url}")
                with open("./failed-sessions.log", "a") as fp:
                    fp.write(page.url + "\n")
                self.logger.error(e)
            finally:
                self.logger.info(f"Going back to sessions page: {sessions_url}")
                ixx = 0
                while page.url != sessions_url:
                    await page.go_back()
                    await wait_idle_then_sleep(page, sleep=3.)
                    self.logger.warning(f"Page URL {page.url} != {sessions_url}")
                    #await page.screenshot(path=f"while-{ixx}.png")
                    ixx += 1
                    if ixx >= 20:
                        raise Exception
                else:
                    await wait_idle_then_sleep(page, sleep=3.)
                    #await page.screenshot(path="finally.png")

        await page.close()

    async def open_events(self, response):
        page = response.meta["playwright_page"]
        await page.screenshot(path=self.get_screenshot_name(response))
        
        # loop over all buttons pointing to events
        events_xpath = "//a[contains(@class, 'chakra-button')]"
        event_elements = await page.query_selector_all(events_xpath)
        self.logger.info(f"Identified {len(event_elements)} events to scrape")
        for i_e, _ in enumerate(event_elements):
            if i_e < 3:
                continue
            self.logger.info(f"At page URL: {page.url}")
            #await page.reload()
            await page.wait_for_load_state("networkidle")
            self.logger.info("Scroll to bottom to load all events")
            await self.scroll_to_bottom(page, item_xpath=events_xpath)
            await page.screenshot(path=f"start-of-event-loop-{i_e}.png", full_page=True)
            # Wait for the specific event element using its index before fetching it
            try:
                self.logger.info(f"Waiting for selector for event {i_e+1}/{len(event_elements)} to appear")
                event_element = await page.wait_for_selector(f"({events_xpath})[{i_e+1}]", timeout=10_000)
            except (TimeoutError, playwright._impl._api_types.TimeoutError):
                self.logger.warning(f"Event {i_e+1}/{len(event_elements)} not found after waiting")
                # Log the page content for debugging purposes
                #self.logger.info(f"Page content: {await page.content()}")
                await page.screenshot(path=f"wtf-{i_e}.png", full_page=True)
                continue
            
            # Click on the event button and navigate to the event page
            self.logger.info(f"Start scraping event: {event_element}")
            event_text = await event_element.inner_text() # "View XXX posters"
            n_posters_expected = int(re.match(".*\s(?P<n_posters>\d+)\s.*", event_text).group("n_posters"))
            self.logger.info(f"Button indicates {n_posters_expected} posters expected")
            await event_element.click()
            ## ~~~~~ Inside event page ~~~~~~
            await page.wait_for_load_state("networkidle")
            
            # Scroll down to load everything
            # make sure at least 95% of the reported abstracts are there (sometimes the number doesn't
            # match what's indicated on the button exactly) before terminating scroll
            self.logger.info("Scroll to bottom to load posters")
            poster_xpath = "//img[contains(@class, 'chakra-image') and @alt]"
            await self.scroll_to_bottom(page, item_xpath=poster_xpath, min_items=int(n_posters_expected*0.95))
            await page.screenshot(path=f"event_{i_e}.png")
            event_url = page.url
            self.logger.info(f"Event URL {event_url}") 
            # Loop over each poster on the fully loaded event page
            poster_elements = await page.query_selector_all(poster_xpath)
            poster_links = await page.query_selector_all("xpath=//main//a")
            poster_urls = [urljoin(page.url, await p.get_attribute('href')) for p in poster_links]
            self.logger.info(f"Identified {len(poster_urls)} posters by their link")
            # TODO
            # Just use //a and following-sibling on a chakra-stack div to get all the poster links so don't have to keep scrolling.
            self.logger.info(f"Identified {len(poster_elements)} posters to scrape")
            for i, (poster_element, poster_url) in enumerate(zip(poster_elements, poster_urls)):
                self.logger.info(f"Scraping poster: {i} at {poster_url}")
                # await page.screenshot(path=f"poster-{i}-before.png")
                # await page.goto(poster_url, wait_until="networkidle")
                # await wait_idle_then_sleep(page, sleep=2.)
                # await page.screenshot(path=f"poster-{i}.png")
                #self.logger.warning(await page.content())
                # Wait for the specific poster element using its index before fetching it
                self.logger.info(f"Check if poster {poster_url} scraped already")
                if in_csv(poster_url):
                    self.logger.info(f"Already scraped {poster_url}, skipping...")
                    continue
                try:
                    self.logger.info(f"Waiting for selector for poster {i} to appear")
                    await self.scroll_to_bottom(page, item_xpath=poster_xpath, min_items=int(n_posters_expected*0.95))
                    poster_element = await page.wait_for_selector(f"({poster_xpath})[{i+1}]", timeout=20_000)
                except (TimeoutError, playwright._impl._api_types.TimeoutError):
                    self.logger.warning(f"Poster element {i} not found after waiting")
                    # Log the page content for debugging purposes
                    await page.screenshot(path=f"no_selector_{i}.png")
                    #self.logger.info(f"Page content: {await page.content()}")
                    #await page.go_back()
                    self.logger.warning(f"Going back to event {i_e} page: {event_url}")
                    await page.goto(event_url)
                    await wait_idle_then_sleep(page, sleep=3.)
                    await self.scroll_to_bottom(page, item_xpath=poster_xpath, min_items=int(n_posters_expected*0.95))
                    await page.screenshot(path="except.png")
                    continue
                else:
                    self.logger.info("Selector appeared, click")

                #Click on the poster link and navigate to the poster page
                ixx = 0
                while page.url != poster_url:
                    self.logger.warning(f"({ixx} click attempts) Page URL {page.url} != Poster URL {poster_url}")
                    await click_with_retry(poster_element, self.logger)
                    await wait_idle_then_sleep(page, sleep=3.)
                    ixx += 1
                # Scrape an item from the poster page using a callback
                #ix = 1 
                try:
                    self.logger.info("Parsing poster page")
                    async for item in async_iterator_with_timeout(self.parse_poster(page), 90.):
                        yield item
                    self.logger.info("Write to CSV")
                    write_to_csv(poster_url)
                except Exception as e:
                    self.logger.error(f"Failed to parse item at {page.url}")
                    with open("./failed.log", "a") as fp:
                        fp.write(page.url + "\n")
                    self.logger.error(e)
                finally:

                    self.logger.info(f"Going back to event {i_e} page: {event_url}")
                    ixx = 0
                    while page.url != event_url:
                        await page.go_back()
                        await wait_idle_then_sleep(page, sleep=3.)
                        self.logger.warning(f"Page URL {page.url} != {event_url}")
                        await page.screenshot(path=f"while-{ixx}.png")
                        ixx += 1
                    else:
                    #await page.goto(event_url)
                    #await self.scroll_to_bottom(page, item_xpath=poster_xpath, min_items=int(n_posters_expected*0.95))
                        await wait_idle_then_sleep(page, sleep=3.)
                        await page.screenshot(path="finally.png")
                    #continue
                    #self.logger.info(f"parse poster iteration {ix} complete")
                    #ix+=1

                # # Return to the event page
                # self.logger.info(f"Going back to event {i_e} page")
                # await page.go_back()
                # await wait_idle_then_sleep(page, sleep=3.)

            # Return to the main events page
            self.logger.info(f"Going back to main events page")
            await page.goto(self.posters_url)#page.go_back()
            await wait_idle_then_sleep(page, sleep=3.)
        # Close the Playwright page
        await page.close()

    def set_user_agent(self, request, response):
        request.headers['User-Agent'] = self.user_agent
        return request

    async def parse_poster(self, page, sleep_switch_tabs=1.):
        """Main scraping method, constructs and populates an item from a given poster page"""
        # upon opening event page (response)
        # Construct the item loader to collect for the scraped data
        self.logger.info(f"Scraping poster basic info at {page.url}")
        
        item = AAAILoaderItem()
        html = await page.content()
        selector = Selector(text=html)
        loader = ItemLoader(item=item,
                            selector=selector)
        # populate the basic fields here from the event splash page
        loader.add_value("url", page.url)
        loader.add_value("conference", self.conference)
        loader.add_value("year", self.year)
        title = page.locator("//h1").last
        loader.add_value("title", await title.inner_text())
        authors = await title.locator("xpath=./following-sibling::div").inner_text()
        loader.add_value("authors", authors)
        # -- open individual tabs and continue scraping
        # scrape abstract (passing the item loader on in the metadata)
        self.logger.info("Opening abstract tab")
        buttons = page.get_by_role("button")
        abstract_text = page.get_by_text("Abstract")#re.compile("\s+?abstract\s+?", re.IGNORECASE))
        abstract_button = page.locator("button:text('Abstract')")
        if abstract_button is not None:
            await abstract_button.hover()
            await asyncio.sleep(sleep_switch_tabs)
            await abstract_button.click()
            await asyncio.sleep(sleep_switch_tabs)
            await page.wait_for_load_state("networkidle")
            self.logger.info("Extract abstract text")
            # self.logger.warning(await page.locator("//div[@role='tabpanel']//p").all_inner_texts())
            loader.add_value("abstract", " ".join(await page.locator("//div[@role='tabpanel']//p").all_inner_texts()))
        else:
            self.logger.warning("No abstract found")
            loader.add_value("abstract", "")
        # scrape poster content
        self.logger.info("Opening poster tab")
        # scrape poster info here
        # poster_button = page.locator("button:text('poster')")
        # if poster_button is not None:
        #     await poster_button.hover()
        #     await asyncio.sleep(sleep_switch_tabs)
        #     await poster_button.click()
        #     await asyncio.sleep(sleep_switch_tabs)
        #     await page.wait_for_load_state("networkidle")
        #     self.logger.info("Extracting poster content")
        loader.selector = (selector := Selector(text=await page.content()))
        slides_url = selector.xpath("//a[contains(text(), 'Download') and @download='slides']/@href").get()
        paper_url = selector.xpath("//a[contains(text(), 'Download') and @download='paper']/@href").get()
        loader.add_value("paper_url", urljoin(page.url, paper_url))
        loader.add_value("slides_url", urljoin(page.url, slides_url))
        item = loader.load_item()
        self.logger.debug("Scraped item:")
        self.logger.debug(item)
        yield item




    
    