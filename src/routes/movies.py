import math
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.functions import func

from src.database.models import MovieModel
from src.database.session import get_db
from sqlalchemy import select
from src.schemas.movies import MovieDetailResponseSchema, MovieListResponseSchema

router = APIRouter()


@router.get("/movies/", response_model=MovieListResponseSchema)
async def get_movies(
        request: Request,
        db: AsyncSession = Depends(get_db),
        page: int = Query(1, ge=1),
        per_page: int = Query(10, ge=1, le=20),
):
    total_items = (await db.execute(select(func.count()).select_from(MovieModel))).scalar()
    total_pages = math.ceil(total_items / per_page) if total_items else 1
    if page > total_pages:
        raise HTTPException(status_code=404, detail="No movies found.")
    res = await db.execute(select(MovieModel).offset((page - 1) * per_page).limit(per_page))
    movies = res.scalars().all()
    total_items = (res.scalar() or 0)
    if total_items == 0:
        raise HTTPException(status_code=404, detail="No movies found.")
    base_url = str(request.url).split("?")[0]
    prev_page = None
    next_page = None

    if page > 1:
        prev_page = base_url + "?page={}".format(page - 1) + "&per_page={}".format(per_page)
    if page < total_pages:
        next_page = base_url + "?page={}".format(page + 1) + "&per_page={}".format(per_page)

    return MovieListResponseSchema(
        movies=movies,
        prev_page=prev_page,
        next_page=next_page,
        total_pages=total_pages,
        total_items=total_items,
    )


@router.get("/movies/{movie_id}/", response_model=MovieDetailResponseSchema)
async def get_movie(movie_id: int, db: AsyncSession = Depends(get_db)):
    movie = await db.get(MovieModel, movie_id)
    if not movie:
        raise HTTPException(status_code=404, detail="Movie with the given ID was not found.")
    return movie
