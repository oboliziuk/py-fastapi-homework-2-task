from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.openapi.models import Response
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from database import get_db
from database.models import (
    CountryModel,
    GenreModel,
    ActorModel,
    LanguageModel,
    MovieModel,
)


from fastapi import Request, Path
import math

from schemas.movies import (
    MovieDetailSchema,
    MovieCreateSchema,
    MovieReplaceSchema,
    MovieUpdateSchema,
    MovieListResponseSchema,
    MovieListItemSchema,
    PaginationParams,
)

router = APIRouter()


@router.get("/movies/", response_model=MovieListResponseSchema)
async def read_movies(
    request: Request,
    pagination: PaginationParams = Depends(),
    db: AsyncSession = Depends(get_db)
):
    page = pagination.page
    per_page = pagination.per_page

    if per_page <= 0:
        raise HTTPException(
            status_code=400, detail="per_page must be >= 1"
        )

    total_items_result = await db.execute(
        select(func.count()).select_from(MovieModel)
    )
    total_items = total_items_result.scalar_one()
    total_pages = math.ceil(total_items / per_page)

    if total_items == 0:
        raise HTTPException(status_code=404, detail="No movies found.")

    result = await db.execute(
        select(MovieModel)
        .order_by(MovieModel.id.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
    )
    movies = result.scalars().all()

    base_url = str(request.url).split("?")[0]
    if not movies:
        raise HTTPException(
            status_code=404,
            detail="No movies found."
        )

    def build_url(page_number: int) -> str:
        return f"{base_url}?page={page_number}&per_page={per_page}"

    return {
        "movies": movies,
        "prev_page": build_url(page - 1) if page > 1 else None,
        "next_page": build_url(page + 1) if page < total_pages else None,
        "total_pages": total_pages,
        "total_items": total_items,
    }


@router.get(
    "/movies/{movie_id}/",
    response_model=MovieDetailSchema
)
async def get_movie(
        movie_id: int = Path(..., ge=1),
        db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(MovieModel)
        .options(
            joinedload(MovieModel.country),
            joinedload(MovieModel.genres),
            joinedload(MovieModel.actors),
            joinedload(MovieModel.languages),
        )
        .where(MovieModel.id == movie_id)
    )
    movie = result.unique().scalar_one_or_none()
    if not movie:
        raise HTTPException(
            status_code=404,
            detail="Movie with the given ID was not found."
        )
    return movie


@router.post(
    "/movies/",
    response_model=MovieDetailSchema
)
async def create_movie(
        movie: MovieCreateSchema, db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(CountryModel).where(CountryModel.name == movie.country))
    country = result.scalar_one_or_none()
    if not country:
        raise HTTPException(status_code=404, detail="Country not found")

    existing_movie_query = await db.execute(
        select(MovieModel).where(
            MovieModel.name == movie.name,
            MovieModel.date == movie.date
        )
    )
    existing_movie = existing_movie_query.scalar_one_or_none()
    if existing_movie:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"A movie with the name '{movie.name}' "
                   f"and release date '{movie.date}' already exists."
        )

    country_result = await db.execute(
        select(CountryModel).where(CountryModel.code == movie.country)
    )
    country = country_result.scalar_one_or_none()
    if not country:
        raise HTTPException(status_code=404, detail="Country not found")

    new_movie = MovieModel(
        name=movie.name,
        date=movie.date,
        score=movie.score,
        overview=movie.overview,
        status=movie.status,
        budget=movie.budget,
        revenue=movie.revenue,
        country_id=country.id,
    )

    new_movie.genres = []
    for genre_name in movie.genres or []:
        result = await db.execute(
            select(GenreModel).where(GenreModel.name == genre_name)
        )
        genre = result.scalar_one_or_none()
        if not genre:
            genre = GenreModel(name=genre_name)
            db.add(genre)
            await db.flush()
            new_movie.genres.append(genre)

    new_movie.actors = []
    for actor_name in movie.actors or []:
        result = await db.execute(
            select(ActorModel).where(ActorModel.name == actor_name)
        )
        actor = result.scalar_one_or_none()
        if not actor:
            actor = ActorModel(name=actor_name)
            db.add(actor)
            await db.flush()
            new_movie.actors.append(actor)

    new_movie.languages = []
    for lang_name in movie.languages or []:
        result = await db.execute(
            select(LanguageModel).where(LanguageModel.name == lang_name)
        )
        lang = result.scalar_one_or_none()
        if not lang:
            lang = LanguageModel(name=lang_name)
            db.add(lang)
            await db.flush()
        new_movie.languages.append(lang)

    db.add(new_movie)
    await db.commit()
    await db.refresh(new_movie)
    return new_movie


@router.put(
    "/movies/{movie_id}/",
    response_model=MovieDetailSchema,
    responses={
        200: {"description": "Movie fully updated."},
        404: {"detail": "Movie with the given ID was not found."},
        400: {"detail": "Invalid input data."}
    }
)
async def replace_movie(
    movie_id: int,
    movie: MovieReplaceSchema,
    db: AsyncSession = Depends(get_db)
):
    db_movie = await db.scalar(
        select(MovieModel).where(MovieModel.id == movie_id)
    )
    if not db_movie:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Movie with the given ID was not found."
        )

    update_data = movie.dict()  # НЕ exclude_unset!
    for field, value in update_data.items():
        setattr(db_movie, field, value)

    await db.commit()
    await db.refresh(db_movie)
    return db_movie


@router.patch(
    "/movies/{movie_id}/",
    response_model=MovieDetailSchema,
    responses={
        200: {"description": "Movie updated successfully."},
        404: {"detail": "Movie with the given ID was not found."},
        400: {"detail": "Invalid input data."}
    }
)
async def update_movie(
        movie_id: int,
        movie: MovieUpdateSchema,
        db: AsyncSession = Depends(get_db),
):
    db_movie = await db.scalar(
        select(MovieModel).where(MovieModel.id == movie_id)
    )
    if not db_movie:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Movie with the given ID was not found."
        )

    update_data = movie.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_movie, field, value)

    await db.commit()
    await db.refresh(db_movie)
    return db_movie


@router.delete(
    "/movies/{movie_id}/",
    status_code=status.HTTP_204_NO_CONTENT
)
async def delete_movie(
        movie_id: int,
        db: AsyncSession = Depends(get_db)
):
    db_movie = await db.scalar(
        select(MovieModel).where(MovieModel.id == movie_id)
    )
    if not db_movie:
        raise HTTPException(status_code=404, detail="Movie with the given ID was not found.")

    await db.delete(db_movie)
    await db.commit()
