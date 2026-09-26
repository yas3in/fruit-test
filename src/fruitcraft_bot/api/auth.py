"""Admin authentication routes."""

from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel
from src.fruitcraft_bot.core.config import settings
from src.fruitcraft_bot.core.security import verify_password, get_password_hash, create_access_token, get_current_admin

router = APIRouter(prefix="/api/auth", tags=["Auth"])


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    username: str


@router.post("/login", response_model=LoginResponse)
async def login(req: LoginRequest):
    # Check credentials against configured admin
    if req.username != settings.admin_username or req.password != settings.admin_password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )
    token = create_access_token(data={"sub": req.username})
    return LoginResponse(access_token=token, username=req.username)


@router.get("/me")
async def get_current_user_info(current_admin: str = Depends(get_current_admin)):
    return {
        "username": current_admin,
        "role": "admin"
    }
