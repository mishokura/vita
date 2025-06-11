# career_helper_api/main.py
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from typing import List, Dict, Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, Boolean, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, Session
import uvicorn
import datetime
from dotenv import load_dotenv
import os
load_dotenv()

# Configs
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# DB setup
DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
Base = declarative_base()

# Security
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Models
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    is_admin = Column(Boolean, default=False)

class CareerPath(Base):
    __tablename__ = "career_paths"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)

class Question(Base):
    __tablename__ = "questions"
    id = Column(Integer, primary_key=True, index=True)
    text = Column(String)
    associations = Column(JSON)

Base.metadata.create_all(bind=engine)

# Pydantic Schemas
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

class QuestionAnswer(BaseModel):
    question_id: int
    answer: int  # scale 0-100

class QuestionResponse(BaseModel):
    text: str
    id: int

class QuestionCreate(BaseModel):
    text: str
    associations: Dict[str, int]

class CareerCreate(BaseModel):
    name: str



def get_password_hash(password):
    return pwd_context.hash(password)

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict, expires_delta: Optional[datetime.timedelta] = None):
    to_encode = data.copy()
    expire = datetime.datetime.utcnow() + (expires_delta or datetime.timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def get_user(db: Session, username: str):
    return db.query(User).filter(User.username == username).first()

def authenticate_user(db: Session, username: str, password: str):
    user = get_user(db, username)
    if user and verify_password(password, user.hashed_password):
        return user
    return None

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(lambda: SessionLocal())):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid credentials")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    user = get_user(db, username)
    if user is None:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return user

def get_admin_user(current_user: User = Depends(get_current_user)):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorized")
    return current_user



app = FastAPI()

@app.post("/token", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(lambda: SessionLocal())):
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/register")
def register(username: str, password: str, is_admin: bool = False, db: Session = Depends(lambda: SessionLocal())):
    if get_user(db, username):
        raise HTTPException(status_code=400, detail="Username taken")
    hashed_password = get_password_hash(password)
    db.add(User(username=username, hashed_password=hashed_password, is_admin=is_admin))
    db.commit()
    return {"msg": "User registered successfully"}

# Admin Endpoints
@app.post("/admin/careers", dependencies=[Depends(get_admin_user)])
def add_career(career: CareerCreate, db: Session = Depends(lambda: SessionLocal())):
    db.add(CareerPath(name=career.name))
    db.commit()
    return {"msg": "Career added"}

@app.post("/admin/questions", dependencies=[Depends(get_admin_user)])
def add_question(question: QuestionCreate, db: Session = Depends(lambda: SessionLocal())):
    db.add(Question(text=question.text, associations=question.associations))
    db.commit()
    return {"msg": "Question added"}

@app.get("/questions", response_model=List[QuestionResponse])
def get_questions(db: Session = Depends(lambda: SessionLocal())):
    questions = db.query(Question).all()
    return [QuestionResponse(id=q.id, text=q.text) for q in questions]

# Answer Handling
@app.post("/submit")
def submit_answers(
    answers: List[QuestionAnswer], 
    last: bool = False, 
    db: Session = Depends(lambda: SessionLocal())
):
    career_scores = {}
    for answer in answers:
        question = db.query(Question).filter(Question.id == answer.question_id).first()
        if not question:
            continue
        for career, weight in question.associations.items():
            career_scores[career] = career_scores.get(career, 0) + (weight * answer.answer / 100)

    if last:
        sorted_scores = sorted(career_scores.items(), key=lambda x: x[1], reverse=True)
        return {"career_recommendations": sorted_scores}

    return {"msg": "Answers received"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
