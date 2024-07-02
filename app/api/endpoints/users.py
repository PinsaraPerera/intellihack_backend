from typing import List, Optional
from fastapi import APIRouter, Depends, status, HTTPException, Request
from app.schemas import user_schema
from app.db.session import get_db
from sqlalchemy.orm import Session
import app.crud.user as user


router = APIRouter(
    prefix="/user",
    tags=["Users"],
)


@router.post("/", response_model=user_schema.User)
def create_user(params: user_schema.UserBase, request: Request, db: Session = Depends(get_db)):
    return user.create(params, db)


@router.get("/{id}", response_model=user_schema.User)
def get_user(id: int, request: Request, db: Session = Depends(get_db)):
    return user.show(id, db)


@router.get("/email/{email}", response_model=user_schema.User)
def get_user_by_email(email: str, request: Request, db: Session = Depends(get_db)):
    return user.show_by_email(email, db)

@router.put("/update/{id}", response_model=user_schema.User)
def update_user(id: int, params: user_schema.User, request: Request, db: Session = Depends(get_db)):
    return user.update_user(id, params, db)
