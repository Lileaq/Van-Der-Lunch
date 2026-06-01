import os
import enum
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base, relationship
from sqlalchemy import Column, Integer, String, Numeric, Table, ForeignKey, Boolean, DateTime, Enum, DECIMAL, func, \
    Float, Text

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_async_engine(
    DATABASE_URL,
    connect_args={
        "init_command": "SET time_zone='+00:00'"
})

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
    orders = relationship("Order", back_populates="user")

restaurant_tags = Table(
    "restaurant_tags",
    Base.metadata,
    Column("restaurant_id", Integer, ForeignKey("restaurants.id"), primary_key=True),
    Column("tag_id", Integer, ForeignKey("tags.id"), primary_key=True),
)


food_tags = Table(
    "food_tags",
    Base.metadata,
    Column("food_item_id", Integer, ForeignKey("food_items.id"), primary_key=True),
    Column("tag_id", Integer, ForeignKey("tags.id"), primary_key=True),
)
class Restaurant(Base):
    __tablename__ = "restaurants"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    address = Column(String(255))
    lat = Column(Numeric(precision=10, scale=8), nullable=True)
    lng = Column(Numeric(precision=11, scale=8), nullable=True)
    opening_hours = Column(String(255))

    tags = relationship("Tag", secondary=restaurant_tags, back_populates="restaurants")
    food_items = relationship("FoodItem", back_populates="restaurant", cascade="all, delete-orphan")
    reviews = relationship("Review", back_populates="restaurant", cascade="all, delete-orphan")
    orders = relationship("Order", back_populates="restaurant")
    opening_hours_list = relationship("RestaurantOpeningHour", back_populates="restaurant")


class RestaurantOpeningHour(Base):
    __tablename__ = "restaurant_opening_hours"
    id = Column(Integer, primary_key=True)
    restaurant_id = Column(Integer, ForeignKey("restaurants.id", ondelete="CASCADE"))
    day_of_week = Column(Integer)
    open_time = Column(Integer)
    close_time = Column(Integer)
    is_closed = Column(Boolean, default=False)

    restaurant = relationship("Restaurant", back_populates="opening_hours_list")


class Tag(Base):
    __tablename__ = "tags"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50))

    restaurants = relationship("Restaurant", secondary=restaurant_tags, back_populates="tags")
    food_items = relationship("FoodItem", secondary=food_tags, back_populates="tags")



class FoodItem(Base):
    __tablename__ = "food_items"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    base_price = Column(Numeric(precision=10, scale=2))
    availability = Column(Boolean,default=True)
    restaurant_id = Column(Integer, ForeignKey("restaurants.id", ondelete="CASCADE"))
    description = Column(String(255))

    restaurant = relationship("Restaurant", back_populates="food_items")
    order_items = relationship("OrderItem", back_populates="food_item")
    tags = relationship("Tag", secondary=food_tags, back_populates="food_items")




class Review(Base):
    __tablename__ = "reviews"
    id = Column(Integer, primary_key=True, index=True)
    restaurant_id = Column(Integer, ForeignKey("restaurants.id", ondelete="CASCADE"))
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    stars = Column(Integer,nullable=True)
    review_text = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    restaurant = relationship("Restaurant", back_populates="reviews")
    user = relationship("User", back_populates="reviews")


class OrderStatus(enum.Enum):
    cart = "cart"
    not_paid = "not paid"
    paid = "paid"
    preparing = "preparing"
    on_the_way = "on_the_way"
    completed = "completed"
    canceled = "canceled"


class Order(Base):
    __tablename__="orders"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    restaurant_id = Column(Integer, ForeignKey("restaurants.id", ondelete="CASCADE"))
    status = Column(Enum(OrderStatus),default=OrderStatus.cart,nullable=False)
    total_price = Column(DECIMAL(10,2),default=0.00)
    created_at = Column(DateTime,server_default=func.now())
    updated_at = Column(DateTime,server_default=func.now(),onupdate=func.now())
    route = Column(Text)
    delivery_time = Column(Float)

    restaurant = relationship("Restaurant", back_populates="orders")
    user = relationship("User", back_populates="orders")
    order_items = relationship("OrderItem",back_populates="order")
    order_courier = relationship("Courier",back_populates="order")

class OrderItem(Base):
    __tablename__="order_items"
    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id", ondelete="CASCADE"))
    food_item_id = Column(Integer, ForeignKey("food_items.id", ondelete="CASCADE"))
    quantity = Column(Integer)

    order = relationship("Order", back_populates="order_items")
    food_item = relationship("FoodItem", back_populates="order_items")

class Courier(Base):
    __tablename__="couriers"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255))
    current_order_id = Column(Integer, ForeignKey("orders.id", ondelete="CASCADE"))

    order = relationship("Order", back_populates="order_courier")


