import os

from fastapi import FastAPI
from motor.motor_asyncio import AsyncIOMotorClient

app = FastAPI()

mongo_uri = os.getenv("MONGO_URI")
client = AsyncIOMotorClient(mongo_uri)
db = client["test_db"]
collection = db["test_collection"]


@app.get("/")
async def read_root():
    return {"message": "Welcome to FastAPI with MongoDB"}


@app.post("/add")
async def add_item(name: str):
    result = await collection.insert_one({"name": name})
    return {"inserted_id": str(result.inserted_id)}


@app.get("/items")
async def get_items():
    items = await collection.find({}, {"_id": 0, "name": 1}).to_list(100)
    return {"items": items}
