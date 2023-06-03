# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html
from pathlib import Path
import typing as ty

import scrapy

from itemloaders.processors import Join, MapCompose, TakeFirst
from pydantic import AnyUrl, Field, validator

from scraper.db import ConferenceItem, Author, Keyword


def strip_space(string: str) -> str:
    return string.strip(" \n")


def split_name(authors: str) -> ty.List[str]:
    return authors.split(",")


class ICMLLoaderItem(scrapy.Item):
    conference: str = scrapy.Field(output_processor=TakeFirst())
    year: int = scrapy.Field(output_processor=TakeFirst())
    url: ty.Optional[AnyUrl] = scrapy.Field(output_processor=TakeFirst())
    item_type: ty.Optional[str] = scrapy.Field(input_processor=MapCompose(strip_space), output_processor=TakeFirst())
    title: ty.Optional[str] = scrapy.Field(input_processor=MapCompose(strip_space), output_processor=TakeFirst())
    authors: ty.Optional[ty.List[str]] = scrapy.Field(input_processor=MapCompose(strip_space, split_name))
    keywords: ty.Optional[ty.List[str]] = scrapy.Field(input_processor=MapCompose(strip_space))
    abstract: ty.Optional[str] = scrapy.Field(output_processor=TakeFirst())
    paper_url: ty.Optional[str] = scrapy.Field(output_processor=TakeFirst())
    poster_url: ty.Optional[str] = scrapy.Field(output_processor=TakeFirst()) 
    slides_url: ty.Optional[str] = scrapy.Field(output_processor=TakeFirst())

    @classmethod
    def parse_keyword(cls, v) -> Keyword:
        parts = v.split(":")
        if len(parts) == 2:
            return Keyword(type=parts[0].rstrip(), value=parts[1].lstrip())
        return Keyword(type=None, value=parts[0])

    def to_sqlmodel(self) -> ConferenceItem:
        keywords = [self.parse_keyword(k) for k in set(self.get("keywords", []))]
        authors = [Author(name=n) for n in set(self.get("authors", []))]
        return ConferenceItem(
            conference=self.get("conference"),
            year=self.get("year"),
            url=self.get("url"),
            item_type=self.get("item_type"),
            title=self.get("title"),
            authors=authors,
            keywords=keywords,
            abstract=self.get("abstract"),
            paper_url=self.get("paper_url"),
            poster_url=self.get("poster_url"),
            slides_url=self.get("slides_url")
        )



class NeurIPSLoaderItem(scrapy.Item):
    conference: str = scrapy.Field(output_processor=TakeFirst())
    year: int = scrapy.Field(output_processor=TakeFirst())
    url: ty.Optional[AnyUrl] = scrapy.Field(output_processor=TakeFirst())
    item_type: ty.Optional[str] = scrapy.Field(input_processor=MapCompose(strip_space), output_processor=TakeFirst())
    title: ty.Optional[str] = scrapy.Field(input_processor=MapCompose(strip_space), output_processor=TakeFirst())
    authors: ty.Optional[ty.List[str]] = scrapy.Field(input_processor=MapCompose(strip_space, split_name))
    keywords: ty.Optional[ty.List[str]] = scrapy.Field(input_processor=MapCompose(strip_space))
    abstract: ty.Optional[str] = scrapy.Field(output_processor=TakeFirst())
    paper_url: ty.Optional[str] = scrapy.Field(output_processor=TakeFirst())
    openreview_url: ty.Optional[str] = scrapy.Field(output_processor=TakeFirst())
    poster_url: ty.Optional[str] = scrapy.Field(output_processor=TakeFirst()) 
    slides_url: ty.Optional[str] = scrapy.Field(output_processor=TakeFirst())

    @classmethod
    def parse_keyword(cls, v) -> Keyword:
        parts = v.split(":")
        if len(parts) == 2:
            return Keyword(type=parts[0].rstrip(), value=parts[1].lstrip())
        return Keyword(type=None, value=parts[0])

    def to_sqlmodel(self) -> ConferenceItem:
        keywords = [self.parse_keyword(k) for k in set(self.get("keywords", []))]
        authors = [Author(name=n) for n in set(self.get("authors", []))]
        return ConferenceItem(
            conference=self.get("conference"),
            year=self.get("year"),
            url=self.get("url"),
            item_type=self.get("item_type"),
            title=self.get("title"),
            authors=authors,
            keywords=keywords,
            abstract=self.get("abstract"),
            paper_url=self.get("paper_url"),
            openreview_url=self.get("openreview_url"),
            poster_url=self.get("poster_url"),
            slides_url=self.get("slides_url")
        )


class AAAILoaderItem(scrapy.Item):
    conference: str = scrapy.Field(output_processor=TakeFirst())
    year: int = scrapy.Field(output_processor=TakeFirst())
    url: ty.Optional[AnyUrl] = scrapy.Field(output_processor=TakeFirst())
    item_type: ty.Optional[str] = scrapy.Field(input_processor=MapCompose(strip_space), output_processor=TakeFirst())
    title: ty.Optional[str] = scrapy.Field(input_processor=MapCompose(strip_space), output_processor=TakeFirst())
    authors: ty.Optional[ty.List[str]] = scrapy.Field(input_processor=MapCompose(strip_space, split_name))
    keywords: ty.Optional[ty.List[str]] = scrapy.Field(input_processor=MapCompose(strip_space))
    abstract: ty.Optional[str] = scrapy.Field(output_processor=TakeFirst())
    paper_url: ty.Optional[str] = scrapy.Field(output_processor=TakeFirst())
    openreview_url: ty.Optional[str] = scrapy.Field(output_processor=TakeFirst())
    poster_url: ty.Optional[str] = scrapy.Field(output_processor=TakeFirst()) 
    slides_url: ty.Optional[str] = scrapy.Field(output_processor=TakeFirst())

    @classmethod
    def parse_keyword(cls, v) -> Keyword:
        parts = v.split(":")
        if len(parts) == 2:
            return Keyword(type=parts[0].rstrip(), value=parts[1].lstrip())
        return Keyword(type=None, value=parts[0])

    def to_sqlmodel(self) -> ConferenceItem:
        keywords = [self.parse_keyword(k) for k in set(self.get("keywords", []))]
        authors = [Author(name=n) for n in set(self.get("authors", []))]
        return ConferenceItem(
            conference=self.get("conference"),
            year=self.get("year"),
            url=self.get("url"),
            item_type=self.get("item_type"),
            title=self.get("title"),
            authors=authors,
            keywords=keywords,
            abstract=self.get("abstract"),
            paper_url=self.get("paper_url"),
            openreview_url=self.get("openreview_url"),
            poster_url=self.get("poster_url"),
            slides_url=self.get("slides_url")
        )