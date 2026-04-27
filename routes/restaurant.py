from fastapi import Depends, APIRouter, HTTPException, Query, Path
from sqlalchemy import select, and_, func
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from database_configuration import get_db, Restaurant, Tag, FoodItem, RestaurantOpeningHour
from datetime import datetime, timezone
from logger import logger
from routes.user import get_current_user
from schemas import RestaurantsResponse, MenuResponse, RestaurantBase

router = APIRouter(
    prefix="/restaurant",
    tags=["restaurant"]
)

@router.get(
    '/restaurants-list',
    summary="Get filtered list of restaurants",
    description="Returns a list of restaurants filtered by location (radius ~50km), category tags or opening hours.",
    response_model=RestaurantsResponse,
    responses={
        200: {"description": "List of restaurants fitting the criteria"},
        404: {"description": "No restaurants fit the critera"},
        500: {"description": "Get restaurant info failed"}
    })
async def restaurant_list(
        db: AsyncSession = Depends(get_db),
        user: dict = Depends(get_current_user),
        # user criteria
        lat : Optional[float] = Query(None, description="Latitude for distance filtering", example=52.23),
        lng : Optional[float] = Query(None, description="Longitude for distance filtering", example=21.01),
        tags : Optional[list[int]] =Query(None, description="List of Tag IDs to filter by"),
        is_open : Optional[bool] = Query(None,description="Determines if opening hours are taken into account")
):
    # returns the list of restaurants that check the criteria loation and/or type_tags
    logger.info("Hit /restaurants-list")
    try:
        query = select(Restaurant).options(
            selectinload(Restaurant.tags),
            selectinload(Restaurant.opening_hours_list)
        )
        filters = []

        if(lat != None):
            # filter by distance <50km so <0.5 on both with abs to check both ways
            filters.append(
                and_(
                    func.abs(Restaurant.lat - lat) < 0.5,
                )
            )

        if (lng != None):
            # filter by distance <50km so <0.5 on both with abs to check both ways
            filters.append(
                and_(
                    func.abs(Restaurant.lng - lng) < 0.5
                )
            )



        if(tags != None):
            # filter by type tags if contains any of the tags then it's added
            query = query.join(Restaurant.tags)
            filters.append(Tag.id.in_(tags))

        if is_open is True:
            now = datetime.now(timezone.utc)
            current_day = now.weekday()
            current_minutes = now.hour * 60 + now.minute

            query = query.join(Restaurant.opening_hours_list)

            filters.append(
                and_(
                    RestaurantOpeningHour.day_of_week == current_day,
                    RestaurantOpeningHour.is_closed == False,
                    RestaurantOpeningHour.open_from_minute <= current_minutes,
                    RestaurantOpeningHour.close_to_minute >= current_minutes
                )
            )

        if filters:
            query = query.where(and_(*filters))

        result = await db.execute(query)
        restaurants_list = result.scalars().unique().all()




    except Exception as e:
        logger.info(f"restaurants list failed : {e}")
        raise HTTPException(status_code=500, detail="Restaurant list failed")

    if not restaurants_list:
        raise HTTPException(status_code=400, detail="No restaurants fit the critera")

    return {"restaurants_list": restaurants_list}


@router.get(
    "/{id}/menu",
    summary="Get restaurant menu",
    description="Returns all food items available in a specific restaurant.",
    response_model=MenuResponse,
    responses={
            200: {"description": "List of restaurants fitting the criteria"},
            404 : {"description": "Food items not found"},
            500: {"description": "Get restaurant menu failed"}
    })
async def info(
        id : int = Path(..., description="The ID of the restaurant"),
        db : AsyncSession = Depends(get_db),
        user: dict = Depends(get_current_user)
):

    # gets restaurant menu based on id
    logger.info("Hit /restaurant/id/menu")
    try:
        query = select(FoodItem).where(FoodItem.restaurant_id == id)
        result = await db.execute(query)
        food_items = result.scalars().all()

    except Exception as e:
        logger.info(f"Restaurants menu failed : {e}")
        raise HTTPException(status_code=500, detail="Restaurant menu failed")

    if food_items is None:
        raise HTTPException(status_code=404, detail="Food items not found")

    return {"food_items": food_items}


@router.get(
    "/{id}",
    summary="Get restaurant details",
    description="Returns full information about a specific restaurant by its ID.",
    response_model=RestaurantBase,
    responses={404: {"description": "Restaurant not found"},
               500: {"description": "Get restaurant info failed"}})
async def info(
        id : int,
        db : AsyncSession = Depends(get_db),
        user: dict = Depends(get_current_user)
):
    # gets full restaurant info based on id
    logger.info("Hit /restaurant/id")
    try:
        query = select(Restaurant).where(Restaurant.id == id)
        result = await db.execute(query)
        restaurant = result.scalars().first()

    except Exception as e:
        logger.info(f"Restaurant info failed : {e}")
        raise HTTPException(status_code=500, detail="Restaurant info failed")

    if not restaurant:
        raise HTTPException(status_code=404, detail="Restaurant not found")
    return restaurant


