from pydantic import BaseModel, Field, constr
from pydantic.config import ConfigDict

from datetime import date, timedelta
from typing import List, Optional

from fastapi import Query
from enum import Enum

from pydantic.v1 import validator


class MovieStatusEnum(str, Enum):
    released = "Released"
    post_production = "Post Production"
    in_production = "In Production"

    class Config:
        from_attributes = True


class CountrySchema(BaseModel):
    id: int
    code: str
    name: Optional[str] = None

    class Config:
        from_attributes = True


class GenreSchema(BaseModel):
    id: int
    name: str = Field(..., max_length=255)

    class Config:
        from_attributes = True


class ActorSchema(BaseModel):
    id: int
    name: str = Field(..., max_length=255)

    class Config:
        from_attributes = True


class LanguageSchema(BaseModel):
    id: int
    name: str = Field(..., max_length=255)

    class Config:
        from_attributes = True


class MovieBase(BaseModel):
    name: constr(max_length=255)
    date: date
    score: float = Field(..., ge=0, le=100)
    overview: str
    status: MovieStatusEnum
    budget: float = Field(..., ge=0)
    revenue: float = Field(..., ge=0)
    country: str
    genres: List[str]
    actors: List[str]
    languages: List[str]

    class Config:
        from_attributes = True

    @validator("date")
    def validate_date_not_too_far(cls, value):
        if value > date.today() + timedelta(days=365):
            raise ValueError("The date must not be more than one year in the future.")
        return value


class MovieCreateSchema(MovieBase):
    pass


class MovieReplaceSchema(MovieBase):
    pass


class MovieUpdateSchema(BaseModel):
    name: Optional[str]
    date: Optional[date]
    score: Optional[float] = Field(None, ge=0, le=100)
    overview: Optional[str]
    status: Optional[MovieStatusEnum]
    budget: Optional[float] = Field(None, ge=0)
    revenue: Optional[float] = Field(None, ge=0)

    @validator("date")
    def validate_date_not_too_far(cls, v):
        if v is not None and v > date.today() + timedelta(days=365):
            raise ValueError("The date must not be more than one year in the future.")
        return v


class MovieDetailSchema(MovieBase):
    id: int
    country: CountrySchema
    genres: List[GenreSchema]
    actors: List[ActorSchema]
    languages: List[LanguageSchema]

    class Config:
        from_attributes = True


class MovieListItemSchema(BaseModel):
    id: int
    name: str
    date: date
    score: float
    overview: str

    class Config:
        from_attributes = True


class PaginationParams(BaseModel):
    page: int = Query(1, ge=1)
    per_page: int = Query(10, ge=1, le=20)


class MovieListResponseSchema(BaseModel):
    movies: List[MovieListItemSchema]
    prev_page: Optional[str]
    next_page: Optional[str]
    total_pages: int
    total_items: int

    class Config:
        from_attributes = True
