from fastapi import FastAPI

app = FastAPI(title="Van Der Lunch -  food delivery service",
    description="API for food delivery service managment",
    version="1.0.0")


@app.get("/")
async def root():
    return {"message": "Hello World"}