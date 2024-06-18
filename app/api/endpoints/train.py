from typing import List, Optional
from fastapi import APIRouter, Depends, status, HTTPException
from app.db.session import get_db
from sqlalchemy.orm import Session
from app.schemas import user_schema
from app.utils import oauth2
import app.crud.train as train

router = APIRouter(
    prefix="/finetune",
    tags=["Train"],
)

@router.post("/", status_code=status.HTTP_200_OK)
def finetune(
    db: Session = Depends(get_db),
    current_user: user_schema.User = Depends(oauth2.get_current_user),
):
    return train.finetune(db, current_user)

