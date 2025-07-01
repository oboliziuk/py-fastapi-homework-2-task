from pydantic import BaseModel, Field, field_validator
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
    name: str
    date: date
    score: float
    overview: str
    status: MovieStatusEnum
    budget: float
    revenue: float
    country: str
    genres: List[str]
    actors: List[str]
    languages: List[str]

    class Config:
        from_attributes = True

    @field_validator("date")
    def validate_date_not_too_far(cls, value):
        if value > date.today() + timedelta(days=365):
            raise ValueError("The date must not be more than one year in the future.")
        return value

    @validator("score")
    def validate_score_between_0_and_100(cls, value):
        if not 0 <= value <= 100:
            raise ValueError("The score must be between 0 and 100.")
        return value

    @validator("budget")
    def validate_budget_non_negative(cls, value):
        if value < 0:
            raise ValueError("The budget must be non-negative.")
        return value

    @validator("revenue")
    def validate_revenue_non_negative(cls, value):
        if value < 0:
            raise ValueError("The revenue must be non-negative.")
        return value


class MovieCreate(MovieBase):
    pass


class MovieReplace(MovieBase):
    pass


class MovieUpdate(BaseModel):
    name: Optional[str]
    date: Optional[date]
    score: Optional[float]
    overview: Optional[str]
    status: Optional[MovieStatusEnum]
    budget: Optional[float]
    revenue: Optional[float]

    class Config:
        from_attributes = True


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
