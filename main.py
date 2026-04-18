from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session

from logger import logger
from database_configuration import Base, Restaurant, get_db
from routes import user

app = FastAPI(title="Van Der Lunch -  food delivery service",
    description="API for food delivery service managment",
    version="1.0.0")

app.include_router(user.router)
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


logger.info("API is running")


