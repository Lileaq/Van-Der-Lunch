import nh3
from fastapi import FastAPI, Depends, APIRouter, HTTPException, Request
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session
from fastapi.responses import JSONResponse

from database_configuration import get_db,User
from passlib.context import CryptContext
import jwt
from datetime import datetime, timedelta
from logger import logger

router = APIRouter(
    prefix="/user",
    tags=["users"]
)



hash_context = CryptContext(schemes=["bcrypt"])
SECRET_KEY = "your_secret"
ALGORITHM = "HS256"
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/user/login")

def get_current_user(token : str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token,SECRET_KEY,algorithms=ALGORITHM)
        username = payload.get("user")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid token")

        return username
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

@router.get("/user_test")
def test_user(user: str = Depends(get_current_user)):
    logger.info("Hit /user_test")
    return {"message": "User endpoint test", "user" : user}

@router.post("/register")
async def register_user(
        register_data : OAuth2PasswordRequestForm = Depends(),
        db: AsyncSession = Depends(get_db)
):
    logger.info("Hit /user/register")
    username = nh3.clean(register_data.username)
    password = nh3.clean(register_data.password)

    # here check username and password criteria

    try:
        user_exists = await check_user_exists(db,username)
        if user_exists:
            return {"msg" : "user exists"}
        else:
            await register_new_user(db,username,password)
            return {"msg" : "User created"}
    except Exception as e:
        logger.info(f"Register failed : {e}")
        raise HTTPException(status_code=500, detail="User register failed")


async def check_user_exists(database,username):
    logger.info("Executing 'check_user_exists'")
    # query on User table
    query = select(User).where(User.email == username)
    result = await database.execute(query)
    user = result.scalars().first()
    if user:
        return user
    else:
        return False

async def register_new_user(database,username,password):
    logger.info("Executing 'register_new_user'")
    # add to User table
    new_user = User(email=username,password=hash_context.hash(password))
    database.add(new_user)
    await database.commit()
    return



@router.post("/login")
async def login_user(
        login_data : OAuth2PasswordRequestForm = Depends(),
        db: AsyncSession = Depends(get_db)
):
    # check if login data is valid
    username = nh3.clean(login_data.username)
    password = nh3.clean(login_data.password)

    try:
        # check if user exists
        user_exists = await check_user_exists(db,username)
        if user_exists == False:
            return {"msg" : "user does not exist"}
        else:
            # check if password is valid
            if hash_context.verify(password,user_exists.password):
                # generate tokens
                access_token = create_token(username)
                refresh_token = create_token(username,True)

                response = JSONResponse({
                    "msg": "you are logged in",
                    "access_token": access_token})

                response.set_cookie(
                    key="refresh_token",
                    value=refresh_token,
                    httponly=True,
                    samesite="lax"
                )

                return response

            else:
                return {"msg": "wrong password"}
    except Exception as e:
        logger.info(f"Login failed : {e}")
        raise HTTPException(status_code=500, detail="User login failed")


def create_token(username,refresh : bool = False):
    # token created with data : username,expiry, is_refresh
    # expiry for refresh is 2 days and for access is 30mins
    if refresh:
        expiry = datetime.utcnow() + timedelta(days=2)
        token_type = "refresh"
    else:
        expiry = datetime.utcnow() + timedelta(seconds=1800)
        token_type = "access"
    payload = {
        "user": username,
        "exp": expiry,
        "refresh": refresh,
        "type" : token_type
    }
    token = jwt.encode(payload,SECRET_KEY,algorithm=ALGORITHM)
    return token



@router.post("/refresh")
async def refresh(request : Request):
    try:

        token = request.cookies.get("refresh_token")
        payload = jwt.decode(token, SECRET_KEY, algorithms=ALGORITHM)
        if payload.get("type") == "refresh":
            # generate new access token
            username = payload.get("user")
            access_token = create_token(username)
            return {
                "access_token" : access_token
            }
        else:
            raise HTTPException(status_code=401, detail="This is not a refresh token")


    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")