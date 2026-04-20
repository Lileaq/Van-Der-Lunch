from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session

from logger import logger
from database_configuration import Base, Restaurant, get_db
from routes import user,restaurant



app = FastAPI(title="Van Der Lunch -  food delivery service",
    description="API for food delivery service managment",
    version="1.0.0")

app.include_router(user.router)
app.include_router(restaurant.router)

from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:5500"],  # Live Server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    logger.info('Hit /root')
    return {"message": "Hello World"}

#return random restaurant info to test db connection
@app.get("/test_connection")
async def test_connection(db: Session = Depends(get_db)):
    restaurant = db.query(Restaurant).first()

    if not restaurant:
        return {"message": "Brak restauracji w bazie"}

    return {
        "id": restaurant.id,
        "name": restaurant.name,
        "opening_hours": restaurant.opening_hours,
        "type_tags": restaurant.type_tags,
        "address": restaurant.address,
        "coordinates": restaurant.coordinates
    }


@app.on_event("startup")
async def startup_event():
    logger.info("API is running")


