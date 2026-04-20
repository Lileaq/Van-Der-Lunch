import nh3
from fastapi import FastAPI, Depends, APIRouter, HTTPException, Request, Query
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from sqlalchemy import select, and_, func
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session
from fastapi.responses import JSONResponse
from typing import Optional

from database_configuration import get_db,Restaurant,Tag,FoodItem,Review
from passlib.context import CryptContext
import jwt
from datetime import datetime, timedelta
from logger import logger

router = APIRouter(
    prefix="/restaurant",
    tags=["restaurant"]
)

@router.get('/restaurants')
async def restaurant_list(
        db: AsyncSession = Depends(get_db),
        # user criteria
        lat : Optional[float] = None,
        lng : Optional[float] = None,
        tags : Optional[list[int]] = Query(None)
):
    # returns the list of restaurants that check the criteria loation and/or type_tags
    logger.info("Hit /restaurants")
    try:
        query = select(Restaurant).options(selectinload(Restaurant.tags))
        filters = []

        if(lat != None and lng != None):
            # filter by distance <50km so <0.5 on both with abs to check both ways
            filters.append(
                and_(
                    func.abs(Restaurant.lat - lat) < 0.5,
                    func.abs(Restaurant.lng - lng) < 0.5
                )
            )
        if(tags != None):
            # filter by type tags if contains any of the tags then it's added
            query = query.join(Restaurant.tags)
            filters.append(Tag.id.in_(tags))

        if filters:
            query = query.where(and_(*filters))

        result = await db.execute(query)
        restaurants_list = result.scalars().unique().all()

        if not restaurants_list:
            return {"msg" : "No restaurants fit the criteria"}

        return {"restaurants_list" : restaurants_list}
    except Exception as e:
        logger.info(f"restaurants list failed : {e}")
        raise HTTPException(status_code=500, detail="restaurant list failed")


@router.get("/restaurant/{id}/menu")
async def info(
        id : int,
        db : AsyncSession = Depends(get_db)
):

    # gets restaurant menu based on id
    logger.info("Hit /restaurant/id/menu")
    query = select(FoodItem).where(FoodItem.restaurant_id == id)
    result = await db.execute(query)
    food_items =  result.scalars().all()
    return {"food_items" : food_items}


@router.get("/restaurant/{id}")
async def info(
        id : int,
        db : AsyncSession = Depends(get_db)):
    # gets full restaurant info based on id
    logger.info("Hit /restaurant/id")
    try:
        query = select(Restaurant).where(Restaurant.id == id)
        result = await db.execute(query)
        restaurant = result.scalars().first()
        return {"restaurant" : restaurant}
    except Exception as e:
        logger.info(f"restaurants info failed : {e}")
        raise HTTPException(status_code=500, detail="restaurant info failed")

@router.get("/restaurant/{id}/reviews")
async def info(
        id : int,
        db : AsyncSession = Depends(get_db)
):
    # gets restaurant reviews based on id
    logger.info("Hit /restaurant/id/reviews")
    try:
        query = select(Review).where(Review.restaurant_id == id)
        result = await db.execute(query)
        reviews = result.scalars().all()
        return {"restaurant": reviews}
    except Exception as e:
        logger.info(f"restaurants reviews failed : {e}")
        raise HTTPException(status_code=500, detail="restaurant reviews failed")

