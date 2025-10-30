import re
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session
from jose import jwt
from passlib.context import CryptContext
from datetime import datetime, timedelta
from app.database import get_db
from app.models import User
from app.config import get_settings

router = APIRouter(prefix="/api/auth", tags=["auth"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
settings = get_settings()

class LoginIn(BaseModel):
    email: EmailStr
    password: str

class SignupIn(BaseModel):
    username: str
    email: EmailStr
    password: str

def validate_saur_email(email: str):
    pattern = r'^[a-z]+\.[a-z-]+@saur\.com$'
    if not re.match(pattern, email, re.IGNORECASE):
        raise HTTPException(400, "Seuls les emails @saur.com (prenom.nom@saur.com) sont autorisés")

def create_access_token(data: dict):
    expire = datetime.utcnow() + timedelta(minutes=settings.JWT_EXPIRE_MINUTES)
    return jwt.encode({**data, "exp": expire}, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        user_id = int(payload["sub"])
    except:
        raise HTTPException(401, "Token invalide")
    user = db.get(User, user_id)
    if not user: raise HTTPException(401, "Utilisateur introuvable")
    return user

@router.post("/login")
def login(data: LoginIn, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == data.email).first()
    if not user or not pwd_context.verify(data.password, user.password_hash):
        raise HTTPException(401, "Identifiants incorrects")
    return {"access_token": create_access_token({"sub": str(user.id)}), "token_type": "bearer"}

@router.post("/signup")
def signup(data: SignupIn, db: Session = Depends(get_db)):
    validate_saur_email(data.email)
    if db.query(User).filter(User.email == data.email).first():
        raise HTTPException(409, "Email déjà utilisé")
    user = User(
        username=data.username,
        email=data.email,
        password_hash=pwd_context.hash(data.password),
        role="editor"
    )
    db.add(user); db.commit(); db.refresh(user)
    return {
        "access_token": create_access_token({"sub": str(user.id)}),
        "user": {"id": user.id, "username": user.username, "role": "editor"}
    }

@router.get("/me")
def me(user = Depends(get_current_user)):
    return {"id": user.id, "username": user.username, "email": user.email, "role": user.role}
