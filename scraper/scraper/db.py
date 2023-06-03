import logging
import typing as ty
import sys
sys.path.insert(0, ".")

from sqlalchemy.ext.asyncio import create_async_engine
from sqlmodel import SQLModel, create_engine, Session, select
from sqlmodel.ext.asyncio.session import AsyncSession

from scraper.settings import get_settings
from scraper.models import Keyword, Author, ConferenceItem, KeywordPubLink, AuthorPubLink


logger = logging.getLogger(__name__)
logger.setLevel(logging.WARNING)

settings = get_settings()
engine = create_engine(settings.database_url, echo=settings.echo_sql)
async_engine = create_async_engine(settings.async_database_url, echo=settings.echo_sql)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


def drop_all_tables():
    SQLModel.metadata.drop_all(engine)


def get_or_create(model: SQLModel, session: Session, **kwargs) -> SQLModel:
    # look for full match on all attributes by default
    # figure out if this works as intended with relationship keys
    # it may also make sense to make the kwargs actually just a set of attributes:
    # the values are already fixed by the model
    if not kwargs:
        kwargs = {k:v for k, v in model.dict().items() if v is not None}
    logger.debug(f"filtering by {kwargs}")
    instance = session.query(model.__class__).filter_by(**kwargs).first()
    if instance:
        logger.warning(f"model already exists in db: {instance}")
        return instance
    logger.debug(f"model doesnt exist yet: {model}")
    return model


async def async_get_or_create(model: SQLModel, session: AsyncSession, **kwargs) -> SQLModel:
    # look for full match on all attributes by default
    # figure out if this works as intended with relationship keys
    # it may also make sense to make the kwargs actually just a set of attributes:
    # the values are already fixed by the model
    if not kwargs:
        kwargs = {k:v for k, v in model.dict().items() if v is not None}
    logger.debug(f"filtering by {kwargs}")
    q = select(model.__class__).filter_by(**kwargs)
    result = await session.execute(q)
    instance = result.scalar_one_or_none()
    #instance = await session.query(model.__class__).filter_by(**kwargs).first()
    if instance:
        logger.warning(f"model already exists in db: {instance}")
        return instance
    logger.debug(f"model doesnt exist yet: {model}")
    return model


# quick test SQLmodel working as intended
if __name__ == "__main__":
    logger.setLevel(logging.INFO)
    drop_all_tables()
    create_db_and_tables()

    a = Author(name="Test Person")
    k = Keyword(value="Misc.")
    logger.info("construct")
    p = ConferenceItem.construct(
        authors = [a],
        keywords = [k],
        title="Test Paper",
        url="https://www.test.paper"
    )
    d = p.dict()
    logger.info("validate")
    p = ConferenceItem.validate(d)

    # duplicates to check get_or_create logic
    k2 = Keyword(value="Interesting")
    k3 = Keyword(value="Interesting")

    a2 = Author(name="Mr. Bean")
    a3 = Author(name="Mr. Bean")

    with Session(engine) as sesh:
        m = get_or_create(p, sesh)
        sesh.add(m)
        sesh.commit()

        kk = get_or_create(k2, sesh)
        sesh.add(kk)
        sesh.commit()

        kk = get_or_create(k3, sesh)
        sesh.add(kk)
        sesh.commit()

        
        aa = get_or_create(a2, sesh)
        sesh.add(aa)
        sesh.commit()

        aa = get_or_create(a3, sesh)
        sesh.add(aa)
        sesh.commit()

    # test creating 2 different publications with the same keywords and see if the keyword entries are duplicated?

    drop_all_tables()