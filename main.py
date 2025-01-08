import os

from fastapi import FastAPI, HTTPException
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel, Field
from bson import ObjectId
from datetime import datetime
from typing import Optional

app = FastAPI()

mongo_uri = os.getenv("MONGO_URI")
client = AsyncIOMotorClient(mongo_uri)
db = client["library_db"]
books_collection = db["books"]
users_collection = db["users"]


class User(BaseModel):
    first_name: str
    last_name: str
    phone_num: str


class UserOut(BaseModel):
    id: str = Field(..., alias="_id")
    first_name: str
    last_name: str
    phone_num: str

    class Config:
        json_encoders = {ObjectId: str}
        populate_by_name = True


class Book(BaseModel):
    title: str
    author: str
    published_year: int
    isbn: str
    cur_owner: Optional[str] = None


class BookOut(BaseModel):
    id: str = Field(..., alias="_id")
    title: str
    author: str
    published_year: int
    isbn: str
    cur_owner: Optional[str]

    class Config:
        json_encoders = {ObjectId: str}
        populate_by_name = True


def book_helper(book) -> dict:
    return {
        "id": str(book["_id"]),
        "title": book["title"],
        "author": book["author"],
        "published_year": book["published_year"],
        "isbn": book["isbn"],
        "cur_owner": book.get("cur_owner"),
    }

def user_helper(user) -> dict():
    return {
        "id": str(user["_id"]),
        "first_name": user["first_name"],
        "last_name": user["last_name"],
        "phone_num": user["phone_num"],
    }

# debug functionality for deleting everything :)
@app.delete("/delete_all")
async def delete_all():
    await books_collection.delete_many({})
    await users_collection.delete_many({})  
    return {"message": "All documents deleted from books and users collections"}


@app.put("/books/{book_id}/assign/{user_id}", response_model=BookOut)
async def assign_book(book_id: str, user_id: str):
    book = await books_collection.find_one({"_id": ObjectId(book_id)})
    if book is None:
        raise HTTPException(status_code=404, detail="Book not found")
    
    if book.get("cur_owner") is not None:
        raise HTTPException(status_code=404, detail="Book is already owned") #TODO: correct status code??

    user = await users_collection.find_one({"_id": ObjectId(user_id)})
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    
    await books_collection.update_one(
        {"_id": ObjectId(book_id)},
        {"$set": {"cur_owner": user_id}}
    )

    updated_book = await books_collection.find_one({"_id": ObjectId(book_id)})
    return book_helper(updated_book)


@app.put("/books/{book_id}/release", response_model=BookOut)
async def release_book(book_id: str):
    book = await books_collection.find_one({"_id": ObjectId(book_id)})
    if book is None:
        raise HTTPException(status_code=404, detail="Book not found")
    
    if book.get("cur_owner") is None:
        raise HTTPException(status_code=404, detail="Book is not owned") #TODO: correct status code??

    await books_collection.update_one(
        {"_id": ObjectId(book_id)},
        {"$set": {"cur_owner": None}}
    )

    updated_book = await books_collection.find_one({"_id": ObjectId(book_id)})
    return book_helper(updated_book)


@app.get("/users/{user_id}/owned_books", response_model=list[BookOut])
async def get_owned_books(user_id: str, skip: int = 0, limit: int = 100):
    books_cursor = books_collection.find({"cur_owner": user_id}).skip(skip).limit(limit)
    books = await books_cursor.to_list(length=limit)
    return [book_helper(book) for book in books]


@app.post("/users", response_model=UserOut)
async def create_user(user: User):
    result = await users_collection.insert_one(user.model_dump())
    new_user = await users_collection.find_one({"_id": result.inserted_id})
    return user_helper(new_user)


@app.get("/users/{user_id}", response_model=UserOut)
async def get_user(user_id: str):
    user = await users_collection.find_one({"_id": ObjectId(user_id)})
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user_helper(user)


@app.put("/users/{user_id}", response_model=UserOut)
async def update_user(user_id: str, user: User):
    result = await users_collection.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": user.model_dump()},
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="User not found")

    updated_user = await users_collection.find_one({"_id": ObjectId(user_id)})
    return user_helper(updated_user)


@app.delete("/users/{user_id}", response_model=dict)
async def delete_user(user_id: str):
    update_result = await books_collection.update_many(
        {"cur_owner": ObjectId(user_id)},
        {"$set": {"cur_owner": None}}
    )
    
    result = await users_collection.delete_one({"_id": ObjectId(user_id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    return {"message": "User deleted successfully",
            "books_updated": update_result.modified_count}


@app.get("/users", response_model=list[UserOut])
async def get_users(skip: int = 0, limit: int = 100):
    users_cursor = users_collection.find().skip(skip).limit(limit)
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
