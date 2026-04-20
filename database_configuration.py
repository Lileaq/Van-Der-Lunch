import os
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base, relationship
from sqlalchemy import Column, Integer, String, Numeric, Table, ForeignKey, Boolean, DateTime

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_async_engine(DATABASE_URL)
SessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)
Base = declarative_base()

async def get_db():
    async with SessionLocal() as db:
        yield db

class User(Base):
    __tablename__ = "users"
    id = Column(Integer,primary_key=True,index=True)
    email = Column(String(255), nullable = False,unique=True)
    password = Column(String(255), nullable=False)
    lat = Column(Numeric(precision=11, scale=8), nullable=True)
    lng = Column(Numeric(precision=11, scale=8), nullable=True)

    reviews = relationship("Review", back_populates="user")

restaurant_tags = Table(
    "restaurant_tags",
    Base.metadata,
    Column("restaurant_id", Integer, ForeignKey("restaurants.id"), primary_key=True),
    Column("tag_id", Integer, ForeignKey("tags.id"), primary_key=True),
)
class Restaurant(Base):
    __tablename__ = "restaurants"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    opening_hours = Column(String(255))
    address = Column(String(255))
    lat = Column(Numeric(precision=11, scale=8), nullable=True)
    lng = Column(Numeric(precision=11, scale=8), nullable=True)

    tags = relationship("Tag", secondary=restaurant_tags, back_populates="restaurants")
    food_items = relationship("FoodItem", back_populates="restaurant", cascade="all, delete-orphan")
    reviews = relationship("Review", back_populates="restaurant", cascade="all, delete-orphan")

class Tag(Base):
    __tablename__ = "tags"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50))

    restaurants = relationship("Restaurant", secondary=restaurant_tags, back_populates="tags")


class FoodItem(Base):
    __tablename__ = "food_items"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    base_price = Column(Numeric(precision=10, scale=2))
    availability = Column(Boolean,default=True)
    restaurant_id = Column(Integer, ForeignKey("restaurants.id", ondelete="CASCADE"))

    restaurant = relationship("Restaurant", back_populates="food_items")

class Review(Base):
    __tablename__ = "reviews"
    id = Column(Integer, primary_key=True, index=True)
    restaurant_id = Column(Integer, ForeignKey("restaurants.id", ondelete="CASCADE"))
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    stars = Column(Integer,nullable=True)
    review_text = Column(String(255), nullable=True)
    created_at = Column(DateTime)

    restaurant = relationship("Restaurant", back_populates="reviews")
    user = relationship("User", back_populates="reviews")

