from fastapi import Depends, APIRouter, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from database_configuration import get_db, Tag, food_tags, restaurant_tags
from logger import logger
from schemas import TagsResponse

router = APIRouter(
    prefix="/tags",
    tags=["tags"]
)


@router.get(
    "/restaurants",
    summary="Get all restaurant tags",
    description="Returns a complete list of tags available for filtering restaurants (e.g., Italian, Vegan, Fast Food).",
    response_model=TagsResponse,
    responses={
        500: {"description": "Internal server error"}
    }
)
async def get_restaurants_tags(
    db: AsyncSession = Depends(get_db)
):
    logger.info("Hit /tags/restaurants")
    try:
        # Pobieramy wyłącznie tagi używane w powiązaniach z restauracjami
        query = select(Tag).join(restaurant_tags).distinct()
        result = await db.execute(query)
        tags = result.scalars().all()
        return {"tags": tags}
    except Exception as e:
        logger.error(f"Failed to fetch restaurant tags: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch restaurant tags")


@router.get(
    "/food",
    summary="Get all food tags",
    description="Returns a complete list of tags available for food items (e.g., Spicy, Gluten-Free, Vegan).",
    response_model=TagsResponse,
    responses={
        500: {"description": "Internal server error"}
    }
)
async def get_food_tags(
    db: AsyncSession = Depends(get_db)
):
    logger.info("Hit /tags/food")
    try:
        # Poprawka: zapytanie na modelu Tag łączone tabelą food_tags, aby wydobyć tagi dla jedzenia
        query = select(Tag).join(food_tags).distinct()
        result = await db.execute(query)
        tags = result.scalars().all()
        return {"tags": tags}
    except Exception as e:
        logger.error(f"Failed to fetch food tags: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch food tags")