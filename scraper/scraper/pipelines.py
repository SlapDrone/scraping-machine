# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html
import asyncio
import logging
# useful for handling different item types with a single interface
from collections import defaultdict
#from itemadapter import ItemAdapter
from pydantic import ValidationError
from sqlmodel import Session
from sqlmodel.ext.asyncio.session import AsyncSession

from scraper.settings import get_settings
from scraper.db import SQLModel, create_db_and_tables, engine, async_engine, ConferenceItem, Keyword, Author, get_or_create, async_get_or_create


logger = logging.getLogger(__name__)


class SQLModelItemPipeline:

    def open_spider(self, spider):
        self.settings = get_settings()
        logger.info("Creating tables")
        create_db_and_tables()

    def close_spider(self, spider):
        pass

    def validate_item(self, item):
        # validate item
        try:
            return item.to_sqlmodel()
        except ValidationError as err:
            logger.error("Skipping item, encountered validation error with details: ")
            logger.error(err)
            logger.error(item)

    def process_item(self, item, spider):
        item = self.validate_item(item)
        if item is not None:
            with Session(engine) as session:
                logger.info("Adding item to database")
                # ensure we don't duplicate entries
                authors = [get_or_create(a, session) for a in item.authors]
                keywords = [get_or_create(k, session) for k in item.keywords]
                item = get_or_create(item, session)
                item.authors = authors
                item.keywords = keywords
                session.add(item)
                session.commit()
                session.refresh(item)
                logger.info("Item added successfully")
        return item



class AsyncSQLModelItemPipeline:

    def open_spider(self, spider):
        self.settings = get_settings()
        logger.info("Creating tables")
        create_db_and_tables()

    def close_spider(self, spider):
        pass

    def validate_item(self, item):
        # validate item
        try:
            return item.to_sqlmodel()
        except ValidationError as err:
            logger.error("Skipping item, encountered validation error with details: ")
            logger.error(err)
            logger.error(item)

    async def process_item(self, item, spider):
        item = self.validate_item(item)
        logger.info("Item to be inserted:")
        logger.info(item)
        if item is not None:
            async with AsyncSession(async_engine) as session:
                logger.info("Adding item to database")
                # ensure we don't duplicate entries
                # https://github.com/MagicStack/asyncpg/issues/863
                #authors = await asyncio.gather(*[async_get_or_create(a, session) for a in item.authors])
                #keywords = await asyncio.gather(*[async_get_or_create(k, session) for k in item.keywords])
                item = await async_get_or_create(item, session)
                logger.info("Item after get_or_create:")
                logger.info(item)
                #item = ConferenceItem.from_orm(item)
                #item.authors = authors
                #item.keywords = keywords
                session.add(item)
                await session.commit()
                await session.refresh(item)
                logger.info("Item added successfully")
        return item