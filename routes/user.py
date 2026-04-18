from fastapi import FastAPI, Depends, APIRouter
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session
from database_configuration import get_db

from logger import logger

router = APIRouter(
    prefix="/user",
    tags=["users"]
)

@router.get("/user_test")
def test_user():
    logger.info("Hit /user_test")
    return {"message": "User endpoint test"}

@router.post("/register")
def register_user(
        register_data : OAuth2PasswordRequestForm = Depends(),
        db: AsyncSession = Depends(get_db)
):
    logger.info("Hit /user/register")
    # chceck if user exists
    # if not then register user
    # return information
    return

def check_user_exists():
    # query on User table
    return

def register_new_user():
    # add to User table
    return