
import typing as ty

from sqlalchemy import UniqueConstraint
from sqlmodel import SQLModel, Field, create_engine, Relationship
from pydantic import AnyUrl, validator


class AuthorPubLink(SQLModel, table=True):
    author_id: ty.Optional[int] = Field(
        default=None, foreign_key="author.id", primary_key=True
    )
    confitem_id: ty.Optional[int] = Field(
        default=None, foreign_key="conferenceitem.id", primary_key=True
    )


class KeywordPubLink(SQLModel, table=True):
    keyword_id: ty.Optional[int] = Field(
        default=None, foreign_key="keyword.id", primary_key=True
    )
    confitem_id: ty.Optional[int] = Field(
        default=None, foreign_key="conferenceitem.id", primary_key=True
    )


class ConferenceItem(SQLModel, table=True):
    id: ty.Optional[int] = Field(default=None, primary_key=True)
    url: AnyUrl
    title: str = Field(index=True, unique=False)
    item_type: ty.Optional[str] = Field(default=None, index=True)
    authors: ty.List["Author"] = Relationship(
        back_populates="conference_items", link_model=AuthorPubLink
    )
    keywords: ty.Optional[ty.List["Keyword"]] = Relationship(
        back_populates="conference_items", link_model=KeywordPubLink
    )
    conference: ty.Optional[str] = Field(default=None)
    year: ty.Optional[int] = Field(default=None)
    abstract: ty.Optional[str] = Field(default=None)
    paper_url: ty.Optional[str] = Field(default=None)
    openreview_url: ty.Optional[str] = Field(default=None)
    poster_url: ty.Optional[str] = Field(default=None)
    slides_url: ty.Optional[str] = Field(default=None)


class Author(SQLModel, table=True):
    id: ty.Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)#, unique=True)

    conference_items: ty.List[ConferenceItem] = Relationship(
        back_populates="authors", link_model=AuthorPubLink
    )


class Keyword(SQLModel, table=True):
    #__table_args__ = (UniqueConstraint("type", "value"),)
    id: ty.Optional[int] = Field(default=None, primary_key=True)
    type: ty.Optional[str] = Field(index=True)
    value: str = Field(index=True)

    conference_items: ty.List[ConferenceItem] = Relationship(
        back_populates="keywords", link_model=KeywordPubLink
    )