import nh3
from fastapi import Depends, APIRouter, HTTPException, Request
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.responses import JSONResponse

from database_configuration import get_db,User
from passlib.context import CryptContext
import jwt
from datetime import datetime, timedelta
from logger import logger
from schemas import LocationChange, RegularSuccessResponse, LoginResponse, TokenRefreshResponse

router = APIRouter(
    prefix="/user",
    tags=["users"]
)


hash_context = CryptContext(schemes=["bcrypt"])
SECRET_KEY = "I have a plan"
ALGORITHM = "HS256"
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/user/login")

async def get_current_user(
        token : str = Depends(oauth2_scheme),
        db: AsyncSession = Depends(get_db)
):
    try:
        payload = jwt.decode(token,SECRET_KEY,algorithms=ALGORITHM)
        username = payload.get("user")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid token")

        query = select(User).where(User.email == username)
        result = await db.execute(query)
        user_info = result.scalars().first()

        return {"id" : user_info.id,"username" : username}
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")
    except Exception as e:
        logger.info(f"Get current user : {e}")
        raise HTTPException(status_code=500, detail="Get current user failed")

@router.post(
    "/register",
    summary="Register new user",
    description="Creates new user",
    responses={
        200: {
            "model" : RegularSuccessResponse,
            "description": "User created succesfully"
        },
        400: {"description" : "User already exists"},
        500: {"description": "User registration failed"}
    })
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
            raise HTTPException(status_code=400, detail="User already exists")
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



@router.post("/login",
    summary="User Login",
    description="Authenticates user and returns an access token. Sets a refresh token in an HttpOnly cookie.",
    response_model=LoginResponse,
    responses={
        200: {"model": LoginResponse},
        401: {"description": "Invalid credentials (wrong email or password)"},
        500: {"description": "User login failed"}
    })
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
            raise HTTPException(status_code=401, detail="User does not exist")
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
                raise HTTPException(status_code=401, detail="Wrong password")
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




@router.post("/refresh",
    summary="Refresh Access Token",
    description="Generates a new access token using the refresh token stored in cookies.",
    response_model=TokenRefreshResponse,
    responses={
        200: {"model": TokenRefreshResponse},
        401: {"description": "Invalid or expired refresh token"}
    })
async def refresh(request : Request):

    try:

        token = request.cookies.get("refresh_token")
        payload = jwt.decode(token, SECRET_KEY, algorithms=ALGORITHM)
        if payload.get("type") == "refresh":
            # generate new access token
            username = payload.get("user")
            access_token = create_token(username)
            return {
                "msg" : "Token successfully refreshed",
                "access_token" : access_token
            }
        else:
            raise HTTPException(status_code=401, detail="This is not a refresh token")


    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")


@router.post("/location",
    summary="Change User Location",
    description="Updates the latitude and longitude of the currently authenticated user.",
    response_model=RegularSuccessResponse,
    responses={
        200: {"model": RegularSuccessResponse},
        401: {"description": "Not authenticated"},
        404: {"description": "No data provided"},
        500: {"description": "Location update failed"}
    })
async def change_location(
        location : LocationChange,
        db: AsyncSession = Depends(get_db),
        user: dict = Depends(get_current_user)
):
    try:
        query = select(User).where(User.id == user["id"])
        result = await db.execute(query)
        user = result.scalars().first()
        if location.lat:
            user.lat = location.lat

        if location.lng:
            user.lng = location.lng
        if not location.lat and not location.lng:
            raise HTTPException(status_code=404, detail="No data provided")

        await db.commit()
        return {"msg" : "User location changed"}
    except Exception as e:
        logger.info(f"Location update failed: {e}")
        raise HTTPException(status_code=500, detail="Location update failed")

