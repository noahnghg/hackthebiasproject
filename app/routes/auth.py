from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from core.database import User, Session, engine, select
import uuid

router = APIRouter(
    prefix="/auth",
    tags=["auth"]
)

class SignUpRequest(BaseModel):
    email: str
    password: str

class SignInRequest(BaseModel):
    email: str
    password: str

class AuthResponse(BaseModel):
    user_id: str
    email: str
    message: str

@router.post("/sign-up", response_model=AuthResponse)
async def sign_up(request: SignUpRequest):
    """Create a new user account."""
    with Session(engine) as session:
        # Check if email already exists
        statement = select(User).where(User.email == request.email)
        existing_user = session.exec(statement).first()
        
        if existing_user:
            raise HTTPException(status_code=400, detail="Email already registered")
        
        # Create new user with empty profile
        new_user = User(
            id=str(uuid.uuid4()),
            email=request.email,
            password=request.password,  # In production, hash this!
            skills="",
            experience="",
            education=""
        )
        session.add(new_user)
        session.commit()
        session.refresh(new_user)
        
        return AuthResponse(
            user_id=new_user.id,
            email=new_user.email,
            message="Account created successfully"
        )

@router.post("/sign-in", response_model=AuthResponse)
async def sign_in(request: SignInRequest):
    """Sign in with email and password."""
    with Session(engine) as session:
        # Find user by email
        statement = select(User).where(User.email == request.email)
        user = session.exec(statement).first()
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Check password (simple comparison - in production, use hashing!)
        if user.password != request.password:
            raise HTTPException(status_code=401, detail="Incorrect password")
        
        return AuthResponse(
            user_id=user.id,
            email=user.email,
            message="Sign in successful"
        )
