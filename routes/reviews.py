import nh3
from fastapi import FastAPI, Depends, APIRouter, HTTPException, Request, Query
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from sqlalchemy import select, and_, func, delete
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session
from fastapi.responses import JSONResponse
from typing import Optional

from database_configuration import get_db,Restaurant,FoodItem,Review,User
from passlib.context import CryptContext
import jwt
from datetime import datetime, timedelta
from logger import logger
from routes.user import get_current_user
from schemas import ReviewCreate

router = APIRouter(
    prefix="/reviews",
    tags=["reviews"]
)


@router.post("/")
async def make_review(
        data : ReviewCreate,
        db: AsyncSession = Depends(get_db)
):
    logger.info("Hit /reviews create new review")
    # create review based on the data sent
    new_review = Review(
        user_id=data.user_id,
        restaurant_id=data.restaurant_id,
        stars=data.stars,
        review_text=data.review_text,
    )
    try:
        # add to the database
        db.add(new_review)
        await db.commit()
        await db.refresh(new_review)  # Pobiera ID nadane przez bazę
        return {"msg": "Review created", "review_id": new_review.id}
    except Exception as e:
        logger.info(f"create review failed : {e}")
        raise HTTPException(status_code=500, detail="create review failed")

    return

@router.get("/{user_id}")
async def get_user_reviews(
        user_id : int,
        db: AsyncSession = Depends(get_db)
):
    # get users reviews list, also sorted by starts or time
    try:
        query = select(Review).where(Review.user_id == user_id)
        result = await db.execute(query)
        user_reviews = result.scalars().all()
        return {"user_reviews": user_reviews}
    except Exception as e:
        logger.info(f"get user review failed : {e}")
        raise HTTPException(status_code=500, detail="get user review failed")




@router.get("/{restaurant_id}")
async def get_restaurant_reviews():
    # get restaurant reviews list also sorted by stars or time
    # copy from other file
    return

@router.delete("/{review_id}")
async def delete_review(
        review_id : int,
        user_email: str = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)

):
    # deletes the review with the specified id
    logger.info("Hit /review/{review_id} delete review")
    # get users id
    try:
        user_query = select(User).where(User.email == user_email)
        result = await db.execute(user_query)
        user = result.scalars().first()

        # delete the review if user id matches
        query = (
            delete(Review)
            .where(
                and_(
                    Review.id == review_id,
                    Review.user_id == user.id
                )
            )
        )

        result = await db.execute(query)
        await db.commit()

        if result.rowcount == 0:
            raise HTTPException(
                status_code=404,
                detail="Review not found"
            )

        return {"msg": f"Review {review_id} deleted successfully"}
    except Exception as e:
        logger.info(f"delete review failed : {e}")
        raise HTTPException(status_code=500, detail="delete review failed")