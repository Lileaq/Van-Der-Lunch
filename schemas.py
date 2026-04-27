from decimal import Decimal
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List, Tuple


# AUTH AND REGULAR RESPONSES
class RegularSuccessResponse(BaseModel):
    msg : str = Field(...,example="Action successful")

class LoginResponse(BaseModel):
    msg: str = Field(..., example="User successfully logged in")
    access_token: str = Field(..., example="eyJhbGciOiJIUzI1...")

class TokenRefreshResponse(BaseModel):
    msg: str = Field(..., example="Token successfully refreshed")
    access_token: str = Field(..., example="eyJhbGciOiJIUzI1...")


# RESTAURANT AND MENU

class TagBase(BaseModel):
    id: int = Field(..., example=1)
    name: str = Field(..., example="Spicy")
    class Config:
        from_attributes = True
class RestaurantBase(BaseModel):
    id: int = Field(...,example=1)
    name: str = Field(..., example="Pizzeria Bella")
    opening_hours : str = Field(...,example="10:00-22:00")
    address: str = Field(..., example="ul. Marszałkowska 10, Warszawa")
    lat: float = Field(..., example=52.2297)
    lng: float = Field(..., example=21.0122)

class FoodItemSchema(BaseModel):
    id: int
    name: str = Field(..., example="Margherita")
    base_price: float = Field(..., example=32.50)
    availability : bool = Field(...,example=True)
    restaurant_id : int = Field(...,example=1)
    description: Optional[str] = Field(None, example="Tomato sauce, mozzarella, basil")
    class Config:
        from_attributes = True



# RESTAURANT AND MENU RESPONSES
class RestaurantsResponse(BaseModel):
    restaurants_list: List[RestaurantBase]

class MenuResponse(BaseModel):
    food_items: List[FoodItemSchema]

class FoodItemResponse(BaseModel):
    id: int = Field(..., examples=[1])
    name: str = Field(..., examples=["Margherita Pizza"])
    base_price: float = Field(..., examples=[35.50])
    availability: bool = Field(..., examples=[True])
    restaurant_id: int = Field(..., examples=[10])
    description: Optional[str] = Field(None, examples=["Delicious cheese pizza"])

    tags: List[TagBase] = []

    class Config:
        from_attributes = True

class FoodListResponse(BaseModel):
    food_list: List[FoodItemResponse]

class TagsResponse(BaseModel):
    tags: List[TagBase]



# ORDER AND LOCATION
class LocationChange(BaseModel):
    lat: Optional[Decimal] = Field(None, description="Szerokość geograficzna", example=52.2297)
    lng: Optional[Decimal] = Field(None, description="Długość geograficzna", example=21.0122)
    class Config:
        from_attributes = True

class ItemInOrder(BaseModel):
    food_id : int
    quantity : int
class OrderCreate(BaseModel):
    order_items : list[ItemInOrder]

# ORDER AND LOCATION RESPONSE
class CreateOrderResponse(BaseModel):
    msg: str = Field(..., example="Order created successfully")
    order_id: int = Field(..., example=1)


class OrderResponse(BaseModel):
    id: int = Field(..., examples=[101])
    restaurant_id: int
    total_price: float = Field(..., examples=[125.50])
    status: str
    delivery_time: float = Field(..., description="Delivery duration in seconds")
    created_at: datetime

    class Config:
        from_attributes = True


class OrderListResponse(BaseModel):
    orders: List[OrderResponse]

class OrderStatusDetailedResponse(BaseModel):
    msg: Optional[str] = Field(None, example="courier on the way")
    status: str = Field(..., example="on_the_way")
    courier_position: Optional[Tuple[float, float]] = Field(None, description="[lat, lng]",examples=[(52.2297, 21.0122)])
    courier_name: str = Field(...,example="Arthur Morgan")
    progress: Optional[str] = Field(None, example="45%")


# REVIEWS
class ReviewCreate(BaseModel):
    restaurant_id: int
    stars: int = Field(ge=1, le=5)
    review_text: Optional[str] = None

class ReviewSchema(BaseModel):
    id: int = Field(...,example=1)
    user_id: int = Field(...,example=2)
    stars: int = Field(..., ge=1, le=5, example=5)
    review_text: Optional[str] = Field(None, example="Amazing pizza!")
    created_at : datetime = Field(...,
        description="The timestamp when the review was created",
        example="2026-04-26T12:00:00"
    )
    class Config:
        from_attributes = True


# REVIEW RESPONSES
class ReviewCreatedResponse(BaseModel):
    msg: str = Field(..., examples=["Review created"])
    review_id: int = Field(..., examples=[101])
class UserReviewsResponse(BaseModel):
    user_reviews: List[ReviewSchema]

class ReviewsResponse(BaseModel):
    reviews: List[ReviewSchema]
