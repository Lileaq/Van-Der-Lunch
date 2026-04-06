from fastapi import FastAPI, Depends
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base, Session
from sqlalchemy import Column, Integer, String


load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class Restaurant(Base):
    __tablename__ = "restaurants"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    opening_hours = Column(String(255))
    type_tags = Column(String(255))
    address = Column(String(255))
    coordinates = Column(String(50))

app = FastAPI(title="Van Der Lunch -  food delivery service",
    description="API for food delivery service managment",
    version="1.0.0")


@app.get("/")
async def root():
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


