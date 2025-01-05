import os

from fastapi import FastAPI, HTTPException
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel
from bson import ObjectId

app = FastAPI()

mongo_uri = os.getenv("MONGO_URI")
client = AsyncIOMotorClient(mongo_uri)
db = client["library_db"]
books_collection = db["books"]


class Book(BaseModel):
    title: str
    author: str
    published_year: int
    isbn: str


class BookOut(BaseModel):
    title: str
    author: str
    published_year: int
    isbn: str

    class Config:
        json_encoders = {ObjectId: str}


def book_helper(book) -> dict:
    return {
        "title": book["title"],
        "author": book["author"],
        "published_year": book["published_year"],
        "isbn": book["isbn"],
        "id": str(book["_id"]),
    }


@app.post("/books", response_model=BookOut)
async def create_book(book: Book):
    result = await books_collection.insert_one(book.model_dump())
    new_book = await books_collection.find_one({"_id": result.inserted_id})
    return book_helper(new_book)


@app.get("/books/{book_id}", response_model=BookOut)
async def get_book(book_id: str):
    book = await books_collection.find_one({"_id": ObjectId(book_id)})
    if book is None:
        raise HTTPException(status_code=404, detail="Book not found")
    return book_helper(book)


@app.put("/books/{book_id}", response_model=BookOut)
async def update_book(book_id: str, book: Book):
    result = await books_collection.update_one(
        {"_id": ObjectId(book_id)},
        {"$set": book.model_dump()},
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Book not found")

    updated_book = await books_collection.find_one({"_id": ObjectId(book_id)})
    return book_helper(updated_book)


@app.delete("/books/{book_id}", response_model=dict)
async def delete_book(book_id: str):
    result = await books_collection.delete_one({"_id": ObjectId(book_id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Book not found")
    return {"message": "Book deleted successfully"}


@app.get("/books", response_model=list[BookOut])
async def get_books(skip: int = 0, limit: int = 100):
    books_cursor = books_collection.find().skip(skip).limit(limit)
    books = await books_cursor.to_list(length=limit)
    return [book_helper(book) for book in books]
