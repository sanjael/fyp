from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from passlib.context import CryptContext

router = APIRouter()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class UserCreate(BaseModel):
    email: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str
    email: str

@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(user: UserCreate):
    return {
        "message": "User registered successfully",
        "access_token": f"jwt-{user.email}-token",
        "token_type": "bearer",
        "email": user.email
    }

@router.post("/login", response_model=Token)
async def login(user: UserCreate):
    return {
        "access_token": f"jwt-{user.email}-token",
        "token_type": "bearer",
        "email": user.email
    }

@router.get("/me")
async def get_me(email: str = "user@ragguard.ai"):
    return {"email": email}

@router.post("/refresh")
async def refresh_token():
    return {"message": "Token refreshed"}

@router.post("/logout")
async def logout():
    return {"message": "Logged out successfully"}

