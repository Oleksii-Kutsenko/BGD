import os

from fastapi import FastAPI, HTTPException
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel
from bson import ObjectId
from datetime import datetime

app = FastAPI()

mongo_uri = os.getenv("MONGO_URI")
client = AsyncIOMotorClient(mongo_uri)
db = client["library_db"]
books_collection = db["books"]

class BookRent(BaseModel):
    book_id: str
    user_id: str
    start_date: datetime
    end_date: datetime


class BookRentOut(BaseModel):
    book_id: str
    user_id: str
    start_date: datetime
    end_date: datetime

    class Config:
        json_encoders = {ObjectId: str}


class User(BaseModel):
    first_name: str
    last_name: str
    phone_num: str


class UserOut(BaseModel):
    first_name: str
    last_name: str
    phone_num: str

    class Config:
        json_encoders = {ObjectId: str}


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

def user_helper(user) -> dict:
    return {
        "first_name": user["first_name"],
        "last_name": user["last_name"],
        "phone_num": user["phone_num"],
        "id": str(user["_id"]),
    }

def book_rent_helper(book_rent) -> dict:
    return {
        "user_id" : book_rent["user_id"],
        "book_id" : book_rent["book_id"],
        "start_date" : book_rent["start_date"],
        "end_date" : book_rent["end_date"],
        "id": str(book_rent["_id"]),
    }

@app.post("/rents", response_model=BookRentOut)
async def create_book_rent(book_rent: BookRent):
    result = await books_collection.insert_one(book_rent.model_dump())
    new_book_rent = await books_collection.find_one({"_id": result.inserted_id})
    return book_rent_helper(new_book_rent)


@app.get("/rents/{rent_id}", response_model=BookRentOut)
async def get_book_rent(book_rent_id: str):
    book_rent = await books_collection.find_one({"_id": ObjectId(book_rent_id)})
    if book_rent is None:
        raise HTTPException(status_code=404, detail="Book rent not found")
    return book_rent_helper(book_rent)


@app.put("/rents/{rent_id}", response_model=BookRentOut)
async def update_book_rent(book_rent_id: str, book_rent: BookRent):
    result = await books_collection.update_one(
        {"_id": ObjectId(book_rent_id)},
        {"$set": book_rent.model_dump()},
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Book rent not found")

    updated_book_rent = await books_collection.find_one({"_id": ObjectId(book_rent_id)})
    return book_rent_helper(updated_book_rent)


@app.delete("/rents/{rent_id}", response_model=dict)
async def delete_book_rent(book_rent_id: str):
    result = await books_collection.delete_one({"_id": ObjectId(book_rent_id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Book rent not found")
    return {"message": "Book rent deleted successfully"}


@app.get("/rents", response_model=list[BookRentOut])
async def get_book_rents(skip: int = 0, limit: int = 100):
    book_rent_cursor = books_collection.find().skip(skip).limit(limit)
    book_rents = await book_rent_cursor.to_list(length=limit)
    return [book_rent_helper(book_rent) for book_rent in book_rents]

###

@app.post("/users", response_model=UserOut)
async def create_user(user: User):
    result = await books_collection.insert_one(user.model_dump())
    new_user = await books_collection.find_one({"_id": result.inserted_id})
    return user_helper(new_user)


@app.get("/users/{user_id}", response_model=UserOut)
async def get_user(user_id: str):
    user = await books_collection.find_one({"_id": ObjectId(user_id)})
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user_helper(user)


@app.put("/users/{user_id}", response_model=UserOut)
async def update_User(user_id: str, user: User):
    result = await books_collection.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": user.model_dump()},
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="User not found")

    updated_user = await books_collection.find_one({"_id": ObjectId(user_id)})
    return user_helper(updated_user)


@app.delete("/users/{user_id}", response_model=dict)
async def delete_user(user_id: str):
    result = await books_collection.delete_one({"_id": ObjectId(user_id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    return {"message": "User deleted successfully"}


@app.get("/users", response_model=list[UserOut])
async def get_users(skip: int = 0, limit: int = 100):
    users_cursor = books_collection.find().skip(skip).limit(limit)
    users = await users_cursor.to_list(length=limit)
    return [user_helper(user) for user in users]

####

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
