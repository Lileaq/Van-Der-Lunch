from fastapi import FastAPI, Depends, APIRouter
from sqlalchemy.orm import Session
from database_configuration import get_db

router = APIRouter(
    prefix="/user",
    tags=["users"]
)

@router.get("/user_test")
def test_user():
    return {"message": "User endpoint test"}

@router.post("/register")
def register_user():
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