from fastapi import APIRouter
from pydantic import BaseModel, EmailStr

router = APIRouter(prefix="/api/users", tags=["users"])

class UserIn(BaseModel):
    email: EmailStr

@router.get("/")
def list_users():
    return [{"id": 1, "email": "admin@example.com"}]

@router.post("/")
def create_user(_: UserIn):
    return {"id": 2}
