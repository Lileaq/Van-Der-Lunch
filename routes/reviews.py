import nh3
from fastapi import Depends, APIRouter, HTTPException
from sqlalchemy import select, and_, delete
from sqlalchemy.ext.asyncio import AsyncSession
from database_configuration import get_db,Review
from logger import logger
from routes.user import get_current_user
from schemas import ReviewCreate, ReviewsResponse, ReviewCreatedResponse, UserReviewsResponse, RegularSuccessResponse

router = APIRouter(
    prefix="/reviews",
    tags=["reviews"]
)


@router.post(
    "/create",
    summary="Create a new review",
    description="Submits a new restaurant review",
    response_model=ReviewCreatedResponse,
    status_code=201
)
async def make_review(
        data : ReviewCreate,
        user: dict = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
):
    logger.info("Hit /reviews create new review")
    # create review based on the data sent
    new_review = Review(
        user_id=user["id"],
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
        logger.info(f"Create review failed : {e}")
        raise HTTPException(status_code=500, detail="Create review failed")



@router.get(
    "/{user_id}",
    summary="Get reviews by user",
    description="Returns a list of all reviews submitted by a specific user.",
    response_model=UserReviewsResponse,
    responses={
        200: {"description": "List of users reviews"},
        500: {"description": "Get users reviews failed"}
    }
)
async def get_user_reviews(
        user_id: int,
        user: dict = Depends(get_current_user),
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




@router.get(
    "/{restaurant_id}",
    summary="Get restaurant reviews",
    description="Returns a list of all user reviews for the specified restaurant.",
    response_model=ReviewsResponse,
    responses={404: {"description": "Restaurant reviews not found"}}
)
async def info(
        restaurant_id : int,
        db : AsyncSession = Depends(get_db),
        user: dict = Depends(get_current_user)
):
    # gets restaurant reviews based on id
    logger.info("Hit /restaurant/id/reviews")
    try:
        query = select(Review).where(Review.restaurant_id == restaurant_id)
        result = await db.execute(query)
        reviews = result.scalars().all()
    except Exception as e:
        logger.info(f"restaurants reviews failed : {e}")
        raise HTTPException(status_code=500, detail="restaurant reviews failed")
    if not reviews:
        raise HTTPException(status_code=404, detail="Restaurant reviews not found")
    return {"reviews": reviews}


@router.delete("/{review_id}",
    summary="Delete a review",
    description="Deletes a specific review. Only the author of the review can delete it.",
    response_model=RegularSuccessResponse,
    responses={
        200: {"description": "Review deleted"},
        404: {"description": "Review not found or unauthorized"},
        500: {"description": "Delete review failed"}
    })
async def delete_review(
        review_id : int,
        user: dict = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)

):
    # deletes the review with the specified id
    logger.info("Hit /review/{review_id} delete review")
    # get users id
    try:
        query = delete(Review).where(
            and_(
                Review.id == review_id,
                Review.user_id == user["id"]
            )
        )

        result = await db.execute(query)
        await db.commit()

        if result.rowcount == 0:
            raise HTTPException(
                status_code=404,
                detail="Review not found or you don't have permission to delete it"
            )

        return {"msg": f"Review {review_id} deleted successfully"}
    except Exception as e:
        logger.info(f"Delete review failed : {e}")
        raise HTTPException(status_code=500, detail="Delete review failed")