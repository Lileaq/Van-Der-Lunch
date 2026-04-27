from fastapi import FastAPI
from logger import logger
from routes import user,restaurant,reviews,order,tags, food



app = FastAPI(title="Van Der Lunch -  food delivery service",
    description="API for food delivery service",
    version="1.0.0")

app.include_router(user.router)
app.include_router(restaurant.router)
app.include_router(reviews.router)
app.include_router(order.router)
app.include_router(tags.router)
app.include_router(food.router)

from fastapi.middleware.cors import CORSMiddleware

# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["http://127.0.0.1:5500"],  # Live Server
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )


@app.get("/")
async def root():
    logger.info('Hit /root')
    return {"message": "Hello!"}

# #return random restaurant info to test db connection
# @app.get("/test_connection")
# async def test_connection(db: Session = Depends(get_db)):
#     restaurant = db.query(Restaurant).first()
#
#     if not restaurant:
#         return {"message": "Brak restauracji w bazie"}
#
#     return {
#         "id": restaurant.id,
#         "name": restaurant.name,
#         "opening_hours": restaurant.opening_hours,
#         "type_tags": restaurant.type_tags,
#         "address": restaurant.address,
#         "coordinates": restaurant.coordinates
#     }


@app.on_event("startup")
async def startup_event():
    logger.info("API is running")


