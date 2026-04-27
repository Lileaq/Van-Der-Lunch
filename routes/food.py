from fastapi import FastAPI, Depends, APIRouter, HTTPException, Query
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from database_configuration import get_db,Tag,FoodItem
from logger import logger
from routes.user import get_current_user
from schemas import FoodItemResponse, FoodListResponse

router = APIRouter(
    prefix="/food",
    tags=["food"]
)
@router.get(
    '/food-list',
    summary="List food items",
    description="Returns a list of food items filtered by food tags.",
    response_model=FoodListResponse,
    responses={
            404: {"description": "Food items not found"},
            500: {"description" : "Get food list failed"}
    })
async def food_list(
        db: AsyncSession = Depends(get_db),
        user: dict = Depends(get_current_user),
        tags : Optional[list[int]] = Query(None)
):
    logger.info("Hit /food-list")
    try:
        query = select(FoodItem).options(selectinload(FoodItem.tags))
        filters = []

        if(tags != None):
            # filter by type tags if contains any of the tags then it's added
            query = query.join(FoodItem.tags)
            filters.append(Tag.id.in_(tags))

        if filters:
            query = query.where(and_(*filters))

        result = await db.execute(query)
        food_list = result.scalars().unique().all()

        if not food_list:
            raise HTTPException(status_code=404,detail="No food fit the criteria")

        return {"food_list" : food_list}
    except Exception as e:
        logger.info(f"food list failed : {e}")
        raise HTTPException(status_code=500, detail="food list failed")

@router.get(
    "/{id}",
    summary="Get food item details",
    description="Returns detailed information about a specific food item including its tags.",
    response_model=FoodItemResponse,
    responses={
        404: {"description": "Food item not found"},
        500: {"description" : "Get food info failed"}
    }
)
async def food_info(
        id : int,
        db : AsyncSession = Depends(get_db),
        user: dict = Depends(get_current_user)
):
    logger.info("Hit /food/id/")
    try:
        query = select(FoodItem).options(selectinload(FoodItem.tags)).where(FoodItem.id == id)
        result = await db.execute(query)
        food = result.scalars().first()

        if not food:
            raise HTTPException(status_code=404, detail="Food item not found")

        return food
    except Exception as e:
        logger.info(f"Get food info failed: {e}")
        raise HTTPException(status_code=500, detail="Get food info failed")



